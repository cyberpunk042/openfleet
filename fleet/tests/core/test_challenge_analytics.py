"""Tests for challenge analytics (M-IV08)."""

from fleet.core.challenge_analytics import (
    AgentMetrics,
    ChallengeAnalytics,
    ChallengeEvent,
    TeachingSignal,
    TierMetrics,
)


# ─── Helpers ──────────────────────────────────────────────────────


def _event(
    agent: str = "worker",
    tier: str = "standard",
    passed: bool = True,
    rounds: int = 1,
    findings: int = 0,
    categories: list[str] | None = None,
    severities: list[str] | None = None,
    task_id: str = "t1",
    challenge_type: str = "automated",
) -> ChallengeEvent:
    return ChallengeEvent(
        task_id=task_id,
        agent_name=agent,
        confidence_tier=tier,
        challenge_type=challenge_type,
        passed=passed,
        rounds_used=rounds,
        findings_count=findings,
        finding_categories=categories or [],
        finding_severities=severities or [],
    )


# ─── ChallengeEvent ─────────────────────────────────────────────


def test_event_to_dict():
    e = _event(agent="dev", tier="trainee", passed=False, findings=2,
               categories=["edge_case", "regression"])
    d = e.to_dict()
    assert d["agent"] == "dev"
    assert d["passed"] is False
    assert d["categories"] == ["edge_case", "regression"]


# ─── ChallengeAnalytics: Recording ──────────────────────────────


def test_record_event():
    a = ChallengeAnalytics()
    a.record(_event())
    assert a.total_events == 1


def test_record_many():
    a = ChallengeAnalytics()
    a.record_many([_event(task_id=f"t{i}") for i in range(5)])
    assert a.total_events == 5


def test_max_events_cap():
    a = ChallengeAnalytics(max_events=3)
    for i in range(5):
        a.record(_event(task_id=f"t{i}"))
    assert a.total_events == 3


# ─── Per-Agent Metrics ───────────────────────────────────────────


def test_agent_pass_rate_all_passed():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=True, task_id="t1"),
        _event(agent="dev", passed=True, task_id="t2"),
    ])
    m = a.agent_pass_rate("dev")
    assert m.pass_rate == 1.0
    assert m.total_challenges == 2


def test_agent_pass_rate_mixed():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=True, task_id="t1"),
        _event(agent="dev", passed=False, findings=2,
               categories=["edge_case", "regression"], task_id="t2"),
    ])
    m = a.agent_pass_rate("dev")
    assert m.pass_rate == 0.5
    assert m.failed == 1
    assert m.total_findings == 2


def test_agent_pass_rate_unknown():
    a = ChallengeAnalytics()
    m = a.agent_pass_rate("nobody")
    assert m.total_challenges == 0
    assert m.pass_rate == 0.0


def test_all_agent_metrics():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=True, task_id="t1"),
        _event(agent="qa", passed=False, task_id="t2"),
        _event(agent="dev", passed=True, task_id="t3"),
    ])
    metrics = a.all_agent_metrics()
    assert len(metrics) == 2
    names = [m.agent_name for m in metrics]
    assert "dev" in names
    assert "qa" in names


def test_agent_avg_rounds():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", rounds=1, task_id="t1"),
        _event(agent="dev", rounds=3, task_id="t2"),
    ])
    m = a.agent_pass_rate("dev")
    assert m.avg_rounds == 2.0


def test_agent_top_categories():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=False, categories=["edge_case", "regression"], task_id="t1"),
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t2"),
    ])
    m = a.agent_pass_rate("dev")
    assert m.top_categories[0][0] == "edge_case"
    assert m.top_categories[0][1] == 2


# ─── Per-Tier Metrics ────────────────────────────────────────────


def test_tier_pass_rate():
    a = ChallengeAnalytics()
    a.record_many([
        _event(tier="trainee", passed=True, task_id="t1"),
        _event(tier="trainee", passed=False, task_id="t2"),
        _event(tier="trainee", passed=False, task_id="t3"),
    ])
    m = a.tier_pass_rate("trainee")
    assert abs(m.pass_rate - 1/3) < 0.01
    assert m.failed == 2


def test_all_tier_metrics():
    a = ChallengeAnalytics()
    a.record_many([
        _event(tier="expert", passed=True, task_id="t1"),
        _event(tier="trainee", passed=False, task_id="t2"),
    ])
    metrics = a.all_tier_metrics()
    assert len(metrics) == 2


def test_tier_unknown():
    a = ChallengeAnalytics()
    m = a.tier_pass_rate("nonexistent")
    assert m.total_challenges == 0


# ─── Common Findings ─────────────────────────────────────────────


def test_common_categories():
    a = ChallengeAnalytics()
    a.record_many([
        _event(categories=["edge_case", "regression"], task_id="t1"),
        _event(categories=["edge_case", "security"], task_id="t2"),
        _event(categories=["edge_case"], task_id="t3"),
    ])
    top = a.common_finding_categories(top_n=2)
    assert top[0] == ("edge_case", 3)


def test_common_severities():
    a = ChallengeAnalytics()
    a.record_many([
        _event(severities=["critical", "major"], task_id="t1"),
        _event(severities=["major", "minor"], task_id="t2"),
    ])
    sev = a.common_finding_severities()
    assert sev["major"] == 2
    assert sev["critical"] == 1


# ─── Teaching Signals ────────────────────────────────────────────


def test_teaching_signal_triggered():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t1"),
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t2"),
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t3"),
    ])
    signals = a.teaching_signals(min_failures=3)
    assert len(signals) == 1
    assert signals[0].agent_name == "dev"
    assert signals[0].category == "edge_case"
    assert signals[0].failure_count == 3
    assert "boundary" in signals[0].suggestion.lower()


def test_teaching_signal_not_triggered_below_threshold():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t1"),
        _event(agent="dev", passed=False, categories=["edge_case"], task_id="t2"),
    ])
    signals = a.teaching_signals(min_failures=3)
    assert len(signals) == 0


def test_teaching_signal_multiple_agents():
    a = ChallengeAnalytics()
    for i in range(4):
        a.record(_event(agent="dev", passed=False, categories=["security"], task_id=f"d{i}"))
    for i in range(3):
        a.record(_event(agent="qa", passed=False, categories=["regression"], task_id=f"q{i}"))
    signals = a.teaching_signals(min_failures=3)
    assert len(signals) == 2
    assert signals[0].failure_count >= signals[1].failure_count  # Sorted by count


def test_teaching_signal_passed_events_ignored():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", passed=True, categories=["edge_case"], task_id="t1"),
        _event(agent="dev", passed=True, categories=["edge_case"], task_id="t2"),
        _event(agent="dev", passed=True, categories=["edge_case"], task_id="t3"),
    ])
    signals = a.teaching_signals(min_failures=3)
    assert len(signals) == 0  # Passed events don't count


# ─── Summary ─────────────────────────────────────────────────────


def test_summary_empty():
    a = ChallengeAnalytics()
    s = a.summary()
    assert s["total_challenges"] == 0
    assert s["overall_pass_rate"] == 0.0


def test_summary_with_data():
    a = ChallengeAnalytics()
    a.record_many([
        _event(agent="dev", tier="standard", passed=True, rounds=1, task_id="t1"),
        _event(agent="dev", tier="standard", passed=False, rounds=2,
               findings=3, categories=["edge_case", "regression", "security"],
               task_id="t2"),
        _event(agent="qa", tier="trainee", passed=True, rounds=1, task_id="t3"),
    ])
    s = a.summary()
    assert s["total_challenges"] == 3
    assert abs(s["overall_pass_rate"] - 2/3) < 0.01
    assert abs(s["avg_rounds"] - 4/3) < 0.01
    assert s["total_findings"] == 3
    assert len(s["agents"]) == 2
    assert len(s["tiers"]) == 2


# ─── Serialization ──────────────────────────────────────────────


def test_agent_metrics_to_dict():
    m = AgentMetrics(
        agent_name="dev", total_challenges=10, passed=8, failed=2,
        pass_rate=0.8, avg_rounds=1.5, total_findings=5,
        top_categories=[("edge_case", 3), ("regression", 2)],
    )
    d = m.to_dict()
    assert d["agent"] == "dev"
    assert d["pass_rate"] == 0.8


def test_tier_metrics_to_dict():
    m = TierMetrics(
        tier="trainee", total_challenges=5, passed=2, failed=3,
        pass_rate=0.4, avg_rounds=2.5,
    )
    d = m.to_dict()
    assert d["tier"] == "trainee"
    assert d["pass_rate"] == 0.4


def test_teaching_signal_to_dict():
    s = TeachingSignal(
        agent_name="dev", category="edge_case",
        failure_count=5, suggestion="Review boundaries",
    )
    d = s.to_dict()
    assert d["agent"] == "dev"
    assert d["failures"] == 5