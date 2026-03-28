"""Task priority scoring — intelligent dispatch ordering.

Scores tasks to determine dispatch priority based on:
- Explicit priority (urgent > high > medium > low)
- Dependency chain depth (critical path tasks first)
- Sprint deadline proximity
- Task type (blockers before features)
- Time waiting in inbox (older tasks get boost)

Used by the orchestrator to decide WHICH task to dispatch when
multiple tasks are ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from fleet.core.models import Task, TaskStatus


# Base scores by explicit priority
PRIORITY_SCORES = {
    "urgent": 100,
    "high": 75,
    "medium": 50,
    "low": 25,
}

# Bonus for task types that unlock other work
TASK_TYPE_BONUS = {
    "blocker": 30,     # Blockers must be resolved ASAP
    "epic": 0,         # Epics are grouping tasks, no bonus
    "story": 10,       # Stories contain subtasks
    "task": 5,
    "subtask": 0,
    "request": 15,     # Requests often block someone
    "concern": 0,
}


@dataclass
class ScoredTask:
    """A task with its computed dispatch priority score."""

    task: Task
    score: float
    reasons: list[str]


def score_task(
    task: Task,
    all_tasks: list[Task],
    now: Optional[datetime] = None,
) -> ScoredTask:
    """Compute a dispatch priority score for a task.

    Higher score = should be dispatched first.
    """
    now = now or datetime.now()
    score = 0.0
    reasons: list[str] = []

    # 1. Base priority score
    base = PRIORITY_SCORES.get(task.priority, 50)
    score += base
    reasons.append(f"priority={task.priority} (+{base})")

    # 2. Task type bonus (blockers first)
    task_type = task.custom_fields.task_type or "task"
    type_bonus = TASK_TYPE_BONUS.get(task_type, 0)
    if type_bonus:
        score += type_bonus
        reasons.append(f"type={task_type} (+{type_bonus})")

    # 3. Dependency chain depth — tasks that unblock MORE downstream work score higher
    downstream_count = _count_downstream(task.id, all_tasks)
    if downstream_count > 0:
        chain_bonus = min(downstream_count * 10, 40)  # Cap at 40
        score += chain_bonus
        reasons.append(f"unblocks={downstream_count} (+{chain_bonus})")

    # 4. Time waiting in inbox — older tasks get a small boost
    if task.created_at:
        hours_waiting = (now - task.created_at).total_seconds() / 3600
        wait_bonus = min(hours_waiting * 2, 20)  # Cap at 20 (10 hours)
        score += wait_bonus
        if wait_bonus >= 5:
            reasons.append(f"waiting={hours_waiting:.0f}h (+{wait_bonus:.0f})")

    # 5. Story points — higher effort tasks don't get priority boost
    #    (we prioritize quick wins and blockers over large tasks)
    sp = task.custom_fields.story_points or 0
    if sp >= 8:
        score -= 5  # Slight penalty for very large tasks
        reasons.append(f"large_task (sp={sp}, -5)")

    return ScoredTask(task=task, score=score, reasons=reasons)


def rank_tasks(
    tasks: list[Task],
    all_tasks: list[Task],
    now: Optional[datetime] = None,
) -> list[ScoredTask]:
    """Rank a list of tasks by dispatch priority (highest first)."""
    now = now or datetime.now()
    scored = [score_task(t, all_tasks, now) for t in tasks]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def _count_downstream(task_id: str, all_tasks: list[Task]) -> int:
    """Count how many tasks are directly waiting on this task."""
    return sum(
        1 for t in all_tasks
        if task_id in t.depends_on
        and t.status in (TaskStatus.INBOX,)
    )


def identify_blocker_type(task: Task) -> str:
    """Identify what kind of blocker a stuck task represents.

    Returns the agent role best suited to resolve it.
    Used for automatic blocker resolution routing.
    """
    title_lower = task.title.lower()
    desc_lower = (task.description or "").lower()
    combined = f"{title_lower} {desc_lower}"

    if any(w in combined for w in ("test", "pytest", "failing test", "coverage")):
        return "qa-engineer"

    if any(w in combined for w in ("security", "cve", "vulnerability", "secret", "credential")):
        return "devsecops-expert"

    if any(w in combined for w in ("docker", "deploy", "ci ", "pipeline", "infrastructure", "dependency", "install")):
        return "devops"

    if any(w in combined for w in ("design", "architecture", "coupling", "refactor", "structure")):
        return "architect"

    if any(w in combined for w in ("doc", "readme", "changelog", "api doc")):
        return "technical-writer"

    if any(w in combined for w in ("ui", "ux", "accessibility", "layout", "interface")):
        return "ux-designer"

    # Default to software-engineer for general code issues
    return "software-engineer"