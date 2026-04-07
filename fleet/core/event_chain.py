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
    PLANE = "plane"         # Plane: issue updates, comments (optional)
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

    # Plane (optional — fires only if Plane configured and issue mapped)
    chain.add(EventSurface.PLANE, "update_issue_state", {
        "issue_id": "",  # Filled by caller if Plane issue exists
        "project_id": "",
        "state": "In Review",
    }, required=False)
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",
        "project_id": "",
        "comment": f"OCMC task completed by {agent_name}: {summary[:80]}",
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


def _trail_event(task_id: str, event_type: str, content: str, agent: str = "") -> Event:
    """Helper: create an INTERNAL trail event for board memory.

    Every chain should record a trail event so the accountability
    generator can reconstruct the complete task history.
    """
    tags = ["trail", f"task:{task_id}", event_type]
    if agent:
        tags.append(f"agent:{agent}")
    return Event(
        surface=EventSurface.INTERNAL,
        action="post_board_memory",
        params={"content": content, "tags": tags},
        required=False,  # trail recording must never break the chain
    )


def build_contribution_chain(
    agent_name: str,
    target_task_id: str,
    target_task_title: str,
    contribution_type: str,
    summary: str = "",
) -> EventChain:
    """Build the event chain when an agent posts a contribution.

    Fires across: board memory (trail), IRC (#contributions), and
    optionally Plane (comment on target issue).
    """
    chain = EventChain(
        operation="contribution",
        source_agent=agent_name,
        task_id=target_task_id,
    )

    # Board memory — trail event on target task
    chain.events.append(_trail_event(
        target_task_id, "contribution_received",
        f"Contribution: {contribution_type} from {agent_name}. {summary[:100]}",
        agent=agent_name,
    ))

    # IRC — #contributions channel
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#contributions",
        "message": f"[{agent_name}] {contribution_type} → {target_task_title[:40]}",
    }, required=False)

    # Plane — comment on target issue (if mapped)
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",  # filled by caller if Plane issue exists
        "project_id": "",
        "comment": f"[{agent_name}] Contributed {contribution_type}: {summary[:80]}",
    }, required=False)

    return chain


def build_gate_request_chain(
    agent_name: str,
    task_id: str,
    task_title: str,
    gate_type: str,
    summary: str,
) -> EventChain:
    """Build the event chain for a PO gate request.

    Gates require PO approval. Routes to: board memory (po-required),
    IRC (#gates), ntfy (high priority to PO).
    """
    chain = EventChain(
        operation="gate_request",
        source_agent=agent_name,
        task_id=task_id,
    )

    # Board memory — tagged for PO attention
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"GATE REQUEST: {gate_type}\nTask: {task_title}\n{summary}",
        "tags": ["gate", "po-required", gate_type, f"task:{task_id}"],
    })

    # IRC — #gates channel
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#gates",
        "message": f"[gate] {gate_type}: {task_title[:40]} — PO approval needed",
    }, required=False)

    # ntfy — high priority to PO
    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": f"Gate: {gate_type}",
        "message": f"Task: {task_title}\n{summary[:200]}",
        "priority": "important",
        "event_type": "review_needed",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "gate_requested",
        f"Gate requested: {gate_type} by {agent_name}. {summary[:80]}",
        agent=agent_name,
    ))

    return chain


def build_rejection_chain(
    reviewer_name: str,
    task_id: str,
    task_title: str,
    agent_name: str,
    reason: str,
    regressed_readiness: int = 0,
    regressed_stage: str = "",
) -> EventChain:
    """Build the event chain when fleet-ops rejects a task.

    Notifies the agent, records trail, alerts IRC #reviews.
    """
    chain = EventChain(
        operation="rejection",
        source_agent=reviewer_name,
        task_id=task_id,
    )

    # Board memory — mention the agent with rejection details
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": (
            f"REJECTED by {reviewer_name}: {task_title}\n"
            f"Reason: {reason}\n"
            f"Readiness: → {regressed_readiness}%"
            + (f", Stage: → {regressed_stage}" if regressed_stage else "")
        ),
        "tags": ["review", "rejection", f"task:{task_id}",
                 f"mention:{agent_name}"],
    })

    # IRC — #reviews channel
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#reviews",
        "message": f"[rejected] {task_title[:40]}: {reason[:60]}",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "rejected",
        f"Rejected by {reviewer_name}. Reason: {reason[:100]}. "
        f"Readiness → {regressed_readiness}%.",
        agent=reviewer_name,
    ))

    return chain


def build_phase_advance_chain(
    task_id: str,
    task_title: str,
    from_phase: str,
    to_phase: str,
    approved_by: str = "po",
) -> EventChain:
    """Build the event chain when a delivery phase advances.

    Phase advancement is always a PO decision. Records trail,
    notifies fleet via IRC and ntfy.
    """
    chain = EventChain(
        operation="phase_advance",
        task_id=task_id,
    )

    # Board memory
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"Phase advanced: {from_phase} → {to_phase} ({task_title})",
        "tags": ["phase", "milestone", f"task:{task_id}"],
    })

    # IRC — #fleet and #sprint
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet",
        "message": f"[phase] {task_title[:40]}: {from_phase} → {to_phase}",
    }, required=False)
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#sprint",
        "message": f"[milestone] {task_title[:40]} advanced to {to_phase}",
    }, required=False)

    # ntfy
    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": f"Phase: {from_phase} → {to_phase}",
        "message": task_title,
        "priority": "info",
        "event_type": "sprint_milestone",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "phase_advanced",
        f"Phase advanced: {from_phase} → {to_phase}. Approved by {approved_by}.",
    ))

    return chain


def build_transfer_chain(
    from_agent: str,
    to_agent: str,
    task_id: str,
    task_title: str,
    stage: str = "",
    readiness: int = 0,
) -> EventChain:
    """Build the event chain when a task transfers between agents."""
    chain = EventChain(
        operation="transfer",
        source_agent=from_agent,
        task_id=task_id,
    )

    # Board memory — mention receiving agent
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": f"Task transferred: {from_agent} → {to_agent}: {task_title}",
        "tags": ["transfer", f"task:{task_id}", f"mention:{to_agent}"],
    })

    # IRC
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet",
        "message": f"[transfer] {from_agent} → {to_agent}: {task_title[:40]}",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "transferred",
        f"Transferred from {from_agent} to {to_agent} at stage {stage}, "
        f"readiness {readiness}%.",
        agent=from_agent,
    ))

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


# ─── New Chain Builders — Elevated Tool Trees ───────────────────────────


def build_comment_chain(
    agent_name: str,
    task_id: str = "",
    content: str = "",
    mention: str = "",
    channel: str = "#fleet",
) -> EventChain:
    """Build the event chain for fleet_chat — comment propagation.

    Board memory + IRC + Plane comment + events + trail.
    If @po or @human mentioned, also fires ntfy.
    """
    chain = EventChain(
        operation="chat_message",
        source_agent=agent_name,
        task_id=task_id,
    )

    # Board memory — already done by tool as primary action
    # IRC — already done by tool as primary action
    # Chain handles: Plane propagation, trail, ntfy for PO mentions

    # Plane — comment on linked issue (if task has one)
    if task_id:
        mention_prefix = f"@{mention} " if mention else ""
        chain.add(EventSurface.PLANE, "post_comment", {
            "issue_id": "",  # filled by caller if Plane issue exists
            "project_id": "",
            "comment": f"[{agent_name}] {mention_prefix}{content[:200]}",
        }, required=False)

    # ntfy — if mentioning PO/human
    if mention in ("human", "po", "PO"):
        chain.add(EventSurface.NOTIFY, "ntfy_publish", {
            "title": f"Fleet chat from {agent_name}",
            "message": content[:300],
            "priority": "important",
            "event_type": "review_needed",
        }, required=False)

    # Trail
    if task_id:
        chain.events.append(_trail_event(
            task_id, "chat_message",
            f"Chat by {agent_name}" + (f" @{mention}" if mention else "") + f": {content[:80]}",
            agent=agent_name,
        ))

    return chain


def build_accept_chain(
    agent_name: str,
    task_id: str,
    task_title: str,
    plan_summary: str = "",
) -> EventChain:
    """Build the event chain for fleet_task_accept — plan acceptance propagation.

    IRC + Plane state/comment + events + trail.
    Primary action (MC update_task + post_comment) done by tool directly.
    """
    chain = EventChain(
        operation="task_accept",
        source_agent=agent_name,
        task_id=task_id,
    )

    # Plane — update state + post plan comment
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",
        "project_id": "",
        "comment": f"[{agent_name}] Plan accepted: {plan_summary[:150]}",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "plan_accepted",
        f"Plan accepted by {agent_name}: {plan_summary[:100]}",
        agent=agent_name,
    ))

    return chain


def build_commit_chain(
    agent_name: str,
    task_id: str,
    message: str,
    sha: str = "",
    files: list[str] | None = None,
) -> EventChain:
    """Build the event chain for fleet_commit — commit propagation.

    MC comment + Plane comment + events + trail + methodology verify.
    Primary action (git add + git commit) done by tool directly.
    """
    chain = EventChain(
        operation="task_commit",
        source_agent=agent_name,
        task_id=task_id,
    )

    # MC — post commit summary as task comment
    file_summary = ", ".join((files or [])[:5])
    if files and len(files) > 5:
        file_summary += f" (+{len(files) - 5} more)"
    chain.add(EventSurface.INTERNAL, "post_comment", {
        "task_id": task_id,
        "comment": f"**Commit** `{sha[:7] if sha else '???'}`: {message}\nFiles: {file_summary}",
    }, required=False)

    # Plane — commit summary on linked issue
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",
        "project_id": "",
        "comment": f"[{agent_name}] Commit: {message}",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "commit",
        f"Commit by {agent_name}: {message} ({sha[:7] if sha else 'no-sha'})",
        agent=agent_name,
    ))

    return chain


def build_task_create_chain(
    creator: str,
    task_id: str,
    task_title: str,
    parent_task_id: str = "",
    agent_name: str = "",
    task_type: str = "",
    project: str = "",
) -> EventChain:
    """Build the event chain for fleet_task_create — task creation propagation.

    Parent comment + IRC + Plane create_issue + events + trail.
    Primary action (mc.create_task) done by tool directly.
    """
    chain = EventChain(
        operation="task_create",
        source_agent=creator,
        task_id=task_id,
    )

    # MC — comment on parent task (if parent exists)
    if parent_task_id:
        chain.add(EventSurface.INTERNAL, "post_comment", {
            "task_id": parent_task_id,
            "comment": (
                f"**Subtask created** by {creator}: {task_title}\n"
                f"Type: {task_type or 'task'} → {agent_name or 'unassigned'}"
            ),
        }, required=False)

    # Plane — create linked issue (if project configured)
    if project:
        chain.add(EventSurface.PLANE, "create_issue", {
            "project_id": "",  # filled by caller if Plane project mapped
            "title": task_title,
            "description": f"Created by {creator} from OCMC. Type: {task_type or 'task'}.",
            "priority": "medium",
        }, required=False)

    # IRC — already done by tool as primary action

    # Trail
    chain.events.append(_trail_event(
        task_id, "task_created",
        f"Task created by {creator}: {task_title}. "
        f"Parent: {parent_task_id[:8] if parent_task_id else 'none'}. "
        f"Agent: {agent_name or 'unassigned'}.",
        agent=creator,
    ))

    return chain


def build_pause_chain(
    agent_name: str,
    task_id: str,
    task_title: str,
    reason: str,
    needed: str = "",
) -> EventChain:
    """Build the event chain for fleet_pause — blocker propagation.

    Board memory (PM mention) + Plane comment + events + trail.
    Primary action (MC post_comment + IRC) done by tool directly.
    """
    chain = EventChain(
        operation="task_paused",
        source_agent=agent_name,
        task_id=task_id,
    )

    # Board memory — mention PM so they see the blocker
    chain.add(EventSurface.INTERNAL, "post_board_memory", {
        "content": (
            f"**BLOCKED** — {agent_name} on {task_title[:40]}:\n"
            f"Reason: {reason}\n"
            f"Needed: {needed}"
        ),
        "tags": ["blocked", f"task:{task_id}", f"mention:project-manager",
                 f"agent:{agent_name}"],
    }, required=False)

    # Plane — comment on linked issue
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",
        "project_id": "",
        "comment": f"[{agent_name}] BLOCKED: {reason}. Needed: {needed}",
    }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "task_paused",
        f"Paused by {agent_name}. Reason: {reason[:80]}. Needed: {needed[:80]}.",
        agent=agent_name,
    ))

    return chain


def build_escalation_chain(
    agent_name: str,
    task_id: str,
    title: str,
    details: str,
    question: str = "",
) -> EventChain:
    """Build the event chain for fleet_escalate — escalation propagation.

    Plane comment + events + trail.
    Primary action (board memory + IRC + ntfy) done by tool directly.
    """
    chain = EventChain(
        operation="escalation",
        source_agent=agent_name,
        task_id=task_id or "",
    )

    # Plane — comment on linked issue
    if task_id:
        chain.add(EventSurface.PLANE, "post_comment", {
            "issue_id": "",
            "project_id": "",
            "comment": f"[{agent_name}] ESCALATED: {title}. {details[:150]}",
        }, required=False)

    # Trail
    if task_id:
        chain.events.append(_trail_event(
            task_id, "escalated",
            f"Escalated by {agent_name}: {title}. {question[:60] if question else ''}",
            agent=agent_name,
        ))

    return chain


def build_progress_chain(
    agent_name: str,
    task_id: str,
    task_title: str,
    done: str = "",
    next_step: str = "",
    blockers: str = "none",
    progress_pct: int = 0,
) -> EventChain:
    """Build the event chain for fleet_task_progress — progress propagation.

    Plane labels/comment + IRC at checkpoints + events + trail.
    Primary action (MC post_comment + update custom field) done by tool directly.
    """
    chain = EventChain(
        operation="task_progress",
        source_agent=agent_name,
        task_id=task_id,
    )

    # Plane — comment with progress summary
    chain.add(EventSurface.PLANE, "post_comment", {
        "issue_id": "",
        "project_id": "",
        "comment": (
            f"[{agent_name}] Progress {progress_pct}%: {done[:100]}"
            + (f"\nNext: {next_step[:80]}" if next_step else "")
        ),
    }, required=False)

    # IRC — only at significant checkpoints (50%, 90%)
    if progress_pct in (50, 90):
        chain.add(EventSurface.CHANNEL, "notify_irc", {
            "channel": "#fleet",
            "message": f"[{agent_name}] {task_title[:40]} — {progress_pct}% complete",
        }, required=False)

    # Trail
    chain.events.append(_trail_event(
        task_id, "progress_update",
        f"Progress by {agent_name}: {progress_pct}%. Done: {done[:60]}.",
        agent=agent_name,
    ))

    return chain


def build_artifact_chain(
    agent_name: str,
    task_id: str,
    artifact_type: str,
    field: str = "",
    completeness_pct: int = 0,
    operation: str = "artifact_updated",
) -> EventChain:
    """Build the event chain for fleet_artifact_create/update — artifact propagation.

    Events + trail. Plane HTML already updated by tool directly via transpose.
    MC comment already posted by tool directly.
    """
    chain = EventChain(
        operation=operation,
        source_agent=agent_name,
        task_id=task_id,
    )

    # Trail
    detail = f"field={field}" if field else "created"
    chain.events.append(_trail_event(
        task_id, operation,
        f"Artifact {operation} by {agent_name}: {artifact_type} ({detail}). "
        f"Completeness: {completeness_pct}%.",
        agent=agent_name,
    ))

    return chain