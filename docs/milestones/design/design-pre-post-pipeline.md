# Design: Pre/Post Processing Pipeline

## User Requirements

> "What we need is a smart system in, middleware and out. pre - progress - post - etc"

> "preparation to task and before and after and structure and triggers and operations"

## The Pipeline

Every task execution goes through three phases. The fleet system handles each phase
so the agent focuses on its work.

### PRE — Before the Agent Thinks

**Trigger:** Task dispatched to agent via chat.send

**What the system does (before the agent sees anything):**

1. **Resolve context** — fleet MCP server starts, reads TOOLS.md, resolves project config
2. **Load task metadata** — read task from MC API: title, description, custom fields, tags, dependencies
3. **Load project state** — recent board memory for this project, active blockers, related tasks
4. **Prepare worktree** — if project task, worktree is already created by dispatch-task.sh
5. **Inject .mcp.json** — fleet MCP server config placed in agent workspace
6. **Set environment** — FLEET_DIR, project URLs, resolved references

**What the agent receives:**
- Task assignment message (from dispatch)
- Fleet MCP tools available (fleet_task_accept, fleet_commit, etc.)
- `fleet_read_context` tool ready — agent calls it first to get full picture

The agent's SOUL.md says: "First thing: call `fleet_read_context`. Then plan."

### PROGRESS — While the Agent Works

**The agent uses fleet MCP tools naturally:**

```
1. fleet_task_accept("Starting: will add type hints to engine module")
   → Server: PATCH task, post comment, notify IRC — agent doesn't see this

2. Agent reads code, thinks, edits files

3. fleet_commit(files=["nnrt/core/engine.py"], message="feat(core): add type hints")
   → Server: validate format, inject task ref, stage, commit — returns SHA

4. fleet_task_progress("Added type hints to 5 functions. Testing next.")
   → Server: post structured comment — agent doesn't format anything

5. Agent runs tests, fixes issues, commits again

6. fleet_task_complete("Added type hints to all public functions in engine.py")
   → Server: push, PR with changelog, custom fields, IRC, board memory — ALL OF IT
```

**The agent never:**
- Constructs a curl command
- Builds JSON payloads
- Resolves URLs manually
- Formats markdown templates
- Manages IRC notifications
- Updates custom fields directly

### POST — After the Agent Finishes

**Trigger:** Task moves to review (via fleet_task_complete)

**What the system does automatically:**

1. **Validate output quality** (fleet-monitor check):
   - PR body has changelog? diff table? references?
   - Task custom fields set (branch, pr_url)?
   - Completion comment uses structured format?
   - Board memory entry exists with proper tags?
   - IRC notifications sent?

2. **Create approval** (via fleet MCP during complete):
   - Confidence score from agent
   - Rubric scores from automated checks
   - Linked to task

3. **Notify** (automatic):
   - IRC #reviews: PR ready with link
   - IRC #fleet: task completed
   - Board memory: PR notification

4. **Wait for human** (fleet-sync monitors):
   - Human reviews PR on GitHub
   - Human approves approval in MC
   - fleet-sync detects → merges PR → moves to done → cleans worktree

5. **Post-completion** (fleet-monitor):
   - Verify merge happened
   - Update daily digest data
   - Log completion metrics

## How the Pipeline is Implemented

**NOT as a monolithic system.** As cooperating components:

| Component | Role | Implementation |
|-----------|------|----------------|
| dispatch-task.sh | PRE: create worktree, inject .mcp.json | Bash script (existing, enhanced) |
| Fleet MCP Server | PROGRESS: native tools for all operations | Python MCP server (new) |
| fleet-sync daemon | POST: merge detection, cleanup | Python daemon (existing, enhanced) |
| fleet-monitor daemon | POST: quality validation, alerts | Python daemon (existing, enhanced) |
| fleet-ops agent | POST: digest, gap detection, governance | AI agent on heartbeat |

Each component is independent. They communicate through MC API (tasks, board memory,
activity events) and IRC. No tight coupling.

> "We have to build clean patterns. make clean design pattern usage"

**Patterns used:**
- **Pipeline pattern**: pre → progress → post stages
- **Command pattern**: each fleet MCP tool is a command with execute/undo
- **Observer pattern**: fleet-sync and fleet-monitor observe MC state changes
- **Template method**: formatters follow template → fill → render
- **Strategy pattern**: alert routing by severity

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M125 | .mcp.json deployment in agent workspaces | Auto-configure during dispatch |
| M126 | fleet_read_context tool | Pre-task context injection |
| M127 | SOUL.md rewrite for tool-based workflow | "Call fleet_read_context first" |
| M128 | Post-task quality validation rules | What's checked, what fails |
| M129 | Approval creation in complete flow | Confidence + rubric on every task |
| M130 | Pipeline integration test | Pre → progress → post verified |

## Relationship to Other Designs

```
design-fleet-mcp-server.md → the PROGRESS layer (tools)
design-ocmc-primitives.md → the METADATA layer (tags, approvals, fields)
design-pre-post-pipeline.md → the ORCHESTRATION layer (when things happen)
design-fleet-python-library.md → the CODE layer (how it's built)
design-agent-interface.md → the AGENT layer (what agents know)
```

Five designs. One system. Each document is one concern.