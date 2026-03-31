"""Flow 2: Model Upgrade — Shadow → Compare → Promote → Route.

Tests the full upgrade path: shadow routing compares models,
promotion manager captures shadow data, tier progression advances,
router uses the promoted model.
"""

from fleet.core.model_promotion import ModelPromotionManager
from fleet.core.shadow_routing import ShadowResult, ShadowRouter
from fleet.core.tier_progression import TierProgressionTracker


def test_upgrade_full_cycle():
    """Shadow → ready → promote → tier advances → router gets new model."""
    router = ShadowRouter(production_model="hermes-3b", candidate_model="qwen3-8b")

    # Simulate 10 shadow comparisons where candidate wins
    for i in range(10):
        result = ShadowResult(
            task_id=f"T-{i}",
            task_type="task",
            production_model="hermes-3b",
            production_response="ok",
            production_latency_seconds=1.0,
            production_passed=True,
            candidate_model="qwen3-8b",
            candidate_response="ok",
            candidate_latency_seconds=0.8,
            candidate_passed=True,
            responses_agree=True,
        )
        router.record(result)

    # Shadow says READY (>80% upgrade-worthy)
    assert router.upgrade_worthy_rate >= 0.8
    assert "READY" in router.format_report()

    # Promote using shadow data
    mgr = ModelPromotionManager(current_default="hermes-3b")
    record = mgr.promote_from_shadow("qwen3-8b", shadow=router, reason="PO approved")
    assert record.promoted_model == "qwen3-8b"
    assert record.shadow_comparisons == 10
    assert record.shadow_agreement_rate == 1.0

    # Tier progresses
    tracker = TierProgressionTracker()
    tracker.set_tier("qwen3-8b", "trainee-validated")
    assert tracker.get_tier("qwen3-8b") == "trainee-validated"

    # Router gets the promoted model
    assert mgr.routing_model() == "qwen3-8b"


def test_upgrade_not_ready():
    """Shadow results below 80% — no promotion."""
    router = ShadowRouter(production_model="hermes-3b", candidate_model="qwen3-8b")

    # 10 comparisons, only 5 where candidate passes
    for i in range(10):
        result = ShadowResult(
            task_id=f"T-{i}",
            task_type="task",
            production_model="hermes-3b",
            production_response="ok",
            production_latency_seconds=1.0,
            production_passed=True,
            candidate_model="qwen3-8b",
            candidate_response="ok" if i < 5 else "fail",
            candidate_latency_seconds=0.8,
            candidate_passed=(i < 5),
            responses_agree=(i < 5),
        )
        router.record(result)

    assert router.upgrade_worthy_rate < 0.8
    assert "NOT READY" in router.format_report()


def test_upgrade_rollback():
    """Post-promotion health degrades → rollback → router reverts."""
    mgr = ModelPromotionManager(current_default="hermes-3b")

    # Record pre-promotion approvals (establishes baseline)
    for _ in range(10):
        mgr.record_approval("hermes-3b", "task", approved=True)

    # Promote — captures pre_promotion_approval_rate from tracker
    record = mgr.promote("qwen3-8b", reason="test")
    assert mgr.routing_model() == "qwen3-8b"
    assert record.pre_promotion_approval_rate == 1.0  # 100% before

    # Post-promotion: new model fails everything
    for _ in range(10):
        mgr.record_approval("qwen3-8b", "task", approved=False)

    # Health check: post-promotion rate = 0%, pre was 100%
    health = mgr.promotion_health()
    assert health is not None
    assert health["status"] in ("degraded", "unhealthy")

    # Rollback
    rolled = mgr.rollback(reason="health degraded")
    assert rolled is not None
    assert mgr.routing_model() == "hermes-3b"


def test_upgrade_tier_gate():
    """Model can't skip tiers (trainee can't go to expert)."""
    tracker = TierProgressionTracker()

    # Start as trainee
    tracker.set_tier("qwen3-8b", "trainee")
    assert tracker.get_tier("qwen3-8b") == "trainee"

    # Can advance to trainee-validated
    tracker.set_tier("qwen3-8b", "trainee-validated")
    assert tracker.get_tier("qwen3-8b") == "trainee-validated"

    # Can advance to standard
    tracker.set_tier("qwen3-8b", "standard")
    assert tracker.get_tier("qwen3-8b") == "standard"

    # Can advance to expert
    tracker.set_tier("qwen3-8b", "expert")
    assert tracker.get_tier("qwen3-8b") == "expert"
