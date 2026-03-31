"""Tests for fleet.core.preembed — FULL pre-embedded context."""

import pytest
from fleet.core.preembed import build_task_preembed, build_heartbeat_preembed
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _make_task(**kwargs) -> Task:
    defaults = {
        "id": "task-12345678",
        "board_id": "board-1",
        "title": "Add FleetControlBar to header",
        "status": TaskStatus.IN_PROGRESS,
        "description": "Inject three Select dropdowns into DashboardShell",
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
        assert "Verbatim Requirement" in text
        assert "Select dropdowns" in text

    def test_includes_description(self):
        task = _make_task()
        text = build_task_preembed(task)
        assert "DashboardShell" in text

    def test_stage_instruction(self):
        task = _make_task(custom_fields=TaskCustomFields(
            task_stage="conversation", task_readiness=20,
        ))
        text = build_task_preembed(task)
        assert "CONVERSATION" in text

    def test_work_stage(self):
        task = _make_task(custom_fields=TaskCustomFields(
            task_stage="work", task_readiness=99,
        ))
        text = build_task_preembed(task)
        assert "WORK" in text

    def test_blocked(self):
        task = _make_task(is_blocked=True)
        text = build_task_preembed(task)
        assert "BLOCKED" in text


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

    def test_with_messages(self):
        text = build_heartbeat_preembed(
            agent_name="architect",
            role="architect",
            assigned_tasks=[],
            messages=[
                {"from": "pm", "content": "Need design input on task #42"},
                {"from": "human", "content": "Focus on the header"},
            ],
        )
        assert "MESSAGES" in text
        assert "design input" in text
        assert "header" in text

    def test_with_directives(self):
        text = build_heartbeat_preembed(
            agent_name="pm",
            role="project-manager",
            assigned_tasks=[],
            directives=[
                {"content": "Start AICP Stage 1", "from": "human", "urgent": True},
            ],
        )
        assert "DIRECTIVES" in text
        assert "URGENT" in text
        assert "AICP Stage 1" in text

    def test_with_tasks_full_detail(self):
        tasks = [
            _make_task(title="Task A", custom_fields=TaskCustomFields(
                task_stage="analysis", task_readiness=30,
                requirement_verbatim="Analyze the header")),
            _make_task(title="Task B", custom_fields=TaskCustomFields(
                task_stage="work", task_readiness=99)),
        ]
        text = build_heartbeat_preembed(
            agent_name="architect",
            role="architect",
            assigned_tasks=tasks,
        )
        assert "ASSIGNED TASKS (2)" in text
        assert "Task A" in text
        assert "Task B" in text
        assert "analysis" in text
        assert "30%" in text
        assert "Analyze the header" in text

    def test_with_role_data(self):
        text = build_heartbeat_preembed(
            agent_name="fleet-ops",
            role="fleet-ops",
            assigned_tasks=[],
            role_data={
                "pending_approvals": 3,
                "review_queue": [{"id": "t1", "title": "Review this"}],
            },
        )
        assert "ROLE DATA" in text
        assert "pending_approvals" in text
        assert "3" in text

    def test_with_events(self):
        text = build_heartbeat_preembed(
            agent_name="agent",
            role="worker",
            assigned_tasks=[],
            events=[
                {"type": "fleet.task.completed", "agent": "arch", "summary": "Done with header", "time": "2026-03-30T10:00:00"},
            ],
        )
        assert "EVENTS" in text
        assert "completed" in text
        assert "arch" in text

    def test_no_size_compression(self):
        """Verify pre-embed is NOT artificially compressed."""
        tasks = [_make_task(title=f"Task {i}", custom_fields=TaskCustomFields(
            requirement_verbatim=f"Full requirement text for task {i} with all the details needed",
            task_stage="analysis", task_readiness=30,
        )) for i in range(5)]
        text = build_heartbeat_preembed(
            agent_name="pm",
            role="project-manager",
            assigned_tasks=tasks,
            messages=[{"from": "human", "content": "Full message content not truncated"}],
            directives=[{"content": "Full directive content", "from": "human"}],
            events=[{"type": "fleet.test", "agent": "x", "summary": "Full event", "time": "2026-03-30T10:00:00"}],
            role_data={"unassigned_tasks": 6, "progress": "5/15 done"},
            fleet_mode="full-autonomous",
            fleet_phase="execution",
            agents_online=8,
            agents_total=10,
        )
        # Must contain FULL data — not truncated
        assert "Full requirement text for task 0" in text
        assert "Full requirement text for task 4" in text
        assert "Full message content not truncated" in text
        assert "Full directive content" in text
        assert "Full event" in text