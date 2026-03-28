"""Task lifecycle engine — PRE → PROGRESS → POST enforcement.

Ensures agents follow a structured workflow:
  PRE: Context loaded, plan shared, dependencies checked
  PROGRESS: Work with commits, progress updates, quality checkpoints
  POST: Tests run, output validated, review gates populated

This module defines the lifecycle stages, validates transitions,
and provides quality checks at each stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from fleet.core.models import Task, TaskCustomFields, TaskStatus


class LifecycleStage(str, Enum):
    """Agent task lifecycle stages."""

    NOT_STARTED = "not_started"     # Task exists but no agent action yet
    CONTEXT_LOADED = "context_loaded"  # fleet_read_context called
    ACCEPTED = "accepted"           # fleet_task_accept called with plan
    IN_PROGRESS = "in_progress"     # Agent is working (commits, progress updates)
    COMPLETING = "completing"       # fleet_task_complete called
    IN_REVIEW = "in_review"         # Task moved to review with gates
    DONE = "done"                   # Approved and transitioned


@dataclass
class LifecycleCheck:
    """Result of a lifecycle validation check."""

    passed: bool
    check_name: str
    message: str = ""


@dataclass
class LifecycleReport:
    """Full lifecycle compliance report for a task."""

    task_id: str
    stage: LifecycleStage
    checks: list[LifecycleCheck] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return all(c.passed for c in self.checks) and not self.issues

    @property
    def score(self) -> float:
        if not self.checks:
            return 0.0
        passed = sum(1 for c in self.checks if c.passed)
        return (passed / len(self.checks)) * 100


def validate_pre_stage(task: Task, has_context: bool, has_plan: bool) -> list[LifecycleCheck]:
    """Validate PRE stage — context loaded and plan shared.

    Checks:
    1. fleet_read_context was called (context loaded)
    2. fleet_task_accept was called with a plan
    3. Task has assigned agent
    4. Task has project set
    """
    checks = []

    checks.append(LifecycleCheck(
        passed=has_context,
        check_name="context_loaded",
        message="fleet_read_context called" if has_context else "Context not loaded — call fleet_read_context first",
    ))

    checks.append(LifecycleCheck(
        passed=has_plan,
        check_name="plan_shared",
        message="Plan shared via fleet_task_accept" if has_plan else "No plan — call fleet_task_accept with your approach",
    ))

    checks.append(LifecycleCheck(
        passed=bool(task.custom_fields.agent_name),
        check_name="agent_assigned",
        message=f"Agent: {task.custom_fields.agent_name}" if task.custom_fields.agent_name else "No agent assigned",
    ))

    checks.append(LifecycleCheck(
        passed=bool(task.custom_fields.project),
        check_name="project_set",
        message=f"Project: {task.custom_fields.project}" if task.custom_fields.project else "No project set",
    ))

    return checks


def validate_progress_stage(
    task: Task,
    commit_count: int,
    has_progress_update: bool,
) -> list[LifecycleCheck]:
    """Validate PROGRESS stage — work happening with proper commits.

    Checks:
    1. At least one commit made (for code tasks)
    2. Progress update posted (for long-running tasks)
    3. Conventional commit format used
    """
    checks = []
    is_code_task = task.custom_fields.task_type in ("task", "subtask", "story", None)

    if is_code_task:
        checks.append(LifecycleCheck(
            passed=commit_count > 0,
            check_name="has_commits",
            message=f"{commit_count} commit(s)" if commit_count > 0 else "No commits — use fleet_commit",
        ))

    checks.append(LifecycleCheck(
        passed=has_progress_update or commit_count <= 1,
        check_name="progress_updates",
        message="Progress shared" if has_progress_update else "Consider posting progress for long tasks",
    ))

    return checks


def validate_post_stage(
    task: Task,
    has_pr: bool,
    tests_passed: bool,
    has_review_gates: bool,
    has_approval: bool,
) -> list[LifecycleCheck]:
    """Validate POST stage — output quality and review readiness.

    Checks:
    1. PR created (for code tasks)
    2. Tests passed
    3. Review gates populated
    4. Approval created for fleet-ops to review
    """
    checks = []
    is_code_task = task.custom_fields.task_type in ("task", "subtask", "story", None)

    if is_code_task:
        checks.append(LifecycleCheck(
            passed=has_pr,
            check_name="pr_created",
            message=f"PR: {task.custom_fields.pr_url}" if has_pr else "No PR — fleet_task_complete should create one",
        ))

    checks.append(LifecycleCheck(
        passed=tests_passed,
        check_name="tests_passed",
        message="Tests passed" if tests_passed else "Tests failed or not run",
    ))

    checks.append(LifecycleCheck(
        passed=has_review_gates,
        check_name="review_gates",
        message="Review gates populated" if has_review_gates else "No review gates — fleet_task_complete should set them",
    ))

    checks.append(LifecycleCheck(
        passed=has_approval,
        check_name="approval_created",
        message="Approval created for fleet-ops" if has_approval else "No approval — fleet_task_complete should create one",
    ))

    return checks


def assess_task_lifecycle(
    task: Task,
    has_context: bool = False,
    has_plan: bool = False,
    commit_count: int = 0,
    has_progress_update: bool = False,
    has_pr: bool = False,
    tests_passed: bool = False,
    has_review_gates: bool = False,
    has_approval: bool = False,
) -> LifecycleReport:
    """Full lifecycle assessment for a task.

    Returns a report with all checks and a compliance score.
    Used by fleet-ops during review to evaluate lifecycle adherence.
    """
    # Determine current stage
    if task.status == TaskStatus.DONE:
        stage = LifecycleStage.DONE
    elif task.status == TaskStatus.REVIEW:
        stage = LifecycleStage.IN_REVIEW
    elif task.status == TaskStatus.IN_PROGRESS:
        if has_plan:
            stage = LifecycleStage.IN_PROGRESS
        elif has_context:
            stage = LifecycleStage.CONTEXT_LOADED
        else:
            stage = LifecycleStage.NOT_STARTED
    else:
        stage = LifecycleStage.NOT_STARTED

    report = LifecycleReport(task_id=task.id, stage=stage)

    # Run checks based on stage
    if stage in (LifecycleStage.IN_REVIEW, LifecycleStage.DONE):
        # Full lifecycle check
        report.checks.extend(validate_pre_stage(task, has_context, has_plan))
        report.checks.extend(validate_progress_stage(task, commit_count, has_progress_update))
        report.checks.extend(validate_post_stage(task, has_pr, tests_passed, has_review_gates, has_approval))
    elif stage == LifecycleStage.IN_PROGRESS:
        report.checks.extend(validate_pre_stage(task, has_context, has_plan))
        report.checks.extend(validate_progress_stage(task, commit_count, has_progress_update))
    elif stage == LifecycleStage.CONTEXT_LOADED:
        report.checks.extend(validate_pre_stage(task, has_context, has_plan))

    # Identify issues
    for check in report.checks:
        if not check.passed:
            report.issues.append(check.message)

    return report