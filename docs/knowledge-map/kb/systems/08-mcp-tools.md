# System 08: MCP Tools — 29 Agent Operations

**Type:** Fleet System
**ID:** S08
**Files:** tools.py (~2800 lines), server.py (~100 lines), context.py (~80 lines)
**Total:** ~2,980 lines
**Tests:** 40+

## What This System Does

Defines every operation agents can perform. Each tool handles infrastructure automatically — agent provides semantic input ("summary of what I did"), tool handles MC API, GitHub, IRC, ntfy, Plane, events. One call to fleet_task_complete triggers 12+ internal operations across 6 surfaces. Stage gating prevents work tools outside work stage. Server runs via FastMCP stdio transport, one instance per agent session spawned by the gateway.

29 tools (25 original + 4 added this session: fleet_contribute, fleet_request_input, fleet_gate_request, fleet_transfer).

## Tool Categories

| Category | Tools | Count |
|----------|-------|-------|
| Task lifecycle | fleet_read_context, fleet_task_accept, fleet_task_progress, fleet_commit, fleet_task_complete, fleet_task_create | 6 |
| Communication | fleet_chat, fleet_alert, fleet_pause, fleet_escalate, fleet_notify_human | 5 |
| Review | fleet_approve | 1 |
| Fleet awareness | fleet_agent_status, fleet_task_context, fleet_heartbeat_context | 3 |
| Contributions | fleet_contribute, fleet_request_input, fleet_gate_request, fleet_transfer | 4 |
| Plane integration | fleet_plane_status, fleet_plane_sprint, fleet_plane_sync, fleet_plane_create_issue, fleet_plane_comment, fleet_plane_update_issue, fleet_plane_list_modules | 7 |
| Artifacts | fleet_artifact_read, fleet_artifact_update, fleet_artifact_create | 3 |

## Stage Gating

```python
WORK_ONLY_TOOLS = {"fleet_task_complete"}  # ONLY in work stage
COMMIT_ALLOWED_STAGES = {"analysis", "investigation", "reasoning", "work"}  # fleet_commit in stages 2-5
```

Calling a gated tool outside its allowed stage:
- Returns error to agent with specific message
- Emits fleet.methodology.protocol_violation event
- Doctor detects in next cycle → teaching lesson injected

## The Tool Pattern

Every tool follows the same architecture:
```
1. Get context (ctx = _get_ctx())
2. Validate (stage check, required params)
3. Resolve (board_id, task, agent info)
4. Execute primary action (MC API, git, etc.)
5. Fire side effects (try/except each — NEVER break primary action)
   ├── Trail event (board memory with trail tags)
   ├── IRC notification
   ├── Plane sync
   ├── Event emission
   └── ntfy (if priority warrants)
6. Return result dict
```

Side effects are individually wrapped in try/except. IRC down doesn't break task completion. Plane unconfigured doesn't block commits. The primary action always succeeds if the infrastructure allows it.

## MCP Server Architecture

```
Gateway starts Claude Code session for agent
├── Reads agents/{name}/mcp.json for server config
├── Spawns: python -m fleet.mcp.server (stdio transport)
├── Server creates FleetMCPContext from env vars:
│   FLEET_DIR, FLEET_TASK_ID, FLEET_PROJECT, FLEET_AGENT, FLEET_WORKSPACE
├── Lazy-initializes clients: MC (SQLite cache), IRC (WebSocket), GitHub (CLI), Plane (optional)
├── Registers 29 tools via register_tools(server)
└── Agent calls tools naturally during session
```

## Relationships

- SPAWNED BY: gateway (OpenClaw) per agent session
- ENFORCES: S01 methodology (stage gating on tools)
- FIRES: S04 event bus (every tool emits events)
- DETECTED BY: S02 immune system (protocol violations from stage gating)
- TREATED BY: S03 teaching (lessons for methodology violations)
- DISPATCHED BY: S07 orchestrator (dispatch triggers tool sessions)
- USES: S10 transpose (artifact tools use to_html/from_html)
- USES: S09 standards (artifact_tracker checks completeness)
- USES: S13 labor (labor stamp assembled at fleet_task_complete)
- USES: S14 router (route_task for backend selection at dispatch)
- SYNCS: S17 Plane (7 Plane tools + sync on completion/commit)
- ROUTES: S18 notifications (alerts, escalations → IRC + ntfy)
- CONNECTS TO: S19 session (context assembly for fleet_task_context, fleet_heartbeat_context)
- CONNECTS TO: agent_roles.py (PR authority checked at fleet_approve)
- CONNECTS TO: contributions.py (fleet_contribute checks synergy matrix)
- CONNECTS TO: trail_recorder.py (trail events from every tool — via PostToolUse hook)
- NOT YET IMPLEMENTED: challenge invocation from fleet_task_complete, codex review trigger, contributor notification on completion, parent aggregate evaluation, full trail recording per tool

## For LightRAG Entity Extraction

Key entities: FleetMCPContext (shared state), FastMCP server (stdio), 29 tool functions, WORK_ONLY_TOOLS, COMMIT_ALLOWED_STAGES, stage gating (_check_stage_allowed).

Key relationships: Agent CALLS tool. Tool VALIDATES stage. Tool EXECUTES primary action. Tool FIRES side effects. Tool EMITS events. Tool RECORDS trail. Stage gating BLOCKS wrong-stage calls. Gateway SPAWNS server. Context SHARES state across tools.
