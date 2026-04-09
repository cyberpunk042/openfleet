# Task: Work stage, NO injection (direct CLI)

**Expected:** NO pre-embedded data. Must call fleet_read_context() FIRST.

## task-context.md

```
# MODE: task | injection: none
# NO pre-embedded data. Call fleet_read_context() FIRST to load your task.

# YOU ARE: software-engineer

# YOUR TASK: Add fleet health dashboard
- ID: task-a1b
- Priority: high
- Type: task
- Description: Dashboard with agent grid, task pipeline, storm, budget

# YOUR STAGE: work

# READINESS: 99% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> Add health dashboard

## Current Stage: WORK

You are in the work protocol. Execute the confirmed plan.

### What you MUST do:
- Execute the plan that was confirmed in reasoning stage
- Follow existing conventions: conventional commits, proper testing
- Stay within scope — work from the verbatim requirement and confirmed plan
- Your task data is pre-embedded in your context (verbatim, stage, contributions)
- Call fleet_task_accept with your plan
- Call fleet_commit for each logical change
- Call fleet_task_complete when done
- fleet_read_context only if you need to load a DIFFERENT task's data

### What you MUST NOT do:
- Do NOT deviate from the confirmed plan
- Do NOT add unrequested scope ("while I'm here" changes)
- Do NOT modify files outside the plan's target files
- Do NOT skip tests

### Required tool sequence:
1. fleet_task_accept (confirm plan — your task data is already pre-embedded)
2. fleet_commit (one or more — conventional format)
3. fleet_task_complete (push, PR, review)
Note: fleet_read_context only needed to load another task's context or refresh stale data

### Standards:
- Conventional commit format
- Task ID in commit messages
- Tests for new functionality
- PR with description referencing the task

Your job is to EXECUTE THE PLAN, not to redesign.

## INPUTS FROM COLLEAGUES
Required contributions (received content appears below if delivered):
- **design_input** from architect
- **qa_test_definition** from qa-engineer

If contributions are NOT shown below → `fleet_request_input()`. Do NOT proceed without required contributions in work stage.

## WHAT TO DO NOW
Starting work. `fleet_task_accept()` with your plan first, then implement.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_commit()` → git + event + trail (one logical change per commit)
- `fleet_task_complete()` → push → PR → approval → IRC → Plane → trail → parent eval
- Every tool call fires automatic chains — you don't update multiple places manually.

```
