# Design: Agent Interface — What Agents Know and How They Work

## User Requirements

> "keep the AI process focus on its work not understanding how to call what tool or API"

> "we find a way to communicate and operate and execute smartly"

> "Some things are about how we remember and how we do things and then there is the per-cases where you have skills and workflows that popup for execution and such."

## The Problem

Current agent SOUL.md is a wall of text with curl command examples. The agent reads
it once and then improvises. Skills are available but optional. Templates exist but
agents don't use them. The agent spends cognitive load on infrastructure instead of work.

## The New Interface

With the Fleet MCP Server, the agent's interface changes fundamentally.
The agent doesn't need to know HTTP, JSON, or API endpoints. It has native tools.

### New SOUL.md Structure

The SOUL.md becomes SHORT and CLEAR. Not a reference manual — a workflow guide.

```markdown
# {Agent Name}

{Role description — 3-4 sentences}

## Your Tools

You have fleet tools available as native tool calls. Use them.

| Tool | When |
|------|------|
| `fleet_read_context` | First thing, every session |
| `fleet_task_accept` | When starting a task |
| `fleet_task_progress` | When you have an update |
| `fleet_commit` | When you have changes to commit |
| `fleet_task_complete` | When you're done |
| `fleet_alert` | When you find a problem |
| `fleet_suggest` | When you have an improvement idea |
| `fleet_pause` | When you're stuck or uncertain |

## Your Workflow

1. Call `fleet_read_context` → understand the task, project, team state
2. Call `fleet_task_accept` → announce you're starting
3. Do your work (read code, think, edit, test)
4. Call `fleet_commit` after each logical change
5. Call `fleet_task_progress` if working for a while
6. When done: call `fleet_task_complete` → everything else is handled for you
7. If stuck: call `fleet_pause` → explain why and wait

## Standards

{Link to STANDARDS.md — conventional commits, code hygiene, etc.}

## That's It

Focus on your expertise. The fleet system handles everything else:
URL resolution, PR creation, IRC notifications, board memory,
custom fields, tags, approvals. You just call the tools.
```

**Compare this to the current SOUL.md:** 100+ lines of curl commands, JSON
construction, and manual formatting instructions. The new version is under 50 lines.

### How Skills and Tools Relate

> "Some things are about how we remember and how we do things and then there is
> the per-cases where you have skills and workflows that popup for execution"

**Two layers:**

1. **Fleet MCP Tools** — always available, handle fleet operations
   - These are the "how we do things" — consistent, automated, every task
   - Agent calls them naturally like any tool

2. **Fleet Skills (SKILL.md)** — domain knowledge, triggered by context
   - These are the "per-cases where you have skills and workflows"
   - fleet-pr skill teaches the agent WHAT makes a good PR (knowledge)
   - The fleet MCP `fleet_task_complete` tool CREATES the PR (execution)
   - Skills inform. Tools execute.

**Example:**
- Agent reads fleet-pr skill → understands what a good PR looks like
- Agent calls `fleet_task_complete` → MCP server uses that knowledge to create the PR
- Agent doesn't manually create the PR — but UNDERSTANDS quality if asked to review one

### .mcp.json Deployment

Every agent workspace gets `.mcp.json` automatically:

```json
{
  "mcpServers": {
    "fleet": {
      "command": "python3",
      "args": ["-m", "fleet.mcp.server"],
      "env": {
        "FLEET_DIR": "{resolved_fleet_dir}",
        "FLEET_TASK_ID": "{task_id}",
        "FLEET_PROJECT": "{project_name}",
        "FLEET_AGENT": "{agent_name}"
      }
    }
  }
}
```

Deployed by:
- `push-soul.sh` — copies template to each workspace
- `dispatch-task.sh` — injects task-specific env vars

### What Agents DON'T Need to Know

| Current (agent must know) | New (system handles) |
|---------------------------|---------------------|
| MC API endpoints | Fleet MCP tools |
| HTTP headers, tokens | Config loaded by server |
| JSON payload construction | Tool params (simple) |
| URL templates + resolution | `fleet_resolve_urls` or automatic |
| IRC notification scripting | Automatic on operations |
| Template selection + filling | Server uses templates internally |
| Custom field names + values | Server sets them on operations |
| Tag taxonomy | Server applies correct tags |
| Git push mechanics | `fleet_commit` / `fleet_task_complete` |
| PR creation via `gh` CLI | Part of `fleet_task_complete` |

### Agent Evolution Path

As the fleet evolves, agents get smarter without changing their SOUL.md:

1. New template? → Update in fleet/templates/. MCP server uses it. Agents unchanged.
2. New custom field? → Add to fleet/core/. MCP server sets it. Agents unchanged.
3. New notification channel? → Add to fleet/infra/. MCP server routes. Agents unchanged.
4. New quality rule? → Add to fleet/core/. fleet-monitor checks. Agents unchanged.

> "make sure this evolve if we respect the rules and high standards"

The system evolves. Agents stay simple.

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M143 | New SOUL.md template | Tool-based workflow, under 50 lines |
| M144 | .mcp.json template + deployment | Auto-configured in agent workspaces |
| M145 | Skill ↔ Tool relationship documentation | Skills inform, tools execute |
| M146 | Agent onboarding guide | How a new agent joins the fleet |
| M147 | Integration test | Agent uses tools naturally, produces quality output |

## Open Questions

1. **Do agents need ALL fleet tools or a subset?** Could scope by role:
   - software-engineer: all tools
   - architect: fleet_task_*, fleet_alert, fleet_suggest (no fleet_commit)
   - technical-writer: fleet_task_*, fleet_commit (no fleet_alert)
   Per-agent tool filtering is possible in the MCP server.

2. **How does the MCP server know which task the agent is working on?**
   Via environment variable `FLEET_TASK_ID` injected by dispatch.
   Or agent calls `fleet_task_accept(task_id=...)` on first use.

3. **What if the agent ignores the tools and uses raw curl?**
   The tools work. Raw curl also works (backward compatible).
   But fleet-monitor flags quality violations from unstructured output.
   Over time, agents learn tools are easier.