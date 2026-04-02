"""Session manager — brain Step 10: context + rate limit awareness.

Two parallel countdowns managed together:
1. Context remaining (per agent): 7% = prepare, 5% = force compact
2. Rate limit remaining (fleet-wide): 85% = prepare, 90% = force action

Aggregate fleet context math:
  5 agents × 200K context near rollover = 1M token spike risk
  Force compact before rollover to prevent 20% quota spike.

Source: fleet-vision-architecture §35, §92, PO requirements CW-01 to CW-10
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class SessionAction(str, Enum):
    """Actions the session manager can take."""
    NONE = "none"
    MONITOR = "monitor"
    PREPARE_COMPACT = "prepare_compact"
    FORCE_COMPACT = "force_compact"
    DUMP_TO_ARTIFACTS = "dump_to_artifacts"
    BLOCK_DISPATCH = "block_dispatch"
    STAGGER_COMPACTION = "stagger_compaction"


@dataclass
class AgentSessionState:
    """Session state for one agent."""
    agent_name: str
    context_used_pct: float = 0.0     # 0-100
    context_window_size: int = 200000  # 200K or 1M
    has_in_progress_task: bool = False
    predicted_work: bool = False       # Does this agent have queued work?
    consecutive_heartbeat_ok: int = 0
    last_heartbeat_cost: float = 0.0


@dataclass
class SessionDecision:
    """Decision for one agent's session."""
    agent_name: str
    action: SessionAction
    reason: str
    priority: int = 0  # Higher = do first


@dataclass
class FleetSessionState:
    """Aggregate session state across all agents."""
    agents: list[AgentSessionState]
    rate_limit_5h_pct: float = 0.0
    rate_limit_7d_pct: float = 0.0
    minutes_to_rollover: float = 300.0  # Minutes until 5h window resets
    budget_mode: str = "standard"


# ─── Per-Agent Evaluation ────────────────────────────────────────────


# Thresholds from PO requirements (§35.4)
CONTEXT_PREPARE_PCT = 93.0     # 7% remaining → start preparing
CONTEXT_FORCE_PCT = 95.0       # 5% remaining → force action
CONTEXT_HEAVY_TOKENS = 40000   # Below this, don't bother compacting
CONTEXT_MAX_FOR_DISPATCH = 800000  # Don't dispatch 1M quests above this


def evaluate_agent_session(
    agent: AgentSessionState,
    rate_limit_pct: float,
    minutes_to_rollover: float,
) -> SessionDecision:
    """Evaluate what to do about one agent's session.

    Args:
        agent: Agent's session state
        rate_limit_pct: Current rate limit usage (0-100)
        minutes_to_rollover: Minutes until rate limit window resets
    """
    context_remaining = 100.0 - agent.context_used_pct
    estimated_tokens = int(agent.context_window_size * agent.context_used_pct / 100)

    # Near rate limit rollover with heavy context → force compact
    if minutes_to_rollover < 30 and estimated_tokens > CONTEXT_HEAVY_TOKENS:
        if agent.has_in_progress_task:
            return SessionDecision(
                agent_name=agent.agent_name,
                action=SessionAction.PREPARE_COMPACT,
                reason=(
                    f"Rollover in {minutes_to_rollover:.0f}min, "
                    f"context={estimated_tokens} tokens — prepare compact"
                ),
                priority=2,
            )
        else:
            return SessionDecision(
                agent_name=agent.agent_name,
                action=SessionAction.DUMP_TO_ARTIFACTS,
                reason=(
                    f"Rollover in {minutes_to_rollover:.0f}min, "
                    f"no active task, {estimated_tokens} tokens — dump + fresh"
                ),
                priority=3,
            )

    # Context nearing capacity
    if agent.context_used_pct >= CONTEXT_FORCE_PCT:
        return SessionDecision(
            agent_name=agent.agent_name,
            action=SessionAction.FORCE_COMPACT,
            reason=f"Context at {agent.context_used_pct:.0f}% — force compact",
            priority=3,
        )

    if agent.context_used_pct >= CONTEXT_PREPARE_PCT:
        return SessionDecision(
            agent_name=agent.agent_name,
            action=SessionAction.PREPARE_COMPACT,
            reason=f"Context at {agent.context_used_pct:.0f}% — prepare for compact",
            priority=1,
        )

    # Heavy context with no predicted work → dump to artifacts
    if (estimated_tokens > CONTEXT_HEAVY_TOKENS
            and not agent.predicted_work
            and not agent.has_in_progress_task
            and agent.consecutive_heartbeat_ok >= 3):
        return SessionDecision(
            agent_name=agent.agent_name,
            action=SessionAction.DUMP_TO_ARTIFACTS,
            reason=(
                f"No predicted work, {estimated_tokens} tokens, "
                f"{agent.consecutive_heartbeat_ok} idle heartbeats — dump"
            ),
            priority=0,
        )

    return SessionDecision(
        agent_name=agent.agent_name,
        action=SessionAction.NONE,
        reason="Session healthy",
    )


# ─── Fleet-Wide Evaluation ───────────────────────────────────────────


@dataclass
class FleetSessionDecisions:
    """Aggregate decisions for the whole fleet."""
    per_agent: list[SessionDecision]
    fleet_action: SessionAction
    fleet_reason: str
    total_estimated_tokens: int
    rollover_spike_risk: float  # 0.0 to 1.0


def evaluate_fleet_sessions(state: FleetSessionState) -> FleetSessionDecisions:
    """Evaluate ALL agent sessions together for coordinated management.

    This is brain Step 10 — runs every orchestrator cycle.
    """
    per_agent = []
    total_tokens = 0

    for agent in state.agents:
        decision = evaluate_agent_session(
            agent, state.rate_limit_5h_pct, state.minutes_to_rollover,
        )
        per_agent.append(decision)
        total_tokens += int(agent.context_window_size * agent.context_used_pct / 100)

    # Sort by priority (highest first — most urgent compactions first)
    per_agent.sort(key=lambda d: d.priority, reverse=True)

    # Fleet-level assessment
    fleet_action = SessionAction.NONE
    fleet_reason = "Fleet sessions healthy"

    # Aggregate rollover spike risk
    # If total tokens near rollover is high, all agents refreshing = massive spike
    rollover_spike_risk = 0.0
    if state.minutes_to_rollover < 30:
        # Risk = total tokens / remaining quota estimate
        # Simplified: high tokens near rollover = high risk
        rollover_spike_risk = min(1.0, total_tokens / 500000)

    # Rate limit pressure
    if state.rate_limit_5h_pct >= 90:
        fleet_action = SessionAction.BLOCK_DISPATCH
        fleet_reason = f"Rate limit at {state.rate_limit_5h_pct:.0f}% — dispatch blocked"
    elif state.rate_limit_5h_pct >= 85:
        fleet_action = SessionAction.PREPARE_COMPACT
        fleet_reason = (
            f"Rate limit at {state.rate_limit_5h_pct:.0f}% — "
            f"preparing compactions, no heavy dispatches"
        )

    # Stagger compactions (don't compact all at once)
    compact_count = sum(
        1 for d in per_agent
        if d.action in (SessionAction.FORCE_COMPACT, SessionAction.PREPARE_COMPACT)
    )
    if compact_count > 2:
        fleet_action = SessionAction.STAGGER_COMPACTION
        fleet_reason = (
            f"{compact_count} agents need compaction — staggering over cycles"
        )

    return FleetSessionDecisions(
        per_agent=per_agent,
        fleet_action=fleet_action,
        fleet_reason=fleet_reason,
        total_estimated_tokens=total_tokens,
        rollover_spike_risk=rollover_spike_risk,
    )
