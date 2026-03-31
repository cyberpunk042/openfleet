"""Confidence tier progression tracking (M-MU07).

Tracks how models earn trust through observed performance.
Models start as trainees and progress through tiers based on
approval rates per task type. The PO decides when to promote.

Design doc requirement:
> Track approval rates per model per task type.
> Dashboard: model performance over time.
> PO decision interface: promote/demote model tier.
> Cross-ref: labor attribution provides the data.

Tier progression:
  trainee            — New/unvalidated model, all work needs extra review
  trainee-validated  — Passes X% of challenges, earning trust
  standard           — PO-approved for specific task types
  expert             — Full trust (reserved for Claude opus)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# ─── Constants ─────────────────────────────────────────────────

VALID_TIERS = ("trainee", "trainee-validated", "standard", "expert")

# Thresholds for automatic readiness signals (PO still decides)
VALIDATION_THRESHOLD = 0.7    # 70% approval → eligible for trainee-validated
STANDARD_THRESHOLD = 0.85     # 85% approval → eligible for standard
MIN_SAMPLES = 10              # Minimum samples before tier eligibility


# ─── Performance Record ───────────────────────────────────────


@dataclass
class PerformanceRecord:
    """A single performance data point for a model."""

    model: str
    task_type: str
    approved: bool
    challenge_passed: bool = False
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


# ─── Model Tier State ─────────────────────────────────────────


@dataclass
class ModelTierState:
    """Current tier state for a model, with per-task-type breakdown."""

    model: str
    current_tier: str = "trainee"
    tier_overrides: dict[str, str] = field(default_factory=dict)
    promoted_at: float = 0.0
    promoted_by: str = ""

    def effective_tier(self, task_type: Optional[str] = None) -> str:
        """Get the effective tier for a task type.

        Task-type-specific overrides take precedence.
        """
        if task_type and task_type in self.tier_overrides:
            return self.tier_overrides[task_type]
        return self.current_tier

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "current_tier": self.current_tier,
            "tier_overrides": dict(self.tier_overrides),
            "promoted_at": self.promoted_at,
            "promoted_by": self.promoted_by,
        }


# ─── Tier Progression Tracker ─────────────────────────────────


class TierProgressionTracker:
    """Tracks model performance and tier progression over time.

    Records approval/challenge results per model per task type.
    Computes readiness signals for tier promotion.
    The PO decides — this module provides data, not decisions.
    """

    def __init__(self, max_records: int = 1000) -> None:
        self._records: list[PerformanceRecord] = []
        self._max_records = max_records
        self._tiers: dict[str, ModelTierState] = {}

    def _ensure_tier_state(self, model: str) -> ModelTierState:
        if model not in self._tiers:
            self._tiers[model] = ModelTierState(model=model)
        return self._tiers[model]

    # ─── Recording ──────────────────────────────────────────────

    def record(self, rec: PerformanceRecord) -> None:
        """Record a performance data point."""
        self._records.append(rec)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        self._ensure_tier_state(rec.model)

    def record_approval(
        self,
        model: str,
        task_type: str,
        approved: bool,
        challenge_passed: bool = False,
    ) -> None:
        self.record(PerformanceRecord(
            model=model, task_type=task_type,
            approved=approved, challenge_passed=challenge_passed,
        ))

    @property
    def total_records(self) -> int:
        return len(self._records)

    # ─── Per-Model Metrics ──────────────────────────────────────

    def _model_records(self, model: str) -> list[PerformanceRecord]:
        return [r for r in self._records if r.model == model]

    def _model_task_records(
        self, model: str, task_type: str,
    ) -> list[PerformanceRecord]:
        return [
            r for r in self._records
            if r.model == model and r.task_type == task_type
        ]

    def approval_rate(
        self, model: str, task_type: Optional[str] = None,
    ) -> float:
        """Approval rate for a model, optionally by task type."""
        records = (
            self._model_task_records(model, task_type)
            if task_type
            else self._model_records(model)
        )
        if not records:
            return 0.0
        return sum(1 for r in records if r.approved) / len(records)

    def challenge_pass_rate(
        self, model: str, task_type: Optional[str] = None,
    ) -> float:
        """Challenge pass rate for a model."""
        records = (
            self._model_task_records(model, task_type)
            if task_type
            else self._model_records(model)
        )
        challenged = [r for r in records if r.challenge_passed is not None]
        if not challenged:
            return 0.0
        return sum(1 for r in challenged if r.challenge_passed) / len(challenged)

    def sample_count(
        self, model: str, task_type: Optional[str] = None,
    ) -> int:
        """Number of samples for a model."""
        if task_type:
            return len(self._model_task_records(model, task_type))
        return len(self._model_records(model))

    def task_types_for_model(self, model: str) -> list[str]:
        """All task types a model has been evaluated on."""
        return list({r.task_type for r in self._model_records(model)})

    # ─── Tier Management ────────────────────────────────────────

    def get_tier(self, model: str) -> str:
        """Get the current tier for a model."""
        state = self._tiers.get(model)
        return state.current_tier if state else "trainee"

    def get_effective_tier(
        self, model: str, task_type: Optional[str] = None,
    ) -> str:
        """Get the effective tier for a model on a task type."""
        state = self._tiers.get(model)
        if not state:
            return "trainee"
        return state.effective_tier(task_type)

    def set_tier(
        self, model: str, tier: str, promoted_by: str = "PO",
    ) -> ModelTierState:
        """Set the overall tier for a model. PO decision."""
        if tier not in VALID_TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {VALID_TIERS}")
        state = self._ensure_tier_state(model)
        state.current_tier = tier
        state.promoted_at = time.time()
        state.promoted_by = promoted_by
        return state

    def set_task_tier(
        self, model: str, task_type: str, tier: str,
        promoted_by: str = "PO",
    ) -> ModelTierState:
        """Set a per-task-type tier override. PO decision."""
        if tier not in VALID_TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {VALID_TIERS}")
        state = self._ensure_tier_state(model)
        state.tier_overrides[task_type] = tier
        state.promoted_at = time.time()
        state.promoted_by = promoted_by
        return state

    def clear_task_tier(self, model: str, task_type: str) -> None:
        """Remove a per-task-type tier override."""
        state = self._tiers.get(model)
        if state and task_type in state.tier_overrides:
            del state.tier_overrides[task_type]

    # ─── Readiness Signals ──────────────────────────────────────

    def tier_readiness(self, model: str) -> dict:
        """Check what tier a model is ready for based on data.

        Returns readiness signals — the PO decides whether to act.
        """
        records = self._model_records(model)
        count = len(records)
        rate = self.approval_rate(model)
        current = self.get_tier(model)

        result: dict = {
            "model": model,
            "current_tier": current,
            "sample_count": count,
            "approval_rate": round(rate, 3),
            "eligible_for": current,  # At minimum, stays at current
            "meets_min_samples": count >= MIN_SAMPLES,
        }

        if count < MIN_SAMPLES:
            result["note"] = f"Need {MIN_SAMPLES - count} more samples"
            return result

        if rate >= STANDARD_THRESHOLD:
            result["eligible_for"] = "standard"
        elif rate >= VALIDATION_THRESHOLD:
            result["eligible_for"] = "trainee-validated"
        else:
            result["eligible_for"] = "trainee"

        # Per-task-type readiness
        task_readiness: dict[str, dict] = {}
        for tt in self.task_types_for_model(model):
            tt_count = self.sample_count(model, tt)
            tt_rate = self.approval_rate(model, tt)
            eligible = "trainee"
            if tt_count >= MIN_SAMPLES:
                if tt_rate >= STANDARD_THRESHOLD:
                    eligible = "standard"
                elif tt_rate >= VALIDATION_THRESHOLD:
                    eligible = "trainee-validated"
            task_readiness[tt] = {
                "sample_count": tt_count,
                "approval_rate": round(tt_rate, 3),
                "eligible_for": eligible,
            }

        result["by_task_type"] = task_readiness
        return result

    # ─── Model Performance Over Time ────────────────────────────

    def performance_window(
        self, model: str, window_size: int = 20,
    ) -> list[float]:
        """Rolling approval rate in windows of N records.

        Shows trend: is the model getting better or worse?
        """
        records = self._model_records(model)
        if len(records) < window_size:
            if not records:
                return []
            rate = sum(1 for r in records if r.approved) / len(records)
            return [round(rate, 3)]

        windows: list[float] = []
        for i in range(0, len(records) - window_size + 1, window_size):
            chunk = records[i:i + window_size]
            rate = sum(1 for r in chunk if r.approved) / len(chunk)
            windows.append(round(rate, 3))
        return windows

    # ─── Summary ────────────────────────────────────────────────

    def models(self) -> list[str]:
        """All tracked models."""
        return list(self._tiers.keys())

    def summary(self) -> dict:
        """Full tier progression summary."""
        model_summaries: dict[str, dict] = {}
        for model in self.models():
            readiness = self.tier_readiness(model)
            model_summaries[model] = {
                "current_tier": readiness["current_tier"],
                "sample_count": readiness["sample_count"],
                "approval_rate": readiness["approval_rate"],
                "eligible_for": readiness["eligible_for"],
                "performance_trend": self.performance_window(model),
            }
        return {
            "total_records": self.total_records,
            "tracked_models": len(self._tiers),
            "models": model_summaries,
        }

    def format_report(self) -> str:
        """Format tier progression as markdown."""
        s = self.summary()
        lines = [
            "## Confidence Tier Progression Report",
            "",
            f"**Total records:** {s['total_records']}",
            f"**Tracked models:** {s['tracked_models']}",
            "",
        ]

        for model, data in s["models"].items():
            lines.append(f"### {model}")
            lines.append(f"- **Current tier:** {data['current_tier']}")
            lines.append(f"- **Samples:** {data['sample_count']}")
            lines.append(f"- **Approval rate:** {data['approval_rate']:.1%}")
            lines.append(f"- **Eligible for:** {data['eligible_for']}")
            if data["performance_trend"]:
                trend = " → ".join(f"{r:.0%}" for r in data["performance_trend"])
                lines.append(f"- **Trend:** {trend}")
            lines.append("")

        return "\n".join(lines)