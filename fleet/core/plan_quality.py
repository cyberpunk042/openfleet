"""Plan quality validation — ensure agents plan before building.

Validates that agent plans meet minimum quality standards:
- Concrete steps (not vague "I'll work on it")
- Verification approach (how will you know it works)
- Risk awareness (what could go wrong)
- Estimated scope (small/medium/large)

Plans that don't meet quality standards get a lower confidence score,
which fleet-ops considers during review.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlanAssessment:
    """Result of assessing a plan's quality."""

    score: float                  # 0-100
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def acceptable(self) -> bool:
        return self.score >= 40  # Minimum threshold

    @property
    def good(self) -> bool:
        return self.score >= 70


# Keywords that indicate plan quality dimensions
STEP_INDICATORS = [
    "step", "first", "then", "next", "after", "finally",
    "1.", "2.", "3.", "-", "will create", "will add", "will implement",
    "will write", "will build", "will update", "will configure",
]

VERIFY_INDICATORS = [
    "test", "verify", "check", "validate", "confirm", "run",
    "ensure", "assert", "expect", "should pass",
]

RISK_INDICATORS = [
    "risk", "concern", "might", "could fail", "watch out",
    "careful", "issue", "depends on", "blocked", "unknown",
    "if", "alternatively", "fallback",
]


def assess_plan(plan_text: str, task_type: str = "task") -> PlanAssessment:
    """Assess the quality of an agent's plan.

    A good plan has:
    - Concrete steps (what will you do)
    - Verification approach (how will you know it works)
    - Risk awareness (what could go wrong)

    Args:
        plan_text: The plan text from fleet_task_accept.
        task_type: Task type for complexity-appropriate validation.

    Returns:
        PlanAssessment with score and feedback.
    """
    if not plan_text or len(plan_text.strip()) < 10:
        return PlanAssessment(
            score=0,
            issues=["Plan is empty or too short. Describe your approach."],
        )

    plan_lower = plan_text.lower()
    score = 0.0
    issues: list[str] = []
    suggestions: list[str] = []

    # 1. Has concrete steps? (weight: 40)
    step_count = sum(1 for indicator in STEP_INDICATORS if indicator in plan_lower)
    if step_count >= 3:
        score += 40
    elif step_count >= 1:
        score += 20
        suggestions.append("Add more concrete steps (what specific files/functions will you change?)")
    else:
        issues.append("No concrete steps found. Describe WHAT you will do, specifically.")

    # 2. Has verification? (weight: 30)
    verify_count = sum(1 for indicator in VERIFY_INDICATORS if indicator in plan_lower)
    if verify_count >= 2:
        score += 30
    elif verify_count >= 1:
        score += 15
        suggestions.append("Explain HOW you'll verify your work (tests, checks)")
    else:
        if task_type not in ("subtask",):  # Subtasks can skip verification
            issues.append("No verification approach. How will you know it works?")

    # 3. Has risk awareness? (weight: 20)
    risk_count = sum(1 for indicator in RISK_INDICATORS if indicator in plan_lower)
    if risk_count >= 1:
        score += 20
    else:
        if task_type in ("epic", "story", "blocker"):  # Complex tasks should have risks
            suggestions.append("Consider what could go wrong or what you're unsure about")

    # 4. Length bonus (weight: 10)
    words = len(plan_text.split())
    if words >= 50:
        score += 10
    elif words >= 20:
        score += 5

    return PlanAssessment(score=score, issues=issues, suggestions=suggestions)


def format_plan_feedback(assessment: PlanAssessment) -> str:
    """Format plan assessment as feedback for the agent."""
    lines = [f"Plan quality: {assessment.score:.0f}/100"]

    if assessment.issues:
        lines.append("\nIssues:")
        for issue in assessment.issues:
            lines.append(f"  - {issue}")

    if assessment.suggestions:
        lines.append("\nSuggestions:")
        for suggestion in assessment.suggestions:
            lines.append(f"  - {suggestion}")

    if assessment.good:
        lines.append("\nPlan looks solid. Proceed.")
    elif assessment.acceptable:
        lines.append("\nPlan is acceptable but could be stronger.")
    else:
        lines.append("\nPlan needs improvement before starting work.")

    return "\n".join(lines)