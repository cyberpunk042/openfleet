"""Budget mode UI data provider (M-BM05).

Provides the data that the OCMC header bar budget controls display:
- Current budget mode
- Cost envelope usage percentage
- Real-time cost ticker
- Per-order budget mode overrides

This module computes the data. The FleetControlBar TSX component
(patches/0005-FleetControlBar.tsx) renders it.

Design doc requirement:
> Display current budget mode in MC header bar (control surface).
> Mode selector dropdown with descriptions.
> Per-order budget mode override.
> Cost envelope progress bar.
> Real-time cost ticker.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# ─── Cost Envelope ─────────────────────────────────────────────


# Default daily cost envelopes per budget mode (USD)
COST_ENVELOPES: dict[str, float] = {
    "blitz": 50.0,
    "standard": 20.0,
    "economic": 10.0,
    "frugal": 5.0,
    "survival": 1.0,
    "blackout": 0.0,
}


@dataclass
class CostTicker:
    """Real-time cost tracking for the UI cost bar."""

    budget_mode: str = "standard"
    cost_today_usd: float = 0.0
    cost_this_hour_usd: float = 0.0
    tasks_today: int = 0
    last_updated: float = 0.0

    def __post_init__(self) -> None:
        if not self.last_updated:
            self.last_updated = time.time()

    @property
    def envelope_usd(self) -> float:
        return COST_ENVELOPES.get(self.budget_mode, 20.0)

    @property
    def cost_used_pct(self) -> float:
        if self.envelope_usd <= 0:
            return 100.0 if self.cost_today_usd > 0 else 0.0
        return min((self.cost_today_usd / self.envelope_usd) * 100, 100.0)

    @property
    def remaining_usd(self) -> float:
        return max(self.envelope_usd - self.cost_today_usd, 0.0)

    @property
    def over_budget(self) -> bool:
        return self.cost_today_usd > self.envelope_usd and self.envelope_usd > 0

    def add_cost(self, cost_usd: float) -> None:
        self.cost_today_usd += cost_usd
        self.cost_this_hour_usd += cost_usd
        self.tasks_today += 1
        self.last_updated = time.time()

    def reset_daily(self) -> None:
        self.cost_today_usd = 0.0
        self.cost_this_hour_usd = 0.0
        self.tasks_today = 0
        self.last_updated = time.time()

    def reset_hourly(self) -> None:
        self.cost_this_hour_usd = 0.0
        self.last_updated = time.time()

    def to_dict(self) -> dict:
        return {
            "budget_mode": self.budget_mode,
            "cost_today_usd": round(self.cost_today_usd, 4),
            "cost_this_hour_usd": round(self.cost_this_hour_usd, 4),
            "envelope_usd": self.envelope_usd,
            "cost_used_pct": round(self.cost_used_pct, 1),
            "remaining_usd": round(self.remaining_usd, 4),
            "over_budget": self.over_budget,
            "tasks_today": self.tasks_today,
        }


# ─── Per-Order Budget Override ─────────────────────────────────


@dataclass
class BudgetOverride:
    """A per-order budget mode override."""

    order_id: str
    budget_mode: str
    reason: str = ""
    set_by: str = "PO"
    set_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.set_at:
            self.set_at = time.time()

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "budget_mode": self.budget_mode,
            "reason": self.reason,
            "set_by": self.set_by,
        }


class BudgetOverrideManager:
    """Manages per-order budget mode overrides.

    Fleet-wide budget mode is the default. Individual orders
    can override it (e.g., "this urgent task uses blitz mode
    even though fleet is in economic mode").
    """

    def __init__(self) -> None:
        self._overrides: dict[str, BudgetOverride] = {}

    def set_override(
        self, order_id: str, budget_mode: str, reason: str = "",
    ) -> BudgetOverride:
        override = BudgetOverride(
            order_id=order_id, budget_mode=budget_mode, reason=reason,
        )
        self._overrides[order_id] = override
        return override

    def get_override(self, order_id: str) -> Optional[BudgetOverride]:
        return self._overrides.get(order_id)

    def clear_override(self, order_id: str) -> bool:
        if order_id in self._overrides:
            del self._overrides[order_id]
            return True
        return False

    def effective_mode(self, order_id: str, fleet_mode: str) -> str:
        """Get the effective budget mode for an order."""
        override = self._overrides.get(order_id)
        if override:
            return override.budget_mode
        return fleet_mode

    @property
    def active_overrides(self) -> list[BudgetOverride]:
        return list(self._overrides.values())

    def to_dict(self) -> dict:
        return {
            "total_overrides": len(self._overrides),
            "overrides": {
                oid: o.to_dict() for oid, o in self._overrides.items()
            },
        }


# ─── Board Config Payload ──────────────────────────────────────


def budget_ui_payload(
    ticker: CostTicker,
    override_mgr: Optional[BudgetOverrideManager] = None,
) -> dict:
    """Build the payload to PATCH into board.fleet_config.

    This is what the FleetControlBar reads to render budget state.
    """
    payload = {
        "budget_mode": ticker.budget_mode,
        "cost_used_pct": round(ticker.cost_used_pct, 1),
        "cost_today_usd": round(ticker.cost_today_usd, 4),
        "envelope_usd": ticker.envelope_usd,
        "remaining_usd": round(ticker.remaining_usd, 4),
        "over_budget": ticker.over_budget,
        "tasks_today": ticker.tasks_today,
    }
    if override_mgr:
        payload["budget_overrides"] = override_mgr.to_dict()
    return payload