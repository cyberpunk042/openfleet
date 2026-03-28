"""Tests for sprint velocity and metrics."""

from datetime import datetime, timedelta

from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.velocity import (
    compute_agent_metrics,
    compute_sprint_metrics,
    format_sprint_report,
)


def _task(
    id: str = "t1", status: str = "done", agent: str = "devops",
    plan_id: str = "s1", story_points: int = 3,
    created_at: datetime | None = None, updated_at: datetime | None = None,
    blocked: bool = False,
) -> Task:
    return Task(
        id=id, board_id="b1", title=f"Task {id}", status=TaskStatus(status),
        custom_fields=TaskCustomFields(
            agent_name=agent, plan_id=plan_id, sprint=plan_id,
            story_points=story_points,
        ),
        created_at=created_at, updated_at=updated_at,
        is_blocked=blocked,
    )


def test_sprint_metrics_all_done():
    now = datetime.now()
    tasks = [
        _task("t1", "done", created_at=now - timedelta(hours=5), updated_at=now),
        _task("t2", "done", created_at=now - timedelta(hours=3), updated_at=now),
        _task("t3", "done", created_at=now - timedelta(hours=1), updated_at=now),
    ]
    m = compute_sprint_metrics(tasks, "s1")
    assert m.total_tasks == 3
    assert m.done_tasks == 3
    assert m.completion_pct == 100.0
    assert m.is_complete
    assert m.total_story_points == 9
    assert m.done_story_points == 9


def test_sprint_metrics_partial():
    tasks = [
        _task("t1", "done", story_points=5),
        _task("t2", "in_progress", story_points=3),
        _task("t3", "inbox", story_points=8),
    ]
    m = compute_sprint_metrics(tasks, "s1")
    assert m.total_tasks == 3
    assert m.done_tasks == 1
    assert m.completion_pct < 50
    assert not m.is_complete
    assert m.done_story_points == 5
    assert m.total_story_points == 16


def test_sprint_metrics_cycle_time():
    now = datetime.now()
    tasks = [
        _task("t1", "done", created_at=now - timedelta(hours=4), updated_at=now),
        _task("t2", "done", created_at=now - timedelta(hours=2), updated_at=now),
    ]
    m = compute_sprint_metrics(tasks, "s1")
    assert m.avg_cycle_time_hours > 0
    assert m.min_cycle_time_hours <= m.avg_cycle_time_hours
    assert m.max_cycle_time_hours >= m.avg_cycle_time_hours


def test_sprint_metrics_blocked():
    tasks = [
        _task("t1", "inbox", blocked=True),
        _task("t2", "done"),
    ]
    m = compute_sprint_metrics(tasks, "s1")
    assert m.blocked_tasks == 1


def test_sprint_metrics_no_tasks():
    m = compute_sprint_metrics([], "nonexistent")
    assert m.total_tasks == 0
    assert m.completion_pct == 0.0


def test_agent_metrics():
    tasks = [
        _task("t1", "done", agent="devops", story_points=3),
        _task("t2", "done", agent="devops", story_points=5),
        _task("t3", "done", agent="software-engineer", story_points=2),
        _task("t4", "in_progress", agent="software-engineer"),
    ]
    metrics = compute_agent_metrics(tasks)
    assert len(metrics) == 2
    devops = next(m for m in metrics if m.agent_name == "devops")
    assert devops.tasks_completed == 2
    assert devops.story_points_completed == 8
    sw = next(m for m in metrics if m.agent_name == "software-engineer")
    assert sw.tasks_completed == 1
    assert sw.tasks_in_progress == 1


def test_format_sprint_report():
    now = datetime.now()
    tasks = [
        _task("t1", "done", story_points=5, created_at=now - timedelta(hours=3), updated_at=now),
        _task("t2", "review", story_points=3),
    ]
    m = compute_sprint_metrics(tasks, "s1")
    report = format_sprint_report(m)
    assert "Sprint Report: s1" in report
    assert "1/2" in report
    assert "50%" in report