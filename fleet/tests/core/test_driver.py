"""Tests for autonomous driver model."""

from fleet.core.driver import (
    DRIVER_AGENTS,
    determine_driver_directive,
    is_driver,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _task(agent: str = "project-manager", status: str = "inbox", auto: bool = False, project: str = "") -> Task:
    return Task(
        id="t1", board_id="b1", title="Test", status=TaskStatus(status),
        custom_fields=TaskCustomFields(agent_name=agent, project=project),
        auto_created=auto,
    )


def test_is_driver():
    assert is_driver("project-manager")
    assert is_driver("fleet-ops")
    assert is_driver("accountability-generator")
    assert is_driver("devsecops-expert")
    assert not is_driver("software-engineer")
    assert not is_driver("qa-engineer")


def test_human_task_highest_priority():
    tasks = [_task("project-manager", "inbox", auto=False)]
    d = determine_driver_directive("project-manager", tasks)
    assert d.priority_level == 1
    assert d.action == "work_on_task"


def test_auto_task_second_priority():
    tasks = [_task("project-manager", "inbox", auto=True)]
    d = determine_driver_directive("project-manager", tasks)
    assert d.priority_level == 2
    assert d.action == "work_on_task"


def test_drive_product_when_idle():
    tasks = []  # No tasks for PM
    d = determine_driver_directive("project-manager", tasks)
    # PM should drive DSPD
    assert d.priority_level in (3, 4)
    if d.priority_level == 3:
        assert d.action == "drive_product"
        assert d.product == "DSPD"


def test_fleet_improvement_when_fully_idle():
    tasks = []
    d = determine_driver_directive("fleet-ops", tasks)
    # fleet-ops doesn't own a product, so falls to improvement
    assert d.action == "improve_fleet"
    assert d.priority_level == 4


def test_done_tasks_dont_count_as_assigned():
    tasks = [_task("project-manager", "done")]
    d = determine_driver_directive("project-manager", tasks)
    # Done tasks shouldn't prevent product driving
    assert d.priority_level >= 3