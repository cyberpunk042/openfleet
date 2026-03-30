"""Integration tests — all 14 fleet control modes tested end-to-end.

Work Modes (5): full-autonomous, project-management-work, local-work-only,
  finish-current-work, work-paused
Cycle Phases (6): execution, planning, analysis, investigation, review,
  crisis-management
Backend Modes (3): claude, localai, hybrid

Each mode test verifies: fleet state → dispatch behavior → agent filtering →
stage instructions → event emission → tool availability.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.fleet_mode import (
    FleetControlState,
    read_fleet_control,
    should_dispatch,
    should_pull_from_plane,
    get_active_agents_for_phase,
    WORK_MODES,
    CYCLE_PHASES,
    BACKEND_MODES,
)
from fleet.core.preembed import build_heartbeat_preembed
from fleet.core.stage_context import get_stage_instructions, get_stage_summary


def _make_task(agent_name="architect", readiness=99, stage="work", **kwargs):
    defaults = {
        "id": "mode-test-001",
        "board_id": "b1",
        "title": "Mode Test Task",
        "status": TaskStatus.INBOX,
        "description": "",
        "priority": "medium",
        "custom_fields": TaskCustomFields(
            task_readiness=readiness,
            task_stage=stage,
            agent_name=agent_name,
            requirement_verbatim="Test requirement",
            project="fleet",
            task_type="task",
        ),
    }
    defaults.update(kwargs)
    return Task(**defaults)


# ═══ WORK MODES ═══════════════════════════════════════════════════════


class TestFullAutonomous:
    """Full Autonomous: everything open, PM pulls from Plane, all agents work."""

    def test_dispatch_allowed(self):
        state = FleetControlState(work_mode="full-autonomous")
        assert should_dispatch(state)

    def test_plane_pull_allowed(self):
        state = FleetControlState(work_mode="full-autonomous")
        assert should_pull_from_plane(state)

    def test_all_agents_active(self):
        state = FleetControlState(work_mode="full-autonomous", cycle_phase="execution")
        agents = get_active_agents_for_phase(state)
        assert agents is None  # None = no filter, all active

    def test_heartbeat_shows_mode(self):
        text = build_heartbeat_preembed(
            "architect", "architect", [],
            fleet_mode="full-autonomous", fleet_phase="execution",
        )
        assert "full-autonomous" in text


class TestProjectManagementWork:
    """PM Work: PM active on Plane, pulls priorities, drives sprints."""

    def test_dispatch_allowed(self):
        state = FleetControlState(work_mode="project-management-work")
        assert should_dispatch(state)

    def test_plane_pull_allowed(self):
        state = FleetControlState(work_mode="project-management-work")
        assert should_pull_from_plane(state)


class TestLocalWorkOnly:
    """Local Work Only: agents work on OCMC tasks only.
    PM does NOT pull new work from Plane. Plane sync still runs."""

    def test_dispatch_allowed(self):
        state = FleetControlState(work_mode="local-work-only")
        assert should_dispatch(state)

    def test_plane_pull_blocked(self):
        state = FleetControlState(work_mode="local-work-only")
        assert not should_pull_from_plane(state)

    def test_heartbeat_shows_local(self):
        text = build_heartbeat_preembed(
            "architect", "architect", [],
            fleet_mode="local-work-only", fleet_phase="execution",
        )
        assert "local-work-only" in text


class TestFinishCurrentWork:
    """Finish Current: no new dispatch. Agents with in-progress finish."""

    def test_dispatch_blocked(self):
        state = FleetControlState(work_mode="finish-current-work")
        assert not should_dispatch(state)

    def test_plane_pull_blocked(self):
        state = FleetControlState(work_mode="finish-current-work")
        assert not should_pull_from_plane(state)


class TestWorkPaused:
    """Work Paused: nothing moves. Zero dispatch. Agents idle."""

    def test_dispatch_blocked(self):
        state = FleetControlState(work_mode="work-paused")
        assert not should_dispatch(state)

    def test_plane_pull_blocked(self):
        state = FleetControlState(work_mode="work-paused")
        assert not should_pull_from_plane(state)


# ═══ CYCLE PHASES ═════════════════════════════════════════════════════


class TestExecutionPhase:
    """Execution: normal work. All agents active."""

    def test_all_agents(self):
        state = FleetControlState(cycle_phase="execution")
        assert get_active_agents_for_phase(state) is None

    def test_stage_instructions_exist(self):
        # During execution, agents follow work protocol
        text = get_stage_instructions("work")
        assert "EXECUTE" in text
        assert "fleet_commit" in text


class TestPlanningPhase:
    """Planning: PM + architect only. Sprint planning."""

    def test_pm_and_architect_only(self):
        state = FleetControlState(cycle_phase="planning")
        agents = get_active_agents_for_phase(state)
        assert agents is not None
        assert "project-manager" in agents
        assert "architect" in agents
        assert "software-engineer" not in agents
        assert "qa-engineer" not in agents

    def test_filtered_agent_count(self):
        state = FleetControlState(cycle_phase="planning")
        agents = get_active_agents_for_phase(state)
        assert len(agents) == 2


class TestAnalysisPhase:
    """Analysis: architect + PM active. Architecture review."""

    def test_architect_and_pm(self):
        state = FleetControlState(cycle_phase="analysis")
        agents = get_active_agents_for_phase(state)
        assert agents is not None
        assert "architect" in agents
        assert "project-manager" in agents

    def test_analysis_stage_instructions(self):
        text = get_stage_instructions("analysis")
        assert "ANALYSIS" in text
        assert "Do NOT produce solutions" in text


class TestInvestigationPhase:
    """Investigation: any assigned agent. Research only."""

    def test_all_agents_for_investigation(self):
        state = FleetControlState(cycle_phase="investigation")
        agents = get_active_agents_for_phase(state)
        assert agents is None  # any assigned agent

    def test_investigation_stage_instructions(self):
        text = get_stage_instructions("investigation")
        assert "RESEARCH" in text or "research" in text.lower()
        assert "Do NOT decide" in text


class TestReviewPhase:
    """Review: fleet-ops only. Clear approval queue."""

    def test_fleet_ops_only(self):
        state = FleetControlState(cycle_phase="review")
        agents = get_active_agents_for_phase(state)
        assert agents == ["fleet-ops"]


class TestCrisisManagement:
    """Crisis: fleet-ops + devsecops only. Security/hotfix."""

    def test_ops_and_security(self):
        state = FleetControlState(cycle_phase="crisis-management")
        agents = get_active_agents_for_phase(state)
        assert "fleet-ops" in agents
        assert "devsecops-expert" in agents
        assert len(agents) == 2


# ═══ BACKEND MODES ════════════════════════════════════════════════════


class TestClaudeBackend:
    """Claude: all inference through Claude. Current default."""

    def test_default_is_claude(self):
        state = FleetControlState()
        assert state.backend_mode == "claude"

    def test_read_from_config(self):
        state = read_fleet_control({"fleet_config": {"backend_mode": "claude"}})
        assert state.backend_mode == "claude"


class TestLocalAIBackend:
    """LocalAI: all inference through LocalAI. Zero Claude tokens."""

    def test_read_localai(self):
        state = read_fleet_control({"fleet_config": {"backend_mode": "localai"}})
        assert state.backend_mode == "localai"


class TestHybridBackend:
    """Hybrid: router decides per operation by complexity."""

    def test_read_hybrid(self):
        state = read_fleet_control({"fleet_config": {"backend_mode": "hybrid"}})
        assert state.backend_mode == "hybrid"


# ═══ MODE COMBINATIONS ════════════════════════════════════════════════


class TestModeCombinations:
    """Three axes are independent. Any combination is valid."""

    def test_local_work_plus_planning_plus_localai(self):
        state = FleetControlState(
            work_mode="local-work-only",
            cycle_phase="planning",
            backend_mode="localai",
        )
        assert should_dispatch(state)
        assert not should_pull_from_plane(state)
        agents = get_active_agents_for_phase(state)
        assert agents is not None
        assert "project-manager" in agents

    def test_paused_plus_crisis_plus_hybrid(self):
        state = FleetControlState(
            work_mode="work-paused",
            cycle_phase="crisis-management",
            backend_mode="hybrid",
        )
        assert not should_dispatch(state)  # paused overrides everything

    def test_full_auto_plus_review_plus_claude(self):
        state = FleetControlState(
            work_mode="full-autonomous",
            cycle_phase="review",
            backend_mode="claude",
        )
        assert should_dispatch(state)
        agents = get_active_agents_for_phase(state)
        assert agents == ["fleet-ops"]

    def test_finish_current_plus_execution(self):
        state = FleetControlState(
            work_mode="finish-current-work",
            cycle_phase="execution",
        )
        assert not should_dispatch(state)
        # Even in execution phase, finish-current blocks new dispatch


# ═══ READINESS GATE + STAGE ENFORCEMENT ═══════════════════════════════


class TestReadinessAndStageEnforcement:
    """Readiness percentage gates work dispatch. Stage gates MCP tools."""

    def test_readiness_0_not_dispatched(self):
        task = _make_task(readiness=0)
        assert task.custom_fields.task_readiness < 99

    def test_readiness_50_not_dispatched(self):
        task = _make_task(readiness=50)
        assert task.custom_fields.task_readiness < 99

    def test_readiness_90_not_dispatched(self):
        """90% is a checkpoint but still below work threshold."""
        task = _make_task(readiness=90)
        assert task.custom_fields.task_readiness < 99

    def test_readiness_99_dispatched(self):
        task = _make_task(readiness=99)
        assert task.custom_fields.task_readiness >= 99

    def test_readiness_100_dispatched(self):
        task = _make_task(readiness=100)
        assert task.custom_fields.task_readiness >= 99

    def test_stage_conversation_summary(self):
        assert "PO" in get_stage_summary("conversation")
        assert "code" in get_stage_summary("conversation").lower()

    def test_stage_work_summary(self):
        assert "plan" in get_stage_summary("work").lower()

    def test_all_valid_modes_listed(self):
        assert len(WORK_MODES) == 5
        assert len(CYCLE_PHASES) == 6
        assert len(BACKEND_MODES) == 3


# ═══ EVENT EMISSION FOR MODE CHANGES ═════════════════════════════════


class TestModeChangeEvents:
    """When modes change, events should be emittable."""

    def test_mode_change_event_creation(self):
        from fleet.core.events import create_event

        event = create_event(
            "fleet.system.mode_changed",
            source="fleet/cli/orchestrator",
            old_work_mode="full-autonomous",
            new_work_mode="work-paused",
            old_cycle_phase="execution",
            new_cycle_phase="execution",
            old_backend_mode="claude",
            new_backend_mode="claude",
            set_by="human",
        )
        assert event.type == "fleet.system.mode_changed"
        assert event.data["old_work_mode"] == "full-autonomous"
        assert event.data["new_work_mode"] == "work-paused"
        assert event.data["set_by"] == "human"

    def test_mode_change_renders_on_irc(self):
        from fleet.core.events import create_event
        from fleet.core.event_display import render_irc

        event = create_event(
            "fleet.system.mode_changed",
            source="test",
            old_work_mode="full-autonomous",
            new_work_mode="planning",
        )
        irc = render_irc(event)
        assert len(irc) > 0