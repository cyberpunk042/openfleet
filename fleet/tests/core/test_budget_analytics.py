"""Tests for budget analytics (M-BM06)."""

from fleet.core.budget_analytics import (
    BudgetAnalytics,
    BudgetEvent,
    BudgetModeMetrics,
    ModeComparison,
)


# ─── Helpers ──────────────────────────────────────────────────────


def _event(
    mode: str = "standard",
    task_type: str = "task",
    cost: float = 0.10,
    sp: int = 2,
    backend: str = "claude-code",
    model: str = "sonnet",
    approved: bool = None,
    challenge_passed: bool = None,
    task_id: str = "t1",
    duration: int = 60,
) -> BudgetEvent:
    return BudgetEvent(
        task_id=task_id,
        budget_mode=mode,
        task_type=task_type,
        story_points=sp,
        cost_usd=cost,
        duration_seconds=duration,
        backend=backend,
        model=model,
        approved=approved,
        challenge_passed=challenge_passed,
    )


# ─── Recording ───────────────────────────────────────────────────


def test_record_event():
    a = BudgetAnalytics()
    a.record(_event())
    assert a.total_events == 1


def test_record_many():
    a = BudgetAnalytics()
    a.record_many([_event(task_id=f"t{i}") for i in range(5)])
    assert a.total_events == 5


def test_max_events_cap():
    a = BudgetAnalytics(max_events=3)
    for i in range(5):
        a.record(_event(task_id=f"t{i}"))
    assert a.total_events == 3


def test_total_cost():
    a = BudgetAnalytics()
    a.record_many([_event(cost=0.10), _event(cost=0.25)])
    assert abs(a.total_cost_usd - 0.35) < 0.001


# ─── Per-Mode Metrics ───────────────────────────────────────────


def test_mode_metrics_basic():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", cost=0.30, duration=60, task_id="t1"),
        _event(mode="standard", cost=0.20, duration=120, task_id="t2"),
        _event(mode="economic", cost=0.05, duration=30, task_id="t3"),
    ])
    m = a.mode_metrics("standard")
    assert m.total_tasks == 2
    assert abs(m.total_cost_usd - 0.50) < 0.001
    assert m.avg_duration_seconds == 90.0


def test_mode_metrics_empty():
    a = BudgetAnalytics()
    m = a.mode_metrics("blitz")
    assert m.total_tasks == 0
    assert m.avg_cost_per_task == 0.0


def test_mode_metrics_approval():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", approved=True, task_id="t1"),
        _event(mode="standard", approved=True, task_id="t2"),
        _event(mode="standard", approved=False, task_id="t3"),
    ])
    m = a.mode_metrics("standard")
    assert m.approved == 2
    assert m.rejected == 1
    assert abs(m.approval_rate - 2 / 3) < 0.01


def test_mode_metrics_challenge():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", challenge_passed=True, task_id="t1"),
        _event(mode="standard", challenge_passed=False, task_id="t2"),
    ])
    m = a.mode_metrics("standard")
    assert m.challenge_passed == 1
    assert m.challenge_failed == 1
    assert m.challenge_pass_rate == 0.5


def test_all_mode_metrics():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", cost=0.50, task_id="t1"),
        _event(mode="economic", cost=0.10, task_id="t2"),
        _event(mode="blitz", cost=0.80, task_id="t3"),
    ])
    metrics = a.all_mode_metrics()
    assert len(metrics) == 3
    assert metrics[0].mode == "blitz"  # Highest cost first


def test_mode_metrics_backends():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="economic", backend="localai", task_id="t1"),
        _event(mode="economic", backend="claude-code", task_id="t2"),
        _event(mode="economic", backend="localai", task_id="t3"),
    ])
    m = a.mode_metrics("economic")
    d = m.to_dict()
    assert d["top_backend"] == "localai"


# ─── Mode Comparison ────────────────────────────────────────────


def test_compare_modes_basic():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", cost=0.30, approved=True, task_id="t1"),
        _event(mode="standard", cost=0.40, approved=True, task_id="t2"),
        _event(mode="economic", cost=0.10, approved=True, task_id="t3"),
        _event(mode="economic", cost=0.05, approved=False, task_id="t4"),
    ])
    comp = a.compare_modes("standard", "economic")
    assert comp is not None
    assert comp.avg_cost_a == 0.35
    assert abs(comp.avg_cost_b - 0.075) < 0.001
    assert comp.cost_difference_pct > 0  # Economic is cheaper
    assert comp.approval_rate_a == 1.0
    assert comp.approval_rate_b == 0.5


def test_compare_modes_by_task_type():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", task_type="bug", cost=0.20, task_id="t1"),
        _event(mode="economic", task_type="bug", cost=0.05, task_id="t2"),
        _event(mode="standard", task_type="story", cost=0.50, task_id="t3"),
    ])
    comp = a.compare_modes("standard", "economic", task_type="bug")
    assert comp is not None
    assert comp.task_type == "bug"
    assert comp.count_a == 1
    assert comp.count_b == 1


def test_compare_modes_no_data():
    a = BudgetAnalytics()
    a.record(_event(mode="standard", task_id="t1"))
    comp = a.compare_modes("standard", "blitz")
    assert comp is None


def test_comparison_to_dict():
    comp = ModeComparison(
        task_type="task", mode_a="standard", mode_b="economic",
        avg_cost_a=0.30, avg_cost_b=0.10,
        approval_rate_a=0.9, approval_rate_b=0.8,
        count_a=10, count_b=5,
    )
    d = comp.to_dict()
    assert d["cost_savings_pct"] > 0
    assert d["quality_difference"] > 0  # standard has higher approval


# ─── Cost by Task Type ──────────────────────────────────────────


def test_cost_by_task_type():
    a = BudgetAnalytics()
    a.record_many([
        _event(task_type="bug", cost=0.10, task_id="t1"),
        _event(task_type="story", cost=0.50, task_id="t2"),
        _event(task_type="bug", cost=0.15, task_id="t3"),
    ])
    costs = a.cost_by_task_type()
    assert costs["story"] == 0.50
    assert costs["bug"] == 0.25


def test_cost_per_story_point():
    a = BudgetAnalytics()
    a.record_many([
        _event(sp=2, cost=0.20, task_id="t1"),
        _event(sp=5, cost=0.50, task_id="t2"),
        _event(sp=3, cost=0.30, task_id="t3"),
    ])
    # Total cost = 1.00, total SP = 10
    assert abs(a.cost_per_story_point() - 0.10) < 0.001


def test_cost_per_story_point_no_sp():
    a = BudgetAnalytics()
    a.record(_event(sp=0, cost=0.10, task_id="t1"))
    assert a.cost_per_story_point() == 0.0


# ─── Summary ────────────────────────────────────────────────────


def test_summary_empty():
    a = BudgetAnalytics()
    s = a.summary()
    assert s["total_events"] == 0
    assert s["total_cost_usd"] == 0.0


def test_summary_with_data():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", cost=0.30, task_type="bug", task_id="t1"),
        _event(mode="economic", cost=0.05, task_type="story", task_id="t2"),
    ])
    s = a.summary()
    assert s["total_events"] == 2
    assert len(s["modes"]) == 2
    assert "bug" in s["cost_by_task_type"]


# ─── Report ─────────────────────────────────────────────────────


def test_format_report():
    a = BudgetAnalytics()
    a.record_many([
        _event(mode="standard", cost=0.30, task_id="t1"),
        _event(mode="economic", cost=0.05, task_id="t2"),
    ])
    report = a.format_report()
    assert "Budget Analytics Report" in report
    assert "standard" in report
    assert "economic" in report


# ─── Serialization ──────────────────────────────────────────────


def test_mode_metrics_to_dict():
    m = BudgetModeMetrics(mode="standard", total_tasks=10, total_cost_usd=2.50)
    d = m.to_dict()
    assert d["mode"] == "standard"
    assert d["avg_cost_per_task"] == 0.25


def test_event_to_dict():
    e = _event(mode="economic", cost=0.05)
    d = e.to_dict()
    assert d["mode"] == "economic"
    assert d["cost_usd"] == 0.05