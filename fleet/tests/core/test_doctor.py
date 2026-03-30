"""Tests for fleet.core.doctor — the immune system doctor."""

import pytest
from fleet.core.doctor import (
    Severity,
    ResponseAction,
    Detection,
    AgentHealth,
    DoctorReport,
    detect_protocol_violation,
    detect_laziness,
    detect_stuck,
    detect_correction_threshold,
    decide_response,
    build_intervention,
)
from fleet.core.teaching import DiseaseCategory


class TestDetectProtocolViolation:
    def test_commit_during_conversation(self):
        d = detect_protocol_violation(
            "architect", "task-1", "conversation", ["fleet_commit"]
        )
        assert d is not None
        assert d.disease == DiseaseCategory.PROTOCOL_VIOLATION
        assert "fleet_commit" in d.evidence

    def test_complete_during_analysis(self):
        d = detect_protocol_violation(
            "architect", "task-1", "analysis", ["fleet_task_complete"]
        )
        assert d is not None

    def test_commit_during_work_ok(self):
        d = detect_protocol_violation(
            "architect", "task-1", "work", ["fleet_commit"]
        )
        assert d is None

    def test_read_context_during_conversation_ok(self):
        d = detect_protocol_violation(
            "architect", "task-1", "conversation", ["fleet_read_context"]
        )
        assert d is None

    def test_no_stage_no_detection(self):
        d = detect_protocol_violation(
            "architect", "task-1", None, ["fleet_commit"]
        )
        assert d is None

    def test_reasoning_stage_allows_commit(self):
        d = detect_protocol_violation(
            "architect", "task-1", "reasoning", ["fleet_commit"]
        )
        assert d is None  # reasoning is not in non_work_stages


class TestDetectLaziness:
    def test_fast_completion(self):
        d = detect_laziness(
            "backend-dev", "task-1",
            story_points=5,
            time_to_complete_minutes=3,
        )
        assert d is not None
        assert d.disease == DiseaseCategory.LAZINESS
        assert "fast" in d.signal.lower()

    def test_normal_speed_ok(self):
        d = detect_laziness(
            "backend-dev", "task-1",
            story_points=5,
            time_to_complete_minutes=30,
        )
        assert d is None

    def test_small_task_not_flagged(self):
        d = detect_laziness(
            "backend-dev", "task-1",
            story_points=1,
            time_to_complete_minutes=1,
        )
        assert d is None  # small tasks can be fast

    def test_partial_criteria(self):
        d = detect_laziness(
            "backend-dev", "task-1",
            story_points=None,
            time_to_complete_minutes=None,
            acceptance_criteria_total=7,
            acceptance_criteria_met=3,
        )
        assert d is not None
        assert "3/7" in d.evidence

    def test_criteria_mostly_met_ok(self):
        d = detect_laziness(
            "backend-dev", "task-1",
            story_points=None,
            time_to_complete_minutes=None,
            acceptance_criteria_total=7,
            acceptance_criteria_met=6,
        )
        assert d is None  # 6/7 > 80%


class TestDetectStuck:
    def test_stuck_no_commits(self):
        d = detect_stuck(
            "architect", "task-1",
            minutes_since_last_activity=90,
            has_commits=False,
        )
        assert d is not None
        assert "stuck" in d.signal.lower()

    def test_active_agent_ok(self):
        d = detect_stuck(
            "architect", "task-1",
            minutes_since_last_activity=10,
            has_commits=False,
        )
        assert d is None

    def test_has_commits_ok(self):
        d = detect_stuck(
            "architect", "task-1",
            minutes_since_last_activity=90,
            has_commits=True,
        )
        assert d is None

    def test_no_activity_data(self):
        d = detect_stuck("architect", "task-1", None)
        assert d is None


class TestDetectCorrectionThreshold:
    def test_below_threshold(self):
        d = detect_correction_threshold("agent", "task-1", 2)
        assert d is None

    def test_at_threshold(self):
        d = detect_correction_threshold("agent", "task-1", 3)
        assert d is not None
        assert d.disease == DiseaseCategory.CONFIDENT_BUT_WRONG
        assert d.suggested_action == ResponseAction.PRUNE

    def test_above_threshold(self):
        d = detect_correction_threshold("agent", "task-1", 5)
        assert d is not None
        assert d.severity == Severity.HIGH

    def test_custom_threshold(self):
        d = detect_correction_threshold("agent", "task-1", 4, threshold=5)
        assert d is None


class TestDecideResponse:
    def test_medium_severity_teaches(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.MEDIUM,
            signal="drifted",
        )
        health = AgentHealth(agent_name="agent")
        assert decide_response(detection, health) == ResponseAction.TRIGGER_TEACHING

    def test_critical_prunes(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.CRITICAL,
            signal="severe",
        )
        health = AgentHealth(agent_name="agent")
        assert decide_response(detection, health) == ResponseAction.PRUNE

    def test_three_corrections_prunes(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.MEDIUM,
            signal="drifted",
        )
        health = AgentHealth(agent_name="agent", correction_count=3)
        assert decide_response(detection, health) == ResponseAction.PRUNE

    def test_high_severity_repeat_offender_prunes(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.HIGH,
            signal="drifted",
        )
        health = AgentHealth(agent_name="agent", total_lessons=2)
        assert decide_response(detection, health) == ResponseAction.PRUNE

    def test_high_severity_first_time_teaches(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.HIGH,
            signal="drifted",
        )
        health = AgentHealth(agent_name="agent", total_lessons=0)
        assert decide_response(detection, health) == ResponseAction.TRIGGER_TEACHING

    def test_agent_in_lesson_no_action(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.MEDIUM,
            signal="drifted",
        )
        health = AgentHealth(agent_name="agent", is_in_lesson=True)
        assert decide_response(detection, health) == ResponseAction.NONE

    def test_stuck_gets_compact(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.DEVIATION,
            severity=Severity.LOW,
            signal="stuck",
            suggested_action=ResponseAction.FORCE_COMPACT,
        )
        health = AgentHealth(agent_name="agent")
        assert decide_response(detection, health) == ResponseAction.FORCE_COMPACT


class TestBuildIntervention:
    def test_basic_intervention(self):
        detection = Detection(
            agent_name="agent", task_id="t1",
            disease=DiseaseCategory.LAZINESS,
            severity=Severity.MEDIUM,
            signal="partial work",
        )
        intervention = build_intervention(
            detection, ResponseAction.TRIGGER_TEACHING,
            lesson_context={"requirement_verbatim": "do all the things"},
        )
        assert intervention.agent_name == "agent"
        assert intervention.action == ResponseAction.TRIGGER_TEACHING
        assert intervention.disease == DiseaseCategory.LAZINESS
        assert "partial work" in intervention.reason


class TestDoctorReport:
    def test_empty_report(self):
        report = DoctorReport()
        assert not report.has_findings
        assert not report.has_interventions
        assert len(report.agents_to_skip) == 0

    def test_report_with_detection(self):
        report = DoctorReport(
            detections=[
                Detection(
                    agent_name="agent", task_id="t1",
                    disease=DiseaseCategory.DEVIATION,
                    severity=Severity.MEDIUM,
                    signal="drifted",
                )
            ],
        )
        assert report.has_findings