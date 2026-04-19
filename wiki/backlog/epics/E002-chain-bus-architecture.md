---
title: "Chain/Bus Architecture"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [chains, buses, propagation, events, tools, group-calls, cross-task-tracking]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Chain/Bus Architecture

## Summary

Validate and evolve the tool chain/bus system so agents naturally call the right tools that do the right chains of actions. Cross-task tracking (PM↔ops task relations), automatic propagation (comments, Plane sync, trail), and clear ins/outs/middles for every operation.

> "agents need to call the right things that will do the right chains of actions... you dont want to have to manually update everywhere.... we already discussed this and there already was a strategy in place we need to validate we do this right. there is a whole logic to this, like adding a comment on a fleet task if related to a PM task we might want to propagate by default like we want to keep track of each ops tasks per PM tasks and so on."

> "WE have to make it possible for the agents to do their work with clear chain entries, ins and outs and middles and groups of operations. Proper interrelation with the brain / orchestrator and the sync and events and notifications and messages."

## Goals

- Validate existing 16 chain builders cover all operations needed
- Design cross-task tracking (PM task → ops subtasks → results propagate back)
- Ensure every tool call produces proper trail, events, notifications
- Make chain selection natural — agents don't think about buses, they call one tool and the chain handles propagation
- Design the "ins and outs and middles" for every group of operations
- Integrate with brain/orchestrator for sync and event handling

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Validate existing 16 chain builders cover all operations needed
- [ ] Design cross-task tracking (PM task → ops subtasks → results propagate back)
- [ ] Ensure every tool call produces proper trail, events, notifications
- [ ] Make chain selection natural — agents don't think about buses, they call one tool and the chain handles propagation
- [ ] Design the "ins and outs and middles" for every group of operations
- [ ] Integrate with brain/orchestrator for sync and event handling

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Document — COMPLETE

- [x] Map every tool → chain → surfaces → [chain-bus-audit.md](../../domains/architecture/chain-bus-audit.md)
- [x] Identify cross-task tracking gaps — parent↔child comment propagation is the main gap
- [x] Document chain system state — 16 builders, 11 wired, ChainRunner with partial failure tolerance
- [x] Identify healthy patterns — one tool = one chain, Plane always optional, clean builder/runner separation

**Key finding:** Chain system is healthier than expected. The main gaps are cross-task propagation (parent doesn't see child completions), EventStore consistency, and ins/outs/middles documentation format. Agent-facing simplicity is working as designed — agents call one tool, chains handle everything.

### Phase 1-3: Design & Implement — PARTIALLY DONE

**Cross-task propagation (DONE — 2026-04-09):**
- [x] build_task_complete_chain: parent gets comment when child completes (agent, summary, PR link)
- [x] build_rejection_chain: parent gets comment when child is rejected (reviewer, reason, agent will fix)
- [x] fleet_task_complete MCP tool passes parent_task_id to chain builder
- [x] Full test suite green (2,347 tests)

**Chain selection for agents (RESOLVED — by design):**
- [x] Agents don't choose buses — they call ONE tool, the chain handles propagation
- [x] TOOLS.md chain docs (→ notation) tell agents what fires. This IS the bus abstraction.
- [x] Design decision: this is working as intended per PO "focused desk" principle

**Remaining:**
- [ ] Update tool-chains.yaml with ins/outs/middles documentation format
- [ ] Wire EventStore recording into ChainRunner.run() for trail completeness
- [ ] Wire brain coordination for chain execution (Layer 2 — event-driven reactions)
- [ ] Update TOOLS.md chain docs if chain behavior changed (regenerate)

### Phase 4: Test & Validate

- [ ] Trace every tool call through its full chain
- [ ] Verify cross-task tracking works (PM sees child task results)
- [ ] Verify trail completeness across all chains
- [ ] Diagram the full bus architecture for PO review

## Existing Foundation

- 16 chain builders in fleet/core/event_chain.py
- ChainRunner with independent failure branches
- 6 surfaces: MC, GitHub, IRC, ntfy, Plane, board memory
- 66 chain docs in tool-chains.yaml

## Relationships

- BUILDS ON: [[Agent Directive Chain Evolution]] (agents need to know the chains)
- ENABLES: [[Brain Evolution]] (brain coordinates chain execution)
- ENABLES: [[Signatures & Transparency]] (chains produce the provenance data)
- RELATES TO: [[Full Autonomous Mode]] (autonomous agents rely on automatic propagation)
- RELATES TO: [[Chain/Bus Architecture Audit — E002 Phase 0]]
