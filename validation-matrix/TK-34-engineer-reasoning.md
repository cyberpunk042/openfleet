# Task: Engineer reasoning — role-specific protocol

**Expected:** Engineer reasoning should say 'implementation plan'. Compare: architect would say 'design_input'.

## task-context.md

```
# MODE: task | injection: full
# Your task data is pre-embedded below. fleet_read_context() only if you need fresh data or a different task.

# YOU ARE: software-engineer

# YOUR TASK: Add fleet health dashboard
- ID: task-a1b
- Priority: high
- Type: story
- Story Points: 5
- Description: Dashboard with agent grid, task pipeline, storm, budget

# YOUR STAGE: reasoning

# READINESS: 85% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge

## Current Stage: REASONING

You are in the reasoning protocol. Plan your approach.

### What you MUST do:
- Decide on an approach based on requirements + analysis + investigation
- Produce a implementation plan with target files and acceptance criteria mapping
- The plan MUST reference the verbatim requirement explicitly
- Specify target files and components
- Map acceptance criteria to specific implementation steps
- Present the plan to the PO for confirmation

### What you MUST NOT do:
- Do NOT start implementing yet
- Do NOT call fleet_task_complete

### What you CAN produce:
- Implementation plans with target files and acceptance criteria mapping
- Design decisions with justification
- Task breakdown (subtasks if needed via fleet_task_create)
- Acceptance criteria mapping
- Commits of planning documents (fleet_commit allowed)
- Plan submission (fleet_task_accept allowed)

### How to advance:
- Plan exists and references the verbatim requirement
- Plan specifies target files
- PO confirmed the plan
- Readiness reaches 99-100%

Your job is to PLAN, not to execute.

## INPUTS FROM COLLEAGUES
<!-- CONTRIBUTIONS_ABOVE -->
### Required Contributions
- **design_input** from architect — *awaiting delivery*
- **qa_test_definition** from qa-engineer — *awaiting delivery*

## WHAT TO DO NOW
Produce a plan. Reference the verbatim requirement explicitly. Use `fleet_task_accept()` to submit the plan for PO confirmation.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_artifact_create/update()` → Plane HTML + completeness check
- `fleet_chat()` → board memory + IRC + agent mentions
- Every tool call fires automatic chains — you don't update multiple places manually.

```

## knowledge-context.md

```
## Stage: REASONING — Resources Available

### Skills:
- /fleet-implementation-planning — map plan to files and changes
- /writing-plans (superpowers) — detailed implementation roadmap
- /brainstorming (superpowers) — explore approaches

### Sub-agents:
- **code-explorer** (sonnet) — understand codebase before planning

### MCP: fleet · filesystem · github · context7

```
