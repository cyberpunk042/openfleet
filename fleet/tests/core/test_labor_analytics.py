"""Tests for labor analytics (M-LA07)."""

from fleet.core.labor_analytics import (
    AgentCostMetrics,
    LaborAnalytics,
    ModelCostMetrics,
    TierCostMetrics,
)
from fleet.core.labor_stamp import LaborStamp


# ─── Helpers ──────────────────────────────────────────────────────


def _stamp(
    agent: str = "dev",
    model: str = "opus",
    backend: str = "claude-code",
    tier: str = "expert",
    cost: float = 0.10,
    duration: int = 60,
    tokens: int = 500,
    budget_mode: str = "standard",
    challenge_rounds: int = 0,
) -> LaborStamp:
    return LaborStamp(
        agent_name=agent,
        backend=backend,
        model=model,
        confidence_tier=tier,
        estimated_cost_usd=cost,
        duration_seconds=duration,
        estimated_tokens=tokens,
        budget_mode=budget_mode,
        challenge_rounds_survived=challenge_rounds,
    )


# ─── Recording ───────────────────────────────────────────────────


def test_record_stamp():
    a = LaborAnalytics()
    a.record(_stamp())
    assert a.total_stamps == 1


def test_record_many():
    a = LaborAnalytics()
    a.record_many([_stamp() for _ in range(5)])
    assert a.total_stamps == 5


def test_max_stamps_cap():
    a = LaborAnalytics(max_stamps=3)
    for _ in range(5):
        a.record(_stamp())
    assert a.total_stamps == 3


def test_total_cost():
    a = LaborAnalytics()
    a.record_many([_stamp(cost=0.10), _stamp(cost=0.25)])
    assert abs(a.total_cost_usd - 0.35) < 0.001


# ─── Per-Agent Metrics ───────────────────────────────────────────


def test_agent_metrics_basic():
    a = LaborAnalytics()
    a.record_many([
        _stamp(agent="dev", cost=0.10, duration=60),
        _stamp(agent="dev", cost=0.20, duration=120),
        _stamp(agent="qa", cost=0.05, duration=30),
    ])
    m = a.agent_metrics("dev")
    assert m.total_tasks == 2
    assert abs(m.total_cost_usd - 0.30) < 0.001
    assert m.avg_duration_seconds == 90.0


def test_agent_metrics_empty():
    a = LaborAnalytics()
    m = a.agent_metrics("nobody")
    assert m.total_tasks == 0
    assert m.avg_cost_per_task == 0.0
    assert m.approval_rate == 0.0


def test_agent_primary_model():
    a = LaborAnalytics()
    a.record_many([
        _stamp(agent="dev", model="opus"),
        _stamp(agent="dev", model="sonnet"),
        _stamp(agent="dev", model="opus"),
    ])
    m = a.agent_metrics("dev")
    assert m.primary_model == "opus"


def test_all_agent_metrics_sorted():
    a = LaborAnalytics()
    a.record_many([
        _stamp(agent="dev", cost=0.50),
        _stamp(agent="qa", cost=0.10),
        _stamp(agent="ops", cost=0.30),
    ])
    metrics = a.all_agent_metrics()
    assert len(metrics) == 3
    assert metrics[0].agent_name == "dev"  # Highest cost first


# ─── Per-Model Metrics ───────────────────────────────────────────


def test_model_metrics_basic():
    a = LaborAnalytics()
    a.record_many([
        _stamp(model="opus", cost=0.30),
        _stamp(model="opus", cost=0.20),
        _stamp(model="sonnet", cost=0.05),
    ])
    m = a.model_metrics("opus")
    assert m.total_tasks == 2
    assert abs(m.total_cost_usd - 0.50) < 0.001


def test_model_metrics_challenge_rounds():
    a = LaborAnalytics()
    a.record_many([
        _stamp(model="hermes-3b", challenge_rounds=2),
        _stamp(model="hermes-3b", challenge_rounds=4),
    ])
    m = a.model_metrics("hermes-3b")
    assert m.avg_challenge_rounds == 3.0


def test_all_model_metrics():
    a = LaborAnalytics()
    a.record_many([
        _stamp(model="opus", cost=0.50),
        _stamp(model="sonnet", cost=0.10),
    ])
    metrics = a.all_model_metrics()
    assert len(metrics) == 2
    assert metrics[0].model == "opus"


# ─── Per-Tier Metrics ────────────────────────────────────────────


def test_tier_metrics_expert():
    a = LaborAnalytics()
    a.record_many([
        _stamp(tier="expert", cost=0.30),
        _stamp(tier="expert", cost=0.20),
    ])
    m = a.tier_metrics("expert")
    assert m.total_tasks == 2
    assert m.challenge_required == 0  # Expert doesn't require challenge


def test_tier_metrics_trainee_challenge():
    a = LaborAnalytics()
    a.record_many([
        _stamp(tier="trainee", challenge_rounds=2),
        _stamp(tier="trainee", challenge_rounds=0),
        _stamp(tier="trainee", challenge_rounds=1),
    ])
    m = a.tier_metrics("trainee")
    assert m.challenge_required == 3
    assert m.challenge_passed == 2  # Two survived at least 1 round
    assert abs(m.challenge_pass_rate - 2 / 3) < 0.01


def test_tier_metrics_community():
    a = LaborAnalytics()
    a.record(_stamp(tier="community", challenge_rounds=1))
    m = a.tier_metrics("community")
    assert m.challenge_required == 1
    assert m.challenge_passed == 1


def test_all_tier_metrics():
    a = LaborAnalytics()
    a.record_many([
        _stamp(tier="expert"),
        _stamp(tier="trainee"),
        _stamp(tier="expert"),
    ])
    metrics = a.all_tier_metrics()
    assert len(metrics) == 2


# ─── Approval Tracking ──────────────────────────────────────────


def test_record_approval():
    a = LaborAnalytics()
    s = _stamp(agent="dev")
    a.record(s)
    a.record_approval("dev", s.timestamp, True)
    m = a.agent_metrics("dev")
    assert m.approved == 1
    assert m.approval_rate == 1.0


def test_record_rejection():
    a = LaborAnalytics()
    s = _stamp(agent="dev")
    a.record(s)
    a.record_approval("dev", s.timestamp, False)
    m = a.agent_metrics("dev")
    assert m.rejected == 1
    assert m.approval_rate == 0.0


def test_mixed_approvals():
    a = LaborAnalytics()
    stamps = [_stamp(agent="dev") for _ in range(3)]
    # Need unique timestamps — they auto-generate but may be same
    for i, s in enumerate(stamps):
        s.timestamp = f"2026-03-31T10:00:0{i}"
        a.record(s)
    a.record_approval("dev", stamps[0].timestamp, True)
    a.record_approval("dev", stamps[1].timestamp, True)
    a.record_approval("dev", stamps[2].timestamp, False)
    m = a.agent_metrics("dev")
    assert m.approved == 2
    assert m.rejected == 1
    assert abs(m.approval_rate - 2 / 3) < 0.01


# ─── Cost Breakdowns ────────────────────────────────────────────


def test_cost_by_backend():
    a = LaborAnalytics()
    a.record_many([
        _stamp(backend="claude-code", cost=0.50),
        _stamp(backend="localai", cost=0.00),
        _stamp(backend="claude-code", cost=0.30),
    ])
    costs = a.cost_by_backend()
    assert costs["claude-code"] == 0.80
    assert costs["localai"] == 0.00


def test_cost_by_budget_mode():
    a = LaborAnalytics()
    a.record_many([
        _stamp(budget_mode="standard", cost=0.50),
        _stamp(budget_mode="economic", cost=0.10),
        _stamp(budget_mode="standard", cost=0.20),
    ])
    costs = a.cost_by_budget_mode()
    assert costs["standard"] == 0.70
    assert costs["economic"] == 0.10


# ─── Summary ────────────────────────────────────────────────────


def test_summary_empty():
    a = LaborAnalytics()
    s = a.summary()
    assert s["total_stamps"] == 0
    assert s["total_cost_usd"] == 0.0
    assert s["overall_approval_rate"] == 0.0


def test_summary_with_data():
    a = LaborAnalytics()
    a.record_many([
        _stamp(agent="dev", model="opus", tier="expert", cost=0.30, backend="claude-code"),
        _stamp(agent="dev", model="sonnet", tier="standard", cost=0.10, backend="claude-code"),
        _stamp(agent="qa", model="hermes-3b", tier="trainee", cost=0.00, backend="localai"),
    ])
    s = a.summary()
    assert s["total_stamps"] == 3
    assert abs(s["total_cost_usd"] - 0.40) < 0.001
    assert len(s["agents"]) == 2
    assert len(s["models"]) == 3
    assert len(s["tiers"]) == 3


# ─── Markdown Report ────────────────────────────────────────────


def test_format_report():
    a = LaborAnalytics()
    a.record_many([
        _stamp(agent="dev", model="opus", cost=0.30),
        _stamp(agent="qa", model="sonnet", cost=0.10),
    ])
    report = a.format_report()
    assert "Labor Analytics Report" in report
    assert "dev" in report
    assert "opus" in report
    assert "$0.30" in report


def test_format_report_empty():
    a = LaborAnalytics()
    report = a.format_report()
    assert "Labor Analytics Report" in report
    assert "$0.00" in report


# ─── Serialization ──────────────────────────────────────────────


def test_agent_metrics_to_dict():
    m = AgentCostMetrics(agent_name="dev", total_tasks=5, total_cost_usd=1.50)
    d = m.to_dict()
    assert d["agent"] == "dev"
    assert d["avg_cost_per_task"] == 0.3


def test_model_metrics_to_dict():
    m = ModelCostMetrics(model="opus", total_tasks=3, total_cost_usd=0.90)
    d = m.to_dict()
    assert d["model"] == "opus"
    assert d["avg_cost_per_task"] == 0.3


def test_tier_metrics_to_dict():
    m = TierCostMetrics(tier="trainee", total_tasks=4, challenge_required=4, challenge_passed=3)
    d = m.to_dict()
    assert d["tier"] == "trainee"
    assert d["challenge_pass_rate"] == 0.75