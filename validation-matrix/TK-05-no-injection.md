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

Execute the confirmed plan. Stay in scope.

### MUST:
- Execute the plan confirmed in reasoning stage
- Stay within scope — verbatim requirement and confirmed plan only
- Consume all contributions before implementing
- Commit each logical change via fleet_commit
- Complete via fleet_task_complete when done

### MUST NOT:
- Do NOT deviate from the confirmed plan
- Do NOT add unrequested scope
- Do NOT modify files outside the plan's target
- Do NOT skip tests

## INPUTS FROM COLLEAGUES
### Required Contributions
- **design_input** from architect — *awaiting delivery*
- **qa_test_definition** from qa-engineer — *awaiting delivery*

If any contribution above shows *awaiting delivery* → `fleet_request_input()`. Do NOT proceed without required contributions in work stage.

## WHAT TO DO NOW
Starting work. `fleet_task_accept()` with your plan first, then implement.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_commit()` → git + event + trail (one logical change per commit)
- `fleet_task_complete()` → push → PR → approval → IRC → Plane → trail → parent eval
- Every tool call fires automatic chains — you don't update multiple places manually.

```
