"""Heartbeat gate — brain evaluation for idle/sleeping agents.

When an agent has brain_evaluates=True (after 1 HEARTBEAT_OK),
the brain evaluates deterministically in Python (FREE, no Claude call):
  - Direct mention? → WAKE
  - Task assigned? → WAKE
  - Contribution task? → WAKE
  - PO directive? → WAKE
  - Role-specific trigger? → WAKE
  - Nothing? → STAY SLEEPING ($0)

Impact: ~70% cost reduction on idle fleet.

Source: fleet-elevation/23, fleet-vision-architecture §33.21, §85
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class HeartbeatDecision(str, Enum):
    """Result of brain heartbeat evaluation."""
    WAKE = "wake"           # Fire real heartbeat with Claude
    SILENT = "silent"       # No Claude call, $0 cost
    STRATEGIC = "strategic"  # Wake with specific config (model, effort)


@dataclass
class WakeReason:
    """Why an agent should wake up."""
    trigger: str        # mention, task, contribution, directive, role_trigger
    details: str        # Human-readable description
    urgency: str = "normal"  # normal, high, critical


@dataclass
class HeartbeatEvaluation:
    """Result of evaluating whether an agent needs a real heartbeat."""
    agent_name: str
    decision: HeartbeatDecision
    reasons: list[WakeReason]
    model_override: Optional[str] = None   # Strategic: use specific model
    effort_override: Optional[str] = None  # Strategic: use specific effort


def evaluate_agent_heartbeat(
    agent_name: str,
    agent_role: str,
    mentions: list[dict],
    assigned_tasks: list[dict],
    directives: list[dict],
    contributions_pending: list[dict],
    events_since_last: list[dict],
    consecutive_heartbeat_ok: int = 0,
) -> HeartbeatEvaluation:
    """Evaluate whether a sleeping/idle agent needs a real heartbeat.

    This runs in Python (FREE) before deciding whether to make a
    Claude API call ($$$). The goal is to avoid waking agents
    that have nothing to do.

    Args:
        agent_name: Agent being evaluated
        agent_role: Agent's role (project-manager, architect, etc.)
        mentions: Board memory entries with mention:{agent_name}
        assigned_tasks: Tasks assigned to this agent (INBOX or IN_PROGRESS)
        directives: PO directives targeted at this agent
        contributions_pending: Contribution tasks for this agent
        events_since_last: Events since last heartbeat
        consecutive_heartbeat_ok: How many consecutive no-work heartbeats

    Returns:
        HeartbeatEvaluation with decision + reasons
    """
    reasons: list[WakeReason] = []

    # 1. Direct mention — someone is talking to this agent
    if mentions:
        for m in mentions:
            reasons.append(WakeReason(
                trigger="mention",
                details=f"@{agent_name} mentioned: {str(m.get('content', ''))[:80]}",
                urgency="high" if "urgent" in str(m.get("tags", [])) else "normal",
            ))

    # 2. PO directive targeted at this agent
    if directives:
        for d in directives:
            reasons.append(WakeReason(
                trigger="directive",
                details=f"PO directive: {str(d.get('content', ''))[:80]}",
                urgency="high",
            ))

    # 3. New task assigned (INBOX status)
    inbox_tasks = [t for t in assigned_tasks
                   if t.get("status") == "inbox"]
    if inbox_tasks:
        for t in inbox_tasks:
            reasons.append(WakeReason(
                trigger="task",
                details=f"New task: {t.get('title', 'untitled')[:60]}",
                urgency="normal",
            ))

    # 4. Contribution task pending
    if contributions_pending:
        for c in contributions_pending:
            reasons.append(WakeReason(
                trigger="contribution",
                details=f"Contribution needed: {c.get('title', '')[:60]}",
                urgency="normal",
            ))

    # 5. Role-specific triggers
    if agent_role == "project-manager":
        # PM wakes when there are unassigned tasks
        unassigned = [t for t in assigned_tasks
                      if not t.get("agent_name") and t.get("status") == "inbox"]
        # Note: PM sees ALL inbox tasks, not just their own
        # This check would need the full task list, not just assigned
        pass

    elif agent_role == "fleet-ops":
        # Fleet-ops wakes when there are pending approvals
        review_events = [e for e in events_since_last
                         if "review" in str(e.get("type", "")).lower()
                         or "approval" in str(e.get("type", "")).lower()]
        if review_events:
            reasons.append(WakeReason(
                trigger="role_trigger",
                details=f"Pending reviews: {len(review_events)} since last heartbeat",
                urgency="normal",
            ))

    elif agent_role == "devsecops-expert":
        # DevSecOps wakes on security events
        security_events = [e for e in events_since_last
                           if "security" in str(e.get("type", "")).lower()
                           or "alert" in str(e.get("type", "")).lower()]
        if security_events:
            reasons.append(WakeReason(
                trigger="role_trigger",
                details=f"Security events: {len(security_events)}",
                urgency="high",
            ))

    # Decision
    if not reasons:
        return HeartbeatEvaluation(
            agent_name=agent_name,
            decision=HeartbeatDecision.SILENT,
            reasons=[],
        )

    # Determine if strategic config needed
    has_urgent = any(r.urgency in ("high", "critical") for r in reasons)
    has_task = any(r.trigger == "task" for r in reasons)

    if has_urgent:
        return HeartbeatEvaluation(
            agent_name=agent_name,
            decision=HeartbeatDecision.STRATEGIC,
            reasons=reasons,
            model_override="opus-4-6",  # Urgent → best model
            effort_override="high",
        )

    if has_task:
        return HeartbeatEvaluation(
            agent_name=agent_name,
            decision=HeartbeatDecision.WAKE,
            reasons=reasons,
        )

    return HeartbeatEvaluation(
        agent_name=agent_name,
        decision=HeartbeatDecision.WAKE,
        reasons=reasons,
    )
