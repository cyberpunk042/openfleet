"""Tests for budget mode system — fleet tempo settings."""

from fleet.core.budget_modes import (
    BUDGET_MODES,
    MODE_ORDER,
    BudgetMode,
    get_mode,
)


# ─── Mode Registry ──────────────────────────────────────────────────


def test_budget_modes_defined():
    """PO-defined modes: turbo, aggressive, standard, economic."""
    assert len(BUDGET_MODES) == 4
    assert "turbo" in BUDGET_MODES
    assert "aggressive" in BUDGET_MODES
    assert "standard" in BUDGET_MODES
    assert "economic" in BUDGET_MODES


def test_mode_order():
    assert MODE_ORDER == ["turbo", "aggressive", "standard", "economic"]


def test_tempo_multipliers_ordered():
    """Turbo is fastest (smallest multiplier), economic is slowest."""
    assert BUDGET_MODES["turbo"].tempo_multiplier < BUDGET_MODES["aggressive"].tempo_multiplier
    assert BUDGET_MODES["aggressive"].tempo_multiplier < BUDGET_MODES["standard"].tempo_multiplier
    assert BUDGET_MODES["standard"].tempo_multiplier < BUDGET_MODES["economic"].tempo_multiplier


def test_standard_is_baseline():
    """Standard mode has tempo_multiplier of 1.0 (no offset)."""
    assert BUDGET_MODES["standard"].tempo_multiplier == 1.0


def test_get_mode_returns_none_for_unknown():
    assert get_mode("nonexistent") is None


# ─── BudgetMode Dataclass ───────────────────────────────────────────


def test_budget_mode_creation():
    mode = BudgetMode(
        name="test",
        description="test mode",
        tempo_multiplier=1.0,
    )
    assert mode.name == "test"
    assert mode.tempo_multiplier == 1.0
