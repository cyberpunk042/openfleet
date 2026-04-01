# System 4: Event Bus

**Source:** `fleet/core/events.py`, `fleet/core/event_chain.py`, `fleet/core/event_router.py`, `fleet/core/event_display.py`
**Status:** ✅ Live verified — events flowing in production
**Design docs:** `fleet-event-bus-architecture.md`, `fleet-event-bus-audit.md`

---

## Purpose

The fleet's nervous system. Every operation produces events across multiple surfaces. One tool call → multi-surface publishing. Tolerates partial failure (IRC down doesn't block task completion).

## Key Concepts

### Event Surfaces (event_chain.py:22-30)

6 surfaces:
- `INTERNAL` — MC: task updates, approvals, board memory
- `PUBLIC` — GitHub: branches, PRs, commits
- `CHANNEL` — IRC: real-time notifications
- `NOTIFY` — ntfy: human push notifications
- `PLANE` — Plane: issue updates, labels, comments
- `META` — System: metrics, quality checks

### Event Chain Pattern (event_chain.py)

One operation produces an `EventChain` with events across surfaces:

```python
chain = EventChain(operation="task_complete", source_agent="worker")
chain.add(EventSurface.INTERNAL, "update_task", params={...})
chain.add(EventSurface.PUBLIC, "create_pr", params={...})
chain.add(EventSurface.CHANNEL, "notify_irc", params={...}, required=False)
chain.add(EventSurface.NOTIFY, "push_ntfy", params={...}, required=False)
```

Required events fail the chain. Optional events (IRC, ntfy) tolerate failure.

### CloudEvents Schema (events.py)

Events stored in `.fleet-events.jsonl` (append-only JSONL). 47 event types across: task, Plane, GitHub, agent, communication, system, immune, teaching, methodology.

### Event Router (event_router.py)

5 routing levels for agent notification:
1. Direct — explicitly addressed to agent
2. Priority — task the agent owns
3. Mention — @agent in message
4. Tag — matches agent capabilities
5. Broadcast — all agents

### Event Display (event_display.py)

Formats events for human-readable display in CLI, IRC, board memory.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Every MCP tool** | Tools emit events via chains | Tools → Events |
| **Orchestrator** | Mode changes, dispatch, health checks emit events | Orchestrator → Events |
| **Doctor** | Protocol violations emit events | Doctor → Events |
| **Methodology** | Stage transitions emit events | Methodology → Events |
| **Notifications** | Events route to IRC, ntfy | Events → Notifications |
| **Plane** | Events trigger Plane label/state updates | Events → Plane |
| **Change Detector** | Reads events to detect changes | Events → Detector |
| **Context Assembly** | Recent events included in agent context | Events → Context |

## What's Needed

- [ ] CloudEvents SDK integration (M-EB02)
- [ ] Agent feed design (M-EB03)
- [ ] Sync map documentation (M-EB04)
- [ ] Mention routing design (M-EB05)
