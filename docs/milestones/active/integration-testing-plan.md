# Integration Testing Plan — Strategic Milestones

**Date:** 2026-03-31
**Status:** PLAN — pending PO approval before execution

---

## 1. Current State

### What We Have
- **47 milestones** implemented across 6 systems
- **731 unit tests** in 26 test files, all passing
- **1797 total tests** across the full fleet (including pre-existing systems)
- **5 wired cross-system connections** (via imports in `backend_router.py`, `storm_integration.py`)

### What We're Missing
- **7 cross-system connections** specified in design docs but not implemented
- **0 cross-system integration tests** — all existing "integration" tests are intra-system
- **No end-to-end flow validation** for the 4 critical paths

### The Problem
Each system works in isolation. The design docs specify how they connect, but the code doesn't implement those connections yet. Integration tests will fail until we wire the connections — so this is two phases of work, not one.

---

## 2. Cross-System Wiring Gaps

### Currently Wired (5)

| From | To | Via |
|------|-----|-----|
| Budget Modes | Backend Router | `backend_router.py` imports `budget_modes` |
| Labor Stamp | Backend Router | `backend_router.py` imports `labor_stamp` |
| Storm Monitor | Storm Integration | `storm_integration.py` imports `storm_monitor` |
| Incident Report | Storm Analytics | `storm_analytics.py` imports `incident_report` |
| Challenge | Challenge Protocol | `challenge_protocol.py` imports `challenge`, `challenge_automated` |

### Missing Connections (7)

| # | From | To | Design Doc Reference | What's Needed |
|---|------|-----|---------------------|---------------|
| W1 | **Budget Modes** | **Challenge Engine** | `iterative-validation` Part 7: Budget-Aware Challenges | `challenge_deferred.py` should import `budget_modes` instead of hardcoding constants |
| W2 | **Labor Stamp** | **Challenge Engine** | `iterative-validation` Part 7: `challenge_skipped: true` in stamp | `labor_stamp.py` needs challenge fields; challenge engine writes to stamp |
| W3 | **Storm Integration** | **Budget Modes** | `storm-prevention` Part 7: CRITICAL→blackout, STORM→survival | `storm_integration.py` should import `budget_modes` to force mode transitions |
| W4 | **Shadow Routing** | **Model Promotion** | `model-upgrade-path`: shadow results feed promotion | `model_promotion.py` should consume `ShadowRouter` reports |
| W5 | **Backend Health** | **Backend Router** | `multi-backend-routing`: health determines routing options | `backend_router.py` should import `backend_health` to check before routing |
| W6 | **Model Promotion** | **Backend Router** | `model-upgrade-path`: promoted model enters routing table | Router should read from promotion manager's active model |
| W7 | **Tier Progression** | **Codex Review** | `multi-backend-routing` M-BR06: tier triggers review | `codex_review.py` should import `tier_progression` for should_trigger logic |
| W8 | **Session Telemetry** | **All Systems** | `context-window-awareness-and-control.md` | New adapter module parses Claude Code session JSON and distributes real values to existing systems |

### W8 Detail: Session Telemetry Adapter

Claude Code exposes JSON session data on every turn (visible to IDE/statusline). This data contains **real values** that our modules currently estimate or leave manual:

| Session JSON Field | Target Module | Existing Intake | Currently |
|---|---|---|---|
| `cost.total_cost_usd` | `CostTicker.add_cost()` | `add_cost(cost_usd: float)` | Estimated |
| `cost.total_duration_ms` | `LaborStamp.duration_seconds` | `assemble_stamp(duration_seconds=)` | Estimated |
| `cost.total_lines_added` | `LaborStamp` | **No field yet** | N/A |
| `cost.total_lines_removed` | `LaborStamp` | **No field yet** | N/A |
| `cost.total_api_duration_ms` | `ClaudeHealth.latency_ms` | `latency_ms` field | Manual |
| `rate_limits.five_hour.used_percentage` | `ClaudeHealth.quota_used_pct` | `quota_used_pct` field | Manual |
| `rate_limits.seven_day.used_percentage` | `ClaudeHealth` | **No field yet** | N/A |
| `context_window.used_percentage` | `StormMonitor.report_indicator()` | `report_indicator(name, value)` | Not tracked |
| `context_window.context_window_size` | `ClaudeHealth` | **No field yet** | N/A |
| `context_window.current_usage.cache_read_input_tokens` | `LaborStamp` | **No field yet** | N/A |
| `model.id` | `LaborStamp.model` | `model` field | Already exists |

**Implementation:** One new module `session_telemetry.py` with:
- `SessionSnapshot` dataclass — typed parse of the JSON
- `ingest(data: dict)` → returns `SessionSnapshot`
- Helper methods to feed values to existing systems:
  - `to_labor_fields() → dict` — fields to merge into LaborStamp assembly
  - `to_claude_health() → dict` — fields to update ClaudeHealth
  - `to_storm_indicators() → list[tuple[str, str]]` — context pressure indicators
  - `to_cost_event() → float` — cost delta for CostTicker

**New fields needed on existing modules:**
- `LaborStamp`: `lines_added: int = 0`, `lines_removed: int = 0`, `cache_read_tokens: int = 0`
- `ClaudeHealth`: `weekly_quota_used_pct: float = 0.0`, `context_window_size: int = 0`

**Scope:** ~150 lines for adapter, ~30 lines field additions across 2 modules.

---

## 3. Integration Phases

### Phase 1: Wire Missing Connections

Before writing integration tests, the systems must actually connect. Each connection is a small, focused change — add an import, add a function call, add a field. No new systems, except the session telemetry adapter (W8).

**Priority order** (by flow criticality):

| Step | Connection | Complexity | Why First |
|------|-----------|------------|-----------|
| 1a | W1: Budget → Challenge | Low | Replace hardcoded constants with import, DRY fix |
| 1b | W2: Labor Stamp ↔ Challenge | Medium | Stamp needs `challenge_skipped` field, challenge writes to stamp |
| 1c | W3: Storm → Budget | Medium | Storm forcing budget mode is core safety behavior |
| 1d | W5: Backend Health → Router | Medium | Health-aware routing is the point of backend_health.py |
| 1e | W4: Shadow → Promotion | Low | Promotion.promote() should accept shadow report data |
| 1f | W6: Promotion → Router | Low | Router reads promoted model from promotion manager |
| 1g | W7: Tier → Codex Review | Low | Review trigger reads tier from tier_progression |
| 1h | W8: Session Telemetry | Medium | New adapter + field additions to LaborStamp and ClaudeHealth |

**Estimated scope:** ~400-500 lines of connection code. One new module (`session_telemetry.py`), field additions to two existing modules.

### Phase 2: Cross-System Integration Tests

Once wired, test the 4 critical end-to-end flows.

---

## 4. The Four Critical Flows

### Flow 1: Task Dispatch (Budget → Router → Stamp → Challenge)

```
Order arrives with budget_mode="economic"
  → budget_modes constrains allowed models (no opus)
  → backend_router selects cheapest capable backend
  → labor_stamp records: model, backend, cost, tier
  → challenge_engine checks: budget_mode="economic" → automated only
  → challenge runs (or defers if frugal/survival)
  → stamp updated: challenge_passed=true OR challenge_skipped=true
```

**Tests needed:**
- `test_dispatch_blitz` — opus allowed, full challenge, stamp records everything
- `test_dispatch_economic` — opus blocked, automated challenge only
- `test_dispatch_frugal` — free backends only, challenge deferred, stamp marks skipped
- `test_dispatch_survival` — LocalAI only, no challenge, stamp marks skipped with reason
- `test_dispatch_blackout` — no dispatch at all

### Flow 2: Model Upgrade (Shadow → Compare → Promote → Route)

```
Shadow router runs task on production + candidate
  → ShadowResult records agreement, pass rates
  → ShadowRouter.format_report() → READY verdict at 80%
  → PO approves promotion
  → model_promotion.promote() captures shadow data
  → tier_progression updates model tier (trainee → trainee-validated)
  → backend_router picks up promoted model for future routing
  → promotion_health monitors post-promotion approval rates
```

**Tests needed:**
- `test_upgrade_full_cycle` — shadow → ready → promote → tier advances → router uses new model
- `test_upgrade_not_ready` — shadow results below 80%, no promotion
- `test_upgrade_rollback` — post-promotion health degrades → rollback → router reverts
- `test_upgrade_tier_gate` — model can't skip tiers (trainee can't go to expert)

### Flow 3: Storm Response (Indicators → Severity → Breakers → Budget → Router)

```
Storm indicators accumulate (void sessions, budget climb, dispatch failures)
  → storm_monitor.evaluate() → severity=WARNING
  → storm_integration forces budget_mode → "economic"
  → backend_router respects circuit breakers (open = skip backend)
  → dispatch limited to 1 concurrent
  → severity escalates to STORM → budget forced to "survival"
  → severity escalates to CRITICAL → budget forced to "blackout"
  → cooldown → breakers reset → budget relaxes → recovery
```

**Tests needed:**
- `test_storm_warning_forces_economic` — WARNING → budget=economic, dispatch=1
- `test_storm_escalation` — WARNING → STORM → CRITICAL progression, budget follows
- `test_storm_circuit_breaker_routing` — open breaker → router skips backend → fallback
- `test_storm_recovery_cycle` — CRITICAL → cooldown → HALF_OPEN → success → CLOSED → budget relaxes
- `test_storm_cost_tracking` — storm analytics records cost during incident

### Flow 4: Cost Control (Budget Envelope → Mode Transition → Routing Change)

```
CostTicker tracks daily spend
  → cost_used_pct crosses 80% → auto-transition to economic
  → cost_used_pct crosses 95% → auto-transition to survival
  → budget_constraints.py blocks expensive dispatches
  → router shifts to free backends (LocalAI, OpenRouter)
  → challenge depth reduces (automated only → skip)
  → labor stamps show cost reduction in per-mode breakdown
```

**Tests needed:**
- `test_cost_pressure_transition` — spending triggers automatic mode downgrade
- `test_cost_recovery_transition` — daily reset → mode can upgrade again
- `test_cost_override` — PO override keeps blitz despite pressure
- `test_cost_stamps` — labor analytics shows cost distribution by budget mode

### Flow 5: Session Telemetry (Session JSON → All Systems)

```
Claude Code session produces JSON with real metrics
  → SessionTelemetry.ingest(json_data) parses into SessionSnapshot
  → to_labor_fields() → LaborStamp gets real duration, lines, cost, cache stats
  → to_claude_health() → ClaudeHealth gets live quota %, latency, context window size
  → to_storm_indicators() → StormMonitor gets context_pressure indicator
  → to_cost_event() → CostTicker gets real cost delta
  → Cross-check: context at 90% + quota at 80% → storm WARNING + budget pressure
```

**Tests needed:**
- `test_telemetry_ingest` — parse real session JSON, verify all fields extracted
- `test_telemetry_to_labor` — session data populates LaborStamp with real values instead of estimates
- `test_telemetry_to_health` — session quota feeds ClaudeHealth, triggers quota_warning at 80%
- `test_telemetry_context_storm` — context at 90% triggers storm indicator, combined with quota pressure escalates severity
- `test_telemetry_cost_feed` — session cost feeds CostTicker, crosses envelope threshold, triggers mode transition

---

## 5. Test File Structure

```
fleet/tests/integration/
  __init__.py
  test_flow_dispatch.py       # Flow 1: 5 tests
  test_flow_model_upgrade.py  # Flow 2: 4 tests
  test_flow_storm_response.py # Flow 3: 5 tests
  test_flow_cost_control.py   # Flow 4: 4 tests
  test_flow_telemetry.py      # Flow 5: 5 tests
  conftest.py                 # Shared fixtures (mock task, mock order, mock stamps, mock session JSON)
```

**Estimated:** 23 integration tests across 5 files.

These are **true cross-system tests** — each test imports from 3+ systems and verifies the full flow. They are NOT duplicates of existing unit tests.

---

## 6. Relationship to Context Management

This integration work should be done with context efficiency in mind:

1. **Phase 1 (wiring)** — small, focused changes. Good for constrained context.
2. **Phase 2 (tests)** — needs to see multiple modules simultaneously. Better with 1M context.
3. **Each flow is an independent sprint** — can `/clear` between flows.
4. **`.claudeignore` should be in place first** — reduces context waste during implementation.

### Recommended execution order:
1. Apply `.claudeignore` files — **DONE**
2. Configure statusline for context visibility — **DONE** (IaC: `~/.claude/statusline.sh` + settings.json)
3. Wire Phase 1 connections (1a-1h) — W1-W7 glue code + W8 session_telemetry.py
4. Write Phase 2 integration tests — better in fresh 1M session, one flow per sprint

---

## 7. What This Does NOT Cover

- **Runtime integration** — these tests verify logic flow, not actual HTTP calls to LocalAI/Claude
- **UI integration** — TSX patches are tested separately
- **Fleet-level orchestration** — how the orchestrator calls these systems in production
- **AICP ↔ Fleet integration** — router_unification.py (M-BR08) is FUTURE

These are appropriate follow-up milestones, not part of this plan.

---

## 8. Success Criteria

- [x] `.claudeignore` files in place for 3 of 4 projects (AICP, Fleet, DSPD)
- [x] Statusline configured via IaC (`~/.claude/statusline.sh` + settings.json)
- [x] All 8 missing connections wired — W1-W7 glue code + W8 session_telemetry.py (Phase 1)
- [x] 23 cross-system integration tests written and passing across 5 flows (Phase 2)
- [x] Zero regressions in existing 744 unit tests (was 731, +30 session telemetry, -17 overlap)
- [x] New fields on LaborStamp (lines_added, lines_removed, cache_read_tokens, challenge_skipped, challenge_skip_reason)
- [x] New fields on ClaudeHealth (weekly_quota_used_pct, context_window_size, weekly_quota_warning, weekly_quota_critical)
- [x] Context pressure as a storm indicator (via session_telemetry.to_storm_indicators)
- [ ] `.claudeignore` for NNRT (4th project)
- [x] Document updated with actual results (2026-03-31)
