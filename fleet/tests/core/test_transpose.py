"""Tests for fleet.core.transpose — object ↔ rich HTML."""

import pytest
from fleet.core.transpose import (
    to_html,
    from_html,
    get_artifact_type,
    update_artifact,
)


class TestToHtml:
    def test_analysis_document(self):
        obj = {
            "title": "Header Structure",
            "scope": "DashboardShell.tsx",
            "findings": [
                {
                    "title": "Center section",
                    "finding": "Has flex-1 with only OrgSwitcher",
                    "files": ["DashboardShell.tsx"],
                    "implications": "Room for fleet controls",
                }
            ],
            "open_questions": ["What about mobile?"],
        }
        html = to_html("analysis_document", obj)
        assert "fleet:artifact:start" in html
        assert "fleet:artifact:end" in html
        assert "fleet:data:" in html
        assert "Header Structure" in html
        assert "DashboardShell.tsx" in html
        assert "<code>" in html
        assert "Room for fleet controls" in html
        assert "What about mobile?" in html

    def test_investigation_document(self):
        obj = {
            "title": "Plane Custom Fields",
            "scope": "Plane CE capabilities",
            "findings": "Plane CE lacks custom fields",
            "options": [
                {"name": "Labels", "pros": "Easy, filterable", "cons": "No numbers"},
                {"name": "HTML injection", "pros": "Flexible", "cons": "Complex"},
            ],
            "sources": ["Plane docs", "API testing"],
        }
        html = to_html("investigation_document", obj)
        assert "<table>" in html
        assert "Labels" in html
        assert "HTML injection" in html
        assert "Plane docs" in html

    def test_plan(self):
        obj = {
            "title": "Add FleetControlBar",
            "requirement_reference": "Add controls to the header bar",
            "approach": "Inject component into DashboardShell",
            "target_files": ["DashboardShell.tsx", "FleetControlBar.tsx"],
            "steps": ["Create component", "Add import", "Render in header"],
            "acceptance_criteria_mapping": {
                "Three dropdowns visible": "Select components for each axis",
            },
        }
        html = to_html("plan", obj)
        assert "<blockquote>" in html
        assert "header bar" in html
        assert "<ol>" in html
        assert "DashboardShell.tsx" in html

    def test_bug(self):
        obj = {
            "title": "Orchestrator NameError",
            "steps_to_reproduce": ["Start daemons", "Wait for cycle"],
            "expected_behavior": "Cycle completes",
            "actual_behavior": "NameError on DRIVER_AGENTS",
            "environment": "WSL2, MC running",
            "impact": "Fleet idle",
        }
        html = to_html("bug", obj)
        assert "NameError" in html
        assert "<ol>" in html
        assert "WSL2" in html

    def test_completion_claim(self):
        obj = {
            "pr_url": "https://github.com/org/repo/pull/42",
            "summary": "Added fleet controls to header",
            "acceptance_criteria_check": [
                {"criterion": "Three dropdowns", "met": True, "evidence": "Visible in header"},
                {"criterion": "PATCH on change", "met": True, "evidence": "fleet_config updated"},
            ],
            "files_changed": ["DashboardShell.tsx", "FleetControlBar.tsx"],
        }
        html = to_html("completion_claim", obj)
        assert "pull/42" in html
        assert "✓" in html
        assert "<table>" in html

    def test_progress_update(self):
        obj = {
            "what_was_done": "Examined 3 files",
            "what_is_next": "Examine remaining 4",
            "readiness_before": 20,
            "readiness_after": 30,
        }
        html = to_html("progress_update", obj)
        assert "Examined 3 files" in html
        assert "20%" in html
        assert "30%" in html

    def test_unknown_type_fallback(self):
        html = to_html("unknown_type", {"key": "value"})
        assert "unknown_type" in html
        assert "key" in html


class TestFromHtml:
    def test_roundtrip_analysis(self):
        obj = {
            "title": "Test Analysis",
            "scope": "test scope",
            "findings": [{"title": "F1", "finding": "found it"}],
        }
        html = to_html("analysis_document", obj)
        result = from_html(html)
        assert result is not None
        assert result["title"] == "Test Analysis"
        assert result["scope"] == "test scope"
        assert len(result["findings"]) == 1

    def test_roundtrip_plan(self):
        obj = {
            "title": "Test Plan",
            "approach": "Do the thing",
            "target_files": ["file.py"],
            "steps": ["Step 1", "Step 2"],
        }
        html = to_html("plan", obj)
        result = from_html(html)
        assert result is not None
        assert result["title"] == "Test Plan"
        assert result["target_files"] == ["file.py"]
        assert len(result["steps"]) == 2

    def test_no_artifact(self):
        assert from_html("<p>Just plain HTML</p>") is None

    def test_empty_html(self):
        assert from_html("") is None
        assert from_html(None) is None


class TestGetArtifactType:
    def test_analysis(self):
        html = to_html("analysis_document", {"title": "test"})
        assert get_artifact_type(html) == "analysis_document"

    def test_plan(self):
        html = to_html("plan", {"title": "test"})
        assert get_artifact_type(html) == "plan"

    def test_no_artifact(self):
        assert get_artifact_type("<p>plain</p>") is None


class TestUpdateArtifact:
    def test_add_finding(self):
        obj = {
            "title": "Analysis",
            "findings": [{"title": "F1", "finding": "first"}],
        }
        html = to_html("analysis_document", obj)

        updated_html = update_artifact(html, {
            "findings": [{"title": "F2", "finding": "second"}],
        })

        result = from_html(updated_html)
        assert len(result["findings"]) == 2
        assert result["findings"][1]["title"] == "F2"

    def test_update_field(self):
        obj = {"title": "Old", "scope": "old scope"}
        html = to_html("analysis_document", obj)

        updated_html = update_artifact(html, {"scope": "new scope"})

        result = from_html(updated_html)
        assert result["scope"] == "new scope"

    def test_update_no_artifact(self):
        html = "<p>plain</p>"
        result = update_artifact(html, {"title": "new"})
        assert result == html  # unchanged