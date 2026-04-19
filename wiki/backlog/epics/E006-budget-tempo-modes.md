---
title: "Budget & Tempo Modes"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [budget, tempo, modes, ocmc, spending, work-window, economic]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Budget & Tempo Modes

## Summary

Add budget mode config to Mission Control as a dropdown, fine-tune spending speed/frequency, support preferred work windows (off-peak doubled usage), and create economic modes that leverage free models.

> "I think we are going to add a budget mode config that we inject in the Openclaw mission control like the multiple other dropdown"

> "I am wondering if there is a new budgetMode (e.g. aggressive... whatever A, B... economic..) to inject into ocmc in order to fine-tune the spending as speed / frequency of tasks / s and whatnot."

> "The use of free open claud models... I know some endpoint are route through a loadbalancer of free models with autorouting to the one available to the level you want if its not too busy."

> "support preferred work window config" — off-peak hours provide doubled usage limits.

## Goals

- Budget mode dropdown in Mission Control UI (like existing dropdowns)
- Multiple modes: aggressive, normal, conservative, economic, minimal
- Each mode controls: dispatch rate, model tier, effort level, heartbeat frequency
- Preferred work window support (off-peak scheduling)
- Integration with free model routing for economic mode

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Budget mode dropdown in Mission Control UI (like existing dropdowns)
- [ ] Multiple modes: aggressive, normal, conservative, economic, minimal
- [ ] Each mode controls: dispatch rate, model tier, effort level, heartbeat frequency
- [ ] Preferred work window support (off-peak scheduling)
- [ ] Integration with free model routing for economic mode

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Document

- [ ] Audit current budget system (budget_monitor.py, budget_modes.py)
- [ ] Document existing MC custom field dropdowns and how they work
- [ ] Research Claude off-peak usage patterns and benefits
- [ ] Document the interaction between budget mode and storm system

### Phase 1: Design

- [ ] Design budget mode enum and config schema
- [ ] Design MC UI integration (custom field or dedicated dropdown)
- [ ] Design the dispatch behavior per mode
- [ ] Design work window awareness in orchestrator
- [ ] Design economic mode with free model routing

### Phase 2: Scaffold & Implement

- [ ] Add budget_mode custom field to MC board config
- [ ] Extend fleet.yaml with budget mode definitions
- [ ] Wire budget mode into orchestrator dispatch decisions
- [ ] Add work window awareness
- [ ] Connect to multi-model routing for economic mode

### Phase 3: Test & Validate

- [ ] Test each mode produces expected dispatch behavior
- [ ] Test mode switching via MC UI
- [ ] Test work window scheduling
- [ ] Test economic mode with free models

## Existing Foundation

- Budget monitor: fleet/core/budget_monitor.py
- Budget modes: fleet/core/budget_modes.py
- Fleet control: fleet/core/fleet_mode.py (work_mode)
- MC board: scripts/configure-board.sh (custom fields)

## Relationships

- RELATES TO: [[Multi-Model Strategy]] (economic mode uses free models)
- RELATES TO: [[Brain Evolution]] (brain reads budget mode for dispatch decisions)
- RELATES TO: [[Agent Lifecycle Fine-Tuning]] (budget mode affects heartbeat timing)
- RELATES TO: [[Effort Escalation Design — E003]] (budget mode drives the escalation matrix)
- RELATES TO: [[Deterministic Bypass Design — E003]] (bypass is the ultimate economy in any mode)
- RELATES TO: [[Claw Code Parity Research]] (LocalAI enables economic mode)
