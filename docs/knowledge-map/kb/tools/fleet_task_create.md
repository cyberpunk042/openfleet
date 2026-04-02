# fleet_task_create

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Create a subtask, follow-up, or chained task on the OCMC board. Supports task hierarchy (parent/child), dependency chains (depends_on), agent assignment, story points, and task types. Enforces a cascade depth limit of 3 levels to prevent infinite auto-creation chains. Notifies IRC on creation.

## Parameters

- `title` (string) — Task title (required).
- `description` (string, optional) — Detailed description of what needs to be done.
- `agent_name` (string, optional) — Assign to a specific agent (e.g., "software-engineer").
- `project` (string, optional) — Project name (e.g., "nnrt", "dspd", "fleet").
- `priority` (string, optional) — "low", "medium", "high", "urgent". Default: "medium".
- `depends_on` (list[string], optional) — Task IDs that must complete first.
- `parent_task` (string, optional) — Parent task ID for subtask/story hierarchy.
- `task_type` (string, optional) — "epic", "story", "task", "subtask", "blocker", "request", "concern". Default: "task".
- `story_points` (integer, optional) — Effort estimate (1, 2, 3, 5, 8, 13).

## Chain Operations

```
fleet_task_create(title, description, agent_name, ...)
├── CASCADE DEPTH CHECK (max 3 levels)
│   ├── Walk parent_task chain via mc.list_tasks
│   ├── depth >= 3 → BLOCKED with error
│   └── Prevents infinite subtask chains
├── RESOLVE: agent_name → agent_id via mc.list_agents()
├── BUILD custom_fields: project, agent_name, parent_task, task_type, story_points
│   └── parent_task defaults to ctx.task_id if not specified
├── mc.create_task(board_id, title, description, priority, ...)
│   └── auto_created=True, auto_reason=f"Created by {creator}"
├── IRC: notify #fleet "SUBTASK" with title and assignee
└── RETURN: {ok, task_id, title, assigned_to, parent_task, depends_on, is_blocked}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| PM | Sprint planning | Create work items and subtasks |
| Architect | During analysis | Break down epic into stories |
| Engineer | During implementation | Create subtasks for complex work |
| Fleet-ops | During review | File fix tasks from rejected reviews |
| Any agent | When blocked | Create blocker or concern tasks |

## Relationships

- DEPENDS ON: fleet_read_context (board context needed for board_id)
- CALLS: mc.list_tasks (cascade depth check), mc.list_agents (agent resolution)
- CREATES: MC task with custom_fields (project, agent_name, parent_task, task_type, story_points)
- CONNECTS TO: dependency system (depends_on creates blocked tasks)
- CONNECTS TO: task hierarchy (parent_task creates subtask tree)
- IRC: notify #fleet "SUBTASK" event
- SAFETY: cascade depth limit (3 levels max) prevents runaway auto-creation
- FEEDS: fleet_task_accept (new tasks appear in agent inboxes)
- CONNECTS TO: fleet_plane_create_issue (PM creates Plane mirror for cross-surface sync)
