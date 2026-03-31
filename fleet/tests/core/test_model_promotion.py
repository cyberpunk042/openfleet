"""Tests for default model promotion (M-MU04)."""

import time

from fleet.core.model_promotion import (
    ApprovalEntry,
    ApprovalTracker,
    ModelPromotionManager,
    PromotionRecord,
)


# ─── PromotionRecord ──────────────────────────────────────────


def test_promotion_record_defaults():
    r = PromotionRecord(promoted_model="qwen3-8b", previous_model="hermes-3b")
    assert r.promoted_by == "PO"
    assert r.promoted_at > 0
    assert not r.rollback


def test_promotion_record_to_dict():
    r = PromotionRecord(
        promoted_model="qwen3-8b", previous_model="hermes-3b",
        reason="Shadow routing showed 90% agreement",
        shadow_comparisons=50, shadow_agreement_rate=0.9,
    )
    d = r.to_dict()
    assert d["promoted_model"] == "qwen3-8b"
    assert d["previous_model"] == "hermes-3b"
    assert d["shadow_comparisons"] == 50
    assert d["shadow_agreement_rate"] == 0.9


# ─── ApprovalTracker ───────────────────────────────────────────


def test_tracker_record():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", True)
    assert t.total_entries == 1


def test_tracker_approval_rate():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", False)
    assert abs(t.approval_rate("hermes-3b") - 2 / 3) < 0.01


def test_tracker_approval_rate_by_model():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("qwen3-8b", "heartbeat", False)
    assert t.approval_rate("hermes-3b") == 1.0
    assert t.approval_rate("qwen3-8b") == 0.0


def test_tracker_approval_rate_all():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("qwen3-8b", "heartbeat", False)
    assert t.approval_rate() == 0.5


def test_tracker_by_task_type():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "review", False)
    rates = t.approval_rate_by_task_type("hermes-3b")
    assert rates["heartbeat"] == 1.0
    assert rates["review"] == 0.0


def test_tracker_empty():
    t = ApprovalTracker()
    assert t.approval_rate() == 0.0
    assert t.approval_rate("nonexistent") == 0.0
    assert t.approval_rate_by_task_type() == {}


def test_tracker_max_entries():
    t = ApprovalTracker(max_entries=3)
    for i in range(5):
        t.record_approval("m", "t", True)
    assert t.total_entries == 3


def test_tracker_since():
    t = ApprovalTracker()
    before = time.time()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", False)
    after = time.time()
    t.record_approval("hermes-3b", "heartbeat", True)

    # Entries since 'after' should only include the last one
    entries = t.entries_since(after)
    assert len(entries) == 1
    assert entries[0].approved is True


def test_tracker_approval_rate_since():
    t = ApprovalTracker()
    t.record_approval("hermes-3b", "heartbeat", False)
    cutoff = time.time()
    t.record_approval("hermes-3b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", True)
    assert t.approval_rate_since(cutoff, "hermes-3b") == 1.0


def test_tracker_approval_rate_since_empty():
    t = ApprovalTracker()
    assert t.approval_rate_since(time.time()) == 0.0


# ─── ModelPromotionManager ─────────────────────────────────────


def test_manager_init():
    m = ModelPromotionManager()
    assert m.current_default == "hermes-3b"
    assert m.fallback_model == "hermes-3b"


def test_manager_promote():
    m = ModelPromotionManager("hermes-3b")
    record = m.promote("qwen3-8b", reason="Shadow passed")
    assert m.current_default == "qwen3-8b"
    assert m.fallback_model == "hermes-3b"
    assert record.promoted_model == "qwen3-8b"
    assert record.previous_model == "hermes-3b"


def test_manager_promote_updates_fallback():
    m = ModelPromotionManager("hermes-3b", fallback_model="phi-2")
    m.promote("qwen3-8b")
    assert m.current_default == "qwen3-8b"
    assert m.fallback_model == "hermes-3b"  # Previous default becomes fallback


def test_manager_promote_with_shadow_data():
    m = ModelPromotionManager()
    record = m.promote(
        "qwen3-8b",
        shadow_comparisons=50,
        shadow_agreement_rate=0.92,
    )
    assert record.shadow_comparisons == 50
    assert record.shadow_agreement_rate == 0.92


def test_manager_promote_records_pre_rate():
    m = ModelPromotionManager()
    m.record_approval("hermes-3b", "heartbeat", True)
    m.record_approval("hermes-3b", "heartbeat", True)
    m.record_approval("hermes-3b", "review", False)
    record = m.promote("qwen3-8b")
    assert abs(record.pre_promotion_approval_rate - 2 / 3) < 0.01


def test_manager_rollback():
    m = ModelPromotionManager()
    m.promote("qwen3-8b")
    assert m.current_default == "qwen3-8b"
    rolled = m.rollback("Approval rate dropped")
    assert rolled is not None
    assert m.current_default == "hermes-3b"
    assert m.fallback_model == "qwen3-8b"
    assert rolled.rollback is True
    assert rolled.rollback_reason == "Approval rate dropped"


def test_manager_rollback_no_promotions():
    m = ModelPromotionManager()
    assert m.rollback() is None


def test_manager_rollback_already_rolled_back():
    m = ModelPromotionManager()
    m.promote("qwen3-8b")
    m.rollback("reason1")
    assert m.rollback("reason2") is None


def test_manager_promotion_history():
    m = ModelPromotionManager()
    m.promote("qwen3-8b")
    m.promote("llama-3.3-8b")
    assert len(m.promotion_history) == 2
    assert m.promotion_history[0].promoted_model == "qwen3-8b"
    assert m.promotion_history[1].promoted_model == "llama-3.3-8b"


def test_manager_last_promotion():
    m = ModelPromotionManager()
    assert m.last_promotion is None
    m.promote("qwen3-8b")
    assert m.last_promotion is not None
    assert m.last_promotion.promoted_model == "qwen3-8b"


# ─── Post-Promotion Monitoring ─────────────────────────────────


def test_post_promotion_approval_rate():
    m = ModelPromotionManager()
    m.record_approval("hermes-3b", "heartbeat", True)
    m.promote("qwen3-8b")
    m.record_approval("qwen3-8b", "heartbeat", True)
    m.record_approval("qwen3-8b", "heartbeat", True)
    m.record_approval("qwen3-8b", "review", False)
    rate = m.post_promotion_approval_rate()
    assert abs(rate - 2 / 3) < 0.01


def test_post_promotion_no_promotions():
    m = ModelPromotionManager()
    m.record_approval("hermes-3b", "heartbeat", True)
    assert m.post_promotion_approval_rate() == 1.0


# ─── Promotion Health ──────────────────────────────────────────


def test_promotion_health_no_promotion():
    m = ModelPromotionManager()
    h = m.promotion_health()
    assert h["status"] == "no_promotion"


def test_promotion_health_healthy():
    m = ModelPromotionManager()
    # Pre-promotion: 80% approval
    for _ in range(4):
        m.record_approval("hermes-3b", "heartbeat", True)
    m.record_approval("hermes-3b", "heartbeat", False)
    m.promote("qwen3-8b")
    # Post-promotion: 90% approval (better)
    for _ in range(9):
        m.record_approval("qwen3-8b", "heartbeat", True)
    m.record_approval("qwen3-8b", "heartbeat", False)
    h = m.promotion_health()
    assert h["status"] == "healthy"


def test_promotion_health_degraded():
    m = ModelPromotionManager()
    # Pre: 100%
    for _ in range(5):
        m.record_approval("hermes-3b", "heartbeat", True)
    m.promote("qwen3-8b")
    # Post: 75% (within 30% but below 90% of baseline)
    for _ in range(3):
        m.record_approval("qwen3-8b", "heartbeat", True)
    m.record_approval("qwen3-8b", "heartbeat", False)
    h = m.promotion_health()
    assert h["status"] == "degraded"


def test_promotion_health_unhealthy():
    m = ModelPromotionManager()
    # Pre: 100%
    for _ in range(5):
        m.record_approval("hermes-3b", "heartbeat", True)
    m.promote("qwen3-8b")
    # Post: 20% (well below 70% of baseline)
    m.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(4):
        m.record_approval("qwen3-8b", "heartbeat", False)
    h = m.promotion_health()
    assert h["status"] == "unhealthy"


def test_promotion_health_rolled_back():
    m = ModelPromotionManager()
    m.promote("qwen3-8b")
    m.rollback("bad")
    h = m.promotion_health()
    assert h["status"] == "rolled_back"


# ─── Summary & Report ──────────────────────────────────────────


def test_summary():
    m = ModelPromotionManager()
    m.record_approval("hermes-3b", "heartbeat", True)
    m.promote("qwen3-8b")
    m.record_approval("qwen3-8b", "heartbeat", True)
    s = m.summary()
    assert s["current_default"] == "qwen3-8b"
    assert s["fallback_model"] == "hermes-3b"
    assert s["total_promotions"] == 1
    assert s["total_rollbacks"] == 0


def test_summary_with_rollback():
    m = ModelPromotionManager()
    m.promote("qwen3-8b")
    m.rollback("dropped")
    s = m.summary()
    assert s["total_rollbacks"] == 1


def test_format_report():
    m = ModelPromotionManager()
    m.record_approval("hermes-3b", "heartbeat", True)
    m.promote("qwen3-8b")
    m.record_approval("qwen3-8b", "heartbeat", True)
    m.record_approval("qwen3-8b", "review", False)
    report = m.format_report()
    assert "Model Promotion Status" in report
    assert "qwen3-8b" in report
    assert "hermes-3b" in report


def test_format_report_no_promotion():
    m = ModelPromotionManager()
    report = m.format_report()
    assert "Model Promotion Status" in report
    assert "hermes-3b" in report