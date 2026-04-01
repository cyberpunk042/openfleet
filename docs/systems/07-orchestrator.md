# System 7: Orchestrator (The Brain)

**Source:** `fleet/cli/orchestrator.py` (1378 lines), `fleet/core/driver.py`, `fleet/core/smart_chains.py`, `fleet/core/context_assembly.py`
**Status:** 🔨 Runs, partially live tested. Core loop works. Some steps incomplete.
**Design docs:** `fleet-elevation/04`, `agent-rework/03`

---

## Purpose

The autonomous brain. Runs every 30 seconds. Reads fleet state, detects what needs attention, refreshes agent context, wakes drivers, dispatches tasks, processes directives, evaluates parents, checks health. Guards: storm monitor, budget monitor, fleet mode, effort profile.

## 9-Step Cycle (orchestrator.py:77-251)

```
Pre-checks: Storm (CRITICAL=stop, STORM=0, WARNING=1) + Gateway duplication + Effort profile + Fleet mode

Step 0: _refresh_agent_contexts()     — write context/ files for ALL agents
Step 1: _security_scan()              — behavioral security check
Step 2: _run_doctor()                 — immune system detection + response
Step 3: _ensure_review_approvals()    — create approval objects
Step 4: _wake_drivers()               — inject wake into PM/fleet-ops sessions
Step 5: _dispatch_ready_tasks()       — dispatch unblocked inbox to agents
Step 6: _process_directives()         — parse PO directives
Step 7: _evaluate_parents()           — children done → parent to review
Step 8: _health_check()               — stuck tasks, offline agents
```

### Step 0: Context Refresh (orchestrator.py:257-366)

Every cycle, writes `agents/{name}/context/fleet-context.md` for ALL agents:
- Assigned tasks (full detail)
- Messages (@mentions from board memory)
- PO directives
- Role-specific data (via role_providers.py)
- Fleet state (mode, phase, backend, agents online)

Also writes `task-context.md` for agents with in-progress tasks.

### Step 2: Doctor (orchestrator.py:369-530)

Persistent health profiles across cycles. Runs detection functions. Produces DoctorReport. Orchestrator:
- Skips flagged agents during dispatch
- Blocks flagged tasks
- Injects teaching lessons via gateway

### Step 4: Wake Drivers (orchestrator.py:761-830)

PM wakes when: unassigned inbox tasks (120s cooldown)
Fleet-ops wakes when: tasks in review (120s cooldown)
Waking = `inject_content(session_key, wake_message)` via gateway WebSocket RPC.

### Step 5: Dispatch (orchestrator.py)

Dispatches unblocked inbox tasks to assigned agents. Respects:
- Doctor report (skip flagged agents/tasks)
- Fleet control state (cycle phase filters active agents)
- Max dispatch per cycle (from effort profile)

## Key Concepts

### Smart Chains (smart_chains.py)

Pre-compute context so agents don't waste MCP calls:
- `DispatchContext` — task + project + worktree pre-computed
- `CompletionChain` — PR + approval + IRC + ntfy in one pass

### Context Assembly (context_assembly.py)

Single source of truth for context bundles:
- `assemble_task_context()` — task + custom fields + methodology + artifact + comments + activity + related + Plane
- `assemble_heartbeat_context()` — role-specific via role_providers

Per-cycle cache prevents redundant MC API calls.

### Role Providers (role_providers.py)

Role-specific data per agent:
- `fleet_ops_provider` → pending_approvals, review_queue, offline_agents
- `project_manager_provider` → unassigned_tasks, blocked_tasks, sprint progress
- `architect_provider` → tasks needing design review

## What Orchestrator Does NOT Do

- Does NOT create Claude Code sessions (gateway does)
- Does NOT manage heartbeat scheduling (gateway cron does)
- Does NOT read agent output (gateway handles)
- Does NOT modify agent files other than context/ (IaC principle)

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Every system** | Orchestrator coordinates all systems | Central hub |
| **Storm** | Storm level gates dispatch | Storm → Orchestrator |
| **Budget** | Budget mode read from board | Budget → Orchestrator |
| **Fleet Mode** | Work mode, cycle phase, backend mode | Control → Orchestrator |
| **Effort Profile** | Dispatch rate, heartbeat frequency | Profile → Orchestrator |
| **Doctor** | Doctor report gates dispatch + triggers teaching | Doctor → Orchestrator |
| **Gateway** | Wake drivers, inject lessons via WebSocket RPC | Orchestrator → Gateway |
| **Context Writer** | Writes agent context/ files | Orchestrator → Agents |
| **Preembed** | Builds heartbeat + task pre-embed data | Preembed → Writer |
| **Role Providers** | Per-role data for heartbeat context | Providers → Preembed |
| **Change Detector** | Identifies what changed since last cycle | Detector → Orchestrator |
| **Directives** | Parses PO directives from board memory | Directives → Orchestrator |
| **Events** | Emits mode change, dispatch, health events | Orchestrator → Events |

## What's Needed

- [ ] Brain-evaluated heartbeats (deterministic eval for DROWSY/SLEEPING)
- [ ] Contribution subtask creation (when task enters REASONING)
- [ ] Full role-specific pre-embed (PM needs Plane, workers need artifacts)
- [ ] Strategic Claude call configuration (model/effort/session per situation)
