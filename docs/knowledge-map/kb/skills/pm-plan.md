# pm-plan

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/pm-plan/SKILL.md
**Invocation:** /pm-plan
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Create or update a project plan by breaking architecture into 5-10 buildable milestones with deliverables, dependencies, effort estimates, and critical path identification. Each milestone must produce something testable. No milestone should take more than 2-3 sessions.

## Process

1. Read idea doc, architecture doc, current project state
2. Break architecture into 5-10 buildable milestones
3. For each milestone: name, description, deliverables, dependencies, estimated effort
4. Identify critical path (which milestones block others)
5. Write plan to .aicp/state.yaml milestones section
6. Present to user for review

## Rules

- Each milestone must produce something TESTABLE (not "set up infrastructure" — "API endpoint returns health check response")
- Dependencies must be EXPLICIT (milestone B depends on milestone A completing)
- No milestone should take more than 2-3 sessions (break down further if larger)

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| PM | ESSENTIAL | Core PM skill — creating project plans |
| Architect | RECOMMENDED | Architecture knowledge informs milestone breakdown |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| reasoning | Plan the project approach (primary) |
| work | Create/update the plan document |

## Relationships

- READS: docs/idea.md (requirements), docs/architecture.md (structure), .aicp/state.yaml (current state)
- PRODUCES: project plan with milestones in .aicp/state.yaml
- CONNECTS TO: fleet-plan skill (fleet-specific variant that creates sprint tasks on OCMC with dependencies)
- CONNECTS TO: fleet-sprint skill (sprint lifecycle uses the plan's milestones)
- CONNECTS TO: fleet_task_create tool (PM creates OCMC tasks from plan milestones)
- CONNECTS TO: fleet_gate_request (plan reviewed at readiness 90% gate)
- CONNECTS TO: pm-assess (assess current state BEFORE planning)
- CONNECTS TO: pm-status-report (report progress AGAINST the plan)
- CONNECTS TO: /plan command (Claude Code plan mode for read-only exploration during planning)
- CONNECTS TO: writing-plans skill (Superpowers — plans broken into 2-5 minute tasks with exact file paths)
- CONNECTS TO: methodology REASONING stage (planning IS the reasoning stage)
- KEY DIFFERENCE FROM fleet-plan: pm-plan creates a project-level plan; fleet-plan creates sprint-level tasks on OCMC with agent assignments, story points, and dependency chains
