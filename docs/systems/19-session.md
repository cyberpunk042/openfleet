# Session & Context — The Data Pipeline Into Every Agent

> **5 files. 1157 lines. Every 30 seconds, the brain computes FULL context
> for every agent and writes it to files the gateway injects into the
> system prompt. Zero MCP calls for awareness. FULL data, not compressed.**
>
> This system is the DATA BACKBONE. Session telemetry parses REAL Claude
> Code JSON (context %, cost, quota, latency, lines changed). Context
> assembly aggregates from MC, Plane, events, methodology, artifacts.
> HeartbeatBundle pre-computes role-specific awareness. Preembed formats
> as structured markdown. Context writer puts it in agent files. The
> agent wakes up ALREADY KNOWING everything it needs to act.

### PO Requirements (Verbatim)

> "an heartbeat should awake with the relevant informations to avoid
> making the AI make needless tools call, adapted to each agent we
> prefect the needed information to already give some information and
> view of the statuses and progressed and recent events and mentions
> and so on. no need to manually look everything the orchestrator just
> bundle it for you without any AI because its direct logic."

> "Where ever we can take this pattern to improve the work and the flow
> and the logic we will. Its very important that the AI focus on what
> it needs and doesn't waste time with needless tools call that can
> be pre-embedded."

---

## 1. Why It Exists

Without pre-embedded context, every agent heartbeat wastes 3-5 MCP
tool calls just to understand the current situation:

```
WITHOUT pre-embed (wasteful):
  Agent wakes → "What tasks do I have?" → fleet_read_context (tokens)
  → "What's the fleet status?" → fleet_agent_status (tokens)
  → "Any messages for me?" → fleet_heartbeat_context (tokens)
  → "What stage am I in?" → fleet_task_context (tokens)
  → NOW the agent can decide what to do
  Total: 4 tool calls × tokens per call = WASTE

WITH pre-embed (efficient):
  Brain writes context/ files (direct logic, no AI, no tokens)
  → Agent wakes → reads context (in system prompt, FREE)
  → Agent ALREADY KNOWS tasks, stage, messages, fleet status
  → Agent acts immediately
  Total: 0 tool calls for awareness = ZERO WASTE
```

### The Compression Disease

The original pre-embed compressed data to 300 characters per field.
Agents couldn't understand their tasks because critical details were
truncated. AR-01 fixed this: FULL data, not compressed.

---

## 2. How It Works

### 2.1 The Full Pipeline

```
ORCHESTRATOR (Step 0, every 30s cycle)
  │
  │  1. Fetch data from MC API (tasks, agents, board memory, approvals)
  │     → cached per cycle (10 agents × same API = 1 actual call)
  │
  │  2. For EACH agent:
  │     ├── Find assigned tasks (inbox + in_progress)
  │     ├── Find messages (@mentions in board memory)
  │     ├── Find PO directives (tagged "directive")
  │     ├── Get role-specific data via role_providers
  │     ├── Build heartbeat pre-embed (FULL data)
  │     ├── Write: agents/{name}/context/fleet-context.md
  │     └── For in-progress: write task-context.md with stage instructions
  │
  ▼
GATEWAY reads context/ files → includes in system prompt
  │
  ▼
AGENT wakes → context already in system prompt → acts immediately
```

### 2.2 HeartbeatBundle — What Agents ACTUALLY See

Example: what architect sees on heartbeat:

```
HEARTBEAT — architect
Time: 2026-04-01 10:42

📋 YOU HAVE ASSIGNED WORK:
  - [in_progress] Add Fleet Controls to Header (id: abc123)

💬 2 CHAT MESSAGE(S) FOR YOU:
  [project-manager]: Design review needed for task abc123.
  [software-engineer]: @architect need guidance on component pattern

📢 Mentioned by: project-manager, software-engineer

📌 2 event(s) in your domain:
  - [IMPORTANT] New epic created: AICP Stage 2 LocalAI Integration
  - Architecture decision recorded: Use Radix UI for dropdowns

🏃 Sprint: 5/15 done (33%)

Fleet: 7/10 online, 1 blocked, 2 pending approvals

ACTION: Work on your assigned task(s). Use fleet tools for
commits/progress/completion.
```

This is FULL pre-computed context. The agent reads and acts.
No tool calls for awareness. The ACTION directive tells the agent
exactly what to do — or to do nothing ("Respond HEARTBEAT_OK.
Do NOT call any tools.").

### 2.3 HeartbeatBundle Fields

```
HeartbeatBundle:
  ├── Identity: agent_name, fleet_id, timestamp
  ├── Work: assigned_tasks (with verbatim, stage_instruction), has_work
  ├── Stage: stage_instructions (full MUST/MUST NOT/CAN protocol)
  ├── Communication: chat_messages, has_chat, mentioned_by
  ├── Domain: domain_events (filtered by agent capabilities)
  ├── Sprint: sprint_summary
  ├── Plane: plane_sprint, plane_new_items, plane_blocked (PM/fleet-ops only)
  ├── Fleet: agents_online/total, tasks_blocked, pending_approvals
  ├── Control: fleet_work_mode, fleet_cycle_phase, fleet_backend_mode
  ├── Budget: budget_warning
  └── Pre-embed: preembed_text (formatted markdown)
```

Key behaviors:
- Verbatim requirement ALWAYS included, NEVER compacted
- Stage instructions from primary task's current stage
- Plane data only for PM and fleet-ops (not workers)
- Domain events filtered by agent capabilities
- ACTION directive tells agent what to do (or to do nothing)
- "Do NOT call any tools" for idle → drives HEARTBEAT_OK → DROWSY → SLEEPING

### 2.4 Session Telemetry (W8 Adapter)

Parses REAL Claude Code JSON and distributes to fleet systems:

```
SessionSnapshot = ingest(json_data)
  ↓
to_labor_fields()    → LaborStamp: real cost, duration, lines, cache
to_claude_health()   → ClaudeHealth: real quota (5h+7d), latency, context size
to_storm_indicators() → StormMonitor: context_pressure, quota_pressure, cache_miss
to_cost_delta()      → CostTicker: incremental real cost
```

Properties: context_label ("1M"/"200K"), context_pressure ("critical"/"high"/"moderate"/"low"), cache_hit_rate (0.0-1.0).

### 2.5 Context Assembly

Two aggregation functions, both cached per cycle:

**assemble_task_context():** task core + custom fields + methodology (stage, instructions, readiness, required/next stages) + artifact (from Plane HTML via transpose, completeness with missing fields + suggested readiness) + comments (last 20) + activity (last 15 events) + related tasks (children, parent, dependencies) + Plane data.

**assemble_heartbeat_context():** role-specific data (via providers) + fleet state + messages + directives + events. Each role gets different data.

---

## 3. File Map

```
fleet/core/
├── session_telemetry.py   Parse Claude Code JSON, distribute to systems  (230 lines)
├── context_assembly.py    Aggregate from MC/Plane/events/methodology     (331 lines)
├── heartbeat_context.py   HeartbeatBundle: pre-computed agent awareness   (340 lines)
├── preembed.py            Format as structured markdown (FULL)            (170 lines)
└── context_writer.py      Write context/ files to agent directories       (86 lines)
```

Total: **1157 lines** across 5 modules.

---

## 4. Per-File Key Functions

### session_telemetry.py (230 lines)
`ingest(data)` → SessionSnapshot. Distribution: `to_labor_fields()`, `to_claude_health()`, `to_storm_indicators()`, `to_cost_delta()`.

### context_assembly.py (331 lines)
`assemble_task_context()` — full task bundle from MC+Plane+events+methodology+transpose. `assemble_heartbeat_context()` — role-specific via providers. Per-cycle cache.

### heartbeat_context.py (340 lines)
`HeartbeatBundle` — 20+ fields, `format_message()` renders emoji-prefixed text with ACTION. `build_heartbeat_context()` — build from direct data (no AI, no API calls).

### preembed.py (170 lines)
`format_task_full()` — FULL task (NOT truncated). `build_heartbeat_preembed()` — directives + messages + tasks + role_data + events. `build_task_preembed()` — task + stage instructions.

### context_writer.py (86 lines)
`write_heartbeat_context()` → fleet-context.md. `write_task_context()` → task-context.md. `clear_task_context()` → remove on completion/prune.

---

## 5. Consumers

| System | What It Consumes | How |
|--------|-----------------|-----|
| **Orchestrator** | preembed + context_writer | Step 0: refresh ALL agent contexts every 30s |
| **MCP Tools** | context_assembly | fleet_task_context(), fleet_heartbeat_context() |
| **Gateway** | context/ files | Reads and injects into agent system prompt |
| **Labor Stamps** | session_telemetry | to_labor_fields() → real cost/duration |
| **Backend Health** | session_telemetry | to_claude_health() → real quota/latency |
| **Storm Monitor** | session_telemetry | to_storm_indicators() → context_pressure |
| **Budget** | session_telemetry | to_cost_delta() → real cost increments |

---

## 6. Design Decisions

**Why pre-embed, not on-demand MCP calls?** Every MCP call costs tokens. Pre-embed is FREE. 10 agents × 4 awareness calls × tokens/call = significant waste eliminated.

**Why FULL data, not compressed?** 300-char compression disease made agents non-functional. FULL means: verbatim requirement, stage instructions, finding details. If it matters, show it completely.

**Why HeartbeatBundle with ACTION directive?** Without clear direction, agents make unnecessary tool calls "just to check." ACTION tells them: work, respond, review, or "Do NOT call any tools." The idle instruction drives HEARTBEAT_OK → content-aware sleep.

**Why domain events filtered by capabilities?** An architect sees "architecture" events. A QA engineer sees "test" events. Capability-based filtering (from AGENT_CAPABILITIES) ensures relevance without noise.

**Why session telemetry as adapter?** ONE module parses Claude Code JSON. MANY systems consume typed output. Schema changes → only adapter changes. Systems don't know about JSON format.

**Why per-cycle cache?** 10 agents × same MC API call = 1 actual call. Cache cleared at cycle start. Prevents 10x API overhead.

---

## 7. What's Needed

- **Session telemetry wired to runtime** — adapter built (W8, 30 tests), distribution helpers exist, but orchestrator doesn't call them. Systems still use estimates.
- **Full role-specific pre-embed (AR-01)** — PM needs Plane sprint data. Workers need artifact completeness + suggested readiness.
- **Contribution data in worker context** — architect's design_input should appear in engineer's task context. Requires fleet_contribute tool.
- **HeartbeatBundle → orchestrator unification** — heartbeat_context.py produces richer bundles than preembed.py. Should be unified.
- **Context size tracking** — monitor how much context each agent uses per heartbeat.

## 8. Test Coverage: **65+ tests** (30 telemetry + 15 assembly + 10 preembed + 10 heartbeat)
