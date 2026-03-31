# Storm Prevention System — Automatic Graduated Response

## Severity: CRITICAL
## Status: DESIGN
## Created: 2026-03-31

An automatic graduated response system that detects, prevents, and recovers
from process storms, cost cascades, and runaway token drain. Not just
detection (which exists) but **prevention through automatic escalation of
protective measures**.

---

## Part 1: PO Requirements (Verbatim)

> "in situation like we just experience we really have to be ready to do
> multiple agent iteration where the validation and testing had to be
> challenged and challenged in order to really fix the bugs and meet the
> requirements."

> "we need to avoid brainless loop and recursive chain that don't end and
> infinite loop or trying to take a task or work on something blocked"

> "the fleet cp is also going to have to keep track of the plan usage in
> general and detect irregularities, detect 50%, detect 5% fast climb,
> 10% fast climb, etc, and 70% 80% and 90% and detect outage"

> "we need to be able to pause all the work or reduce the efforts and
> strategy like that strategic and driven by the user and circumstances"

---

## Part 2: What Happened — The March 2026 Catastrophe

### Root Causes (from catastrophic-usage-drain-investigation.md)

15 bugs combined to create a perfect storm:
1. Orchestrator called `_send_chat` directly → unlimited Claude sessions every 30s
2. Gateway had 22 duplicate agents → double heartbeat targets
3. Stale gateway processes → independent token drain
4. Module globals reset on restart → immediate triggering
5. No session rate limiting
6. No token budget awareness
7. Agent heartbeats called unnecessary tools
8. No cascade depth limit
9. No max-dispatch-per-cycle
10. Nested tool calls doubling token usage
11. Board 90% noise → expensive context loading
12. Gateway restart fired ALL heartbeats simultaneously
13. No fleet pause command
14. No outage/rate-limit detection
15. Review/heartbeat tasks consumed sessions to process

### What Was Built After (C0-C14)

| Fix | What It Does | Limitation |
|-----|-------------|------------|
| C0 | Reverted _send_chat calls | Prevents that specific bug, not the category |
| C1 | Cleaned duplicate agents | Manual cleanup, could recur |
| C3 | Fleet pause/resume | Manual — human must notice and act |
| C4 | Session rate limiter | Fixed threshold, doesn't adapt |
| C5 | Token budget monitor | Detects problems, doesn't auto-respond |
| C6 | Max dispatch per cycle (3) | Fixed limit, doesn't adapt to pressure |
| C7 | Cascade depth limit (3) | Fixed limit |
| C13 | Effort profiles | Manual selection, doesn't auto-transition |

**The gap:** Every fix is either **manual** (human must notice and act)
or **fixed threshold** (doesn't adapt to conditions). There is no
**automatic graduated response** that detects a storm forming and
progressively tightens controls before it becomes catastrophic.

---

## Part 3: Storm Detection

### Storm Indicators

| Indicator | How to Detect | Threshold |
|-----------|--------------|-----------|
| **Session burst** | Sessions/minute > 5x normal | Normal = 2/min, storm = 10/min |
| **Fast climb** | Budget % increase > 5% in 10 min | Already in budget_monitor.py |
| **Void sessions** | Sessions with no useful output > 50% | Track output-to-session ratio |
| **Dispatch storm** | Dispatches/cycle > max_dispatch × 2 | Should never exceed limit |
| **Cascade depth** | Task auto-creates task auto-creates task | Depth > 3 = cascade |
| **Agent thrashing** | Same agent woken > 3x in 30 min with no work | Heartbeat waste |
| **Error storm** | Error rate > 30% of operations | Failing silently, retrying |
| **Memory growth** | Process RSS > 2x baseline | Memory leak / unbounded state |
| **Gateway duplication** | Multiple gateway processes | Stale processes still running |

### Storm Severity Levels

| Level | Indicators Active | Response |
|-------|------------------|----------|
| **CLEAR** | 0 indicators | Normal operation |
| **WATCH** | 1 indicator | Log + monitor, no action yet |
| **WARNING** | 2 indicators | Reduce: drop to economic mode |
| **STORM** | 3+ indicators | Contain: drop to survival mode, alert PO |
| **CRITICAL** | Fast climb + session burst | Blackout: stop everything, alert PO urgently |

---

## Part 4: Automatic Graduated Response

### The Response Chain

```
CLEAR → normal operation
  ↓ (1 indicator triggers)
WATCH → log, increase monitoring frequency (30s → 15s)
  ↓ (2 indicators, or 1 persists > 5 min)
WARNING → force economic budget mode
        → reduce heartbeat intervals 2x
        → alert fleet-ops (IRC + ntfy)
        → start recording session traces
  ↓ (3+ indicators, or warning persists > 10 min)
STORM → force survival budget mode
      → disable all heartbeats except fleet-ops
      → max dispatch = 0 (no new work)
      → alert PO (ntfy URGENT)
      → dump diagnostic snapshot
  ↓ (fast climb + burst, or storm persists > 15 min)
CRITICAL → force blackout
         → kill all agent sessions
         → disable gateway heartbeats
         → alert PO (ntfy MAX PRIORITY + IRC)
         → write incident report
         → fleet requires manual restart (fleet resume)
```

### Auto-Recovery (De-escalation)

```
CRITICAL → (PO manually resumes) → STORM
  ↓ (indicators clear for 10 min)
STORM → WARNING
  ↓ (indicators clear for 15 min)
WARNING → WATCH
  ↓ (indicators clear for 30 min)
WATCH → CLEAR
```

**De-escalation is slower than escalation.** Getting worse is fast
(seconds to minutes). Getting better requires sustained stability
(minutes to hours). This prevents oscillation.

### No False Positives

Each indicator has a **confirmation window** before triggering:
- Session burst: sustained for > 60 seconds (not a momentary spike)
- Fast climb: confirmed by two readings 5 minutes apart
- Void sessions: rolling window of last 10 sessions
- Error storm: rolling window of last 20 operations

One bad reading doesn't trigger response. **Sustained anomaly** does.

---

## Part 5: Diagnostic Snapshot

When storm level reaches WARNING or above, the brain captures a
diagnostic snapshot:

```python
@dataclass
class StormDiagnostic:
    """Captured when storm conditions detected."""

    timestamp: str
    severity: str                    # watch/warning/storm/critical
    indicators: list[str]           # Which indicators are active
    budget_reading: QuotaReading    # Current budget state
    active_sessions: int            # How many agent sessions running
    sessions_last_hour: int         # Session count in last 60 min
    dispatches_last_hour: int       # Dispatch count in last 60 min
    void_session_pct: float         # % of sessions with no useful output
    gateway_process_count: int      # How many gateway processes running
    agent_states: dict              # Per-agent: state, last heartbeat, session count
    error_log: list[str]            # Last 20 errors
    budget_mode: str                # Current budget mode
    effort_profile: str             # Current effort profile
```

Snapshot is:
- Written to `logs/storm-diagnostics/` as JSON
- Posted to board memory with `[storm-diagnostic]` tag
- Sent to PO via ntfy with summary
- Available to fleet-ops for post-incident analysis

---

## Part 6: Circuit Breakers

### Per-Agent Circuit Breaker

Each agent has a circuit breaker that trips independently:

```
CLOSED (normal) → agent can receive work
    ↓ (3 void sessions in a row, or 2 errors in a row)
OPEN (tripped) → agent blocked from receiving work
    ↓ (cooldown: 5 minutes)
HALF-OPEN → allow ONE session to test
    ↓ (session produces useful work)
CLOSED → agent restored
    ↓ (session is void/error again)
OPEN → cooldown doubles (10 min, then 20 min, max 60 min)
```

### Per-Backend Circuit Breaker

Each backend (Claude, LocalAI, OpenRouter) has a circuit breaker:

```
CLOSED → backend receives requests
    ↓ (3 consecutive failures, or timeout)
OPEN → backend skipped, fallback used
    ↓ (cooldown: 2 minutes)
HALF-OPEN → route ONE request to test
    ↓ (success)
CLOSED
```

### Global Circuit Breaker

The fleet-wide kill switch:

```
CLOSED → fleet operates normally
    ↓ (storm level CRITICAL)
OPEN → everything stops
    ↓ (PO manually runs `fleet resume`)
CLOSED → fleet restarts with STORM-level protections
    ↓ (indicators clear for 30 min)
Normal operation
```

---

## Part 7: Integration with Existing Systems

### Budget Monitor Enhancement

`budget_monitor.py` gains storm awareness:

```python
class BudgetMonitor:
    def check_storm_indicators(self) -> list[str]:
        """Check for storm indicators from budget data.

        Returns list of active indicators.
        """
        indicators = []
        reading = self._last_reading
        if not reading:
            return indicators

        # Fast climb
        if len(self._history) >= 2:
            prev = self._history[-2]
            climb = reading.weekly_all_pct - prev.weekly_all_pct
            elapsed = (reading.timestamp - prev.timestamp).total_seconds()
            if climb >= 5 and elapsed < 600:
                indicators.append(f"fast_climb:{climb:.0f}%_in_{elapsed:.0f}s")

        # Absolute thresholds
        if reading.weekly_all_pct >= 90:
            indicators.append(f"budget_critical:{reading.weekly_all_pct:.0f}%")
        elif reading.weekly_all_pct >= 80:
            indicators.append(f"budget_high:{reading.weekly_all_pct:.0f}%")

        return indicators
```

### Orchestrator Enhancement

The orchestrator checks storm level at the START of every cycle:

```python
# In orchestrator cycle:
storm_level = storm_monitor.evaluate()
if storm_level == "CRITICAL":
    _execute_blackout()
    return  # stop cycle
if storm_level == "STORM":
    _force_survival_mode()
    state.max_dispatch = 0  # no new work
if storm_level == "WARNING":
    _force_economic_mode()
    state.max_dispatch = 1
```

### Gateway Enhancement

Gateway checks for stale processes on startup:

```python
# On gateway start:
existing = find_gateway_processes()
if len(existing) > 1:
    storm_monitor.report_indicator("gateway_duplication")
    kill_stale_gateways(keep_newest=True)
```

### Fleet-ops as Storm Responder

When storm level reaches WARNING:
- fleet-ops is the ONLY agent that remains active
- fleet-ops reads the diagnostic snapshot
- fleet-ops posts analysis to IRC #fleet
- fleet-ops recommends action (reduce effort, kill specific process, etc.)

---

## Part 8: Post-Incident Analysis

After every storm event (WARNING or above), the system generates a
**post-incident report**:

```markdown
## Storm Incident Report — 2026-03-31 14:23

### Severity: STORM
### Duration: 8 minutes (14:23 — 14:31)
### Cost Impact: ~$1.40 estimated

### Indicators
- session_burst: 12 sessions/min (normal: 2/min)
- void_sessions: 80% (8 of 10 sessions produced no work)

### Root Cause
Gateway restart fired 11 heartbeats simultaneously.
All agents had nothing to do → void sessions.

### Automatic Response
1. 14:23 — WATCH detected (session burst)
2. 14:24 — WARNING triggered (session burst + void sessions)
3. 14:24 — Budget mode forced to economic
4. 14:24 — Heartbeat intervals doubled
5. 14:26 — Void sessions continued → STORM
6. 14:26 — Budget mode forced to survival
7. 14:26 — All heartbeats disabled except fleet-ops
8. 14:26 — PO alerted via ntfy
9. 14:31 — Indicators cleared → de-escalation began

### Prevention
- Stagger gateway heartbeats after restart (existing fix C11)
- Reduce default heartbeat concurrency to max 3 simultaneous

### Labor Cost
- 10 void sessions × ~$0.14 each = ~$1.40 wasted
- Storm response: $0 (deterministic)
```

---

## Part 9: Milestones

### M-SP01: Storm Monitor Core
- Define storm indicators with thresholds
- Implement `StormMonitor` class with `evaluate()` method
- Severity levels: CLEAR/WATCH/WARNING/STORM/CRITICAL
- Confirmation windows (no false positives)
- Tests for every indicator and severity transition
- **Status:** ⏳ PENDING

### M-SP02: Automatic Graduated Response
- Response chain: WATCH → WARNING → STORM → CRITICAL
- Automatic budget mode forcing at each level
- Automatic heartbeat adjustment
- Automatic dispatch limiting
- Tests for escalation and de-escalation
- **Status:** ⏳ PENDING

### M-SP03: Diagnostic Snapshot
- `StormDiagnostic` data model
- Capture on WARNING and above
- Write to logs, board memory, ntfy
- Include: sessions, dispatches, errors, agent states, budget
- **Status:** ⏳ PENDING

### M-SP04: Per-Agent Circuit Breaker
- Circuit breaker per agent: CLOSED → OPEN → HALF-OPEN
- Void session detection triggers open
- Exponential backoff cooldown
- Tests for state transitions
- **Status:** ⏳ PENDING

### M-SP05: Per-Backend Circuit Breaker
- Circuit breaker per backend: Claude, LocalAI, OpenRouter
- Failure detection triggers open
- Fallback routing when backend circuit is open
- Tests for failover scenarios
- **Status:** ⏳ PENDING

### M-SP06: Gateway Duplication Detection
- On gateway startup: detect existing processes
- Kill stale gateways automatically
- Report indicator if duplicates found
- Script: `scripts/clean-gateways.sh`
- **Status:** ⏳ PENDING

### M-SP07: Post-Incident Report Generation
- Automatic report after every WARNING+ event
- Template: severity, duration, cost, indicators, response, prevention
- Posted to board memory, saved to logs
- fleet-ops reviews post-incident
- **Status:** ⏳ PENDING

### M-SP08: Orchestrator Storm Integration
- Storm check at start of every cycle
- Respect storm level for dispatch decisions
- Force budget mode transitions
- Record storm events in event bus
- **Status:** ⏳ PENDING

### M-SP09: Storm Analytics
- Track: storm frequency, duration, cost impact
- Track: which indicators trigger most often
- Track: time to detection, time to response
- Feed into prevention improvements
- Cross-ref: labor stamps provide cost data
- **Status:** ⏳ PENDING

---

## Part 10: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Budget Mode System | Storm response forces budget mode transitions |
| Labor Attribution | Labor stamps track cost during storms |
| Multi-Backend Router | Backend circuit breakers feed into routing decisions |
| Iterative Validation | Storms often caused by insufficiently validated fixes |
| Catastrophic Drain Investigation | This system prevents the category of problems found there |
| Effort Profiles | Storm response overrides effort profiles |
| Agent Lifecycle | Circuit breakers interact with agent sleep/wake |
| Fleet Elevation Doc 4 | The brain executes storm response (deterministic, zero cost) |
| Fleet Elevation Doc 23 | Agent lifecycle states change during storms |

---

## Part 11: Why This Matters

The March 2026 catastrophe happened because the fleet had only one
response to problems: **the human notices and kills processes**. By the
time the human noticed, 20% of the weekly budget was gone in 5 seconds.

With the storm prevention system:
- **5 seconds:** Session burst detected, WATCH triggered
- **65 seconds:** Sustained burst confirmed, WARNING triggered, economic mode forced
- **2-3 minutes:** If not improving, STORM triggered, survival mode forced
- **5 minutes:** If still not improving, CRITICAL triggered, blackout

Total cost of that 5-minute storm with prevention: ~$0.50 instead of 20%
of the weekly plan.

The storm prevention system is the fleet's **immune response at the
infrastructure level**. The doctor catches agent behavior problems.
The storm monitor catches infrastructure behavior problems. Together,
they protect the fleet from catastrophic failure.

> The most expensive storm is the one nobody detects until it's over.
> The cheapest storm is the one that triggers automatic protection in
> the first 60 seconds.