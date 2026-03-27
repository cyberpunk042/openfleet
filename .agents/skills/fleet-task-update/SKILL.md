---
name: fleet-task-update
description: >
  Update a Mission Control task status with proper workflow steps.
  Use when accepting, progressing, completing, or blocking a task.
  Triggers on: "update task", "accept task", "complete task", "task done",
  "mark done", "mark review", "fleet task update".
user-invocable: true
---

# Fleet Task Update

Update Mission Control task status following the fleet workflow.

## When to Use

At every task lifecycle transition: accept → progress → complete/block.

## Task States

```
inbox → in_progress → review → done
                   → blocked (post comment explaining why)
```

## Workflow

### 1. Accept Task (inbox → in_progress)

```bash
curl -s -X PATCH "$BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID" \
  -H "X-Agent-Token: $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "comment": "Starting work: <brief plan>."}'
```

### 2. Post Progress (while in_progress)

```bash
curl -s -X POST "$BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID/comments" \
  -H "X-Agent-Token: $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "Progress: <what was done so far>."}'
```

### 3. Complete Task (in_progress → review or done)

Use `review` if the task requires approval. Use `done` for autonomous completion.

```bash
curl -s -X PATCH "$BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID" \
  -H "X-Agent-Token: $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "review", "comment": "Branch: fleet/<agent>/<task-short>\nCommits: <N>\nFiles: <list>\nSummary: <what was done>."}'
```

### 4. Report Blocker (when blocked)

Don't change status — post a comment explaining the blocker:

```bash
curl -s -X POST "$BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID/comments" \
  -H "X-Agent-Token: $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "**Blocked**: <reason>.\n\nNeeded: <what would unblock>."}'
```

## Prerequisites

- Read TOOLS.md at session start for `AUTH_TOKEN`, `BASE_URL`, `BOARD_ID`
- Task ID comes from the task assignment message
- Always read the task description before starting work

## Rules

- **Always** accept before doing work (inbox → in_progress)
- **Always** post a completion comment with branch/commits/files
- **Never** skip straight to done without posting what was done
- **Never** leave a task in_progress without progress comments
- If blocked, say WHY and what you need — don't silently fail