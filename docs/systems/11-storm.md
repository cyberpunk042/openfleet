# System 11: Storm Prevention

**Source:** `fleet/core/storm_monitor.py`, `fleet/core/storm_integration.py`, `fleet/core/storm_analytics.py`, `fleet/core/incident_report.py`
**Status:** 🔨 Unit + integration tests. Orchestrator uses storm monitor. Not live tested at scale.
**Design docs:** `storm-prevention-system.md` (M-SP01-09)

---

## Purpose

Detect runaway cost, cascading failures, and fleet misbehavior AUTOMATICALLY. Graduated response from monitoring to full shutdown. Prevent the March catastrophe from repeating.

### PO Requirement (Verbatim)

> "we need to be able to pause all the work or reduce the efforts and strategy like that strategic and driven by the user and circumstances"

## Key Concepts

### 9 Storm Indicators (storm_monitor.py)

1. `session_burst` — >10 sessions/min
2. `fast_climb` — budget climbing fast
3. `void_sessions` — >50% void rate
4. `dispatch_storm` — high dispatch rate
5. `cascade_depth` — nested dispatch chains
6. `agent_thrashing` — agent failures
7. `error_storm` — error surge
8. `gateway_duplication` — immediate flag (March root cause)
9. `context_pressure` — context at 70%+ (from session telemetry W8)

### 5 Severity Levels

```
CLEAR   → normal operation
WATCH   → monitoring, note in log
WARNING → dispatch ≤ 1, diagnostic snapshot, force economic mode
STORM   → dispatch = 0, force survival mode, alert PO
CRITICAL → halt cycle, force blackout, alert PO urgently
```

### Storm → Budget Forcing (storm_integration.py)

```python
STORM_BUDGET_FORCING = {
    CRITICAL: "blackout",
    STORM: "survival",
    WARNING: "economic",
}
```

Validated against `budget_modes.MODE_ORDER` at import time (W3 wiring).

### Circuit Breakers (storm_monitor.py)

Per-agent and per-backend circuit breakers:
- CLOSED → (failures) → OPEN → (cooldown) → HALF_OPEN → (success) → CLOSED
- failure_threshold: 3
- Cooldown: 300s agents, 120s backends, doubles on repeated trips, max 1h

### Diagnostic Snapshots (storm_monitor.py)

Captured on WARNING+: severity, indicators, sessions, dispatches, void rate, agent states, errors, budget mode. Persisted to disk (50-file cap).

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Storm check is pre-step gate every cycle | Storm → Orchestrator |
| **Budget** | Storm forces budget mode | Storm → Budget |
| **Backend Router** | Circuit breakers affect routing fallback | Storm → Router |
| **Session Telemetry** | Context pressure as storm indicator (W8) | Telemetry → Storm |
| **Gateway Guard** | Gateway duplication check feeds storm | Guard → Storm |
| **Events** | Storm events emitted | Storm → Events |
| **Notifications** | WARNING+ → IRC #alerts, STORM+ → ntfy PO | Storm → Notifications |

## What's Needed

- [ ] Storm analytics integration with budget analytics
- [ ] Post-incident automatic report generation
- [ ] De-escalation tuning (slower than escalation)
- [ ] Live test: simulate storm, verify graduated response
