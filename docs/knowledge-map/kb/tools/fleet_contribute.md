# fleet_contribute

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — contributions can be posted from any stage

## Purpose

Contribute specialist input to another agent's task. When you're assigned a contribution task (design_input, security_requirement, qa_test_definition, ux_spec, documentation_outline), use this to deliver your input to the target task. Your contribution is embedded into the target agent's context so they can reference it during implementation.

## Parameters

- `task_id` (string) — The TARGET task ID (the task you're contributing TO, not your own)
- `contribution_type` (string) — Type: design_input, security_requirement, qa_test_definition, ux_spec, feasibility_assessment, infrastructure_design, application_requirements, implementation_context, design_context, technical_accuracy, architecture_context, documentation_outline
- `content` (string) — Your contribution content (full text, not compressed)

## Chain Operations

```
fleet_contribute(task_id, contribution_type, content)
├── POST COMMENT: typed contribution on target task (mc.post_comment)
├── UPDATE TARGET: contribution_type field on target task
├── MARK OWN DONE: own contribution subtask → status "done"
├── EMIT EVENT: fleet.contribution.posted
├── TRAIL: trail.contribution.posted event with agent + type + target
├── NOTIFY OWNER: @mention target task owner ("contribution received")
├── IRC: #fleet "[contribute] {agent} → {target}: {type}"
├── PLANE SYNC: post contribution as Plane issue comment
└── CHECK COMPLETENESS: all required contributions received?
    ├── YES → emit fleet.contribution.all_received
    │         notify PM: "all contributions in for task {target}"
    │         unblock dispatch gate (if contribution gate active)
    └── NO  → log which contributions still missing
```

## Who Uses It

| Role | Contribution Type | To Whom | When |
|------|------------------|---------|------|
| Architect | design_input | Engineer, DevOps, QA, Writer, DevSecOps | Task enters REASONING → brain creates contribution subtask |
| DevSecOps | security_requirement | Engineer, DevOps | Security-relevant tasks |
| QA | qa_test_definition | Engineer | Test criteria BEFORE implementation |
| UX | ux_spec | Engineer | UI-facing tasks |
| Engineer | feasibility_assessment | Architect | Architecture review |
| Engineer | implementation_context | QA, DevSecOps, Writer | After implementation |
| Writer | documentation_outline | PM | Documentation planning |
| DevOps | deployment_manifest | Engineer | Infrastructure for features |

## Relationships

- DEPENDS ON: fleet_read_context (load target task context first)
- CREATES: typed comment on target task
- UPDATES: target task's contribution tracking
- COMPLETES: own contribution subtask (auto-done)
- FEEDS: target agent's context (preembed.py → "INPUTS FROM COLLEAGUES" section)
- TRIGGERS: contribution completeness check (contributions.py)
- GATES: dispatch of target task (if contribution gate enabled — dispatch blocked until required contributions received)
- CONFIGURED BY: config/synergy-matrix.yaml (who contributes what to whom)
- SYNERGY MATRIX: fleet-elevation/15 defines the contribution relationships
- TRAIL: records trail.contribution.posted event
- EVENTS: fleet.contribution.posted, fleet.contribution.all_received (if complete)
- ANTI-PATTERN: doctor detects siloed_work if agent completes without receiving required contributions
