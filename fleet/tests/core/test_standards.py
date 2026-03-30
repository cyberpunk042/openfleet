"""Tests for fleet.core.standards — standards library."""

import pytest
from fleet.core.standards import (
    STANDARDS,
    get_standard,
    list_standards,
    check_standard,
)


class TestRegistry:
    def test_standards_registered(self):
        assert len(STANDARDS) >= 7

    def test_task_standard_exists(self):
        assert "task" in STANDARDS

    def test_bug_standard_exists(self):
        assert "bug" in STANDARDS

    def test_plan_standard_exists(self):
        assert "plan" in STANDARDS

    def test_pull_request_standard_exists(self):
        assert "pull_request" in STANDARDS

    def test_completion_claim_exists(self):
        assert "completion_claim" in STANDARDS

    def test_analysis_document_exists(self):
        assert "analysis_document" in STANDARDS

    def test_investigation_document_exists(self):
        assert "investigation_document" in STANDARDS


class TestGetStandard:
    def test_known_type(self):
        s = get_standard("task")
        assert s is not None
        assert s.artifact_type == "task"

    def test_unknown_type(self):
        assert get_standard("nonexistent") is None

    def test_task_has_required_fields(self):
        s = get_standard("task")
        names = [f.name for f in s.required_fields]
        assert "title" in names
        assert "requirement_verbatim" in names
        assert "acceptance_criteria" in names

    def test_bug_has_required_fields(self):
        s = get_standard("bug")
        names = [f.name for f in s.required_fields]
        assert "steps_to_reproduce" in names
        assert "expected_behavior" in names
        assert "actual_behavior" in names

    def test_plan_references_requirement(self):
        s = get_standard("plan")
        names = [f.name for f in s.required_fields]
        assert "requirement_reference" in names
        assert "target_files" in names


class TestListStandards:
    def test_returns_list(self):
        standards = list_standards()
        assert isinstance(standards, list)
        assert len(standards) >= 7

    def test_all_have_descriptions(self):
        for s in list_standards():
            assert s.description, f"{s.artifact_type} has no description"

    def test_all_have_required_fields(self):
        for s in list_standards():
            assert len(s.required_fields) > 0, f"{s.artifact_type} has no required fields"

    def test_all_have_quality_criteria(self):
        for s in list_standards():
            assert len(s.quality_criteria) > 0, f"{s.artifact_type} has no quality criteria"


class TestCheckStandard:
    def test_fully_compliant(self):
        result = check_standard("task", {
            "title": True,
            "requirement_verbatim": True,
            "description": True,
            "acceptance_criteria": True,
            "task_type": True,
            "task_stage": True,
            "task_readiness": True,
            "priority": True,
            "project": True,
        })
        assert result.compliant
        assert result.score == 100
        assert len(result.missing_fields) == 0

    def test_missing_required_fields(self):
        result = check_standard("task", {
            "title": True,
            # requirement_verbatim missing
            "description": True,
            # acceptance_criteria missing
        })
        assert not result.compliant
        assert "requirement_verbatim" in result.missing_fields
        assert "acceptance_criteria" in result.missing_fields

    def test_optional_fields_not_blocking(self):
        # agent_name and story_points are optional on task
        result = check_standard("task", {
            "title": True,
            "requirement_verbatim": True,
            "description": True,
            "acceptance_criteria": True,
            "task_type": True,
            "task_stage": True,
            "task_readiness": True,
            "priority": True,
            "project": True,
            # agent_name and story_points NOT provided — they're optional
        })
        assert result.compliant

    def test_unknown_artifact_type(self):
        result = check_standard("nonexistent", {"title": True})
        assert result.compliant  # no standard = nothing to fail
        assert result.score == 100

    def test_score_decreases_with_missing(self):
        result = check_standard("task", {"title": True})
        assert result.score < 100

    def test_score_partial_compliance(self):
        result = check_standard("task", {
            "title": True,
            "requirement_verbatim": True,
            "description": True,
            "acceptance_criteria": True,
            "task_type": True,
            "task_stage": True,
            # missing: task_readiness, priority, project (3 fields)
        })
        assert 0 < result.score < 100

    def test_bug_compliance(self):
        result = check_standard("bug", {
            "title": True,
            "steps_to_reproduce": True,
            "expected_behavior": True,
            "actual_behavior": True,
            "environment": True,
            "impact": True,
        })
        assert result.compliant

    def test_bug_missing_steps(self):
        result = check_standard("bug", {
            "title": True,
            "expected_behavior": True,
            "actual_behavior": True,
            "environment": True,
            "impact": True,
        })
        assert not result.compliant
        assert "steps_to_reproduce" in result.missing_fields

    def test_completion_claim_compliance(self):
        result = check_standard("completion_claim", {
            "pr_url": True,
            "summary": True,
            "acceptance_criteria_check": True,
            "files_changed": True,
        })
        assert result.compliant