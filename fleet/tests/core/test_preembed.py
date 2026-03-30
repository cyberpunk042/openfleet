"""Tests for fleet.core.preembed — compact pre-embedded context."""

import pytest
from unittest.mock import MagicMock
from fleet.core.preembed import build_task_preembed, build_heartbeat_preembed
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _make_task(**kwargs) -> Task:
    defaults = {
        "id": "task-12345678",
        "board_id": "board-1",
        "title": "Add FleetControlBar to header",
        "status": TaskStatus.IN_PROGRESS,
        "description": "",
        "priority": "high",
        "custom_fields": TaskCustomFields(
            task_readiness=80,
            task_stage="reasoning",
            requirement_verbatim="Add three Select dropdowns to the DashboardShell header bar",
            project="fleet",
        ),
    }
    defaults.update(kwargs)
    return Task(**defaults)


class TestTaskPreembed:
    def test_basic(self):
        task = _make_task()
        text = build_task_preembed(task)
        assert "TASK CONTEXT" in text
        assert "task-123" in text
        assert "FleetControlBar" in text
        assert "reasoning" in text
        assert "80%" in text
        assert "header bar" in text

    def test_includes_verbatim(self):
        task = _make_task()
        text = build_task_preembed(task)
        assert "Requirement:" in text
        assert "Select dropdowns" in text

    def test_stage_instruction(self):
        task = _make_task(custom_fields=TaskCustomFields(
            task_stage="conversation", task_readiness=20,
        ))
        text = build_task_preembed(task)
        assert "DISCUSS" in text
        assert "Do NOT produce code" in text

    def test_work_stage(self):
        task = _make_task(custom_fields=TaskCustomFields(
            task_stage="work", task_readiness=99,
        ))
        text = build_task_preembed(task)
        assert "EXECUTE" in text

    def test_blocked(self):
        task = _make_task(is_blocked=True)
        text = build_task_preembed(task)
        assert "BLOCKED" in text

    def test_completeness_summary(self):
        task = _make_task()
        text = build_task_preembed(task, completeness_summary="3/5 required (60%)")
        assert "3/5" in text

    def test_size_budget(self):
        task = _make_task()
        text = build_task_preembed(task)
        assert len(text) < 1000  # fits in gateway context/ file


class TestHeartbeatPreembed:
    def test_basic(self):
        text = build_heartbeat_preembed(
            agent_name="fleet-ops",
            role="fleet-ops",
            assigned_tasks=[],
            agents_online=8,
            agents_total=10,
            fleet_mode="full-autonomous",
            fleet_phase="execution",
        )
        assert "HEARTBEAT CONTEXT" in text
        assert "fleet-ops" in text
        assert "8/10" in text
        assert "idle" in text

    def test_with_messages(self):
        text = build_heartbeat_preembed(
            agent_name="architect",
            role="architect",
            assigned_tasks=[],
            messages_count=3,
            directives_count=1,
            events_count=5,
        )
        assert "3 message" in text
        assert "1 directive" in text
        assert "5 event" in text

    def test_with_tasks(self):
        tasks = [
            _make_task(title="Task A", custom_fields=TaskCustomFields(task_stage="analysis", task_readiness=30)),
            _make_task(title="Task B", custom_fields=TaskCustomFields(task_stage="work", task_readiness=99)),
        ]
        text = build_heartbeat_preembed(
            agent_name="architect",
            role="architect",
            assigned_tasks=tasks,
        )
        assert "2 assigned" in text
        assert "Task A" in text
        assert "Task B" in text

    def test_role_summary(self):
        text = build_heartbeat_preembed(
            agent_name="fleet-ops",
            role="fleet-ops",
            assigned_tasks=[],
            role_summary="3 pending approvals, 1 review",
        )
        assert "3 pending approvals" in text

    def test_size_budget(self):
        tasks = [_make_task(title=f"Task {i}") for i in range(5)]
        text = build_heartbeat_preembed(
            agent_name="agent",
            role="worker",
            assigned_tasks=tasks,
            messages_count=5,
            events_count=10,
            role_summary="Some role data",
            fleet_mode="full-autonomous",
            fleet_phase="execution",
            agents_online=8,
            agents_total=10,
        )
        assert len(text) < 1500  # compact enough for injection