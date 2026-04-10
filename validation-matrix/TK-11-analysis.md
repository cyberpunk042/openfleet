# Task: Analysis stage — examine codebase, produce analysis document

**Expected:** Analysis stage. Output should go to wiki/domains/. NO solutions, NO code. Reference specific files and lines.

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

# YOUR STAGE: analysis

# READINESS: 30% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge

## Current Stage: ANALYSIS

You are in the analysis protocol. Examine what exists.

### What you MUST do:
- Read and examine the codebase, existing implementation, architecture
- Produce an analysis document in wiki/domains/ (knowledge layer)
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
### Required Contributions
- **design_input** from architect — *awaiting delivery*
- **qa_test_definition** from qa-engineer — *awaiting delivery*

## WHAT TO DO NOW
Examine the codebase. Produce an analysis document in wiki/domains/ with file and line references. Do NOT produce solutions yet.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_artifact_create/update()` → Plane HTML + completeness check
- `fleet_chat()` → board memory + IRC + agent mentions
- Every tool call fires automatic chains — you don't update multiple places manually.

```
