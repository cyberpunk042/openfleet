"""Default model promotion — config switch + monitoring (M-MU04).

Manages the lifecycle of promoting a candidate model to default.
Tracks pre/post promotion approval rates so the PO can verify
the new model performs at least as well in production.

Design doc requirement:
> Update fleet config to use Qwen3-8B as default.
> Update backend registry.
> hermes-3b as fallback.
> Monitor approval rates post-promotion.

The PO decides when to promote. This module provides the data
and the mechanism, not the decision.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fleet.core.shadow_routing import ShadowRouter
from typing import Optional


# ─── Promotion Record ─────────────────────────────────────────


@dataclass
class PromotionRecord:
    """A record of a model promotion event."""

    promoted_model: str
    previous_model: str
    promoted_at: float = 0.0
    promoted_by: str = "PO"              # Always PO — models don't self-promote
    reason: str = ""
    shadow_comparisons: int = 0          # How many shadow comparisons before promotion
    shadow_agreement_rate: float = 0.0   # Agreement rate at time of promotion
    pre_promotion_approval_rate: float = 0.0
    rollback: bool = False               # Was this promotion rolled back?
    rollback_reason: str = ""

    def __post_init__(self) -> None:
        if not self.promoted_at:
            self.promoted_at = time.time()

    def to_dict(self) -> dict:
        return {
            "promoted_model": self.promoted_model,
            "previous_model": self.previous_model,
            "promoted_at": self.promoted_at,
            "promoted_by": self.promoted_by,
            "reason": self.reason,
            "shadow_comparisons": self.shadow_comparisons,
            "shadow_agreement_rate": round(self.shadow_agreement_rate, 3),
            "pre_promotion_approval_rate": round(self.pre_promotion_approval_rate, 3),
            "rollback": self.rollback,
            "rollback_reason": self.rollback_reason,
        }


# ─── Approval Tracker ─────────────────────────────────────────


@dataclass
class ApprovalEntry:
    """A single approval/rejection data point."""

    model: str
    task_type: str
    approved: bool
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


class ApprovalTracker:
    """Tracks approval rates per model, pre and post promotion.

    Used to compare: is the new default performing as well
    as the old default did?
    """

    def __init__(self, max_entries: int = 500) -> None:
        self._entries: list[ApprovalEntry] = []
        self._max_entries = max_entries

    def record(self, entry: ApprovalEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def record_approval(
        self, model: str, task_type: str, approved: bool,
    ) -> None:
        self.record(ApprovalEntry(model=model, task_type=task_type, approved=approved))

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    def approval_rate(self, model: Optional[str] = None) -> float:
        """Overall approval rate, optionally filtered by model."""
        entries = self._entries
        if model:
            entries = [e for e in entries if e.model == model]
        if not entries:
            return 0.0
        return sum(1 for e in entries if e.approved) / len(entries)

    def approval_rate_by_task_type(
        self, model: Optional[str] = None,
    ) -> dict[str, float]:
        """Approval rate broken down by task type."""
        entries = self._entries
        if model:
            entries = [e for e in entries if e.model == model]

        groups: dict[str, list[ApprovalEntry]] = {}
        for e in entries:
            groups.setdefault(e.task_type, []).append(e)

        return {
            tt: round(sum(1 for e in ents if e.approved) / len(ents), 3)
            for tt, ents in groups.items()
        }

    def entries_since(self, timestamp: float) -> list[ApprovalEntry]:
        """Entries after a given timestamp (e.g., post-promotion)."""
        return [e for e in self._entries if e.timestamp > timestamp]

    def approval_rate_since(
        self, timestamp: float, model: Optional[str] = None,
    ) -> float:
        """Approval rate since a given timestamp."""
        entries = self.entries_since(timestamp)
        if model:
            entries = [e for e in entries if e.model == model]
        if not entries:
            return 0.0
        return sum(1 for e in entries if e.approved) / len(entries)


# ─── Model Promotion Manager ──────────────────────────────────


class ModelPromotionManager:
    """Manages the model promotion lifecycle.

    Tracks the current default model, records promotion events,
    and monitors post-promotion approval rates.
    """

    def __init__(
        self,
        current_default: str = "hermes-3b",
        fallback_model: str = "hermes-3b",
    ) -> None:
        self.current_default = current_default
        self.fallback_model = fallback_model
        self._promotions: list[PromotionRecord] = []
        self._tracker = ApprovalTracker()

    @property
    def tracker(self) -> ApprovalTracker:
        return self._tracker

    @property
    def promotion_history(self) -> list[PromotionRecord]:
        return list(self._promotions)

    @property
    def last_promotion(self) -> Optional[PromotionRecord]:
        return self._promotions[-1] if self._promotions else None

    def routing_model(self) -> str:
        """Return the model name to use for LocalAI routing.

        Callers pass this to route_task(localai_model=...) so the router
        always uses the promoted model (or fallback if rolled back).
        """
        return self.current_default

    def promote(
        self,
        new_model: str,
        reason: str = "",
        shadow_comparisons: int = 0,
        shadow_agreement_rate: float = 0.0,
    ) -> PromotionRecord:
        """Promote a new model to default.

        The previous default becomes the fallback.
        """
        pre_rate = self._tracker.approval_rate(self.current_default)

        record = PromotionRecord(
            promoted_model=new_model,
            previous_model=self.current_default,
            reason=reason,
            shadow_comparisons=shadow_comparisons,
            shadow_agreement_rate=shadow_agreement_rate,
            pre_promotion_approval_rate=pre_rate,
        )

        self.fallback_model = self.current_default
        self.current_default = new_model
        self._promotions.append(record)
        return record

    def promote_from_shadow(
        self,
        new_model: str,
        shadow: "ShadowRouter",
        reason: str = "",
    ) -> PromotionRecord:
        """Promote a model using shadow routing data.

        Convenience wrapper that extracts shadow stats and passes
        them to promote(). The PO still makes the decision to call this.
        """
        return self.promote(
            new_model=new_model,
            reason=reason or f"Shadow routing: {shadow.upgrade_worthy_rate:.0%} upgrade-worthy",
            shadow_comparisons=shadow.total_comparisons,
            shadow_agreement_rate=shadow.agreement_rate,
        )

    def rollback(self, reason: str = "") -> Optional[PromotionRecord]:
        """Roll back the last promotion. Previous model becomes default again."""
        if not self._promotions:
            return None

        last = self._promotions[-1]
        if last.rollback:
            return None  # Already rolled back

        last.rollback = True
        last.rollback_reason = reason

        self.current_default = last.previous_model
        self.fallback_model = last.promoted_model
        return last

    def record_approval(
        self, model: str, task_type: str, approved: bool,
    ) -> None:
        """Record an approval/rejection for monitoring."""
        self._tracker.record_approval(model, task_type, approved)

    def post_promotion_approval_rate(self) -> float:
        """Approval rate of the current default since its promotion."""
        if not self._promotions:
            return self._tracker.approval_rate(self.current_default)
        last = self._promotions[-1]
        if last.rollback:
            return 0.0
        return self._tracker.approval_rate_since(
            last.promoted_at, self.current_default,
        )

    def promotion_health(self) -> dict:
        """Check if the current promotion is healthy.

        Compares post-promotion approval rate against
        the pre-promotion baseline.
        """
        if not self._promotions:
            return {
                "status": "no_promotion",
                "current_default": self.current_default,
            }

        last = self._promotions[-1]
        if last.rollback:
            return {
                "status": "rolled_back",
                "current_default": self.current_default,
                "rollback_reason": last.rollback_reason,
            }

        post_rate = self.post_promotion_approval_rate()
        pre_rate = last.pre_promotion_approval_rate
        diff = post_rate - pre_rate if pre_rate > 0 else 0.0

        if post_rate >= pre_rate * 0.9:  # Within 10% of baseline
            status = "healthy"
        elif post_rate >= pre_rate * 0.7:  # Within 30%
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "current_default": self.current_default,
            "fallback_model": self.fallback_model,
            "pre_promotion_rate": round(pre_rate, 3),
            "post_promotion_rate": round(post_rate, 3),
            "rate_difference": round(diff, 3),
        }

    def summary(self) -> dict:
        """Full promotion manager summary."""
        return {
            "current_default": self.current_default,
            "fallback_model": self.fallback_model,
            "total_promotions": len(self._promotions),
            "total_rollbacks": sum(1 for p in self._promotions if p.rollback),
            "promotion_health": self.promotion_health(),
            "approval_rate_current": round(
                self._tracker.approval_rate(self.current_default), 3,
            ),
            "approval_by_task_type": self._tracker.approval_rate_by_task_type(
                self.current_default,
            ),
        }

    def format_report(self) -> str:
        """Format promotion status as markdown."""
        s = self.summary()
        health = s["promotion_health"]
        lines = [
            "## Model Promotion Status",
            "",
            f"**Current default:** {s['current_default']}",
            f"**Fallback:** {s['fallback_model']}",
            f"**Promotions:** {s['total_promotions']} "
            f"({s['total_rollbacks']} rolled back)",
            f"**Current approval rate:** {s['approval_rate_current']:.1%}",
            "",
        ]

        if health["status"] != "no_promotion":
            lines.append(f"### Promotion Health: {health['status'].upper()}")
            if "pre_promotion_rate" in health:
                lines.append(
                    f"- Pre-promotion: {health['pre_promotion_rate']:.1%}"
                )
                lines.append(
                    f"- Post-promotion: {health['post_promotion_rate']:.1%}"
                )
                lines.append(
                    f"- Difference: {health['rate_difference']:+.1%}"
                )
            lines.append("")

        if s["approval_by_task_type"]:
            lines.append("### Approval Rate by Task Type")
            for tt, rate in s["approval_by_task_type"].items():
                lines.append(f"- {tt}: {rate:.1%}")

        return "\n".join(lines)