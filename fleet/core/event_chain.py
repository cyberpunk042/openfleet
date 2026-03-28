"""Event chains — multi-surface publishing for fleet operations.

A single fleet operation (e.g., task_complete) produces a CHAIN of events
across multiple surfaces:
  - Internal (MC): task update, approval, board memory
  - Public (GitHub): branch push, PR creation
  - Channel (IRC): real-time notification
  - Notify (ntfy): human notification with priority routing
  - Meta (System): quality check, metrics update

Each operation defines its event chain. The chain runner executes all
events, tolerating partial failure (one surface failing doesn't block others).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventSurface(str, Enum):
    """Target surface for an event."""

    INTERNAL = "internal"   # MC: task updates, approvals, board memory
    PUBLIC = "public"       # GitHub: branches, PRs
    CHANNEL = "channel"     # IRC: real-time messages
    NOTIFY = "notify"       # ntfy: human notifications
    META = "meta"           # System: metrics, quality checks


@dataclass
class Event:
    """A single event in a chain."""

    surface: EventSurface
    action: str             # What to do (e.g., "update_task", "create_pr", "notify_irc")
    params: dict = field(default_factory=dict)
    required: bool = True   # If False, failure doesn't fail the chain
    result: Any = None
    error: str = ""
    executed: bool = False


@dataclass
class EventChain:
    """A chain of events produced by a single operation."""

    operation: str          # e.g., "task_complete", "task_create", "alert"
    source_agent: str = ""
    task_id: str = ""
    events: list[Event] = field(default_factory=list)

    def add(
        self,
        surface: EventSurface,
        action: str,
        params: dict | None = None,
        required: bool = True,
    ) -> Event:
        """Add an event to the chain."""
        event = Event(surface=surface, action=action, params=params or {}, required=required)
        self.events.append(event)
        return event

    @property
    def internal_events(self) -> list[Event]:
        return [e for e in self.events if e.surface == EventSurface.INTERNAL]

    @property
    def public_events(self) -> list[Event]:
        return [e for e in self.events if e.surface == EventSurface.PUBLIC]

    @property
    def channel_events(self) -> list[Event]:
        return [e for e in self.events if e.surface == EventSurface.CHANNEL]

    @property
    def notify_events(self) -> list[Event]:
        return [e for e in self.events if e.surface == EventSurface.NOTIFY]

    @property
    def meta_events(self) -> list[Event]:
        return [e for e in self.events if e.surface == EventSurface.META]


@dataclass
class ChainResult:
    """Result of executing an event chain."""

    operation: str
    total_events: int = 0
    executed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.failed == 0 or all(
            not e for e in self.errors  # Only non-required failures
        )


# ─── Chain Builders ──────────────────────────────────────────────────────

def build_task_complete_chain(
    task_id: str,
    agent_name: str,
    summary: str,
    pr_url: str = "",
    branch: str = "",
    test_results: str = "",
    project: str = "",
) -> EventChain:
    """Build the event chain for task completion.

    Produces events across all surfaces:
    1. Internal: update task status, create approval, post board memory
    2. Public: push branch, create PR (if code task)
    3. Channel: IRC notification
    4. Notify: ntfy notification (info level)
    5. Meta: quality check, metrics update
    """
    chain = EventChain(operation="task_complete", source_agent=agent_name, task_id=task_id)

    # Internal
    chain.add(EventSurface.INTERNAL, "update_task_status", {
        "task_id": task_id, "status": "review", "agent": agent_name,
    })
    chain.add(EventSurface.INTERNAL, "create_approval", {
        "task_id": task_id, "confidence": 85, "tests": test_results,
    })
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"Completed: {summary[:100]}", "tags": ["completed", f"project:{project}"],
    }, required=False)

    # Public (code tasks)
    if branch:
        chain.add(EventSurface.PUBLIC, "push_branch", {"branch": branch})
    if pr_url:
        chain.add(EventSurface.PUBLIC, "create_pr", {"pr_url": pr_url})

    # Channel
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet", "message": f"[{agent_name}] PR READY: {summary[:50]}",
    }, required=False)
    if pr_url:
        chain.add(EventSurface.CHANNEL, "notify_irc", {
            "channel": "#reviews", "message": f"[{agent_name}] Review: {pr_url}",
        }, required=False)

    # Notify
    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": f"Task completed: {summary[:40]}",
        "priority": "info",
        "event_type": "task_done",
    }, required=False)

    # Meta
    chain.add(EventSurface.META, "update_metrics", {
        "agent": agent_name, "task_id": task_id,
    }, required=False)

    return chain


def build_alert_chain(
    agent_name: str,
    severity: str,
    title: str,
    details: str,
    category: str = "quality",
    project: str = "",
) -> EventChain:
    """Build the event chain for an alert."""
    chain = EventChain(operation="alert", source_agent=agent_name)

    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"ALERT [{severity}]: {title}\n{details}",
        "tags": ["alert", severity, category, f"project:{project}"],
    })

    channel = "#alerts" if severity in ("critical", "high") else "#fleet"
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": channel, "message": f"[{agent_name}] {severity.upper()}: {title}",
    }, required=False)

    priority = "urgent" if severity in ("critical", "high") else "important"
    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": title, "priority": priority,
        "event_type": "security_alert" if category == "security" else "blocker",
    }, required=False)

    return chain


def build_sprint_complete_chain(
    plan_id: str,
    total_tasks: int,
    story_points: int,
) -> EventChain:
    """Build the event chain for sprint completion."""
    chain = EventChain(operation="sprint_complete")

    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"Sprint {plan_id} complete: {total_tasks} tasks, {story_points} SP",
        "tags": ["sprint", "complete", f"plan:{plan_id}"],
    })

    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet",
        "message": f"[fleet] Sprint {plan_id} COMPLETE: {total_tasks} tasks, {story_points} SP",
    }, required=False)

    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": f"Sprint {plan_id} complete!",
        "priority": "info",
        "event_type": "sprint_complete",
    }, required=False)

    return chain