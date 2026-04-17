---
title: "Directive: Multi-Level Tasks + Tools_Blocked Rethink"
type: note
domain: log
note_type: directive
status: active
created: 2026-04-10
updated: 2026-04-10
tags: [directive, tasks, ops-board, plane, tools-blocked, methodology, multi-level, PO]
confidence: medium
sources: []
---

# Directive: Multi-Level Tasks + Tools_Blocked Rethink

## Summary

PO directive establishing two distinct task levels in OpenFleet — **Ops board tasks** (OCMC pieces that agents execute and send for fleet-ops review) vs **Plane tasks** (the real PM-level story/epic that may have multiple Ops pieces contributing). An agent can complete their Ops task without completing the Plane task. Also directs rethinking `tools_blocked` in methodology.yaml: blocking should be per-model-per-stage (contribution + analysis ≠ feature + analysis), not globally per-stage. Plane is optional augmentation; the platform must work without it.

## PO Directive (verbatim)

> "for the tools_blocked I am not sure... it think it stem from an old misunderstanding to adapt to the current stage... but there are multiple level of task...."

> "we need to regather this vision... I could complete a task in the Ops board without completing a task on Plane / PM. otherwise how have I going to send it for review?"

> "Ops board tasks are pieces from the real task on Plane. sometimes the agent create a Plane task when available and sometimes its only on Ops but then the sync system will probably give it a representation and association anyway the important is that during his task, no matter what state, the agent is about to contribute the right way, like when it must enhance or produce new artifacts or segments / pieces of artifacts and documents or when its in work mode and need to make its own action plan on the piece of the PM plan he took and create child task that have dependencies and whatnot..."

> "Do not forget this program is supposed to work even when Plane is not there, Plane only augment the experience and capabilities and true PM."

## Interpretation

### Two Task Levels
- **Ops board tasks** (OCMC): pieces of work an agent executes. Completes → sent to fleet-ops for review. Agent's operational unit.
- **Plane tasks** (PM level): the real story/epic in Plane. May have multiple Ops tasks as pieces. PM tracks at this level.

An agent completes their Ops task (sends for review) WITHOUT completing the Plane task. The Plane task continues with other agents' pieces.

### Tools_blocked Reconsideration
The current tools_blocked in methodology.yaml blocks tools PER STAGE globally. But:
- A contribution task at analysis stage might need different tool permissions than a feature task at analysis stage
- An agent during any stage might need to create subtasks, produce artifacts, commit analysis documents
- The blocking should be per-model-per-stage, not globally per-stage

### Plane Independence
The system works WITHOUT Plane. Plane augments but is not required. All tool blocking, methodology, and task lifecycle must function on Ops board alone. When Plane is connected, it adds PM visibility and sync.

### Open Design Questions
- Should tools_blocked move from per-stage to per-model-per-stage?
- How does fleet_task_complete relate to contribution completion (fleet_contribute)?
- When an agent creates child tasks on the Ops board, how do those relate to the Plane story?

## Relationships

- FEEDS INTO: [[Operational Modes — Heartbeat vs Task, Injection Levels]]
