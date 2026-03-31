"""Challenge analytics (M-IV08).

Aggregates challenge outcomes to track quality patterns:

  - Per-agent pass rates: who produces work that survives challenge?
  - Per-tier pass rates: which confidence tiers need more scrutiny?
  - Average rounds to pass: how many iterations before work is clean?
  - Common findings: what do agents keep getting wrong?
  - Teaching signals: repeated failures → lessons for the teaching system

All analytics are computed from ChallengeRecord history, not stored
separately. The teaching system consumes these signals to generate
targeted lessons for agents that struggle with specific categories.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# ─── Challenge Event ─────────────────────────────────────────────


@dataclass
class ChallengeEvent:
    """A completed challenge event for analytics aggregation.

    Extracted from ChallengeRecord after a challenge completes.
    """

    task_id: str
    agent_name: str
    confidence_tier: str
    challenge_type: str              # automated, agent, cross-model, scenario
    passed: bool
    rounds_used: int
    findings_count: int
    finding_categories: list[str]    # Categories of findings
    finding_severities: list[str]    # Severities of findings

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent_name,
            "tier": self.confidence_tier,
            "type": self.challenge_type,
            "passed": self.passed,
            "rounds": self.rounds_used,
            "findings": self.findings_count,
            "categories": self.finding_categories,
            "severities": self.finding_severities,
        }


# ─── Analytics Aggregator ────────────────────────────────────────


class ChallengeAnalytics:
    """Aggregates challenge events and computes analytics.

    Maintains an in-memory buffer of events and provides
    computed metrics on demand.
    """

    def __init__(self, max_events: int = 500) -> None:
        self._events: list[ChallengeEvent] = []
        self._max_events = max_events

    @property
    def total_events(self) -> int:
        return len(self._events)

    def record(self, event: ChallengeEvent) -> None:
        """Record a challenge event."""
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def record_many(self, events: list[ChallengeEvent]) -> None:
        """Record multiple events."""
        for e in events:
            self.record(e)

    # ─── Per-Agent Metrics ────────────────────────────────────

    def agent_pass_rate(self, agent_name: str) -> AgentMetrics:
        """Compute pass rate for a specific agent."""
        events = [e for e in self._events if e.agent_name == agent_name]
        return _compute_agent_metrics(agent_name, events)

    def all_agent_metrics(self) -> list[AgentMetrics]:
        """Compute pass rates for all agents."""
        agents: dict[str, list[ChallengeEvent]] = {}
        for e in self._events:
            agents.setdefault(e.agent_name, []).append(e)

        return [
            _compute_agent_metrics(name, events)
            for name, events in sorted(agents.items())
        ]

    # ─── Per-Tier Metrics ─────────────────────────────────────

    def tier_pass_rate(self, tier: str) -> TierMetrics:
        """Compute pass rate for a specific confidence tier."""
        events = [e for e in self._events if e.confidence_tier == tier]
        return _compute_tier_metrics(tier, events)

    def all_tier_metrics(self) -> list[TierMetrics]:
        """Compute pass rates for all tiers."""
        tiers: dict[str, list[ChallengeEvent]] = {}
        for e in self._events:
            tiers.setdefault(e.confidence_tier, []).append(e)

        return [
            _compute_tier_metrics(tier, events)
            for tier, events in sorted(tiers.items())
        ]

    # ─── Common Findings ──────────────────────────────────────

    def common_finding_categories(self, top_n: int = 5) -> list[tuple[str, int]]:
        """Most common finding categories across all events."""
        counter: Counter[str] = Counter()
        for e in self._events:
            counter.update(e.finding_categories)
        return counter.most_common(top_n)

    def common_finding_severities(self) -> dict[str, int]:
        """Distribution of finding severities."""
        counter: Counter[str] = Counter()
        for e in self._events:
            counter.update(e.finding_severities)
        return dict(counter)

    # ─── Teaching Signals ─────────────────────────────────────

    def teaching_signals(self, min_failures: int = 3) -> list[TeachingSignal]:
        """Identify agents with repeated failures in the same category.

        These signals feed into the teaching system to generate
        targeted lessons.

        Args:
            min_failures: Minimum repeated failures to trigger a signal.

        Returns:
            List of TeachingSignal objects.
        """
        # Track per-agent category failures
        agent_failures: dict[str, Counter[str]] = {}
        for e in self._events:
            if not e.passed:
                counter = agent_failures.setdefault(e.agent_name, Counter())
                counter.update(e.finding_categories)

        signals: list[TeachingSignal] = []
        for agent, categories in agent_failures.items():
            for category, count in categories.items():
                if count >= min_failures:
                    signals.append(TeachingSignal(
                        agent_name=agent,
                        category=category,
                        failure_count=count,
                        suggestion=_suggest_lesson(category, count),
                    ))

        return sorted(signals, key=lambda s: -s.failure_count)

    # ─── Summary ──────────────────────────────────────────────

    def summary(self) -> dict:
        """Complete analytics summary."""
        if not self._events:
            return {
                "total_challenges": 0,
                "overall_pass_rate": 0.0,
                "avg_rounds": 0.0,
            }

        passed = sum(1 for e in self._events if e.passed)
        total_rounds = sum(e.rounds_used for e in self._events)

        return {
            "total_challenges": len(self._events),
            "overall_pass_rate": passed / len(self._events) if self._events else 0.0,
            "avg_rounds": total_rounds / len(self._events) if self._events else 0.0,
            "total_findings": sum(e.findings_count for e in self._events),
            "agents": [m.to_dict() for m in self.all_agent_metrics()],
            "tiers": [m.to_dict() for m in self.all_tier_metrics()],
            "common_categories": self.common_finding_categories(),
            "teaching_signals": [s.to_dict() for s in self.teaching_signals()],
        }


# ─── Metric Containers ──────────────────────────────────────────


@dataclass
class AgentMetrics:
    """Challenge metrics for a single agent."""

    agent_name: str
    total_challenges: int
    passed: int
    failed: int
    pass_rate: float
    avg_rounds: float
    total_findings: int
    top_categories: list[tuple[str, int]]

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "total": self.total_challenges,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 2),
            "avg_rounds": round(self.avg_rounds, 2),
            "findings": self.total_findings,
            "top_categories": self.top_categories,
        }


@dataclass
class TierMetrics:
    """Challenge metrics for a confidence tier."""

    tier: str
    total_challenges: int
    passed: int
    failed: int
    pass_rate: float
    avg_rounds: float

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "total": self.total_challenges,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 2),
            "avg_rounds": round(self.avg_rounds, 2),
        }


@dataclass
class TeachingSignal:
    """Signal for the teaching system — agent needs lesson."""

    agent_name: str
    category: str
    failure_count: int
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "category": self.category,
            "failures": self.failure_count,
            "suggestion": self.suggestion,
        }


# ─── Internal Helpers ────────────────────────────────────────────


def _compute_agent_metrics(
    agent_name: str,
    events: list[ChallengeEvent],
) -> AgentMetrics:
    if not events:
        return AgentMetrics(
            agent_name=agent_name,
            total_challenges=0, passed=0, failed=0,
            pass_rate=0.0, avg_rounds=0.0,
            total_findings=0, top_categories=[],
        )

    passed = sum(1 for e in events if e.passed)
    failed = len(events) - passed
    total_rounds = sum(e.rounds_used for e in events)
    total_findings = sum(e.findings_count for e in events)

    cats: Counter[str] = Counter()
    for e in events:
        cats.update(e.finding_categories)

    return AgentMetrics(
        agent_name=agent_name,
        total_challenges=len(events),
        passed=passed,
        failed=failed,
        pass_rate=passed / len(events),
        avg_rounds=total_rounds / len(events),
        total_findings=total_findings,
        top_categories=cats.most_common(3),
    )


def _compute_tier_metrics(
    tier: str,
    events: list[ChallengeEvent],
) -> TierMetrics:
    if not events:
        return TierMetrics(
            tier=tier,
            total_challenges=0, passed=0, failed=0,
            pass_rate=0.0, avg_rounds=0.0,
        )

    passed = sum(1 for e in events if e.passed)
    total_rounds = sum(e.rounds_used for e in events)

    return TierMetrics(
        tier=tier,
        total_challenges=len(events),
        passed=passed,
        failed=len(events) - passed,
        pass_rate=passed / len(events),
        avg_rounds=total_rounds / len(events),
    )


def _suggest_lesson(category: str, failure_count: int) -> str:
    """Generate a teaching suggestion based on failure pattern."""
    suggestions = {
        "edge_case": "Review boundary value analysis and null handling patterns",
        "regression": "Improve test coverage before submitting — run full suite",
        "security": "Study OWASP top 10 and input validation patterns",
        "logic_error": "Practice code review and trace execution paths manually",
        "requirement_gap": "Re-read requirements verbatim before implementing",
        "test_gap": "Add tests for every code path including error cases",
        "performance": "Profile code and check algorithmic complexity",
        "concurrency": "Study async patterns, race conditions, and lock discipline",
        "architecture": "Review import structure and module dependencies",
        "error_handling": "Use specific exception types, never bare except",
    }
    base = suggestions.get(category, f"Review {category} patterns and best practices")
    return f"{base} ({failure_count} failures detected)"