"""Integration tests — verify systems work against live fleet infrastructure.

These tests require MC backend running at localhost:8000.
Skip if infrastructure is down.

Tests cover: methodology, immune system, teaching, transpose, context
assembly, control surface, event bus — all against real MC API.
"""

import asyncio
import os
import pytest

from fleet.infra.config_loader import ConfigLoader

# Skip all if no LOCAL_AUTH_TOKEN or MC is down
_loader = ConfigLoader()
_env = _loader.load_env()
_token = _env.get("LOCAL_AUTH_TOKEN", "")

try:
    import httpx
    _resp = httpx.get("http://localhost:8000/healthz", timeout=3)
    _mc_up = _resp.status_code == 200
except Exception:
    _mc_up = False

pytestmark = pytest.mark.skipif(
    not _token or not _mc_up,
    reason="MC backend not available or no LOCAL_AUTH_TOKEN",
)


@pytest.fixture
async def mc():
    from fleet.infra.mc_client import MCClient
    client = MCClient(token=_token)
    yield client
    await client.close()


@pytest.fixture
async def board_id(mc):
    bid = await mc.get_board_id()
    assert bid, "No board found"
    return bid


# ─── Methodology System ────────────────────────────────────────────────


class TestMethodologyLive:
    @pytest.mark.asyncio
    async def test_custom_fields_exist(self, mc, board_id):
        """Verify methodology custom fields are on the board."""
        tasks = await mc.list_tasks(board_id)
        # Check that TaskCustomFields has our new fields
        if tasks:
            t = tasks[0]
            assert hasattr(t.custom_fields, 'task_readiness')
            assert hasattr(t.custom_fields, 'requirement_verbatim')
            assert hasattr(t.custom_fields, 'task_stage')

    @pytest.mark.asyncio
    async def test_stage_progression_engine(self):
        """Verify methodology engine works with real task types."""
        from fleet.core.methodology import get_required_stages, get_next_stage, Stage

        # Epic should have all stages
        stages = get_required_stages("epic")
        assert len(stages) == 5
        assert stages[0] == Stage.CONVERSATION
        assert stages[-1] == Stage.WORK

        # Next stage from conversation for epic
        nxt = get_next_stage("conversation", stages)
        assert nxt == Stage.ANALYSIS

    @pytest.mark.asyncio
    async def test_standards_library(self):
        """Verify all artifact standards are defined."""
        from fleet.core.standards import list_standards, check_standard

        standards = list_standards()
        assert len(standards) >= 7

        # Check a task standard
        result = check_standard("task", {
            "title": True, "requirement_verbatim": True,
            "description": True, "acceptance_criteria": True,
            "task_type": True, "task_stage": True,
            "task_readiness": True, "priority": True, "project": True,
        })
        assert result.compliant

    @pytest.mark.asyncio
    async def test_stage_context_instructions(self):
        """Verify all stages have protocol instructions."""
        from fleet.core.stage_context import get_stage_instructions

        for stage in ["conversation", "analysis", "investigation", "reasoning", "work"]:
            text = get_stage_instructions(stage)
            assert len(text) > 100, f"No instructions for {stage}"


# ─── Immune System ─────────────────────────────────────────────────────


class TestImmuneSystemLive:
    @pytest.mark.asyncio
    async def test_doctor_detection_patterns(self):
        """Verify detection functions work with realistic data."""
        from fleet.core.doctor import (
            detect_protocol_violation,
            detect_laziness,
            detect_stuck,
            detect_correction_threshold,
        )

        # Protocol violation: commit during conversation
        d = detect_protocol_violation("architect", "t1", "conversation", ["fleet_commit"])
        assert d is not None
        assert d.disease.value == "protocol_violation"

        # No violation: commit during work
        d = detect_protocol_violation("architect", "t1", "work", ["fleet_commit"])
        assert d is None

        # Laziness: fast completion
        d = detect_laziness("dev", "t1", story_points=5, time_to_complete_minutes=1)
        assert d is not None

        # Correction threshold
        d = detect_correction_threshold("agent", "t1", 3)
        assert d is not None
        assert d.suggested_action.value == "prune"

    @pytest.mark.asyncio
    async def test_doctor_response_decisions(self):
        """Verify response decision logic."""
        from fleet.core.doctor import (
            Detection, AgentHealth, Severity, ResponseAction,
            decide_response,
        )
        from fleet.core.teaching import DiseaseCategory

        # Medium severity first time → teach
        det = Detection("agent", "t1", DiseaseCategory.DEVIATION, Severity.MEDIUM, "drifted")
        health = AgentHealth(agent_name="agent")
        assert decide_response(det, health) == ResponseAction.TRIGGER_TEACHING

        # Critical → prune
        det = Detection("agent", "t1", DiseaseCategory.DEVIATION, Severity.CRITICAL, "severe")
        assert decide_response(det, health) == ResponseAction.PRUNE

    @pytest.mark.asyncio
    async def test_event_types_registered(self):
        """Verify immune/teaching/methodology event types exist."""
        from fleet.core.events import EVENT_TYPES

        immune_events = [k for k in EVENT_TYPES if "immune" in k]
        teaching_events = [k for k in EVENT_TYPES if "teaching" in k]
        methodology_events = [k for k in EVENT_TYPES if "methodology" in k]

        assert len(immune_events) >= 5
        assert len(teaching_events) >= 5
        assert len(methodology_events) >= 5


# ─── Teaching System ───────────────────────────────────────────────────


class TestTeachingSystemLive:
    @pytest.mark.asyncio
    async def test_lesson_adaptation(self):
        """Verify lessons adapt to specific disease + context."""
        from fleet.core.teaching import adapt_lesson, DiseaseCategory, format_lesson_for_injection

        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="architect",
            task_id="t1",
            context={
                "requirement_verbatim": "Add controls to the header bar",
                "agent_plan": "Create a sidebar page",
            },
        )
        assert "header bar" in lesson.content
        assert "sidebar" in lesson.content

        # Format for injection
        text = format_lesson_for_injection(lesson)
        assert "TEACHING SYSTEM" in text
        assert "Exercise" in text

    @pytest.mark.asyncio
    async def test_lesson_tracking(self):
        """Verify lesson tracker records and queries."""
        from fleet.core.teaching import LessonTracker, DiseaseCategory, LessonOutcome

        tracker = LessonTracker()
        tracker.record_lesson("agent-a", "t1", DiseaseCategory.DEVIATION, 1, LessonOutcome.NO_CHANGE)
        tracker.record_lesson("agent-a", "t2", DiseaseCategory.DEVIATION, 2, LessonOutcome.COMPREHENSION_VERIFIED)

        assert tracker.total_lessons == 2
        assert tracker.get_agent_disease_count("agent-a", DiseaseCategory.DEVIATION) == 2


# ─── Transpose Layer ──────────────────────────────────────────────────


class TestTransposeLayerLive:
    @pytest.mark.asyncio
    async def test_full_roundtrip(self):
        """Verify object → HTML → object roundtrip for all types."""
        from fleet.core.transpose import to_html, from_html, get_artifact_type

        test_objects = {
            "analysis_document": {"title": "Test", "scope": "test", "findings": [{"title": "F1", "finding": "found"}]},
            "investigation_document": {"title": "Test", "findings": "found", "options": [{"name": "A", "pros": "good", "cons": "bad"}]},
            "plan": {"title": "Test", "approach": "do it", "target_files": ["f.py"], "steps": ["step 1"]},
            "bug": {"title": "Test", "steps_to_reproduce": ["step 1"], "expected_behavior": "works", "actual_behavior": "broken"},
            "completion_claim": {"pr_url": "https://github.com/pr/1", "summary": "done", "files_changed": ["f.py"]},
            "progress_update": {"what_was_done": "stuff", "readiness_before": 20, "readiness_after": 50},
        }

        for art_type, obj in test_objects.items():
            html = to_html(art_type, obj)
            assert "fleet-artifact-start" in html
            parsed = from_html(html)
            assert parsed is not None, f"Roundtrip failed for {art_type}"
            assert parsed.get("title") == obj.get("title"), f"Title mismatch for {art_type}"
            assert get_artifact_type(html) == art_type

    @pytest.mark.asyncio
    async def test_artifact_completeness(self):
        """Verify completeness checking against standards."""
        from fleet.core.artifact_tracker import check_artifact_completeness

        # Empty analysis — not complete
        result = check_artifact_completeness("analysis_document", {})
        assert not result.is_complete
        assert result.suggested_readiness == 0

        # Full analysis — complete
        result = check_artifact_completeness("analysis_document", {
            "title": "t", "scope": "s", "current_state": "c",
            "findings": [{"x": "y"}], "implications": "i",
        })
        assert result.is_complete
        assert result.suggested_readiness >= 90


# ─── Context System ───────────────────────────────────────────────────


class TestContextSystemLive:
    @pytest.mark.asyncio
    async def test_task_context_assembly(self, mc, board_id):
        """Verify task context assembles from live MC data."""
        from fleet.core.context_assembly import assemble_task_context, clear_context_cache

        clear_context_cache()
        tasks = await mc.list_tasks(board_id)
        if not tasks:
            pytest.skip("No tasks on board")

        task = tasks[0]
        result = await assemble_task_context(task, mc, board_id)

        assert "task" in result
        assert result["task"]["id"] == task.id
        assert "custom_fields" in result
        assert "methodology" in result
        assert "comments" in result
        assert "related_tasks" in result

    @pytest.mark.asyncio
    async def test_role_providers(self, mc, board_id):
        """Verify role providers return data from live fleet."""
        from fleet.core.role_providers import fleet_ops_provider, project_manager_provider

        tasks = await mc.list_tasks(board_id)
        agents = await mc.list_agents()

        ops_data = await fleet_ops_provider("fleet-ops", tasks, agents, mc, board_id)
        assert "pending_approvals" in ops_data
        assert "review_queue" in ops_data

        pm_data = await project_manager_provider("pm", tasks, agents, mc, board_id)
        assert "unassigned_tasks" in pm_data
        assert "progress" in pm_data

    @pytest.mark.asyncio
    async def test_preembed_generation(self, mc, board_id):
        """Verify pre-embed text generates from live task data."""
        from fleet.core.preembed import build_task_preembed, build_heartbeat_preembed

        tasks = await mc.list_tasks(board_id)
        if tasks:
            text = build_task_preembed(tasks[0])
            assert "TASK CONTEXT" in text
            # No size limit — FULL data

        hb_text = build_heartbeat_preembed(
            agent_name="fleet-ops", role="fleet-ops",
            assigned_tasks=tasks[:2] if tasks else [],
            agents_online=3, agents_total=10,
            fleet_mode="full-autonomous", fleet_phase="execution",
        )
        assert "HEARTBEAT CONTEXT" in hb_text


# ─── Control Surface ──────────────────────────────────────────────────


class TestControlSurfaceLive:
    @pytest.mark.asyncio
    async def test_fleet_mode_reader(self, mc, board_id):
        """Verify fleet_config can be read from live board."""
        from fleet.core.fleet_mode import read_fleet_control

        board_data = await mc.get_board(board_id)
        state = read_fleet_control(board_data)
        assert state.work_mode in [
            "full-autonomous", "project-management-work",
            "local-work-only", "finish-current-work", "work-paused",
        ]
        assert state.cycle_phase in [
            "execution", "planning", "analysis",
            "investigation", "review", "crisis-management",
        ]

    @pytest.mark.asyncio
    async def test_directives_parsing(self, mc, board_id):
        """Verify directive parsing works against live board memory."""
        from fleet.core.directives import parse_directives

        memory = await mc.list_memory(board_id, limit=20)
        directives = parse_directives(memory)
        # May be empty if no directives posted — that's OK
        assert isinstance(directives, list)


# ─── Event Display ────────────────────────────────────────────────────


class TestEventDisplayLive:
    @pytest.mark.asyncio
    async def test_all_renderers_handle_new_events(self):
        """Verify event display handles immune/teaching/methodology events."""
        from fleet.core.events import create_event
        from fleet.core.event_display import render_irc, render_board_memory, render_ntfy

        test_events = [
            create_event("fleet.immune.disease_detected", source="test", agent="arch", disease="deviation", signal="drifted"),
            create_event("fleet.immune.agent_pruned", source="test", agent="arch", reason="too sick"),
            create_event("fleet.teaching.lesson_started", source="test", agent="arch", disease="laziness"),
            create_event("fleet.teaching.comprehension_verified", source="test", agent="arch"),
            create_event("fleet.methodology.stage_changed", source="test", from_stage="analysis", to_stage="reasoning"),
            create_event("fleet.methodology.protocol_violation", source="test", agent="dev", violation="commit during conversation"),
        ]

        for event in test_events:
            irc = render_irc(event)
            assert len(irc) > 0, f"Empty IRC render for {event.type}"

            mem = render_board_memory(event)
            assert mem["content"], f"Empty board memory for {event.type}"
            assert len(mem["tags"]) > 0, f"No tags for {event.type}"

    @pytest.mark.asyncio
    async def test_system_tags_in_board_memory(self):
        """Verify system tags are added to board memory entries."""
        from fleet.core.events import create_event
        from fleet.core.event_display import render_board_memory

        immune_event = create_event("fleet.immune.agent_pruned", source="test", agent="x")
        mem = render_board_memory(immune_event)
        assert "immune-system" in mem["tags"]

        teaching_event = create_event("fleet.teaching.lesson_started", source="test", agent="x")
        mem = render_board_memory(teaching_event)
        assert "teaching-system" in mem["tags"]

        meth_event = create_event("fleet.methodology.stage_changed", source="test")
        mem = render_board_memory(meth_event)
        assert "methodology" in mem["tags"]


# ─── Gateway Client ───────────────────────────────────────────────────


class TestGatewayClientLive:
    @pytest.mark.asyncio
    async def test_gateway_functions_importable(self):
        """Verify gateway client functions are importable and callable."""
        from fleet.infra.gateway_client import (
            prune_agent,
            force_compact,
            inject_content,
            create_fresh_session,
        )
        # Don't actually call them — just verify they exist
        assert callable(prune_agent)
        assert callable(force_compact)
        assert callable(inject_content)
        assert callable(create_fresh_session)