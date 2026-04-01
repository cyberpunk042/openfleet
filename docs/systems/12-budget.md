# System 12: Budget System

**Source:** `fleet/core/budget_monitor.py`, `fleet/core/budget_modes.py`, `fleet/core/budget_analytics.py`, `fleet/core/budget_ui.py`
**Status:** 🔨 Unit + integration tests. Budget monitor active in orchestrator.
**Design docs:** `budget-mode-system.md` (M-BM01-06)

---

## Purpose

Control fleet spending through graduated budget modes. Each mode constrains which models, backends, and effort levels are allowed. Automatic transitions based on quota pressure. Per-order overrides for PO control.

## Key Concepts

### 6 Budget Modes (budget_modes.py)

| Mode | Envelope | Allowed Models | Max Effort |
|------|----------|---------------|------------|
| blitz | $50/day | opus, sonnet, haiku | max |
| standard | $20/day | opus, sonnet | high |
| economic | $10/day | sonnet | medium |
| frugal | $5/day | (none — free only) | medium |
| survival | $1/day | (none — free only) | low |
| blackout | $0/day | (none) | low |

`MODE_ORDER`: blitz → standard → economic → frugal → survival → blackout

### Model Constraining (budget_modes.py:178-210)

`constrain_model_by_budget(model, effort, reason, budget_mode)` — if model not in mode's allowed list, downgrade to best allowed. If no models allowed, caller routes to LocalAI/free.

### Auto-Transitions (budget_modes.py)

`evaluate_auto_transition(current_mode, quota_used_pct)` — triggers mode downgrade at thresholds:
- 70% → next tighter mode
- 80% → skip to economic
- 90% → skip to frugal
- 95% → skip to survival

### Cost Ticker (budget_ui.py:41-99)

Real-time tracking: cost_today_usd, cost_this_hour_usd, tasks_today. Properties: envelope_usd, cost_used_pct, remaining_usd, over_budget.

### Per-Order Override (budget_ui.py:102+)

`BudgetOverrideManager` — PO can override budget mode for specific orders. `effective_mode(order_id, base_mode)` returns override or base.

### Budget Analytics (budget_analytics.py)

Per-mode metrics: total_tasks, total_cost, approval_rate, challenge_pass_rate. Mode comparison. Cost by task type. Cost per story point.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Budget mode read from board config | Budget → Orchestrator |
| **Backend Router** | Budget constrains allowed models/backends | Budget → Router |
| **Challenge Engine** | Budget mode determines challenge depth (W1 wiring) | Budget → Challenge |
| **Storm** | Storm forces budget mode (W3 wiring) | Storm → Budget |
| **Labor Stamps** | Stamps record budget_mode per task | Budget → Stamps |
| **Session Telemetry** | Real cost from Claude session data (W8) | Telemetry → Budget |
| **Control Surface** | Budget mode in FleetControlBar dropdown (M-BM05 patch) | Budget → UI |

## What's Needed

- [ ] Live test: budget pressure triggering mode transition
- [ ] Cost ticker fed by session telemetry (real costs, not estimates)
- [ ] Budget mode visible in OCMC UI (FleetControlBar)
- [ ] Prompt caching integration (90% savings on cached input)
