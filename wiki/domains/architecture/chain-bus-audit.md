---
title: "Chain/Bus Architecture Audit — E002 Phase 0"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E002, chains, buses, event-chain, propagation, audit]
sources:
  - id: event-chain
    type: documentation
    file: fleet/core/event_chain.py
  - id: chain-runner
    type: documentation
    file: fleet/core/chain_runner.py
  - id: tools
    type: documentation
    file: fleet/mcp/tools.py
epic: E002
phase: "0 — Research"
---

# Chain/Bus Architecture Audit

## Summary

Audit of OpenFleet's chain and bus architecture as E002 Phase 0 input. Inventories the 16 chain builders and the bus infrastructure currently in code, maps responsibilities, and identifies the overlap, drift, and simplification opportunities that motivate the E002 chain-bus redesign track.

## Current State

### Chain Builders (16)

| Builder | Operation | Surfaces | Used By MCP Tool |
|---------|-----------|----------|-----------------|
| build_task_complete_chain | Task completion | MC, GitHub, IRC, ntfy, Plane, Meta | fleet_task_complete ✓ |
| build_alert_chain | Alert raised | MC, IRC, ntfy | fleet_alert ✓ |
| build_contribution_chain | Contribution posted | MC, IRC, Plane | fleet_contribute (exists in tools.py) |
| build_gate_request_chain | PO gate request | MC, IRC, ntfy, Plane | fleet_gate_request (exists) |
| build_rejection_chain | Review rejection | MC, IRC | fleet_approve (rejection path) ✓ |
| build_phase_advance_chain | Phase advancement | MC, IRC, ntfy, Plane | fleet_phase_advance (exists) |
| build_transfer_chain | Task transfer | MC, IRC | fleet_transfer (exists) |
| build_sprint_complete_chain | Sprint done | MC, IRC, Plane | (orchestrator) |
| build_comment_chain | Chat/comment | MC, IRC, Plane, ntfy | fleet_chat ✓ |
| build_accept_chain | Plan accepted | MC, Plane | fleet_task_accept ✓ |
| build_commit_chain | Code committed | MC, Plane | fleet_commit ✓ |
| build_task_create_chain | Task created | MC, IRC, Plane | fleet_task_create ✓ |
| build_pause_chain | Work paused | MC, IRC | fleet_pause ✓ |
| build_escalation_chain | Escalation | MC, IRC, ntfy, Plane | fleet_escalate ✓ |
| build_progress_chain | Progress reported | MC, Plane, IRC | fleet_task_progress ✓ |
| build_artifact_chain | Artifact updated | MC, Plane | fleet_artifact_update/create |

**11/16 chain builders are wired to MCP tools.** The remaining 5 (contribution, gate_request, phase_advance, transfer, sprint_complete) have chain builders ready but their MCP tool wiring needs verification.

### Chain Runner

ChainRunner executes events sequentially across 6 surfaces. Partial failure tolerance — non-required events failing don't block the chain. Surfaces: MC (internal), GitHub (public), IRC (channel), ntfy (notify), Plane (optional), Meta (metrics).

### What's Working

1. **Tool → chain → surfaces** pattern is established and consistent
2. Every state-modifying tool call fires a chain
3. Trail recording via PostToolUse hook catches what chains might miss
4. Plane events are all `required=False` (Plane is optional surface)
5. ntfy routing classifies by event severity (critical → PO device)

### What's Missing

#### 1. Cross-Task Propagation (PM↔Child Tracking)

**Gap:** When a child task completes, the parent task doesn't automatically get a summary comment. PM creates subtasks but can't easily see which children are done without checking each one.

**Current:** fleet_task_complete on child → parent evaluation in orchestrator Step 7 (checks if ALL children done → parent to review). But there's NO comment propagation — parent task comment log doesn't show "child X completed by agent Y: summary."

**Needed:**
- build_task_complete_chain should optionally add a comment to parent task
- build_progress_chain should optionally propagate to parent
- build_rejection_chain should notify PM when child is rejected
- Parent task should have a "Children Status" section in its context

#### 2. Contribution Flow Chain Wiring

**Gap:** build_contribution_chain exists (L227-266) but the fleet_contribute MCP tool (L3097) needs to be verified that it actually calls the chain runner.

**Needed:** Verify fleet_contribute → build_contribution_chain → ChainRunner.run() path works end-to-end.

#### 3. Chain Selection Guidance for Agents

**Gap:** Agents don't explicitly know about chains — they call a tool and the chain fires. But the PO directive says agents should "know if it need to use this bus or this bus." Currently agents don't choose buses — the tool handles it.

**Design question:** Is this a gap or working as intended? The PO's "focused desk" principle says agents call one tool and chains handle propagation. The agent doesn't need to think about buses.

**Current answer:** Working as intended. The chain abstraction IS the bus selection. fleet_task_complete IS the bus to "complete a task" — the agent doesn't choose between "complete + push + PR + IRC" separately. The chain docs in TOOLS.md (the **→** notation) tell agents what fires.

#### 4. Ins/Outs/Middles Documentation

**Gap:** The PO said "clear chain entries, ins and outs and middles." tool-chains.yaml documents the chains but not in ins/outs/middles format.

**Current:** tool-chains.yaml has what/when/chain/input/auto per tool. This covers ins (input) and outs (auto/chain) but not middles (intermediate operations).

**Needed:** Consider adding intermediate steps to tool-chains.yaml for complex chains. Example:
```
fleet_task_complete:
  in: summary
  middle: push branch → create PR → update MC status → create approval
  out: IRC notification, ntfy, Plane sync, trail, parent eval
```

#### 5. Event Store Integration

**Gap:** EventStore (fleet/core/events.py) records events but isn't consistently used by all chain builders. Some events fire to surfaces but don't get recorded in the JSONL event log.

**Needed:** Every chain execution should record to EventStore for trail completeness.

## Healthy Patterns

1. **One tool = one chain = multiple surfaces.** This is correct and the PO's design principle holds.
2. **Partial failure tolerance.** IRC down doesn't block task completion. Plane disconnected doesn't break anything.
3. **Chain builders are pure functions.** They build the chain, ChainRunner executes it. Clean separation.
4. **Plane is always optional.** Every Plane event is `required=False`. Fleet works without Plane.

## Recommendations for E002

1. **Add parent comment propagation** to build_task_complete_chain, build_progress_chain, build_rejection_chain
2. **Verify fleet_contribute chain wiring** end-to-end
3. **Enhance tool-chains.yaml** with ins/outs/middles format for complex chains
4. **Wire EventStore recording** into ChainRunner.run() (record every chain execution)
5. **Keep agent-facing simplicity** — agents call one tool, chains handle everything. This IS the bus abstraction.

## Relationships

- PART_OF: E002 (Chain/Bus Architecture)
- FEEDS_INTO: E001 (TOOLS.md chain docs come from this audit)
- RELATES_TO: E003 (Brain coordinates chain execution)
- RELATES_TO: E012 (Autonomous — chains must work reliably for 24h operation)
