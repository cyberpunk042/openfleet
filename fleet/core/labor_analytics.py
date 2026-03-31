"""Labor analytics (M-LA07).

Aggregates labor stamps across tasks to provide cost and quality
insights per agent, per model, per confidence tier, and per backend.

Design doc requirement (verbatim):
> Aggregate labor stamps across tasks: cost per agent, cost per model,
> cost per confidence tier, approval rate per tier.
> Surface in fleet-ops monitoring.
> Feed into budget mode decisions.

The analytics engine consumes LaborStamp objects (from completed tasks)
and produces aggregated metrics that the PO and fleet-ops can use for
decision-making: which agents cost the most, which models produce the
best approval rates, whether trainee-tier work is ready for promotion.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.labor_stamp import LaborStamp


# ─── Per-Agent Cost Metrics ──────────────────────────────────────


@dataclass
class AgentCostMetrics:
    """Aggregated cost and quality metrics for a single agent."""

    agent_name: str
    total_tasks: int = 0
    total_cost_usd: float = 0.0
    total_duration_seconds: int = 0
    total_tokens: int = 0
    approved: int = 0
    rejected: int = 0
    models_used: Counter = field(default_factory=Counter)
    backends_used: Counter = field(default_factory=Counter)

    @property
    def avg_cost_per_task(self) -> float:
        return self.total_cost_usd / self.total_tasks if self.total_tasks else 0.0

    @property
    def avg_duration_seconds(self) -> float:
        return self.total_duration_seconds / self.total_tasks if self.total_tasks else 0.0

    @property
    def approval_rate(self) -> float:
        total_reviewed = self.approved + self.rejected
        return self.approved / total_reviewed if total_reviewed else 0.0

    @property
    def primary_model(self) -> str:
        return self.models_used.most_common(1)[0][0] if self.models_used else ""

    @property
    def primary_backend(self) -> str:
        return self.backends_used.most_common(1)[0][0] if self.backends_used else ""

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "total_tasks": self.total_tasks,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "avg_cost_per_task": round(self.avg_cost_per_task, 4),
            "avg_duration_seconds": round(self.avg_duration_seconds, 1),
            "total_tokens": self.total_tokens,
            "approved": self.approved,
            "rejected": self.rejected,
            "approval_rate": round(self.approval_rate, 3),
            "primary_model": self.primary_model,
            "primary_backend": self.primary_backend,
        }


# ─── Per-Model Cost Metrics ─────────────────────────────────────


@dataclass
class ModelCostMetrics:
    """Aggregated cost and quality metrics for a specific model."""

    model: str
    total_tasks: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    approved: int = 0
    rejected: int = 0
    avg_challenge_rounds: float = 0.0
    _challenge_rounds_sum: int = 0

    @property
    def avg_cost_per_task(self) -> float:
        return self.total_cost_usd / self.total_tasks if self.total_tasks else 0.0

    @property
    def approval_rate(self) -> float:
        total_reviewed = self.approved + self.rejected
        return self.approved / total_reviewed if total_reviewed else 0.0

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "total_tasks": self.total_tasks,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "avg_cost_per_task": round(self.avg_cost_per_task, 4),
            "total_tokens": self.total_tokens,
            "approved": self.approved,
            "rejected": self.rejected,
            "approval_rate": round(self.approval_rate, 3),
            "avg_challenge_rounds": round(self.avg_challenge_rounds, 2),
        }


# ─── Per-Tier Metrics ───────────────────────────────────────────


@dataclass
class TierCostMetrics:
    """Aggregated cost and quality metrics for a confidence tier."""

    tier: str
    total_tasks: int = 0
    total_cost_usd: float = 0.0
    approved: int = 0
    rejected: int = 0
    challenge_required: int = 0
    challenge_passed: int = 0

    @property
    def avg_cost_per_task(self) -> float:
        return self.total_cost_usd / self.total_tasks if self.total_tasks else 0.0

    @property
    def approval_rate(self) -> float:
        total_reviewed = self.approved + self.rejected
        return self.approved / total_reviewed if total_reviewed else 0.0

    @property
    def challenge_pass_rate(self) -> float:
        return (
            self.challenge_passed / self.challenge_required
            if self.challenge_required
            else 0.0
        )

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "total_tasks": self.total_tasks,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "avg_cost_per_task": round(self.avg_cost_per_task, 4),
            "approved": self.approved,
            "rejected": self.rejected,
            "approval_rate": round(self.approval_rate, 3),
            "challenge_required": self.challenge_required,
            "challenge_passed": self.challenge_passed,
            "challenge_pass_rate": round(self.challenge_pass_rate, 3),
        }


# ─── Labor Analytics Engine ─────────────────────────────────────


class LaborAnalytics:
    """Aggregates labor stamps for fleet-wide cost and quality analytics.

    Feed stamps as tasks complete. Query aggregated metrics at any time
    for fleet-ops monitoring, budget mode decisions, and PO reporting.
    """

    def __init__(self, max_stamps: int = 500) -> None:
        self._stamps: list[LaborStamp] = []
        self._max_stamps = max_stamps
        # Approval tracking is separate — stamps don't carry approval status
        self._approvals: dict[str, bool] = {}  # task_key → approved

    def record(self, stamp: LaborStamp) -> None:
        """Record a labor stamp from a completed task."""
        self._stamps.append(stamp)
        if len(self._stamps) > self._max_stamps:
            self._stamps = self._stamps[-self._max_stamps:]

    def record_many(self, stamps: list[LaborStamp]) -> None:
        """Record multiple stamps at once."""
        for s in stamps:
            self.record(s)

    def record_approval(
        self, agent_name: str, task_id: str, approved: bool
    ) -> None:
        """Record an approval/rejection for a task.

        Keyed by agent_name:task_id so we can match approvals to stamps.
        """
        self._approvals[f"{agent_name}:{task_id}"] = approved

    @property
    def total_stamps(self) -> int:
        return len(self._stamps)

    @property
    def total_cost_usd(self) -> float:
        return sum(s.estimated_cost_usd for s in self._stamps)

    # ─── Per-Agent Metrics ───────────────────────────────────────

    def agent_metrics(self, agent_name: str) -> AgentCostMetrics:
        """Get aggregated metrics for a specific agent."""
        stamps = [s for s in self._stamps if s.agent_name == agent_name]
        metrics = AgentCostMetrics(agent_name=agent_name)

        for s in stamps:
            metrics.total_tasks += 1
            metrics.total_cost_usd += s.estimated_cost_usd
            metrics.total_duration_seconds += s.duration_seconds
            metrics.total_tokens += s.estimated_tokens
            metrics.models_used[s.model] += 1
            metrics.backends_used[s.backend] += 1

            key = f"{agent_name}:{s.timestamp}"
            if key in self._approvals:
                if self._approvals[key]:
                    metrics.approved += 1
                else:
                    metrics.rejected += 1

        return metrics

    def all_agent_metrics(self) -> list[AgentCostMetrics]:
        """Get metrics for all agents, sorted by total cost descending."""
        agents = {s.agent_name for s in self._stamps}
        metrics = [self.agent_metrics(a) for a in agents]
        metrics.sort(key=lambda m: m.total_cost_usd, reverse=True)
        return metrics

    # ─── Per-Model Metrics ───────────────────────────────────────

    def model_metrics(self, model: str) -> ModelCostMetrics:
        """Get aggregated metrics for a specific model."""
        stamps = [s for s in self._stamps if s.model == model]
        metrics = ModelCostMetrics(model=model)

        for s in stamps:
            metrics.total_tasks += 1
            metrics.total_cost_usd += s.estimated_cost_usd
            metrics.total_tokens += s.estimated_tokens
            metrics._challenge_rounds_sum += s.challenge_rounds_survived

            key = f"{s.agent_name}:{s.timestamp}"
            if key in self._approvals:
                if self._approvals[key]:
                    metrics.approved += 1
                else:
                    metrics.rejected += 1

        if metrics.total_tasks:
            metrics.avg_challenge_rounds = (
                metrics._challenge_rounds_sum / metrics.total_tasks
            )

        return metrics

    def all_model_metrics(self) -> list[ModelCostMetrics]:
        """Get metrics for all models, sorted by total cost descending."""
        models = {s.model for s in self._stamps if s.model}
        metrics = [self.model_metrics(m) for m in models]
        metrics.sort(key=lambda m: m.total_cost_usd, reverse=True)
        return metrics

    # ─── Per-Tier Metrics ────────────────────────────────────────

    def tier_metrics(self, tier: str) -> TierCostMetrics:
        """Get aggregated metrics for a confidence tier."""
        stamps = [s for s in self._stamps if s.confidence_tier == tier]
        metrics = TierCostMetrics(tier=tier)

        for s in stamps:
            metrics.total_tasks += 1
            metrics.total_cost_usd += s.estimated_cost_usd

            if s.confidence_tier in ("trainee", "community", "hybrid"):
                metrics.challenge_required += 1
                if s.challenge_rounds_survived > 0:
                    metrics.challenge_passed += 1

            key = f"{s.agent_name}:{s.timestamp}"
            if key in self._approvals:
                if self._approvals[key]:
                    metrics.approved += 1
                else:
                    metrics.rejected += 1

        return metrics

    def all_tier_metrics(self) -> list[TierCostMetrics]:
        """Get metrics for all tiers."""
        tiers = {s.confidence_tier for s in self._stamps if s.confidence_tier}
        metrics = [self.tier_metrics(t) for t in tiers]
        metrics.sort(key=lambda m: m.total_tasks, reverse=True)
        return metrics

    # ─── Cost Breakdown ──────────────────────────────────────────

    def cost_by_backend(self) -> dict[str, float]:
        """Total cost grouped by backend."""
        costs: dict[str, float] = {}
        for s in self._stamps:
            costs[s.backend] = costs.get(s.backend, 0.0) + s.estimated_cost_usd
        return {k: round(v, 2) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    def cost_by_budget_mode(self) -> dict[str, float]:
        """Total cost grouped by budget mode."""
        costs: dict[str, float] = {}
        for s in self._stamps:
            mode = s.budget_mode or "unknown"
            costs[mode] = costs.get(mode, 0.0) + s.estimated_cost_usd
        return {k: round(v, 2) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    # ─── Summary ─────────────────────────────────────────────────

    def summary(self) -> dict:
        """Full analytics summary for fleet-ops and PO reporting."""
        agent_metrics = self.all_agent_metrics()
        model_metrics = self.all_model_metrics()
        tier_metrics = self.all_tier_metrics()

        total_approved = sum(m.approved for m in agent_metrics)
        total_rejected = sum(m.rejected for m in agent_metrics)
        total_reviewed = total_approved + total_rejected

        return {
            "total_stamps": self.total_stamps,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "overall_approval_rate": (
                round(total_approved / total_reviewed, 3) if total_reviewed else 0.0
            ),
            "cost_by_backend": self.cost_by_backend(),
            "cost_by_budget_mode": self.cost_by_budget_mode(),
            "agents": [m.to_dict() for m in agent_metrics],
            "models": [m.to_dict() for m in model_metrics],
            "tiers": [m.to_dict() for m in tier_metrics],
        }

    def format_report(self) -> str:
        """Format analytics as a markdown report for fleet-ops."""
        s = self.summary()
        lines = [
            "## Labor Analytics Report",
            "",
            f"**Total tasks:** {s['total_stamps']}",
            f"**Total cost:** ${s['total_cost_usd']:.2f}",
            f"**Approval rate:** {s['overall_approval_rate']:.1%}",
            "",
        ]

        # Cost by backend
        lines.append("### Cost by Backend")
        for backend, cost in s["cost_by_backend"].items():
            lines.append(f"- {backend}: ${cost:.2f}")
        lines.append("")

        # Cost by budget mode
        lines.append("### Cost by Budget Mode")
        for mode, cost in s["cost_by_budget_mode"].items():
            lines.append(f"- {mode}: ${cost:.2f}")
        lines.append("")

        # Per-agent
        lines.append("### Per-Agent Metrics")
        lines.append("| Agent | Tasks | Cost | Avg/Task | Approval |")
        lines.append("|-------|-------|------|----------|----------|")
        for m in s["agents"]:
            lines.append(
                f"| {m['agent']} | {m['total_tasks']} "
                f"| ${m['total_cost_usd']:.2f} "
                f"| ${m['avg_cost_per_task']:.4f} "
                f"| {m['approval_rate']:.1%} |"
            )
        lines.append("")

        # Per-model
        lines.append("### Per-Model Metrics")
        lines.append("| Model | Tasks | Cost | Approval |")
        lines.append("|-------|-------|------|----------|")
        for m in s["models"]:
            lines.append(
                f"| {m['model']} | {m['total_tasks']} "
                f"| ${m['total_cost_usd']:.2f} "
                f"| {m['approval_rate']:.1%} |"
            )
        lines.append("")

        # Per-tier
        lines.append("### Per-Tier Metrics")
        lines.append("| Tier | Tasks | Cost | Approval | Challenge Pass |")
        lines.append("|------|-------|------|----------|----------------|")
        for m in s["tiers"]:
            lines.append(
                f"| {m['tier']} | {m['total_tasks']} "
                f"| ${m['total_cost_usd']:.2f} "
                f"| {m['approval_rate']:.1%} "
                f"| {m['challenge_pass_rate']:.1%} |"
            )

        return "\n".join(lines)