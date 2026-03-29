"""Heartbeat context bundler — pre-compute agent context without AI.

When the gateway fires a heartbeat for an agent, the orchestrator (or a
pre-heartbeat hook) bundles relevant information so the agent receives it
WITH the heartbeat message. The agent doesn't need to call fleet_read_context
or fleet_agent_status — the information is already there.

This saves tokens: instead of 3-5 tool calls per heartbeat (each consuming
tokens), the agent gets a pre-computed summary and only calls tools when
it needs to ACT on something.

> "an heartbeat should awake with the relevant informations to avoid making
> the AI make needless tools call, adapted to each agent we prefect the needed
> information to already give some information and view of the statuses and
> progressed and recent events and mentions and so on. no need to manually look
> everything the orchestrator just bundle it for your without any AI because
> its direct logic."
>
> "Where ever we can take this pattern to improve the work and the flow and
> the logic we will. Its very important that the AI focus on what it needs
> and doesn't waste time with needless tools call that can be pre-embedded."

The bundler uses direct API calls (no AI, no tokens) to build the context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fleet.core.models import Agent, Task, TaskStatus
from fleet.core.routing import AGENT_CAPABILITIES


@dataclass
class HeartbeatBundle:
    """Pre-computed context for an agent heartbeat. No AI needed to build this."""

    agent_name: str
    fleet_id: str = ""
    timestamp: str = ""

    # Work status
    assigned_tasks: list[dict] = field(default_factory=list)
    has_work: bool = False

    # Chat messages for this agent
    chat_messages: list[dict] = field(default_factory=list)
    has_chat: bool = False

    # Domain events (filtered by agent's capabilities)
    domain_events: list[dict] = field(default_factory=list)

    # Sprint progress (if agent is in a sprint)
    sprint_summary: str = ""

    # Fleet health snapshot
    agents_online: int = 0
    agents_total: int = 0
    tasks_blocked: int = 0
    pending_approvals: int = 0

    # Mentions
    mentioned_by: list[str] = field(default_factory=list)

    # Plane sprint data (PM and fleet-ops only — optional surface)
    plane_available: bool = False
    plane_sprint: str = ""
    plane_new_items: list[dict] = field(default_factory=list)
    plane_blocked: int = 0

    # Budget warning (if any)
    budget_warning: str = ""

    def format_message(self) -> str:
        """Format as a message to include in the heartbeat wake."""
        lines = [
            f"HEARTBEAT — {self.agent_name}",
            f"Time: {self.timestamp}",
            "",
        ]

        # Work status (most important)
        if self.has_work:
            lines.append("📋 YOU HAVE ASSIGNED WORK:")
            for t in self.assigned_tasks:
                lines.append(f"  - [{t['status']}] {t['title']} (id: {t['id']})")
            lines.append("")
        else:
            lines.append("No assigned tasks.")
            lines.append("")

        # Chat (second most important)
        if self.has_chat:
            lines.append(f"💬 {len(self.chat_messages)} CHAT MESSAGE(S) FOR YOU:")
            for m in self.chat_messages[:3]:
                lines.append(f"  [{m['source']}]: {m['content'][:100]}")
            lines.append("")

        # Mentions
        if self.mentioned_by:
            lines.append(f"📢 Mentioned by: {', '.join(self.mentioned_by)}")
            lines.append("")

        # Domain events
        if self.domain_events:
            lines.append(f"📌 {len(self.domain_events)} event(s) in your domain:")
            for e in self.domain_events[:3]:
                lines.append(f"  - {e['content'][:80]}")
            lines.append("")

        # Sprint
        if self.sprint_summary:
            lines.append(f"🏃 Sprint: {self.sprint_summary}")
            lines.append("")

        # Plane (PM and fleet-ops)
        if self.plane_available:
            if self.plane_sprint:
                lines.append(f"📊 Plane sprint: {self.plane_sprint}")
            if self.plane_new_items:
                lines.append(f"📥 {len(self.plane_new_items)} new Plane item(s):")
                for item in self.plane_new_items[:3]:
                    lines.append(f"  - [{item.get('priority','?')}] {item.get('title','?')[:60]}")
            if self.plane_blocked > 0:
                lines.append(f"🚫 {self.plane_blocked} blocked in Plane")
            lines.append("")
        elif self.agent_name in ("project-manager", "fleet-ops"):
            lines.append("📊 Plane: not configured")
            lines.append("")

        # Fleet health
        lines.append(
            f"Fleet: {self.agents_online}/{self.agents_total} online, "
            f"{self.tasks_blocked} blocked, {self.pending_approvals} pending approvals"
        )

        # Budget
        if self.budget_warning:
            lines.append(f"⚠️ BUDGET: {self.budget_warning}")

        # Instructions
        lines.append("")
        if self.has_work:
            lines.append("ACTION: Work on your assigned task(s). Use fleet tools for commits/progress/completion.")
        elif self.has_chat:
            lines.append("ACTION: Respond to chat messages using fleet_chat().")
        elif self.domain_events:
            lines.append("ACTION: Review domain events. Participate if relevant. Use fleet_chat() to respond.")
        else:
            lines.append("Nothing needs your attention. Respond HEARTBEAT_OK. Do NOT call any tools.")

        return "\n".join(lines)


def build_heartbeat_context(
    agent_name: str,
    tasks: list[Task],
    agents: list[Agent],
    board_memory: list = None,
    approvals: list = None,
    fleet_id: str = "",
    sprint_id: str = "",
    plane_data: dict = None,
    event_feed: list = None,
) -> HeartbeatBundle:
    """Build heartbeat context for an agent using direct data (no AI).

    This function uses ONLY the data passed to it — no API calls, no LLM.
    The caller (orchestrator or daemon) fetches the data once per cycle
    and passes it to this function for each agent.
    """
    now = datetime.now()
    bundle = HeartbeatBundle(
        agent_name=agent_name,
        fleet_id=fleet_id,
        timestamp=now.strftime("%Y-%m-%d %H:%M"),
    )

    # Assigned tasks for this agent
    for t in tasks:
        if t.custom_fields.agent_name == agent_name and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS):
            bundle.assigned_tasks.append({
                "id": t.id[:8],
                "title": t.title[:60],
                "status": t.status.value,
                "priority": t.priority,
            })
    bundle.has_work = len(bundle.assigned_tasks) > 0

    # Chat messages mentioning this agent
    if board_memory:
        for m in board_memory:
            tags = m.tags if hasattr(m, 'tags') else m.get('tags', [])
            if "chat" in tags and (
                f"mention:{agent_name}" in tags
                or "mention:all" in tags
                or (agent_name == "fleet-ops" and "mention:lead" in tags)
            ):
                source = m.source if hasattr(m, 'source') else m.get('source', '?')
                content = m.content if hasattr(m, 'content') else m.get('content', '')
                bundle.chat_messages.append({"source": source, "content": content[:200]})
                # Track who mentioned this agent
                if source and source not in bundle.mentioned_by:
                    bundle.mentioned_by.append(source)
    bundle.has_chat = len(bundle.chat_messages) > 0

    # Domain events — filter board memory by agent capabilities
    capabilities = AGENT_CAPABILITIES.get(agent_name, [])
    if board_memory and capabilities:
        for m in board_memory:
            tags = m.tags if hasattr(m, 'tags') else m.get('tags', [])
            content = m.content if hasattr(m, 'content') else m.get('content', '')
            if "chat" in tags:
                continue  # Chat already handled above
            # Check if any tag matches agent's domain
            content_lower = content.lower()
            if any(cap in content_lower for cap in capabilities[:5]):
                bundle.domain_events.append({"content": content[:150], "tags": tags})
                if len(bundle.domain_events) >= 5:
                    break

    # Sprint summary
    if sprint_id:
        sprint_tasks = [t for t in tasks if t.custom_fields.plan_id == sprint_id or t.custom_fields.sprint == sprint_id]
        done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
        total = len(sprint_tasks)
        if total > 0:
            bundle.sprint_summary = f"{done}/{total} done ({done*100//total}%)"

    # Fleet health
    bundle.agents_online = sum(1 for a in agents if a.status == "online" and "Gateway" not in a.name)
    bundle.agents_total = sum(1 for a in agents if "Gateway" not in a.name)
    bundle.tasks_blocked = sum(1 for t in tasks if t.is_blocked)
    bundle.pending_approvals = len(approvals) if approvals else 0

    # Plane data (PM and fleet-ops only — pre-fetched by caller)
    if plane_data and agent_name in ("project-manager", "fleet-ops"):
        bundle.plane_available = True
        bundle.plane_sprint = plane_data.get("sprint_summary", "")
        bundle.plane_new_items = plane_data.get("new_items", [])
        bundle.plane_blocked = plane_data.get("blocked_count", 0)

    # Event feed (from persistent event store — no API calls)
    if event_feed:
        for event in event_feed:
            priority = event.get("priority", "info")
            event_type = event.get("type", "")
            title = event.get("data", {}).get("title", event.get("data", {}).get("summary", event_type))

            if priority in ("urgent", "important"):
                bundle.domain_events.append({
                    "content": f"[{priority.upper()}] {title[:100]}",
                    "tags": event.get("data", {}).get("tags", []),
                })
            elif agent_name in event.get("data", {}).get("mentions", []):
                bundle.mentioned_by.append(event.get("data", {}).get("agent", "system"))

    return bundle