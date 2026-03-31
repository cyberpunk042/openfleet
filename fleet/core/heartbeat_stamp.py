"""Heartbeat labor stamps (M-LA08).

Even heartbeats get minimal labor stamps so the fleet can track
heartbeat cost trends and detect when heartbeats are too expensive.

Design doc requirement:
> Even heartbeats get minimal labor stamps (agent, model, cost, duration).
> Track heartbeat cost trends — detect when heartbeats are too expensive.
> Cross-ref: catastrophic drain prevention.

The March 2026 catastrophe was largely driven by heartbeat sessions
consuming Claude tokens. Heartbeat stamps provide the data to detect
this pattern early and trigger automatic response.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.labor_stamp import LaborStamp


# ─── Heartbeat Stamp ────────────────────────────────────────────


def create_heartbeat_stamp(
    agent_name: str,
    backend: str = "claude-code",
    model: str = "sonnet",
    duration_seconds: int = 0,
    estimated_tokens: int = 0,
    estimated_cost_usd: float = 0.0,
    budget_mode: str = "standard",
    void: bool = False,
) -> LaborStamp:
    """Create a minimal labor stamp for a heartbeat session.

    Heartbeats are not full tasks — they just check if the agent
    has work. But they still consume tokens and cost money, so they
    must be tracked for cost trend analysis.

    Args:
        agent_name: Agent that ran the heartbeat.
        backend: Backend used (should be localai in the target state).
        model: Model used for the heartbeat.
        duration_seconds: Wall-clock time for the heartbeat.
        estimated_tokens: Approximate tokens consumed.
        estimated_cost_usd: Estimated cost in USD.
        budget_mode: Active budget mode during the heartbeat.
        void: Whether the heartbeat produced no useful work.
    """
    return LaborStamp(
        agent_name=agent_name,
        agent_role="heartbeat",
        backend=backend,
        model=model,
        effort="low",
        skills_used=["heartbeat"],
        tools_called=["fleet_read_context"],
        session_type="fresh",
        duration_seconds=duration_seconds,
        estimated_tokens=estimated_tokens,
        estimated_cost_usd=estimated_cost_usd,
        budget_mode=budget_mode,
        iteration=1,
    )


# ─── Heartbeat Cost Tracker ─────────────────────────────────────


@dataclass
class HeartbeatCostEntry:
    """A single heartbeat cost data point."""

    agent_name: str
    cost_usd: float
    duration_seconds: int
    backend: str
    model: str
    void: bool
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


class HeartbeatCostTracker:
    """Tracks heartbeat costs over time and detects anomalies.

    The March 2026 catastrophe was driven by heartbeat sessions
    costing ~$0.15 each at 10+/minute. This tracker detects
    when heartbeat costs are abnormally high relative to baseline.
    """

    def __init__(
        self,
        max_entries: int = 200,
        cost_threshold_usd: float = 0.10,
        rate_threshold_per_hour: int = 30,
    ) -> None:
        self._entries: list[HeartbeatCostEntry] = []
        self._max_entries = max_entries
        self._cost_threshold = cost_threshold_usd
        self._rate_threshold = rate_threshold_per_hour

    def record(self, entry: HeartbeatCostEntry) -> None:
        """Record a heartbeat cost entry."""
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def record_from_stamp(self, stamp: LaborStamp, void: bool = False) -> None:
        """Record from a heartbeat LaborStamp."""
        self.record(HeartbeatCostEntry(
            agent_name=stamp.agent_name,
            cost_usd=stamp.estimated_cost_usd,
            duration_seconds=stamp.duration_seconds,
            backend=stamp.backend,
            model=stamp.model,
            void=void,
        ))

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    @property
    def total_cost_usd(self) -> float:
        return sum(e.cost_usd for e in self._entries)

    @property
    def avg_cost_per_heartbeat(self) -> float:
        return self.total_cost_usd / len(self._entries) if self._entries else 0.0

    @property
    def void_rate(self) -> float:
        if not self._entries:
            return 0.0
        void_count = sum(1 for e in self._entries if e.void)
        return void_count / len(self._entries)

    def entries_last_hour(self) -> list[HeartbeatCostEntry]:
        """Get entries from the last hour."""
        cutoff = time.time() - 3600
        return [e for e in self._entries if e.timestamp > cutoff]

    def cost_last_hour(self) -> float:
        """Total heartbeat cost in the last hour."""
        return sum(e.cost_usd for e in self.entries_last_hour())

    def rate_last_hour(self) -> int:
        """Number of heartbeats in the last hour."""
        return len(self.entries_last_hour())

    # ─── Anomaly Detection ───────────────────────────────────────

    def is_cost_anomaly(self) -> bool:
        """Whether average heartbeat cost exceeds the threshold.

        Default threshold: $0.10 per heartbeat. Heartbeats should
        cost $0 when routed to LocalAI, or ~$0.01-0.03 via Claude
        sonnet with low effort. If they cost $0.10+, something is
        wrong (wrong model, too much context, unnecessary tools).
        """
        return self.avg_cost_per_heartbeat > self._cost_threshold

    def is_rate_anomaly(self) -> bool:
        """Whether heartbeat rate exceeds the threshold.

        Default threshold: 30/hour. Normal operation: 10 agents
        with 30-minute heartbeats = 20/hour. If we see 30+,
        heartbeats are too frequent (gateway restart, stuck agent).
        """
        return self.rate_last_hour() > self._rate_threshold

    def check_anomalies(self) -> list[str]:
        """Check for all heartbeat anomalies.

        Returns list of anomaly descriptions (empty = no anomalies).
        """
        anomalies: list[str] = []

        if self.is_cost_anomaly():
            anomalies.append(
                f"heartbeat cost anomaly: avg ${self.avg_cost_per_heartbeat:.4f}/heartbeat "
                f"(threshold: ${self._cost_threshold:.2f})"
            )

        if self.is_rate_anomaly():
            anomalies.append(
                f"heartbeat rate anomaly: {self.rate_last_hour()}/hour "
                f"(threshold: {self._rate_threshold}/hour)"
            )

        if self.void_rate > 0.8 and self.total_entries >= 5:
            anomalies.append(
                f"heartbeat void rate: {self.void_rate:.0%} "
                f"(most heartbeats producing no useful work)"
            )

        return anomalies

    # ─── Per-Agent Breakdown ─────────────────────────────────────

    def cost_by_agent(self) -> dict[str, float]:
        """Total heartbeat cost per agent."""
        costs: dict[str, float] = {}
        for e in self._entries:
            costs[e.agent_name] = costs.get(e.agent_name, 0.0) + e.cost_usd
        return {k: round(v, 4) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    def rate_by_agent(self) -> dict[str, int]:
        """Heartbeat count per agent."""
        counts: dict[str, int] = {}
        for e in self._entries:
            counts[e.agent_name] = counts.get(e.agent_name, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def cost_by_backend(self) -> dict[str, float]:
        """Total heartbeat cost per backend."""
        costs: dict[str, float] = {}
        for e in self._entries:
            costs[e.backend] = costs.get(e.backend, 0.0) + e.cost_usd
        return {k: round(v, 4) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    # ─── Summary ─────────────────────────────────────────────────

    def summary(self) -> dict:
        """Heartbeat cost summary for fleet-ops."""
        return {
            "total_heartbeats": self.total_entries,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_cost_per_heartbeat": round(self.avg_cost_per_heartbeat, 4),
            "void_rate": round(self.void_rate, 3),
            "cost_last_hour": round(self.cost_last_hour(), 4),
            "rate_last_hour": self.rate_last_hour(),
            "anomalies": self.check_anomalies(),
            "cost_by_agent": self.cost_by_agent(),
            "cost_by_backend": self.cost_by_backend(),
        }