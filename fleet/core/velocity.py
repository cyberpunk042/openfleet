"""Sprint velocity and metrics — data-driven project management.

Tracks:
- Story points completed per sprint
- Task cycle time (inbox → done)
- Agent throughput (tasks completed per agent)
- Sprint progress (done/total, projected completion)
- Blocker resolution time

Used by PM for sprint planning and retrospectives, by fleet-ops for
performance monitoring, and by the orchestrator for sprint-aware decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from fleet.core.models import Task, TaskStatus


@dataclass
class SprintMetrics:
    """Metrics for a sprint or plan."""

    plan_id: str
    total_tasks: int = 0
    done_tasks: int = 0
    in_progress_tasks: int = 0
    review_tasks: int = 0
    inbox_tasks: int = 0
    blocked_tasks: int = 0

    total_story_points: int = 0
    done_story_points: int = 0

    avg_cycle_time_hours: float = 0.0   # Average inbox → done time
    min_cycle_time_hours: float = 0.0
    max_cycle_time_hours: float = 0.0

    @property
    def completion_pct(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.done_tasks / self.total_tasks) * 100

    @property
    def points_completion_pct(self) -> float:
        if self.total_story_points == 0:
            return 0.0
        return (self.done_story_points / self.total_story_points) * 100

    @property
    def is_complete(self) -> bool:
        return self.done_tasks == self.total_tasks and self.total_tasks > 0


@dataclass
class AgentMetrics:
    """Per-agent performance metrics."""

    agent_name: str
    tasks_completed: int = 0
    story_points_completed: int = 0
    avg_cycle_time_hours: float = 0.0
    tasks_in_progress: int = 0
    tasks_in_review: int = 0


def compute_sprint_metrics(
    tasks: list[Task],
    plan_id: str,
) -> SprintMetrics:
    """Compute metrics for a specific sprint plan.

    Args:
        tasks: All board tasks.
        plan_id: Sprint plan ID to filter by.
    """
    sprint_tasks = [
        t for t in tasks
        if t.custom_fields.plan_id == plan_id
        or t.custom_fields.sprint == plan_id
    ]

    if not sprint_tasks:
        return SprintMetrics(plan_id=plan_id)

    metrics = SprintMetrics(plan_id=plan_id, total_tasks=len(sprint_tasks))

    cycle_times: list[float] = []

    for task in sprint_tasks:
        sp = task.custom_fields.story_points or 0
        metrics.total_story_points += sp

        if task.status == TaskStatus.DONE:
            metrics.done_tasks += 1
            metrics.done_story_points += sp

            # Cycle time: created_at → updated_at (as proxy for done_at)
            if task.created_at and task.updated_at:
                hours = (task.updated_at - task.created_at).total_seconds() / 3600
                cycle_times.append(hours)

        elif task.status == TaskStatus.IN_PROGRESS:
            metrics.in_progress_tasks += 1
        elif task.status == TaskStatus.REVIEW:
            metrics.review_tasks += 1
        elif task.status == TaskStatus.INBOX:
            metrics.inbox_tasks += 1

        if task.is_blocked:
            metrics.blocked_tasks += 1

    if cycle_times:
        metrics.avg_cycle_time_hours = sum(cycle_times) / len(cycle_times)
        metrics.min_cycle_time_hours = min(cycle_times)
        metrics.max_cycle_time_hours = max(cycle_times)

    return metrics


def compute_agent_metrics(
    tasks: list[Task],
) -> list[AgentMetrics]:
    """Compute per-agent performance metrics across all tasks.

    Returns metrics for every agent that has completed work.
    """
    agent_data: dict[str, AgentMetrics] = {}

    for task in tasks:
        agent_name = task.custom_fields.agent_name
        if not agent_name:
            continue

        if agent_name not in agent_data:
            agent_data[agent_name] = AgentMetrics(agent_name=agent_name)

        metrics = agent_data[agent_name]
        sp = task.custom_fields.story_points or 0

        if task.status == TaskStatus.DONE:
            metrics.tasks_completed += 1
            metrics.story_points_completed += sp
        elif task.status == TaskStatus.IN_PROGRESS:
            metrics.tasks_in_progress += 1
        elif task.status == TaskStatus.REVIEW:
            metrics.tasks_in_review += 1

    # Compute average cycle times per agent
    for task in tasks:
        if task.status != TaskStatus.DONE:
            continue
        agent_name = task.custom_fields.agent_name
        if not agent_name or agent_name not in agent_data:
            continue
        if task.created_at and task.updated_at:
            hours = (task.updated_at - task.created_at).total_seconds() / 3600
            m = agent_data[agent_name]
            # Running average approximation
            if m.tasks_completed > 0:
                m.avg_cycle_time_hours = (
                    (m.avg_cycle_time_hours * (m.tasks_completed - 1) + hours) / m.tasks_completed
                )

    result = sorted(agent_data.values(), key=lambda m: m.tasks_completed, reverse=True)
    return result


def format_sprint_report(metrics: SprintMetrics) -> str:
    """Format sprint metrics as a structured markdown report."""
    lines = [
        f"## Sprint Report: {metrics.plan_id}",
        "",
        f"**Progress:** {metrics.done_tasks}/{metrics.total_tasks} tasks "
        f"({metrics.completion_pct:.0f}%)",
    ]

    if metrics.total_story_points > 0:
        lines.append(
            f"**Story Points:** {metrics.done_story_points}/{metrics.total_story_points} "
            f"({metrics.points_completion_pct:.0f}%)"
        )

    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Done | {metrics.done_tasks} |")
    if metrics.in_progress_tasks:
        lines.append(f"| In Progress | {metrics.in_progress_tasks} |")
    if metrics.review_tasks:
        lines.append(f"| Review | {metrics.review_tasks} |")
    if metrics.inbox_tasks:
        lines.append(f"| Inbox | {metrics.inbox_tasks} |")
    if metrics.blocked_tasks:
        lines.append(f"| Blocked | {metrics.blocked_tasks} |")

    if metrics.avg_cycle_time_hours > 0:
        lines.extend([
            "",
            f"**Avg Cycle Time:** {metrics.avg_cycle_time_hours:.1f}h",
            f"**Min/Max:** {metrics.min_cycle_time_hours:.1f}h / {metrics.max_cycle_time_hours:.1f}h",
        ])

    if metrics.is_complete:
        lines.extend(["", "**Sprint Complete.**"])

    return "\n".join(lines)


def format_agent_report(agent_metrics: list[AgentMetrics]) -> str:
    """Format agent metrics as a markdown table."""
    lines = [
        "## Agent Performance",
        "",
        "| Agent | Tasks Done | Story Points | Avg Cycle | Active |",
        "|-------|-----------|-------------|----------|--------|",
    ]

    for m in agent_metrics:
        active = m.tasks_in_progress + m.tasks_in_review
        lines.append(
            f"| {m.agent_name} | {m.tasks_completed} | "
            f"{m.story_points_completed} | "
            f"{m.avg_cycle_time_hours:.1f}h | "
            f"{active} |"
        )

    return "\n".join(lines)