"""Tests for fleet.core.artifact_tracker — progressive work tracking."""

import pytest
from fleet.core.artifact_tracker import (
    check_artifact_completeness,
    format_completeness_summary,
)


class TestAnalysisCompleteness:
    def test_empty_analysis(self):
        result = check_artifact_completeness("analysis_document", {})
        assert not result.is_complete
        assert result.required_pct == 0
        assert result.suggested_readiness == 0
        assert "title" in result.missing_required

    def test_partial_analysis(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "Header Analysis",
            "scope": "DashboardShell.tsx",
        })
        assert not result.is_complete
        assert result.required_pct > 0
        assert result.required_pct < 100
        assert "title" not in result.missing_required
        assert "scope" not in result.missing_required
        assert "findings" in result.missing_required

    def test_complete_analysis(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "Header Analysis",
            "scope": "DashboardShell.tsx",
            "current_state": "Three sections in header",
            "findings": [{"title": "F1", "finding": "Room for controls"}],
            "implications": "Can inject FleetControlBar",
        })
        assert result.is_complete
        assert result.required_pct == 100
        assert result.suggested_readiness >= 90


class TestPlanCompleteness:
    def test_empty_plan(self):
        result = check_artifact_completeness("plan", {})
        assert not result.is_complete
        assert result.suggested_readiness == 0

    def test_plan_with_requirement(self):
        result = check_artifact_completeness("plan", {
            "title": "Add FleetControlBar",
            "requirement_reference": "Add controls to the header bar",
            "approach": "Inject into DashboardShell",
            "target_files": ["DashboardShell.tsx"],
            "steps": ["Create component", "Add import"],
            "acceptance_criteria_mapping": {"Three dropdowns": "Select components"},
        })
        assert result.is_complete
        assert result.required_pct == 100


class TestBugCompleteness:
    def test_minimal_bug(self):
        result = check_artifact_completeness("bug", {
            "title": "Crash",
        })
        assert not result.is_complete
        assert "steps_to_reproduce" in result.missing_required

    def test_full_bug(self):
        result = check_artifact_completeness("bug", {
            "title": "Orchestrator NameError",
            "steps_to_reproduce": ["Start daemons", "Wait"],
            "expected_behavior": "Completes",
            "actual_behavior": "NameError",
            "environment": "WSL2",
            "impact": "Fleet idle",
        })
        assert result.is_complete


class TestReadinessSuggestion:
    def test_zero(self):
        result = check_artifact_completeness("analysis_document", {})
        assert result.suggested_readiness == 0

    def test_early(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "Test",
        })
        assert result.suggested_readiness in (10, 20)

    def test_half(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "Test",
            "scope": "test",
            "current_state": "test",
        })
        assert result.suggested_readiness >= 50

    def test_complete(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "t", "scope": "s", "current_state": "c",
            "findings": [{"x": "y"}], "implications": "i",
        })
        assert result.suggested_readiness >= 90


class TestUnknownType:
    def test_unknown_artifact(self):
        result = check_artifact_completeness("unknown_thing", {"foo": "bar"})
        assert result.total_required == 0
        assert result.is_complete  # no standard = nothing to fail


class TestFormatSummary:
    def test_incomplete(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "Test",
        })
        summary = format_completeness_summary(result)
        assert "IN PROGRESS" in summary
        assert "Missing:" in summary
        assert "Suggested readiness:" in summary

    def test_complete(self):
        result = check_artifact_completeness("analysis_document", {
            "title": "t", "scope": "s", "current_state": "c",
            "findings": [{"x": "y"}], "implications": "i",
        })
        summary = format_completeness_summary(result)
        assert "COMPLETE" in summary