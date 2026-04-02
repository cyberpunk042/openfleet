# fleet-test

**Type:** Skill (slash command)
**Invocation:** /fleet-test
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-test
**User-invocable:** No (agent-only)

## Purpose

Guides agents in running and analyzing test results as part of a task review. Covers test execution, failure analysis (regression vs pre-existing vs environment), verdict reporting, and creation of fix tasks or infrastructure tasks when issues are found.

## Assigned Roles

- **qa-engineer** -- primary user, runs tests and produces test verdicts for reviews

## Methodology Stages

- **Stage 5 (WORK)** -- QA engineer uses this skill when executing test subtasks created by fleet-review
- **Cross-stage: REVIEW gate** -- test results feed directly into the approval decision by fleet-ops

## What It Produces

- Test execution results with pass/fail counts
- Per-failure analysis: test file, function, line, expected vs actual, regression classification
- Completion summary with verdict (PASS/FAIL) via fleet_task_complete
- Fix subtasks assigned back to the original author for failing tests
- Infrastructure/dependency tasks assigned to devops for missing test infrastructure

## Key Steps

1. **Identify the Target** -- read parent task for PR URL and branch, find the project worktree or clone
2. **Run Tests** -- execute pytest with short traceback and verbose output in the worktree
3. **Analyze Results** -- for each failure determine: what test failed (file, function, line), expected vs actual, whether it is a regression from these changes or pre-existing, whether it is an environment issue (missing dependency)
4. **Report** -- complete review task via fleet_task_complete with summary: "X/Y tests pass. Z failures: [list]. Verdict: PASS/FAIL"
5. **If Tests Fail** -- create fix subtask for the original author via fleet_task_create with parent linkage and high priority
6. **If Missing Infrastructure** -- create blocker task assigned to devops via fleet_task_create for missing dependencies

## Relationships

- USED BY: qa-engineer
- CONNECTS TO: fleet_task_complete (MCP tool), fleet_task_create (MCP tool), fleet-review (skill, produces QA subtasks that fleet-test executes), feature-test (AICP skill, overlapping test execution capability)
- FEEDS: fleet-review decision (test verdict determines approve/reject), fix task pipeline (original author receives regression fix tasks), devops pipeline (infrastructure gaps routed to devops)
- DEPENDS ON: parent task with PR URL and branch, project worktree or clone, pytest and test dependencies installed, fleet-review having created the QA subtask
