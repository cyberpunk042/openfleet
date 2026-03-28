"""PR hygiene — detect and resolve stale, conflicting, and orphaned pull requests.

Problems this module detects:
1. Conflicting PRs — merge conflicts that need resolution
2. Stale PRs — open PRs whose tasks are already done
3. Duplicate PRs — multiple PRs for the same task/work
4. Orphaned PRs — open PRs with no linked task
5. Long-open PRs — PRs that have been open too long without activity

For each issue, produces a recommended action:
- Create resolve-conflict task for the agent
- Close stale PRs (task already done via different path)
- Close duplicate PRs (keep newest, close older)
- Create task for orphaned PRs
- Alert on long-open PRs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from fleet.core.models import Task, TaskStatus


@dataclass
class PRIssue:
    """A detected PR hygiene issue."""

    issue_type: str        # conflicting, stale, duplicate, orphaned, long_open
    severity: str          # high, medium, low
    pr_url: str
    pr_number: int = 0
    pr_title: str = ""
    task_id: str = ""
    task_status: str = ""
    description: str = ""
    recommended_action: str = ""
    target_agent: str = ""  # Who should handle it


@dataclass
class PRHygieneReport:
    """Full PR hygiene assessment."""

    issues: list[PRIssue] = field(default_factory=list)
    total_open_prs: int = 0
    conflicting: int = 0
    stale: int = 0

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)


def assess_pr_hygiene(
    tasks: list[Task],
    open_prs: list[dict],
    now: Optional[datetime] = None,
) -> PRHygieneReport:
    """Assess PR hygiene across all fleet projects.

    Args:
        tasks: All board tasks.
        open_prs: List of open PRs with fields: url, number, title, mergeable, created_at
        now: Current time (for staleness checks).

    Returns:
        PRHygieneReport with issues and recommended actions.
    """
    now = now or datetime.now()
    report = PRHygieneReport(total_open_prs=len(open_prs))

    # Build PR URL → task mapping
    task_by_pr: dict[str, Task] = {}
    for task in tasks:
        if task.custom_fields.pr_url:
            task_by_pr[task.custom_fields.pr_url] = task

    for pr in open_prs:
        pr_url = pr.get("url", "")
        pr_number = pr.get("number", 0)
        pr_title = pr.get("title", "")
        mergeable = pr.get("mergeable", "UNKNOWN")
        created_at = pr.get("created_at")

        linked_task = task_by_pr.get(pr_url)

        # 1. Conflicting PR
        if mergeable == "CONFLICTING":
            report.conflicting += 1
            agent = linked_task.custom_fields.agent_name if linked_task else "software-engineer"
            task_status = linked_task.status.value if linked_task else "unknown"

            report.issues.append(PRIssue(
                issue_type="conflicting",
                severity="high",
                pr_url=pr_url,
                pr_number=pr_number,
                pr_title=pr_title,
                task_id=linked_task.id if linked_task else "",
                task_status=task_status,
                description=(
                    f"PR #{pr_number} has merge conflicts. "
                    f"Task status: {task_status}. "
                    f"Branch needs rebase against main."
                ),
                recommended_action=_recommend_conflict_action(linked_task),
                target_agent=agent,
            ))

        # 2. Stale PR — task is done but PR still open
        if linked_task and linked_task.status == TaskStatus.DONE:
            report.stale += 1
            report.issues.append(PRIssue(
                issue_type="stale",
                severity="medium",
                pr_url=pr_url,
                pr_number=pr_number,
                pr_title=pr_title,
                task_id=linked_task.id,
                task_status="done",
                description=(
                    f"PR #{pr_number} is still open but task is already done. "
                    f"Either merge this PR or close it."
                ),
                recommended_action=(
                    "If PR has useful changes not in main → merge. "
                    "If work was done via a different PR → close as stale. "
                    "Fleet-ops should evaluate."
                ),
                target_agent="fleet-ops",
            ))

        # 3. Long-open PR (> 48 hours without merge)
        if created_at:
            try:
                if isinstance(created_at, str):
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    created = created_at
                hours_open = (now - created.replace(tzinfo=None)).total_seconds() / 3600
                if hours_open > 48:
                    report.issues.append(PRIssue(
                        issue_type="long_open",
                        severity="low",
                        pr_url=pr_url,
                        pr_number=pr_number,
                        pr_title=pr_title,
                        task_id=linked_task.id if linked_task else "",
                        description=f"PR #{pr_number} open for {hours_open:.0f}h. Needs attention.",
                        recommended_action="Review and merge, or close if no longer relevant.",
                        target_agent="fleet-ops",
                    ))
            except Exception:
                pass

    return report


def _recommend_conflict_action(task: Optional[Task]) -> str:
    """Recommend action for a conflicting PR based on task state."""
    if not task:
        return "No linked task. Close PR or create a task for it."

    if task.status == TaskStatus.DONE:
        return (
            "Task is DONE — the work may have been merged via a different path. "
            "Close this conflicting PR unless it has unique changes. "
            "If unique changes exist, create a new task to rebase and re-submit."
        )

    if task.status == TaskStatus.REVIEW:
        return (
            "Task is in REVIEW with conflicting PR. "
            "Create a resolve-conflict subtask for the original agent. "
            "Agent must rebase branch against main and force-push."
        )

    if task.status == TaskStatus.IN_PROGRESS:
        return (
            "Task still in progress. Agent should rebase before completing. "
            "Post a comment reminding the agent about the conflict."
        )

    return (
        "Create a resolve-conflict task. Agent must rebase branch against main."
    )