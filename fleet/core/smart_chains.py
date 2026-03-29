"""Smart chains — batch multiple operations into single pre-computed results.

> "why call 5 tools when you can just call a chain that does it all?
> it a mix of communication and logic and pragmatism"
> "Where ever we can take this pattern to improve the work and the flow
> and the logic we will."

Instead of agents making 5 separate MCP tool calls (each consuming tokens),
the fleet pre-computes results using direct API calls (no AI, no tokens).

Chains:
1. heartbeat_chain: pre-compute all heartbeat context (DONE in heartbeat_context.py)
2. dispatch_chain: pre-compute task context + worktree + model selection
3. completion_chain: post-compute PR + approval + IRC + ntfy in one pass
4. review_chain: pre-compute review context for fleet-ops

The pattern: orchestrator/daemon does the API calls, bundles the result,
passes it to the agent as pre-computed context. Agent reads, decides, acts.
No wasted tool calls for data the orchestrator already has.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.models import Task, TaskStatus


@dataclass
class DispatchContext:
    """Pre-computed context sent WITH a task dispatch message.

    Instead of the agent calling fleet_read_context (3+ API calls),
    the orchestrator pre-computes everything and includes it in the
    dispatch message. Agent reads it and starts working immediately.
    """

    task_id: str
    task_title: str
    task_description: str
    task_priority: str
    task_type: str = ""
    project: str = ""
    worktree: str = ""
    branch: str = ""
    parent_task: str = ""
    depends_on: list[str] = field(default_factory=list)
    story_points: int = 0
    model: str = "sonnet"
    effort: str = "medium"
    acceptance_criteria: str = ""

    # Pre-computed from board state
    recent_decisions: list[str] = field(default_factory=list)
    related_work: list[str] = field(default_factory=list)
    sprint_progress: str = ""

    def format_message(self) -> str:
        """Format as dispatch message — agent gets everything it needs."""
        lines = [
            f"TASK ASSIGNMENT — {self.task_title}",
            f"ID: {self.task_id[:8]}",
            f"Priority: {self.task_priority}",
            f"Type: {self.task_type}",
            f"Model: {self.model} (effort: {self.effort})",
            "",
        ]

        if self.project:
            lines.append(f"Project: {self.project}")
        if self.worktree:
            lines.append(f"Worktree: {self.worktree}")
            lines.append(f"Branch: {self.branch}")
        if self.story_points:
            lines.append(f"Story Points: {self.story_points}")
        if self.parent_task:
            lines.append(f"Parent: {self.parent_task[:8]}")

        lines.extend(["", "Description:", self.task_description or "(none)", ""])

        if self.acceptance_criteria:
            lines.extend(["Acceptance Criteria:", self.acceptance_criteria, ""])

        if self.recent_decisions:
            lines.append("Recent decisions relevant to your work:")
            for d in self.recent_decisions[:3]:
                lines.append(f"  - {d[:100]}")
            lines.append("")

        if self.related_work:
            lines.append("Related work by other agents:")
            for w in self.related_work[:3]:
                lines.append(f"  - {w[:100]}")
            lines.append("")

        if self.sprint_progress:
            lines.append(f"Sprint: {self.sprint_progress}")
            lines.append("")

        lines.extend([
            "WORKFLOW:",
            "1. Read this context (already provided — no need to call fleet_read_context)",
            "2. fleet_task_accept(plan='your approach')",
            "3. Do the work — commit with fleet_commit()",
            "4. fleet_task_complete(summary='what you did')",
            "",
            "If blocked: fleet_pause(reason, needed)",
            "If you find other work: fleet_task_create()",
        ])

        return "\n".join(lines)


def build_dispatch_context(
    task: Task,
    board_memory: list = None,
    all_tasks: list = None,
    model: str = "sonnet",
    effort: str = "medium",
    worktree: str = "",
    branch: str = "",
) -> DispatchContext:
    """Build pre-computed dispatch context from existing data. No API calls."""
    ctx = DispatchContext(
        task_id=task.id,
        task_title=task.title,
        task_description=task.description or "",
        task_priority=task.priority,
        task_type=task.custom_fields.task_type or "task",
        project=task.custom_fields.project or "",
        worktree=worktree,
        branch=branch,
        parent_task=task.custom_fields.parent_task or "",
        depends_on=task.depends_on,
        story_points=task.custom_fields.story_points or 0,
        model=model,
        effort=effort,
    )

    # Extract relevant decisions from board memory
    if board_memory:
        for m in board_memory:
            tags = m.tags if hasattr(m, 'tags') else m.get('tags', [])
            content = m.content if hasattr(m, 'content') else m.get('content', '')
            if "decision" in tags:
                project = task.custom_fields.project or ""
                if project and f"project:{project}" in tags:
                    ctx.recent_decisions.append(content[:150])
                elif not project:
                    ctx.recent_decisions.append(content[:150])

    # Find related work from other agents on same project
    if all_tasks:
        project = task.custom_fields.project or ""
        for t in all_tasks:
            if t.id == task.id:
                continue
            if t.custom_fields.project == project and t.status in (TaskStatus.IN_PROGRESS, TaskStatus.REVIEW):
                agent = t.custom_fields.agent_name or "?"
                ctx.related_work.append(f"[{agent}] {t.title[:60]} ({t.status.value})")

    # Sprint progress
    sprint_id = task.custom_fields.plan_id or task.custom_fields.sprint
    if sprint_id and all_tasks:
        sprint_tasks = [t for t in all_tasks if t.custom_fields.plan_id == sprint_id or t.custom_fields.sprint == sprint_id]
        done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
        total = len(sprint_tasks)
        if total > 0:
            ctx.sprint_progress = f"{done}/{total} done ({done * 100 // total}%)"

    return ctx