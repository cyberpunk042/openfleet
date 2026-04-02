"""Budget modes — fleet tempo settings.

PO requirement (verbatim):
> "I am wondering if there is a new budgetMode (e.g. aggressive...
> whatever A, B... economic..) to inject into ocmc order to fine-tune
> the spending as speed / frequency of tasks / s and whatnot"

Budget modes control the TEMPO of the fleet:
- Orchestrator cycle speed
- Heartbeat frequency
- Consequence: operations per minute

Values are OFFSETS applied to the base config in fleet.yaml,
not absolute replacements.

Mode definitions are TBD — waiting for PO input.
PO examples: "aggressive" (faster tempo), "economic" (slower pace).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BudgetMode:
    """Fleet tempo setting — offsets applied to base fleet.yaml config."""

    name: str
    description: str
    tempo_multiplier: float                # Applied to orchestrator/heartbeat intervals
                                           # < 1.0 = faster, > 1.0 = slower


# PO-defined modes (2026-04-02):
#   turbo=5s, aggressive=15s, standard=30s, economic=60s cycle
# tempo_multiplier is relative to standard (30s base):
#   < 1.0 = faster than standard, > 1.0 = slower than standard
BUDGET_MODES: dict[str, BudgetMode] = {
    "turbo": BudgetMode(
        name="turbo",
        description="Maximum speed — 5s orchestrator cycle, fastest heartbeats",
        tempo_multiplier=5.0 / 30.0,  # ~0.167
    ),
    "aggressive": BudgetMode(
        name="aggressive",
        description="Fast tempo — 15s orchestrator cycle, fast heartbeats",
        tempo_multiplier=15.0 / 30.0,  # 0.5
    ),
    "standard": BudgetMode(
        name="standard",
        description="Normal tempo — 30s orchestrator cycle, normal heartbeats",
        tempo_multiplier=1.0,
    ),
    "economic": BudgetMode(
        name="economic",
        description="Slow tempo — 60s orchestrator cycle, slow heartbeats",
        tempo_multiplier=60.0 / 30.0,  # 2.0
    ),
}

MODE_ORDER: list[str] = ["turbo", "aggressive", "standard", "economic"]


def get_mode(name: str) -> Optional[BudgetMode]:
    """Get a budget mode by name."""
    return BUDGET_MODES.get(name)


def get_active_mode_name(fleet_dir: str = "") -> str:
    """Read the active budget mode from config."""
    import os
    import yaml

    if fleet_dir:
        config_path = os.path.join(fleet_dir, "config", "fleet.yaml")
    else:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "fleet.yaml",
        )

    try:
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("orchestrator", {}).get("budget_mode", "")
    except Exception:
        return ""
