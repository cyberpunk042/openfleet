# Design: Fleet MCP Server — Native Tools for Agents

## User Requirements

> "keep the AI process focus on its work not understanding how to call what tool or API"

> "Imagine inline command during the AI work and he knows that if he writes this in live we have a process that catch it and does the work that is needed"

> "I dont want an expression that could be a clean, clear and interpolated, interoperable, one liner to be a monstruous long or even multiline operation of something that could be greatly reduced / optimised / made better / easier to use and leaner"

## The Revolution

Currently an agent updating a task writes 5 lines of curl with JSON construction,
header management, URL building, and error handling. That's **the agent doing
infrastructure work instead of its actual job.**

MCP (Model Context Protocol) is Anthropic's protocol for giving LLMs native tools.
OpenClaw already integrates MCP — agents can call MCP tools as naturally as they
call `exec` or `read`. A tool call is ONE structured invocation, not a bash script.

**We build a Fleet MCP Server.** It runs as a subprocess alongside the agent.
It exposes fleet operations as native tools. The agent calls them like any other tool.
The server handles everything — API calls, URL resolution, template filling,
IRC notification, custom field updates, tag management.

## What Changes

### Before (current — agent writes infrastructure code):
```
Agent thinks: "I need to update the task status"
Agent writes: curl -s -X PATCH "$BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID" \
  -H "X-Agent-Token: $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "comment": "Starting work.", "custom_field_values": {"branch": "fleet/sw-eng/abc123"}}'
Agent then writes: bash scripts/notify-irc.sh --agent "software-engineer" --event "STARTED" ...
```

### After (revolution — agent calls a native tool):
```
Agent thinks: "I need to update the task status"
Agent calls: fleet_task_update(status="in_progress", comment="Starting work.")
→ Server handles: API call, custom field update, IRC notification, board memory — ALL OF IT
```

The agent's context is spent on THINKING and WORKING, not on bash/curl/JSON.

## MCP Server Design

### How It Runs

OpenClaw loads MCP servers from `.mcp.json` in the agent workspace.
Each server is a subprocess (stdio transport).

```json
// .mcp.json in each agent workspace
{
  "mcpServers": {
    "fleet": {
      "command": "python3",
      "args": ["-m", "fleet.mcp_server"],
      "env": {
        "FLEET_DIR": "/path/to/openclaw-fleet"
      }
    }
  }
}
```

The fleet MCP server is a Python module (`fleet/mcp_server.py`) that:
1. Reads TOOLS.md for credentials on startup
2. Reads config/url-templates.yaml for URL resolution
3. Exposes tools via MCP protocol
4. Handles all API calls, formatting, notifications internally

### Tools Exposed

Each tool is what an agent would naturally want to do. Clean I/O. Minimal params.
The server handles all complexity internally.

#### `fleet_task_accept`
**What agent provides:** task_id, brief plan
**What server does:** PATCH task status=in_progress, post structured acceptance comment,
notify IRC #fleet, set custom fields if missing

#### `fleet_task_progress`
**What agent provides:** summary of what's done, what's next
**What server does:** POST structured progress comment using template, with URLs

#### `fleet_task_complete`
**What agent provides:** summary of what was done
**What server does:**
1. Push branch to remote
2. Create PR with changelog, diff table, all URLs (fleet-pr template)
3. Set task custom fields (branch, pr_url)
4. Post structured completion comment with all refs
5. Notify IRC #fleet and #reviews
6. Post to board memory (tags: pr, review, project:{name})
7. Move task to review

One tool call. The agent just says "I'm done, here's what I did."

#### `fleet_commit`
**What agent provides:** files to stage, commit message (type + description)
**What server does:** validate conventional format, inject task reference,
stage files, commit. Returns commit SHA.

#### `fleet_alert`
**What agent provides:** severity, title, details, category
**What server does:** route to correct surfaces based on severity (IRC channel,
board memory tags, task blocker if critical). All formatting handled.

#### `fleet_suggest`
**What agent provides:** title, observation, suggestion, area
**What server does:** post to board memory with proper template and tags,
notify IRC #fleet

#### `fleet_create_task`
**What agent provides:** title, description, target agent, priority
**What server does:** create task via MC API with project custom field,
proper tags, parent task reference, notify board memory + IRC

#### `fleet_pause`
**What agent provides:** reason, what's needed to unblock
**What server does:** post blocker comment, notify IRC #fleet,
post to board memory if cross-agent impact

#### `fleet_gap`
**What agent provides:** what's missing, category, impact
**What server does:** post gap report to board memory with template,
notify IRC #fleet

#### `fleet_resolve_urls`
**What agent provides:** project, branch, files, task_id
**What server does:** resolve all URLs from config, return as structured data.
Agent uses these in its own markdown output.

#### `fleet_board_memory`
**What agent provides:** content, type (alert/decision/suggestion/knowledge), tags
**What server does:** format with template, ensure tags, post to MC API

#### `fleet_read_context`
**What agent provides:** (nothing — or project name)
**What server does:** return recent board memory entries, active tasks,
recent decisions, known blockers. Agent starts INFORMED.

### Tool I/O Design

> "We need to think I/O and directive and Meta"

Every tool follows the same pattern:

**Input:** minimal, semantic, what the agent naturally knows
```json
{
  "summary": "Added type hints to all public functions",
  "files_changed": ["nnrt/core/engine.py", "nnrt/core/contracts.py"]
}
```

**Output:** structured, rich, everything the agent might need next
```json
{
  "ok": true,
  "pr_url": "https://github.com/.../pull/5",
  "branch": "fleet/software-engineer/abc123",
  "compare_url": "https://github.com/.../compare/main...fleet/...",
  "task_url": "http://localhost:3000/boards/.../tasks/...",
  "notifications": ["IRC #fleet", "IRC #reviews", "board memory"],
  "next_steps": "Task moved to review. Human will review PR."
}
```

The agent can use the output URLs in its own responses if needed.

## Pre-Processing: Context Injection

> "preparation to task and before"

When the agent starts a session, the MCP server provides `fleet_read_context`:

```json
{
  "task": {
    "id": "...", "title": "...", "description": "...",
    "project": "nnrt", "custom_fields": {...}, "tags": [...]
  },
  "project": {
    "name": "nnrt", "owner": "cyberpunk042", "repo": "...",
    "worktree": "/path/to/worktree", "branch": "fleet/sw-eng/..."
  },
  "urls": {
    "task": "http://localhost:3000/...",
    "compare": "https://github.com/...",
    "board": "http://localhost:3000/..."
  },
  "recent_board_memory": [
    {"content": "...", "tags": [...], "created_at": "..."}
  ],
  "recent_decisions": [...],
  "active_blockers": [...],
  "team_activity": [
    {"agent": "architect", "task": "...", "status": "in_progress"}
  ]
}
```

Agent starts with FULL AWARENESS. No manual context loading.

## Post-Processing: Validation

> "after and structure and triggers and operations"

After the agent completes (task moves to review), fleet-sync + fleet-monitor:
1. Validate PR body has changelog, diff table, URLs
2. Validate task custom fields are set
3. Validate board memory entry exists
4. Validate IRC notifications were sent
5. If any fail → quality alert to governance agent

## Architecture: Clean Code

> "strong OOP and SRP... never more than ~500"

```
fleet/
├── mcp_server.py          # MCP server entry point (<200 lines)
├── core/
│   ├── __init__.py
│   ├── task.py             # Task operations (accept, progress, complete)
│   ├── pr.py               # PR creation with templates
│   ├── commit.py           # Git commit operations
│   ├── alert.py            # Alert routing by severity
│   ├── memory.py           # Board memory operations
│   └── urls.py             # URL resolution
├── infra/
│   ├── __init__.py
│   ├── mc_client.py        # Mission Control API client
│   ├── irc_client.py       # IRC notification (via gateway RPC)
│   ├── gh_client.py        # GitHub CLI wrapper
│   └── config.py           # Config loading (url-templates, projects)
├── templates/
│   ├── __init__.py
│   ├── pr_body.py          # PR body composer
│   ├── comment.py          # Task comment formatters
│   ├── memory.py           # Board memory formatters
│   └── irc.py              # IRC message formatters
└── tests/
    ├── test_task.py
    ├── test_pr.py
    └── ...
```

Each file: one responsibility, under 500 lines, documented.

## What This Replaces

| Current | New |
|---------|-----|
| 25+ bash scripts | Python `fleet/` package |
| Inline curl in SKILL.md | Native MCP tool calls |
| Agent constructs JSON | Agent calls tool with simple params |
| Manual URL resolution | Automatic in server |
| Manual IRC notification | Automatic on every operation |
| Manual template filling | Server uses templates internally |
| No pre-task context | `fleet_read_context` provides everything |
| No post-task validation | fleet-monitor checks quality |

## Dependencies

- MCP Python SDK: `mcp` package (Anthropic's official SDK)
- OpenClaw MCP integration: already built in (`.mcp.json` config)
- Fleet config: url-templates.yaml, projects.yaml, skill-assignments.yaml
- MC API: existing endpoints (tasks, board memory, approvals, activity)
- GitHub CLI: `gh` for PR operations

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M106 | Fleet MCP server scaffold | Entry point, MCP protocol, tool registration |
| M107 | fleet/infra/ — MC client, IRC client, GH client | Clean API wrappers |
| M108 | fleet/core/task.py — accept, progress, complete | Task lifecycle tools |
| M109 | fleet/core/pr.py — push, changelog, PR creation | PR composer tool |
| M110 | fleet/core/alert.py + memory.py | Alert routing, board memory tools |
| M111 | fleet/templates/ — all formatters | PR body, comments, memory, IRC |
| M112 | fleet_read_context — pre-task injection | Context loading tool |
| M113 | .mcp.json deployment | Auto-configure in agent workspaces |
| M114 | Agent SOUL.md rewrite | Teach tool-based workflow |
| M115 | Post-task quality validation | fleet-monitor checks |
| M116 | E2E quality test | Full task with MCP tools |

## Open Questions

1. **MCP server per agent or shared?** Per-agent reads TOOLS.md for that agent's creds.
   Shared would need credential routing. Per-agent is simpler and more secure.

2. **How does the MCP server get the task context?** From the dispatch message?
   Or by reading board state on startup? Both — dispatch provides task_id,
   server reads full context from MC API.

3. **Error handling:** What if MC API is down? What if push fails?
   Server returns structured error. Agent sees it as tool error. Agent can retry or pause.

4. **Testing:** How do we test MCP tools? Mock MC API + mock GitHub.
   Unit tests for each tool. Integration test with real MC.