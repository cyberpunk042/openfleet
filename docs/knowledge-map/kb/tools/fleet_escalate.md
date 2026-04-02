# fleet_escalate

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Escalate to the human (PO) when direction, a decision, or human judgment is needed. Posts the escalation to board memory (persistent), as a task comment (if task exists), to IRC #alerts (immediate visibility), and sends an ntfy push notification with urgent priority. This is the primary human-in-the-loop tool — agents must not make decisions beyond their authority.

## Parameters

- `title` (string) — Short summary of what needs attention.
- `details` (string) — Full context: what you have found, what the options are.
- `task_id` (string, optional) — Task this relates to (uses current task if not specified).
- `question` (string, optional) — The specific question you need answered.

## Chain Operations

```
fleet_escalate(title, details, task_id, question)
├── CONTEXT: resolve task_id (param or ctx.task_id)
├── BOARD MEMORY: mc.post_memory
│   ├── Tags: ["escalation", "human-attention", "agent:{name}"]
│   └── Content: formatted escalation with title, agent, task, details, question
├── TASK COMMENT (if task_id exists):
│   └── mc.post_comment(board_id, task_id, formatted escalation)
├── IRC: irc.notify("#alerts", "NEEDS HUMAN" event)
│   └── Always #alerts channel (human-attention events)
├── NTFY: NtfyClient.publish
│   ├── priority: "urgent"
│   ├── tags: ["rotating_light", "escalation"]
│   └── Sends push notification to human's devices
└── RETURN: {ok, action: "Escalated. Wait for human response.", task_id}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL agents | Need human judgment | Cannot proceed without PO decision |
| Engineer | Ambiguous requirements | Multiple valid approaches |
| Architect | Architecture trade-offs | Strategic decisions beyond agent scope |
| Fleet-ops | Review disagreements | Conflicting reviewer opinions |
| QA | Test criteria unclear | Definition of done needs PO input |
| DevSecOps | Security risk assessment | Risk acceptance is human decision |

## Relationships

- DEPENDS ON: fleet_read_context (for task context, optional)
- STORES: board memory with escalation + human-attention tags
- POSTS: task comment (if task exists)
- IRC: notify #alerts "NEEDS HUMAN" event
- NTFY: urgent push notification via NtfyClient
- DISCOVERED BY: fleet_read_context (escalations field)
- CONNECTS TO: fleet_pause (often follows a pause)
- CONNECTS TO: fleet_notify_human (escalate is urgent; notify_human is general)
- CONNECTS TO: fleet_gate_request (gates are structured escalations at checkpoints)
- AGENT MUST: stop and wait for human response after escalating
