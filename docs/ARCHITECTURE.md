# Fleet Architecture

> **94 core modules. 20 systems. 10 agents. 25 MCP tools. ~255 milestones.**
>
> This document shows how everything connects. Each system has its own
> detailed doc in `docs/systems/`. This doc shows the big picture:
> what talks to what, how data flows, and where the gaps are.

---

## 1. System Map

```
┌──────────────────────────────────────────────────────────────────┐
│                         PO (Product Owner)                        │
│                                                                    │
│  Plane issues │ OCMC directives │ Phase gates │ Budget overrides  │
└────────┬──────┴────────┬────────┴──────┬──────┴────────┬─────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Brain)                            │
│              fleet/cli/orchestrator.py — 30s cycle                │
│                                                                    │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ │
│  │ Storm   │ │ Budget  │ │ Fleet    │ │ Effort  │ │ Change   │ │
│  │ Monitor │ │ Monitor │ │ Mode     │ │ Profile │ │ Detector │ │
│  └────┬────┘ └────┬────┘ └─────┬────┘ └────┬────┘ └─────┬────┘ │
│       │           │            │            │            │       │
│  9 Steps: Context → Security → Doctor → Approvals →      │       │
│           Wake → Dispatch → Directives → Parents → Health │       │
└────────┬─────────────────────────────────────────────────────────┘
         │ writes context/ files          │ inject_content()
         ▼                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    GATEWAY (OpenClaw)                              │
│              ws://localhost:18789 — WebSocket RPC                  │
│                                                                    │
│  Reads: agents/{name}/ files → builds system prompt               │
│  Runs: claude --permission-mode bypassPermissions                 │
│  MCP: python -m fleet.mcp.server (25 tools, stdio)                │
│  Sessions: prune, compact, inject, create fresh                   │
└────────┬─────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    10 AGENTS                                      │
│                                                                    │
│  Drivers:  PM │ fleet-ops │ devsecops │ accountability             │
│  Workers:  architect │ engineer │ devops │ QA │ writer │ UX       │
│                                                                    │
│  Each agent: CLAUDE.md + HEARTBEAT.md + context/ + MCP tools      │
│  Lifecycle: ACTIVE → IDLE → DROWSY → SLEEPING → OFFLINE          │
└────────┬─────────────────────────────────────────────────────────┘
         │ MCP tool calls
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    25 MCP TOOLS                                   │
│                                                                    │
│  Task:    read_context, accept, progress, commit, complete, create │
│  Comms:   chat, alert, pause, escalate, notify_human               │
│  Review:  approve                                                  │
│  Plane:   status, sprint, sync, create/comment/update/modules      │
│  Artifact: read, update, create                                    │
│  Status:  agent_status, task_context, heartbeat_context            │
│                                                                    │
│  Stage gate: fleet_commit + fleet_task_complete BLOCKED outside work│
└────────┬─────────────────────────────────────────────────────────┘
         │ events propagate
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    6 SURFACES                                     │
│                                                                    │
│  INTERNAL: MC (tasks, memory, approvals)                           │
│  PUBLIC:   GitHub (branches, PRs, commits)                         │
│  CHANNEL:  IRC (#fleet, #alerts, #reviews)                        │
│  NOTIFY:   ntfy (PO mobile)                                       │
│  PLANE:    Plane (issues, labels, comments)                       │
│  META:     Metrics, quality checks                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. The 20 Systems — Interconnection Matrix

### 2.1 Who Calls Whom

```
                    Meth  Immn  Teach Event Ctrl  Life  Orch  MCP   Std   Trans Storm Budg  Labor Route Chall Model Plane Notif Sess  Infra
Methodology    (1)   -     →     .     →     .     .     .     →     ←     .     .     .     .     .     .     .     .     .     →     .
Immune         (2)   ←     -     →     →     .     →     .     .     ←     .     .     .     .     .     .     .     .     .     .     .
Teaching       (3)   .     ←     -     →     .     .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
Event Bus      (4)   ←     ←     ←     -     .     .     .     ←     .     .     .     .     .     .     .     .     ←     ←     .     .
Control        (5)   .     .     .     →     -     .     .     .     .     .     ←     ←     .     .     .     .     .     .     .     .
Lifecycle      (6)   .     ←     .     .     .     -     .     .     .     .     ←     ←     .     .     .     .     .     .     .     .
Orchestrator   (7)   .     ←     ←     ←     ←     ←     -     .     .     .     ←     ←     .     .     .     .     .     .     ←     ←
MCP Tools      (8)   ←     .     .     →     .     .     .     -     ←     ←     .     .     ←     .     .     .     →     .     .     ←
Standards      (9)   .     →     →     .     .     .     .     →     -     ←     .     .     .     .     .     .     .     .     .     .
Transpose     (10)   .     .     .     .     .     .     .     ←     ←     -     .     .     .     .     .     .     ←     .     .     .
Storm         (11)   .     .     .     →     →     →     →     .     .     .     -     →     .     →     .     .     .     →     ←     .
Budget        (12)   .     .     .     .     .     .     →     .     .     .     ←     -     ←     →     →     .     .     .     ←     .
Labor         (13)   .     .     .     →     .     .     .     ←     .     .     .     ←     -     ←     ←     .     .     .     ←     .
Router        (14)   .     .     .     .     .     .     .     .     .     .     ←     ←     →     -     .     .     .     .     ←     .
Challenge     (15)   .     .     .     .     .     .     .     .     .     .     .     ←     ←     .     -     .     .     .     .     .
Model         (16)   .     .     .     .     .     .     .     .     .     .     .     ←     →     →     .     -     .     .     .     .
Plane         (17)   ←     .     .     →     .     .     →     ←     .     ←     .     .     .     .     .     .     -     .     .     ←
Notifications (18)   .     .     .     ←     .     .     ←     ←     .     .     ←     .     .     .     .     .     .     -     .     .
Session       (19)   →     .     .     .     .     .     ←     .     .     .     →     →     →     →     .     .     .     .     -     .
Infrastructure(20)   .     .     .     .     .     .     ←     ←     .     .     .     .     .     .     .     .     ←     .     .     -

→ = this system calls/imports from the column system
← = this system is called/imported by the column system
```

### 2.2 Critical Paths

**Task dispatch path:**
```
Orchestrator → Control (mode check) → Budget (quota check) →
Storm (severity check) → Router (backend selection) →
MCP Tools (dispatch) → Agent (work) → Events (propagate)
```

**Review path:**
```
Agent (fleet_task_complete) → MCP Tools → Events (6 surfaces) →
fleet-ops (heartbeat wake) → MCP Tools (fleet_approve) →
Standards (compliance check) → Events (approval result)
```

**Disease detection path:**
```
Agent (tool call) → MCP Tools (stage check) → Events (violation) →
Doctor (detect) → Teaching (lesson) → Gateway (inject) → Agent (learn)
```

**Cost control path:**
```
Budget Monitor (OAuth API) → Orchestrator (quota check) →
Budget Modes (constraint) → Router (backend selection) →
Storm (severity → budget forcing) → Lifecycle (agent sleeping)
```

---

## 3. Data Flow

### 3.1 Agent Context (What Agents See)

```
Orchestrator writes every 30s:
  ↓
agents/{name}/context/fleet-context.md
  ├── Fleet state (mode, phase, backend, agents online)
  ├── PO directives (from board memory)
  ├── Messages (@mentions for this agent)
  ├── Assigned tasks (FULL detail)
  ├── Role-specific data (via role_providers)
  └── Events since last heartbeat

agents/{name}/context/task-context.md
  ├── Task details (FULL — not compressed)
  ├── Stage instructions (MUST/MUST NOT/CAN)
  ├── Artifact state (completeness, suggested readiness)
  └── Related tasks (children, parent, dependencies)
```

### 3.2 Event Propagation (What Surfaces See)

```
Agent calls fleet_task_complete(summary)
  ↓
MCP Tool: fleet_task_complete
  ├── git push branch
  ├── create PR (title, body, labels)
  ├── MC: update task status → review
  ├── MC: create approval for fleet-ops
  ├── MC: post completion comment (with labor stamp)
  ├── IRC: "[agent] PR READY: {summary}"
  ├── IRC #reviews: "[agent] Review: {pr_url}"
  ├── ntfy: "Task completed: {summary}"
  ├── Plane: update issue state
  ├── Plane: post comment
  └── Event: fleet.task.completed (stored in JSONL)
```

---

## 4. Module Inventory

94 core modules organized by system. See `docs/systems/README.md` for the full index.

| System | Modules | Lines | Tests | Status |
|--------|---------|-------|-------|--------|
| Methodology | 3 | 877 | 55+ | ✅ Verified |
| Immune System | 3 | 746 | 50+ | ✅ Verified |
| Teaching | 1 | 485 | 25+ | ✅ Verified |
| Event Bus | 4 | 1248 | 60+ | ✅ Verified |
| Control Surface | 3 | 305 | 35+ | 🔨 Code exists |
| Agent Lifecycle | 2 | 423 | 35+ | 🔨 Code exists |
| Orchestrator | 8 | 2595 | 75+ | 🔨 Partial live |
| MCP Tools | 3 | 2517 | 40+ | 🔨 Code exists |
| Standards | 4 | 739 | 50+ | 🔨 Code exists |
| Transpose | 2 | 573 | 35+ | 🔨 Code exists |
| Storm | 4 | 1440 | 90 | 🔨 Code exists |
| Budget | 4 | 1151 | 103 | 🔨 Code exists |
| Labor | 3 | 901 | 59+ | 🔨 Code exists |
| Router | 5 | 1611 | 141 | 🔨 Code exists |
| Challenge | 8 | 2831 | 235 | 🔨 Code exists |
| Models | 6+3 | 1767 | 130 | 🔨 Code exists |
| Plane | 4 | 1208 | 40+ | 🔨 Code exists |
| Notifications | 3 | 536 | 30+ | 🔨 Code exists |
| Session/Context | 5 | 1157 | 65+ | 🔨 Code exists |
| Infrastructure | 8 | 1908 | 30+ | 🔨 Code exists |
| **Total** | **94** | **~24,000** | **~1800+** | |

---

## 5. Configuration

```
config/
├── fleet.yaml              Fleet-wide: gateway, MC, orchestrator, effort
├── phases.yaml             PO-defined delivery phase progressions
├── agent-identities.yaml   Agent display names
├── skill-assignments.yaml  Skill → agent mapping
├── skill-packs.yaml        External skill sources
├── projects.yaml           Project definitions
├── url-templates.yaml      URL resolution templates
└── fleet-identity.yaml     Fleet ID, machine, UUID
```

---

## 6. Agent File Structure

```
agents/{name}/
├── agent.yaml           Gateway config (COMMITTED)
├── CLAUDE.md            Role-specific rules (COMMITTED, max 4000 chars)
├── HEARTBEAT.md         Action protocol (COMMITTED)
├── context/
│   ├── fleet-context.md Heartbeat data (GENERATED by brain every cycle)
│   └── task-context.md  Task data (GENERATED at dispatch)
├── IDENTITY.md          Who the agent is (GENERATED for workers, COMMITTED for persistent)
├── SOUL.md              Values, boundaries (GENERATED for workers, COMMITTED for persistent)
├── TOOLS.md             Chain-aware tool reference (GENERATED)
├── AGENTS.md            Knowledge of colleagues (GENERATED for workers, COMMITTED for persistent)
└── USER.md              Who agent serves (GENERATED for workers, COMMITTED for persistent)
```

Injection order: IDENTITY → SOUL → CLAUDE → TOOLS → AGENTS → context/ → HEARTBEAT

---

## 7. Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| OpenClaw Gateway | 9400 (HTTP), 18789 (WS) | Agent sessions, MCP |
| Mission Control | 8000 | Tasks, agents, board memory, approvals |
| LocalAI | 8090 | LLM inference, embeddings, reranking |
| Plane | — | Project management, issues, sprints |
| The Lounge (IRC) | 9000 | Agent communication, human visibility |
| ntfy | external | Push notifications to PO |

---

## 8. What's Not Connected

| From | To | Gap |
|------|-----|-----|
| AICP RAG (rag.py, kb.py) | Fleet agents | RAG not accessible from fleet |
| AICP Router (router.py) | Fleet router | No bridge (router_unification.py is schema only) |
| Session Telemetry (W8) | Runtime systems | Adapter built, not wired to orchestrator |
| Fleet Routing | Real dispatch | Router exists, orchestrator doesn't use it fully |
| Contribution flow | Agents | fleet_contribute tool not built |
| Brain evaluation | DROWSY agents | Data structures exist, logic not in orchestrator |

---

## 9. Honest Status

**61 milestones live verified.** 56 with code but not live tested. ~133 designed only. 5 blocked by operational readiness.

**Zero end-to-end live tests** with real agents doing real work through the full lifecycle (dispatch → stages → contributions → work → challenge → review → done).

The code exists. The tests pass. The systems connect. But nobody has pressed "go" and watched 10 agents work together on real tasks through real methodology stages with real challenges and real approvals.

That is the next milestone.
