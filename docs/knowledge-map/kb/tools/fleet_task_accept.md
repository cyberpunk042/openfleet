# fleet_task_accept

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** Allowed in reasoning and work stages. Blocked in conversation, analysis, investigation.

## Purpose

Accept an assigned task and submit a work plan. Transitions the task from inbox to in_progress, posts the plan as a structured comment, assesses plan quality against task type, and notifies IRC. Agents must call fleet_read_context first to load task context before accepting.

## Parameters

- `plan` (string) — Your approach: concrete steps, verification strategy, risks identified.
- `task_id` (string, optional) — Task ID if not already set via fleet_read_context.

## Chain Operations

```
fleet_task_accept(plan, task_id)
├── GATE: _check_stage_allowed("fleet_task_accept")
│   ├── conversation, analysis, investigation → BLOCKED
│   ├── reasoning, work → ALLOWED
│   └── violation → fleet.methodology.protocol_violation event → doctor
├── CONTEXT: resolve task_id (from param or ctx.task_id)
├── mc.get_task(board_id, task_id)           → load task_type for plan assessment
├── plan_quality.assess_plan(plan, task_type) → score 0-100, issues, suggestions
├── comment_tmpl.format_accept(plan, agent)  → structured acceptance comment
├── mc.update_task(board_id, task_id, status="in_progress")
│   └── Sets custom_fields.agent_name
├── irc.notify_event(agent, "STARTED", title, url) → IRC #fleet notification
└── RETURN: {ok, status: "in_progress", task_url, plan_score, plan_feedback?}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL worker agents | After fleet_read_context | Accept assignment, submit plan |
| Engineer | Before implementation | Share implementation approach |
| Architect | Before analysis | Share analysis plan |
| QA | Before test writing | Share test strategy |
| DevOps | Before infra work | Share IaC approach |

## Relationships

- DEPENDS ON: fleet_read_context (context must be loaded — task_id required)
- GATES: _check_stage_allowed — conversation/analysis/investigation stages block acceptance
- CALLS: plan_quality.assess_plan for plan scoring and feedback
- PRECEDES: fleet_commit, fleet_task_progress, fleet_task_complete
- UPDATES: MC task status (inbox → in_progress)
- SETS: custom_fields.agent_name on task
- IRC: notify_event "STARTED" to #fleet
- CONNECTS TO: comment_tmpl.format_accept (structured comment template)
- CONNECTS TO: methodology stage enforcement (REASONING_AND_WORK_TOOLS set)
