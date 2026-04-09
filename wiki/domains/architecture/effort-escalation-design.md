---
title: "Effort Escalation Design — E003"
type: reference
domain: architecture
status: draft
created: 2026-04-09
updated: 2026-04-09
tags: [E003, E006, E008, effort, model, escalation, budget, adaptive]
sources: [fleet/core/model_selection.py, fleet/core/budget_modes.py, config/fleet.yaml]
epic: E003
phase: "1 — Design"
---

# Effort Escalation Design

## PO Directive

> "There is a logic of escalation of effort and model and source that is also necessary also adaptive based on the settings."

## Current State

model_selection.py selects model + effort from:
1. Backend mode override (localai/hybrid)
2. Task custom field override
3. Story points (≥8 → opus)
4. Task type (epic/story → opus)
5. Agent role (deep reasoning agents → opus on medium+ tasks)
6. Stage floor (thinking stages raise effort)

**What's missing:** No budget mode influence, no context pressure awareness, no adaptive learning from outcomes, no multi-source routing (Codex, MiMo, free models).

## Design: Unified Escalation Logic

### Input Signals (6 dimensions)

```
TASK SIGNALS:
  1. Complexity      — story points, task type, explicit complexity field
  2. Stage           — thinking stages need deeper reasoning

AGENT SIGNALS:
  3. Role            — deep reasoning agents (architect, PM, devsecops, accountability)
  4. Health          — doctor corrections, lessons delivered, rejection history

FLEET SIGNALS:
  5. Budget mode     — turbo (full power), standard, economic (minimize cost), minimal
  6. Context pressure — rate limit %, context %, aggregate fleet load
```

### Output Decision

```
→ Model:  opus | sonnet | haiku | localai | openrouter
→ Effort: max | high | medium | low
→ Source: claude-code | localai | openrouter-free | direct (no LLM)
→ Reason: human-readable explanation for labor stamp
```

### Escalation Matrix

```
                    turbo        standard     economic     minimal
                    ─────        ────────     ────────     ───────
HIGH complexity     opus/high    opus/medium  sonnet/high  sonnet/medium
MEDIUM complexity   opus/medium  sonnet/high  sonnet/med   haiku/medium
LOW complexity      sonnet/med   sonnet/low   haiku/low    localai/med
ROUTINE             sonnet/low   haiku/low    localai/med  localai/low

Stage override: thinking stages (conversation→reasoning) raise effort by 1 level
Agent override: deep reasoning agents raise model by 1 tier
Context pressure: >85% rate limit → drop effort by 1 level
Doctor flag: agent in lesson or recently pruned → raise effort (needs clarity, not speed)
```

### Budget Modes (from E006)

| Mode | Dispatch Rate | Model Tier | Effort Cap | Heartbeat Interval |
|------|-------------|-----------|-----------|-------------------|
| turbo | max (2/cycle) | opus allowed | max | fast (from config) |
| standard | normal (2/cycle) | sonnet default, opus for complex | high | standard |
| economic | reduced (1/cycle) | sonnet cap, haiku for routine | medium | slow (2x) |
| minimal | minimal (1/cycle) | haiku default, localai when available | low | very slow (3x) |

### Adaptive Adjustments

**After rejection:** Next attempt on same task raises effort by 1 level and may raise model tier. If the work wasn't good enough, the next try gets more cognitive resource.

**After 3 corrections:** Prune (immune system). Fresh session gets the ORIGINAL model selection — not escalated from the corrupted session.

**Budget critical (>90% rate limit):** Drop to economic mode regardless of configured budget mode. PO can override.

**Storm active:** Storm severity overrides — WARNING caps at 1 dispatch/cycle, STORM blocks dispatch entirely.

### Implementation

Extend `select_model_for_task()` in model_selection.py:

```python
def select_model_for_task(
    task: Task,
    agent_name: str = "",
    backend_mode: str = "claude",
    budget_mode: str = "standard",     # NEW
    rate_limit_pct: float = 0.0,       # NEW
    context_pct: float = 0.0,          # NEW
    rejection_count: int = 0,          # NEW
    doctor_flagged: bool = False,      # NEW
) -> ModelConfig:
```

The orchestrator passes these values at dispatch time from:
- `budget_mode` → fleet control state (from MC board settings)
- `rate_limit_pct` → budget_monitor._last_reading
- `context_pct` → session_telemetry (when wired)
- `rejection_count` → task.custom_fields.labor_iteration
- `doctor_flagged` → doctor_report.agents_to_skip

### Where This Fits in the Flow

```
Orchestrator Step 5 (dispatch):
  → read fleet control state (budget_mode)
  → read budget monitor (rate_limit_pct)
  → for each task to dispatch:
      → select_model_for_task(task, agent, budget_mode, rate_limit_pct, ...)
      → model + effort + source in dispatch context
      → agent receives in labor stamp
```

## Relationships

- PART_OF: E003 (Brain Evolution — intelligence in model selection)
- RELATES_TO: E006 (Budget Modes — budget mode drives the escalation matrix)
- RELATES_TO: E005 (Multi-Model — source selection for Codex, MiMo, free models)
- RELATES_TO: E008 (Lifecycle — budget mode affects heartbeat intervals)
- RELATES_TO: E009 (Signatures — model + effort + source in labor stamps)
