"""Plane watcher — detects changes in Plane and emits fleet events.

Polls the Plane API for changes since the last check:
- New issues created (by human or PM)
- Issue state changes
- Issue priority changes
- New comments
- Cycle status changes

Each detected change becomes a CloudEvent in the event store,
routed to the appropriate agents via the event routing engine.

> "no matter from where I mention, that it be internal chat or Plane,
> or if I change something manually on the platform, you must detect
> and record the event and do the appropriate chain of operations"
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from fleet.core.events import EventStore, create_event
from fleet.infra.plane_client import PlaneClient

logger = logging.getLogger(__name__)


@dataclass
class PlaneWatcherState:
    """Tracks what we've seen to detect deltas."""

    # issue_id → last_updated_at
    known_issues: dict[str, str] = field(default_factory=dict)
    # cycle_id → status
    known_cycles: dict[str, str] = field(default_factory=dict)
    # Last poll timestamp
    last_poll: str = ""


class PlaneWatcher:
    """Polls Plane API and emits events for detected changes.

    Usage::

        watcher = PlaneWatcher(plane_client, workspace_slug="fleet")
        events = await watcher.poll()
        # events are automatically stored in EventStore
    """

    def __init__(
        self,
        plane: PlaneClient,
        workspace_slug: str = "fleet",
        state_path: str = "",
    ) -> None:
        self._plane = plane
        self._ws = workspace_slug
        self._store = EventStore()

        if not state_path:
            fleet_dir = os.environ.get("FLEET_DIR", ".")
            state_path = os.path.join(fleet_dir, ".fleet-plane-watcher.json")
        self._state_path = Path(state_path)
        self._state = self._load_state()

    def _load_state(self) -> PlaneWatcherState:
        if self._state_path.exists():
            try:
                with open(self._state_path) as f:
                    data = json.load(f)
                return PlaneWatcherState(
                    known_issues=data.get("known_issues", {}),
                    known_cycles=data.get("known_cycles", {}),
                    last_poll=data.get("last_poll", ""),
                )
            except Exception:
                pass
        return PlaneWatcherState()

    def _save_state(self) -> None:
        try:
            with open(self._state_path, "w") as f:
                json.dump({
                    "known_issues": self._state.known_issues,
                    "known_cycles": self._state.known_cycles,
                    "last_poll": self._state.last_poll,
                }, f)
        except Exception:
            pass

    async def poll(self) -> list[dict]:
        """Poll Plane for changes. Returns list of events emitted."""
        events_emitted = []

        try:
            projects = await self._plane.list_projects(self._ws)
        except Exception as e:
            logger.warning("Plane watcher: cannot list projects: %s", e)
            return events_emitted

        for proj in projects:
            try:
                # Check issues
                issues = await self._plane.list_issues(self._ws, proj.id, limit=50)
                for issue in issues:
                    issue_key = f"{proj.identifier}/{issue.id}"
                    known_updated = self._state.known_issues.get(issue_key, "")

                    if not known_updated:
                        # New issue
                        event = create_event(
                            "fleet.plane.issue_created",
                            source="fleet/core/plane_watcher",
                            subject=issue.id,
                            recipient="project-manager",
                            priority="info",
                            tags=["plane", f"project:{proj.identifier}"],
                            surfaces=["internal"],
                            title=issue.title,
                            priority_level=issue.priority,
                            project=proj.identifier,
                            issue_id=issue.id,
                            sequence_id=issue.sequence_id,
                        )
                        self._store.append(event)
                        events_emitted.append({
                            "type": "fleet.plane.issue_created",
                            "project": proj.identifier,
                            "title": issue.title,
                        })

                    elif issue.updated_at and issue.updated_at != known_updated:
                        # Issue changed — emit update event
                        event = create_event(
                            "fleet.plane.issue_updated",
                            source="fleet/core/plane_watcher",
                            subject=issue.id,
                            recipient="project-manager",
                            priority="info",
                            tags=["plane", f"project:{proj.identifier}"],
                            surfaces=["internal"],
                            title=issue.title,
                            project=proj.identifier,
                            issue_id=issue.id,
                        )
                        self._store.append(event)
                        events_emitted.append({
                            "type": "fleet.plane.issue_updated",
                            "project": proj.identifier,
                            "title": issue.title,
                        })

                    # Update known state
                    self._state.known_issues[issue_key] = issue.updated_at or ""

                # Check cycles
                cycles = await self._plane.list_cycles(self._ws, proj.id)
                for cycle in cycles:
                    cycle_key = f"{proj.identifier}/{cycle.id}"
                    known_status = self._state.known_cycles.get(cycle_key, "")

                    if cycle.status != known_status:
                        if known_status == "" and cycle.status:
                            # New cycle
                            pass  # Don't emit for existing cycles on first poll
                        elif cycle.status == "current" and known_status != "current":
                            event = create_event(
                                "fleet.plane.cycle_started",
                                source="fleet/core/plane_watcher",
                                subject=cycle.id,
                                recipient="project-manager",
                                priority="important",
                                mentions=["project-manager", "fleet-ops"],
                                tags=["plane", "sprint", f"project:{proj.identifier}"],
                                surfaces=["internal", "channel"],
                                cycle_name=cycle.name,
                                project=proj.identifier,
                            )
                            self._store.append(event)
                            events_emitted.append({
                                "type": "fleet.plane.cycle_started",
                                "project": proj.identifier,
                                "name": cycle.name,
                            })
                        elif cycle.status == "completed" and known_status != "completed":
                            event = create_event(
                                "fleet.plane.cycle_completed",
                                source="fleet/core/plane_watcher",
                                subject=cycle.id,
                                recipient="project-manager",
                                priority="important",
                                mentions=["project-manager", "fleet-ops"],
                                tags=["plane", "sprint", f"project:{proj.identifier}"],
                                surfaces=["internal", "channel", "notify"],
                                cycle_name=cycle.name,
                                project=proj.identifier,
                            )
                            self._store.append(event)
                            events_emitted.append({
                                "type": "fleet.plane.cycle_completed",
                                "project": proj.identifier,
                                "name": cycle.name,
                            })

                    self._state.known_cycles[cycle_key] = cycle.status or ""

            except Exception as e:
                logger.warning("Plane watcher: error polling %s: %s", proj.identifier, e)

        self._state.last_poll = datetime.utcnow().isoformat() + "Z"
        self._save_state()

        return events_emitted