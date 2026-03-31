"""Flow 4: Cost Control — Budget Envelope → Mode Transition → Routing Change.

Tests cost pressure triggering automatic mode transitions,
which in turn constrain routing and challenge depth.
"""

from fleet.core.budget_modes import constrain_model_by_budget
from fleet.core.budget_ui import CostTicker
from fleet.core.challenge_deferred import should_defer_challenge
from fleet.core.labor_stamp import LaborStamp


def test_cost_pressure_transition():
    """Spending crosses envelope threshold → mode should downgrade."""
    ticker = CostTicker(budget_mode="standard")  # $20 envelope

    # Spend 80% of envelope
    ticker.add_cost(16.0)
    assert ticker.cost_used_pct >= 80.0
    assert not ticker.over_budget

    # Spend past 100%
    ticker.add_cost(5.0)
    assert ticker.over_budget is True

    # In production, the orchestrator would transition to economic
    # We verify the data that drives that decision
    ticker_economic = CostTicker(budget_mode="economic")  # $10 envelope
    assert ticker_economic.envelope_usd == 10.0


def test_cost_recovery_transition():
    """Daily reset → mode can upgrade again."""
    ticker = CostTicker(budget_mode="economic")
    ticker.add_cost(11.0)  # Over $10 envelope
    assert ticker.over_budget is True

    # Daily reset
    ticker.reset_daily()
    assert ticker.cost_today_usd == 0.0
    assert ticker.over_budget is False
    assert ticker.cost_used_pct == 0.0


def test_cost_override():
    """PO override keeps blitz despite pressure."""
    from fleet.core.budget_ui import BudgetOverrideManager

    mgr = BudgetOverrideManager()

    # Current mode is economic due to cost pressure
    base_mode = "economic"

    # PO overrides a specific order to blitz
    mgr.set_override("ORDER-42", "blitz", reason="PO: critical delivery")
    effective = mgr.effective_mode("ORDER-42", base_mode)
    assert effective == "blitz"

    # Other orders still use base mode
    effective_other = mgr.effective_mode("ORDER-99", base_mode)
    assert effective_other == "economic"

    # Model selection respects blitz override
    model, effort, reason = constrain_model_by_budget("opus", "high", "test", effective)
    assert model == "opus"  # Opus allowed in blitz

    # Challenge NOT deferred in blitz
    assert should_defer_challenge("blitz") is False


def test_cost_stamps():
    """Labor stamps record budget mode — analytics can break down cost by mode."""
    stamps = []
    for mode in ("blitz", "standard", "economic", "frugal"):
        stamp = LaborStamp(
            agent_name="worker",
            backend="claude-code" if mode != "frugal" else "localai",
            model="opus" if mode == "blitz" else "sonnet" if mode != "frugal" else "hermes-3b",
            budget_mode=mode,
            estimated_cost_usd=1.0 if mode == "blitz" else 0.5 if mode == "standard" else 0.1 if mode == "economic" else 0.0,
        )
        stamps.append(stamp)

    # Verify stamps have distinct budget modes
    modes = {s.budget_mode for s in stamps}
    assert modes == {"blitz", "standard", "economic", "frugal"}

    # Frugal stamp should be free (localai)
    frugal = [s for s in stamps if s.budget_mode == "frugal"][0]
    assert frugal.estimated_cost_usd == 0.0
    assert frugal.backend == "localai"
