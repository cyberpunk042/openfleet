"""Tests for skill enforcement — required tool usage per task type."""

from fleet.core.skill_enforcement import check_compliance, get_required_tools


def test_code_task_compliant():
    report = check_compliance("task", [
        "fleet_read_context", "fleet_task_accept", "fleet_commit", "fleet_task_complete",
    ])
    assert report.compliant
    assert report.confidence_penalty == 0


def test_code_task_missing_commit():
    report = check_compliance("task", [
        "fleet_read_context", "fleet_task_accept", "fleet_task_complete",
    ])
    assert not report.compliant
    assert "fleet_commit" in report.required_missed
    assert report.confidence_penalty >= 10


def test_epic_must_create_subtasks():
    report = check_compliance("epic", [
        "fleet_read_context", "fleet_agent_status", "fleet_task_accept",
    ])
    # Missing fleet_task_create
    assert not report.compliant
    assert "fleet_task_create" in report.required_missed


def test_epic_compliant():
    report = check_compliance("epic", [
        "fleet_read_context", "fleet_agent_status", "fleet_task_create", "fleet_task_accept",
    ])
    assert report.compliant


def test_review_must_use_approve():
    report = check_compliance("review", [
        "fleet_read_context", "fleet_agent_status",
    ])
    assert not report.compliant
    assert "fleet_approve" in report.required_missed


def test_story_requires_progress():
    report = check_compliance("story", [
        "fleet_read_context", "fleet_task_accept", "fleet_task_create",
        "fleet_commit", "fleet_task_complete",
    ])
    # Missing fleet_task_progress which is required for stories
    assert not report.compliant


def test_confidence_penalty_scales():
    report = check_compliance("task", [])  # Nothing used
    assert report.confidence_penalty == 30  # Max penalty (capped)


def test_get_required_tools():
    tools = get_required_tools("epic")
    assert "fleet_task_create" in tools
    assert "fleet_read_context" in tools


def test_unknown_type_falls_back_to_task():
    report = check_compliance("unknown_type", [
        "fleet_read_context", "fleet_task_accept", "fleet_commit", "fleet_task_complete",
    ])
    assert report.compliant