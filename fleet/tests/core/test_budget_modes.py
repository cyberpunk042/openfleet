"""Tests for budget mode system — graduated spending strategy."""

from fleet.core.budget_modes import (
    BUDGET_MODES,
    MODE_ORDER,
    BudgetMode,
    ModeTransition,
    OrderBudgetConfig,
    constrain_model_by_budget,
    deescalate,
    escalate,
    evaluate_auto_transition,
    evaluate_envelope_transition,
    evaluate_escalation,
    get_mode,
    mode_allows_model,
)


# ─── Mode Registry ──────────────────────────────────────────────────


def test_all_six_modes_exist():
    assert len(BUDGET_MODES) == 6
    for name in ["blitz", "standard", "economic", "frugal", "survival", "blackout"]:
        assert name in BUDGET_MODES


def test_mode_order_matches_registry():
    for name in MODE_ORDER:
        assert name in BUDGET_MODES


def test_blitz_is_most_intensive():
    mode = BUDGET_MODES["blitz"]
    assert mode.allow_opus is True
    assert mode.max_dispatch_per_cycle == 5
    assert "opus" in mode.allowed_models


def test_blackout_is_fully_frozen():
    mode = BUDGET_MODES["blackout"]
    assert mode.allowed_models == []
    assert mode.allowed_backends == []
    assert mode.max_dispatch_per_cycle == 0
    assert mode.heartbeat_interval_min == 0
    assert mode.is_active is False


def test_survival_no_claude_models():
    mode = BUDGET_MODES["survival"]
    assert mode.allowed_models == []
    assert "localai" in mode.allowed_backends
    assert mode.is_active is True  # Still dispatching, just no Claude


def test_economic_no_opus():
    mode = BUDGET_MODES["economic"]
    assert mode.allow_opus is False
    assert "opus" not in mode.allowed_models
    assert "sonnet" in mode.allowed_models


def test_get_mode_returns_none_for_unknown():
    assert get_mode("nonexistent") is None


# ─── Escalation / De-escalation ──────────────────────────────────────


def test_deescalate_standard_to_economic():
    assert deescalate("standard") == "economic"


def test_deescalate_blackout_stays():
    assert deescalate("blackout") == "blackout"


def test_escalate_economic_to_standard():
    assert escalate("economic") == "standard"


def test_escalate_blitz_stays():
    assert escalate("blitz") == "blitz"


def test_deescalate_unknown_defaults():
    assert deescalate("unknown") == "economic"


def test_escalate_unknown_defaults():
    assert escalate("unknown") == "standard"


def test_full_deescalation_chain():
    """Deescalating repeatedly from blitz reaches blackout."""
    mode = "blitz"
    chain = [mode]
    for _ in range(10):
        mode = deescalate(mode)
        chain.append(mode)
        if mode == "blackout":
            break
    assert chain[-1] == "blackout"
    assert chain == ["blitz", "standard", "economic", "frugal", "survival", "blackout"]


# ─── Model Allowance ────────────────────────────────────────────────


def test_opus_allowed_in_blitz():
    assert mode_allows_model("blitz", "opus") is True


def test_opus_blocked_in_economic():
    assert mode_allows_model("economic", "opus") is False


def test_sonnet_allowed_in_economic():
    assert mode_allows_model("economic", "sonnet") is True


def test_no_models_in_survival():
    assert mode_allows_model("survival", "opus") is False
    assert mode_allows_model("survival", "sonnet") is False


def test_unknown_mode_is_permissive():
    assert mode_allows_model("unknown", "opus") is True


# ─── Budget-Constrained Model Selection ─────────────────────────────


def test_constrain_opus_in_economic():
    model, effort, reason = constrain_model_by_budget(
        "opus", "high", "large task", "economic",
    )
    assert model == "sonnet"  # Downgraded
    assert "constrained" in reason


def test_constrain_sonnet_in_economic_unchanged():
    model, effort, reason = constrain_model_by_budget(
        "sonnet", "medium", "standard task", "economic",
    )
    assert model == "sonnet"  # No change


def test_constrain_effort_capped():
    model, effort, reason = constrain_model_by_budget(
        "sonnet", "max", "epic", "economic",
    )
    assert effort == "medium"  # economic caps at medium
    assert "capped" in reason


def test_constrain_survival_blocks_claude():
    model, effort, reason = constrain_model_by_budget(
        "sonnet", "medium", "task", "survival",
    )
    assert "blocked" in reason


def test_constrain_blitz_no_change():
    model, effort, reason = constrain_model_by_budget(
        "opus", "max", "epic", "blitz",
    )
    assert model == "opus"
    assert effort == "max"


# ─── OrderBudgetConfig ──────────────────────────────────────────────


def test_envelope_tracking():
    config = OrderBudgetConfig(cost_envelope_usd=10.0)
    config.record_cost(3.0)
    assert config.envelope_remaining == 7.0
    assert config.envelope_pct_used == 30.0


def test_envelope_exhausted():
    config = OrderBudgetConfig(cost_envelope_usd=5.0, cost_spent_usd=5.5)
    allowed, reason = config.check_envelope()
    assert allowed is False
    assert "exhausted" in reason


def test_envelope_warning_at_80pct():
    config = OrderBudgetConfig(cost_envelope_usd=10.0, cost_spent_usd=8.5)
    allowed, reason = config.check_envelope()
    assert allowed is True  # Still allowed but warning
    assert "85%" in reason


def test_no_envelope_always_allowed():
    config = OrderBudgetConfig()  # No envelope set
    allowed, reason = config.check_envelope()
    assert allowed is True
    assert reason == ""


def test_envelope_remaining_never_negative():
    config = OrderBudgetConfig(cost_envelope_usd=5.0, cost_spent_usd=10.0)
    assert config.envelope_remaining == 0.0


# ─── Automatic Mode Transitions (M-BM03) ──────────────────────────


def test_auto_transition_70pct_to_economic():
    t = evaluate_auto_transition("standard", weekly_all_pct=72.0)
    assert t is not None
    assert t.to_mode == "economic"
    assert t.triggered_by == "quota_pressure"


def test_auto_transition_80pct_to_frugal():
    t = evaluate_auto_transition("standard", weekly_all_pct=82.0)
    assert t is not None
    assert t.to_mode == "frugal"


def test_auto_transition_90pct_to_survival():
    t = evaluate_auto_transition("standard", weekly_all_pct=91.0)
    assert t is not None
    assert t.to_mode == "survival"


def test_auto_transition_95pct_to_blackout():
    t = evaluate_auto_transition("standard", weekly_all_pct=96.0)
    assert t is not None
    assert t.to_mode == "blackout"


def test_auto_transition_already_at_target():
    """If already at economic and 72% quota, no transition needed."""
    t = evaluate_auto_transition("economic", weekly_all_pct=72.0)
    assert t is None


def test_auto_transition_below_threshold():
    """At 60% quota, no de-escalation from standard."""
    t = evaluate_auto_transition("standard", weekly_all_pct=60.0)
    assert t is None


def test_auto_transition_never_escalates():
    """Auto transition never goes from frugal to standard, even at low quota."""
    t = evaluate_auto_transition("frugal", weekly_all_pct=30.0)
    assert t is None


def test_auto_transition_session_emergency():
    """Session quota at 95% forces survival minimum."""
    t = evaluate_auto_transition("standard", weekly_all_pct=50.0, session_pct=96.0)
    assert t is not None
    assert t.to_mode == "survival"


def test_auto_transition_session_already_survival():
    """Session emergency no-op if already at survival."""
    t = evaluate_auto_transition("survival", weekly_all_pct=50.0, session_pct=96.0)
    assert t is None


# ─── Envelope Transitions ─────────────────────────────────────────


def test_envelope_80pct_to_economic():
    t = evaluate_envelope_transition("standard", envelope_pct_used=85.0)
    assert t is not None
    assert t.to_mode == "economic"
    assert t.triggered_by == "envelope_exhausted"


def test_envelope_95pct_to_frugal():
    t = evaluate_envelope_transition("standard", envelope_pct_used=97.0)
    assert t is not None
    assert t.to_mode == "frugal"


def test_envelope_100pct_to_survival():
    t = evaluate_envelope_transition("standard", envelope_pct_used=100.0)
    assert t is not None
    assert t.to_mode == "survival"


def test_envelope_below_threshold():
    t = evaluate_envelope_transition("standard", envelope_pct_used=70.0)
    assert t is None


def test_envelope_already_at_target():
    t = evaluate_envelope_transition("frugal", envelope_pct_used=97.0)
    assert t is None


# ─── Escalation ───────────────────────────────────────────────────


def test_escalation_blocked_task():
    t = evaluate_escalation("economic", blocked_cycles=3, escalation_allowed=True)
    assert t is not None
    assert t.to_mode == "standard"
    assert t.triggered_by == "escalation"


def test_escalation_not_allowed():
    t = evaluate_escalation("economic", blocked_cycles=5, escalation_allowed=False)
    assert t is None


def test_escalation_not_enough_cycles():
    t = evaluate_escalation("economic", blocked_cycles=1, escalation_allowed=True)
    assert t is None


def test_escalation_already_blitz():
    t = evaluate_escalation("blitz", blocked_cycles=5, escalation_allowed=True)
    assert t is None