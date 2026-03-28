"""Tests for task priority scoring."""

from datetime import datetime, timedelta

from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.task_scoring import (
    identify_blocker_type,
    rank_tasks,
    score_task,
)


def _task(
    id: str = "t1",
    title: str = "Test",
    priority: str = "medium",
    task_type: str = "task",
    story_points: int = 0,
    depends_on: list[str] | None = None,
    created_at: datetime | None = None,
) -> Task:
    return Task(
        id=id, board_id="b1", title=title,
        status=TaskStatus.INBOX, priority=priority,
        custom_fields=TaskCustomFields(
            task_type=task_type,
            story_points=story_points,
        ),
        depends_on=depends_on or [],
        created_at=created_at,
    )


def test_urgent_scores_higher_than_low():
    urgent = score_task(_task(priority="urgent"), [])
    low = score_task(_task(priority="low"), [])
    assert urgent.score > low.score


def test_blocker_type_boosts_score():
    blocker = score_task(_task(task_type="blocker"), [])
    regular = score_task(_task(task_type="task"), [])
    assert blocker.score > regular.score


def test_downstream_deps_boost_score():
    parent = _task(id="p1")
    child1 = _task(id="c1", depends_on=["p1"])
    child2 = _task(id="c2", depends_on=["p1"])
    all_tasks = [parent, child1, child2]

    scored = score_task(parent, all_tasks)
    assert any("unblocks" in r for r in scored.reasons)
    assert scored.score > score_task(_task(), []).score


def test_old_tasks_get_wait_bonus():
    now = datetime.now()
    old = _task(created_at=now - timedelta(hours=10))
    new = _task(created_at=now)

    scored_old = score_task(old, [], now)
    scored_new = score_task(new, [], now)
    assert scored_old.score > scored_new.score


def test_large_tasks_slight_penalty():
    large = score_task(_task(story_points=13), [])
    small = score_task(_task(story_points=2), [])
    assert small.score > large.score


def test_rank_tasks_orders_by_score():
    tasks = [
        _task(id="low", priority="low"),
        _task(id="urgent", priority="urgent"),
        _task(id="high", priority="high"),
    ]
    ranked = rank_tasks(tasks, tasks)
    assert ranked[0].task.id == "urgent"
    assert ranked[1].task.id == "high"
    assert ranked[2].task.id == "low"


def test_identify_blocker_type_tests():
    t = _task(title="Fix failing tests in plane_client")
    assert identify_blocker_type(t) == "qa-engineer"


def test_identify_blocker_type_docker():
    t = _task(title="Docker compose service won't start")
    assert identify_blocker_type(t) == "devops"


def test_identify_blocker_type_security():
    t = _task(title="CVE-2024-1234 in dependency")
    assert identify_blocker_type(t) == "devsecops-expert"


def test_identify_blocker_type_architecture():
    t = _task(title="Refactor coupling between modules")
    assert identify_blocker_type(t) == "architect"


def test_identify_blocker_type_default():
    t = _task(title="Some generic bug fix")
    assert identify_blocker_type(t) == "software-engineer"