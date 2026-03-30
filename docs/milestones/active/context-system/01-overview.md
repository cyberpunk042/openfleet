# Context System — MCP Layer + Pre-Embedded Data

**Date:** 2026-03-30
**Status:** Design — from discussion with PO
**Scope:** The full system for delivering aggregated data to agents
through MCP group calls and pre-embedded context

---

## PO Requirements (Verbatim)

> "we are going to have to upgrade mcp group calls and pre-injected /
> pre-embeded data, like the current task."

> "We want to be able to aggregate the information, so the AI can for
> example get all the related work on his task and the comments and
> activies. the transposed data blob, the custom field and state and
> stage and such."

> "Heartbeat too will have its pre-embedded data but not the same as
> the task, more focused on the events and messages and other role
> related responsabilities."

---

## The Four Quadrants

Two contexts × two mechanisms = four distinct areas:

|  | **MCP Group Calls** | **Pre-Embedded Data** |
|--|--------------------|-----------------------|
| **Task** | Agent calls one tool, gets all task data aggregated | Task data baked into session before agent starts working |
| **Heartbeat** | Agent calls one tool, gets all heartbeat data aggregated | Heartbeat data baked into session before agent wakes up |

### Task × MCP Group Calls
The agent is working on a task. It calls ONE tool and gets everything:
transposed artifact, custom fields, state, stage, comments, activity,
related tasks, completeness, Plane state. No multiple calls to assemble
working context.

### Task × Pre-Embedded Data
Before the agent even makes a call, the task data is already in its
session context. The gateway injects it when the agent is dispatched
for task work. The agent's system prompt includes the task bundle.

### Heartbeat × MCP Group Calls
The agent wakes up between tasks. It calls ONE tool and gets role-specific
data: events since last heartbeat, messages, directives, fleet state,
pending work for its role (approvals for fleet-ops, unassigned tasks
for PM, etc.).

### Heartbeat × Pre-Embedded Data
Before the agent's heartbeat executes, the heartbeat data is already in
its session context. The gateway injects it. The agent sees messages,
events, role data without calling anything.

---

## For Each Quadrant: Foundation → Infrastructure → Integration → Testing

Each of the four quadrants needs:

### Foundation
- What data belongs in this quadrant
- Data model / schema for the bundle
- Sources: which existing systems provide the data

### Infrastructure
- How the data is assembled (aggregation logic)
- How it's stored/cached (per cycle? per session?)
- How it's delivered (MCP response? system prompt injection? context/ files?)

### Integration
- Connected to: orchestrator, gateway, event bus, transpose layer,
  methodology system, immune system, Plane sync, standards library
- How the bundle interacts with each system
- What triggers bundle assembly (dispatch? heartbeat? on-demand?)

### Testing
- Unit tests for aggregation logic
- Integration tests for end-to-end delivery
- Verification that agents receive correct data

---

## Documents in This Series

1. **01-overview.md** — this document
2. **02-task-mcp.md** — Task × MCP group calls
3. **03-task-preembed.md** — Task × pre-embedded data
4. **04-heartbeat-mcp.md** — Heartbeat × MCP group calls
5. **05-heartbeat-preembed.md** — Heartbeat × pre-embedded data
6. **06-mcp-layer-upgrade.md** — MCP infrastructure changes
7. **07-integration.md** — How all four connect to fleet systems
8. **08-milestones.md** — Full milestone breakdown

---

## Relationship to Existing Systems

| System | Provides Data To |
|--------|-----------------|
| **Transpose Layer** | Task artifact object + completeness |
| **Methodology System** | Stage, readiness, protocol instructions |
| **Immune System** | Health alerts, doctor flags |
| **Teaching System** | Active lessons, comprehension status |
| **Event Bus** | Events since last cycle, activity history |
| **Plane Sync** | Plane state, labels, issue data |
| **Standards Library** | Artifact completeness checks |
| **Directives** | PO commands pending for agent |
| **Board Memory** | Messages, decisions, alerts |
| **Agent Roles** | Role-specific data providers |