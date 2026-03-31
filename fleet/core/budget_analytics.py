"""Budget analytics (M-BM06).

Tracks cost, quality, and efficiency per budget mode over time.
Answers the PO's key questions:
  - Which mode costs the most?
  - Do economic-mode tasks get rejected more?
  - What is the cost difference for the same task type across modes?
  - When should I switch modes?

Design doc requirement:
> Track cost per mode over time.
> Compare: same task type, different modes → cost difference.
> Measure quality impact: do economic-mode tasks get rejected more?
> Feed into PO decision-making about when to use which mode.
> Cross-ref: labor stamps provide the data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# ─── Budget Event ───────────────────────────────────────────────


@dataclass
class BudgetEvent:
    """A single task's budget data point for analytics."""

    task_id: str
    budget_mode: str                   # blitz/standard/economic/frugal/survival
    task_type: str = "task"            # task, story, bug, subtask, epic
    story_points: int = 0
    cost_usd: float = 0.0
    duration_seconds: int = 0
    backend: str = ""
    model: str = ""
    approved: Optional[bool] = None    # None = not yet reviewed
    challenge_passed: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "mode": self.budget_mode,
            "task_type": self.task_type,
            "story_points": self.story_points,
            "cost_usd": round(self.cost_usd, 4),
            "duration_seconds": self.duration_seconds,
            "backend": self.backend,
            "model": self.model,
            "approved": self.approved,
            "challenge_passed": self.challenge_passed,
        }


# ─── Per-Mode Metrics ───────────────────────────────────────────


@dataclass
class BudgetModeMetrics:
    """Aggregated metrics for a single budget mode."""

    mode: str
    total_tasks: int = 0
    total_cost_usd: float = 0.0
    total_duration_seconds: int = 0
    approved: int = 0
    rejected: int = 0
    challenge_passed: int = 0
    challenge_failed: int = 0
    backends_used: Counter = field(default_factory=Counter)
    models_used: Counter = field(default_factory=Counter)
    task_types: Counter = field(default_factory=Counter)

    @property
    def avg_cost_per_task(self) -> float:
        return self.total_cost_usd / self.total_tasks if self.total_tasks else 0.0

    @property
    def avg_duration_seconds(self) -> float:
        return self.total_duration_seconds / self.total_tasks if self.total_tasks else 0.0

    @property
    def approval_rate(self) -> float:
        total = self.approved + self.rejected
        return self.approved / total if total else 0.0

    @property
    def challenge_pass_rate(self) -> float:
        total = self.challenge_passed + self.challenge_failed
        return self.challenge_passed / total if total else 0.0

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "total_tasks": self.total_tasks,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "avg_cost_per_task": round(self.avg_cost_per_task, 4),
            "avg_duration_seconds": round(self.avg_duration_seconds, 1),
            "approved": self.approved,
            "rejected": self.rejected,
            "approval_rate": round(self.approval_rate, 3),
            "challenge_pass_rate": round(self.challenge_pass_rate, 3),
            "top_backend": (
                self.backends_used.most_common(1)[0][0]
                if self.backends_used else ""
            ),
            "top_model": (
                self.models_used.most_common(1)[0][0]
                if self.models_used else ""
            ),
        }


# ─── Mode Comparison ────────────────────────────────────────────


@dataclass
class ModeComparison:
    """Comparison of two modes for the same task type."""

    task_type: str
    mode_a: str
    mode_b: str
    avg_cost_a: float
    avg_cost_b: float
    approval_rate_a: float
    approval_rate_b: float
    count_a: int
    count_b: int

    @property
    def cost_difference_pct(self) -> float:
        """How much cheaper mode_b is compared to mode_a (positive = savings)."""
        if self.avg_cost_a == 0:
            return 0.0
        return ((self.avg_cost_a - self.avg_cost_b) / self.avg_cost_a) * 100

    @property
    def quality_difference(self) -> float:
        """Approval rate difference (mode_a - mode_b). Negative = mode_b is worse."""
        return self.approval_rate_a - self.approval_rate_b

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "mode_a": self.mode_a,
            "mode_b": self.mode_b,
            "avg_cost_a": round(self.avg_cost_a, 4),
            "avg_cost_b": round(self.avg_cost_b, 4),
            "cost_savings_pct": round(self.cost_difference_pct, 1),
            "approval_rate_a": round(self.approval_rate_a, 3),
            "approval_rate_b": round(self.approval_rate_b, 3),
            "quality_difference": round(self.quality_difference, 3),
            "count_a": self.count_a,
            "count_b": self.count_b,
        }


# ─── Budget Analytics Engine ────────────────────────────────────


class BudgetAnalytics:
    """Tracks and analyzes cost/quality across budget modes.

    Feed events as tasks complete. Query metrics for PO reporting,
    mode comparison, and budget mode decision-making.
    """

    def __init__(self, max_events: int = 500) -> None:
        self._events: list[BudgetEvent] = []
        self._max_events = max_events

    def record(self, event: BudgetEvent) -> None:
        """Record a budget event from a completed task."""
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def record_many(self, events: list[BudgetEvent]) -> None:
        for e in events:
            self.record(e)

    @property
    def total_events(self) -> int:
        return len(self._events)

    @property
    def total_cost_usd(self) -> float:
        return sum(e.cost_usd for e in self._events)

    # ─── Per-Mode Metrics ────────────────────────────────────────

    def mode_metrics(self, mode: str) -> BudgetModeMetrics:
        """Get aggregated metrics for a specific budget mode."""
        events = [e for e in self._events if e.budget_mode == mode]
        metrics = BudgetModeMetrics(mode=mode)

        for e in events:
            metrics.total_tasks += 1
            metrics.total_cost_usd += e.cost_usd
            metrics.total_duration_seconds += e.duration_seconds
            if e.backend:
                metrics.backends_used[e.backend] += 1
            if e.model:
                metrics.models_used[e.model] += 1
            metrics.task_types[e.task_type] += 1

            if e.approved is True:
                metrics.approved += 1
            elif e.approved is False:
                metrics.rejected += 1

            if e.challenge_passed is True:
                metrics.challenge_passed += 1
            elif e.challenge_passed is False:
                metrics.challenge_failed += 1

        return metrics

    def all_mode_metrics(self) -> list[BudgetModeMetrics]:
        """Get metrics for all modes, sorted by total cost descending."""
        modes = {e.budget_mode for e in self._events}
        metrics = [self.mode_metrics(m) for m in modes]
        metrics.sort(key=lambda m: m.total_cost_usd, reverse=True)
        return metrics

    # ─── Mode Comparison ─────────────────────────────────────────

    def compare_modes(
        self, mode_a: str, mode_b: str, task_type: Optional[str] = None,
    ) -> Optional[ModeComparison]:
        """Compare two modes for the same task type.

        If task_type is None, compares across all task types.
        Returns None if either mode has no data.
        """
        events_a = [
            e for e in self._events
            if e.budget_mode == mode_a
            and (task_type is None or e.task_type == task_type)
        ]
        events_b = [
            e for e in self._events
            if e.budget_mode == mode_b
            and (task_type is None or e.task_type == task_type)
        ]

        if not events_a or not events_b:
            return None

        avg_cost_a = sum(e.cost_usd for e in events_a) / len(events_a)
        avg_cost_b = sum(e.cost_usd for e in events_b) / len(events_b)

        approved_a = sum(1 for e in events_a if e.approved is True)
        reviewed_a = sum(1 for e in events_a if e.approved is not None)
        approved_b = sum(1 for e in events_b if e.approved is True)
        reviewed_b = sum(1 for e in events_b if e.approved is not None)

        return ModeComparison(
            task_type=task_type or "all",
            mode_a=mode_a,
            mode_b=mode_b,
            avg_cost_a=avg_cost_a,
            avg_cost_b=avg_cost_b,
            approval_rate_a=approved_a / reviewed_a if reviewed_a else 0.0,
            approval_rate_b=approved_b / reviewed_b if reviewed_b else 0.0,
            count_a=len(events_a),
            count_b=len(events_b),
        )

    # ─── Cost by Task Type ───────────────────────────────────────

    def cost_by_task_type(self) -> dict[str, float]:
        """Total cost grouped by task type."""
        costs: dict[str, float] = {}
        for e in self._events:
            costs[e.task_type] = costs.get(e.task_type, 0.0) + e.cost_usd
        return {k: round(v, 2) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    def cost_per_story_point(self) -> float:
        """Average cost per story point across all events."""
        sp_events = [e for e in self._events if e.story_points > 0]
        if not sp_events:
            return 0.0
        total_cost = sum(e.cost_usd for e in sp_events)
        total_sp = sum(e.story_points for e in sp_events)
        return total_cost / total_sp if total_sp else 0.0

    # ─── Summary ─────────────────────────────────────────────────

    def summary(self) -> dict:
        """Full budget analytics summary."""
        mode_metrics = self.all_mode_metrics()

        return {
            "total_events": self.total_events,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "cost_per_story_point": round(self.cost_per_story_point(), 4),
            "cost_by_task_type": self.cost_by_task_type(),
            "modes": [m.to_dict() for m in mode_metrics],
        }

    def format_report(self) -> str:
        """Format budget analytics as markdown."""
        s = self.summary()
        lines = [
            "## Budget Analytics Report",
            "",
            f"**Total tasks:** {s['total_events']}",
            f"**Total cost:** ${s['total_cost_usd']:.2f}",
            f"**Cost per SP:** ${s['cost_per_story_point']:.4f}",
            "",
        ]

        lines.append("### Cost by Task Type")
        for tt, cost in s["cost_by_task_type"].items():
            lines.append(f"- {tt}: ${cost:.2f}")
        lines.append("")

        lines.append("### Per-Mode Metrics")
        lines.append("| Mode | Tasks | Cost | Avg/Task | Approval | Challenge |")
        lines.append("|------|-------|------|----------|----------|-----------|")
        for m in s["modes"]:
            lines.append(
                f"| {m['mode']} | {m['total_tasks']} "
                f"| ${m['total_cost_usd']:.2f} "
                f"| ${m['avg_cost_per_task']:.4f} "
                f"| {m['approval_rate']:.1%} "
                f"| {m['challenge_pass_rate']:.1%} |"
            )

        return "\n".join(lines)