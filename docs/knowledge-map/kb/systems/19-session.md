# System 19: Session & Context — The Data Pipeline Into Every Agent

**Type:** Fleet System
**ID:** S19
**Files:** session_telemetry.py (230), context_assembly.py (331), heartbeat_context.py (340), preembed.py (170), context_writer.py (86)
**Total:** 1,157 lines
**Tests:** 65+

## What This System Does

The DATA BACKBONE. Every 30 seconds, the brain computes FULL context for every agent and writes it to files the gateway injects into the system prompt. Zero MCP calls needed for awareness — agents wake up ALREADY KNOWING everything. FULL data, not compressed (the 300-char compression disease made agents non-functional).

Session telemetry parses REAL Claude Code JSON → distributes typed data to labor stamps, backend health, storm indicators, cost tracking.

## The Pipeline

```
Orchestrator Step 0: _refresh_agent_contexts()
├── mc.list_tasks(board_id)          → cached per cycle (10 agents = 1 call)
├── mc.list_memory(board_id)         → directives, mentions
├── For each agent:
│   ├── Filter tasks assigned to this agent
│   ├── Filter messages mentioning this agent
│   ├── Filter PO directives for this agent
│   ├── role_providers.py → role-specific data (5 providers)
│   ├── preembed.py: format_heartbeat_preembed() → structured markdown
│   └── context_writer.py: write files
│       ├── agents/{name}/context/fleet-context.md
│       └── agents/{name}/context/task-context.md
└── Gateway reads these files at next heartbeat → injects into system prompt
```

## HeartbeatBundle (20+ fields)

Identity, work (assigned tasks with verbatim + stage instructions), communication (chat messages, @mentions), domain events (filtered by agent subscriptions), sprint summary, Plane data (PM/fleet-ops only), fleet health, control state (work_mode, cycle_phase, backend_mode, budget_mode), budget warnings. ACTION directive at end drives HEARTBEAT_OK.

## Session Telemetry Adapter (W8)

Parses Claude Code JSON session data → SessionSnapshot (18 typed fields):
```
to_labor_fields(snap)      → LaborStamp fields (duration, tokens, cost, lines)
to_claude_health(snap)     → ClaudeHealth (quota 5h/7d, context %, latency)
to_storm_indicators(snap)  → StormMonitor (context_pressure, quota_pressure)
to_cost_delta(snap)        → BudgetMonitor (cost increase since last reading)
```

Properties: context_label (1M/200K), context_pressure (≥70%), cache_hit_rate.

**CRITICAL:** Adapter exists (230 lines, 30 tests). NOT WIRED to orchestrator runtime. Systems use estimates or zeros.

## Relationships

- PRODUCED BY: orchestrator.py Step 0 (every cycle)
- INJECTED BY: gateway (_build_agent_context reads context/ files)
- CONSUMED BY: every agent (wakes with context pre-loaded)
- CONNECTS TO: S07 orchestrator (Step 0 produces, Step 10 manages sessions)
- CONNECTS TO: S06 agent lifecycle (heartbeat data drives HEARTBEAT_OK → idle tracking)
- CONNECTS TO: S11 storm (session_telemetry → to_storm_indicators)
- CONNECTS TO: S12 budget (session_telemetry → to_cost_delta)
- CONNECTS TO: S13 labor (session_telemetry → to_labor_fields)
- CONNECTS TO: fleet-context.md Layer 6 (this system WRITES it)
- CONNECTS TO: task-context.md Layer 7 (this system WRITES it)
- CONNECTS TO: autocomplete chain (context assembly arranges data for correct behavior)
- NOT YET WIRED: session telemetry to runtime (systems use estimates), full role-specific pre-embed (PM needs Plane sprint, workers need artifact completeness), contribution data in worker context, HeartbeatBundle/preembed unification
