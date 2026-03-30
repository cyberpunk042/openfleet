"""Tests for fleet.core.context_assembly + role_providers + preembed."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.context_assembly import assemble_task_context, assemble_heartbeat_context, clear_context_cache
from fleet.core.role_providers import (
    ROLE_PROVIDERS,
    get_role_provider,
    fleet_ops_provider,
    project_manager_provider,
    architect_provider,
    worker_provider,
)
from fleet.core.preembed import build_task_preembed, build_heartbeat_preembed


def _make_task(
    id="task-001",
    title="Test Task",
    status=TaskStatus.IN_PROGRESS,
    agent_name="architect",
    **cf_kwargs,
) -> Task:
    cf_defaults = {
        "task_readiness": 50,
        "task_stage": "analysis",
        "requirement_verbatim": "Build the thing",
        "project": "fleet",
        "agent_name": agent_name,
        "task_type": "task",
    }
    cf_defaults.update(cf_kwargs)
    return Task(
        id=id,
        board_id="board-1",
        title=title,
        status=status,
        description="A test task",
        priority="medium",
        custom_fields=TaskCustomFields(**cf_defaults),
    )


def _mock_mc():
    mc = AsyncMock()
    mc.list_tasks = AsyncMock(return_value=[])
    mc.list_comments = AsyncMock(return_value=[
        {"agent_name": "architect", "message": "Examined header structure", "created_at": "2026-03-30T10:00"},
        {"agent_name": "human", "message": "Focus on center section", "created_at": "2026-03-30T10:05"},
    ])
    mc.list_memory = AsyncMock(return_value=[])
    mc.list_approvals = AsyncMock(return_value=[])
    return mc


class TestAssembleTaskContext:
    def setup_method(self):
        clear_context_cache()

    @pytest.mark.asyncio
    async def test_basic_assembly(self):
        task = _make_task()
        mc = _mock_mc()
        mc.list_tasks = AsyncMock(return_value=[task])

        result = await assemble_task_context(task, mc, "board-1")

        assert result["task"]["id"] == "task-001"
        assert result["task"]["title"] == "Test Task"
        assert result["custom_fields"]["readiness"] == 50
        assert result["custom_fields"]["stage"] == "analysis"
        assert result["custom_fields"]["requirement_verbatim"] == "Build the thing"

    @pytest.mark.asyncio
    async def test_methodology_included(self):
        task = _make_task(task_stage="reasoning", task_type="epic")
        mc = _mock_mc()
        mc.list_tasks = AsyncMock(return_value=[task])

        result = await assemble_task_context(task, mc, "board-1")

        assert result["methodology"]["stage"] == "reasoning"
        assert "reasoning" in result["methodology"]["required_stages"]
        assert result["methodology"]["stage_instructions"]  # not empty

    @pytest.mark.asyncio
    async def test_comments_included(self):
        task = _make_task()
        mc = _mock_mc()
        mc.list_tasks = AsyncMock(return_value=[task])

        result = await assemble_task_context(task, mc, "board-1")

        assert len(result["comments"]) == 2
        assert "header structure" in result["comments"][0]["content"]

    @pytest.mark.asyncio
    async def test_related_tasks(self):
        parent = _make_task(id="parent-001", title="Parent Epic", task_type="epic")
        child = _make_task(id="child-001", title="Child Task", parent_task="parent-001")
        mc = _mock_mc()
        mc.list_tasks = AsyncMock(return_value=[parent, child])

        result = await assemble_task_context(child, mc, "board-1")

        relations = result["related_tasks"]
        assert any(r["relation"] == "parent" for r in relations)


class TestAssembleHeartbeatContext:
    @pytest.mark.asyncio
    async def test_basic_heartbeat(self):
        tasks = [_make_task(agent_name="fleet-ops")]
        mc = _mock_mc()
        agents = [MagicMock(name="fleet-ops", status="online")]

        result = await assemble_heartbeat_context(
            agent_name="fleet-ops",
            role="fleet-ops",
            tasks=tasks,
            agents=agents,
            mc=mc,
            board_id="board-1",
        )

        assert result["agent"] == "fleet-ops"
        assert result["role"] == "fleet-ops"
        assert len(result["assigned_tasks"]) == 1

    @pytest.mark.asyncio
    async def test_role_data_with_providers(self):
        tasks = [
            _make_task(status=TaskStatus.REVIEW, agent_name="architect"),
            _make_task(id="t2", status=TaskStatus.INBOX, agent_name=""),
        ]
        mc = _mock_mc()
        mc.list_tasks = AsyncMock(return_value=tasks)
        mc.list_approvals = AsyncMock(return_value=[])
        agents = []

        result = await assemble_heartbeat_context(
            agent_name="fleet-ops",
            role="fleet-ops",
            tasks=tasks,
            agents=agents,
            mc=mc,
            board_id="board-1",
            role_providers=ROLE_PROVIDERS,
        )

        assert "role_data" in result
        # fleet-ops should get review queue data
        assert "review_queue" in result["role_data"]


class TestRoleProviders:
    def test_all_roles_registered(self):
        assert len(ROLE_PROVIDERS) >= 10

    def test_fleet_ops_provider_exists(self):
        assert get_role_provider("fleet-ops").__name__ == "fleet_ops_provider"

    def test_pm_provider_exists(self):
        assert get_role_provider("project-manager").__name__ == "project_manager_provider"

    def test_unknown_role_gets_worker(self):
        assert get_role_provider("unknown-role").__name__ == "worker_provider"

    @pytest.mark.asyncio
    async def test_fleet_ops_returns_approvals(self):
        mc = _mock_mc()
        mc.list_approvals = AsyncMock(return_value=[])
        tasks = [_make_task(status=TaskStatus.REVIEW)]
        result = await fleet_ops_provider("fleet-ops", tasks, [], mc, "board-1")
        assert "pending_approvals" in result
        assert "review_queue" in result

    @pytest.mark.asyncio
    async def test_pm_returns_unassigned(self):
        tasks = [
            _make_task(status=TaskStatus.INBOX, agent_name=""),
            _make_task(id="t2", status=TaskStatus.INBOX, agent_name="architect"),
        ]
        result = await project_manager_provider("pm", tasks, [], AsyncMock(), "board-1")
        assert result["unassigned_tasks"] == 1

    @pytest.mark.asyncio
    async def test_architect_returns_design_tasks(self):
        tasks = [
            _make_task(task_type="epic", task_stage="investigation"),
        ]
        result = await architect_provider("architect", tasks, [], AsyncMock(), "board-1")
        assert len(result["design_tasks"]) == 1


class TestPreembedIntegration:
    def test_task_preembed_from_task(self):
        task = _make_task(task_stage="work", task_readiness=99)
        text = build_task_preembed(task)
        assert "TASK CONTEXT" in text
        assert "work" in text
        assert "99%" in text
        assert "EXECUTE" in text

    def test_heartbeat_preembed_format(self):
        tasks = [_make_task()]
        text = build_heartbeat_preembed(
            agent_name="architect",
            role="architect",
            assigned_tasks=tasks,
            messages_count=2,
            fleet_mode="full-autonomous",
            fleet_phase="execution",
            agents_online=8,
            agents_total=10,
        )
        assert "HEARTBEAT CONTEXT" in text
        assert "architect" in text
        assert "8/10" in text
        assert "2 message" in text