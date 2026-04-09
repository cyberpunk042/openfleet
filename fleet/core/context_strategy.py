"""Context strategy — progressive response to context and rate limit pressure.

Evaluates each agent's context usage and rate limit position, then
produces an action the orchestrator writes to the agent's pre-embed.
Agents see the action structurally — they don't poll for it.

Design: wiki/domains/architecture/context-strategy-design.md

Thresholds:
  Context: 70% AWARE → 80% PREPARE → 90% EXTRACT → 95% COMPACT
  Rate limit: 70% INFORM → 85% CONSERVE → 90% CRITICAL → 95% STOP

PO directive: "strategical in context switching and mindful of the
current context size relative to the next forced compact"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ContextAction(str, Enum):
    """Progressive action based on context/rate limit pressure."""
    NORMAL = "normal"       # < 70% — work freely
    AWARE = "aware"         # 70% — informed, no change needed
    PREPARE = "prepare"     # 80% — save working state to artifacts
    EXTRACT = "extract"     # 90% — dump state NOW before forced compact
    COMPACT = "compact"     # 95% — proactive compact (better than forced)


class RateLimitAction(str, Enum):
    """Progressive action based on rate limit pressure."""
    NORMAL = "normal"       # < 70%
    INFORM = "inform"       # 70% — agent informed, conserve when possible
    CONSERVE = "conserve"   # 85% — effort reduced
    CRITICAL = "critical"   # 90% — finish current op, no new dispatch
    STOP = "stop"           # 95% — hold all dispatch, wait for rollover


@dataclass
class ContextEvaluation:
    """Result of evaluating one agent's context and rate limit position."""
    agent_name: str
    context_pct: float
    rate_limit_pct: float
    context_action: ContextAction
    rate_limit_action: RateLimitAction
    message: str  # Human-readable for pre-embed injection

    @property
    def needs_attention(self) -> bool:
        return (self.context_action != ContextAction.NORMAL
                or self.rate_limit_action != RateLimitAction.NORMAL)

    @property
    def should_block_dispatch(self) -> bool:
        return self.rate_limit_action in (RateLimitAction.CRITICAL, RateLimitAction.STOP)

    @property
    def should_compact(self) -> bool:
        return self.context_action == ContextAction.COMPACT


class ContextStrategy:
    """Evaluate and respond to context pressure per agent.

    Called by orchestrator Step 0 (context refresh) every 30s cycle.
    Results written to agent pre-embed so agents see their position.
    """

    # Context thresholds
    CONTEXT_AWARE = 70.0
    CONTEXT_PREPARE = 80.0
    CONTEXT_EXTRACT = 90.0
    CONTEXT_COMPACT = 95.0

    # Rate limit thresholds
    RATE_INFORM = 70.0
    RATE_CONSERVE = 85.0
    RATE_CRITICAL = 90.0
    RATE_STOP = 95.0

    def __init__(self):
        # Track compaction times to stagger across agents
        self._last_compact: dict[str, datetime] = {}
        # Minimum seconds between compactions fleet-wide
        self._compact_stagger_seconds = 120

    def evaluate(
        self,
        agent_name: str,
        context_pct: float = 0.0,
        rate_limit_pct: float = 0.0,
    ) -> ContextEvaluation:
        """Evaluate context and rate limit position for one agent.

        Args:
            agent_name: Agent being evaluated.
            context_pct: Context window usage (0-100). 0 if unknown.
            rate_limit_pct: Rate limit usage (0-100). 0 if unknown.

        Returns:
            ContextEvaluation with actions and message for pre-embed.
        """
        ctx_action = self._evaluate_context(context_pct)
        rate_action = self._evaluate_rate_limit(rate_limit_pct)
        message = self._build_message(context_pct, rate_limit_pct, ctx_action, rate_action)

        return ContextEvaluation(
            agent_name=agent_name,
            context_pct=context_pct,
            rate_limit_pct=rate_limit_pct,
            context_action=ctx_action,
            rate_limit_action=rate_action,
            message=message,
        )

    def should_dispatch(self, rate_limit_pct: float) -> bool:
        """Can the fleet dispatch new work at this rate limit level?"""
        return rate_limit_pct < self.RATE_CRITICAL

    def should_compact_agent(self, agent_name: str, context_pct: float) -> bool:
        """Should this agent be proactively compacted?

        Checks context threshold AND stagger (don't compact all agents at once).
        """
        if context_pct < self.CONTEXT_COMPACT:
            return False

        # Stagger check — don't compact if another agent compacted recently
        now = datetime.now()
        for name, last_time in self._last_compact.items():
            if name != agent_name:
                elapsed = (now - last_time).total_seconds()
                if elapsed < self._compact_stagger_seconds:
                    logger.debug(
                        "Stagger: skip compact for %s — %s compacted %ds ago",
                        agent_name, name, elapsed,
                    )
                    return False

        return True

    def record_compaction(self, agent_name: str) -> None:
        """Record that an agent was compacted (for stagger tracking)."""
        self._last_compact[agent_name] = datetime.now()

    def _evaluate_context(self, pct: float) -> ContextAction:
        if pct <= 0:
            return ContextAction.NORMAL  # No data
        if pct >= self.CONTEXT_COMPACT:
            return ContextAction.COMPACT
        if pct >= self.CONTEXT_EXTRACT:
            return ContextAction.EXTRACT
        if pct >= self.CONTEXT_PREPARE:
            return ContextAction.PREPARE
        if pct >= self.CONTEXT_AWARE:
            return ContextAction.AWARE
        return ContextAction.NORMAL

    def _evaluate_rate_limit(self, pct: float) -> RateLimitAction:
        if pct <= 0:
            return RateLimitAction.NORMAL  # No data
        if pct >= self.RATE_STOP:
            return RateLimitAction.STOP
        if pct >= self.RATE_CRITICAL:
            return RateLimitAction.CRITICAL
        if pct >= self.RATE_CONSERVE:
            return RateLimitAction.CONSERVE
        if pct >= self.RATE_INFORM:
            return RateLimitAction.INFORM
        return RateLimitAction.NORMAL

    def _build_message(
        self,
        context_pct: float,
        rate_limit_pct: float,
        ctx_action: ContextAction,
        rate_action: RateLimitAction,
    ) -> str:
        """Build human-readable message for agent pre-embed."""
        parts = []

        if ctx_action == ContextAction.NORMAL and rate_action == RateLimitAction.NORMAL:
            return ""  # No message needed

        if ctx_action == ContextAction.AWARE:
            parts.append(f"Context: {context_pct:.0f}% used. Aware — no action needed yet.")
        elif ctx_action == ContextAction.PREPARE:
            parts.append(
                f"Context: {context_pct:.0f}% used. PREPARE — save working state "
                "to artifacts (fleet_task_progress, fleet_artifact_update, fleet_commit) "
                "before continuing."
            )
        elif ctx_action == ContextAction.EXTRACT:
            parts.append(
                f"Context: {context_pct:.0f}% used. EXTRACT — dump all working state "
                "to artifacts NOW. Commit uncommitted work. Post progress. "
                "Forced compaction is imminent."
            )
        elif ctx_action == ContextAction.COMPACT:
            parts.append(
                f"Context: {context_pct:.0f}% used. COMPACT — proactive compaction "
                "will happen. Your pre-embedded context will be refreshed."
            )

        if rate_action == RateLimitAction.INFORM:
            parts.append(f"Rate limit: {rate_limit_pct:.0f}%. Conserve when possible.")
        elif rate_action == RateLimitAction.CONSERVE:
            parts.append(f"Rate limit: {rate_limit_pct:.0f}%. CONSERVE — effort reduced.")
        elif rate_action == RateLimitAction.CRITICAL:
            parts.append(
                f"Rate limit: {rate_limit_pct:.0f}%. CRITICAL — finish current "
                "operation, no new work will be dispatched."
            )
        elif rate_action == RateLimitAction.STOP:
            parts.append(
                f"Rate limit: {rate_limit_pct:.0f}%. STOP — dispatch halted, "
                "waiting for rate limit rollover."
            )

        return "\n".join(parts)
