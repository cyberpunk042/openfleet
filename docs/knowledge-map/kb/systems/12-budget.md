# System 12: Budget — Fleet Tempo & Quota Monitoring

**Type:** Fleet System
**ID:** S12
**Files:** budget_monitor.py (~200 lines), budget_modes.py (~150 lines), budget_analytics.py (~250 lines), budget_ui.py (~200 lines)
**Total:** ~800 lines
**Tests:** 40+

## What This System Does

Controls fleet TEMPO (how fast and frequently agents work) via budget modes, and monitors real Claude quota via OAuth API to prevent overruns. Budget mode is a TEMPO SETTING — it controls orchestrator cycle speed and heartbeat frequency. It does NOT control which models are allowed, which backends are enabled, or dollar amounts. Those are separate concerns (model_selection.py, fleet_mode.py backend_mode, challenge system).

PO requirement: "I am wondering if there is a new budgetMode (e.g. aggressive... whatever A, B... economic..) to inject into ocmc order to fine-tune the spending as speed / frequency of tasks"

## Budget Modes (4 defined, PO-driven)

| Mode | Orchestrator Cycle | Tempo Multiplier | Description |
|------|-------------------|-----------------|-------------|
| turbo | 5s | 0.167× | Maximum speed, fastest heartbeats |
| aggressive | 15s | 0.5× | Fast tempo |
| standard | 30s | 1.0× (baseline) | Normal operation |
| economic | 60s | 2.0× | Slow pace, conserve quota |

Tempo multiplier applied to: orchestrator cycle interval, gateway heartbeat CRON intervals, driver wake cooldowns. ALL crons scale with budget mode — not just the orchestrator.

Guard rails: MIN 5 min heartbeat interval (prevent runaway costs), MAX 2 hours (prevent dead fleet), MIN 5s orchestrator cycle, MAX 120s.

## Real Quota Monitoring

budget_monitor.py reads Claude OAuth API usage (cached 5 minutes):
- 5-hour session window usage %
- 7-day all-models window usage %
- 7-day sonnet-specific window usage %

Hard limits that PAUSE dispatch:
- Weekly ≥ 90% → PAUSE
- Session ≥ 95% → PAUSE
- Fast climb +5% in 10 minutes → PAUSE + storm indicator

Progressive alerts at 50%, 70%, 80%, 90% thresholds → IRC + ntfy.

## Separate Concerns

| Setting | What It Controls | Source |
|---------|-----------------|--------|
| budget_mode | Fleet tempo (speed/frequency) | budget_modes.py |
| backend_mode | Which backends enabled (7 combos) | fleet_mode.py |
| work_mode | Which agents active | fleet_mode.py |
| model_selection | opus vs sonnet per task | model_selection.py |

These are INDEPENDENT. Any combination valid.

## Cost Optimization Potential

| Optimization | Savings | Status |
|-------------|---------|--------|
| Silent heartbeats (brain evaluation) | ~70% | NOT BUILT |
| Prompt caching | ~90% on cached input | NOT DEPLOYED |
| LocalAI routing (simple tasks) | ~100% on routed tasks | NOT CONNECTED |
| Batch API (async work) | ~50% | NOT USED |
| Smart compaction (pre-rollover) | Prevents 20% spike | NOT BUILT |

Only real quota monitoring is implemented. The savings mechanisms are designed but not deployed.

## Relationships

- READ BY: orchestrator.py (budget check at dispatch gate, tempo for sleep interval)
- STORED IN: OCMC fleet_config (budget_mode), Claude OAuth API (quota readings)
- GATES: orchestrator dispatch (unsafe quota → pause)
- PRODUCES: budget alerts (50%, 70%, 80%, 90% thresholds)
- FEEDS: storm_monitor.py (fast_climb indicator from budget readings)
- CONNECTS TO: S05 control surface (budget_mode is a fleet_config axis)
- CONNECTS TO: S07 orchestrator (dispatch gate + cycle interval)
- CONNECTS TO: S11 storm (fast_climb indicator)
- CONNECTS TO: S13 labor (cost tracking per stamp)
- CONNECTS TO: S19 session (session_telemetry → to_cost_delta)
- CONNECTS TO: gateway_client.py (update_cron_tempo for heartbeat intervals)
- CONNECTS TO: /cost command (session cost), /usage command (rate limit)
- NOT YET IMPLEMENTED: budget analytics dashboard, per-order overrides tested, auto mode transitions on pressure

## For LightRAG Entity Extraction

Key entities: BudgetMode (4 defined: turbo/aggressive/standard/economic), tempo_multiplier (float), QuotaReading (5h/7d usage %), BudgetMonitor, budget_alert (threshold events).

Key relationships: PO SETS budget_mode. Orchestrator READS budget_mode. Tempo multiplier SCALES cycle interval + CRONs. Budget monitor READS OAuth API. Quota breach PAUSES dispatch. Fast climb TRIGGERS storm indicator. Budget mode INDEPENDENT of backend_mode and work_mode.
