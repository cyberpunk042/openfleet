# fleet_task_complete

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** WORK stage ONLY — blocked in conversation, analysis, investigation, reasoning

## Purpose

Complete your task. One call does everything: push branch, create PR, assemble labor stamp, update MC status to review, create approval for fleet-ops, fire event chain across all 6 surfaces (MC, GitHub, IRC, ntfy, Plane, event bus). The flagship tool — 12+ internal operations from one agent call.

## Parameters

- `summary` (string) — What you did and why (2-3 sentences)

## Chain Operations

```
fleet_task_complete(summary)
├── GATE: _check_stage_allowed("fleet_task_complete") → blocks outside work
├── RUN TESTS: pytest --tb=line -q → pass/fail + summary
├── GET BRANCH: git branch --show-current
├── GET COMMITS: git log --oneline (since dispatch)
├── GET DIFF: git diff --stat
├── PUSH: git push origin {branch}
├── CREATE PR: gh pr create (title, body with labor attribution)
├── LABOR STAMP: assemble from dispatch_record + session telemetry
│   ├── agent_name, backend, model, effort, confidence_tier
│   ├── duration_seconds, estimated_tokens, skills_used
│   └── Write 8+ labor_* fields to task custom_fields
├── REVIEW GATES: build per task_type + confidence_tier
│   ├── trainee/community → challenge + architect + fleet-ops
│   ├── standard → fleet-ops only
│   └── epic/blocker → + architect/devsecops review
├── UPDATE MC: status → "review", custom_fields (branch, pr_url, labor_*)
├── CREATE APPROVAL: confidence based on tests + compliance
├── EVENT CHAIN: build_task_complete_chain()
│   ├── INTERNAL: update task, create approval, post memory (trail)
│   ├── PUBLIC: push branch, create PR
│   ├── CHANNEL: IRC #fleet + #reviews
│   ├── NOTIFY: ntfy to PO
│   ├── PLANE: update issue state → "In Review"
│   └── META: log metrics
├── EMIT EVENT: fleet.task.completed
├── SET PROGRESS: task_progress = 70 (WORK_COMPLETE)
├── TRAIL: trail.task.completed event
├── CHALLENGE: evaluate if adversarial challenge needed
├── CODEX: trigger codex review if applicable
├── NOTIFY CONTRIBUTORS: alert agents who contributed
└── PARENT CHECK: all children done → parent to review
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| Software Engineer | End of work stage | Implementation complete |
| DevOps | Infrastructure task done | IaC changes complete |
| QA | Test task done | Test implementation complete |
| Architect | Design task done (rare) | Design artifact complete |
| DevSecOps | Security task done | Security fix/audit complete |
| Technical Writer | Doc task done | Documentation complete |

## Relationships

- DEPENDS ON: fleet_read_context (must be called first), fleet_task_accept (plan confirmed)
- GATES: _check_stage_allowed blocks outside work stage → protocol_violation event → doctor → teaching
- FIRES: build_task_complete_chain (event_chain.py) → 6 surfaces
- PRODUCES: LaborStamp (labor_stamp.py), PR (gh_client.py), approval (mc_client.py)
- TRIGGERS: challenge system (challenge_protocol.py) — evaluates if challenge needed
- TRIGGERS: codex review (codex_review.py) — if confidence tier warrants
- NOTIFIES: fleet-ops (approval created), contributors (their input was used), PM (via parent check)
- UPDATES: task_progress = 70, task status = review
- TRAIL: records trail.task.completed event
- CONSUMED BY: fleet-ops (sees pending approval in heartbeat), orchestrator (Step 3 ensures approval exists)

## Stage Enforcement

If called outside WORK stage:
- Returns error: "Methodology violation: fleet_task_complete is only allowed during work stage"
- Emits: fleet.methodology.protocol_violation event
- Doctor detects: detect_protocol_violation() → teaching lesson injected
- Agent must complete current stage protocol first
