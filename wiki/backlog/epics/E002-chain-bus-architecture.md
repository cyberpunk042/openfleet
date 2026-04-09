---
title: "Chain/Bus Architecture"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-08
tags: [chains, buses, propagation, events, tools, group-calls, cross-task-tracking]
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

## Phases

### Phase 0: Document

- [ ] Map every tool → chain → surfaces it propagates to
- [ ] Identify cross-task tracking gaps (PM↔ops, parent↔child)
- [ ] Document what the brain currently does vs what it should do for chains
- [ ] Document the event system's current state and gaps

### Phase 1: Design

- [ ] Design cross-task comment propagation (comment on child → visible on parent)
- [ ] Design the chain selection logic for agents (when to use which bus)
- [ ] Design the "ins/outs/middles" documentation format for tool-chains.yaml
- [ ] Design the brain's role in chain coordination

### Phase 2: Scaffold

- [ ] Update tool-chains.yaml with ins/outs/middles documentation
- [ ] Scaffold any new chain builders needed for cross-task tracking
- [ ] Scaffold brain integration points

### Phase 3: Implement

- [ ] Build cross-task propagation chains
- [ ] Enhance existing chains with missing operations
- [ ] Wire brain coordination for chain execution
- [ ] Update TOOLS.md generation to include chain selection guidance

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

- DEPENDS_ON: E001 (Agent Directive Chain — agents need to know the chains)
- ENABLES: E003 (Brain Evolution — brain coordinates chain execution)
- ENABLES: E009 (Signatures — chains produce the provenance data)
- RELATES_TO: E012 (Full Autonomous Mode — autonomous agents rely on automatic propagation)
