# Tool Chain Investigation — Group Calls, Cross-Platform Propagation, Event Streams

**Date:** 2026-04-07
**Status:** Investigation — mapping what exists, what's missing, what needs wiring
**Scope:** Every fleet MCP tool → chain → cross-platform propagation

---

## PO Requirements (Verbatim, from this session)

> "only the main group calls were done, too many individual platform
> specific operations still are suggested"

> "its good to have them to understand the trees and original or
> individual possibilities but the truth is that the tools we will
> give to the agents do not need to be ambiguous or limited or
> 1 to 1 operations"

> "its only logical for a comment to propagate everywhere it needs
> and enter the event stream and trigger whatever it needs like
> notifications and such"

> "its normal that submitting something has post operations that have
> deterministic logic and propagation and/or cross-referencing and
> progress tracking through the multiple connected platforms"

> "e.g. the two boards having their own chat / comment and mention
> strategy and such"

---

## 1. Chain Infrastructure — What Exists (SOLID)

### EventChain (fleet/core/event_chain.py)
- Typed events per surface: INTERNAL, PUBLIC, CHANNEL, NOTIFY, PLANE, META
- EventChain class with add(), surface property accessors
- ChainResult with ok, executed, failed, errors
- _trail_event() helper for standardized trail recording

### ChainRunner (fleet/core/chain_runner.py)
- Executes all events in a chain sequentially
- Failure tolerance: non-required events fail without breaking chain
- Required events failing = chain failure
- Emits CloudEvent for every chain execution
- Generates cross-references between surfaces
- Surface handlers: INTERNAL (MC), PUBLIC (GitHub), CHANNEL (IRC),
  NOTIFY (ntfy), PLANE (Plane API), META (logging)

### 8 Chain Builders (fleet/core/event_chain.py)
1. build_task_complete_chain — INTERNAL + PUBLIC + CHANNEL + NOTIFY + PLANE + META
2. build_alert_chain — INTERNAL + CHANNEL + NOTIFY
3. build_contribution_chain — INTERNAL (trail) + CHANNEL + PLANE
4. build_gate_request_chain — INTERNAL + CHANNEL + NOTIFY + trail
5. build_rejection_chain — INTERNAL + CHANNEL + trail
6. build_phase_advance_chain — INTERNAL + CHANNEL + NOTIFY + trail
7. build_transfer_chain — INTERNAL + CHANNEL + trail
8. build_sprint_complete_chain — INTERNAL + CHANNEL + NOTIFY

---

## 2. What's Wired vs Disconnected

### WIRED (tool uses chain runner):
| Tool | Chain Builder | Surfaces |
|------|--------------|----------|
| fleet_task_complete | build_task_complete_chain | ALL 6 surfaces ✓ |

### DISCONNECTED (chain builder exists but tool doesn't use it):
| Tool | Chain Builder Available | Tool Currently Does |
|------|----------------------|---------------------|
| fleet_alert | build_alert_chain | Direct: board memory + IRC (no chain runner) |
| fleet_contribute | build_contribution_chain | Direct: comment + custom field + own task done + event + trail + IRC + Plane comment |
| fleet_approve (reject) | build_rejection_chain | Direct: approval + status + comment + IRC + event + fix task |
| fleet_transfer | build_transfer_chain | Direct: custom field + comment + context package + Plane + event + IRC + mention |
| fleet_gate_request | build_gate_request_chain | Direct: board memory + IRC + ntfy + custom field + event + trail |
| (fleet_phase_advance) | build_phase_advance_chain | Tool NOT IMPLEMENTED |
| (sprint milestone) | build_sprint_complete_chain | Used by orchestrator, not a tool |

### NO CHAIN BUILDER EXISTS (tool does direct platform calls):
| Tool | Current Behavior | Missing Propagation |
|------|-----------------|---------------------|
| fleet_chat | board memory + IRC | No Plane, no events, no trail |
| fleet_task_progress | comment + custom field + partial events | No Plane, no IRC, no trail |
| fleet_commit | git + comment | No Plane, no events, no trail |
| fleet_task_accept | status + comment + IRC + plan assessment | No Plane, no events, no trail |
| fleet_pause | comment + IRC | No Plane, no events, no trail, no PM mention |
| fleet_escalate | board memory + IRC + ntfy | No events, no trail |
| fleet_task_create | task + IRC | No Plane issue, no events, no trail |
| fleet_artifact_create | object + Plane HTML + completeness + comment | No events, no trail |
| fleet_artifact_update | object + Plane HTML + completeness + comment | No events, no trail |

---

## 3. The Propagation Model — What SHOULD Happen

### For every agent-facing tool call:

```
Agent calls ONE tool
    ↓
Tool builds EventChain (chain builder)
    ↓
ChainRunner executes across surfaces:
    ├── INTERNAL (MC): task update, comment, board memory, approval
    ├── PUBLIC (GitHub): branch, PR (if applicable)
    ├── CHANNEL (IRC): notification to relevant channel
    ├── NOTIFY (ntfy): PO notification (if severity warrants)
    ├── PLANE (Plane): issue update, comment, label sync (if linked)
    ├── META: event emission, trail recording, metrics
    └── Cross-refs generated between surfaces
```

### Cross-platform comment/mention strategy:

A comment posted on an ops board task should:
1. Appear as a comment on the ops board task ✓ (INTERNAL)
2. Appear as a comment on the linked Plane issue (PLANE — if linked)
3. Appear in IRC in the relevant channel (CHANNEL)
4. Enter the event stream (META — via CloudEvent)
5. Record trail (INTERNAL — board memory with trail tag)
6. Route @mentions to target agent's heartbeat context (INTERNAL — mention tag)
7. Trigger ntfy if the mention is PO/human (NOTIFY)

A mention on Plane should:
1. Be detected by the Plane watcher daemon
2. Create an event in the event stream
3. Route to the mentioned agent's heartbeat context
4. Appear in IRC if relevant

### Cross-platform state strategy:

A task status change on ops board should:
1. Update the ops board status ✓ (INTERNAL)
2. Update the linked Plane issue state (PLANE)
3. Update Plane labels (stage:X, readiness:N) (PLANE)
4. Notify IRC (CHANNEL)
5. Enter event stream (META)
6. Record trail (INTERNAL)

---

## 4. Platform-Specific Tools — What They Should Become

### Currently exposed as agent-facing tools:
- fleet_plane_status — returns Plane project state
- fleet_plane_sprint — returns sprint details
- fleet_plane_sync — triggers bidirectional sync
- fleet_plane_create_issue — creates Plane issue
- fleet_plane_comment — posts Plane comment
- fleet_plane_update_issue — updates Plane issue fields
- fleet_plane_list_modules — lists Plane modules

### What they should be:

**fleet_plane_status / fleet_plane_sprint:**
→ This data should be in the PM's pre-embedded context (heartbeat data).
The PM doesn't need to call a tool — the orchestrator pre-computes it.
Could remain as an on-demand tool for ad-hoc queries, but primary
access is through pre-embedded context.

**fleet_plane_sync:**
→ Bidirectional sync runs as a daemon (fleet/cli/daemon.py sync daemon).
Agent-facing tool is useful for PM to force immediate sync.
Should remain but is infrastructure, not daily agent work.

**fleet_plane_create_issue:**
→ Should be PART OF fleet_task_create's chain. When PM creates a task
on the ops board, the chain automatically creates the linked Plane issue
if the project is configured. The agent calls ONE tool (fleet_task_create),
the chain handles both boards.

**fleet_plane_comment:**
→ Should be PART OF comment propagation chains. When any tool posts a
comment on an ops board task, the chain propagates to the linked Plane
issue automatically. No separate tool needed.

**fleet_plane_update_issue:**
→ Should be PART OF state/field update chains. When a task's status,
readiness, or stage changes on the ops board, the chain updates the
Plane issue state and labels. No separate tool needed.

**fleet_plane_list_modules:**
→ Infrastructure query. Could be part of pre-embedded context for PM.

### Summary: What agents should see

**Keep as agent-facing (group calls):**
All current non-Plane tools — but rewired through chain runner.

**Internalize (become part of chains):**
- fleet_plane_comment → part of comment propagation
- fleet_plane_update_issue → part of state propagation
- fleet_plane_create_issue → part of fleet_task_create chain

**Keep for specific roles (infrastructure queries):**
- fleet_plane_status → PM/writer context or on-demand
- fleet_plane_sprint → PM context or on-demand
- fleet_plane_sync → PM force-sync
- fleet_plane_list_modules → PM/writer planning

---

## 5. Chain Builders Needed

### New chain builders to create (following existing pattern):

```python
# Comment propagation — used by fleet_chat, fleet_task_progress, any comment
def build_comment_chain(
    agent_name, task_id, task_title, content,
    mention="", channel="#fleet",
) -> EventChain:
    # INTERNAL: post_board_memory (tagged with mention if present)
    # INTERNAL: post_comment on task (if task_id)
    # CHANNEL: IRC notification
    # PLANE: post_comment on linked issue (if linked)
    # META: event emission
    # trail event

# Task acceptance — fleet_task_accept
def build_accept_chain(
    agent_name, task_id, task_title, plan_summary,
) -> EventChain:
    # INTERNAL: update_task_status → in_progress
    # INTERNAL: post_comment with plan
    # CHANNEL: IRC #fleet — started
    # PLANE: update issue state + comment
    # META: event emission
    # trail event

# Code commit — fleet_commit
def build_commit_chain(
    agent_name, task_id, files, message,
) -> EventChain:
    # INTERNAL: post_comment on task
    # CHANNEL: IRC (optional, could be noisy)
    # PLANE: post_comment on linked issue
    # META: event emission, methodology check
    # trail event

# Task creation — fleet_task_create
def build_task_create_chain(
    creator, task_id, task_title, parent_task_id,
    agent_name, task_type, project,
) -> EventChain:
    # INTERNAL: post_comment on parent (if parent exists)
    # CHANNEL: IRC #fleet
    # PLANE: create_issue on linked project (if configured)
    # META: event emission
    # trail event

# Pause/blocker — fleet_pause
def build_pause_chain(
    agent_name, task_id, task_title, reason, needed,
) -> EventChain:
    # INTERNAL: post_comment on task
    # INTERNAL: post_board_memory (mention PM)
    # CHANNEL: IRC #fleet — BLOCKED
    # PLANE: post_comment on linked issue
    # META: event emission
    # trail event

# Escalation — fleet_escalate
def build_escalation_chain(
    agent_name, task_id, title, details, question,
) -> EventChain:
    # INTERNAL: post_board_memory (escalation, po-required)
    # INTERNAL: post_comment on task (if task_id)
    # CHANNEL: IRC #alerts
    # NOTIFY: ntfy urgent to PO
    # PLANE: post_comment on linked issue
    # META: event emission
    # trail event

# Progress update — fleet_task_progress
def build_progress_chain(
    agent_name, task_id, task_title,
    done, next_step, blockers, progress_pct,
) -> EventChain:
    # INTERNAL: post_comment on task
    # INTERNAL: update custom field (task_progress)
    # CHANNEL: IRC (only at checkpoints: 50%, 90%)
    # PLANE: update labels (readiness), post_comment
    # META: event emission, checkpoint events
    # trail event

# Artifact operations — fleet_artifact_create, fleet_artifact_update
def build_artifact_chain(
    agent_name, task_id, artifact_type, field, completeness,
) -> EventChain:
    # INTERNAL: post_comment (artifact update summary)
    # PLANE: HTML already updated via transpose (done in tool)
    # META: event emission, completeness tracking
    # trail event
```

---

## 6. Wiring Plan — Per Tool

### Tools with existing chain builders (wire them in):

| Tool | Chain Builder | Wiring Work |
|------|--------------|-------------|
| fleet_alert | build_alert_chain | Replace direct board memory + IRC with chain runner |
| fleet_contribute | build_contribution_chain | Add chain runner call alongside existing logic |
| fleet_approve (reject) | build_rejection_chain | Add chain runner for rejection path |
| fleet_transfer | build_transfer_chain | Replace direct calls with chain runner |
| fleet_gate_request | build_gate_request_chain | Replace direct calls with chain runner |

### Tools needing new chain builders (create + wire):

| Tool | New Builder | Key Additions |
|------|-------------|---------------|
| fleet_chat | build_comment_chain | + Plane comment, + events, + trail |
| fleet_task_progress | build_progress_chain | + Plane labels/comment, + IRC at checkpoints, + trail |
| fleet_commit | build_commit_chain | + Plane comment, + events, + trail |
| fleet_task_accept | build_accept_chain | + Plane state/comment, + events, + trail |
| fleet_pause | build_pause_chain | + Plane comment, + events, + trail, + PM mention |
| fleet_escalate | build_escalation_chain | + events, + trail (ntfy already there) |
| fleet_task_create | build_task_create_chain | + Plane issue creation, + events, + trail |
| fleet_artifact_create/update | build_artifact_chain | + events, + trail (Plane HTML already there) |

### Tools that don't need chains (read-only):
- fleet_read_context — read only
- fleet_agent_status — read only
- fleet_artifact_read — read only
- fleet_heartbeat_context — read only
- fleet_task_context — read only
- fleet_request_input — creates a mention/task, could have a light chain

### Tools to internalize (become part of other chains):
- fleet_plane_comment → part of comment chains
- fleet_plane_update_issue → part of state update chains
- fleet_plane_create_issue → part of fleet_task_create chain

### Tools to keep for specific infrastructure queries:
- fleet_plane_status — PM/writer context
- fleet_plane_sprint — PM context
- fleet_plane_sync — PM force-sync
- fleet_plane_list_modules — PM/writer planning

---

## 7. The Dual-Board Comment/Mention Strategy

### Ops Board (OCMC)
- **Comments:** on task (mc.post_comment) — visible to assigned agent
- **Board memory:** fleet-wide tagged (mc.post_memory) — mention routing via tags
- **Mentions:** `mention:{agent}` tag → agent sees in heartbeat context MESSAGES
- **Special mentions:** `mention:all` (everyone), `mention:lead` (fleet-ops)

### Plane
- **Comments:** on issue (plane.add_comment) — visible to watchers
- **Mentions:** @agent in comment HTML — detected by plane_watcher daemon
- **Labels:** state, readiness, stage labels for visual tracking
- **Description HTML:** artifact sections via transpose layer

### Cross-Platform Routing
When an agent posts a comment on ops board:
1. Comment appears on ops board task
2. If task linked to Plane issue → comment propagated to Plane issue
3. If comment has @mention → mention tag on ops board, @mention in Plane comment
4. IRC notification
5. Event emitted for routing

When someone comments on Plane:
1. plane_watcher daemon detects new comment
2. Creates board memory entry with mention routing
3. Agent sees in next heartbeat context

This is BIDIRECTIONAL but ASYMMETRIC:
- Ops board → Plane: automatic via chains (every comment propagates)
- Plane → ops board: via plane_watcher daemon (poll-based, ~120s)

---

## 8. Event Stream Integration

Every tool call should emit a CloudEvent:
- Event type: `fleet.{operation}` (e.g., fleet.chat.message, fleet.task.commit)
- Source: `fleet/mcp/tools/{tool_name}`
- Subject: task_id (when applicable)
- Recipient: mentioned agent or "all"
- Priority: based on severity/importance
- Tags: operation-specific
- Surfaces: where the event was published

The chain runner ALREADY does this (lines 86-102 in chain_runner.py):
```python
store.append(create_event(
    f"fleet.chain.{chain.operation}",
    source="fleet/core/chain_runner",
    ...
))
```

So wiring tools through chain runner automatically gets event stream integration.

---

## 9. Implementation Order

### Phase 1: Build missing chain builders
Create 8 new builders in event_chain.py following the existing pattern.
Test each builder independently.

### Phase 2: Wire existing builders into tools
Replace direct platform calls in tools.py with chain runner execution
for the 5 tools that have existing builders.

### Phase 3: Wire new builders into tools
Replace direct platform calls in tools.py with chain runner execution
for the 8 tools with new builders.

### Phase 4: Internalize Plane-specific tools
Make fleet_task_create chain create Plane issues.
Make comment chains propagate to Plane.
Make state update chains update Plane labels/state.

### Phase 5: Update TOOLS.md
NOW the chains actually fire. Document them truthfully.
Generate per-role TOOLS.md from tool-roles.yaml + verified chains.

### Phase 6: Test
- Each chain builder fires correct events
- Chain runner handles partial failures
- Plane propagation works when connected, gracefully skips when not
- Trail recorded for every operation
- Events emitted for every operation
- IRC notifications reach correct channels
- @mentions route correctly across platforms

---

## 10. What This Means for TOOLS.md Generation

The TOOLS.md can only document what ACTUALLY FIRES. Currently:
- fleet_task_complete — full chain (truthfully documentable)
- Everything else — partial chains (would be lying to document full propagation)

After the chain wiring:
- Every tool has full cross-platform propagation
- TOOLS.md can truthfully document: "this one call does everything"
- Per-role filtering from tool-roles.yaml
- Agent doesn't need to think about platforms — the chain handles it

The TOOLS.md generation is BLOCKED on chain wiring. Not because we can't
generate files, but because generating files that describe capabilities
the tools don't have is LYING to the agents.

---

## 11. Scope Assessment

| Work | Effort | What |
|------|--------|------|
| 8 new chain builders | Medium | Follow existing pattern, ~40-60 lines each |
| Wire 5 existing builders | Small | Replace direct calls with chain runner |
| Wire 8 new builders | Medium | Refactor tool functions to use chain runner |
| Plane internalization | Medium | chain builder additions + tool simplification |
| Testing | Large | Per-chain, per-surface, cross-platform, failure tolerance |
| TOOLS.md generation | Small (after chains) | tool-roles.yaml + generator script |

Total: significant infrastructure work. Not a quick fix.
But the chain infrastructure IS built. The runner IS built.
The surface handlers ARE built. It's wiring, not building from scratch.
