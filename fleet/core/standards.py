"""Standards library — what "done right" looks like for every artifact type.

The methodology system enforces high standards for everything agents produce.
Each artifact type has a definition of required fields, quality criteria,
and examples. Standards are enforced through methodology checks and referenced
by the teaching system for adapted lessons.

Standards evolve — new artifact types get added, existing standards get
refined as the PO identifies quality gaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RequiredField:
    """A field that must be present on an artifact."""
    name: str
    description: str
    required: bool = True  # False = recommended but not blocking


@dataclass
class Standard:
    """Defines what "complete" and "correct" looks like for an artifact type."""
    artifact_type: str
    description: str
    required_fields: list[RequiredField] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)
    positive_example: str = ""
    negative_example: str = ""


@dataclass
class ComplianceResult:
    """Result of checking an artifact against its standard."""
    artifact_type: str
    missing_fields: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return len(self.missing_fields) == 0 and len(self.failed_criteria) == 0

    @property
    def score(self) -> int:
        """0-100 compliance score."""
        total = len(self.missing_fields) + len(self.failed_criteria)
        if total == 0:
            return 100
        # Rough scoring — each missing field/criteria deducts points
        return max(0, 100 - (total * 15))


# ─── Standard Definitions ───────────────────────────────────────────────

STANDARDS: dict[str, Standard] = {}


def _register(standard: Standard) -> Standard:
    STANDARDS[standard.artifact_type] = standard
    return standard


# ── Full Task ───────────────────────────────────────────────────────────

_register(Standard(
    artifact_type="task",
    description="A task ready for work (99-100% readiness)",
    required_fields=[
        RequiredField("title", "Clear, specific, actionable. Not vague."),
        RequiredField("requirement_verbatim", "PO's exact words. The anchor for all work."),
        RequiredField("description", "Enough context that the agent doesn't need to guess."),
        RequiredField("acceptance_criteria", "Specific, checkable conditions. Not 'it works'."),
        RequiredField("task_type", "epic/story/task/subtask/bug/spike correctly set."),
        RequiredField("task_stage", "Appropriate to current phase."),
        RequiredField("task_readiness", "Reflects actual readiness, confirmed by PO."),
        RequiredField("agent_name", "Appropriate agent assigned.", required=False),
        RequiredField("priority", "Set correctly."),
        RequiredField("story_points", "Estimated.", required=False),
        RequiredField("project", "Set."),
    ],
    quality_criteria=[
        "Title is an action, not a goal ('Add X to Y' not 'improve Z')",
        "Verbatim requirement populated with PO's actual words",
        "Description references design documents or codebase locations",
        "Acceptance criteria are checkable (yes/no, not subjective)",
        "Dependencies linked if any exist",
    ],
))


# ── Full Bug Report ─────────────────────────────────────────────────────

_register(Standard(
    artifact_type="bug",
    description="A bug report with enough detail to reproduce and fix",
    required_fields=[
        RequiredField("title", "Specific. What's broken, where."),
        RequiredField("steps_to_reproduce", "Concrete sequence that triggers the bug."),
        RequiredField("expected_behavior", "What should happen."),
        RequiredField("actual_behavior", "What actually happens. Error messages, logs."),
        RequiredField("environment", "Which system, version, configuration."),
        RequiredField("impact", "How severe. What's affected. Who's blocked."),
        RequiredField("evidence", "Screenshots, log excerpts, error output.", required=False),
    ],
    quality_criteria=[
        "Title names the specific error or behavior, not 'X is broken'",
        "Steps to reproduce are numbered and specific",
        "Expected vs actual clearly separated",
        "Error messages and stack traces included verbatim",
        "Impact states who is blocked and severity",
    ],
))


# ── Analysis Document ───────────────────────────────────────────────────

_register(Standard(
    artifact_type="analysis_document",
    description="Analysis of current state — what exists, what it means",
    required_fields=[
        RequiredField("title", "What was analyzed."),
        RequiredField("scope", "What was examined, what was excluded."),
        RequiredField("current_state", "What exists today. Specific files, line numbers."),
        RequiredField("findings", "What was discovered. Concrete observations."),
        RequiredField("implications", "What this means for the task."),
        RequiredField("open_questions", "What couldn't be determined.", required=False),
    ],
    quality_criteria=[
        "References specific files and line numbers, not vague descriptions",
        "Findings are concrete observations, not opinions",
        "Scope clearly states what was and wasn't examined",
        "Implications connect findings to the task at hand",
    ],
))


# ── Investigation Document ──────────────────────────────────────────────

_register(Standard(
    artifact_type="investigation_document",
    description="Research findings — what's possible, what options exist",
    required_fields=[
        RequiredField("title", "What was investigated."),
        RequiredField("scope", "What was researched, what sources consulted."),
        RequiredField("findings", "What was found, organized by topic."),
        RequiredField("options", "Multiple approaches with tradeoffs.", required=False),
        RequiredField("recommendations", "What the investigation suggests.", required=False),
        RequiredField("open_questions", "What couldn't be answered.", required=False),
    ],
    quality_criteria=[
        "Multiple options explored, not just the first one found",
        "Sources cited where applicable",
        "Findings organized by topic, not as a stream of consciousness",
        "Tradeoffs stated for each option",
    ],
))


# ── Plan / Reasoning Document ──────────────────────────────────────────

_register(Standard(
    artifact_type="plan",
    description="Implementation plan — what will be done and how",
    required_fields=[
        RequiredField("title", "What's being planned."),
        RequiredField("requirement_reference", "Verbatim requirement quoted."),
        RequiredField("approach", "What will be done. Specific files, components."),
        RequiredField("target_files", "Exactly which files will be modified or created."),
        RequiredField("steps", "Ordered implementation steps."),
        RequiredField("acceptance_criteria_mapping", "How each criterion will be met."),
        RequiredField("risks", "What could go wrong.", required=False),
    ],
    quality_criteria=[
        "Plan explicitly references the verbatim requirement",
        "Target files are specific paths, not categories",
        "Steps are ordered and each is actionable",
        "Acceptance criteria mapped to specific steps",
    ],
))


# ── Pull Request ────────────────────────────────────────────────────────

_register(Standard(
    artifact_type="pull_request",
    description="A PR ready for review",
    required_fields=[
        RequiredField("title", "Short, specific. Conventional commit format."),
        RequiredField("description", "What was done and why. References the task."),
        RequiredField("changes", "What files were modified and why."),
        RequiredField("testing", "What tests were run. Results."),
        RequiredField("task_reference", "Links to OCMC task and Plane issue."),
        RequiredField("commits", "Conventional commit format.", required=False),
    ],
    quality_criteria=[
        "Title follows conventional commit format (type(scope): description)",
        "Description explains WHY, not just WHAT",
        "Test results included or test plan stated",
        "Task ID referenced for traceability",
    ],
))


# ── Completion Claim ────────────────────────────────────────────────────

_register(Standard(
    artifact_type="completion_claim",
    description="Agent claiming a task is done — must have evidence",
    required_fields=[
        RequiredField("pr_url", "Link to the pull request."),
        RequiredField("summary", "What was done."),
        RequiredField("acceptance_criteria_check", "Each criterion with evidence."),
        RequiredField("files_changed", "List of files modified."),
    ],
    quality_criteria=[
        "Every acceptance criterion addressed with specific evidence",
        "PR URL is valid and accessible",
        "Summary matches the verbatim requirement",
        "No criteria marked 'done' without evidence",
    ],
))


# ─── Public API ─────────────────────────────────────────────────────────


def get_standard(artifact_type: str) -> Optional[Standard]:
    """Get the standard for an artifact type."""
    return STANDARDS.get(artifact_type)


def list_standards() -> list[Standard]:
    """List all registered standards."""
    return list(STANDARDS.values())


def check_standard(
    artifact_type: str,
    present_fields: dict[str, bool],
) -> ComplianceResult:
    """Check an artifact against its standard.

    Args:
        artifact_type: The type of artifact to check.
        present_fields: Dict of field_name → is_present for each required field.

    Returns:
        ComplianceResult with missing fields and score.
    """
    standard = get_standard(artifact_type)
    if not standard:
        return ComplianceResult(artifact_type=artifact_type)

    result = ComplianceResult(artifact_type=artifact_type)

    for rf in standard.required_fields:
        if rf.required and not present_fields.get(rf.name, False):
            result.missing_fields.append(rf.name)

    return result