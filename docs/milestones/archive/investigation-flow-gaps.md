# Investigation: Fleet Systemic Failures — Why Agents Don't Do Their Jobs

## The Core Problem

The fleet has 10 agents with well-defined roles. None of them are doing their jobs.

- **PM** should evaluate incoming work, create subtasks, assign agents, drive sprints → **does nothing unless manually dispatched**
- **fleet-ops** should monitor board health, enforce quality, process reviews, generate digests → **is offline, nothing restarts it**
- **Cyberpunk-Zero** should proactively scan for CVEs, audit dependencies, flag security concerns → **sits idle**
- **architect** should review designs when architecture work is done → **only works when explicitly dispatched**
- **qa-engineer** should test when PRs are created → **only works when explicitly dispatched**
- **All agents** should remain alive, react to events, communicate, and fulfill their roles → **they are dead processes**

When a human creates a high-level task like "Build DSPD with Plane integration", the PM should:
1. Read the task and architecture docs
2. Create 5-10 subtasks with parent task reference
3. Assign each subtask to the right agent
4. Dispatch them in dependency order
5. Track sprint progress
6. Report to IRC and board memory

**None of this happens.** One task gets manually dispatched, one agent does it, moves to review, and the fleet is dead.

---

## Systemic Issue 1: Agents Are Not Alive

### How Agents Actually Work (Platform Level)

OpenClaw agents have:
- **Persistent sessions** (`agent:<name>:main`) — session history maintained across messages
- **Heartbeat system** — agents poll every 10 minutes via `HEARTBEAT.md` instructions
- **Two message delivery modes**:
  - `deliver=true` → push (agent woken immediately)
  - `deliver=false` → poll (agent gets message on next heartbeat)
- **Wake mechanism** — `chat.send(deliver=true)` wakes agent, must check in within 30 seconds
- **Status tracking** — `last_seen_at`, considered offline after 10 minutes without heartbeat

### What's Broken

| Agent | Should Be | Actually Is | Root Cause |
|-------|-----------|-------------|------------|
| fleet-ops | Alive on heartbeat, monitoring continuously | **OFFLINE** | No restart mechanism, heartbeat failed and nothing recovered it |
| project-manager | Alive, evaluating incoming work, driving sprints | **DORMANT** | No heartbeat configured (HEARTBEAT.md is template-only) |
| devsecops-expert | Alive, scanning proactively | **DORMANT** | No heartbeat configured (HEARTBEAT.md is template-only) |
| accountability-gen | Alive, driving NNRT/products | **OFFLINE** | No heartbeat, no trigger |
| All worker agents | Ready to respond when events occur | **DEAD** | Only wake on explicit `fleet dispatch` via CLI |

### What Must Happen

**Every driver agent needs an active HEARTBEAT.md with real tasks.** Not a template. Real instructions for what to do each cycle.

**Every agent needs to stay alive.** The platform supports heartbeats (10-minute cycles). The fleet must:
1. Configure heartbeats for ALL agents, not just fleet-ops
2. Monitor heartbeat health — if an agent misses a heartbeat, restart it
3. Use `deliver=true` for urgent messages (not `deliver=false` like dispatch currently does)
4. The orchestrator must ensure agents are online and responsive

---

## Systemic Issue 2: No Event-Driven Behavior

### Events That Should Trigger Agent Actions

| Event | Who Should React | What They Should Do |
|-------|-----------------|---------------------|
| Task created in inbox | **PM** | Evaluate complexity, create subtasks, assign agents |
| Task moved to in_progress | **fleet-ops** | Log it, start tracking time |
| Task moved to review | **fleet-ops** | Check quality, process approval |
| Task moved to review | **qa-engineer** | Run tests if PR exists |
| Task moved to review | **architect** | Review if design task |
| Approval pending | **fleet-ops** | Evaluate confidence, auto-approve or escalate |
| Task moved to done | **PM** | Check dependencies, dispatch next tasks |
| Task moved to done | **fleet-ops** | Update sprint metrics, clean up |
| PR created | **devsecops-expert** | Security scan the changes |
| PR created | **qa-engineer** | Run test suite against branch |
| Agent offline > 2 hours | **fleet-ops** | Alert IRC, attempt restart |
| Blocker posted | **PM** | Evaluate, reassign or escalate |
| No human work assigned | **PM** | Drive DSPD product roadmap |
| No human work assigned | **accountability-gen** | Drive NNRT/Factual product |
| No human work assigned | **devsecops-expert** | Proactive security research |

### What Exists Today

**NOTHING.** Zero event handlers. Zero webhooks. Zero triggers.

- MC supports webhooks (`task.*`, `issue.*`, `comment.*` events with HMAC-SHA256 signatures)
- The fleet has zero webhook receivers
- The `EventChainResult` model exists in `fleet/core/models.py` but is never used
- The design-event-chains.md describes the architecture but nothing is built
- Dispatch uses `deliver=false` (polling) instead of `deliver=true` (push)
- The only "events" are polling daemons that observe but never act

### What Must Happen

**Two approaches (both needed):**

**A. Orchestrator daemon (polling, immediate priority)**
- Runs every 30-60 seconds
- Checks board state and acts on what it finds
- Processes approvals, dispatches tasks, wakes agents
- This is the minimum viable method of work

**B. Webhook event system (proper solution, builds on A)**
- Fleet registers webhooks with MC for task state changes
- Webhook receiver endpoint in fleet (HTTP or gateway callback)
- Event handlers route to appropriate agents
- Real-time, not polling

---

## Systemic Issue 3: PM Doesn't Create Subtasks

### What PM Should Do

When a high-level task arrives (e.g., "DSPD: Build with Plane integration"):

```
PM reads task → analyzes scope → creates subtasks:

  S1-1: Research Plane Docker requirements          → devops
  S1-2: Add Plane to docker-compose.plane.yaml      → devops       (depends: S1-1)
  S1-3: Configure workspace + project               → devops       (depends: S1-2)
  S1-4: Generate API key + test API                  → devops       (depends: S1-3)
  S1-5: fleet/infra/plane_client.py                  → sw-engineer  (depends: S1-4)
  S1-6: fleet/cli/plane.py                           → sw-engineer  (depends: S1-5)
  S1-7: Plane ↔ OCMC sync                           → sw-engineer  (depends: S1-6)
  S1-8: PM agent Plane integration                   → sw-engineer  (depends: S1-7)

Each with:
  - Parent task reference (depends_on field)
  - Assigned agent
  - Story points estimate
  - Priority
  - Project tag
```

### What Actually Happens

PM was dispatched to "Break down architecture into sprint-ready tasks." PM posted a sprint plan to **board memory as plain text**. That's it. No actual tasks were created in MC. No depends_on relationships. No agent assignments. The plan sits in board memory and nothing reads it.

### What's Missing

1. **PM doesn't have a mechanism to create tasks** — `fleet_read_context` gives it board state, but there's no MCP tool for creating tasks. The `fleet create` CLI exists but PM can't call CLI commands. There is NO `fleet_task_create` MCP tool.

2. **No parent-child task model** — `depends_on` field exists on Task but:
   - `fleet create` doesn't accept `--depends-on`
   - MC API may not support it in custom fields
   - Nothing reads or enforces dependencies

3. **PM's HEARTBEAT.md is a template** — it says "keep this file empty to skip heartbeat." PM has no autonomous trigger.

4. **PM can't dispatch other agents** — even if PM creates tasks, it can't dispatch them. Dispatch requires gateway WebSocket access that only the CLI has.

---

## Systemic Issue 4: No Approval Processing

### The Approval Chain

```
Agent completes task
    → fleet_task_complete creates approval (confidence=85%, rubric scores)
    → Task moves to "review"
    → ??? WHO APPROVES ???
    → sync daemon tries to move review → done
    → Gets 409 (approval required)
    → Prints "PENDING" and gives up
    → Task stuck forever
```

### What's Missing

| Component | Status | Detail |
|-----------|--------|--------|
| `mc_client.approve_approval()` | **DOES NOT EXIST** | No API method to approve |
| `fleet approve` CLI | **DOES NOT EXIST** | No command for human/daemon approval |
| `fleet_approve` MCP tool | **DOES NOT EXIST** | Agents can't approve each other's work |
| Auto-approve logic | **DOES NOT EXIST** | No threshold-based auto-approval |
| Approval daemon | **DOES NOT EXIST** | Nothing processes pending approvals |
| fleet-ops review logic | **BROKEN** | Agent is offline, HEARTBEAT.md mentions approvals but can't execute |

### MC API for Approvals

MC has the approval CRUD API:
- `POST /api/v1/boards/{id}/approvals` — create (used by fleet_task_complete)
- `GET /api/v1/boards/{id}/approvals` — list (used by list_approvals)
- `PATCH /api/v1/boards/{id}/approvals/{id}` — update status → **FLEET NEVER CALLS THIS**

The PATCH endpoint exists but fleet has no code to call it.

---

## Systemic Issue 5: No Orchestration / Method of Work

### What the Daemons Actually Do

| Daemon | Interval | What It Does | What It Should Also Do |
|--------|----------|-------------|----------------------|
| sync | 60s | Merge PRs for done tasks, close review tasks if PR merged, cleanup worktrees | **Process approvals, transition tasks, dispatch next** |
| monitor | 300s | IRC alerts for stale inbox/review, offline agents | **Restart agents, escalate to PM, trigger action** |
| auth | 120s | Rotate Claude Code OAuth token, restart gateway | Fine as-is |
| **orchestrator** | — | **DOES NOT EXIST** | **The entire lifecycle engine** |

### The Missing Orchestrator

Every 30-60 seconds:

```
1. APPROVE
   - List pending approvals
   - If confidence >= 80% AND rubric passes → auto-approve
   - If confidence < 80% → notify IRC, request human review
   - If pending > 24h → escalate to #alerts

2. TRANSITION
   - List review tasks with approved approvals
   - Move to done
   - Post completion to IRC, board memory
   - Trigger worktree cleanup

3. DISPATCH NEXT
   - For each task that just moved to done:
     - Find tasks with depends_on pointing to this task
     - Check if ALL their dependencies are now done
     - If yes → auto-dispatch to assigned agent
   - For inbox tasks with assigned agents:
     - Auto-dispatch if agent is online and not overloaded

4. WAKE DRIVERS
   - If PM is online but idle → send heartbeat with current board state
   - If fleet-ops is offline → restart via gateway wake
   - If any driver has been idle > 30 min → nudge with work

5. HEALTH
   - Check all agents online/offline
   - Restart offline agents via gateway
   - Alert if restart fails
```

---

## Systemic Issue 6: Missing MCP Tools for Agent Autonomy

### What Agents Can Do (7 tools)

| Tool | Purpose |
|------|---------|
| fleet_read_context | Read task, project, URLs, board memory |
| fleet_task_accept | Accept and start a task |
| fleet_task_progress | Post progress update |
| fleet_commit | Commit with conventional format |
| fleet_task_complete | Push, PR, approval, comment, IRC, done |
| fleet_alert | Post security/quality/architecture alert |
| fleet_pause | Stop and escalate when blocked |

### What Agents CAN'T Do (Missing Tools)

| Missing Tool | Who Needs It | Why |
|-------------|-------------|-----|
| `fleet_task_create` | PM, fleet-ops, all agents | Create follow-up tasks, subtasks, bug reports |
| `fleet_task_assign` | PM | Assign tasks to agents |
| `fleet_task_dispatch` | PM | Dispatch tasks to agents (currently CLI-only) |
| `fleet_approve` | fleet-ops, PM | Approve/reject task completions |
| `fleet_sprint_status` | PM | Read sprint progress, velocity |
| `fleet_agent_status` | fleet-ops | Check which agents are online/offline |
| `fleet_wake_agent` | fleet-ops, PM | Wake a dormant agent |

**The PM literally cannot do its job.** It can read board state but can't create tasks, assign agents, or dispatch work. It can only post to board memory and IRC — which is what it did (posted a sprint plan as text instead of creating actual tasks).

---

## Systemic Issue 7: Gateway Environment Variable Limitation

### The Problem

OpenClaw gateway starts MCP servers **once at agent provisioning**. The `.mcp.json` env vars are read at that time. When `fleet dispatch` updates `.mcp.json` with `FLEET_TASK_ID`, `FLEET_PROJECT`, `FLEET_WORKTREE`, the running MCP server **does not pick up the changes**.

### Evidence

Debug log (`/home/jfortin/openclaw-fleet/.fleet-mcp-debug.log`):
```
[2026-03-28T13:30:01] Fleet MCP server starting
  FLEET_DIR=/home/jfortin/openclaw-fleet
  FLEET_TASK_ID=           ← EMPTY (should be task ID)
  FLEET_AGENT=             ← EMPTY (should be agent name)
```

### Workarounds Applied This Session

1. `fleet_read_context` now resolves project from task custom fields (was already there)
2. `fleet_read_context` now resolves agent_name from task custom fields (**new fix**)
3. `fleet_task_complete` now resolves project_name from filesystem worktree detection (**new fix**)
4. `fleet dispatch` now writes agent_name + worktree to task custom fields (**new fix**)
5. `fleet create` now writes agent_name to task custom fields (**new fix**)

### Remaining Impact

All context must flow through MC API (task custom fields), not env vars. This works but adds latency and requires agents to always call `fleet_read_context` first. The dispatch message already tells agents to do this.

---

## What Must Be Built — Priority Order

### Priority 1: Make Agents Alive (Heartbeats)

**Every agent needs an active HEARTBEAT.md.** Not a template.

| Agent | Heartbeat Tasks |
|-------|----------------|
| **project-manager** | Check inbox for unassigned tasks → evaluate and create subtasks. Check done tasks → dispatch next in sprint. Report sprint status. |
| **fleet-ops** | (Already has HEARTBEAT.md). Board health, digest, quality. **Add: process approvals, restart offline agents.** |
| **devsecops-expert** | Scan for new CVEs in fleet dependencies. Check recent PRs for security concerns. Post findings. |
| **accountability-gen** | Check NNRT progress. Drive product roadmap when idle. |
| Worker agents | Check if they have assigned tasks. If yes, work on them. If no, report idle. |

### Priority 2: Missing MCP Tools

| Tool | File | What |
|------|------|------|
| `fleet_task_create` | `fleet/mcp/tools.py` | Create task with title, description, agent, project, depends_on, priority |
| `fleet_approve` | `fleet/mcp/tools.py` | Approve or reject a pending approval |
| `fleet_agent_status` | `fleet/mcp/tools.py` | List agents with online/offline status |

These unblock PM and fleet-ops from doing their jobs via MCP tools.

### Priority 3: Approval Processing

| Component | File | What |
|-----------|------|------|
| `approve_approval()` | `fleet/infra/mc_client.py` | PATCH approval status to approved/rejected |
| Auto-approve logic | `fleet/core/orchestrator.py` | If confidence >= threshold → approve |
| Approval check in sync | `fleet/cli/sync.py` | Check approval status before transitioning review → done |

### Priority 4: Orchestrator Daemon

| Component | File | What |
|-----------|------|------|
| Orchestrator engine | `fleet/core/orchestrator.py` | approve → transition → dispatch → wake → health |
| Daemon integration | `fleet/cli/daemon.py` | Add to `_run_all()` |
| Sprint plan loader | `fleet/core/sprint.py` | Parse structured sprint plan |

### Priority 5: Task Dependencies

| Component | File | What |
|-----------|------|------|
| `--depends-on` in create | `fleet/cli/create.py` | Accept parent task references |
| Dependency field in MCP | `fleet/mcp/tools.py` | `fleet_task_create` accepts depends_on |
| Dependency check | `fleet/core/orchestrator.py` | Block dispatch until deps are done |
| Sprint plan YAML | `config/sprints/` | Machine-readable task sequences |

### Priority 6: Event-Driven Triggers (Proper Solution)

| Component | File | What |
|-----------|------|------|
| Webhook receiver | `fleet/infra/webhook_server.py` | HTTP endpoint for MC webhooks |
| Event handlers | `fleet/core/events.py` | Route events to agent actions |
| Webhook registration | `fleet/cli/setup.py` | Register fleet webhook URL with MC |
| `deliver=true` dispatch | `fleet/cli/dispatch.py` | Push messages instead of poll |

---

## Dependency Graph

```
P1: Heartbeats (make agents alive)
    │
    ├── PM heartbeat → PM starts evaluating work
    ├── fleet-ops heartbeat → fleet-ops starts monitoring
    └── Agent health monitoring → offline agents get restarted
         │
P2: Missing MCP Tools ←── agents need tools to act
    │
    ├── fleet_task_create → PM can create subtasks
    ├── fleet_approve → fleet-ops can process approvals
    └── fleet_agent_status → fleet-ops can check health
         │
P3: Approval Processing ←── unblocks task transitions
    │
    ├── mc_client.approve_approval()
    ├── Auto-approve in orchestrator
    └── Sync uses approval check
         │
P4: Orchestrator Daemon ←── drives the flow
    │
    ├── approve → transition → dispatch → wake → health
    └── Sprint plan awareness
         │
P5: Task Dependencies ←── enables sprint flow
    │
    ├── depends_on in create/dispatch
    └── Machine-readable sprint plans
         │
P6: Event-Driven (proper, replaces polling) ←── real-time
    │
    ├── MC webhooks → fleet handler
    └── Push delivery (deliver=true) for urgent messages
```

**P1 and P2 are the foundation. Without alive agents that have tools, nothing else matters.**

---

## Bugs Fixed This Session

1. **PR URL bug** (`fleet/mcp/tools.py:212`): Worktree detection didn't set `ctx.project_name` → URLs pointed to wrong repo
2. **Agent identity bug** (`fleet/mcp/tools.py:69`): agent_name not resolved from task custom fields when env var empty
3. **Dispatch custom fields** (`fleet/cli/dispatch.py:82`): Now writes agent_name + worktree to MC task custom fields
4. **Create custom fields** (`fleet/cli/create.py:78`): Now writes agent_name to task custom fields

---

## Current Fleet State (Snapshot 2026-03-28)

### Agents
| Agent | Status | Last Seen | Doing What |
|-------|--------|-----------|------------|
| devsecops-expert | online | recent | Idle |
| project-manager | online | recent | Idle (posted sprint plan, nothing else) |
| fleet-ops | **OFFLINE** | unknown | Nothing (should be monitoring) |
| ux-designer | online | recent | Idle |
| technical-writer | online | recent | Idle |
| software-engineer | **OFFLINE** | unknown | Idle |
| qa-engineer | online | recent | Idle |
| devops | online | recent | Just completed S1-1 |
| architect | online | recent | Idle (completed DSPD architecture) |
| accountability-gen | **OFFLINE** | unknown | Idle |

**7 agents online. 3 offline. 0 doing useful work right now.**

### Tasks
- **6 in review** — nobody reviewing
- **1 in_progress** — stuck (type hints task from old sprint)
- **2 pending approvals** — nobody processing
- **19 done** — completed work
- **0 in inbox** — nothing new queued (because PM didn't create subtasks)

### DSPD Sprint 1
- S1-1 completed (devops, PR #1) — stuck in review
- S1-2 through S1-8 — **never created as actual tasks** (only exist as text in PM's board memory post)