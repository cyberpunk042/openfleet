"""Agent lifecycle — smart status management for fleet agents.

Tracks agent activity and manages transitions between states:
  ACTIVE → IDLE → SLEEPING → OFFLINE

Agents wake on: task assignment, tag reference, @mention, explicit wake.
After 1 HEARTBEAT_OK, the brain takes over evaluation (silent heartbeat).
The cron never stops — the brain intercepts and evaluates for free.

PO requirement (verbatim):
> "the agent need to be able to do silent heartbeat when they deem
> after a while that there is nothing new from the heartbeat, (2-3..)
> then it relay the work to the brain to actually do a compare and an
> automated work of the heartbeat in order to determine if it require
> a real heartbeat."

Refined (2026-04-01): 1 HEARTBEAT_OK is enough if done properly.
No intermediate "drowsy" state — after one heartbeat with nothing,
the brain takes the relay immediately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class AgentStatus(str, Enum):
    """Agent status — drives heartbeat behavior and cost.

    ACTIVE → IDLE → SLEEPING → OFFLINE

    After 1 HEARTBEAT_OK, agent transitions to IDLE and the brain
    takes over heartbeat evaluation. The cron still fires, but the
    brain intercepts — if nothing for this agent, silent OK ($0).
    If wake trigger found, brain fires real heartbeat with strategic config.

    The agent never stops. The brain is the filter between cron and Claude call.
    """

    ACTIVE = "active"       # Working on a task right now
    IDLE = "idle"           # 1 HEARTBEAT_OK — brain evaluates, cron still fires
    SLEEPING = "sleeping"   # Extended idle, brain evaluates, longer intervals
    OFFLINE = "offline"     # Very extended, slow wake


# Transition thresholds (seconds) — time-based
SLEEPING_AFTER = 30 * 60      # 30 minutes idle → sleeping
OFFLINE_AFTER = 4 * 60 * 60   # 4 hours sleeping → offline

# Content-aware threshold — 1 HEARTBEAT_OK = brain takes over
IDLE_AFTER_HEARTBEAT_OK = 1   # 1 proper heartbeat with nothing → brain relay

# MC computes agent status dynamically: if last_seen_at > OFFLINE_AFTER, agent
# shows as offline. Our heartbeat intervals MUST stay below this threshold or
# agents flicker offline between heartbeats.
MC_OFFLINE_AFTER = 10 * 60  # 10 minutes (MC's with_computed_status)

# Heartbeat intervals by status (seconds)
# All intervals < MC_OFFLINE_AFTER to prevent agents showing offline between beats.
# Brain evaluation is free (no Claude calls) so frequent checks cost nothing.
HEARTBEAT_INTERVALS = {
    AgentStatus.ACTIVE: 0,              # No cron — agent drives its own work
    AgentStatus.IDLE: 8 * 60,           # 8 minutes — frequent, brain-gated (free)
    AgentStatus.SLEEPING: 8 * 60,       # 8 minutes — same: must stay < MC_OFFLINE_AFTER
    AgentStatus.OFFLINE: 8 * 60,        # 8 minutes — same: agent stays visible in MC
}


@dataclass
class AgentState:
    """Tracked state for a single agent."""

    name: str
    status: AgentStatus = AgentStatus.IDLE
    last_active_at: Optional[datetime] = None    # Last time agent had work
    last_heartbeat_at: Optional[datetime] = None  # Last heartbeat sent
    last_task_completed_at: Optional[datetime] = None
    current_task_id: Optional[str] = None
    # Content-aware lifecycle fields
    consecutive_heartbeat_ok: int = 0             # HEARTBEAT_OK count
    last_heartbeat_data_hash: str = ""            # Hash of pre-embed data at last heartbeat

    def update_activity(self, now: datetime, has_active_task: bool, task_id: str = "") -> None:
        """Update agent state based on current activity."""
        if has_active_task:
            self.status = AgentStatus.ACTIVE
            self.last_active_at = now
            self.current_task_id = task_id
            self.consecutive_heartbeat_ok = 0  # reset — agent is working
            return

        # No active task — transition based on idle duration
        if self.last_active_at is None:
            self.last_active_at = now

        idle_seconds = (now - self.last_active_at).total_seconds()

        # After 1 HEARTBEAT_OK → IDLE (brain takes over)
        if self.consecutive_heartbeat_ok >= IDLE_AFTER_HEARTBEAT_OK:
            if idle_seconds >= OFFLINE_AFTER:
                self.status = AgentStatus.OFFLINE
            elif idle_seconds >= SLEEPING_AFTER:
                self.status = AgentStatus.SLEEPING
            else:
                self.status = AgentStatus.IDLE
        else:
            # Haven't had a HEARTBEAT_OK yet — still fresh idle
            self.status = AgentStatus.IDLE

        self.current_task_id = None

    def record_heartbeat_ok(self) -> None:
        """Record that the agent's heartbeat returned HEARTBEAT_OK.

        After 1 HEARTBEAT_OK, the brain takes over evaluation.
        The cron still fires, brain intercepts for free.
        """
        self.consecutive_heartbeat_ok += 1

    def record_heartbeat_work(self) -> None:
        """Record that the agent's heartbeat produced actual work.

        Resets the HEARTBEAT_OK counter — agent is active.
        """
        self.consecutive_heartbeat_ok = 0

    def needs_heartbeat(self, now: datetime) -> bool:
        """Check if this agent needs a heartbeat based on status and interval.

        Note: this determines if the CRON should fire. The brain's
        HeartbeatGate then decides if it's a real Claude call or silent OK.
        """
        if self.status == AgentStatus.ACTIVE:
            return False  # Active agents drive their own work

        interval = HEARTBEAT_INTERVALS.get(self.status, 600)
        if interval == 0:
            return False

        if self.last_heartbeat_at is None:
            return True

        return (now - self.last_heartbeat_at).total_seconds() >= interval

    def mark_heartbeat_sent(self, now: datetime) -> None:
        """Record that a heartbeat was sent."""
        self.last_heartbeat_at = now

    def wake(self, now: datetime) -> None:
        """Explicitly wake this agent (task assigned, @mention, etc.)."""
        self.status = AgentStatus.IDLE
        self.last_active_at = now
        self.consecutive_heartbeat_ok = 0  # reset — agent is awake

    def should_wake_for_task(self) -> bool:
        """Check if agent should be woken for a task assignment."""
        return self.status in (AgentStatus.IDLE, AgentStatus.SLEEPING, AgentStatus.OFFLINE)

    @property
    def brain_evaluates(self) -> bool:
        """Whether the brain should intercept this agent's heartbeat.

        After 1 HEARTBEAT_OK, the brain evaluates deterministically
        instead of making a Claude call. The cron still fires.
        """
        return self.consecutive_heartbeat_ok >= IDLE_AFTER_HEARTBEAT_OK


class FleetLifecycle:
    """Manages the lifecycle state of all fleet agents.

    Used by the orchestrator to make smart decisions about:
    - When to send heartbeats (status-based intervals)
    - When to wake agents (task assignment, triggers)
    - When the brain should intercept (brain_evaluates property)
    - Fleet resource optimization (idle agents cost $0)
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentState] = {}

    def get_or_create(self, name: str) -> AgentState:
        """Get or create agent state tracker."""
        if name not in self._agents:
            self._agents[name] = AgentState(name=name)
        return self._agents[name]

    def update_all(
        self,
        now: datetime,
        active_agents: dict[str, str],  # agent_name → task_id
    ) -> None:
        """Update all tracked agents based on current board state.

        Args:
            now: Current timestamp.
            active_agents: Map of agent names with active (in_progress) tasks.
        """
        for name, state in self._agents.items():
            task_id = active_agents.get(name, "")
            state.update_activity(now, bool(task_id), task_id)

    def agents_needing_heartbeat(self, now: datetime) -> list[AgentState]:
        """Return agents that need a heartbeat check."""
        return [
            state for state in self._agents.values()
            if state.needs_heartbeat(now)
        ]

    def get_status_summary(self) -> dict[str, list[str]]:
        """Return agent names grouped by status."""
        summary: dict[str, list[str]] = {
            "active": [],
            "idle": [],
            "sleeping": [],
            "offline": [],
        }
        for state in self._agents.values():
            summary[state.status.value].append(state.name)
        return summary

    def is_fleet_idle(self) -> bool:
        """Check if the entire fleet has no active work."""
        return all(
            s.status != AgentStatus.ACTIVE
            for s in self._agents.values()
        )
