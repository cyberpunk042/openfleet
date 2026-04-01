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

## 4. Per-File Documentation

### 4.1 `session_telemetry.py` — W8 Adapter (230 lines)

Parses Claude Code session JSON into typed `SessionSnapshot` and
distributes real values to fleet systems via helper functions.

| Class/Function | Lines | What It Does |
|---------------|-------|-------------|
| `SessionSnapshot` | 21-97 | 18 typed fields: model_id, context_window_size, context_used_pct, total_cost_usd, total_duration_ms, total_lines_added/removed, cache_read_tokens, five_hour_used_pct, seven_day_used_pct, etc. Properties: context_label, context_pressure, cache_hit_rate, duration_seconds, api_latency_ms. |
| `ingest(data)` | 104-157 | Parse JSON dict → SessionSnapshot. Handles missing/null fields gracefully (all default to zero/empty). Nested extraction: model.id, context_window.used_percentage, rate_limits.five_hour.used_percentage. |
| `to_labor_fields(snap)` | 163-182 | Returns dict matching LaborStamp field names: model, model_version, duration_seconds, estimated_tokens, estimated_cost_usd, lines_added, lines_removed, cache_read_tokens, session_type. |
| `to_claude_health(snap)` | 185-207 | Returns dict matching ClaudeHealth fields: latency_ms, model_available, quota_used_pct (from 5h window), weekly_quota_used_pct, context_window_size. |
| `to_storm_indicators(snap)` | 210-244 | Returns list[(name, value)]: context_pressure (if ≥70%), quota_pressure_5h (if ≥80%), quota_pressure_7d (if ≥80%), cache_miss (if hit_rate <10% and >10K tokens). |
| `to_cost_delta(snap, previous)` | 247-253 | Returns incremental cost: max(snap.total_cost_usd - previous, 0.0). |

### 4.2 `context_assembly.py` — Aggregator (331 lines)

Single source of truth for context bundles. Cached per orchestrator cycle.

| Function | Lines | What It Does |
|----------|-------|-------------|
| `clear_context_cache(cycle_id)` | 28-32 | Clear per-cycle cache. Called at start of each orchestrator cycle. |
| `assemble_task_context(task, mc, board_id, plane, event_store)` | 35-223 | Aggregates 7 sections: (1) task core (id, title, status, priority), (2) custom_fields (readiness, stage, verbatim, agent, SP), (3) methodology (stage instructions via stage_context, required/next stages), (4) artifact (from Plane HTML via transpose — type, data, completeness with missing fields + suggested readiness), (5) comments (last 20 via MC API), (6) activity (last 15 events from store), (7) related_tasks (children, parent, dependencies with status). Cached by task_id per cycle. |
| `assemble_heartbeat_context(agent, role, tasks, agents, mc, board_id, event_store, role_providers, fleet_state)` | 226-331 | Role-specific via providers. Assigns tasks filtered by agent name. Messages filtered by @mention tags. Events filtered by agent relevance. Fleet state from board config. |

### 4.3 `heartbeat_context.py` — HeartbeatBundle (340 lines)

Pre-computes FULL agent awareness WITHOUT AI — direct Python logic only.

| Class | Lines | Purpose |
|-------|-------|---------|
| `HeartbeatBundle` | 37-165 | 20+ fields covering work, communication, domain, sprint, Plane, fleet health, budget, control state. `format_message()` renders emoji-prefixed sections with ACTION directive at end. |

| Function | Lines | What It Does |
|----------|-------|-------------|
| `build_heartbeat_context(agent_name, tasks, agents, board_memory, approvals, fleet_id, sprint_id, plane_data, event_feed, fleet_state)` | 168-340 | Builds HeartbeatBundle from DIRECT DATA passed by caller. No API calls, no AI. Filters: tasks by agent_name, messages by @mention tags (including lead/all aliases), domain events by AGENT_CAPABILITIES keyword match. Sets stage_instructions from primary task's stage. Plane data only for PM/fleet-ops. Budget warning from fleet state. |

Key behaviors in `build_heartbeat_context()`:
- Verbatim requirement: `task_info["requirement_verbatim"]` — ALWAYS present, NEVER compacted (line 206)
- Stage instruction: `get_stage_instructions(stage)` injected for primary task (line 220)
- Domain filtering: `any(cap in content_lower for cap in capabilities[:5])` — top 5 capabilities matched against board memory content (line 249)
- Urgent/important events from event_feed promoted to domain_events (line 289)
- Mentioned agents from events tracked in `mentioned_by` (line 293)

### 4.4 `preembed.py` — Markdown Formatting (170 lines)

Formats assembled data as structured markdown agents read naturally.

| Function | Lines | What It Does |
|----------|-------|-------------|
| `format_events(events, limit)` | 19-35 | Format event list: timestamp, type, agent, summary. Truncates at limit. |
| `format_task_full(task)` | 38-63 | FULL task: id, status, priority, agent, type, stage, readiness, SP, verbatim (FULL), description (500 char), blocked_by, PR, Plane. This is NOT truncated — verbatim requirement appears in full. |
| `build_task_preembed(task, completeness)` | 66-91 | Task context = format_task_full() + stage instructions from stage_context.py + artifact completeness if available. |
| `build_heartbeat_preembed(agent, role, tasks, messages, directives, events, role_data, fleet_mode, fleet_phase, fleet_backend, agents_online, agents_total)` | 94-170 | Structured markdown with headers: HEARTBEAT CONTEXT → PO DIRECTIVES → MESSAGES → ASSIGNED TASKS (FULL per task) → ROLE DATA → EVENTS. Fleet state on first line. |

### 4.5 `context_writer.py` — File Writer (86 lines)

Writes to `agents/{name}/context/` directory. Gateway reads on heartbeat.

| Function | Lines | What It Does |
|----------|-------|-------------|
| `write_heartbeat_context(agent_name, content)` | 24-37 | Write `fleet-context.md`. Creates context/ dir if missing. Returns True on success. |
| `write_task_context(agent_name, content)` | 40-53 | Write `task-context.md`. Created at dispatch time, refreshed every cycle for in-progress tasks. |
| `clear_task_context(agent_name)` | 56-67 | Delete `task-context.md`. Called when task completes or agent is pruned. |

AGENTS_DIR resolved from `__file__` → `fleet/core/` → `../../agents/` = repo root `agents/`.

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

---

## 8. Role Provider Data — What Each Agent Gets

The orchestrator uses role_providers to give each role different data
in their heartbeat context:

| Provider | Agent | Returns |
|----------|-------|---------|
| `fleet_ops_provider` | fleet-ops | `pending_approvals` (count + [{id, task_id, status}]), `review_queue` ([{id, title, agent}]), `offline_agents` ([names]) |
| `project_manager_provider` | PM | `unassigned_tasks` (count + [{id, title, priority}]), `blocked_tasks` (count), `progress` ("5/15 done (33%)"), `inbox_count` |
| `architect_provider` | architect | `design_tasks` ([{id, title, stage}] — epics/stories in analysis/investigation/reasoning), `high_complexity` ([{id, title}]) |
| `devsecops_provider` | devsecops | `security_tasks` ([{id, title}] — tagged security), `prs_needing_security_review` ([{id, title, pr}]) |
| `worker_provider` | all others | `my_tasks_count`, `in_review` ([{id, title, pr}]) |

Registry: `ROLE_PROVIDERS` dict → `get_role_provider(role)` falls back to worker_provider.

---

## 9. Data Shapes

### SessionSnapshot

```python
SessionSnapshot(
    model_id="claude-opus-4-6",
    context_window_size=1_000_000,
    context_used_pct=42.0,
    total_cost_usd=0.15,
    total_duration_ms=180_000,
    total_lines_added=256,
    total_lines_removed=31,
    cache_read_tokens=2000,
    five_hour_used_pct=23.5,
    seven_day_used_pct=41.2,
    # context_label = "1M"
    # context_pressure = "low"
    # cache_hit_rate = 0.13
)
```

### Assembled Task Context (dict)

```python
{
    "task": {"id": "abc123", "title": "Add Fleet Controls", "status": "in_progress"},
    "custom_fields": {"readiness": 30, "stage": "analysis", "requirement_verbatim": "Add fleet controls..."},
    "methodology": {
        "stage": "analysis",
        "stage_summary": "Analyzing codebase — produce analysis document",
        "stage_instructions": "## Current Stage: ANALYSIS\n\n### What you MUST do:\n...",
        "readiness": 30,
        "required_stages": ["analysis", "reasoning", "work"],
        "next_stage": "reasoning",
    },
    "artifact": {
        "type": "analysis_document",
        "data": {"title": "Header Analysis", "scope": "DashboardShell.tsx", "findings": [...]},
        "completeness": {
            "required_pct": 60,
            "missing_required": ["implications"],
            "suggested_readiness": 50,
            "summary": "Analysis: 3/5 required (60%). Missing: implications.",
        },
    },
    "comments": [{"author": "project-manager", "content": "Assigned for analysis...", "time": "..."}],
    "activity": [{"type": "fleet.task.dispatched", "time": "...", "agent": "architect"}],
    "related_tasks": [{"id": "def456", "title": "Design Review", "status": "inbox", "relation": "child"}],
    "plane": {"issue_id": "plane-uuid", "project_id": "project-uuid", "workspace": "fleet"},
}
```

### Context File (what gateway injects)

```markdown
# HEARTBEAT CONTEXT

Agent: architect
Role: architect
Fleet: 7/10 online | Mode: full-autonomous | Phase: execution | Backend: claude

## PO DIRECTIVES
- Focus on AICP Stage 1 (from human)

## ASSIGNED TASKS (1)

### Add Fleet Controls to Header
- ID: abc123
- Status: in_progress
- Stage: analysis
- Readiness: 30%
- Verbatim Requirement: Add fleet controls to the OCMC header bar
  so the PO can switch work mode, cycle phase, and backend mode
  without modifying config files.

## Current Stage: ANALYSIS
### What you MUST do:
- Read and examine the codebase, existing implementation, architecture
- Produce an analysis document (iterative, work-in-progress)
- Reference SPECIFIC files and line numbers
### What you MUST NOT do:
- Do NOT produce solutions (that's reasoning stage)
- Do NOT call fleet_commit or fleet_task_complete

## ROLE DATA
### design_tasks (3)
  - {'id': 'ghi789', 'title': 'Implement budget mode...', 'stage': 'reasoning'}

## EVENTS SINCE LAST HEARTBEAT
  2026-04-01T10:35 [completed] software-engineer: Task xyz done
```

---

## 10. Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_session_telemetry.py` | 30 | Ingest (full/minimal/empty/null), all distribution helpers, properties |
| `test_context_assembly.py` | 15+ | Task + heartbeat assembly, methodology inclusion, caching |
| `test_preembed.py` | 10+ | format_task_full (verbatim preserved), build functions |
| `test_heartbeat_context.py` | 10+ | Bundle building, capability filtering, format_message |
| **Total** | **65+** | Core logic covered. Missing: runtime integration, role provider integration |
