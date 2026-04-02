# fleet_task_progress

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Post a progress update on the current task. Reports what is done, what is next, and any blockers. Updates the task_progress custom field and emits checkpoint events at key thresholds (50%+). Creates trail entries in board memory for fleet-ops visibility.

## Parameters

- `done` (string) — What you have completed so far.
- `next_step` (string) — What you are working on next.
- `blockers` (string, optional) — Any blockers, or "none". Default: "none".
- `progress_pct` (integer, optional) — Work progress 0-100. Milestones: 0=started, 50=halfway, 70=done, 80=challenged, 90=reviewed. Default: 0.

## Chain Operations

```
fleet_task_progress(done, next_step, blockers, progress_pct)
├── CONTEXT: ctx.task_id must be set (via fleet_read_context)
├── comment_tmpl.format_progress(done, next_step, blockers, agent)
├── mc.post_comment(board_id, task_id, comment)    → visible on task
├── IF progress_pct > 0:
│   ├── mc.update_task(custom_fields={"task_progress": progress_pct})
│   └── IF progress_pct >= 50:
│       └── EVENT: fleet.methodology.checkpoint_reached
├── TRAIL: mc.post_memory → trail tag with progress % and task reference
└── RETURN: {ok: true, progress_pct}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL worker agents | During task execution | Report progress to board |
| Engineer | Mid-implementation | Show code progress |
| Architect | During analysis | Report investigation progress |
| QA | During test writing | Report coverage progress |
| Fleet-ops | During review | Provide feedback (via comment) |

## Relationships

- DEPENDS ON: fleet_read_context (task_id must be set)
- FOLLOWS: fleet_task_accept (task must be in_progress)
- PRECEDES: fleet_task_complete (progress accumulates toward completion)
- UPDATES: MC task custom_fields.task_progress
- TRAIL: trail.progress_update event in board memory
- EVENT: fleet.methodology.checkpoint_reached at 50%+ thresholds
- CONNECTS TO: comment_tmpl.format_progress (structured comment template)
- CONNECTS TO: methodology checkpoint system (progress milestones)
- FEEDS: fleet-ops heartbeat (progress visible in team_activity)
