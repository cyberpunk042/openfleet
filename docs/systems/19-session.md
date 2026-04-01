# System 19: Session & Context

**Source:** `fleet/core/session_telemetry.py`, `fleet/core/context_assembly.py`, `fleet/core/context_writer.py`, `fleet/core/preembed.py`, `fleet/core/heartbeat_context.py`
**Status:** 🔨 Session telemetry built (30 tests). Context assembly works. Pre-embed functional.
**Design docs:** `context-bundles.md` (CB01-05), `context-window-awareness-and-control.md`, `agent-rework/02`

---

## Purpose

Build, assemble, and inject context for agents. Session telemetry parses real Claude Code JSON data. Context assembly aggregates data from MC, Plane, events. Preembed formats it. Context writer writes to agent files. The brain uses this every cycle.

## Key Concepts

### Session Telemetry (session_telemetry.py — W8)

Parses Claude Code session JSON into `SessionSnapshot`:
- context_window_size, context_used_pct, context_remaining_pct
- total_cost_usd, total_duration_ms, total_api_duration_ms
- total_lines_added/removed, cache_read_tokens
- five_hour_used_pct, seven_day_used_pct (rate limits)

Distribution helpers:
- `to_labor_fields()` — real values for LaborStamp
- `to_claude_health()` — real quota/latency for ClaudeHealth
- `to_storm_indicators()` — context_pressure, quota_pressure, cache_miss
- `to_cost_delta()` — incremental cost for CostTicker

### Context Assembly (context_assembly.py)

Two assembly functions:
- `assemble_task_context(task, mc, board_id, plane, event_store)` — task core + custom fields + methodology (stage, instructions, readiness) + artifact (from Plane HTML via transpose) + comments + activity + related tasks + Plane data
- `assemble_heartbeat_context(agent, role, tasks, agents, mc, board_id, event_store, role_providers, fleet_state)` — role-specific via providers

Per-cycle cache prevents redundant API calls.

### Preembed (preembed.py)

- `format_task_full()` — FULL task detail (NOT truncated, except description at 500 chars)
- `build_task_preembed()` — task + stage instructions from stage_context.py
- `build_heartbeat_preembed()` — directives + messages + assigned tasks + role_data + events

### Context Writer (context_writer.py)

Writes to `agents/{name}/context/`:
- `write_heartbeat_context(agent_name, content)` → `fleet-context.md`
- `write_task_context(agent_name, content)` → `task-context.md`

Gateway reads these files when agent heartbeats.

### Role Providers (role_providers.py)

Per-role data:
- `fleet_ops_provider` → pending_approvals, review_queue, offline_agents
- `project_manager_provider` → unassigned_tasks, blocked_tasks, sprint progress
- `architect_provider` → tasks needing design review

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Step 0 refreshes all contexts every cycle | Orchestrator → Context |
| **Gateway** | Reads context/ files for system prompt | Context → Gateway |
| **Labor Stamps** | Session telemetry provides real values | Telemetry → Stamps |
| **Backend Health** | Session telemetry provides real quota | Telemetry → Health |
| **Storm** | Session telemetry provides context_pressure indicator | Telemetry → Storm |
| **Budget** | Session telemetry provides real cost | Telemetry → Budget |
| **Methodology** | Stage instructions injected into task context | Methodology → Context |
| **Plane** | Plane data assembled into task context | Plane → Context |

## What's Needed

- [ ] Full role-specific pre-embed per AR-01 spec (PM needs Plane sprint, workers need artifact completeness)
- [ ] Session telemetry wired to runtime (adapter built, not connected)
- [ ] Context size tracking (know how much context each agent uses)
- [ ] Contribution data included in worker context (requires fleet_contribute tool)
