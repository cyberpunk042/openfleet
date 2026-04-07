# Tool Chain Elevation — Group Calls, Tree Execution, Cross-Platform Propagation

**Date:** 2026-04-07
**Status:** Investigation + Reasoning — full analysis before implementation
**Scope:** Every MCP tool → elevated tree → cross-platform propagation → TOOLS.md generation
**Depends on:** fleet-elevation/24 (tool call trees), fleet-elevation/04 (brain), fleet-elevation/20 (anti-corruption), fleet-elevation/15 (synergy), systems/04 (event bus), systems/08 (MCP tools), systems/18 (notifications)
**Part of:** Path-to-live Phase C (Brain Evolution) — enables Phase B completion (TOOLS.md)

---

## PO Requirements (Verbatim)

> "chain is calling multiple tools, not just small process and
> transformation but also add a comment to the mc board for example
> and auto adding it to the task on Plane and etc.... a tree map to
> generate multiple tool call from a single one."

> "only using specific tool when necessary but also aiming for group
> calls."

> "agents need to call the right things that will do the right chains
> of actions... you dont want to have to manually update everywhere"

> "its only logical for a comment to propagate everywhere it needs
> and enter the event stream and trigger whatever it needs like
> notifications and such"

> "its normal that submitting something has post operations that have
> deterministic logic and propagation and/or cross-referencing and
> progress tracking through the multiple connected platforms"

> "e.g. the two boards having their own chat / comment and mention
> strategy and such"

> "only the main group calls were done, too many individual platform
> specific operations still are suggested"

> "its good to have them to understand the trees and original or
> individual possibilities but the truth is that the tools we will
> give to the agents do not need to be ambiguous or limited or
> 1 to 1 operations"

> "no matter from where I mention, that it be internal chat or Plane,
> or if I change something manually on the platform, you must detect
> and record the event and do the appropriate chain of operations"

> "always cross reference, like when updating a task on Plane you can
> say it in the internal chat naturally"

> "why call 5 tools when you can just call a chain that does it all?
> it a mix of communication and logic and pragmatism"

> "Where ever we can take this pattern to improve the work and the flow
> and the logic we will."

> "WE have to make it possible for the agents to do their work with
> clear chain entries, ins and outs and middles and groups of operations."

> "we need to do the right directive so the AI know if it need to use
> this bus or this bus and know that it will do this chain naturally and
> do this and that and so on."

---

## What The PO Is Saying — Distilled Without Conflation

These requirements speak to several distinct but connected things:

### 1. Group Calls = Trees, Not Chains

A "group call" is ONE agent-facing tool call that triggers a TREE of real internal operations. Not a flat sequence. A tree with branches — some independent, some sequential, each with its own failure mode. The agent calls ONE tool. The system executes the TREE.

This is NOT the same as:
- A "side effect" (passive consequence of an action)
- A "notification" (just telling someone something happened)
- A "chain" in the flat sequential sense (event after event)

It IS:
- A tree of actual function calls (mc.update_task, mc.post_comment, plane.post_comment, irc.notify, events.emit, mc.post_memory)
- With independent branches (IRC failing doesn't block Plane)
- With per-operation failure criticality (MC is source of truth → critical; IRC is notification → best-effort; Plane is display → retryable)
- With sequential dependencies within branches (create_approval AFTER update_task)

### 2. Cross-Platform Propagation = Surfaces Connected, Not Isolated

When something happens on one surface, ALL relevant surfaces should know. A comment on OCMC propagates to the linked Plane issue, appears in IRC, enters the event stream, records trail. This is deterministic — not the agent's job to manually update each surface. The tree handles it.

This is NOT the same as:
- "Sync" (bidirectional replication of state)
- The agent calling fleet_plane_comment separately

It IS:
- Automatic propagation as part of the tree
- OCMC → Plane: automatic via tree (every relevant operation propagates)
- Plane → OCMC: via plane_watcher daemon (poll-based, asymmetric by design)
- Mention routing across surfaces (@agent in OCMC → tag in board memory → agent sees in heartbeat; @agent in Plane → watcher detects → board memory)

### 3. Individual Platform Tools = Internalized Into Trees

The fleet_plane_comment, fleet_plane_update_issue, fleet_plane_create_issue tools exist as 1-to-1 platform operations. The PO says these should be PART OF the trees, not separate agent-facing tools. When fleet_task_create runs, the tree auto-creates the linked Plane issue. When fleet_chat runs, the tree auto-propagates to the linked Plane issue.

This is NOT the same as:
- Removing all Plane tools (fleet_plane_status, fleet_plane_sync stay as infrastructure queries for PM)
- Making Plane mandatory (trees gracefully skip Plane when not configured)

It IS:
- fleet_plane_comment → absorbed into comment propagation trees
- fleet_plane_update_issue → absorbed into state propagation trees
- fleet_plane_create_issue → absorbed into fleet_task_create tree
- fleet_plane_status, fleet_plane_sprint, fleet_plane_sync, fleet_plane_list_modules → remain as PM/writer infrastructure queries

### 4. Config Drives Generation, Generation Documents Reality

tool-roles.yaml is CONFIG that wires which agent receives which tool directives in their generated TOOLS.md. tool-chains.yaml is CONFIG that documents what each tool's tree does. generate-tools-md.sh reads both configs + tools.py and produces per-role TOOLS.md files.

This is NOT documentation about what exists. It IS configuration that drives behavior.

The constraint: tool-chains.yaml must describe what ACTUALLY fires. TOOLS.md must be truthful. If the tree doesn't fire Plane propagation, tool-chains.yaml must not claim it does. After the trees are wired, tool-chains.yaml is updated, TOOLS.md is regenerated, and agents receive accurate information about what their tools do.

### 5. The Autocomplete Chain Depends On This

The TOOLS.md at injection position 4 tells the agent what ONE call does. "You do NOT need to: push code, create PR, notify reviewers, update Plane." If this is accurate, the autocomplete chain works — the agent trusts one call and doesn't try to manually replicate the tree. If TOOLS.md is wrong, the autocomplete chain breaks — the agent doesn't know what's automatic and might try manual operations.

This connects to anti-corruption Line 1 (structural prevention): making correct behavior the path of least resistance. If the tree handles everything, the agent's natural action is ONE tool call. Deviation (calling individual platform tools) requires fighting the autocomplete chain.

### 6. Trail Recording = First-Class Concern

Every tree records a trail event. Even if other operations fail. The trail captures what was ATTEMPTED — who did what, when, for which task. This feeds the accountability generator (trail reconstruction), fleet-ops review (methodology verification), and the immune system (trail gap detection).

Today most tools don't record trail. This is a gap that makes fleet-ops review incomplete and accountability-generator non-functional.

---

## Architecture — Two Patterns, Two Contexts

### Pattern 1: Tool Trees (flat execution via ChainRunner)

When an agent calls a tool, the tool:
1. Does its **primary domain logic** (the thing that MUST succeed — git commit, MC status update, task creation)
2. Builds a **tree** as an EventChain for propagation (the things that SHOULD happen — IRC, Plane, trail, events, cross-refs)
3. Fires the tree via **ChainRunner** (best-effort, failure-tolerant per operation)
4. Returns result from step 1 regardless of tree outcome

The primary action is OUTSIDE the tree. The tree handles propagation. This means: if ChainRunner crashes, the primary action already succeeded. The agent gets a success response. IRC/Plane/trail catch up eventually.

fleet-elevation/24 explicitly states: "CRITICAL CODE AWARENESS: The tree execution engine ALREADY EXISTS. Do not create new modules — evolve existing ones."

Existing infrastructure to evolve:
- `fleet/core/event_chain.py` — EventChain, EventSurface, Event, 8 chain builders
- `fleet/core/chain_runner.py` — ChainRunner with 6 surface handlers
- `fleet/core/smart_chains.py` — DispatchContext, pre-computed batch operations
- `fleet/core/cross_refs.py` — event → cross-reference generation (pure logic)
- `fleet/core/events.py` — CloudEvents store, 47 event types, agent feeds

### Pattern 2: Chain Registry (reactive cascading via orchestrator)

When events fire, registered handlers react. Handlers can emit NEW events that cascade. This is the brain's Layer 2 — the nervous system. Designed in fleet-elevation/04 but NOT yet in code.

Examples from the design:
- `fleet.methodology.stage_changed` → create_contribution_opportunities + notify + trail
- `fleet.methodology.readiness_changed` → checkpoint at 50%, gate at 90%
- `fleet.contribution.posted` → propagate to target + check completeness + if all received notify PM

This is DIFFERENT from tool trees:
- Tool trees = "I called a tool, execute the tree" (synchronous, within the tool call)
- Chain registry = "An event happened, who cares?" (asynchronous, between orchestrator cycles)

Both patterns exist in the design. Tool trees are the immediate work. Chain registry is brain evolution (separate milestone).

### What The ChainRunner Needs to Support

Current handler actions per surface:

| Surface | Existing Actions | Missing Actions |
|---------|-----------------|-----------------|
| INTERNAL | update_task_status, create_approval, post_board_memory, post_comment | update_custom_fields |
| PUBLIC | push_branch, create_pr | (sufficient) |
| CHANNEL | notify_irc | (sufficient) |
| NOTIFY | ntfy_publish | (sufficient) |
| PLANE | update_issue_state, post_comment | create_issue, update_labels |
| META | update_metrics | (sufficient — chain-level CloudEvent emission already works) |

New actions needed:
- **INTERNAL: update_custom_fields** — for setting readiness, stage, agent_name, gate_pending, contribution data via `mc.update_task(custom_fields=...)`
- **PLANE: create_issue** — for fleet_task_create tree to auto-create linked Plane issues (when project is configured)
- **PLANE: update_labels** — for readiness/stage label sync on linked Plane issues

### Tree Execution Principles (from fleet-elevation/24)

**Parallel where possible:**
- mc.post_comment AND irc.send → parallel (independent)
- mc.create_approval AFTER mc.update_task → sequential (needs task in review)
- plane_sync AFTER mc.update_task → sequential (needs new status)
- events.emit AND mc.post_memory → parallel (independent)

**Failure isolation per operation:**
- mc.update_task fails → STOP tree (MC is source of truth, must succeed)
- irc.send fails → log, continue (notification, not critical)
- plane_sync fails → queue for retry (display surface, not source of truth)
- ntfy fails → log, continue (notification, not critical)
- trail always records — even if other operations fail

**The current ChainRunner approximation:**
Events with `required=True` → failure stops the chain. Events with `required=False` → failure logged, chain continues. This is a boolean approximation of the three-level criticality (critical / best-effort / retryable). For now, it's sufficient: critical operations are `required=True` and placed first (fail-fast). Non-critical operations are `required=False`. Retry/queue capability is a future evolution.

---

## Per-Tool Gap Analysis — Current vs Elevated Tree

### fleet_read_context (read-only — no tree needed)
- **Current:** MC get_task + list_memory + list_tasks + list_agents + events query
- **Elevated:** + context_assembly.assemble_task_context() + phase standards
- **Gap:** Phase standards injection not implemented. Otherwise complete.

### fleet_task_accept
- **Current:** MC update_task(status=in_progress) + post_comment(plan) + IRC notify_event
- **Elevated:** + Plane update state/comment + events.emit(fleet.task.accepted) + trail + plan_references_verbatim check
- **Gap:** No Plane propagation, no event emission, no trail, no verbatim check

### fleet_task_progress
- **Current:** MC post_comment + update_task(custom_fields.task_progress) + partial event at checkpoints + manual trail
- **Elevated:** + Plane labels/comment + IRC at checkpoints (50%, 90%) + gate request at 90% + proper trail
- **Gap:** No Plane propagation, IRC only at checkpoints but not wired, no gate auto-request at 90%

### fleet_commit
- **Current:** git add + git commit. Nothing else.
- **Elevated:** + MC post_comment(commit_summary) + Plane comment + events.emit(fleet.task.commit) + trail + methodology verification
- **Gap:** No MC comment, no Plane, no events, no trail. Most disconnected tool.

### fleet_task_complete
- **Current:** Full tree via ChainRunner — push + PR + MC status + approval + IRC + ntfy + Plane + events + cross-refs. Plus labor stamp, review gates, skill compliance.
- **Elevated:** + notify_contributors + evaluate_parent improvements + trail
- **Gap:** Smallest gap. Contributor notification and parent evaluation could be improved. Trail recording partial.

### fleet_chat
- **Current:** MC post_memory(tagged) + IRC notify
- **Elevated:** + Plane comment on linked issue (if task context) + events.emit(fleet.chat.message) + trail (if task_id) + ntfy if @po/@human
- **Gap:** No Plane, no events, no trail, no PO notification on @human mention

### fleet_alert
- **Current:** MC post_memory(tagged) + IRC notify (routed by severity)
- **Elevated:** + events.emit(fleet.alert.posted) + trail + ntfy for critical/high + security_hold for security category
- **Gap:** No events, no trail, no ntfy (existing chain builder has ntfy but isn't wired), no security_hold. Chain builder build_alert_chain EXISTS but tool does direct calls instead.

### fleet_pause
- **Current:** MC post_comment + IRC notify_event
- **Elevated:** + Plane comment + events.emit(fleet.task.blocked) + trail + board_memory with PM mention
- **Gap:** No Plane, no events, no trail, no PM mention routing

### fleet_escalate
- **Current:** MC post_memory + MC post_comment + IRC notify + ntfy publish
- **Elevated:** + events.emit(fleet.escalation) + trail + Plane comment
- **Gap:** No events, no trail, no Plane. ntfy already works (direct call).

### fleet_task_create
- **Current:** MC create_task + IRC notify. Cascade depth check.
- **Elevated:** + Plane create_issue (linked) + MC post_comment on parent + events.emit(fleet.task.created) + trail + contribution opportunity event if contribution_type
- **Gap:** No Plane issue creation, no parent comment, no events, no trail, no contribution tracking

### fleet_approve
- **Current:** MC approve_approval + MC update_task(status) + MC post_comment + IRC notify + event emission + auto-create fix task on rejection
- **Elevated (approve):** + Plane state→done + trail + evaluate_parent + sprint_progress
- **Elevated (reject):** + Plane state→in_progress + readiness regression + trail + doctor signal. Chain builder build_rejection_chain EXISTS but not wired.
- **Gap:** No Plane propagation, no trail, rejection chain not wired

### fleet_contribute
- **Current:** MC post_comment + update_custom_fields + mark own task done + event + trail + IRC + Plane comment + mention routing. Most complete non-chain tool.
- **Elevated:** + check_contribution_completeness (all required received? → notify PM). Chain builder build_contribution_chain EXISTS but not wired.
- **Gap:** Completeness check not wired. Existing chain builder not used.

### fleet_transfer
- **Current:** MC update_task(agent_name) + MC post_comment + trail + mention + Plane comment + IRC + event. Fairly complete.
- **Elevated:** + context packaging (artifacts, contributions, trail summary) for receiving agent. Chain builder build_transfer_chain EXISTS but not wired.
- **Gap:** Context packaging minimal. Chain builder not wired.

### fleet_gate_request
- **Current:** MC post_memory(tagged) + MC update_task(gate_pending) + ntfy + IRC + trail + event. Fairly complete.
- **Elevated:** Matches current. Chain builder build_gate_request_chain EXISTS but not wired.
- **Gap:** Chain builder not wired (tool does direct calls that match).

### fleet_artifact_create / fleet_artifact_update
- **Current:** Object create/update + Plane HTML transpose + completeness check + MC post_comment
- **Elevated:** + events.emit(fleet.artifact.created/updated) + trail + readiness suggestion propagation
- **Gap:** No events, no trail, readiness suggestion exists but not propagated to Plane labels

### fleet_request_input
- **Current:** MC post_memory(mention) + MC post_comment + trail + IRC + event
- **Elevated:** + check if contribution task exists for this role
- **Gap:** No contribution task existence check

### fleet_notify_human (simple — no tree needed)
- **Current:** ntfy publish. Complete.
- **Gap:** None.

### fleet_agent_status (read-only — no tree needed)
- **Current:** MC list_agents + list_tasks + list_approvals. Complete.
- **Gap:** None.

### fleet_task_context / fleet_heartbeat_context (read-only — no tree needed)
- **Current:** context_assembly. Complete.
- **Gap:** None.

### Plane Tools — Internalization Decision

| Tool | Decision | Reason |
|------|----------|--------|
| fleet_plane_status | **KEEP** | PM/writer infrastructure query. No tree equivalent. |
| fleet_plane_sprint | **KEEP** | PM infrastructure query. No tree equivalent. |
| fleet_plane_sync | **KEEP** | PM force-sync. Infrastructure operation. |
| fleet_plane_list_modules | **KEEP** | PM/writer planning query. No tree equivalent. |
| fleet_plane_create_issue | **INTERNALIZE** | Becomes part of fleet_task_create tree (auto-create linked issue) |
| fleet_plane_comment | **INTERNALIZE** | Becomes part of comment propagation in all trees |
| fleet_plane_update_issue | **INTERNALIZE** | Becomes part of state/label propagation in all trees |

Internalized tools can remain in code for direct use by PM in edge cases, but agents should not need to call them — the trees handle it.

---

## Missing Tool: fleet_phase_advance

tool-roles.yaml lists this for PM. fleet-elevation/24 has its complete tree. It does NOT exist in tools.py.

```
fleet_phase_advance(task_id, from_phase, to_phase, evidence)
├── phases.check_phase_standards(task, from_phase)
│   └── if not met → return error
├── MC post_memory [gate, phase-advance, po-required]
├── IRC #gates
├── ntfy (high priority)
├── events.emit(fleet.phase.advance_requested)
└── trail
```

This needs to be built as a new tool.

---

## Existing Chain Builders — Status

8 builders exist in event_chain.py. Their wiring status:

| Builder | Used By | Status |
|---------|---------|--------|
| build_task_complete_chain | fleet_task_complete | **WIRED** via ChainRunner ✓ |
| build_alert_chain | fleet_alert | **NOT WIRED** — tool does direct calls |
| build_contribution_chain | fleet_contribute | **NOT WIRED** — tool does direct calls |
| build_gate_request_chain | fleet_gate_request | **NOT WIRED** — tool does direct calls |
| build_rejection_chain | fleet_approve (reject path) | **NOT WIRED** — tool does direct calls |
| build_transfer_chain | fleet_transfer | **NOT WIRED** — tool does direct calls |
| build_phase_advance_chain | (fleet_phase_advance) | **NO TOOL** — tool doesn't exist |
| build_sprint_complete_chain | (orchestrator) | Used by orchestrator, not a tool |

### New Builders Needed

| Builder | For Tool | Key Operations |
|---------|----------|----------------|
| build_comment_chain | fleet_chat | board_memory + IRC + Plane comment + events + trail + ntfy if @po |
| build_accept_chain | fleet_task_accept | MC comment + IRC + Plane state/comment + events + trail + verbatim check |
| build_progress_chain | fleet_task_progress | MC comment + Plane labels/comment + IRC at checkpoints + events + trail |
| build_commit_chain | fleet_commit | MC comment + Plane comment + events + trail + methodology verify |
| build_pause_chain | fleet_pause | MC comment + board_memory(PM mention) + IRC + Plane comment + events + trail |
| build_escalation_chain | fleet_escalate | board_memory + IRC #alerts + Plane comment + events + trail (ntfy stays direct — primary action) |
| build_task_create_chain | fleet_task_create | parent comment + IRC + Plane create_issue + events + trail |
| build_artifact_chain | fleet_artifact_create/update | MC comment + events + trail + readiness suggestion |

Each follows the existing pattern in event_chain.py: create EventChain, add events per surface, return chain. The ChainRunner executes it.

---

## Implementation Sequence

### Step 1: Evolve ChainRunner (new handler actions)

Add to `_handle_internal`:
- `update_custom_fields` action → `mc.update_task(board_id, task_id, custom_fields={...})`

Add to `_handle_plane`:
- `create_issue` action → `plane.create_issue(workspace, project_id, title, description_html, priority, label_ids)`
- `update_labels` action → `plane.update_issue(workspace, project_id, issue_id, label_ids=[...])`

### Step 2: Build new chain builders (8)

In event_chain.py, following the existing pattern. Each builder:
- Creates EventChain with operation name and source_agent
- Adds events per surface with appropriate required/optional flags
- Critical operations (MC source of truth) are required=True and FIRST
- Non-critical operations (IRC, Plane, ntfy) are required=False
- Trail event via _trail_event() helper — always last, always required=False
- Plane events include issue_id/project_id params (empty — filled by caller if linked)

### Step 3: Wire existing builders into tools (5)

For fleet_alert, fleet_contribute, fleet_approve(reject), fleet_transfer, fleet_gate_request:
- The builder already exists and matches the tool's elevated tree
- Add ChainRunner construction (same pattern as fleet_task_complete)
- Add chain execution after primary action
- Add fallback if chain fails (direct IRC/memory, same pattern as fleet_task_complete)
- Keep existing _emit_event calls as belt-and-suspenders

### Step 4: Wire new builders into tools (8)

For fleet_chat, fleet_task_accept, fleet_task_progress, fleet_commit, fleet_pause, fleet_escalate, fleet_task_create, fleet_artifact_create/update:
- Build chain after primary action succeeds
- Execute via ChainRunner
- Some tools need refactoring: fleet_commit currently does NOTHING after git commit — the entire propagation tree is new

### Step 5: Build fleet_phase_advance tool

New tool in tools.py following the tree from fleet-elevation/24.
Uses build_phase_advance_chain (already exists).

### Step 6: Internalize Plane operations

- fleet_task_create tree adds PLANE create_issue event (when project configured and parent has plane_issue_id)
- Comment propagation trees add PLANE post_comment event (when task has plane_issue_id)
- State propagation trees add PLANE update_issue_state + update_labels events

### Step 7: Update configs

- tool-chains.yaml: update chain descriptions to match what actually fires
- tool-roles.yaml: verify per-role tool sets are correct (fleet_phase_advance now exists)

### Step 8: Regenerate TOOLS.md

- Run generate-tools-md.sh for all 10 agents
- Verify output matches the standard (What/When/Chain/Input/"You do NOT need to")
- Verify per-role filtering is correct (engineer doesn't see PM tools)

### Step 9: Tests

Per fleet-elevation/24 testing requirements:
- Each tree fires all operations (happy path)
- Each tree handles operation failure (critical stops, non-critical continues)
- Trail event always recorded
- Stage enforcement blocks inappropriate calls
- Plane sync fires when plane_issue_id exists, skips gracefully when not
- Events emitted with correct data
- Cross-references generated where applicable

Existing test patterns in test_event_chain.py and test_chain_runner.py provide the template.

---

## What This Enables (Downstream Impact)

### TOOLS.md Becomes Truthful
Agents receive accurate information about what their tools do. "You do NOT need to: push code, create PR, notify reviewers, update Plane" — because the tree actually handles all of that.

### Autocomplete Chain Strengthens (Anti-Corruption Line 1)
When TOOLS.md accurately describes group calls, the agent's natural action is ONE tool call. No need to manually update Plane, post to IRC, record trail. The correct behavior is the default. Deviation requires fighting the autocomplete chain.

### Fleet-Ops Gets Real Trail Data
Every operation records trail. Fleet-ops can verify: did the task go through all required stages? Were contributions received? Was the PO gate approved? Were stage transitions authorized? The review becomes REAL because the data exists.

### Accountability-Generator Can Function
Trail events tagged `trail` + `task:{id}` enable full task history reconstruction. The compliance reports and audit trails have data to work with.

### PM Gets Contribution Completeness Signals
When fleet_contribute fires its tree, the completeness check notifies PM when all required contributions are received. PM knows the task is ready for work stage advancement without manually checking.

### PO Sees Plane Updates Automatically
Every relevant operation propagates to the linked Plane issue. PO checks Plane → sees comments, state changes, labels, artifact HTML — all automatically populated by trees. No manual sync needed.

### Cross-References Connect All 6 Surfaces
The ChainRunner already calls generate_cross_refs(). With all tools wired through the runner, cross-references fire for every operation — not just fleet_task_complete.

### Brain Layer 2 Has Real Events to React To
The chain registry (future) needs events to cascade from. With all tools emitting proper events, the brain can register handlers: stage_changed → create contributions, readiness_changed → gate enforcement, contribution.posted → completeness check.

---

## Relationship to Other Work

| Work Item | Relationship |
|-----------|-------------|
| Agent elevation (Phase B) | TOOLS.md generation is BLOCKED on chain wiring. Can't document chains that don't fire. |
| Brain evolution (Phase C) | Chain registry needs proper events from tools. This work produces those events. |
| Contribution flow (Phase E) | fleet_contribute tree needs completeness checking. Brain contribution creation needs events to react to. |
| Phase system (Phase E) | fleet_phase_advance tool built here. Phase standards injection is separate. |
| First live test (Phase D) | Live test validates: dispatch → agent → tool calls → trees fire → review. Trees must work. |
| Immune system | Trail gaps become detectable. Doctor can check trail completeness. |
| Standards | Artifact completeness → readiness → Plane labels. The propagation chain from standards through methodology to Plane. |

---

## Files Affected

| File | Change Type | Description |
|------|------------|-------------|
| fleet/core/chain_runner.py | EVOLVE | Add update_custom_fields (INTERNAL), create_issue + update_labels (PLANE) |
| fleet/core/event_chain.py | EVOLVE | Add 8 new chain builders following existing pattern |
| fleet/mcp/tools.py | EVOLVE | Wire all builders into tools, add fleet_phase_advance |
| config/tool-chains.yaml | UPDATE | Match chain descriptions to what actually fires |
| config/tool-roles.yaml | UPDATE | Add fleet_phase_advance to PM |
| scripts/generate-tools-md.sh | VERIFY | Should work as-is once configs are accurate |
| fleet/tests/core/test_event_chain.py | EXTEND | Tests for 8 new builders |
| fleet/tests/core/test_chain_runner.py | EXTEND | Tests for new handler actions |
| fleet/tests/mcp/test_tool_trees.py | NEW | Per-tool tree execution tests |

---

## What This Document Does NOT Cover

- **Chain Registry (brain Layer 2)**: event → handler registration, cascading reactions. Separate milestone.
- **Autocomplete chain builder**: context assembly that arranges data for autocomplete. Separate from tool trees.
- **Phase system implementation**: config/phases.yaml enforcement, phase standards injection. fleet_phase_advance tool is built here, but the phase system itself is separate.
- **Contribution brain logic**: brain auto-creating contribution tasks at reasoning stage. Separate from fleet_contribute tool tree.
- **Session management**: context dumping, compaction, rate limit awareness. Different system.
- **Agent file content**: IDENTITY.md, SOUL.md, CLAUDE.md, HEARTBEAT.md per agent. Phase B work.
- **AGENTS.md generation**: driven by synergy-matrix.yaml via generate-agents-md.sh. Separate pipeline.
