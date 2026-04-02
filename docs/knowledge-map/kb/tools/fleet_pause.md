# fleet_pause

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Pause work and escalate when stuck, uncertain, or blocked. Posts a structured blocker comment on the task and notifies IRC with a BLOCKED event. The agent should stop work and wait for human input or another agent's help before continuing. Does not change task status — the task remains in_progress but visibly blocked.

## Parameters

- `reason` (string) — Why you are pausing (be specific).
- `needed` (string) — What would unblock you (who needs to do what).

## Chain Operations

```
fleet_pause(reason, needed)
├── CONTEXT: ctx.task_id must be set (via fleet_read_context)
├── comment_tmpl.format_blocker(reason, needed, agent)
├── mc.post_comment(board_id, task_id, comment)  → visible on task
├── IRC: irc.notify_event(agent, "BLOCKED", reason[:60], task_url)
│   └── Posted to #fleet with task URL
└── RETURN: {ok, action: "Wait for human input."}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL agents | When stuck | Signal need for help |
| Engineer | Unclear requirements | Need PO clarification |
| Architect | Conflicting constraints | Need human decision |
| QA | Test environment broken | Need DevOps fix |
| DevSecOps | Security concern | Need human approval to proceed |

## Relationships

- DEPENDS ON: fleet_read_context (task_id must be set)
- FOLLOWS: fleet_task_accept (task must be accepted/in_progress)
- POSTS: comment on task via mc.post_comment
- IRC: notify_event "BLOCKED" to #fleet channel
- CONNECTS TO: comment_tmpl.format_blocker (structured blocker template)
- CONNECTS TO: fleet_escalate (if blocker needs human decision, escalate)
- CONNECTS TO: fleet_request_input (if blocker needs another agent's expertise)
- DOES NOT CHANGE: task status (remains in_progress, agent stops working)
- DISCOVERED BY: fleet-ops heartbeat (blocked tasks visible in fleet_health)
