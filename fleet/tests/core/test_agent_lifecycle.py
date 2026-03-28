"""Tests for agent lifecycle — smart status management."""

from datetime import datetime, timedelta

from fleet.core.agent_lifecycle import (
    AgentState,
    AgentStatus,
    FleetLifecycle,
    IDLE_AFTER,
    SLEEPING_AFTER,
)


def test_new_agent_is_idle():
    state = AgentState(name="test")
    assert state.status == AgentStatus.IDLE


def test_active_when_has_task():
    state = AgentState(name="test")
    now = datetime.now()
    state.update_activity(now, has_active_task=True, task_id="t1")
    assert state.status == AgentStatus.ACTIVE
    assert state.current_task_id == "t1"


def test_idle_after_task_completes():
    state = AgentState(name="test")
    now = datetime.now()
    state.update_activity(now, has_active_task=True, task_id="t1")
    assert state.status == AgentStatus.ACTIVE

    # Task completes, but still within idle threshold
    state.update_activity(now, has_active_task=False)
    assert state.status == AgentStatus.IDLE


def test_sleeping_after_idle_timeout():
    state = AgentState(name="test")
    now = datetime.now()
    state.last_active_at = now - timedelta(seconds=SLEEPING_AFTER + 1)
    state.update_activity(now, has_active_task=False)
    assert state.status == AgentStatus.SLEEPING


def test_active_agent_no_heartbeat_needed():
    state = AgentState(name="test")
    now = datetime.now()
    state.update_activity(now, has_active_task=True, task_id="t1")
    assert state.needs_heartbeat(now) is False


def test_idle_agent_needs_heartbeat():
    state = AgentState(name="test")
    now = datetime.now()
    state.status = AgentStatus.IDLE
    # No heartbeat ever sent
    assert state.needs_heartbeat(now) is True


def test_idle_agent_no_heartbeat_if_recent():
    state = AgentState(name="test")
    now = datetime.now()
    state.status = AgentStatus.IDLE
    state.last_heartbeat_at = now  # Just sent
    assert state.needs_heartbeat(now) is False


def test_sleeping_agent_needs_heartbeat_after_interval():
    state = AgentState(name="test")
    now = datetime.now()
    state.status = AgentStatus.SLEEPING
    state.last_heartbeat_at = now - timedelta(hours=3)  # Over 2-hour sleeping interval
    assert state.needs_heartbeat(now) is True


def test_wake_transitions_to_idle():
    state = AgentState(name="test")
    state.status = AgentStatus.SLEEPING
    now = datetime.now()
    state.wake(now)
    assert state.status == AgentStatus.IDLE


def test_should_wake_for_task():
    state = AgentState(name="test")
    state.status = AgentStatus.SLEEPING
    assert state.should_wake_for_task() is True
    state.status = AgentStatus.IDLE
    assert state.should_wake_for_task() is False


def test_fleet_lifecycle_update_all():
    lifecycle = FleetLifecycle()
    lifecycle.get_or_create("architect")
    lifecycle.get_or_create("devops")

    now = datetime.now()
    lifecycle.update_all(now, {"devops": "task-123"})

    assert lifecycle.get_or_create("devops").status == AgentStatus.ACTIVE
    assert lifecycle.get_or_create("architect").status == AgentStatus.IDLE


def test_fleet_lifecycle_status_summary():
    lifecycle = FleetLifecycle()
    s1 = lifecycle.get_or_create("a")
    s1.status = AgentStatus.ACTIVE
    s2 = lifecycle.get_or_create("b")
    s2.status = AgentStatus.SLEEPING
    s3 = lifecycle.get_or_create("c")
    s3.status = AgentStatus.IDLE

    summary = lifecycle.get_status_summary()
    assert "a" in summary["active"]
    assert "b" in summary["sleeping"]
    assert "c" in summary["idle"]


def test_fleet_idle_when_no_active():
    lifecycle = FleetLifecycle()
    lifecycle.get_or_create("a").status = AgentStatus.IDLE
    lifecycle.get_or_create("b").status = AgentStatus.SLEEPING
    assert lifecycle.is_fleet_idle() is True


def test_fleet_not_idle_when_active():
    lifecycle = FleetLifecycle()
    lifecycle.get_or_create("a").status = AgentStatus.ACTIVE
    lifecycle.get_or_create("b").status = AgentStatus.IDLE
    assert lifecycle.is_fleet_idle() is False