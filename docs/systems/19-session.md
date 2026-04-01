# Session & Context — Real Data Into Agent Context

> **5 files. 1157 lines. Builds, assembles, and injects context for every agent every cycle.**
>
> Session telemetry parses REAL Claude Code JSON (context %, cost,
> quota, latency, lines changed). Context assembly aggregates data
> from MC, Plane, events, methodology, artifacts into one bundle.
> Preembed formats it as structured markdown. Context writer puts it
> in agent files. The brain does this every 30 seconds so agents
> always have FULL, CURRENT data — not compressed, not stale.

---

## 1. Why It Exists

Agents need context to make decisions. Without pre-embedded context,
agents would need to make 5-10 MCP tool calls just to understand
their situation — burning tokens on data the orchestrator already has.

Pre-embedding means: the orchestrator computes the context ONCE,
writes it to files, and the gateway includes it in the system prompt.
The agent reads and acts. Zero MCP calls for awareness.

### The Compression Disease

The original pre-embed compressed data to 300 characters per field.
Agents couldn't understand their tasks because critical details were
truncated. The agent-rework AR-01 milestone fixed this: FULL data,
not compressed.

---

## 2. How It Works

### 2.1 Session Telemetry (W8 Adapter)

Claude Code exposes JSON session data to IDE/statusline. The session
telemetry adapter parses this and distributes real values to fleet
systems that currently use estimates:

```
Claude Code Session JSON
  ↓
SessionSnapshot = ingest(json_data)
  ├── context_window_size: 1M or 200K
  ├── context_used_pct: 42%
  ├── total_cost_usd: $0.15
  ├── total_duration_ms: 180000
  ├── total_lines_added/removed: 256/31
  ├── cache_read_tokens: 2000
  ├── five_hour_used_pct: 23.5%
  └── seven_day_used_pct: 41.2%
  ↓
Distribution helpers:
  ├── to_labor_fields() → LaborStamp gets real cost/duration/lines
  ├── to_claude_health() → ClaudeHealth gets real quota/latency
  ├── to_storm_indicators() → context_pressure, quota_pressure
  └── to_cost_delta() → CostTicker gets real cost increments
```

### 2.2 Context Assembly

Single source of truth for building context bundles:

```
assemble_task_context(task, mc, board_id, plane, event_store)
  ↓
Returns dict with:
  ├── task: id, title, status, priority, description
  ├── custom_fields: readiness, stage, verbatim, agent, SP, type
  ├── methodology: stage, instructions (MUST/MUST NOT/CAN),
  │                readiness, required_stages, next_stage
  ├── artifact: type, data (from Plane HTML via transpose),
  │             completeness (required_pct, missing, suggested_readiness)
  ├── comments: last 20, author + content + time
  ├── activity: last 15 events for this task
  ├── related_tasks: children, parent, dependencies
  └── plane: issue_id, project_id, workspace
```

```
assemble_heartbeat_context(agent, role, tasks, agents, mc, ...)
  ↓
Returns dict with:
  ├── role-specific data (via role_providers):
  │   ├── fleet-ops: pending_approvals, review_queue, offline_agents
  │   ├── PM: unassigned_tasks, blocked, sprint progress
  │   ├── architect: design_tasks, high_complexity
  │   ├── devsecops: security_tasks, PRs needing review
  │   └── workers: my_tasks_count, in_review
  ├── fleet state: mode, phase, backend, agents online
  ├── messages: @mentions for this agent
  ├── directives: PO commands
  └── events: since last heartbeat
```

Per-cycle cache prevents redundant MC API calls.

### 2.3 Preembed — Formatting

Formats assembled data as structured markdown agents read naturally:

```markdown
# HEARTBEAT CONTEXT

Agent: architect
Role: architect
Fleet: 7/10 online | Mode: full-autonomous | Phase: execution

## PO DIRECTIVES
- Focus on AICP Stage 1 (from human)

## MESSAGES
- From project-manager: Design review needed for task abc123

## ASSIGNED TASKS (2)

### Add Fleet Controls to Header
- ID: abc123
- Status: in_progress
- Stage: analysis
- Readiness: 30%
- Verbatim Requirement: "Add fleet controls to the OCMC header bar..."

## ROLE DATA
### design_tasks (3)
  - {'id': 'ghi789', 'title': 'Implement budget mode...', 'stage': 'reasoning'}
```

### 2.4 Context Writer

Writes to `agents/{name}/context/`:
- `fleet-context.md` — heartbeat data (every cycle)
- `task-context.md` — current task data (at dispatch + every cycle for in-progress)

Gateway reads these files when building the agent's system prompt.

---

## 3. File Map

```
fleet/core/
├── session_telemetry.py  Parse Claude Code JSON, distribute to systems (230 lines)
├── context_assembly.py   Aggregate task + heartbeat bundles           (331 lines)
├── context_writer.py     Write context/ files to agent directories    (86 lines)
├── preembed.py           Format as structured markdown                (170 lines)
└── heartbeat_context.py  Heartbeat-specific context building          (340 lines)
```

Total: **1157 lines** across 5 modules.

---

## 4. Key Functions

| Module | Function | What It Does |
|--------|----------|-------------|
| session_telemetry | `ingest(data)` | Parse JSON → SessionSnapshot |
| session_telemetry | `to_labor_fields(snap)` | Real cost/duration for LaborStamp |
| session_telemetry | `to_claude_health(snap)` | Real quota/latency for ClaudeHealth |
| session_telemetry | `to_storm_indicators(snap)` | context_pressure, quota_pressure indicators |
| session_telemetry | `to_cost_delta(snap, prev)` | Incremental cost for CostTicker |
| context_assembly | `assemble_task_context()` | Full task bundle: methodology + artifact + comments + related |
| context_assembly | `assemble_heartbeat_context()` | Role-specific heartbeat bundle via providers |
| preembed | `format_task_full(task)` | FULL task detail (NOT truncated) |
| preembed | `build_heartbeat_preembed()` | Directives + messages + tasks + role data + events |
| preembed | `build_task_preembed()` | Task + stage instructions |
| context_writer | `write_heartbeat_context(agent, content)` | Write fleet-context.md |
| context_writer | `write_task_context(agent, content)` | Write task-context.md |
| context_writer | `clear_task_context(agent)` | Remove task-context.md (task done / pruned) |

---

## 5. Consumers

| Layer | Module | How It Uses It |
|-------|--------|---------------|
| **Orchestrator** | Step 0 | `_refresh_agent_contexts()` calls preembed + context_writer every cycle |
| **Orchestrator** | Step 0 | Uses role_providers for per-role data |
| **MCP Tools** | `fleet_task_context()` | Uses `assemble_task_context()` |
| **MCP Tools** | `fleet_heartbeat_context()` | Uses `assemble_heartbeat_context()` |
| **Gateway** | — | Reads context/ files for system prompt |

---

## 6. Design Decisions

**Why pre-embed, not on-demand MCP calls?** Every MCP call costs tokens. Pre-embed is FREE (file read in system prompt). Agents don't waste 5 calls just to understand their situation.

**Why FULL data, not compressed?** The 300-char compression disease made agents non-functional. FULL means: full verbatim requirement, full task description, full finding details. If it's important enough to show, show it completely.

**Why per-cycle cache?** Context assembly calls MC API, Plane API, event store. Caching per cycle means: 10 agents × same MC call = 1 actual call. Cache cleared at start of each cycle.

**Why session telemetry as adapter, not direct integration?** The adapter parses ONE JSON format and distributes to MANY systems. If the JSON schema changes, only the adapter changes. Systems receive typed data through helper functions.

---

## 7. What's Needed

- Session telemetry wired to runtime (adapter built, not connected to orchestrator)
- Full role-specific pre-embed per AR-01 spec (PM needs Plane sprint data, workers need artifact completeness)
- Contribution data included in worker task context (requires fleet_contribute tool)
- Context size tracking (monitor how much context each agent uses)

## 8. Test Coverage: **65+ tests** (30 session telemetry + 15 context assembly + 10 preembed + 10 heartbeat)
