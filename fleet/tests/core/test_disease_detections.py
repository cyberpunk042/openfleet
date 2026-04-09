"""Tests for the 7 new disease detection functions in fleet.core.doctor."""

import pytest
from fleet.core.doctor import (
    detect_scope_creep,
    detect_compression,
    detect_code_without_reading,
    detect_cascading_fix,
    detect_abstraction,
    detect_not_listening,
    DiseaseCategory,
    Severity,
)


class TestScopeCreep:
    def test_no_creep_within_plan(self):
        d = detect_scope_creep("eng", "t1", ["a.py", "b.py"], ["a.py", "b.py", "c.py"])
        assert d is None

    def test_creep_with_many_extra_files(self):
        d = detect_scope_creep("eng", "t1",
            ["a.py", "b.py", "x.py", "y.py", "z.py"],
            ["a.py", "b.py"])
        assert d is not None
        assert d.disease == DiseaseCategory.SCOPE_CREEP

    def test_small_incidental_allowed(self):
        # 1-2 extra files are tolerated (test helpers, imports)
        d = detect_scope_creep("eng", "t1", ["a.py", "b.py", "c.py"], ["a.py", "b.py"])
        assert d is None

    def test_no_data_returns_none(self):
        assert detect_scope_creep("eng", "t1", [], []) is None
        assert detect_scope_creep("eng", "t1", ["a.py"], []) is None


class TestCompression:
    def test_no_compression_similar_length(self):
        d = detect_compression("eng", "t1", 100, 80)
        assert d is None

    def test_compression_detected(self):
        d = detect_compression("eng", "t1", 200, 30)
        assert d is not None
        assert d.disease == DiseaseCategory.COMPRESSION

    def test_short_verbatim_ignored(self):
        d = detect_compression("eng", "t1", 10, 3)
        assert d is None


class TestCodeWithoutReading:
    def test_reads_before_writes_ok(self):
        d = detect_code_without_reading("eng", "t1",
            ["Read", "fleet_commit"], has_read_calls=True)
        assert d is None

    def test_writes_without_reads_detected(self):
        d = detect_code_without_reading("eng", "t1",
            ["fleet_commit"], has_read_calls=False)
        assert d is not None
        assert d.disease == DiseaseCategory.CODE_WITHOUT_READING

    def test_no_writes_no_detection(self):
        d = detect_code_without_reading("eng", "t1",
            ["fleet_chat"], has_read_calls=False)
        assert d is None

    def test_fleet_read_context_counts(self):
        d = detect_code_without_reading("eng", "t1",
            ["fleet_read_context", "fleet_commit"], has_read_calls=False)
        assert d is None  # fleet_read_context counts as a read


class TestCascadingFix:
    def test_first_attempt_ok(self):
        assert detect_cascading_fix("eng", "t1", 1) is None

    def test_second_attempt_ok(self):
        assert detect_cascading_fix("eng", "t1", 2) is None

    def test_third_attempt_detected(self):
        d = detect_cascading_fix("eng", "t1", 3)
        assert d is not None
        assert d.disease == DiseaseCategory.CASCADING_FIX
        assert d.severity == Severity.HIGH

    def test_fourth_attempt_also_detected(self):
        d = detect_cascading_fix("eng", "t1", 4)
        assert d is not None


class TestAbstraction:
    def test_specific_terms_preserved(self):
        d = detect_abstraction("eng", "t1",
            "Build FleetControlBar with SelectDropdown in DashboardShell header",
            "Build FleetControlBar with SelectDropdown in DashboardShell header")
        assert d is None

    def test_terms_abstracted_away(self):
        d = detect_abstraction("eng", "t1",
            "Build FleetControlBar with SelectDropdown in DashboardShell header using ReactComponent",
            "Build a control component with dropdowns in the main layout")
        assert d is not None
        assert d.disease == DiseaseCategory.ABSTRACTION

    def test_no_verbatim_returns_none(self):
        assert detect_abstraction("eng", "t1", "", "something") is None
        assert detect_abstraction("eng", "t1", "something", "") is None


class TestNotListening:
    def test_questions_answered(self):
        d = detect_not_listening("eng", "t1", po_questions_count=3, agent_answers_count=3)
        assert d is None

    def test_questions_unanswered(self):
        d = detect_not_listening("eng", "t1", po_questions_count=3, agent_answers_count=0)
        assert d is not None
        assert d.disease == DiseaseCategory.NOT_LISTENING

    def test_no_questions_ok(self):
        d = detect_not_listening("eng", "t1", po_questions_count=0, agent_answers_count=0)
        assert d is None
