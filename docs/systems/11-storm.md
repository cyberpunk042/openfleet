# Storm Prevention — Automatic Graduated Response

> **4 files. 1440 lines. Detects runaway cost and cascading failures automatically.**
>
> The storm prevention system monitors 9 indicators for fleet misbehavior,
> evaluates severity on a 5-level scale, and applies graduated automatic
> response — from monitoring to full fleet shutdown. Circuit breakers
> trip per-agent and per-backend. Diagnostic snapshots capture state on
> WARNING+. Post-incident reports analyze what happened.
> Prevents the March catastrophe from repeating.

### PO Requirements (Verbatim)

> "we need to be able to pause all the work or reduce the efforts and
> strategy like that strategic and driven by the user and circumstances"

> "the fleet cp is also going to have to keep track of the plan usage...
> detect 50%, detect 5% fast climb, 10% fast climb, etc"

> "we need to avoid brainless loop and recursive chain that don't end"

---

## 1. Why It Exists

The March catastrophe: 15 bugs combined into a storm that burned
through the weekly quota in hours. Gateway duplication spawned
multiple instances. Void sessions consumed tokens producing nothing.
No detection, no automatic response, no circuit breakers.

The storm prevention system ensures this never happens again:

```
Normal operation
  ↓
Indicator fires (void_sessions > 50%)
  ↓
Confirmation window (sustained, not spike)
  ↓
Severity evaluated: WATCH → WARNING → STORM → CRITICAL
  ↓
Automatic graduated response:
  ├── WARNING → economic mode, dispatch ≤ 1, diagnostic snapshot
  ├── STORM → survival mode, dispatch = 0, alert PO
  └── CRITICAL → blackout mode, halt cycle, urgent alert PO
  ↓
De-escalation (slower than escalation)
  ↓
Post-incident report generated
```

---

## 2. How It Works

### 2.1 The 9 Indicators

```
┌─────────────────────────────────────────────────────────┐
│                 STORM INDICATORS                         │
│                                                          │
│  1. session_burst    — >10 sessions/min                  │
│  2. fast_climb       — budget climbing fast              │
│  3. void_sessions    — >50% void rate                    │
│  4. dispatch_storm   — high dispatch rate                │
│  5. cascade_depth    — nested dispatch chains            │
│  6. agent_thrashing  — agent failures                    │
│  7. error_storm      — error surge                       │
│  8. gateway_duplication — March root cause (IMMEDIATE)   │
│  9. context_pressure — context at 70%+ (from W8 telemetry)│
│                                                          │
│  Each indicator:                                         │
│    - Reported via report_indicator(name, value)           │
│    - Has a confirmation window (seconds before confirmed) │
│    - Must be SUSTAINED, not a one-time spike             │
│    - Exception: gateway_duplication is IMMEDIATE           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 The 5 Severity Levels

```
┌──────────┐
│  CLEAR   │ Normal operation. No indicators confirmed.
│          │ Response: nothing
└────┬─────┘
     │ 1 indicator confirmed
     ▼
┌──────────┐
│  WATCH   │ Monitoring. Something anomalous.
│          │ Response: log note
└────┬─────┘
     │ 2+ indicators confirmed
     ▼
┌──────────┐
│ WARNING  │ Fleet is under pressure.
│          │ Response: economic mode, dispatch ≤ 1, diagnostic snapshot
│          │ Alert: IRC #alerts
└────┬─────┘
     │ 3+ indicators OR critical indicator
     ▼
┌──────────┐
│  STORM   │ Fleet is in trouble.
│          │ Response: survival mode, dispatch = 0
│          │ Alert: IRC #alerts + ntfy PO
└────┬─────┘
     │ Cascade detected OR gateway duplication
     ▼
┌──────────┐
│ CRITICAL │ Fleet emergency.
│          │ Response: blackout mode, HALT cycle
│          │ Alert: IRC #alerts + ntfy PO URGENT
└──────────┘
```

### 2.3 Storm → Budget Forcing (W3 Wiring)

```python
STORM_BUDGET_FORCING = {
    StormSeverity.CRITICAL: "blackout",   # $0/day, fleet frozen
    StormSeverity.STORM: "survival",      # $1/day, LocalAI only
    StormSeverity.WARNING: "economic",    # $10/day, sonnet only
}
# Validated against budget_modes.MODE_ORDER at import time
```

### 2.4 Circuit Breakers

Per-agent and per-backend circuit breakers (state machine):

```
CLOSED ──(failures ≥ 3)──► OPEN ──(cooldown)──► HALF_OPEN ──(success)──► CLOSED
                                                       │
                                                       └──(failure)──► OPEN
                                                          (cooldown doubles)

Configuration:
  failure_threshold: 3
  agent cooldown: 300s (5 min)
  backend cooldown: 120s (2 min)
  cooldown_multiplier: 2.0 (doubles on repeated trips)
  max_cooldown: 3600s (1 hour)
```

Used by backend_router to skip backends with open breakers → fallback.

### 2.5 Diagnostic Snapshots

Captured on WARNING+ severity:

```python
StormDiagnostic:
    severity: str           # current severity level
    indicators: list[str]   # active confirmed indicators
    active_sessions: int    # current session count
    sessions_last_hour: int
    dispatches_last_hour: int
    void_session_pct: float
    agent_states: dict      # per-agent status
    error_count_last_20: int
    budget_mode: str        # current budget mode
    timestamp: float
```

Persisted to disk in `state/diagnostics/` (50-file cap, oldest deleted).

### 2.6 Post-Incident Reports

Generated when storm ends (severity drops from WARNING+ to CLEAR/WATCH):

```
IncidentReport:
    peak_severity, started_at, ended_at, duration_seconds
    indicators (what triggered)
    root_cause (if identifiable)
    responses (timeline of automatic actions)
    budget_mode_before → budget_mode_after
    estimated_cost_usd
    void_sessions / total_sessions
    prevention_recommendations
```

Posted to board memory tagged `[storm, incident, postmortem]`.

---

## 3. File Map

```
fleet/core/
├── storm_monitor.py     9 indicators, severity evaluation, circuit breakers (417 lines)
├── storm_integration.py Storm→budget forcing, event tracking, response logic (334 lines)
├── storm_analytics.py   Historical storm analysis, frequency, cost trends  (249 lines)
└── incident_report.py   Post-incident report generation                    (440 lines)
```

Total: **1440 lines** across 4 modules.

---

## 4. Per-File Documentation

### 4.1 `storm_monitor.py` — Detection Engine (417 lines)

#### Enums & Constants

| Name | Type | Value |
|------|------|-------|
| `StormSeverity` | Enum | CLEAR, WATCH, WARNING, STORM, CRITICAL |
| `CONFIRMATION_SECONDS` | dict | Per-indicator confirmation window (60-300s, gateway_duplication=0 immediate) |

#### Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `StormIndicator` | 56-67 | name, value, detected_at, confirmed bool |
| `StormDiagnostic` | 73-114 | Snapshot: severity, indicators, sessions, dispatches, void rate, agents, errors, budget mode |
| `CircuitBreaker` | 121-165 | State machine: CLOSED→OPEN→HALF_OPEN→CLOSED. failure_threshold=3, cooldown with multiplier. Methods: check(), record_success(), record_failure(). |
| `StormMonitor` | 208-417 | Main engine: report_indicator(), report_session(), report_dispatch(), report_error(), evaluate() → severity, capture_diagnostic(). Agent + backend breaker management. |

#### Key Functions on StormMonitor

| Method | Lines | What It Does |
|--------|-------|-------------|
| `report_indicator(name, value)` | 228-242 | Report an indicator. Confirm if past confirmation window. |
| `report_session(void)` | 248-269 | Track session for burst detection and void rate. |
| `evaluate()` | — | Count confirmed indicators → map to severity level. |
| `capture_diagnostic(budget_mode)` | 388-403 | Snapshot current state to StormDiagnostic. |
| `get_agent_breaker(name)` | 371-374 | Get/create per-agent circuit breaker. |
| `get_backend_breaker(name)` | 376-384 | Get/create per-backend circuit breaker. |

### 4.2 `storm_integration.py` — Orchestrator Integration (334 lines)

#### Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `StormResponse` | 27-55 | What orchestrator should do: severity, max_dispatch, force_budget_mode, halt_cycle, should_alert_po/irc, alert_message, notes. |
| `StormEventTracker` | 121-265 | Tracks active/completed storm events. Methods: process_cycle(), get_active_event(), get_completed_incidents(), force_close(). |

#### Key Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `evaluate_storm_response(monitor, current_budget, current_max_dispatch)` | 58-115 | Evaluate severity → build StormResponse. CRITICAL=halt+blackout. STORM=survival+0 dispatch. WARNING=economic+1 dispatch. Uses STORM_BUDGET_FORCING validated against budget_modes.MODE_ORDER. |

### 4.3 `storm_analytics.py` — Historical Analysis (249 lines)

| Class | Lines | Purpose |
|-------|-------|---------|
| `StormRecord` | 27-74 | Historical storm for analytics: severity, duration, cost, indicators, void rate, response time. `from_report()` factory. |
| `StormAnalytics` | 80-249 | Engine: record(), severity_distribution(), indicator_frequency(), duration_stats(), response_time_analysis(), cost_analysis(), void_rate_analysis(), summary(), format_report(). |

### 4.4 `incident_report.py` — Post-Incident (440 lines)

| Class | Lines | Purpose |
|-------|-------|---------|
| `ResponseEntry` | 27-39 | Timeline entry: timestamp, action, detail. |
| `IncidentReport` | 46-80 | Full report: severity, timing, indicators, root_cause, responses, cost, void sessions, prevention recommendations. |
| `StormEvent` | — | Tracks a storm from start to end: peak_severity, indicators_over_time, responses_applied. |

---

## 5. Dependency Graph

```
storm_monitor.py         ← standalone (time, datetime, dataclasses, enum)
    ↑
storm_integration.py     ← imports StormMonitor, StormSeverity, severity_index
                            imports IncidentReport, StormEvent
                            imports budget_modes.MODE_ORDER (W3 wiring)
    ↑
storm_analytics.py       ← imports IncidentReport
    ↑
incident_report.py       ← imports severity_index from storm_monitor (optional)
```

### External Connections (W3 Wiring)

```python
# storm_integration.py
from fleet.core.budget_modes import MODE_ORDER

STORM_BUDGET_FORCING = {
    StormSeverity.CRITICAL: "blackout",
    StormSeverity.STORM: "survival",
    StormSeverity.WARNING: "economic",
}
# Validated at import: assert mode in MODE_ORDER for each
```

---

## 6. Consumers

| Layer | Module | What It Imports | How It Uses It |
|-------|--------|----------------|---------------|
| **Orchestrator** | `orchestrator.py` | `StormMonitor, StormSeverity, severity_index` | Pre-check every cycle: evaluate severity → gate dispatch. Diagnostic snapshot on WARNING+. |
| **Backend Router** | `backend_router.py` | `StormMonitor` (TYPE_CHECKING) | `_apply_circuit_breakers()`: check backend breaker → fallback if open. |
| **Session Telemetry** | `session_telemetry.py` | — (indirect) | `to_storm_indicators()` produces context_pressure, quota_pressure indicators fed to storm_monitor. |
| **Gateway Guard** | `gateway_guard.py` | — (indirect) | Gateway duplication check feeds storm indicator. |

---

## 7. Design Decisions

### Why confirmation windows, not immediate detection?

A single high reading is noise. Two readings 60 seconds apart is
a pattern. Confirmation windows prevent false positives from
one-time spikes (e.g., legitimate burst of task completions).
Exception: gateway_duplication is immediate (March root cause).

### Why 5 severity levels, not 3?

CLEAR and WATCH add nuance below WARNING. WATCH means "something
anomalous but not yet alarming" — the system monitors but doesn't
act. This prevents premature budget forcing from a single indicator.
STORM vs CRITICAL differentiates "pause dispatch" from "halt the
entire cycle" — important operational distinction.

### Why de-escalation slower than escalation?

Escalation should be fast (detect and respond quickly). De-escalation
should be slow (make sure the storm is truly over before resuming).
If de-escalation were fast, the system would oscillate between
WARNING and CLEAR, constantly switching budget modes.

### Why per-agent AND per-backend circuit breakers?

Agent breakers catch one sick agent without affecting others.
Backend breakers catch a failing service (LocalAI down) without
blaming individual agents. Different granularity for different
failure modes.

### Why diagnostic snapshots to disk?

Diagnostics must survive restarts. If the storm causes a crash,
the snapshot is already on disk. The 50-file cap prevents filling
the filesystem. File format is JSON for easy inspection.

### Why separate storm_integration from storm_monitor?

storm_monitor is pure detection (no side effects). storm_integration
is pure response (no detection). Separation means: you can test
detection without triggering responses, and you can test response
logic without needing real indicators. The orchestrator calls both.

---

## 8. Storm Response Flow (End-to-End)

```
Orchestrator cycle starts
  ↓
storm_monitor.evaluate() → severity
  ↓
If WARNING+:
  ├── capture_diagnostic(budget_mode) → save to disk
  └── evaluate_storm_response(monitor, budget, dispatch)
       ↓
       StormResponse:
         severity=WARNING
         force_budget_mode="economic"
         max_dispatch=1
         should_alert_irc=True
  ↓
Orchestrator applies response:
  ├── config["max_dispatch_per_cycle"] = 1
  ├── IRC: "[storm] WARNING: ..."
  └── Continue cycle with limited dispatch
  ↓
If STORM:
  ├── config["max_dispatch_per_cycle"] = 0
  ├── IRC + ntfy PO
  └── Continue cycle (monitoring only)
  ↓
If CRITICAL:
  ├── IRC + ntfy PO URGENT
  └── return state (HALT — no further steps)
  ↓
Storm ends (indicators clear, severity drops)
  ↓
StormEventTracker.process_cycle() detects end
  ↓
Generate IncidentReport from StormEvent
  ↓
Post to board memory: [storm, incident, postmortem]
  ↓
StormAnalytics records for trend analysis
```

---

## 9. Data Shapes

### StormResponse

```python
StormResponse(
    severity=StormSeverity.WARNING,
    max_dispatch=1,
    force_budget_mode="economic",
    should_capture_diagnostic=True,
    should_alert_irc=True,
    should_alert_po=False,
    alert_message="WARNING: Storm: WARNING | Indicators: void_sessions(62%), fast_climb(8%/5min)",
    halt_cycle=False,
    notes=["STORM WARNING: dispatch limited to 1"],
)
```

### CircuitBreaker State

```python
CircuitBreaker(
    state="OPEN",
    failure_threshold=3,
    consecutive_failures=3,
    cooldown_seconds=300.0,
    cooldown_multiplier=2.0,
    last_trip_time=1711900000.0,
    trip_count=2,
    max_cooldown=3600.0,
)
```

### IncidentReport

```python
IncidentReport(
    incident_id="storm-2026-03-31-001",
    peak_severity="STORM",
    started_at=1711899000.0,
    ended_at=1711902600.0,
    duration_seconds=3600.0,
    indicators=["void_sessions:62%", "fast_climb:8%/5min", "session_burst:15/min"],
    root_cause="Gateway duplication spawned 3 instances",
    responses=[
        ResponseEntry(timestamp=..., action="force_economic", detail="WARNING detected"),
        ResponseEntry(timestamp=..., action="force_survival", detail="STORM escalation"),
    ],
    budget_mode_before="standard",
    budget_mode_after="survival",
    estimated_cost_usd=45.20,
    void_sessions=42,
    total_sessions=68,
    void_session_pct=61.8,
    prevention_recommendations=[
        "Check gateway duplication before starting agents",
        "Lower void_sessions threshold from 50% to 40%",
    ],
)
```

---

## 10. What's Needed

### Integration Gaps

- **Storm analytics connected to budget analytics** — cost per storm
  should flow into per-mode cost comparisons
- **Session telemetry feeding indicators** — W8 adapter built,
  `to_storm_indicators()` produces context_pressure/quota_pressure,
  but not wired into orchestrator's storm_monitor.report_indicator()
- **De-escalation tuning** — currently same speed as escalation

### Missing Functionality

- **Post-incident auto-report** — IncidentReport structure exists,
  generation logic exists in StormEventTracker, but reports not
  automatically posted to board memory on storm end
- **Prevention recommendations engine** — currently manual text,
  could be rule-based (same root cause → same recommendation)

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_storm_monitor.py` | 32 | Indicators, severity, circuit breakers, diagnostics |
| `test_storm_integration.py` | 32 | Response logic, event tracking, budget forcing |
| `test_storm_analytics.py` | 26 | Storm records, frequency, duration, cost |
| **Total** | **90** | Core logic covered. Missing: end-to-end storm cycle |
