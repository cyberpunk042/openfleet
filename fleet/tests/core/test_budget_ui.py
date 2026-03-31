"""Tests for budget mode UI data provider (M-BM05)."""

from fleet.core.budget_ui import (
    COST_ENVELOPES,
    BudgetOverride,
    BudgetOverrideManager,
    CostTicker,
    budget_ui_payload,
)


# ─── CostTicker ───────────────────────────────────────────────


def test_ticker_defaults():
    t = CostTicker()
    assert t.budget_mode == "standard"
    assert t.cost_today_usd == 0.0
    assert t.cost_used_pct == 0.0


def test_ticker_envelope():
    t = CostTicker(budget_mode="standard")
    assert t.envelope_usd == 20.0
    t2 = CostTicker(budget_mode="frugal")
    assert t2.envelope_usd == 5.0


def test_ticker_cost_used_pct():
    t = CostTicker(budget_mode="standard", cost_today_usd=10.0)
    assert t.cost_used_pct == 50.0


def test_ticker_cost_used_pct_over():
    t = CostTicker(budget_mode="standard", cost_today_usd=25.0)
    assert t.cost_used_pct == 100.0  # Capped at 100


def test_ticker_blackout_zero_envelope():
    t = CostTicker(budget_mode="blackout", cost_today_usd=0.0)
    assert t.cost_used_pct == 0.0
    t2 = CostTicker(budget_mode="blackout", cost_today_usd=0.01)
    assert t2.cost_used_pct == 100.0


def test_ticker_remaining():
    t = CostTicker(budget_mode="standard", cost_today_usd=8.0)
    assert t.remaining_usd == 12.0


def test_ticker_remaining_over_budget():
    t = CostTicker(budget_mode="standard", cost_today_usd=25.0)
    assert t.remaining_usd == 0.0


def test_ticker_over_budget():
    t = CostTicker(budget_mode="standard", cost_today_usd=21.0)
    assert t.over_budget
    t2 = CostTicker(budget_mode="standard", cost_today_usd=19.0)
    assert not t2.over_budget


def test_ticker_add_cost():
    t = CostTicker(budget_mode="standard")
    t.add_cost(5.0)
    t.add_cost(3.0)
    assert t.cost_today_usd == 8.0
    assert t.cost_this_hour_usd == 8.0
    assert t.tasks_today == 2


def test_ticker_reset_daily():
    t = CostTicker(budget_mode="standard", cost_today_usd=10.0)
    t.tasks_today = 5
    t.reset_daily()
    assert t.cost_today_usd == 0.0
    assert t.tasks_today == 0


def test_ticker_reset_hourly():
    t = CostTicker(budget_mode="standard")
    t.add_cost(5.0)
    t.reset_hourly()
    assert t.cost_this_hour_usd == 0.0
    assert t.cost_today_usd == 5.0  # Daily not reset


def test_ticker_to_dict():
    t = CostTicker(budget_mode="economic", cost_today_usd=5.0)
    d = t.to_dict()
    assert d["budget_mode"] == "economic"
    assert d["envelope_usd"] == 10.0
    assert d["cost_used_pct"] == 50.0
    assert d["over_budget"] is False


# ─── COST_ENVELOPES ───────────────────────────────────────────


def test_cost_envelopes_all_modes():
    assert "blitz" in COST_ENVELOPES
    assert "standard" in COST_ENVELOPES
    assert "economic" in COST_ENVELOPES
    assert "frugal" in COST_ENVELOPES
    assert "survival" in COST_ENVELOPES
    assert "blackout" in COST_ENVELOPES


def test_cost_envelopes_ordering():
    assert COST_ENVELOPES["blitz"] > COST_ENVELOPES["standard"]
    assert COST_ENVELOPES["standard"] > COST_ENVELOPES["economic"]
    assert COST_ENVELOPES["economic"] > COST_ENVELOPES["frugal"]
    assert COST_ENVELOPES["frugal"] > COST_ENVELOPES["survival"]
    assert COST_ENVELOPES["survival"] > COST_ENVELOPES["blackout"]
    assert COST_ENVELOPES["blackout"] == 0.0


# ─── BudgetOverride ───────────────────────────────────────────


def test_override_defaults():
    o = BudgetOverride(order_id="ORD-1", budget_mode="blitz")
    assert o.set_by == "PO"
    assert o.set_at > 0


def test_override_to_dict():
    o = BudgetOverride(
        order_id="ORD-1", budget_mode="blitz", reason="urgent fix",
    )
    d = o.to_dict()
    assert d["order_id"] == "ORD-1"
    assert d["budget_mode"] == "blitz"
    assert d["reason"] == "urgent fix"


# ─── BudgetOverrideManager ────────────────────────────────────


def test_manager_set_override():
    m = BudgetOverrideManager()
    o = m.set_override("ORD-1", "blitz", "urgent")
    assert o.budget_mode == "blitz"
    assert len(m.active_overrides) == 1


def test_manager_get_override():
    m = BudgetOverrideManager()
    m.set_override("ORD-1", "blitz")
    assert m.get_override("ORD-1") is not None
    assert m.get_override("ORD-2") is None


def test_manager_clear_override():
    m = BudgetOverrideManager()
    m.set_override("ORD-1", "blitz")
    assert m.clear_override("ORD-1")
    assert not m.clear_override("ORD-1")  # Already cleared
    assert len(m.active_overrides) == 0


def test_manager_effective_mode_with_override():
    m = BudgetOverrideManager()
    m.set_override("ORD-1", "blitz")
    assert m.effective_mode("ORD-1", "standard") == "blitz"


def test_manager_effective_mode_no_override():
    m = BudgetOverrideManager()
    assert m.effective_mode("ORD-1", "standard") == "standard"


def test_manager_to_dict():
    m = BudgetOverrideManager()
    m.set_override("ORD-1", "blitz")
    m.set_override("ORD-2", "economic")
    d = m.to_dict()
    assert d["total_overrides"] == 2
    assert "ORD-1" in d["overrides"]
    assert "ORD-2" in d["overrides"]


# ─── budget_ui_payload ─────────────────────────────────────────


def test_payload_basic():
    t = CostTicker(budget_mode="standard", cost_today_usd=8.0)
    t.tasks_today = 3
    p = budget_ui_payload(t)
    assert p["budget_mode"] == "standard"
    assert p["cost_used_pct"] == 40.0
    assert p["tasks_today"] == 3
    assert "budget_overrides" not in p


def test_payload_with_overrides():
    t = CostTicker(budget_mode="standard")
    m = BudgetOverrideManager()
    m.set_override("ORD-1", "blitz")
    p = budget_ui_payload(t, m)
    assert "budget_overrides" in p
    assert p["budget_overrides"]["total_overrides"] == 1