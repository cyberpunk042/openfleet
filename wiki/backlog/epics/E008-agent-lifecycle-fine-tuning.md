---
title: "Agent Lifecycle Fine-Tuning"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [sleep, offline, heartbeat, context-switching, compaction, timing, effort, responsive]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Agent Lifecycle Fine-Tuning

## Summary

Fine-tune sleep/offline/silent heartbeat timing for a proficient autonomous fleet. Strategic context switching. Self-triggered compaction before forced ones. Effort escalation adaptive to settings. Don't waste breath, yet be responsive and prompt to work.

> "we are going to need to fine tune the timing for the sleep and offline and silent heartbeat and all the reasoning and real logical settings for a proficient autonomous fleet. that do not waste breath and yet is very responsive and prompt to work. very strategical in context switching and mindful of the current context size relative to the next forced compact that require adapting preparing and potentially even triggering it ourself before rechaining to regather the context to continue working if necessary"

> "we need to be smart and fine tune the brain we know that a lot does not require agent."

> "There is a logic of escalation of effort and model and source that is also necessary also adaptive based on the settings."

## Goals

- Fine-tune IDLE/SLEEPING/OFFLINE thresholds per role (not one-size-fits-all)
- Brain-evaluated heartbeats for IDLE+ agents ($0 silent when nothing to do)
- Context-aware compaction strategy (detect approaching limits, prepare artifacts, self-trigger)
- Effort escalation logic (stage → complexity → effort → model → source, adaptive)
- Preferred work window support (off-peak hours = doubled usage limits)
- Budget mode adjusts heartbeat intervals (turbo = fast, economic = slow)

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Fine-tune IDLE/SLEEPING/OFFLINE thresholds per role (not one-size-fits-all)
- [ ] Brain-evaluated heartbeats for IDLE+ agents ($0 silent when nothing to do)
- [ ] Context-aware compaction strategy (detect approaching limits, prepare artifacts, self-trigger)
- [ ] Effort escalation logic (stage → complexity → effort → model → source, adaptive)
- [ ] Preferred work window support (off-peak hours = doubled usage limits)
- [ ] Budget mode adjusts heartbeat intervals (turbo = fast, economic = slow)

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- fleet/core/agent_lifecycle.py — ACTIVE→IDLE→SLEEPING→OFFLINE state machine
- fleet/core/heartbeat_gate.py — HeartbeatDecision (wake/silent/strategic), deterministic evaluation
- fleet/core/brain_writer.py — writes .brain-decision.json per agent every cycle
- config/agent-autonomy.yaml — per-role wake triggers, thresholds
- config/agent-crons.yaml — staggered heartbeat intervals (10m fleet-ops → 28m accountability)
- scripts/clean-gateway-config.sh — heartbeat staggering on provisioning
- fleet/core/model_selection.py — stage-aware effort floors
- fleet/core/budget_modes.py — tempo setting (affects dispatch rate)
- context-window-awareness-and-control.md — CW-01 to CW-10 requirements

## Phases

### Phase 0: Document & Research

- [ ] Audit current lifecycle thresholds (30min→sleeping, 4h→offline) — are they right?
- [ ] Audit brain-evaluated heartbeat path — is it actually saving money?
- [ ] Measure real cost of idle fleet (silent heartbeats vs real heartbeats)
- [ ] Document context compaction behavior — when does Claude force-compact? what triggers it?
- [ ] Document preferred work window mechanics (off-peak usage doubling)
- [ ] Map effort escalation paths — what determines model + effort today vs what's needed

### Phase 1: Design

- [ ] Design per-role lifecycle profiles (PM needs fast wake, accountability can sleep longer)
- [ ] Design context strategy module (approaching limit → prepare → extract → compact or fresh)
- [ ] Design unified effort decision (task type × stage × complexity × budget mode → model + effort)
- [ ] Design work window awareness in orchestrator (schedule dispatch for off-peak when possible)
- [ ] Design heartbeat interval adaptation per budget mode

### Phase 2: Implement

- [ ] Implement per-role lifecycle profiles in agent-autonomy.yaml
- [ ] Implement context strategy module (detect, prepare, self-trigger)
- [ ] Implement unified effort escalation
- [ ] Wire work window awareness into dispatch
- [ ] Wire budget mode to heartbeat intervals (update CRONs dynamically)

### Phase 3: Test & Validate

- [ ] Measure cost reduction from lifecycle tuning (before vs after)
- [ ] Test context strategy prevents data loss during compaction
- [ ] Test effort escalation selects correct model per situation
- [ ] Test work window scheduling dispatches at off-peak

## Relationships

- BUILDS ON: [[Brain Evolution]] (brain controls lifecycle)
- RELATES TO: [[Budget & Tempo Modes]] (budget mode drives timing)
- RELATES TO: [[Agent Directive Chain Evolution]] (agents need awareness of context limits)
- RELATES TO: [[Full Autonomous Mode]] (timing must work for 24h operation)
- RELATES TO: [[Context Strategy Design — E003]] (compaction timing intersects with lifecycle)
- RELATES TO: [[Effort Escalation Design — E003]] (effort affects call frequency, affects heartbeat)
