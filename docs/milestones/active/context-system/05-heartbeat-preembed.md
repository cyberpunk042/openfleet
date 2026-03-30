# Heartbeat × Pre-Embedded Data

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 5 of 8)

---

## What This Is

Before the agent's heartbeat executes, data is already in its session
context. The gateway injects it. The agent sees messages, events, role
data without calling any tool. Pre-baked into the session.

This is different from task pre-embed — focused on events, messages,
and role responsibilities, NOT task-specific data.

---

## How It Works

The gateway triggers a heartbeat for an agent. Before the agent's
HEARTBEAT.md instructions execute, the gateway injects pre-embedded
data into the session context. The agent reads it as part of its
initial context.

Currently: the heartbeat context is built by `build_heartbeat_context`
in `fleet/core/heartbeat_context.py` and rendered by the `HeartbeatBundle.
render()` method. This is the pre-embed mechanism — it already exists
in a basic form.

The upgrade: make it role-specific and richer.

---

## What Gets Pre-Embedded

- **Messages for this agent** — @mentions, directives, chat
- **Events summary** — what happened since last heartbeat, compact
- **Role summary** — one-line per role responsibility
  (fleet-ops: "3 pending approvals", PM: "2 unassigned tasks")
- **Fleet state** — work mode, phase, backend (already exists)
- **Assigned tasks** — quick list with stage + readiness (already exists)

Compact format — this goes into the system prompt, so it needs to be
concise. The full data is available via MCP heartbeat group call if
the agent needs more detail.

---

## Foundation Milestones

### HP-F01: Role-specific heartbeat summary
- Per-role one-liner: "3 pending approvals" for fleet-ops
- Computed from the same data as the MCP heartbeat bundle
- Compact enough for system prompt injection

### HP-F02: Events summary formatter
- Last N events compressed into a compact summary
- Not full event detail — just "architect completed task X,
  backend-dev pruned, mode changed to planning"

---

## Infrastructure Milestones

### HP-I01: Upgrade HeartbeatBundle
- Add role_summary field
- Add events_summary field
- Keep existing fields (assigned_tasks, chat, fleet_state)
- Render method produces the pre-embed text

### HP-I02: Gateway heartbeat injection
- HeartbeatBundle rendered text injected into agent session
- Before HEARTBEAT.md instructions execute
- Mechanism: system prompt append or context/ file

---

## Integration Milestones

### HP-G01: Wire to role providers
- Same role providers as heartbeat MCP (HM-F02)
- Compact summary version for pre-embed

### HP-G02: Wire to event bus
- Compact event summary from event store

---

## Testing Milestones

### HP-T01: HeartbeatBundle rendering tests
- Verify role summary appears in rendered output
- Verify events summary appears
- Verify size stays within budget