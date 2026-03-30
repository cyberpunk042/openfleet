"""Teaching system — adapted lessons, injection, comprehension verification.

The teaching system adapts and responds. When the immune system triggers it,
the teaching system creates adapted lessons, delivers them, and verifies
comprehension through practice.

Key insight from PO: "seen the pattern does not break the pattern, it forging
the right path multiple times that does."

The teaching system:
1. Stores lessons organized by disease category
2. Adapts lessons to the specific disease + task + agent
3. Injects lessons into agent context (forcing autocomplete from rules)
4. Verifies comprehension through practice exercises
5. Reports outcome to immune system (comprehension verified / no change)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DiseaseCategory(str, Enum):
    """Disease categories the teaching system addresses."""
    DEVIATION = "deviation"
    LAZINESS = "laziness"
    CONFIDENT_BUT_WRONG = "confident_but_wrong"
    PROTOCOL_VIOLATION = "protocol_violation"
    ABSTRACTION = "abstraction"
    CODE_WITHOUT_READING = "code_without_reading"
    SCOPE_CREEP = "scope_creep"
    CASCADING_FIX = "cascading_fix"
    CONTEXT_CONTAMINATION = "context_contamination"
    NOT_LISTENING = "not_listening"
    COMPRESSION = "compression"


class LessonOutcome(str, Enum):
    """Outcome of a teaching session."""
    COMPREHENSION_VERIFIED = "comprehension_verified"
    NO_CHANGE = "no_change"
    IN_PROGRESS = "in_progress"


@dataclass
class PracticeExercise:
    """An exercise the agent must complete to demonstrate comprehension."""
    instruction: str
    verification_hint: str  # what a correct response should contain


@dataclass
class Lesson:
    """An adapted lesson for a specific disease + task + agent."""
    disease: DiseaseCategory
    agent_name: str
    task_id: str
    content: str  # the lesson text injected into context
    exercise: PracticeExercise
    attempt: int = 0
    max_attempts: int = 3
    outcome: LessonOutcome = LessonOutcome.IN_PROGRESS


@dataclass
class LessonTemplate:
    """Template for generating adapted lessons per disease category."""
    disease: DiseaseCategory
    description: str
    lesson_template: str  # with {placeholders}
    exercise_template: str  # with {placeholders}
    verification_hint_template: str  # what correct response contains


# ─── Lesson Templates ───────────────────────────────────────────────────

TEMPLATES: dict[DiseaseCategory, LessonTemplate] = {}


def _reg(t: LessonTemplate) -> LessonTemplate:
    TEMPLATES[t.disease] = t
    return t


_reg(LessonTemplate(
    disease=DiseaseCategory.DEVIATION,
    description="Agent drifted from the spec — output doesn't match verbatim requirement",
    lesson_template=(
        "Your task's verbatim requirement says:\n"
        '"{requirement_verbatim}"\n\n'
        "Your plan says:\n"
        '"{agent_plan}"\n\n'
        "These don't match. The requirement is the source of truth. "
        "Your words must map to the requirement's words."
    ),
    exercise_template=(
        "Re-read the verbatim requirement word by word. For each specific "
        "term in the requirement, state which file and which line of code "
        "that maps to. Then produce a corrected plan that addresses each "
        "term in the requirement."
    ),
    verification_hint_template=(
        "Response should reference the verbatim requirement terms "
        "and map them to specific files/locations."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.LAZINESS,
    description="Agent did partial work — not all requirements addressed",
    lesson_template=(
        "Your task requires: {requirement_summary}\n\n"
        "You addressed: {what_agent_did}\n\n"
        "Missing: {what_is_missing}\n\n"
        "Partial work is not complete work."
    ),
    exercise_template=(
        "List ALL items required by the task. For each item, state "
        "whether you addressed it and where (file, line). Identify "
        "every item you missed. Then describe what needs to be done "
        "for each missing item."
    ),
    verification_hint_template=(
        "Response should list all required items and acknowledge "
        "which ones were missed."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.CONFIDENT_BUT_WRONG,
    description="Agent confidently built the wrong thing (Z when A was specified)",
    lesson_template=(
        "You were building: {what_agent_built}\n"
        "The requirement says: {requirement_verbatim}\n\n"
        "These are different things. Your understanding was wrong, "
        "not just a detail — the direction was wrong."
    ),
    exercise_template=(
        "Without referencing your previous plan, read ONLY the verbatim "
        "requirement. Write a single sentence stating what is being asked. "
        "Use only words that appear in the requirement. Do not add "
        "interpretation."
    ),
    verification_hint_template=(
        "Response should be a single sentence using only words from "
        "the verbatim requirement."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.PROTOCOL_VIOLATION,
    description="Agent violated the methodology protocol for its current stage",
    lesson_template=(
        "Your task is in {current_stage} stage.\n"
        "During {current_stage}, the protocol allows: {allowed_actions}\n"
        "You did: {what_agent_did}\n\n"
        "This is a protocol violation."
    ),
    exercise_template=(
        "State what stage your task is in. State what the protocol "
        "for that stage allows. State what you did that violated the "
        "protocol. Describe what you should have done instead."
    ),
    verification_hint_template=(
        "Response should correctly identify the stage, the protocol "
        "rules, and what the agent should have done."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.ABSTRACTION,
    description="Agent replaced literal words with its own interpretation",
    lesson_template=(
        "The PO said: {requirement_verbatim}\n\n"
        "You interpreted this as: {agent_interpretation}\n\n"
        "The PO's words mean what they mean. Do not abstract. "
        "Do not interpret. Process the exact words."
    ),
    exercise_template=(
        "Read the PO's words again. For each word in the requirement, "
        "write what that word literally means — not what you think the "
        "PO 'really' means. Words mean what they mean."
    ),
    verification_hint_template=(
        "Response should demonstrate literal word-by-word processing "
        "without adding interpretation."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.CODE_WITHOUT_READING,
    description="Agent wrote code without reading the existing implementation",
    lesson_template=(
        "You modified {file_path} without reading it first.\n"
        "You called {function_name} with wrong arguments.\n\n"
        "Always read before writing. Always trace before modifying."
    ),
    exercise_template=(
        "Read the file you were modifying. List every function in it. "
        "For the function you were calling, state its exact signature "
        "(parameters, types, return value). Then state what you "
        "should have called it with."
    ),
    verification_hint_template=(
        "Response should show the actual function signature from the "
        "file, not from memory."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.SCOPE_CREEP,
    description="Agent added unrequested scope — 'while I'm here' changes",
    lesson_template=(
        "Your task scope is: {requirement_verbatim}\n\n"
        "You also did: {extra_work}\n\n"
        "Nobody asked for {extra_work}. Stay in scope."
    ),
    exercise_template=(
        "List everything the task asks for. List everything you did. "
        "Identify every item in your work that is NOT in the task. "
        "For each extra item, state: 'This was not asked for.'"
    ),
    verification_hint_template=(
        "Response should clearly separate in-scope from out-of-scope work."
    ),
))

_reg(LessonTemplate(
    disease=DiseaseCategory.COMPRESSION,
    description="Agent minimized or compressed the PO's vision into something smaller",
    lesson_template=(
        "The PO described a {scope_description}.\n"
        "You compressed it into: {what_agent_produced}\n\n"
        "Do not minimize. Do not compress. The PO's scope is the scope."
    ),
    exercise_template=(
        "Re-read the PO's full description. List every component, "
        "every requirement, every detail. Do not summarize — list. "
        "How many items are there? How many did your output address?"
    ),
    verification_hint_template=(
        "Response should list all components without summarizing or compressing."
    ),
))


# ─── Lesson Adaptation ──────────────────────────────────────────────────


def adapt_lesson(
    disease: DiseaseCategory,
    agent_name: str,
    task_id: str,
    context: dict,
) -> Lesson:
    """Create an adapted lesson from a template + context.

    Args:
        disease: Which disease was detected.
        agent_name: Which agent needs the lesson.
        task_id: Which task the disease was detected on.
        context: Dict with placeholder values for the template.
            Keys match {placeholders} in the template strings.

    Returns:
        An adapted Lesson ready for injection.
    """
    template = TEMPLATES.get(disease)
    if not template:
        # Fallback — generic lesson
        return Lesson(
            disease=disease,
            agent_name=agent_name,
            task_id=task_id,
            content=f"A {disease.value} issue was detected. Review your work against the task requirements.",
            exercise=PracticeExercise(
                instruction="Re-read the task requirements and explain what you should do differently.",
                verification_hint="Response should reference the specific task requirements.",
            ),
        )

    # Fill templates with context
    def fill(template_str: str) -> str:
        result = template_str
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    return Lesson(
        disease=disease,
        agent_name=agent_name,
        task_id=task_id,
        content=fill(template.lesson_template),
        exercise=PracticeExercise(
            instruction=fill(template.exercise_template),
            verification_hint=fill(template.verification_hint_template),
        ),
    )


def format_lesson_for_injection(lesson: Lesson) -> str:
    """Format a lesson as text ready to be injected into agent context.

    This is the content that gets forced into the agent's context via
    gateway chat.send or context/ files. The agent must autocomplete
    from this before continuing its original work.
    """
    parts = [
        "═══ TEACHING SYSTEM — LESSON ═══",
        "",
        f"Disease detected: {lesson.disease.value}",
        f"Attempt: {lesson.attempt + 1}/{lesson.max_attempts}",
        "",
        "─── What happened ───",
        lesson.content,
        "",
        "─── Exercise ───",
        lesson.exercise.instruction,
        "",
        "─── Instructions ───",
        "You MUST complete the exercise above before returning to your task.",
        "Demonstrate that you understand by producing the requested output.",
        "If you cannot demonstrate understanding, this lesson will repeat.",
        f"After {lesson.max_attempts} attempts without change, you will be pruned.",
        "",
        "═══ END LESSON ═══",
    ]
    return "\n".join(parts)


def evaluate_response(
    lesson: Lesson,
    agent_response: str,
) -> LessonOutcome:
    """Evaluate whether an agent's response demonstrates comprehension.

    This is a basic evaluation — checks if the response contains key
    terms from the verification hint. More sophisticated evaluation
    (semantic comparison) can be added later.

    Args:
        lesson: The lesson that was delivered.
        agent_response: What the agent produced after the lesson.

    Returns:
        LessonOutcome indicating whether comprehension was verified.
    """
    if not agent_response or not agent_response.strip():
        return LessonOutcome.NO_CHANGE

    hint = lesson.exercise.verification_hint.lower()
    response_lower = agent_response.lower()

    # Basic heuristic: check if response addresses the exercise
    # This will be evolved with more sophisticated checks
    indicators = [
        # Agent references the requirement
        "requirement" in response_lower or "verbatim" in response_lower,
        # Agent acknowledges what went wrong
        "should have" in response_lower or "instead" in response_lower
        or "wrong" in response_lower or "mistake" in response_lower,
        # Response has substance (not just "I understand")
        len(agent_response.strip()) > 100,
        # Response doesn't just repeat the lesson back
        lesson.content[:50].lower() not in response_lower,
    ]

    if sum(indicators) >= 2:
        return LessonOutcome.COMPREHENSION_VERIFIED
    return LessonOutcome.NO_CHANGE