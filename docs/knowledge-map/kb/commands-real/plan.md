# /plan

**Type:** Claude Code Built-In Command
**Category:** Git & Code
**Available to:** ALL agents (especially Architect, PM, Engineer)

## What It Actually Does

Enters plan mode — a read-only exploration state where Claude analyzes code, reads files, searches patterns, but does NOT make modifications. Optionally takes a task description to focus the planning. Claude enters `plan` permission mode where writes are blocked. This is structurally enforced — not a suggestion, a gate.

In plan mode, Claude can: Read files, Glob for patterns, Grep for content, use WebSearch/WebFetch, run read-only Bash commands, think deeply about architecture. Claude cannot: Write files, Edit files, run destructive Bash commands.

Plan mode produces a PLAN — a structured approach to the task. The plan IS the deliverable in REASONING stage.

## When Fleet Agents Should Use It

**REASONING stage (primary):** The methodology says "plan your approach." /plan is HOW you do that. Enter plan mode → explore the codebase → understand the architecture → produce a plan that references specific files and functions → exit plan mode → fleet_task_accept with the plan.

**Before complex implementation:** Engineer about to implement a feature with 5+ files affected. Don't start coding — /plan first. Read the target files, understand patterns, map dependencies. Then exit plan mode and implement with confidence.

**Architecture design sessions:** Architect exploring multiple design options. /plan lets you read everything without accidentally writing code. Produce the design document from a complete understanding.

**Investigation stage:** Exploring options before deciding. /plan provides read-only safety while researching.

**Sprint planning (PM):** PM exploring the backlog, reading task states, understanding what's available. /plan prevents accidental modifications while surveying.

## Per-Role Usage Patterns

| Role | When | What They Plan |
|------|------|---------------|
| Architect | REASONING | System design: read codebase → identify patterns → propose architecture → multiple options |
| Engineer | REASONING | Implementation: read target files → understand existing patterns → map changes → plan steps |
| PM | REASONING | Sprint: read backlog → assess capacities → plan assignments → map dependencies |
| QA | REASONING | Test strategy: read implementation → identify test scenarios → plan test approach |
| DevSecOps | INVESTIGATION | Security: read code for vulnerabilities → assess attack surface → plan security review |

## The Plan → Accept → Work Flow

```
1. Agent enters REASONING stage (readiness ~80%)
2. /plan [task description]
   └── Claude enters read-only mode
   └── Agent explores codebase, reads files, searches patterns
   └── Agent formulates approach
3. Agent exits plan mode
4. fleet_task_accept(plan) — submits the plan
   └── plan_quality.py assesses: steps(40pts), verification(30pts), risks(20pts), length(10pts)
   └── Plan must reference verbatim requirement
   └── Plan must specify target files
5. PO reviews plan → gate at readiness 90%
6. PO approves → readiness 99 → WORK stage
7. Agent implements THE PLAN (no deviation)
```

## Relationships

- MAPS TO: methodology REASONING stage ("Your job is to PLAN, not to execute")
- CONNECTS TO: fleet_task_accept (plan submitted after /plan exploration)
- CONNECTS TO: writing-plans skill (Superpowers — "plans clear enough for enthusiastic junior dev")
- CONNECTS TO: fleet_gate_request (plan reviewed at readiness 90% gate)
- CONNECTS TO: plan_quality.py (plan assessed for concrete steps, verification, risks)
- CONNECTS TO: standards.py — plan artifact type requires: title, requirement_reference, approach, target_files, steps, acceptance_criteria_mapping
- CONNECTS TO: /branch command (branch to explore alternative plan without losing current)
- CONNECTS TO: /context command (check context before heavy planning reads)
- CONNECTS TO: architecture-propose skill (produce architecture during plan mode)
- ENFORCES: stage_context.py "Do NOT start implementing yet. Do NOT commit code." — plan mode structurally prevents this
- ANTI-CORRUPTION: prevents the "code first, plan later" disease
