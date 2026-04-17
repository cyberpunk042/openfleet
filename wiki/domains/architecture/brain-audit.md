---
title: "Brain (Orchestrator) Audit — E003 Phase 0"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E003, brain, orchestrator, intelligence, audit]
sources:
  - id: orchestrator
    type: documentation
    file: fleet/cli/orchestrator.py
  - id: brain-writer
    type: documentation
    file: fleet/core/brain_writer.py
  - id: heartbeat-gate
    type: documentation
    file: fleet/core/heartbeat_gate.py
  - id: 04-the-brain
    type: documentation
    file: docs/milestones/active/fleet-elevation/04-the-brain.md
epic: E003
phase: "0 — Research"
---

# Brain (Orchestrator) Audit

## Summary

Audit of the orchestrator (the Brain) as the starting artifact for E003 Phase 0. Documents the current 13-step dispatch cycle, identifies components (storm monitor, budget monitor, fleet mode, effort profile, change detector), and surfaces the bypass / escalation / context-strategy design questions that drive the E003 reasoning stage.

## Current Cycle (13 steps in code)

```
PRE-CYCLE:
  Storm evaluate → dispatch limiting (CRITICAL=halt, STORM=0 dispatch, WARNING=1 max)
  Gateway duplication check → storm indicator if detected

STEP A: Brain decisions (EVERY cycle)
  write_brain_decisions() → .brain-decision.json per non-active agent
  Evaluates: mentions, tasks, directives, contributions → wake/silent/strategic
  Pure Python, $0 cost

STEP B: MC liveness (at agent CRON intervals)
  heartbeat_agent() for agents whose CRON has elapsed
  Reads brain decision to determine message suffix
  Gateway keepalive for gateway agents (8 min interval)

STEP 0: Refresh agent contexts
  _refresh_agent_contexts() → fleet-context.md, task-context.md, knowledge-context.md
  Per agent: messages, directives, role data, Navigator assembly
  ALWAYS runs (even when dispatch paused)

--- dispatch_blocked gate ---

STEP 1: Security scan
STEP 2: Doctor (immune system)
STEP 3: Ensure review approvals
STEP 4: Wake drivers (PM, fleet-ops)
STEP 5: Dispatch ready tasks (4 gates: budget, storm, doctor, fleet mode)
STEP 6: Process directives
STEP 7: Evaluate parent completion
STEP 8: Health check
```

## What's Intelligent (Working)

1. **Brain-evaluated heartbeats** — write_brain_decisions() runs every cycle, writes .brain-decision.json. Gateway reads it. Silent heartbeats = $0. Estimated ~70% cost reduction when fleet is idle.

2. **Storm graduated response** — 5 severity levels, automatic dispatch limiting. CRITICAL halts the cycle entirely. Gateway duplication is the #1 indicator (learned from March catastrophe).

3. **Doctor integration** — immune system produces skip/block lists. Orchestrator respects them. Interventions (teach, compact, prune) execute in the doctor step.

4. **Context refresh with Navigator** — every 30s, per-agent context files refreshed with Navigator-assembled knowledge map content. Role providers supply per-role data. Contributions appended to task-context.md.

5. **Fleet control state** — work mode, cycle phase, backend mode all checked before dispatch. Dispatch blocked when fleet paused.

## What's Missing (vs fleet-elevation/04 Spec)

The spec describes a 3-layer brain. Current implementation is Layer 1 only.

### Layer 1: The Cycle (IMPLEMENTED)

Poll-based, every 30 seconds. Read state → run steps → repeat. This is what exists.

**Missing from Layer 1:**
- Step 3 (Gate Processing) — the spec says check pending gate requests, process PO responses. Current Step 3 only ensures approval objects exist. No gate request processing.
- Step 4 (Contribution Management) — the spec says detect tasks needing contributions, create subtasks, check completeness. Current Step 4 only wakes PM/fleet-ops. No contribution logic.
- Step 9 (Cross-Task Propagation) — spec says propagate child comments to parent, contribution artifacts to target, transfer context. Not in current cycle.

### Layer 2: Chain Registry (NOT IMPLEMENTED)

Event-driven, reactive. When events fire, handlers react deterministically. Stage changes trigger contribution creation. Completions trigger parent evaluation.

**What this would mean:** Instead of polling every 30s to check "did any stage change?", the MCP tool that changes the stage fires an event, and a handler reacts immediately. This is more responsive and cleaner than polling.

**Current workaround:** Polling covers it. The orchestrator checks everything every 30s. Not elegant but functional.

### Layer 3: Logic Engine (NOT IMPLEMENTED)

Rule-based, configurable. Complex dispatch decisions evaluated from multiple data points. "Should this task be dispatched?" evaluates: unblocked, assigned, online, not busy, doctor cleared, phase standards met, contributions received, fleet mode allows.

**What this would mean:** Dispatch logic moved from hardcoded Python to configurable rules. PO could adjust dispatch criteria without code changes.

**Current reality:** Dispatch logic is in _dispatch_ready_tasks() with hardcoded checks. Works but not configurable.

## Specific Gaps

| Gap | Spec Reference | Impact | Effort |
|-----|---------------|--------|--------|
| Contribution auto-creation | §Step 4, fleet-elevation/15 | Blocks full synergy — specialists can't contribute automatically | 8-16h |
| Contribution completeness as dispatch gate | §Step 5, contributions.py | Agents can start work without design input | 2-4h (code exists, needs wiring) |
| Cross-task propagation | §Step 9 | PM can't track child progress from parent | 4-8h |
| Gate processing | §Step 3 | PO gate responses not processed automatically | 4-8h |
| Phase standards injection | §Step 5 | Agents don't see delivery phase quality bars | 2-4h |
| Context compaction strategy | §Session management | No preparation for forced compaction | 8-16h |
| Effort escalation logic | §Brain intelligence | Model/effort selection is simple, not adaptive | 4-8h |
| EventStore wiring | §Trail | Not all chain executions recorded in event log | 2-4h |

## What the Brain DOES Right

The brain's fundamental architecture is sound:
- **30s cycle is reliable.** It never stops, even when everything else fails.
- **Separation of concerns.** Brain writes context, gateway runs sessions. Brain NEVER creates Claude sessions directly.
- **Budget protection.** MC down → gateway can't start → zero Claude calls. Budget monitor reads real OAuth quota.
- **Agent lifecycle is clean.** ACTIVE→IDLE→SLEEPING→OFFLINE with content-aware transitions. brain_evaluates property cleanly separates "real heartbeat" from "silent check."
- **Navigator integration is already wired.** The hardest part (knowledge map assembly → context file injection) is working.

## Path Forward

The brain doesn't need a rewrite — it needs **wiring.** The modules exist:
- contributions.py has detect_contribution_opportunities() and check_contribution_completeness()
- heartbeat_gate.py has evaluate_agent_heartbeat()
- phases.py loads phase config with gates
- event_chain.py has all 16 builders

The orchestrator needs new steps that CALL these modules. The architecture supports it — the cycle just needs more steps.

## Relationships

- PART_OF: E003 (Brain Evolution)
- FEEDS_INTO: E001 (brain writes context that agents read)
- FEEDS_INTO: E012 (autonomous mode depends on intelligent brain)
- RELATES_TO: E002 (brain coordinates chain execution)
- RELATES_TO: E008 (lifecycle timing depends on brain tuning)
