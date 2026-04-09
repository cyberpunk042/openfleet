# Task: Conversation stage — clarify requirements, NO code

**Expected:** CLARIFY only. NO code, NO solutions, NO designs. Ask questions.

## task-context.md

```
# MODE: task | injection: full
# Your task data is pre-embedded below. fleet_read_context() only if you need fresh data or a different task.

# YOU ARE: software-engineer

# YOUR TASK: Add fleet health dashboard
- ID: task-a1b
- Priority: high
- Type: story
- Description: Dashboard with agent grid, task pipeline, storm, budget

# YOUR STAGE: conversation

# READINESS: 10% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> We need a dashboard but details unclear

## Current Stage: CONVERSATION

You are in the conversation protocol. Your task is NOT ready for work.

### What you MUST do:
- DISCUSS with the PO to understand the requirements
- Ask SPECIFIC questions about anything unclear
- Identify and STATE what you don't understand
- Propose your understanding and accept correction
- Extract knowledge and meaning from the PO

### What you MUST NOT do:
- Do NOT write code
- Do NOT commit changes
- Do NOT create PRs
- Do NOT produce finished deliverables
- Do NOT call fleet_commit or fleet_task_complete

### What you CAN produce:
- Questions in task comments
- Draft proposals for PO review
- Work-in-progress analysis (clearly marked as draft)

### How to advance:
- The PO confirms your understanding
- The PO increases readiness
- Verbatim requirement is populated and clear
- No open questions remain

Your job is to UNDERSTAND, not to BUILD.

## INPUTS FROM COLLEAGUES
Required contributions (received content appears below if delivered):
- **design_input** from architect
- **qa_test_definition** from qa-engineer

If contributions are NOT shown below → `fleet_request_input()`. Do NOT proceed without required contributions in work stage.

## WHAT TO DO NOW
Ask clarifying questions. Post them to the task comments. Do NOT write code. Your job is to understand, not to build.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_artifact_create/update()` → Plane HTML + completeness check
- `fleet_chat()` → board memory + IRC + agent mentions
- Every tool call fires automatic chains — you don't update multiple places manually.

```

## knowledge-context.md

```
## Stage: CONVERSATION — Resources Available

### Skills:
- /fleet-communicate — which channel for what
- /brainstorming (superpowers) — explore problem space

### Sub-agents:
- **code-explorer** (sonnet) — reference codebase in questions

### MCP: fleet · filesystem

```
