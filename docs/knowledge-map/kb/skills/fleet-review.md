# fleet-review

**Type:** Skill (slash command)
**Invocation:** /fleet-review
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-review
**User-invocable:** No (agent-only)

## Purpose

Provides a structured review checklist for board leads and QA reviewers evaluating completed tasks. Covers both code tasks (PR verification, conventional commits, test results, secrets scanning) and non-code tasks (requirement coverage, publication-quality markdown, cross-references).

## Assigned Roles

- **fleet-ops** -- primary reviewer role, uses this as the 7-step review checklist

## Methodology Stages

- **Stage 5 (WORK)** -- fleet-ops uses this skill when reviewing completed work from other agents
- **Cross-stage: WORK to REVIEW transition** -- this skill drives the review gate between task completion and approval

## What It Produces

- Approval or rejection decision via fleet_approve
- QA subtasks for code tasks (dispatched to qa-engineer)
- Escalation to human review when needed
- Structured feedback on rejected work (specific what and why)

## Key Steps

1. **Load Context** -- call fleet_read_context(task_id, project) and fleet_agent_status() to understand what was done
2. **Evaluate the Work (Code Tasks)** -- check PR exists, conventional commits, tests included, test pass results, plan quality score, no secrets in diff, no hardcoded paths
3. **Evaluate the Work (Non-Code Tasks)** -- check output addresses requirements, publication quality markdown, cross-references with URLs
4. **Create QA Subtask** -- for code tasks, create a QA subtask assigned to qa-engineer via fleet_task_create with parent linkage
5. **Decide** -- approve via fleet_approve("approved"), reject via fleet_approve("rejected") with specific feedback, or escalate via fleet_escalate for human review

## Relationships

- USED BY: fleet-ops
- CONNECTS TO: fleet_approve (MCP tool), fleet_task_create (MCP tool), fleet_escalate (MCP tool), fleet_read_context (MCP tool), fleet_agent_status (MCP tool)
- FEEDS: approval chain (task state transitions from review to done), QA subtask pipeline (qa-engineer receives test execution subtasks)
- DEPENDS ON: fleet_read_context (must load task context first), completed task with artifacts to review, fleet MCP server running
