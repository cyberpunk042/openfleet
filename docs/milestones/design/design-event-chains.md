# Design: Event Chains & Multi-Surface Publishing

## User Requirements

> "Sometime its operations that triggers multiple things, multiple events, publish to both the public but also the internal or in reverse internal but with a piece public, bigger or not or in reverse or equal and whatnot."

## What This Means

A single action in the fleet doesn't produce ONE event. It produces a CHAIN.

### Example: Agent Completes a Task

```
fleet_task_complete("Added type hints to engine module")
    ↓
    ├── INTERNAL (Mission Control)
    │   ├── Task status → review
    │   ├── Task comment (structured completion)
    │   ├── Task custom fields (branch, pr_url)
    │   ├── Approval created (confidence + rubric)
    │   └── Board memory entry (tags: pr, review, project:nnrt)
    │
    ├── PUBLIC (GitHub)
    │   ├── Branch pushed
    │   ├── PR created (rich body with changelog)
    │   └── PR linked to task (in description)
    │
    ├── CHANNEL (IRC)
    │   ├── #fleet: "[sw-eng] ✅ PR READY: Add type hints — pr_url"
    │   ├── #reviews: "[sw-eng] 🔀 PR for review: Add type hints — pr_url | compare_url"
    │   └── (nothing to #alerts — not an alert)
    │
    └── META (System)
        ├── fleet-monitor: quality check triggered
        ├── fleet-sync: PR tracked for merge detection
        └── fleet-digest: data collected for daily report
```

One tool call → 15+ actions across 4 surfaces.

### Example: Security Alert Found

```
fleet_alert(severity="critical", title="CVE in pydantic", ...)
    ↓
    ├── INTERNAL
    │   ├── Board memory (tags: alert, critical, security, project:nnrt)
    │   ├── Task blocker comment (if task-related)
    │   └── Approval request (human must acknowledge)
    │
    ├── PUBLIC
    │   └── (nothing — security alerts don't go to GitHub)
    │
    ├── CHANNEL
    │   ├── #alerts: "🔴 [sw-eng] CRITICAL: CVE in pydantic — nvd_url"
    │   └── #fleet: "⚠️ [sw-eng] Security alert posted — see #alerts"
    │
    └── META
        ├── fleet-monitor: tracks unresolved alert
        ├── fleet-ops: includes in daily digest
        └── Proposed task: "Fix CVE in pydantic" for devops
```

### The Pattern

> "operations that triggers multiple things, multiple events"

Every fleet operation defines:
1. **Internal events** — what changes in MC (tasks, memory, approvals)
2. **Public events** — what changes on GitHub (branches, PRs, issues)
3. **Channel events** — what's broadcast on IRC (which channels, what format)
4. **Meta events** — what the system tracks (monitoring, digest, sync)

Some operations are:
- **Internal only** (board memory decision record → no public, no channel)
- **Public + internal** (PR created → GitHub + MC + IRC)
- **Channel only** (daily digest → IRC + board memory, no GitHub)
- **Cascading** (merge → task done → worktree cleanup → digest data → IRC)

> "in reverse internal but with a piece public, bigger or not or in reverse or equal"

The RATIO varies. Sometimes the public piece is big (PR with full changelog) and
the internal piece is small (task status change). Sometimes internal is big
(detailed board memory with reasoning) and public is just a reference.

The event chain system must support ALL combinations.

## Design

### Event Chain Registry

Each fleet operation registers its event chain:

```python
# In fleet/core/events.py
class EventChain:
    """Defines what happens when an operation occurs."""

    internal: list[InternalEvent]   # MC changes
    public: list[PublicEvent]       # GitHub changes
    channel: list[ChannelEvent]     # IRC messages
    meta: list[MetaEvent]           # System tracking
```

The MCP server tool handlers emit event chains, not individual API calls.
The event chain runner processes them in order, handling failures gracefully.

### Event Types

**Internal:** task_update, memory_post, approval_create, comment_post
**Public:** branch_push, pr_create, pr_comment
**Channel:** irc_message (with channel routing)
**Meta:** quality_check, sync_track, digest_collect

### Failure Handling

If one event in the chain fails, the others still execute.
Failed events are logged and retried. The chain is NOT atomic —
partial completion is acceptable (IRC notification failure shouldn't
block PR creation).

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M153 | Event chain model | Define chain structure, event types |
| M154 | Chain runner | Execute chains with failure handling |
| M155 | Operation → chain mapping | Each fleet tool defines its chain |
| M156 | Multi-surface publishing test | Verify all surfaces receive correct events |

---