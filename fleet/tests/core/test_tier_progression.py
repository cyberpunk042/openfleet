"""Tests for confidence tier progression tracking (M-MU07)."""

import pytest

from fleet.core.tier_progression import (
    MIN_SAMPLES,
    ModelTierState,
    PerformanceRecord,
    STANDARD_THRESHOLD,
    TierProgressionTracker,
    VALID_TIERS,
    VALIDATION_THRESHOLD,
)


# ─── ModelTierState ────────────────────────────────────────────


def test_tier_state_defaults():
    s = ModelTierState(model="hermes-3b")
    assert s.current_tier == "trainee"
    assert s.tier_overrides == {}


def test_tier_state_effective_tier():
    s = ModelTierState(model="qwen3-8b", current_tier="trainee")
    assert s.effective_tier() == "trainee"
    assert s.effective_tier("heartbeat") == "trainee"


def test_tier_state_override():
    s = ModelTierState(
        model="qwen3-8b", current_tier="trainee",
        tier_overrides={"heartbeat": "standard"},
    )
    assert s.effective_tier("heartbeat") == "standard"
    assert s.effective_tier("review") == "trainee"  # Falls back to default


def test_tier_state_to_dict():
    s = ModelTierState(
        model="qwen3-8b", current_tier="trainee-validated",
        tier_overrides={"heartbeat": "standard"},
    )
    d = s.to_dict()
    assert d["model"] == "qwen3-8b"
    assert d["current_tier"] == "trainee-validated"
    assert d["tier_overrides"]["heartbeat"] == "standard"


# ─── Recording ─────────────────────────────────────────────────


def test_record():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    assert t.total_records == 1


def test_record_creates_tier_state():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    assert t.get_tier("qwen3-8b") == "trainee"


def test_record_max_cap():
    t = TierProgressionTracker(max_records=5)
    for i in range(10):
        t.record_approval("qwen3-8b", "heartbeat", True)
    assert t.total_records == 5


# ─── Approval Rate ─────────────────────────────────────────────


def test_approval_rate_overall():
    t = TierProgressionTracker()
    for _ in range(8):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(2):
        t.record_approval("qwen3-8b", "heartbeat", False)
    assert t.approval_rate("qwen3-8b") == 0.8


def test_approval_rate_by_task_type():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.record_approval("qwen3-8b", "review", False)
    assert t.approval_rate("qwen3-8b", "heartbeat") == 1.0
    assert t.approval_rate("qwen3-8b", "review") == 0.0


def test_approval_rate_empty():
    t = TierProgressionTracker()
    assert t.approval_rate("nonexistent") == 0.0


def test_challenge_pass_rate():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True, challenge_passed=True)
    t.record_approval("qwen3-8b", "heartbeat", True, challenge_passed=True)
    t.record_approval("qwen3-8b", "heartbeat", False, challenge_passed=False)
    assert abs(t.challenge_pass_rate("qwen3-8b") - 2 / 3) < 0.01


def test_sample_count():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.record_approval("qwen3-8b", "review", True)
    assert t.sample_count("qwen3-8b") == 2
    assert t.sample_count("qwen3-8b", "heartbeat") == 1


def test_task_types_for_model():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.record_approval("qwen3-8b", "review", True)
    t.record_approval("qwen3-8b", "heartbeat", True)
    types = t.task_types_for_model("qwen3-8b")
    assert set(types) == {"heartbeat", "review"}


# ─── Tier Management ──────────────────────────────────────────


def test_get_tier_default():
    t = TierProgressionTracker()
    assert t.get_tier("unknown") == "trainee"


def test_set_tier():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)  # Create state
    state = t.set_tier("qwen3-8b", "trainee-validated")
    assert state.current_tier == "trainee-validated"
    assert t.get_tier("qwen3-8b") == "trainee-validated"


def test_set_tier_invalid():
    t = TierProgressionTracker()
    with pytest.raises(ValueError, match="Invalid tier"):
        t.set_tier("qwen3-8b", "invalid-tier")


def test_set_task_tier():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.set_task_tier("qwen3-8b", "heartbeat", "standard")
    assert t.get_effective_tier("qwen3-8b", "heartbeat") == "standard"
    assert t.get_effective_tier("qwen3-8b", "review") == "trainee"


def test_set_task_tier_invalid():
    t = TierProgressionTracker()
    with pytest.raises(ValueError, match="Invalid tier"):
        t.set_task_tier("qwen3-8b", "heartbeat", "mega-expert")


def test_clear_task_tier():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.set_task_tier("qwen3-8b", "heartbeat", "standard")
    assert t.get_effective_tier("qwen3-8b", "heartbeat") == "standard"
    t.clear_task_tier("qwen3-8b", "heartbeat")
    assert t.get_effective_tier("qwen3-8b", "heartbeat") == "trainee"


def test_clear_task_tier_nonexistent():
    t = TierProgressionTracker()
    # Should not raise
    t.clear_task_tier("unknown", "heartbeat")


def test_effective_tier_unknown_model():
    t = TierProgressionTracker()
    assert t.get_effective_tier("unknown") == "trainee"
    assert t.get_effective_tier("unknown", "heartbeat") == "trainee"


# ─── Tier Readiness ───────────────────────────────────────────


def test_readiness_insufficient_samples():
    t = TierProgressionTracker()
    for _ in range(MIN_SAMPLES - 1):
        t.record_approval("qwen3-8b", "heartbeat", True)
    r = t.tier_readiness("qwen3-8b")
    assert not r["meets_min_samples"]
    assert "Need" in r.get("note", "")


def test_readiness_trainee():
    t = TierProgressionTracker()
    # 50% approval — below validation threshold
    for _ in range(MIN_SAMPLES):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(MIN_SAMPLES):
        t.record_approval("qwen3-8b", "heartbeat", False)
    r = t.tier_readiness("qwen3-8b")
    assert r["eligible_for"] == "trainee"


def test_readiness_trainee_validated():
    t = TierProgressionTracker()
    # 75% approval — above VALIDATION (70%) but below STANDARD (85%)
    for _ in range(15):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(5):
        t.record_approval("qwen3-8b", "heartbeat", False)
    r = t.tier_readiness("qwen3-8b")
    assert r["eligible_for"] == "trainee-validated"


def test_readiness_standard():
    t = TierProgressionTracker()
    # 90% approval — above STANDARD (85%)
    for _ in range(18):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(2):
        t.record_approval("qwen3-8b", "heartbeat", False)
    r = t.tier_readiness("qwen3-8b")
    assert r["eligible_for"] == "standard"


def test_readiness_per_task_type():
    t = TierProgressionTracker()
    # Heartbeat: 100% (standard-eligible)
    for _ in range(MIN_SAMPLES):
        t.record_approval("qwen3-8b", "heartbeat", True)
    # Review: 50% (trainee)
    for _ in range(MIN_SAMPLES // 2):
        t.record_approval("qwen3-8b", "review", True)
    for _ in range(MIN_SAMPLES // 2):
        t.record_approval("qwen3-8b", "review", False)
    r = t.tier_readiness("qwen3-8b")
    assert "by_task_type" in r
    assert r["by_task_type"]["heartbeat"]["eligible_for"] == "standard"
    assert r["by_task_type"]["review"]["eligible_for"] == "trainee"


# ─── Performance Window ───────────────────────────────────────


def test_performance_window_empty():
    t = TierProgressionTracker()
    assert t.performance_window("qwen3-8b") == []


def test_performance_window_small():
    t = TierProgressionTracker()
    for _ in range(5):
        t.record_approval("qwen3-8b", "heartbeat", True)
    windows = t.performance_window("qwen3-8b", window_size=20)
    assert len(windows) == 1
    assert windows[0] == 1.0


def test_performance_window_multiple():
    t = TierProgressionTracker()
    # Window 1: all pass
    for _ in range(10):
        t.record_approval("qwen3-8b", "heartbeat", True)
    # Window 2: half pass
    for _ in range(5):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(5):
        t.record_approval("qwen3-8b", "heartbeat", False)
    windows = t.performance_window("qwen3-8b", window_size=10)
    assert len(windows) == 2
    assert windows[0] == 1.0
    assert windows[1] == 0.5


# ─── Models List ───────────────────────────────────────────────


def test_models():
    t = TierProgressionTracker()
    t.record_approval("qwen3-8b", "heartbeat", True)
    t.record_approval("hermes-3b", "heartbeat", True)
    assert set(t.models()) == {"qwen3-8b", "hermes-3b"}


def test_models_empty():
    t = TierProgressionTracker()
    assert t.models() == []


# ─── Summary & Report ─────────────────────────────────────────


def test_summary():
    t = TierProgressionTracker()
    for _ in range(MIN_SAMPLES):
        t.record_approval("qwen3-8b", "heartbeat", True)
    s = t.summary()
    assert s["tracked_models"] == 1
    assert s["total_records"] == MIN_SAMPLES
    assert "qwen3-8b" in s["models"]
    assert s["models"]["qwen3-8b"]["current_tier"] == "trainee"


def test_summary_empty():
    t = TierProgressionTracker()
    s = t.summary()
    assert s["total_records"] == 0
    assert s["tracked_models"] == 0


def test_format_report():
    t = TierProgressionTracker()
    for _ in range(MIN_SAMPLES):
        t.record_approval("qwen3-8b", "heartbeat", True)
    for _ in range(MIN_SAMPLES):
        t.record_approval("hermes-3b", "heartbeat", True)
    report = t.format_report()
    assert "Confidence Tier Progression Report" in report
    assert "qwen3-8b" in report
    assert "hermes-3b" in report
    assert "trainee" in report


def test_format_report_empty():
    t = TierProgressionTracker()
    report = t.format_report()
    assert "Confidence Tier Progression Report" in report


# ─── Valid Tiers ───────────────────────────────────────────────


def test_valid_tiers():
    assert "trainee" in VALID_TIERS
    assert "trainee-validated" in VALID_TIERS
    assert "standard" in VALID_TIERS
    assert "expert" in VALID_TIERS