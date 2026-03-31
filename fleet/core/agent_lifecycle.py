"""Agent lifecycle — smart status management for fleet agents.

Tracks agent activity and manages transitions between states:
  ACTIVE → IDLE → SLEEPING → OFFLINE

Agents wake on: task assignment, tag reference, @mention, explicit wake.
Agents sleep when idle too long. Heartbeat frequency adapts to status.

This module is used by the orchestrator to decide WHEN to wake agents
and HOW OFTEN to check on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class AgentStatus(str, Enum):
    """Smart agent status — drives heartbeat frequency and wake behavior.

    ACTIVE → IDLE → DROWSY → SLEEPING → OFFLINE

    DROWSY is content-aware: after 2-3 consecutive HEARTBEAT_OK responses,
    the agent signals "nothing for me" and the brain can evaluate
    deterministically instead of making a Claude call.

    > "the agent need to be able to do silent heartbeat when they deem
    > after a while that there is nothing new from the heartbeat, (2-3..)
    > then it relay the work to the brain to actually do a compare and an
    > automated work of the heartbeat in order to determine if it require
    > a real heartbeat."
    """

    ACTIVE = "active"       # Working on a task right now
    IDLE = "idle"           # Awake, watching for work (no active task)
    DROWSY = "drowsy"       # 2-3 HEARTBEAT_OK — brain can evaluate instead
    SLEEPING = "sleeping"   # Dormant, brain evaluates for free (no Claude calls)
    OFFLINE = "offline"     # Extended sleep, longer wake time


# Transition thresholds (seconds) — time-based fallbacks
IDLE_AFTER = 10 * 60          # 10 minutes without work → idle
SLEEPING_AFTER = 30 * 60      # 30 minutes idle → sleeping
OFFLINE_AFTER = 4 * 60 * 60   # 4 hours sleeping → offline

# Content-aware thresholds — HEARTBEAT_OK count based
DROWSY_AFTER_HEARTBEAT_OK = 2   # consecutive HEARTBEAT_OK → drowsy
SLEEPING_AFTER_HEARTBEAT_OK = 3  # consecutive HEARTBEAT_OK → sleeping

# Heartbeat intervals by status (seconds)
# IMPORTANT: keep these long enough to avoid flooding the board
HEARTBEAT_INTERVALS = {
    AgentStatus.ACTIVE: 0,              # No heartbeat — agent drives its own work
    AgentStatus.IDLE: 30 * 60,          # 30 minutes — normal monitoring
    AgentStatus.DROWSY: 60 * 60,        # 60 minutes — reduced, brain evaluates between
    AgentStatus.SLEEPING: 2 * 60 * 60,  # 2 hours — rare check
    AgentStatus.OFFLINE: 2 * 60 * 60,   # 2 hours — minimal check
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
    consecutive_heartbeat_ok: int = 0             # HEARTBEAT_OK count → drowsy/sleeping
    last_heartbeat_data_hash: str = ""            # Hash of pre-embed data at last heartbeat

    def update_activity(self, now: datetime, has_active_task: bool, task_id: str = "") -> None:
        """Update agent state based on current activity."""
        if has_active_task:
            self.status = AgentStatus.ACTIVE
            self.last_active_at = now
            self.current_task_id = task_id
            self.consecutive_heartbeat_ok = 0  # reset — agent is working
            return

        # No active task — transition based on HEARTBEAT_OK count
        # (content-aware) with time-based fallback
        if self.last_active_at is None:
            self.last_active_at = now

        idle_seconds = (now - self.last_active_at).total_seconds()

        # Content-aware transitions take priority over time-based
        if self.consecutive_heartbeat_ok >= SLEEPING_AFTER_HEARTBEAT_OK:
            self.status = AgentStatus.SLEEPING
        elif self.consecutive_heartbeat_ok >= DROWSY_AFTER_HEARTBEAT_OK:
            self.status = AgentStatus.DROWSY
        # Time-based fallback (if heartbeat_ok counting isn't happening)
        elif idle_seconds < IDLE_AFTER:
            self.status = AgentStatus.IDLE
        elif idle_seconds < SLEEPING_AFTER:
            # Use DROWSY as intermediate before SLEEPING
            if self.status != AgentStatus.DROWSY:
                self.status = AgentStatus.DROWSY
            else:
                self.status = AgentStatus.SLEEPING
        elif idle_seconds < OFFLINE_AFTER:
            self.status = AgentStatus.SLEEPING
        else:
            self.status = AgentStatus.OFFLINE

        self.current_task_id = None

    def record_heartbeat_ok(self) -> None:
        """Record that the agent's heartbeat returned HEARTBEAT_OK.

        Called by the orchestrator when an agent heartbeat produces
        no work. Drives content-aware sleep transitions.
        """
        self.consecutive_heartbeat_ok += 1

    def record_heartbeat_work(self) -> None:
        """Record that the agent's heartbeat produced actual work.

        Resets the HEARTBEAT_OK counter — agent is active.
        """
        self.consecutive_heartbeat_ok = 0

    def needs_heartbeat(self, now: datetime) -> bool:
        """Check if this agent needs a heartbeat based on status and interval."""
        if self.status == AgentStatus.ACTIVE:
            return False  # Active agents drive their own work

        interval = HEARTBEAT_INTERVALS.get(self.status, 300)
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
        return self.status in (AgentStatus.DROWSY, AgentStatus.SLEEPING, AgentStatus.OFFLINE)


class FleetLifecycle:
    """Manages the lifecycle state of all fleet agents.

    Used by the orchestrator to make smart decisions about:
    - When to send heartbeats (status-based intervals)
    - When to wake agents (task assignment, triggers)
    - When to let agents sleep (no work available)
    - Fleet resource optimization (don't cycle idle agents)
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
            "drowsy": [],
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