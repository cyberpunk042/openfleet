# Task: Architect producing design_input contribution

**Expected:** Architect examining codebase for design. Should show CONTRIBUTION TASK section with target task verbatim, fleet_contribute() reference.

## task-context.md

```
# MODE: task | injection: full
# Your task data is pre-embedded below. fleet_read_context() only if you need fresh data or a different task.

# YOU ARE: architect

# YOUR TASK: Contribute design_input for: fleet health dashboard
- ID: task-con
- Priority: medium
- Type: subtask

# YOUR STAGE: analysis

# READINESS: 50% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> Provide design_input: approach, target files, patterns for the fleet health dashboard

## CONTRIBUTION TASK
**Type:** design_input
**Target task:** task-a1b
**Title:** Add fleet health dashboard to MC frontend
**Verbatim:** Add a health dashboard showing: agent grid (online/idle/sleeping/offline), task pipeline (inbox/progress/review/done counts), storm indicator with severity color, budget gauge with percentage
**Delivery phase:** mvp
**Stage:** work

Call `fleet_contribute()` when your contribution is ready.

## Current Stage: ANALYSIS

You are in the analysis protocol. Examine what exists.

### What you MUST do:
- Read and examine the codebase, existing implementation, architecture
- Produce an analysis document (iterative, work-in-progress)
- Reference SPECIFIC files and line numbers — not vague descriptions
- Present findings to the PO via task comments
- Identify implications for the task

### What you MUST NOT do:
- Do NOT produce solutions (that's reasoning stage)
- Do NOT write implementation code
- Do NOT call fleet_task_complete

### What you CAN produce:
- Analysis documents with file references
- Current state assessments
- Gap analysis
- Dependency mapping
- Impact analysis
- Commits of analysis documents (fleet_commit allowed)

### How to advance:
- Analysis document exists and covers the relevant codebase areas
- PO reviewed the findings
- Implications for the task are clear

Your job is to UNDERSTAND WHAT EXISTS, not to solve the problem.

## INPUTS FROM COLLEAGUES
*(No contributions required.)*

## WHAT TO DO NOW
Examine the codebase. Produce an analysis document with file and line references. Do NOT produce solutions yet.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_artifact_create/update()` → Plane HTML + completeness check
- `fleet_chat()` → board memory + IRC + agent mentions
- Every tool call fires automatic chains — you don't update multiple places manually.

```
