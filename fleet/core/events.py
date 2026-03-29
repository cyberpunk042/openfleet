"""Fleet event system — CloudEvents-based event store and agent feeds.

Events are first-class objects. Notifications are views over events.

Uses CloudEvents (CNCF) as canonical schema:
  specversion: "1.0"
  type: "fleet.task.completed"
  source: "fleet/mcp/tools/fleet_task_complete"
  id: UUID
  time: ISO8601
  data: {...}

Fleet extensions:
  subject: task/agent/issue ID
  data.recipient: target agent (or "all", "pm", "lead")
  data.priority: urgent/important/info
  data.surfaces: which surfaces this event publishes to
  data.mentions: @agent-name references
  data.tags: capability/domain tags for routing
  data.actions: suggested actions for the recipient
  data.refs: cross-references to other surfaces

Agent feed = filtered projection of events:
  - Filtered by recipient, mentions, tags, capabilities
  - Ordered by priority then time
  - Tracked: seen/unseen per agent
  - Persistent: survives restarts
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ─── Event Types ──────────────────────────────────────────────────────────

# Naming: fleet.{domain}.{action}
EVENT_TYPES = {
    # Task lifecycle
    "fleet.task.created": "New task created in OCMC",
    "fleet.task.accepted": "Agent accepted a task with plan",
    "fleet.task.progress": "Agent reported progress",
    "fleet.task.completed": "Agent completed task (PR ready)",
    "fleet.task.approved": "fleet-ops approved task",
    "fleet.task.rejected": "fleet-ops rejected task",
    "fleet.task.dispatched": "Orchestrator dispatched task to agent",
    "fleet.task.blocked": "Task is blocked by dependency",
    "fleet.task.unblocked": "Task dependency resolved",

    # Plane lifecycle
    "fleet.plane.issue_created": "New issue in Plane",
    "fleet.plane.issue_updated": "Plane issue state/priority changed",
    "fleet.plane.issue_commented": "Comment on Plane issue",
    "fleet.plane.cycle_started": "Sprint started in Plane",
    "fleet.plane.cycle_completed": "Sprint completed in Plane",
    "fleet.plane.sync": "Plane ↔ OCMC sync completed",

    # GitHub lifecycle
    "fleet.github.pr_created": "PR created",
    "fleet.github.pr_merged": "PR merged",
    "fleet.github.pr_commented": "Comment on PR",
    "fleet.github.ci_passed": "CI checks passed",
    "fleet.github.ci_failed": "CI checks failed",
    "fleet.github.review_requested": "Review requested on PR",

    # Agent lifecycle
    "fleet.agent.online": "Agent came online",
    "fleet.agent.offline": "Agent went offline",
    "fleet.agent.heartbeat": "Agent heartbeat completed",
    "fleet.agent.stuck": "Agent stuck (no progress for X hours)",

    # Communication
    "fleet.chat.message": "Internal chat message",
    "fleet.chat.mention": "Agent @mentioned in chat",
    "fleet.alert.posted": "Alert posted",
    "fleet.escalation": "Escalation to human",

    # System
    "fleet.system.sync": "Cross-platform sync completed",
    "fleet.system.health": "Health check result",
    "fleet.system.config_changed": "Configuration changed",
    "fleet.system.gateway_restart": "Gateway restarted",
}


@dataclass
class FleetEvent:
    """A fleet event in CloudEvents format with fleet extensions.

    This is the canonical unit of the event bus. Everything that happens
    in the fleet is an event. Notifications are generated FROM events.
    """

    # CloudEvents required
    id: str = ""
    type: str = ""
    source: str = ""
    time: str = ""

    # CloudEvents optional
    subject: str = ""  # task_id, agent_name, issue_id

    # Fleet data payload
    data: dict = field(default_factory=dict)

    # Fleet extensions (stored in data for CloudEvents compat)
    @property
    def recipient(self) -> str:
        return self.data.get("recipient", "all")

    @property
    def priority(self) -> str:
        return self.data.get("priority", "info")

    @property
    def mentions(self) -> list[str]:
        return self.data.get("mentions", [])

    @property
    def tags(self) -> list[str]:
        return self.data.get("tags", [])

    @property
    def surfaces(self) -> list[str]:
        return self.data.get("surfaces", [])

    @property
    def actions(self) -> list[dict]:
        return self.data.get("actions", [])

    @property
    def refs(self) -> dict:
        return self.data.get("refs", {})

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.time:
            self.time = datetime.utcnow().isoformat() + "Z"


def create_event(
    event_type: str,
    source: str,
    subject: str = "",
    recipient: str = "all",
    priority: str = "info",
    mentions: list[str] | None = None,
    tags: list[str] | None = None,
    surfaces: list[str] | None = None,
    actions: list[dict] | None = None,
    refs: dict | None = None,
    **extra_data,
) -> FleetEvent:
    """Create a fleet event with standard fields."""
    data = {
        "recipient": recipient,
        "priority": priority,
        "mentions": mentions or [],
        "tags": tags or [],
        "surfaces": surfaces or ["internal"],
        "actions": actions or [],
        "refs": refs or {},
        **extra_data,
    }
    return FleetEvent(
        type=event_type,
        source=source,
        subject=subject,
        data=data,
    )


# ─── Event Store ──────────────────────────────────────────────────────────


class EventStore:
    """Persistent local event store. Survives restarts.

    Events are stored as JSONL (one event per line) for fast appending.
    Agent feeds are built by querying the store with filters.
    """

    def __init__(self, store_path: str = ""):
        if not store_path:
            fleet_dir = os.environ.get("FLEET_DIR", ".")
            store_path = os.path.join(fleet_dir, ".fleet-events.jsonl")
        self._path = Path(store_path)
        self._seen: dict[str, set[str]] = {}  # agent_name → set of event IDs seen
        self._seen_path = self._path.with_suffix(".seen.json")
        self._load_seen()

    def _load_seen(self) -> None:
        if self._seen_path.exists():
            try:
                with open(self._seen_path) as f:
                    raw = json.load(f)
                self._seen = {k: set(v) for k, v in raw.items()}
            except Exception:
                self._seen = {}

    def _save_seen(self) -> None:
        try:
            with open(self._seen_path, "w") as f:
                json.dump({k: list(v) for k, v in self._seen.items()}, f)
        except Exception:
            pass

    def append(self, event: FleetEvent) -> None:
        """Append an event to the store."""
        record = {
            "specversion": "1.0",
            "id": event.id,
            "type": event.type,
            "source": event.source,
            "subject": event.subject,
            "time": event.time,
            "data": event.data,
        }
        with open(self._path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def query(
        self,
        agent_name: str = "",
        event_types: list[str] | None = None,
        since: str = "",
        unseen_only: bool = False,
        limit: int = 50,
    ) -> list[FleetEvent]:
        """Query events matching filters. Returns newest first."""
        if not self._path.exists():
            return []

        events: list[FleetEvent] = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Type filter
                if event_types and record.get("type") not in event_types:
                    continue

                # Time filter
                if since and record.get("time", "") < since:
                    continue

                # Agent relevance filter
                data = record.get("data", {})
                if agent_name:
                    recipient = data.get("recipient", "all")
                    mentions = data.get("mentions", [])
                    tags = data.get("tags", [])

                    relevant = (
                        recipient == "all"
                        or recipient == agent_name
                        or agent_name in mentions
                        # PM gets unassigned items
                        or (agent_name == "project-manager" and recipient in ("pm", "unassigned"))
                        # fleet-ops gets lead items
                        or (agent_name == "fleet-ops" and recipient in ("lead", "ops"))
                    )
                    if not relevant:
                        continue

                # Unseen filter
                if unseen_only:
                    seen_ids = self._seen.get(agent_name, set())
                    if record["id"] in seen_ids:
                        continue

                events.append(FleetEvent(
                    id=record["id"],
                    type=record["type"],
                    source=record["source"],
                    subject=record.get("subject", ""),
                    time=record.get("time", ""),
                    data=data,
                ))

        # Newest first, limited
        events.sort(key=lambda e: e.time, reverse=True)
        return events[:limit]

    def mark_seen(self, agent_name: str, event_ids: list[str]) -> None:
        """Mark events as seen by an agent."""
        if agent_name not in self._seen:
            self._seen[agent_name] = set()
        self._seen[agent_name].update(event_ids)
        self._save_seen()

    def count_unseen(self, agent_name: str) -> int:
        """Count unseen events for an agent."""
        return len(self.query(agent_name=agent_name, unseen_only=True, limit=1000))