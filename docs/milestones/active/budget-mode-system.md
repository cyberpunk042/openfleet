# Budget Mode System for OCMC Orders

## Severity: STRATEGIC
## Status: DESIGN
## Created: 2026-03-31

A graduated budget mode system injected into OCMC orders that controls
spending rate, model selection, task frequency, and backend routing.
Not a reactive alert system — a **proactive strategy** that shapes how
the fleet operates before costs accumulate.

---

## Part 1: PO Requirements (Verbatim)

> "I am wondering if there is a new budgetMode (e.g. aggressive... whatever
> A, B... economic..) to inject into ocmc order to fine-tune the spending
> as speed / frequency of tasks / s and whatnot. The use of free open
> claude models..."

> "I know some endpoint are route through a loadbalancer of free models
> with autorouting to the one available to the level you want if its not
> too busy."

> "we need to evolve and make things observable and clean and scalable."

---

## Part 2: Current State vs. What's Needed

### What Exists Today

| Component | What It Does | Limitation |
|-----------|-------------|------------|
| `effort_profiles.py` | 4 profiles: full/conservative/minimal/paused | Static, fleet-wide, not per-order |
| `budget_monitor.py` | Reads Claude quota %, fast-climb detection | Reactive — detects problems, doesn't prevent them |
| `model_selection.py` | Picks opus/sonnet by task complexity | No cost awareness, no free-tier routing |
| Orchestrator | Checks `budget_monitor.check_quota()` before dispatch | Binary: safe or pause. No gradations. |

### What's Missing

1. **Per-order budget mode** — each OCMC order should carry a budget strategy
2. **Graduated response** — not just "go" or "stop" but 5+ levels of intensity
3. **Free-tier routing** — use OpenRouter free models or LocalAI before Claude
4. **Cost envelope** — per-order spending limit, not just global quota %
5. **Automatic escalation/de-escalation** — budget mode adjusts based on spend rate
6. **Budget mode in OCMC order schema** — first-class field, not afterthought

---

## Part 3: Budget Mode Design

### The Modes

| Mode | Speed | Models Allowed | Backends | Max Dispatch/Cycle | Heartbeat Interval | Use When |
|------|-------|----------------|----------|-------------------|-------------------|----------|
| **blitz** | Maximum | opus + sonnet | Claude only | 5 | 15m | Sprint deadline, critical bugs, time-sensitive |
| **standard** | Normal | opus (complex) + sonnet (rest) | Claude + LocalAI | 2 | 30m | Normal operation, balanced cost/speed |
| **economic** | Moderate | sonnet only + LocalAI | Claude sonnet + LocalAI | 1 | 60m | Budget-conscious, steady work |
| **frugal** | Slow | sonnet (complex only) + LocalAI + free | Claude sonnet + LocalAI + OpenRouter free | 1 | 120m | Low budget, non-urgent work |
| **survival** | Minimal | LocalAI + free only | LocalAI + OpenRouter free | 1 per hour | 480m | Near-zero Claude spend, keep fleet alive |
| **blackout** | Zero | None | None | 0 | disabled | Budget exhausted, fleet frozen |

### Mode Inheritance

```
PO sets global mode → fleet.yaml / fleet effort <mode>
   ↓
OCMC order can override → order.budget_mode = "economic"
   ↓
Task inherits order mode unless overridden → task.custom_fields.budget_mode
   ↓
Brain respects the most restrictive mode in the chain
```

### Mode Schema (OCMC Order)

```yaml
# In OCMC order / MC task creation:
budget_mode: "economic"        # Required — controls spending strategy
cost_envelope_usd: 5.00        # Optional — max spend for this order
cost_so_far_usd: 0.00          # Tracked — accumulated cost (from labor stamps)
escalation_allowed: true       # Can the brain escalate mode if task is stuck?
```

### Automatic Mode Transitions

The brain can **de-escalate** (reduce spending) automatically based on
budget pressure. It can **escalate** (increase spending) only if
`escalation_allowed: true` on the order.

```
Budget Pressure Triggers:
  weekly_quota >= 70%  → force economic (if currently standard or blitz)
  weekly_quota >= 80%  → force frugal
  weekly_quota >= 90%  → force survival
  weekly_quota >= 95%  → force blackout
  fast_climb detected  → drop one level immediately

Cost Envelope Triggers:
  order cost >= 50% of envelope → warn PO
  order cost >= 80% of envelope → force economic
  order cost >= 100% of envelope → freeze order, notify PO

Escalation (if allowed):
  task blocked > 2 cycles with LocalAI → escalate to Claude sonnet
  task blocked > 5 cycles with sonnet → escalate to opus
  Always: cheapest backend that can handle the task wins
```

---

## Part 4: Integration with Model Selection

### Current Flow

```
task → model_selection.py → ModelConfig(opus, high) → dispatch
```

### New Flow

```
task → budget_mode check → allowed models filter → model_selection.py
   → ModelConfig(sonnet, medium) → backend_router → (Claude | LocalAI | OpenRouter)
   → dispatch → labor stamp records what was used
```

The budget mode **constrains** model selection. If the mode is `economic`,
`model_selection.py` cannot return opus regardless of task complexity.
The selection still considers story points and task type, but within the
bounds of what the mode allows.

```python
def constrain_model_by_budget(
    config: ModelConfig,
    budget_mode: str,
) -> ModelConfig:
    """Constrain model selection to what the budget mode allows."""
    mode = BUDGET_MODES[budget_mode]

    if config.model not in mode.allowed_models:
        # Downgrade to best allowed model
        fallback = mode.allowed_models[-1]  # Last = most capable allowed
        return ModelConfig(
            model=fallback,
            effort=min(config.effort, mode.max_effort),
            reason=f"{config.reason} [constrained by {budget_mode} mode]",
        )

    return config
```

---

## Part 5: Integration with Multi-Backend Router

When budget mode is `frugal` or `survival`, the router considers free
backends first:

```
frugal mode routing priority:
  1. Can LocalAI handle this? (structured response, heartbeat, simple review)
     YES → route to LocalAI (cost: $0)
  2. Can OpenRouter free tier handle this? (general reasoning, medium complexity)
     YES → route to OpenRouter free (cost: $0)
  3. Needs Claude? → sonnet only, medium effort
     Route to Claude sonnet (cost: standard)

survival mode routing priority:
  1. Can this be done without an LLM? (direct MCP call, template response)
     YES → route to direct/no-LLM (cost: $0)
  2. Can LocalAI handle this?
     YES → route to LocalAI (cost: $0)
  3. Can OpenRouter free tier handle this?
     YES → route to OpenRouter free (cost: $0)
  4. Absolutely must use Claude? → only fleet-ops for critical monitoring
     Route to Claude sonnet, low effort (cost: minimal)
```

---

## Part 6: Effort Profile Evolution

Current effort profiles (full/conservative/minimal/paused) become
**presets** that map to budget modes:

| Old Profile | Maps To | Notes |
|-------------|---------|-------|
| full | blitz or standard | PO chooses which |
| conservative | economic | Same intent |
| minimal | survival | Same intent |
| paused | blackout | Same intent |

New budget modes are **more granular** and carry additional fields
(cost envelope, escalation policy). The old profiles remain as
convenience aliases.

---

## Part 7: OCMC Order Schema Update

```python
@dataclass
class OrderBudgetConfig:
    """Budget configuration for an OCMC order."""

    mode: str = "standard"               # blitz/standard/economic/frugal/survival/blackout
    cost_envelope_usd: float | None = None  # Max spend for this order
    cost_spent_usd: float = 0.0          # Accumulated from labor stamps
    escalation_allowed: bool = True      # Can brain escalate mode?
    model_ceiling: str | None = None     # Hard cap: e.g., "sonnet" means no opus ever
    backend_preference: str | None = None # "localai-first", "claude-only", etc.
    max_iterations: int = 3              # Max retry attempts before human escalation
```

This config is:
- Set by PO when creating orders (or defaults from fleet.yaml)
- Readable by the brain at dispatch time
- Updated by the brain when auto-de-escalating
- Reported in labor stamps (so cost_spent_usd is accurate)

---

## Part 8: Milestones

### M-BM01: BudgetMode Data Model
- Define `BudgetMode` enum and `BUDGET_MODES` registry
- Define `OrderBudgetConfig` dataclass
- Add budget_mode field to OCMC order schema
- Add to task custom fields
- Tests for mode constraints
- **Status:** ⏳ PENDING

### M-BM02: Mode-Constrained Model Selection
- Modify `model_selection.py` to accept budget mode
- Implement `constrain_model_by_budget()`
- Ensure opus is blocked in economic/frugal/survival modes
- Tests for every mode × model combination
- **Status:** ⏳ PENDING

### M-BM03: Automatic Mode Transitions
- Brain checks budget pressure every cycle
- Auto-de-escalate when quota thresholds exceeded
- Auto-escalate (if allowed) when tasks are stuck
- Cost envelope tracking per order
- Alert PO on envelope breach
- **Status:** ⏳ PENDING

### M-BM04: Budget Mode in Fleet CLI
- `fleet budget` — show current mode and quota
- `fleet budget set <mode>` — set global mode
- `fleet budget order <order-id> <mode>` — set per-order mode
- `fleet budget report` — cost breakdown by mode, agent, model
- **Status:** ⏳ PENDING

### M-BM05: Budget Mode in OCMC UI
- Display current budget mode in MC header bar (control surface)
- Mode selector dropdown with descriptions
- Per-order budget mode override
- Cost envelope progress bar
- Real-time cost ticker
- **Status:** ⏳ PENDING

### M-BM06: Budget Analytics
- Track cost per mode over time
- Compare: same task type, different modes → cost difference
- Measure quality impact: do economic-mode tasks get rejected more?
- Feed into PO decision-making about when to use which mode
- Cross-ref: labor stamps provide the data
- **Status:** ⏳ PENDING

---

## Part 9: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Labor Attribution | Labor stamps provide per-task cost data for envelope tracking |
| Multi-Backend Router | Budget mode determines which backends are available |
| Storm Prevention | Budget mode is the first line of defense against cost storms |
| Iterative Validation | Budget mode limits how many validation iterations are affordable |
| Effort Profiles | Existing profiles become aliases for budget modes |
| Catastrophic Drain | Budget modes would have prevented the 20% drain entirely |
| Strategic Vision LocalAI | Budget modes drive LocalAI offload decisions |
| Fleet Elevation Doc 23 | Agent lifecycle sleep/wake adjusted by budget mode |

---

## Part 10: Why This Matters

The catastrophic drain happened because the fleet had only two states:
**running** and **paused**. The moment running became dangerous, the only
option was to kill everything. Budget modes create a **spectrum of intensity**
that lets the fleet stay alive and productive at any budget pressure level.

With budget modes:
- The PO sets the strategy. The brain executes it.
- The fleet never burns more than it's told to.
- Free models and LocalAI get used first when budget is tight.
- The fleet degrades gracefully instead of crashing or burning tokens.
- Every order carries its own spending constraints.
- Cost is observable, predictable, and controllable.

> "reduce the efforts and strategy like that strategic and driven by the
> user and circumstances" — this is exactly what budget modes deliver.