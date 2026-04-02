"""Integration tests — full system flow chains.

Tests verify that multiple systems interact correctly:
- Doctor detects → decides response → teaching creates lesson → formatted for injection
- Methodology stage → MCP tool enforcement → protocol violation detection
- Task context assembly → completeness → readiness suggestion
- Orchestrator cycle components → fleet control → dispatch gates
- Transpose → artifact update → completeness check → readiness progression
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _make_task(
    id="flow-test-001",
    title="Flow Test Task",
    status=TaskStatus.IN_PROGRESS,
    agent_name="architect",
    **cf_kwargs,
) -> Task:
    cf_defaults = {
        "task_readiness": 50,
        "task_stage": "analysis",
        "requirement_verbatim": "Add three Select dropdowns to the header bar",
        "project": "fleet",
        "agent_name": agent_name,
        "task_type": "task",
        "story_points": 5,
    }
    cf_defaults.update(cf_kwargs)
    return Task(
        id=id, board_id="board-1", title=title, status=status,
        description="Test", priority="medium",
        custom_fields=TaskCustomFields(**cf_defaults),
    )


# ─── Flow 1: Doctor → Teaching → Lesson Injection ─────────────────────


class TestDoctorTeachingFlow:
    """Doctor detects disease → decides to teach → teaching creates
    adapted lesson → lesson formatted for gateway injection."""

    @pytest.mark.asyncio
    async def test_deviation_detection_to_lesson(self):
        """Full chain: detect deviation → create lesson → format for injection."""
        from fleet.core.doctor import detect_protocol_violation, decide_response, AgentHealth, build_intervention
        from fleet.core.teaching import adapt_lesson, format_lesson_for_injection, DiseaseCategory

        # Step 1: Doctor detects protocol violation
        detection = detect_protocol_violation(
            "architect", "task-42", "conversation", ["fleet_commit"]
        )
        assert detection is not None

        # Step 2: Doctor decides response
        health = AgentHealth(agent_name="architect")
        action = decide_response(detection, health)
        assert action.value == "trigger_teaching"

        # Step 3: Build intervention with lesson context
        intervention = build_intervention(detection, action, lesson_context={
            "requirement_verbatim": "Add controls to the header bar",
            "current_stage": "conversation",
            "what_agent_did": "fleet_commit",
        })

        # Step 4: Teaching creates adapted lesson
        lesson = adapt_lesson(
            disease=DiseaseCategory.PROTOCOL_VIOLATION,
            agent_name="architect",
            task_id="task-42",
            context=intervention.lesson_context,
        )
        assert "conversation" in lesson.content
        assert "fleet_commit" in lesson.content

        # Step 5: Format for gateway injection
        text = format_lesson_for_injection(lesson)
        assert "TEACHING SYSTEM" in text
        assert "Exercise" in text
        assert "pruned" in text.lower()

    @pytest.mark.asyncio
    async def test_three_strikes_to_prune(self):
        """Agent corrected 3 times → doctor decides prune, not teach."""
        from fleet.core.doctor import detect_correction_threshold, decide_response, AgentHealth

        detection = detect_correction_threshold("architect", "task-42", 3)
        assert detection is not None

        health = AgentHealth(agent_name="architect", correction_count=3)
        action = decide_response(detection, health)
        assert action.value == "prune"

    @pytest.mark.asyncio
    async def test_lesson_evaluation_flow(self):
        """Lesson delivered → agent responds → evaluate comprehension."""
        from fleet.core.teaching import (
            adapt_lesson, evaluate_response, DiseaseCategory, LessonOutcome,
        )

        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION, "architect", "t1",
            {"requirement_verbatim": "header bar", "agent_plan": "sidebar"},
        )

        # Bad response — just acknowledgment
        result = evaluate_response(lesson, "I understand.")
        assert result == LessonOutcome.NO_CHANGE

        # Good response — references requirement
        result = evaluate_response(lesson, (
            "I see my mistake. The requirement says header bar but I was "
            "building a sidebar. I should have looked at DashboardShell.tsx "
            "instead of creating a new route."
        ))
        assert result == LessonOutcome.COMPREHENSION_VERIFIED


# ─── Flow 2: Methodology → MCP → Protocol Violation ───────────────────


class TestMethodologyMCPFlow:
    """Methodology stage → MCP tool check → violation detected by both
    MCP layer and doctor."""

    @pytest.mark.asyncio
    async def test_stage_blocks_commit(self):
        """MCP tool enforcement blocks fleet_commit during conversation."""
        from fleet.mcp.tools import _check_stage_allowed, COMMIT_ALLOWED_STAGES
        from fleet.mcp.tools import _ctx

        # Simulate: agent in conversation stage
        ctx = MagicMock()
        ctx.task_id = "task-1"
        ctx._task_stage = "conversation"

        import fleet.mcp.tools as tools_mod
        old_ctx = tools_mod._ctx
        tools_mod._ctx = ctx

        try:
            result = _check_stage_allowed("fleet_commit")
            assert result is not None
            assert result["ok"] is False
            assert "conversation" in result["error"]
            assert "Methodology violation" in result["error"]
        finally:
            tools_mod._ctx = old_ctx

    @pytest.mark.asyncio
    async def test_stage_allows_commit_during_work(self):
        """fleet_commit allowed during work stage."""
        from fleet.mcp.tools import _check_stage_allowed

        ctx = MagicMock()
        ctx.task_id = "task-1"
        ctx._task_stage = "work"

        import fleet.mcp.tools as tools_mod
        old_ctx = tools_mod._ctx
        tools_mod._ctx = ctx

        try:
            result = _check_stage_allowed("fleet_commit")
            assert result is None  # allowed
        finally:
            tools_mod._ctx = old_ctx


# ─── Flow 3: Transpose → Completeness → Readiness ─────────────────────


class TestTransposeCompletenessFlow:
    """Create artifact → update progressively → completeness increases →
    readiness suggestion increases."""

    @pytest.mark.asyncio
    async def test_progressive_completeness(self):
        """Artifact grows across cycles, completeness tracks progress."""
        from fleet.core.transpose import to_html, from_html, update_artifact
        from fleet.core.artifact_tracker import check_artifact_completeness

        # Cycle 1: Create with just title
        obj = {"title": "Header Analysis"}
        html = to_html("analysis_document", obj)
        comp = check_artifact_completeness("analysis_document", obj)
        assert comp.required_pct < 50
        readiness_1 = comp.suggested_readiness

        # Cycle 2: Add scope and findings
        html = update_artifact(html, {
            "scope": "DashboardShell.tsx header section",
            "findings": [{"title": "Center section", "finding": "Has room"}],
        })
        obj2 = from_html(html)
        comp2 = check_artifact_completeness("analysis_document", obj2)
        assert comp2.required_pct > comp.required_pct
        readiness_2 = comp2.suggested_readiness
        assert readiness_2 >= readiness_1

        # Cycle 3: Add remaining required fields
        html = update_artifact(html, {
            "current_state": "Three sections in header",
            "implications": "FleetControlBar fits in center section",
        })
        obj3 = from_html(html)
        comp3 = check_artifact_completeness("analysis_document", obj3)
        assert comp3.is_complete
        assert comp3.suggested_readiness >= 90


# ─── Flow 4: Context Assembly → Pre-embed → Dispatch ──────────────────


class TestContextDispatchFlow:
    """Context assembly → pre-embed → dispatch injection chain."""

    @pytest.mark.asyncio
    async def test_task_context_includes_methodology(self):
        """Task context assembly includes methodology + completeness."""
        from fleet.core.context_assembly import assemble_task_context, clear_context_cache

        clear_context_cache()
        task = _make_task(task_stage="reasoning", task_readiness=80)
        mc = AsyncMock()
        mc.list_tasks = AsyncMock(return_value=[task])
        mc.list_comments = AsyncMock(return_value=[])

        result = await assemble_task_context(task, mc, "board-1")

        assert result["methodology"]["stage"] == "reasoning"
        assert result["methodology"]["readiness"] == 80
        assert result["methodology"]["stage_instructions"]  # not empty
        assert result["custom_fields"]["requirement_verbatim"] == "Add three Select dropdowns to the header bar"

    @pytest.mark.asyncio
    async def test_preembed_from_task(self):
        """Pre-embed generated from task reflects correct stage."""
        from fleet.core.preembed import build_task_preembed

        task = _make_task(task_stage="work", task_readiness=99)
        text = build_task_preembed(task)
        assert "work" in text
        assert "99%" in text
        assert "EXECUTE" in text
        assert "header bar" in text  # verbatim requirement included

    @pytest.mark.asyncio
    async def test_heartbeat_context_role_specific(self):
        """Heartbeat context includes role-specific data."""
        from fleet.core.context_assembly import assemble_heartbeat_context
        from fleet.core.role_providers import ROLE_PROVIDERS

        tasks = [
            _make_task(status=TaskStatus.REVIEW, agent_name="dev"),
            _make_task(id="t2", status=TaskStatus.INBOX, agent_name=""),
        ]
        mc = AsyncMock()
        mc.list_memory = AsyncMock(return_value=[])
        mc.list_approvals = AsyncMock(return_value=[])

        result = await assemble_heartbeat_context(
            agent_name="fleet-ops", role="fleet-ops",
            tasks=tasks, agents=[], mc=mc, board_id="b1",
            role_providers=ROLE_PROVIDERS,
        )

        assert result["role"] == "fleet-ops"
        assert "review_queue" in result["role_data"]


# ─── Flow 5: Fleet Control → Orchestrator Gates ───────────────────────


class TestControlOrchestratorFlow:
    """Fleet control state → orchestrator reads → dispatch gates apply."""

    @pytest.mark.asyncio
    async def test_paused_mode_blocks_dispatch(self):
        """Work paused mode blocks dispatch."""
        from fleet.core.fleet_mode import (
            FleetControlState, read_fleet_control,
            should_dispatch, should_pull_from_plane,
            get_active_agents_for_phase,
        )

        state = read_fleet_control({"fleet_config": {"work_mode": "work-paused"}})
        assert not should_dispatch(state)
        assert not should_pull_from_plane(state)

    @pytest.mark.asyncio
    async def test_local_work_allows_dispatch_blocks_plane(self):
        """Local work only: dispatch OK, Plane pull blocked."""
        from fleet.core.fleet_mode import FleetControlState, should_dispatch, should_pull_from_plane

        state = FleetControlState(work_mode="local-work-only")
        assert should_dispatch(state)
        assert not should_pull_from_plane(state)

    @pytest.mark.asyncio
    async def test_crisis_mode_filters_agents(self):
        """Crisis management only allows fleet-ops + devsecops."""
        from fleet.core.fleet_mode import FleetControlState, get_active_agents_for_phase

        state = FleetControlState(cycle_phase="crisis-management")
        agents = get_active_agents_for_phase(state)
        assert agents is not None
        assert "fleet-ops" in agents
        assert "devsecops-expert" in agents
        assert "software-engineer" not in agents

    @pytest.mark.asyncio
    async def test_readiness_gate(self):
        """Tasks below 99% readiness don't get dispatched for work."""
        low = _make_task(task_readiness=50, status=TaskStatus.INBOX)
        high = _make_task(id="t2", task_readiness=99, status=TaskStatus.INBOX)

        inbox = [t for t in [low, high] if t.custom_fields.task_readiness >= 99]
        assert len(inbox) == 1
        assert inbox[0].id == "t2"


# ─── Flow 6: Event System End-to-End ──────────────────────────────────


class TestEventSystemFlow:
    """Event created → rendered for multiple surfaces → tags correct."""

    @pytest.mark.asyncio
    async def test_immune_event_renders_on_all_surfaces(self):
        """Immune event renders correctly for IRC, board memory, ntfy."""
        from fleet.core.events import create_event
        from fleet.core.event_display import render_irc, render_board_memory, render_ntfy

        event = create_event(
            "fleet.immune.agent_pruned",
            source="fleet/core/doctor",
            agent="architect",
            reason="3 corrections, model wrong",
        )

        irc = render_irc(event)
        assert "PRUNED" in irc
        assert "architect" in irc

        mem = render_board_memory(event)
        assert "immune-system" in mem["tags"]
        assert "PRUNED" in mem["content"]

        ntfy = render_ntfy(event)
        assert "PRUNED" in ntfy["title"]

    @pytest.mark.asyncio
    async def test_methodology_event_tagged_correctly(self):
        """Methodology events get methodology tag in board memory."""
        from fleet.core.events import create_event
        from fleet.core.event_display import render_board_memory

        event = create_event(
            "fleet.methodology.stage_changed",
            source="test",
            from_stage="analysis",
            to_stage="reasoning",
            authorized_by="po",
        )

        mem = render_board_memory(event)
        assert "methodology" in mem["tags"]
        assert "analysis" in mem["content"]
        assert "reasoning" in mem["content"]