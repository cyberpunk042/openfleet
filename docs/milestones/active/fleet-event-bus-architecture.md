# Fleet Event Bus Architecture — The Nervous System

**Date:** 2026-03-29
**Status:** Requirements captured — deep investigation needed
**Scope:** Central event bus, agent notification feed, cross-platform sync, CloudEvents, deterministic routing

---

## User Vision (Verbatim — Complete)

### The Central Hub

> "lets make sure all the communication and mcp and tool is 100% for everything
> and that events work and mentions works and wake up works and project manager
> watching to display when attributed to no one in precise or mistagged, we have
> to be logic and like the command center aggregate everything and redistribute
> and orchestrate and lets the agents do their works and their heartbeats and
> their responsive to targeted events, proper use of tagging and responsiveness
> to tagging."

> "We need a smart central hub if we dont already have it and we need to do things
> properly and make sure that what can be on the logical layer and/or automated
> with an AI is and they only do what is required and very easily and that trigger
> chains of operations and chains of events and such and that synchronise whatever
> need to be synchronised and track the multiplatform and the remote."

> "we need to make sure this is strong and evolved. we need to make sure it will
> track everything properly and give the right information to everyone embedded
> and into their heartbeat and adapted. It will be kinda a central plan to all
> this, agents acting as their own cortex and this layer relying on reliable
> consistent and deterministic logic."

### Cross-Platform Event Detection

> "no matter from where I mention, that it be internal chat or Plane, or if I
> change something manually on the platform, you must detect and record the event
> and do the appropriate chain of operations and possible forward or event with
> directive for the agents of concern."

> "We need the proper way to communicate naturally and automatically and
> multiplexed and fluid."

### Adaptive Display and Cross-Referencing

> "Do not minimize anything and you will need to go back and review too and
> validate we have everything that you quoted from me and the new stuff too for
> new milestones. making sure everything is properly used and in chain to do the
> proper display adapted to the channel and always cross reference, like when
> updating a task on Plane you can say it in the internal chat naturally."

### IaC Sync and Persistence

> "Remember the need for the sync of the seed / config for the IaC so that the
> differential is not only recorded as event for sync for whatever purpose and
> agent tracking and possibly event in cache or memory then it would restart from
> there after whatever reason, shutdown or even delete of the docker compose"

### Agent Notification Feed

> "I wonder if the AI themselves should not have notification like I do with ntfy.
> but for them, no need to be in ntfy, its more like what they would look at (be
> feed) on trigger or during their heartbeat."

Agent notification structure (proposed):
```json
{
  "title": "...",
  "body": "...",
  "data": {...},
  "timestamp": "...",
  "type": "...",
  "recipient": "...",
  "actions": [...]
}
```

> "Always with a local memory not to have resync from scratch everytime, they can
> even have the notion of seen or not and such, or important, general event or
> with mentions or remark or tag of concern or associated to your work."

### Standards Research (User Provided)

> "Use CloudEvents as canonical schema. Store events (not notifications).
> Generate notifications as projections."

CloudEvents schema (CNCF standard):
```json
{
  "specversion": "1.0",
  "type": "com.example.notification",
  "source": "/my/service",
  "id": "1234",
  "time": "2026-03-29T12:00:00Z",
  "data": {...}
}
```

Key insight from user research:
> "There is no standard because notifications are not first-class objects.
> They are: views over events."

Building blocks:
- **CloudEvents** (CNCF) → canonical event schema
- **Web Push** (IETF) → delivery standard
- **Notifications API** (WHATWG) → display semantics
- **ActivityPub** → federated inbox/outbox model

### Design Philosophy

> "thats right we need to evolve. there is multiple milestones, lets treat it
> as such."

> "this is going to be a long job and we have a lot of think and analysis and
> investigation and research to do."

> "Lets make sure we exploit the full potential of everything and add what is
> needed and use the proper pattern and make a support connected and operable
> and reliable system."

---

## Architecture: What We're Building

### The Nervous System

```
                     ┌─────────────────────────────┐
                     │     Fleet Event Bus          │
                     │  (deterministic, no AI)      │
                     │                              │
                     │  CloudEvents store            │
                     │  Agent notification feeds     │
                     │  Cross-platform state sync    │
                     │  Chain dispatcher              │
                     └──────────┬───────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
    ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
    │  Plane  │           │  OCMC   │           │ GitHub  │
    │ watcher │           │ watcher │           │ watcher │
    └────┬────┘           └────┬────┘           └────┬────┘
         │                      │                      │
    ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
    │  IRC    │           │  ntfy   │           │ manual  │
    │ watcher │           │ watcher │           │ changes │
    └─────────┘           └─────────┘           └─────────┘
```

### Event Flow

```
1. DETECT: Watcher detects change on a surface
2. RECORD: CloudEvent created and stored locally (persistent)
3. ROUTE: Event matched to recipient agents by type, tags, mentions
4. ENRICH: Event decorated with context (related work, cross-refs)
5. DISPATCH: Event added to agent's notification feed
6. TRIGGER: Chain operations fired (multi-surface publish)
7. SYNC: State differential recorded for IaC persistence
8. TRACK: Agent sees/acknowledges event on next heartbeat
```

### Agent Cortex Model

Each agent has:
- **Notification feed** — ordered list of events relevant to them
- **Seen/unseen tracking** — agents mark events as processed
- **Priority levels** — urgent (immediate wake), important (next heartbeat), info (background)
- **Tag subscriptions** — agent subscribes to event types matching their capabilities
- **Work context** — events associated with their current tasks
- **Mentions** — direct @agent references from any surface

```
Agent Heartbeat:
  1. Read notification feed (pre-computed, no API calls needed)
  2. Process unseen events by priority
  3. Take action (create tasks, respond, escalate)
  4. Mark events as seen
  5. Emit new events from actions taken
```

---

## Investigation Needed

### I-1: Current State Review

Before building anything, review ALL existing code for:

| Component | File | What to Check |
|-----------|------|---------------|
| Event chain model | `fleet/core/event_chain.py` | Complete? All surfaces covered? |
| Chain runner | `fleet/core/chain_runner.py` | All handlers implemented? Error handling? |
| Smart chains | `fleet/core/smart_chains.py` | Used anywhere? Or dead code? |
| Heartbeat context | `fleet/core/heartbeat_context.py` | Covers all data sources? Plane data? |
| Notification router | `fleet/core/notification_router.py` | Classification correct? All event types? |
| Routing | `fleet/core/routing.py` | Capability matching working? |
| Skill enforcement | `fleet/core/skill_enforcement.py` | All task types covered? |
| MCP tools (20) | `fleet/mcp/tools.py` | Each tool emits events? Or individual calls? |
| Orchestrator | `fleet/cli/orchestrator.py` | All 6 steps correct? Uses chains? |
| Sync daemon | `fleet/cli/sync.py` | Detects changes? Or just polls? |
| Remote watcher | `fleet/core/remote_watcher.py` | GitHub only? Expandable? |
| Driver model | `fleet/core/driver.py` | Products defined correctly? |
| Agent roles | `fleet/core/agent_roles.py` | All roles? Secondary responsibilities? |

### I-2: Anti-Pattern Detection

Check for:
- Individual API calls where chains should be used
- Hardcoded routing where config should drive it
- Missing error handling on surface operations
- Inconsistent event naming across surfaces
- Data that's computed repeatedly instead of cached
- Tools that don't notify other surfaces of changes
- Events that get lost (fire-and-forget with no persistence)

### I-3: CloudEvents Research

Investigate:
- CloudEvents Python SDK: `cloudevents` package
- How to integrate CloudEvents schema with our EventChain model
- Storage format for persistent event store
- Query patterns for agent notification feeds
- Integration with existing event_chain.py

### I-4: Agent Notification Feed Design

Design the feed system:
- Storage: SQLite? JSON file? In-memory with persistence?
- Schema: CloudEvents base + fleet extensions (recipient, actions, seen)
- Query: "give me unseen events for agent X, priority >= important"
- Lifecycle: create → route → deliver → seen → archive
- Retention: how long to keep? Rotation policy?

### I-5: Cross-Platform State Sync

Map ALL state changes across surfaces:
- What changes in Plane should propagate to OCMC?
- What changes in OCMC should propagate to Plane?
- What changes in GitHub should trigger events?
- What manual changes in any surface should be detected?
- How to handle conflicts?
- How to maintain IaC config differential?

### I-6: Mention and Tagging System

Design unified mention system:
- @agent-name in Plane comments → agent heartbeat feed
- @agent-name in IRC → agent heartbeat feed
- @agent-name in OCMC board memory → agent heartbeat feed
- Tag subscriptions: agent subscribes to tags matching capabilities
- Untagged/unassigned items → PM's feed for triage

---

## Milestones

### Phase 1: Investigation and Design (this document + follow-ups)

| # | Milestone | Scope |
|---|-----------|-------|
| M-EB01 | Current state audit | Review all 13+ modules for completeness, anti-patterns |
| M-EB02 | CloudEvents research | SDK, schema, integration plan |
| M-EB03 | Agent feed design | Storage, schema, query, lifecycle |
| M-EB04 | Cross-platform sync map | All surface changes documented |
| M-EB05 | Mention/tagging design | Unified @mention across surfaces |

### Phase 2: Event Store and Feed (the foundation)

| # | Milestone | Scope |
|---|-----------|-------|
| M-EB06 | CloudEvents event store | Persistent local store, fleet/core/event_store.py |
| M-EB07 | Agent notification feed | Feed per agent, seen/unseen, priority filtering |
| M-EB08 | Feed in heartbeat context | Pre-compute feed into HeartbeatBundle |
| M-EB09 | Event creation from all MCP tools | Every tool emits CloudEvents |

### Phase 3: Watchers and Detection (cross-platform)

| # | Milestone | Scope |
|---|-----------|-------|
| M-EB10 | Plane watcher (events from Plane changes) | Webhook + poll |
| M-EB11 | OCMC watcher enhancement (delta detection) | State tracking |
| M-EB12 | GitHub watcher enhancement (CI, merge, reviews) | Expand remote_watcher |
| M-EB13 | Manual change detection (config diffs) | IaC differential |

### Phase 4: Routing and Chains (the intelligence)

| # | Milestone | Scope |
|---|-----------|-------|
| M-EB14 | Event → agent routing engine | Tags, mentions, capabilities, subscriptions |
| M-EB15 | Wire all MCP tools to chain runner | Replace individual calls |
| M-EB16 | Adaptive display per channel | Same event → different format per surface |
| M-EB17 | Cross-reference automation | Event on one surface → reference on others |

### Phase 5: Sync and Persistence (operational resilience)

| # | Milestone | Scope |
|---|-----------|-------|
| M-EB18 | IaC config differential sync | Track changes → update YAML configs |
| M-EB19 | Event store persistence (restart recovery) | Local cache, no resync |
| M-EB20 | State export/import (rebuild recovery) | Full state → configs → rebuild |

---

## Total Milestone Count (All Documents)

| Document | Prefix | Count |
|----------|--------|-------|
| plane-full-configuration.md | M-PF | 9 |
| plane-skills-and-chains.md | M-SC | 8 |
| plane-iac-evolution.md | M-P | 10 |
| plane-platform-maturity.md | M-PM | 10 |
| plane-sync-worker.md | M-SW | 10 |
| **fleet-event-bus-architecture.md** | **M-EB** | **20** |
| **Total** | | **67** |

---

## Design Principles

1. **Events, not notifications.** Store events. Generate notifications as projections.
2. **Deterministic logic layer.** No AI for routing/tracking. AI is the cortex (agent), not the nervous system.
3. **CloudEvents canonical schema.** Standard, transport-agnostic, widely adopted.
4. **Persistent local store.** Survives restarts. Agents don't resync from scratch.
5. **Adapted display per channel.** Same event → rich HTML in Plane, compact in IRC, structured in heartbeat.
6. **Cross-reference everything.** Every event on one surface links to related items on other surfaces.
7. **Agent feeds are personal.** Filtered by capability, tags, mentions, work association.
8. **Seen/unseen tracking.** Agents process at their own pace. Nothing gets lost.
9. **Chain operations.** One event → multi-surface publish. Deterministic, not fire-and-forget.
10. **IaC differential.** Runtime changes tracked. Config updated. Rebuild recovers.