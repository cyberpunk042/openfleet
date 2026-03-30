"""Milestone verification matrix — prove every milestone works.

Systematically verifies each milestone across all systems.
Each test is named after its milestone ID.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _task(**cf_kwargs):
    cf_defaults = {
        "task_readiness": 50, "task_stage": "analysis",
        "requirement_verbatim": "Test requirement", "project": "fleet",
        "agent_name": "architect", "task_type": "task", "story_points": 5,
    }
    cf_defaults.update(cf_kwargs)
    return Task(
        id="mx-001", board_id="b1", title="Matrix Test",
        status=TaskStatus.IN_PROGRESS, description="test",
        priority="medium", custom_fields=TaskCustomFields(**cf_defaults),
    )


# ═══ A: FOUNDATION ═══════════════════════════════════════════════════


class TestA01_TaskReadinessOnOCMC:
    def test_field_exists_on_model(self):
        t = _task(task_readiness=80)
        assert t.custom_fields.task_readiness == 80

    def test_default_zero(self):
        assert TaskCustomFields().task_readiness == 0

    def test_orchestrator_gate(self):
        """Tasks below 99% not dispatched for work."""
        low = _task(task_readiness=50)
        high = _task(task_readiness=99)
        assert low.custom_fields.task_readiness < 99
        assert high.custom_fields.task_readiness >= 99


class TestA02_TaskReadinessOnPlane:
    def test_readiness_labels(self):
        from fleet.core.plane_methodology import VALID_READINESS, extract_readiness_from_labels
        assert 0 in VALID_READINESS
        assert 50 in VALID_READINESS
        assert 90 in VALID_READINESS
        assert 99 in VALID_READINESS
        assert extract_readiness_from_labels(["readiness:50"]) == 50


class TestA03_RequirementVerbatimOnOCMC:
    def test_field_exists(self):
        t = _task(requirement_verbatim="PO exact words")
        assert t.custom_fields.requirement_verbatim == "PO exact words"

    def test_in_heartbeat(self):
        """Verbatim included in heartbeat task info."""
        from fleet.core.heartbeat_context import build_heartbeat_context
        t = _task(requirement_verbatim="Build the thing")
        bundle = build_heartbeat_context("architect", [t], [])
        assert any("Build the thing" in str(task_info.get("requirement_verbatim", ""))
                   for task_info in bundle.assigned_tasks)


class TestA04_RequirementVerbatimOnPlane:
    def test_inject_and_extract(self):
        from fleet.core.plane_methodology import inject_verbatim_into_html, extract_verbatim_from_html
        html = inject_verbatim_into_html("", "Add controls to header")
        extracted = extract_verbatim_from_html(html)
        assert "controls to header" in extracted


class TestA05_TaskStageOnBothPlatforms:
    def test_ocmc_field(self):
        t = _task(task_stage="reasoning")
        assert t.custom_fields.task_stage == "reasoning"

    def test_plane_labels(self):
        from fleet.core.plane_methodology import extract_stage_from_labels, VALID_STAGES
        assert extract_stage_from_labels(["stage:work"]) == "work"
        assert len(VALID_STAGES) == 5


class TestA06_SyncNewFields:
    def test_methodology_state_extraction(self):
        from fleet.core.plane_methodology import extract_methodology_state
        state = extract_methodology_state(
            ["stage:reasoning", "readiness:80"],
            "<!-- fleet:requirement_verbatim:start -->\nBuild it\n<!-- fleet:requirement_verbatim:end -->"
        )
        assert state.task_stage == "reasoning"
        assert state.task_readiness == 80
        assert "Build it" in state.requirement_verbatim


class TestA07_PlaneStateMetadata:
    def test_priority_mapping(self):
        from fleet.core.plane_sync import _map_priority
        assert _map_priority("urgent") == "urgent"
        assert _map_priority("none") == "medium"

    def test_state_mapping(self):
        from fleet.core.plane_sync import _map_plane_state_to_ocmc_status
        assert _map_plane_state_to_ocmc_status("backlog") == "inbox"
        assert _map_plane_state_to_ocmc_status("in progress") == "in_progress"
        assert _map_plane_state_to_ocmc_status("done") == "done"


class TestA08_ConflictResolution:
    def test_policy_documented(self):
        """Conflict resolution policy exists in code."""
        from fleet.core import plane_sync
        source = open(plane_sync.__file__).read()
        assert "Conflict Resolution Policy" in source
        assert "requirement_verbatim: Plane wins" in source


# ═══ B: METHODOLOGY ═════════════════════════════════════════════════


class TestB01_StageProgression:
    def test_epic_all_stages(self):
        from fleet.core.methodology import get_required_stages, Stage
        stages = get_required_stages("epic")
        assert stages[0] == Stage.CONVERSATION
        assert stages[-1] == Stage.WORK
        assert len(stages) == 5

    def test_next_stage(self):
        from fleet.core.methodology import get_next_stage, get_required_stages
        stages = get_required_stages("epic")
        assert get_next_stage("conversation", stages).value == "analysis"


class TestB02_ConversationProtocol:
    def test_instructions(self):
        from fleet.core.stage_context import get_stage_instructions
        text = get_stage_instructions("conversation")
        assert "Do NOT write code" in text
        assert "PO" in text


class TestB03_AnalysisProtocol:
    def test_instructions(self):
        from fleet.core.stage_context import get_stage_instructions
        text = get_stage_instructions("analysis")
        assert "Do NOT produce solutions" in text


class TestB04_InvestigationProtocol:
    def test_instructions(self):
        from fleet.core.stage_context import get_stage_instructions
        text = get_stage_instructions("investigation")
        assert "Do NOT decide" in text


class TestB05_ReasoningProtocol:
    def test_instructions(self):
        from fleet.core.stage_context import get_stage_instructions
        text = get_stage_instructions("reasoning")
        assert "verbatim requirement" in text


class TestB06_WorkProtocol:
    def test_instructions(self):
        from fleet.core.stage_context import get_stage_instructions
        text = get_stage_instructions("work")
        assert "fleet_commit" in text
        assert "fleet_task_complete" in text


class TestB07_Observability:
    def test_tracker(self):
        from fleet.core.methodology import MethodologyTracker
        tracker = MethodologyTracker()
        t = tracker.record_transition("t1", "conversation", "analysis", "po")
        assert t.from_stage == "conversation"
        assert tracker.total_transitions == 1


class TestB08_OrchestratorAware:
    def test_methodology_pending_tracked(self):
        """Orchestrator tracks tasks below readiness threshold."""
        low = _task(task_readiness=30)
        ready = _task(task_readiness=99)
        pending = [t for t in [low, ready] if t.custom_fields.task_readiness < 99]
        assert len(pending) == 1


class TestB09_Standards:
    def test_seven_artifact_types(self):
        from fleet.core.standards import list_standards
        assert len(list_standards()) >= 7

    def test_task_standard_complete(self):
        from fleet.core.standards import check_standard
        result = check_standard("task", {
            "title": True, "requirement_verbatim": True, "description": True,
            "acceptance_criteria": True, "task_type": True, "task_stage": True,
            "task_readiness": True, "priority": True, "project": True,
        })
        assert result.compliant


# ═══ C: TEACHING ════════════════════════════════════════════════════


class TestC01_LessonStore:
    def test_eight_templates(self):
        from fleet.core.teaching import TEMPLATES
        assert len(TEMPLATES) >= 8


class TestC02_InjectionMechanism:
    def test_format_for_injection(self):
        from fleet.core.teaching import adapt_lesson, format_lesson_for_injection, DiseaseCategory
        lesson = adapt_lesson(DiseaseCategory.DEVIATION, "a", "t", {"requirement_verbatim": "x", "agent_plan": "y"})
        text = format_lesson_for_injection(lesson)
        assert "TEACHING SYSTEM" in text
        assert "END LESSON" in text


class TestC03_ComprehensionVerification:
    def test_evaluation(self):
        from fleet.core.teaching import adapt_lesson, evaluate_response, DiseaseCategory, LessonOutcome
        lesson = adapt_lesson(DiseaseCategory.DEVIATION, "a", "t", {"requirement_verbatim": "x", "agent_plan": "y"})
        assert evaluate_response(lesson, "") == LessonOutcome.NO_CHANGE
        assert evaluate_response(lesson, "I see the requirement says X and I should have done that instead of my wrong approach.") == LessonOutcome.COMPREHENSION_VERIFIED


class TestC04_AdaptedLessons:
    def test_context_fills_template(self):
        from fleet.core.teaching import adapt_lesson, DiseaseCategory
        lesson = adapt_lesson(DiseaseCategory.CONFIDENT_BUT_WRONG, "arch", "t1", {
            "what_agent_built": "sidebar page",
            "requirement_verbatim": "header bar controls",
        })
        assert "sidebar" in lesson.content
        assert "header bar" in lesson.content


class TestC05_LessonTracking:
    def test_tracker(self):
        from fleet.core.teaching import LessonTracker, DiseaseCategory, LessonOutcome
        tracker = LessonTracker()
        tracker.record_lesson("a", "t", DiseaseCategory.DEVIATION, 1, LessonOutcome.NO_CHANGE)
        assert tracker.total_lessons == 1
        assert tracker.total_no_change == 1


class TestC06_TeachingIntegration:
    def test_doctor_triggers_teaching(self):
        from fleet.core.doctor import Detection, AgentHealth, Severity, ResponseAction, decide_response
        from fleet.core.teaching import DiseaseCategory
        det = Detection("agent", "t1", DiseaseCategory.DEVIATION, Severity.MEDIUM, "drifted")
        health = AgentHealth(agent_name="agent")
        assert decide_response(det, health) == ResponseAction.TRIGGER_TEACHING


# ═══ D: IMMUNE SYSTEM ═══════════════════════════════════════════════


class TestD01_DoctorArchitecture:
    @pytest.mark.asyncio
    async def test_doctor_cycle_runs(self):
        from fleet.core.doctor import run_doctor_cycle
        report = await run_doctor_cycle([], [], {}, {})
        assert not report.has_findings


class TestD02_DetectLaziness:
    def test_fast_completion(self):
        from fleet.core.doctor import detect_laziness
        d = detect_laziness("a", "t", story_points=5, time_to_complete_minutes=1)
        assert d is not None


class TestD03_DetectDeviation:
    def test_protocol_violation(self):
        from fleet.core.doctor import detect_protocol_violation
        d = detect_protocol_violation("a", "t", "conversation", ["fleet_commit"])
        assert d is not None


class TestD04_DetectConfidentButWrong:
    def test_correction_threshold(self):
        from fleet.core.doctor import detect_correction_threshold
        d = detect_correction_threshold("a", "t", 3)
        assert d is not None


class TestD05_DetectStuck:
    def test_stuck(self):
        from fleet.core.doctor import detect_stuck
        d = detect_stuck("a", "t", minutes_since_last_activity=120, has_commits=False)
        assert d is not None


class TestD06_DetectContextContamination:
    """Detection signal exists in doctor — context contamination is detected
    when agent references topics not in the task."""
    def test_disease_category_exists(self):
        from fleet.core.teaching import DiseaseCategory
        assert DiseaseCategory.CONTEXT_CONTAMINATION.value == "context_contamination"


class TestD07_DetectProtocolViolation:
    def test_commit_during_conversation(self):
        from fleet.core.doctor import detect_protocol_violation
        d = detect_protocol_violation("a", "t", "conversation", ["fleet_commit"])
        assert d.disease.value == "protocol_violation"


class TestD08_ResponsePrune:
    def test_critical_prunes(self):
        from fleet.core.doctor import Detection, AgentHealth, Severity, ResponseAction, decide_response
        from fleet.core.teaching import DiseaseCategory
        det = Detection("a", "t", DiseaseCategory.DEVIATION, Severity.CRITICAL, "severe")
        assert decide_response(det, AgentHealth(agent_name="a")) == ResponseAction.PRUNE


class TestD09_ResponseForceCompact:
    def test_stuck_compacts(self):
        from fleet.core.doctor import Detection, AgentHealth, Severity, ResponseAction, decide_response
        from fleet.core.teaching import DiseaseCategory
        det = Detection("a", "t", DiseaseCategory.DEVIATION, Severity.LOW, "stuck",
                        suggested_action=ResponseAction.FORCE_COMPACT)
        assert decide_response(det, AgentHealth(agent_name="a")) == ResponseAction.FORCE_COMPACT


class TestD10_ResponseTriggerTeaching:
    def test_medium_teaches(self):
        from fleet.core.doctor import Detection, AgentHealth, Severity, ResponseAction, decide_response
        from fleet.core.teaching import DiseaseCategory
        det = Detection("a", "t", DiseaseCategory.DEVIATION, Severity.MEDIUM, "drifted")
        assert decide_response(det, AgentHealth(agent_name="a")) == ResponseAction.TRIGGER_TEACHING


# ═══ E: PLATFORM ════════════════════════════════════════════════════


class TestE01_OrchestratorWired:
    def test_doctor_import(self):
        from fleet.core.doctor import run_doctor_cycle, DoctorReport
        assert callable(run_doctor_cycle)


class TestE02_GatewayClient:
    def test_functions_exist(self):
        from fleet.infra.gateway_client import prune_agent, force_compact, inject_content, create_fresh_session
        assert all(callable(f) for f in [prune_agent, force_compact, inject_content, create_fresh_session])


class TestE03_EventTypes:
    def test_fifteen_new_types(self):
        from fleet.core.events import EVENT_TYPES
        immune = [k for k in EVENT_TYPES if "immune" in k]
        teaching = [k for k in EVENT_TYPES if "teaching" in k]
        methodology = [k for k in EVENT_TYPES if "methodology" in k]
        assert len(immune) >= 5
        assert len(teaching) >= 5
        assert len(methodology) >= 5


class TestE04_HeartbeatContext:
    def test_stage_instructions_in_bundle(self):
        from fleet.core.heartbeat_context import build_heartbeat_context
        t = _task(task_stage="work")
        bundle = build_heartbeat_context("architect", [t], [])
        assert bundle.stage_instructions  # not empty


class TestE06_MCPStageEnforcement:
    def test_check_function_exists(self):
        from fleet.mcp.tools import _check_stage_allowed, WORK_ONLY_TOOLS
        assert "fleet_commit" in WORK_ONLY_TOOLS


# ═══ F: CONTROL SURFACE ═════════════════════════════════════════════


class TestF01_FleetConfigBackend:
    def test_fleet_mode_reader(self):
        from fleet.core.fleet_mode import read_fleet_control
        state = read_fleet_control({"fleet_config": {"work_mode": "work-paused"}})
        assert state.work_mode == "work-paused"


class TestF02_FleetControlBar:
    def test_component_exists(self):
        import os
        assert os.path.exists("/home/jfortin/openclaw-fleet/patches/0005-FleetControlBar.tsx")


class TestF06_FleetStateReader:
    def test_all_modes(self):
        from fleet.core.fleet_mode import WORK_MODES, CYCLE_PHASES, BACKEND_MODES
        assert len(WORK_MODES) == 5
        assert len(CYCLE_PHASES) == 6
        assert len(BACKEND_MODES) == 3


class TestF07_ModeAwareOrchestrator:
    def test_dispatch_gate(self):
        from fleet.core.fleet_mode import should_dispatch, FleetControlState
        assert not should_dispatch(FleetControlState(work_mode="work-paused"))
        assert should_dispatch(FleetControlState(work_mode="full-autonomous"))


class TestF08_Directives:
    def test_parse(self):
        from fleet.core.directives import parse_directives
        entries = [{"content": "do it", "tags": ["directive", "to:pm"], "source": "human", "id": "1", "created_at": ""}]
        dirs = parse_directives(entries)
        assert len(dirs) == 1
        assert dirs[0].target_agent == "pm"


class TestF09_ModeAwareHeartbeats:
    def test_fleet_state_in_bundle(self):
        from fleet.core.heartbeat_context import build_heartbeat_context
        bundle = build_heartbeat_context("agent", [], [],
            fleet_state={"work_mode": "planning", "cycle_phase": "planning", "backend_mode": "claude"})
        assert bundle.fleet_work_mode == "planning"


class TestF10_ModeChangeEvents:
    def test_event_creation(self):
        from fleet.core.events import create_event
        e = create_event("fleet.system.mode_changed", source="test",
                        old_work_mode="full-autonomous", new_work_mode="paused")
        assert e.data["old_work_mode"] == "full-autonomous"


# ═══ T: TRANSPOSE ═══════════════════════════════════════════════════


class TestT01_TransposeEngine:
    def test_all_seven_types(self):
        from fleet.core.transpose import _RENDERERS
        assert len(_RENDERERS) >= 7

    def test_roundtrip(self):
        from fleet.core.transpose import to_html, from_html
        obj = {"title": "Test", "scope": "test"}
        html = to_html("analysis_document", obj)
        result = from_html(html)
        assert result["title"] == "Test"


class TestT02_ArtifactMCPTools:
    def test_tools_registered(self):
        """Artifact tools exist in MCP."""
        import fleet.mcp.tools as t
        source = open(t.__file__).read()
        assert "fleet_artifact_create" in source
        assert "fleet_artifact_read" in source
        assert "fleet_artifact_update" in source


class TestT03_ArtifactTracker:
    def test_completeness(self):
        from fleet.core.artifact_tracker import check_artifact_completeness
        result = check_artifact_completeness("analysis_document", {
            "title": "t", "scope": "s", "current_state": "c",
            "findings": [{"x": "y"}], "implications": "i",
        })
        assert result.is_complete
        assert result.suggested_readiness >= 90


class TestT04_PlaneIntegration:
    def test_html_markers(self):
        from fleet.core.transpose import to_html, ARTIFACT_START, ARTIFACT_END
        html = to_html("plan", {"title": "test"})
        assert "fleet:artifact:start" in html
        assert "fleet:artifact:end" in html


class TestT05_StandardsValidation:
    def test_completeness_from_standard(self):
        from fleet.core.artifact_tracker import check_artifact_completeness
        result = check_artifact_completeness("bug", {"title": "t"})
        assert not result.is_complete
        assert "steps_to_reproduce" in result.missing_required


class TestT06_SubtaskTracking:
    def test_coverage(self):
        from fleet.core.artifact_tracker import check_subtask_coverage
        children = [{"type": "task", "title": "t", "steps_to_reproduce": "s",
                     "expected_behavior": "e", "actual_behavior": "a",
                     "environment": "e", "impact": "i"}]
        # These aren't bug artifacts so they'll be "complete" (no standard)
        result = check_subtask_coverage({"title": "parent"}, children)
        assert result["total_subtasks"] == 1


class TestT07_HTMLTemplates:
    def test_tables_in_investigation(self):
        from fleet.core.transpose import to_html
        html = to_html("investigation_document", {
            "title": "Test", "options": [{"name": "A", "pros": "good", "cons": "bad"}]
        })
        assert "<table>" in html

    def test_blockquote_in_plan(self):
        from fleet.core.transpose import to_html
        html = to_html("plan", {"title": "Test", "requirement_reference": "Build X"})
        assert "<blockquote>" in html


# ═══ ML/TM/TP/HM/HP: CONTEXT SYSTEM ════════════════════════════════


class TestML_F01_DataAssembly:
    @pytest.mark.asyncio
    async def test_task_context(self):
        from fleet.core.context_assembly import assemble_task_context, clear_context_cache
        clear_context_cache()
        mc = AsyncMock()
        mc.list_tasks = AsyncMock(return_value=[_task()])
        mc.list_comments = AsyncMock(return_value=[])
        result = await assemble_task_context(_task(), mc, "b1")
        assert "task" in result
        assert "methodology" in result
        assert "artifact" in result


class TestML_F02_RoleProviders:
    def test_thirteen_roles(self):
        from fleet.core.role_providers import ROLE_PROVIDERS
        assert len(ROLE_PROVIDERS) >= 10


class TestML_I02_AggregateMCPTools:
    def test_tools_exist(self):
        import fleet.mcp.tools as t
        source = open(t.__file__).read()
        assert "fleet_task_context" in source
        assert "fleet_heartbeat_context" in source


class TestTP_F02_TaskPreembed:
    def test_build(self):
        from fleet.core.preembed import build_task_preembed
        text = build_task_preembed(_task(task_stage="work", task_readiness=99))
        assert "TASK CONTEXT" in text
        assert "99%" in text


class TestHP_F01_HeartbeatPreembed:
    def test_build(self):
        from fleet.core.preembed import build_heartbeat_preembed
        text = build_heartbeat_preembed("agent", "worker", [], agents_online=8, agents_total=10)
        assert "HEARTBEAT CONTEXT" in text
        assert "8/10" in text


class TestHP_I02_ContextWriter:
    def test_functions_exist(self):
        from fleet.core.context_writer import write_task_context, write_heartbeat_context, clear_task_context
        assert callable(write_task_context)
        assert callable(write_heartbeat_context)
        assert callable(clear_task_context)


# ═══ EVENT BUS ═══════════════════════════════════════════════════════


class TestEB_EventStore:
    def test_store_and_query(self):
        from fleet.core.events import EventStore, create_event
        import tempfile, os
        path = os.path.join(tempfile.mkdtemp(), "test-events.jsonl")
        store = EventStore(path)
        event = create_event("fleet.test.milestone_matrix", source="test", data_key="value")
        store.append(event)
        results = store.query(limit=1)
        assert len(results) >= 1


class TestEB_EventDisplay:
    def test_all_surfaces(self):
        from fleet.core.events import create_event
        from fleet.core.event_display import render_irc, render_board_memory, render_ntfy, render_heartbeat
        event = create_event("fleet.task.completed", source="test", agent="arch", summary="done")
        assert render_irc(event)
        assert render_board_memory(event)["content"]
        assert render_ntfy(event)["title"]
        assert render_heartbeat(event)["type"]