# fleet_read_context

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Load full task and project context. Call this FIRST every session before any other tool. Returns the complete task state including verbatim requirement, stage instructions, acceptance criteria, artifact state, contributions received, and related tasks.

## Parameters

- `task_id` (string) — The task ID from your assignment
- `project` (string) — Project name (e.g., "nnrt", "fleet")

## Chain Operations

```
fleet_read_context
├── mc.get_task(board_id, task_id)          → load task data
├── mc.list_memory(board_id, limit=20)      → board memory (decisions, alerts, mentions)
├── ctx.resolve_board_id()                  → resolve board
├── urls.resolve(project, task_id)          → resolve cross-reference links
├── store task_stage + task_readiness       → for stage enforcement by other tools
├── context_assembly.assemble_task_context()
│   ├── methodology: stage, instructions, required stages
│   ├── contributions: architect input, QA tests, DevSecOps reqs
│   ├── artifact: current state + completeness from Plane HTML
│   ├── comments: typed, with contributor attribution
│   ├── related_tasks: parent, children, dependencies
│   └── phase: current phase, standards, requirements
└── return: full context bundle
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL agents | Session start | First call — loads everything |
| Workers | Before fleet_task_accept | Need full context before planning |
| Fleet-ops | During review | Load task for 7-step review |
| PM | Heartbeat | Check assigned tasks |

## Relationships

- READS FROM: mc_client.py (MC API), context_assembly.py, methodology.py, stage_context.py
- STORES: task_stage and task_readiness in session context (used by _check_stage_allowed)
- FEEDS: all subsequent tool calls (they depend on context loaded here)
- CONNECTS TO: fleet_task_context (alternative full context call), fleet_heartbeat_context (role-specific variant)
- EVENTS: none emitted (read-only)
