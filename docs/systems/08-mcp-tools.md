# MCP Tools — 25 Agent Operations

> **3 files. 2517 lines. 25 tools that define what agents CAN DO.**
>
> Every agent operation goes through an MCP tool. Each tool handles
> infrastructure automatically — the agent provides semantic input,
> the tool does MC API calls, GitHub operations, IRC notifications,
> Plane sync, and event emission. Stage gating prevents work tools
> outside work stage. The server runs via stdio transport from the
> gateway, one instance per agent session.

---

## 1. Why It Exists

Without MCP tools, agents would need to:
- Make raw HTTP calls to MC API (authentication, error handling)
- Run git commands directly (branch naming, commit format)
- Post to IRC manually (channel selection, format)
- Create PRs with proper templates (changelog, labels)
- Update Plane issues (label sync, state mapping)
- Track events (emit, route, persist)

Each of these is 20-50 lines of infrastructure code. An agent doing
a task completion would need ~200 lines of infrastructure. With
MCP tools, it's one call:

```python
fleet_task_complete(summary="Added fleet controls to header bar")
```

This one call triggers: git push → PR creation → MC status update →
approval creation → completion comment → IRC notification → ntfy
notification → Plane state update → event emission → metrics update.

The agent thinks semantically. The tool handles infrastructure.

---

## 2. How It Works

### 2.1 The MCP Server

```
Gateway starts agent session
  ↓
Gateway reads agents/{name}/mcp.json (or _template/mcp.json)
  ↓
Gateway spawns: python -m fleet.mcp.server (stdio transport)
  ↓
Server creates FleetMCPContext from env vars:
  FLEET_DIR, FLEET_TASK_ID, FLEET_PROJECT, FLEET_AGENT, FLEET_WORKSPACE
  ↓
Server registers 25 tools via register_tools(server)
  ↓
Agent calls tools naturally during Claude Code session
  ↓
Tool handler: validates input → calls infrastructure → fires events
  ↓
Returns result dict to agent
```

### 2.2 Stage Gating

```python
WORK_ONLY_TOOLS = {"fleet_commit", "fleet_task_complete"}

Agent calls fleet_commit during analysis stage:
  ↓
_check_stage_allowed("fleet_commit")
  ↓
stage = "analysis" ≠ "work"
  ↓
Emit: fleet.methodology.protocol_violation
  ↓
Return: {"ok": False, "error": "Methodology violation: fleet_commit
         is only allowed during work stage. Your task is in 'analysis'
         stage. Complete the analysis protocol first."}
  ↓
Doctor picks up violation next cycle → teaching lesson
```

### 2.3 Context (Shared State)

```
FleetMCPContext (one per server instance):
  ├── fleet_dir     — fleet repo root
  ├── task_id       — current task (set by fleet_read_context)
  ├── project_name  — project name
  ├── agent_name    — from FLEET_AGENT env var
  ├── board_id      — OCMC board (resolved lazily)
  ├── worktree      — git worktree path
  ├── fleet_id      — fleet identity (for cross-fleet)
  │
  └── Clients (lazy-initialized):
      ├── mc     — MCClient (MC API, cached with SQLite)
      ├── irc    — IRCClient (gateway WebSocket)
      ├── gh     — GHClient (GitHub API)
      ├── plane  — PlaneClient (optional — None if not configured)
      └── urls   — UrlResolver (config-driven URL templates)
```

---

## 3. The 25 Tools — Complete Reference

### 3.1 Task Lifecycle (6 tools)

| Tool | Stage Gate | What It Does | Chain |
|------|-----------|-------------|-------|
| `fleet_read_context(task_id, project)` | Any | Load task + project + board memory + URLs + team state. Sets ctx.task_id for subsequent calls. | None (read-only) |
| `fleet_task_accept(plan, task_id)` | Any | Accept task with plan. Updates status → in_progress. Assesses plan quality (score/100). Posts acceptance comment. | → MC update → IRC notification |
| `fleet_task_progress(done, next_step, blockers)` | Any | Post progress comment on current task. | → MC comment |
| `fleet_commit(files, message)` | **WORK only** | Stage files, git commit (conventional format with task ref). | → git commit → event |
| `fleet_task_complete(summary)` | **WORK only** | Complete task: push branch, create PR, update MC, create approval, post comment, notify IRC+ntfy, update Plane. | → push → PR → MC → approval → comment → IRC → ntfy → Plane → event |
| `fleet_task_create(title, description, ...)` | Any | Create task/subtask. Sets parent_task, depends_on, agent, type, stage, readiness, SP. | → MC create → event → IRC |

### 3.2 Communication (5 tools)

| Tool | What It Does | Chain |
|------|-------------|-------|
| `fleet_chat(message, mention, channel)` | Post to board memory. @mention routes to agent heartbeat. Tags for searchability. | → MC memory → @mention routing → IRC |
| `fleet_alert(severity, title, details, category)` | Raise alert. Categories: security, quality, architecture, workflow. Critical/high → ntfy PO. | → MC memory → IRC (#alerts or #fleet) → ntfy |
| `fleet_pause(reason, needed)` | Pause work, report blocker. Creates board memory entry. | → MC memory → IRC |
| `fleet_escalate(title, details, severity)` | Escalate to human. Always goes to ntfy + IRC #alerts. | → MC memory → ntfy PO → IRC #alerts |
| `fleet_notify_human(title, message, priority)` | Direct notification to PO. Priority: info/important/urgent. | → ntfy |

### 3.3 Review (1 tool)

| Tool | What It Does | Chain |
|------|-------------|-------|
| `fleet_approve(approval_id, decision, comment)` | Approve or reject. Checks agent PR authority (can_reject, rejection_creates_fix_task). On approve: task → done. On reject: post feedback, optionally create fix task. | → MC approval → status update → event → IRC #reviews |

### 3.4 Fleet Awareness (2 tools)

| Tool | What It Does |
|------|-------------|
| `fleet_agent_status()` | Agent statuses, task counts by status, pending approvals, fleet mode. |
| `fleet_task_context(task_id)` | Full assembled task context: task + methodology + artifact + comments + activity + related + Plane. Uses context_assembly.assemble_task_context(). |
| `fleet_heartbeat_context()` | Role-specific heartbeat data. Uses context_assembly.assemble_heartbeat_context(). |

### 3.5 Plane Integration (7 tools)

| Tool | What It Does |
|------|-------------|
| `fleet_plane_status(project)` | Project status: sprint, modules, recent issues. |
| `fleet_plane_sprint(project)` | Current sprint: issues, progress, velocity. |
| `fleet_plane_sync(direction)` | Trigger Plane ↔ OCMC sync. Direction: "both", "plane_to_ocmc", "ocmc_to_plane". |
| `fleet_plane_create_issue(title, description, project, ...)` | Create Plane issue with labels, priority, module. |
| `fleet_plane_comment(issue_id, comment, project)` | Comment on Plane issue. Agent name prefixed. |
| `fleet_plane_update_issue(issue_id, project, state, priority, labels)` | Update Plane issue fields. |
| `fleet_plane_list_modules(project)` | List modules with status, lead, issue counts. |

### 3.6 Artifact Management (3 tools)

| Tool | What It Does | Chain |
|------|-------------|-------|
| `fleet_artifact_read(task_id)` | Read structured artifact from task's Plane issue. Reverse transpose: HTML → object. | ← Plane HTML → object |
| `fleet_artifact_update(field, value, append, task_id)` | Update artifact field. Forward transpose: object → HTML. Checks completeness against standard. | → object update → Plane HTML → completeness check → readiness suggestion |
| `fleet_artifact_create(artifact_type, title, task_id)` | Create new artifact of given type. Initialize with standard's required fields. Render to Plane HTML. | → object create → Plane HTML → initial completeness |

---

## 4. File Map

```
fleet/mcp/
├── tools.py      25 tool definitions, stage gating, review gates  (2280 lines)
├── server.py     FastMCP server setup, stdio transport             (74 lines)
└── context.py    Shared state: clients, env, fleet identity        (163 lines)
```

Total: **2517 lines**.

---

## 5. Per-File Documentation

### 5.1 `tools.py` — 25 Tool Definitions (2280 lines)

#### Internal Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `_build_review_gates(task_type, has_code)` | 21-60 | Build reviewer requirements: QA for code, architect for epic/story, devsecops for security, fleet-ops always final. |
| `_get_ctx()` | 69-75 | Get or create FleetMCPContext from env. Singleton per server. |
| `_report_error(tool_name, error)` | 77-84 | Log tool errors to .fleet-errors.json. |
| `_emit_event(event_type, ...)` | 86-128 | Emit fleet event with standard fields. Try/except — events never break tools. |
| `_check_stage_allowed(tool_name)` | 137-171 | Stage gate: WORK_ONLY_TOOLS blocked outside work stage. Returns error dict + emits protocol_violation. |
| `register_tools(server)` | 174+ | Register all 25 tools on FastMCP server. |

#### Tool Patterns

Every tool follows the same pattern:
```python
@server.tool()
async def fleet_xxx(args) -> dict:
    # 1. Get context
    ctx = _get_ctx()

    # 2. Validate (stage check if needed)
    stage_error = _check_stage_allowed("fleet_xxx")
    if stage_error:
        return stage_error

    # 3. Resolve board/task
    board_id = await ctx.resolve_board_id()

    # 4. Execute primary action (MC API, git, etc.)
    try:
        result = await ctx.mc.do_something(...)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # 5. Fire side effects (IRC, ntfy, events — try/except each)
    try:
        await ctx.irc.notify_event(...)
    except Exception:
        pass  # side effects never break primary action

    # 6. Return result
    return {"ok": True, "data": result}
```

### 5.2 `server.py` — MCP Server (74 lines)

| Function | Lines | What It Does |
|----------|-------|-------------|
| `create_server()` | 20-34 | Create FastMCP with name="fleet" and instructions. Call register_tools(). |
| `run_server()` | 37-71 | Log startup to .fleet-mcp-debug.log. Create server. Log registered tools. Run with stdio transport. |

### 5.3 `context.py` — Shared State (163 lines)

| Class | Lines | Purpose |
|-------|-------|---------|
| `FleetMCPContext` | 23-164 | Shared state for all tools. Env-based init. Lazy clients: mc (with SQLite cache), irc (gateway WebSocket), gh (GitHub), plane (optional), urls (config-driven). Fleet identity for cross-fleet ops. |

| Method | What It Does |
|--------|-------------|
| `from_env()` | Create context from FLEET_DIR, FLEET_AGENT, etc. Load fleet identity. |
| `mc` (property) | Lazy MCClient with auth from TOOLS.md or env. SQLite cache. |
| `irc` (property) | Lazy IRCClient with gateway token from openclaw.json. |
| `gh` (property) | Lazy GHClient. |
| `plane` (property) | Lazy PlaneClient — returns None if not configured. |
| `urls` (property) | Lazy UrlResolver from config templates. |
| `resolve_board_id()` | Resolve board ID from MC API if not known. |

---

## 6. Dependency Graph

```
server.py      ← imports register_tools from tools
    ↑
tools.py       ← imports FleetMCPContext from context
    │             imports from fleet.core: plan_quality, comment templates,
    │             pr templates, irc templates, memory templates,
    │             event_chain, event_router, events, agent_roles,
    │             behavioral_security, context_assembly, methodology
    ↑
context.py     ← imports: MCClient, IRCClient, GHClient, PlaneClient,
                  ConfigLoader, UrlResolver, Project, federation
```

tools.py is the hub — it imports from nearly every fleet.core module.

---

## 7. Consumers

MCP tools are consumed by AGENTS via Claude Code sessions. They are
not imported by Python code — they're called via MCP protocol.

| Consumer | How |
|----------|-----|
| **All 10 agents** | Via Claude Code MCP tool calls during heartbeat/task sessions |
| **Gateway** | Spawns the MCP server process per agent session |
| **Template** | `agents/_template/mcp.json` configures the fleet MCP server |

---

## 8. Design Decisions

### Why 25 tools, not fewer?

Each tool is ONE semantic operation. Combining "commit + complete"
into one tool would prevent incremental commits. Splitting "alert"
into "alert_security" and "alert_quality" would add confusion.
25 tools cover the full agent operation surface without overlap.

### Why stage gating in the tool layer, not the gateway?

The tool layer knows the task stage (from ctx). The gateway doesn't
know stage — it's a session manager. Gating at the tool level means
the error message is specific and actionable: "Your task is in
analysis stage. Complete the analysis protocol first."

### Why lazy-initialized clients?

Not every tool call needs every client. fleet_chat needs MC and IRC
but not GitHub or Plane. Lazy init means clients are only created
when first needed, reducing startup time and avoiding auth errors
for unconfigured services.

### Why try/except around side effects?

IRC being down should not prevent task completion. Plane not configured
should not break commits. Each side effect (IRC, ntfy, Plane, events)
is independently wrapped in try/except. The primary action (MC update,
git commit) is the only thing that can fail the tool call.

### Why does fleet_task_complete handle EVERYTHING?

One call = complete lifecycle. The agent shouldn't need to know about
branch pushing, PR templates, approval creation, IRC channels, or
Plane state mapping. All of that is infrastructure the tool handles.
This is the "smart chains" philosophy: "why call 5 tools when you
can call one that does it all?"

### Why does fleet_approve check PR authority?

Not every agent can reject PRs. If software-engineer calls
fleet_approve with decision="rejected", the tool checks
can_agent_reject() from agent_roles.py. This prevents unauthorized
rejections without relying on the agent to know its own authority.

---

## 9. Tools NOT Implemented (Design Docs Specify)

| Tool | Purpose | Blocker |
|------|---------|---------|
| `fleet_contribute` | Post contribution to another agent's task | Contribution flow not designed in code |
| `fleet_request_input` | Request missing contribution from PM | Requires fleet_contribute first |
| `fleet_gate_request` | Request PO gate approval (phase advancement) | Phase gate enforcement not in orchestrator |

These 3 tools are the CRITICAL gap for the contribution flow
described in fleet-elevation/15 (cross-agent synergy).

The event_chain.py already has `build_contribution_chain()` and
`build_gate_request_chain()` — the chain builders exist, the
tools to trigger them don't.

---

## 10. What's Needed

### Missing Tools (3)

1. **`fleet_contribute(task_id, contribution_type, content)`**
   - Agent posts design_input, qa_test_definition, security_requirement,
     ux_spec, or documentation_outline to another agent's task
   - Fires `build_contribution_chain()` (already exists in event_chain.py)
   - Updates target task's custom fields with contribution data
   - Pre-embed includes contribution in target agent's task context

2. **`fleet_request_input(task_id, target_role, request)`**
   - Agent requests missing contribution from PM
   - PM creates contribution subtask for the right specialist

3. **`fleet_gate_request(task_id, gate_type, summary)`**
   - Agent requests PO gate approval for phase advancement
   - Fires `build_gate_request_chain()` (already exists in event_chain.py)
   - Routes to ntfy with high priority

### Existing Tool Improvements

- `fleet_artifact_update` — completeness check not reliably connected to readiness suggestion
- `fleet_task_complete` — labor stamp assembly not integrated
- `fleet_approve` — challenge engine not integrated (trainee tier should trigger challenge)
- Session telemetry data not flowing into tool responses

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_tools.py` | 30+ | Tool registration, stage gating, review gates |
| `test_mcp_context.py` | 10+ | Context creation, lazy clients |
| **Total** | **40+** | Core logic covered. Missing: full chain execution, Plane integration |
