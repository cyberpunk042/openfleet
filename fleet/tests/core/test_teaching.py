"""Tests for fleet.core.teaching — teaching system."""

import pytest
from fleet.core.teaching import (
    DiseaseCategory,
    LessonOutcome,
    TEMPLATES,
    adapt_lesson,
    format_lesson_for_injection,
    evaluate_response,
)


class TestTemplates:
    def test_all_major_diseases_covered(self):
        assert DiseaseCategory.DEVIATION in TEMPLATES
        assert DiseaseCategory.LAZINESS in TEMPLATES
        assert DiseaseCategory.CONFIDENT_BUT_WRONG in TEMPLATES
        assert DiseaseCategory.PROTOCOL_VIOLATION in TEMPLATES
        assert DiseaseCategory.ABSTRACTION in TEMPLATES
        assert DiseaseCategory.CODE_WITHOUT_READING in TEMPLATES
        assert DiseaseCategory.SCOPE_CREEP in TEMPLATES
        assert DiseaseCategory.COMPRESSION in TEMPLATES

    def test_all_templates_have_content(self):
        for disease, template in TEMPLATES.items():
            assert template.lesson_template, f"{disease} has no lesson template"
            assert template.exercise_template, f"{disease} has no exercise template"
            assert template.verification_hint_template, f"{disease} has no hint"


class TestAdaptLesson:
    def test_deviation_lesson(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="architect",
            task_id="task-42",
            context={
                "requirement_verbatim": "Add controls to the header bar",
                "agent_plan": "Create a sidebar page",
            },
        )
        assert lesson.disease == DiseaseCategory.DEVIATION
        assert lesson.agent_name == "architect"
        assert "header bar" in lesson.content
        assert "sidebar page" in lesson.content

    def test_laziness_lesson(self):
        lesson = adapt_lesson(
            DiseaseCategory.LAZINESS,
            agent_name="backend-dev",
            task_id="task-55",
            context={
                "requirement_summary": "Update all 7 call sites",
                "what_agent_did": "Updated 3 call sites",
                "what_is_missing": "4 call sites not updated",
            },
        )
        assert "7 call sites" in lesson.content
        assert "3 call sites" in lesson.content

    def test_confident_but_wrong_lesson(self):
        lesson = adapt_lesson(
            DiseaseCategory.CONFIDENT_BUT_WRONG,
            agent_name="architect",
            task_id="task-42",
            context={
                "what_agent_built": "A sidebar navigation page",
                "requirement_verbatim": "Add three Select dropdowns to the header",
            },
        )
        assert "sidebar" in lesson.content
        assert "header" in lesson.content
        assert "wrong" in lesson.content.lower()

    def test_protocol_violation_lesson(self):
        lesson = adapt_lesson(
            DiseaseCategory.PROTOCOL_VIOLATION,
            agent_name="devops-expert",
            task_id="task-10",
            context={
                "current_stage": "conversation",
                "allowed_actions": "discussing, asking questions, proposing",
                "what_agent_did": "committed code and created a PR",
            },
        )
        assert "conversation" in lesson.content
        assert "committed code" in lesson.content

    def test_unknown_disease_fallback(self):
        lesson = adapt_lesson(
            DiseaseCategory.NOT_LISTENING,  # no template for this
            agent_name="agent",
            task_id="task-1",
            context={},
        )
        assert lesson.content  # should have fallback content
        assert lesson.exercise.instruction  # should have fallback exercise

    def test_lesson_has_max_attempts(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="architect",
            task_id="task-42",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        assert lesson.max_attempts == 3
        assert lesson.attempt == 0


class TestFormatLesson:
    def test_has_markers(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "build X", "agent_plan": "build Y"},
        )
        text = format_lesson_for_injection(lesson)
        assert "TEACHING SYSTEM" in text
        assert "END LESSON" in text
        assert "Exercise" in text

    def test_includes_attempt_count(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        lesson.attempt = 1
        text = format_lesson_for_injection(lesson)
        assert "2/3" in text  # attempt 1 displays as 2/3

    def test_includes_prune_warning(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        text = format_lesson_for_injection(lesson)
        assert "pruned" in text.lower()


class TestEvaluateResponse:
    def test_empty_response(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        assert evaluate_response(lesson, "") == LessonOutcome.NO_CHANGE

    def test_just_acknowledge(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        assert evaluate_response(lesson, "I understand.") == LessonOutcome.NO_CHANGE

    def test_substantive_response(self):
        lesson = adapt_lesson(
            DiseaseCategory.DEVIATION,
            agent_name="agent",
            task_id="task-1",
            context={"requirement_verbatim": "x", "agent_plan": "y"},
        )
        response = (
            "I see my mistake. The verbatim requirement says to add controls "
            "to the header bar, but I should have looked at DashboardShell.tsx "
            "instead of creating a sidebar page. The correct approach maps "
            "the requirement to the center section of the header component."
        )
        assert evaluate_response(lesson, response) == LessonOutcome.COMPREHENSION_VERIFIED

    def test_response_references_requirement(self):
        lesson = adapt_lesson(
            DiseaseCategory.LAZINESS,
            agent_name="agent",
            task_id="task-1",
            context={
                "requirement_summary": "update all sites",
                "what_agent_did": "3 of 7",
                "what_is_missing": "4 sites",
            },
        )
        response = (
            "Looking at the requirement again, I should have updated all 7 call sites. "
            "I missed files X, Y, Z, W. I need to find those files and apply the same "
            "changes I made to the other 3. Instead of claiming done, I should verify "
            "all sites are covered."
        )
        assert evaluate_response(lesson, response) == LessonOutcome.COMPREHENSION_VERIFIED