"""Budget modes — graduated spending strategy for fleet operations.

Six modes from maximum intensity to full stop:
  blitz     — Maximum speed, all models, highest cost
  standard  — Normal operation, balanced cost/speed
  economic  — Budget-conscious, sonnet + LocalAI only
  frugal    — Low budget, free models preferred
  survival  — Near-zero Claude spend, keep fleet alive
  blackout  — Budget exhausted, fleet frozen

Modes are set globally (fleet.yaml) or per-order (OCMC task custom field).
The brain respects the most restrictive mode in the chain.
Budget pressure triggers automatic de-escalation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetMode:
    """Configuration for a budget spending mode."""

    name: str
    description: str
    allowed_models: list[str]              # Models allowed in this mode
    allowed_backends: list[str]            # Backends allowed
    max_effort: str                        # Maximum effort level
    max_dispatch_per_cycle: int            # Max tasks dispatched per orchestrator cycle
    heartbeat_interval_min: int            # Minutes between heartbeats (0 = disabled)
    allow_opus: bool                       # Whether opus model is available
    allow_challenges: bool                 # Whether adversarial challenges run

    @property
    def is_active(self) -> bool:
        """Whether the fleet is doing any work in this mode."""
        return self.max_dispatch_per_cycle > 0 or self.heartbeat_interval_min > 0


BUDGET_MODES: dict[str, BudgetMode] = {
    "blitz": BudgetMode(
        name="blitz",
        description="Maximum speed — all models, all backends, highest cost",
        allowed_models=["opus", "sonnet", "haiku"],
        allowed_backends=["claude-code", "localai", "openrouter"],
        max_effort="max",
        max_dispatch_per_cycle=5,
        heartbeat_interval_min=15,
        allow_opus=True,
        allow_challenges=True,
    ),
    "standard": BudgetMode(
        name="standard",
        description="Normal operation — balanced cost and speed",
        allowed_models=["opus", "sonnet"],
        allowed_backends=["claude-code", "localai", "openrouter"],
        max_effort="high",
        max_dispatch_per_cycle=2,
        heartbeat_interval_min=30,
        allow_opus=True,
        allow_challenges=True,
    ),
    "economic": BudgetMode(
        name="economic",
        description="Budget-conscious — sonnet + LocalAI, no opus",
        allowed_models=["sonnet"],
        allowed_backends=["claude-code", "localai", "openrouter"],
        max_effort="medium",
        max_dispatch_per_cycle=1,
        heartbeat_interval_min=60,
        allow_opus=False,
        allow_challenges=True,
    ),
    "frugal": BudgetMode(
        name="frugal",
        description="Low budget — free models preferred, sonnet for complex only",
        allowed_models=["sonnet"],
        allowed_backends=["localai", "openrouter", "claude-code"],
        max_effort="medium",
        max_dispatch_per_cycle=1,
        heartbeat_interval_min=120,
        allow_opus=False,
        allow_challenges=False,  # challenges cost tokens
    ),
    "survival": BudgetMode(
        name="survival",
        description="Near-zero Claude spend — LocalAI + free only, fleet stays alive",
        allowed_models=[],  # No Claude models
        allowed_backends=["localai", "openrouter", "direct"],
        max_effort="low",
        max_dispatch_per_cycle=1,
        heartbeat_interval_min=480,
        allow_opus=False,
        allow_challenges=False,
    ),
    "blackout": BudgetMode(
        name="blackout",
        description="Fleet frozen — nothing runs, budget exhausted",
        allowed_models=[],
        allowed_backends=[],
        max_effort="low",
        max_dispatch_per_cycle=0,
        heartbeat_interval_min=0,
        allow_opus=False,
        allow_challenges=False,
    ),
}

# Ordered from most to least intensive — used for escalation/de-escalation
MODE_ORDER = ["blitz", "standard", "economic", "frugal", "survival", "blackout"]


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
        return cfg.get("orchestrator", {}).get("budget_mode", "standard")
    except Exception:
        return "standard"


def deescalate(current: str) -> str:
    """Drop one level of intensity (toward blackout).

    Returns the next less-intensive mode.
    """
    try:
        idx = MODE_ORDER.index(current)
    except ValueError:
        return "economic"
    next_idx = min(idx + 1, len(MODE_ORDER) - 1)
    return MODE_ORDER[next_idx]


def escalate(current: str) -> str:
    """Raise one level of intensity (toward blitz).

    Returns the next more-intensive mode.
    Only the brain calls this, and only if escalation_allowed is True.
    """
    try:
        idx = MODE_ORDER.index(current)
    except ValueError:
        return "standard"
    next_idx = max(idx - 1, 0)
    return MODE_ORDER[next_idx]


def mode_allows_model(mode_name: str, model: str) -> bool:
    """Check if a model is allowed under a budget mode."""
    mode = BUDGET_MODES.get(mode_name)
    if not mode:
        return True  # Unknown mode = permissive (fail open)
    if not mode.allowed_models:
        return False  # No models allowed (survival/blackout for Claude)
    return model in mode.allowed_models


def constrain_model_by_budget(
    model: str,
    effort: str,
    reason: str,
    budget_mode: str,
) -> tuple[str, str, str]:
    """Constrain model selection to what the budget mode allows.

    Returns (model, effort, reason) — potentially downgraded.
    """
    mode = BUDGET_MODES.get(budget_mode)
    if not mode:
        return model, effort, reason

    # Check if model is allowed
    if model not in mode.allowed_models:
        if mode.allowed_models:
            fallback = mode.allowed_models[-1]  # Last = most capable allowed
            return (
                fallback,
                _cap_effort(effort, mode.max_effort),
                f"{reason} [constrained by {budget_mode}: {model}→{fallback}]",
            )
        # No Claude models allowed — caller must route to LocalAI/free
        return model, effort, f"{reason} [blocked by {budget_mode}: no Claude models]"

    # Cap effort level
    capped_effort = _cap_effort(effort, mode.max_effort)
    if capped_effort != effort:
        reason = f"{reason} [effort capped by {budget_mode}: {effort}→{capped_effort}]"

    return model, capped_effort, reason


# Effort level ordering
_EFFORT_ORDER = ["low", "medium", "high", "max"]


def _cap_effort(effort: str, max_effort: str) -> str:
    """Cap effort to maximum allowed."""
    try:
        eidx = _EFFORT_ORDER.index(effort)
        midx = _EFFORT_ORDER.index(max_effort)
    except ValueError:
        return effort
    return _EFFORT_ORDER[min(eidx, midx)]


# ─── Automatic Mode Transitions (M-BM03) ──────────────────────────


# Quota thresholds that trigger automatic de-escalation.
# When weekly_all_pct hits a threshold, the fleet drops to that mode.
QUOTA_DEESCALATION_THRESHOLDS: list[tuple[float, str]] = [
    (95.0, "blackout"),   # 95%+ → full stop
    (90.0, "survival"),   # 90%+ → free-only, keep alive
    (80.0, "frugal"),     # 80%+ → minimize Claude
    (70.0, "economic"),   # 70%+ → no opus, sonnet only
]


@dataclass
class ModeTransition:
    """Records a budget mode transition with reason."""

    from_mode: str
    to_mode: str
    reason: str
    triggered_by: str       # "quota_pressure", "envelope_exhausted", "manual", "escalation"
    quota_pct: float = 0.0


def evaluate_auto_transition(
    current_mode: str,
    weekly_all_pct: float,
    session_pct: float = 0.0,
) -> Optional[ModeTransition]:
    """Evaluate whether quota pressure requires a mode transition.

    Returns a ModeTransition if the fleet should de-escalate, or None
    if the current mode is already appropriate.

    Only de-escalates — never auto-escalates past the current mode.
    Escalation requires explicit PO approval or the brain's
    escalation_allowed flag.
    """
    current_idx = _mode_index(current_mode)

    for threshold, target_mode in QUOTA_DEESCALATION_THRESHOLDS:
        if weekly_all_pct >= threshold:
            target_idx = _mode_index(target_mode)
            # Only de-escalate (higher index = less intensive)
            if target_idx > current_idx:
                return ModeTransition(
                    from_mode=current_mode,
                    to_mode=target_mode,
                    reason=f"weekly quota at {weekly_all_pct:.0f}% (threshold: {threshold:.0f}%)",
                    triggered_by="quota_pressure",
                    quota_pct=weekly_all_pct,
                )
            break  # Already at or below target intensity

    # Session quota emergency — if session hits 95% force survival minimum
    if session_pct >= 95.0 and current_idx < _mode_index("survival"):
        return ModeTransition(
            from_mode=current_mode,
            to_mode="survival",
            reason=f"session quota at {session_pct:.0f}% — emergency de-escalation",
            triggered_by="quota_pressure",
            quota_pct=session_pct,
        )

    return None


def evaluate_envelope_transition(
    current_mode: str,
    envelope_pct_used: float,
) -> Optional[ModeTransition]:
    """Evaluate whether a cost envelope is triggering a transition.

    Per-order cost envelopes can independently force de-escalation:
    - 80% used → economic
    - 95% used → frugal
    - 100% used → survival (order frozen, only free work)
    """
    current_idx = _mode_index(current_mode)

    if envelope_pct_used >= 100.0:
        target = "survival"
    elif envelope_pct_used >= 95.0:
        target = "frugal"
    elif envelope_pct_used >= 80.0:
        target = "economic"
    else:
        return None

    target_idx = _mode_index(target)
    if target_idx > current_idx:
        return ModeTransition(
            from_mode=current_mode,
            to_mode=target,
            reason=f"cost envelope at {envelope_pct_used:.0f}%",
            triggered_by="envelope_exhausted",
            quota_pct=envelope_pct_used,
        )

    return None


def evaluate_escalation(
    current_mode: str,
    blocked_cycles: int,
    escalation_allowed: bool = False,
) -> Optional[ModeTransition]:
    """Evaluate whether a task blocked too long warrants escalation.

    Only escalates if:
    - The task has been blocked for 2+ orchestrator cycles
    - escalation_allowed is True (set by PO on the order)
    - Current mode is below blitz

    Returns a ModeTransition one level up, or None.
    """
    if not escalation_allowed:
        return None

    if blocked_cycles < 2:
        return None

    current_idx = _mode_index(current_mode)
    if current_idx <= 0:
        return None  # Already at blitz

    target = escalate(current_mode)
    if target == current_mode:
        return None

    return ModeTransition(
        from_mode=current_mode,
        to_mode=target,
        reason=f"task blocked for {blocked_cycles} cycles, escalating",
        triggered_by="escalation",
    )


def _mode_index(mode_name: str) -> int:
    """Get the index of a mode in MODE_ORDER (0=blitz, 5=blackout)."""
    try:
        return MODE_ORDER.index(mode_name)
    except ValueError:
        return 1  # Default to standard


# ─── Order Budget ──────────────────────────────────────────────────


@dataclass
class OrderBudgetConfig:
    """Budget configuration for a specific OCMC order/task.

    Set by PO when creating orders, readable by the brain at dispatch.
    """

    mode: str = "standard"
    cost_envelope_usd: Optional[float] = None  # Max spend for this order
    cost_spent_usd: float = 0.0                # Accumulated from labor stamps
    escalation_allowed: bool = True             # Can brain escalate mode?
    model_ceiling: Optional[str] = None         # Hard cap (e.g., "sonnet")
    max_iterations: int = 3                     # Max retry attempts

    @property
    def envelope_remaining(self) -> Optional[float]:
        if self.cost_envelope_usd is None:
            return None
        return max(0.0, self.cost_envelope_usd - self.cost_spent_usd)

    @property
    def envelope_pct_used(self) -> Optional[float]:
        if self.cost_envelope_usd is None or self.cost_envelope_usd == 0:
            return None
        return min(100.0, (self.cost_spent_usd / self.cost_envelope_usd) * 100)

    def record_cost(self, cost_usd: float) -> None:
        """Record cost from a labor stamp."""
        self.cost_spent_usd += cost_usd

    def check_envelope(self) -> tuple[bool, str]:
        """Check if the cost envelope allows more work.

        Returns (allowed, reason).
        """
        if self.cost_envelope_usd is None:
            return True, ""
        pct = self.envelope_pct_used or 0
        if pct >= 100:
            return False, f"Cost envelope exhausted: ${self.cost_spent_usd:.2f}/${self.cost_envelope_usd:.2f}"
        if pct >= 80:
            return True, f"Cost envelope at {pct:.0f}%: ${self.cost_spent_usd:.2f}/${self.cost_envelope_usd:.2f}"
        return True, ""