# Workstream 4: Navigability & Traceability

## Goal

Every change is traceable: commit → task → agent → decision. The human leader
can navigate from any artifact to its full context without guessing.

## The Problem

Right now:
- A commit says "add type hints" but doesn't link to the MC task
- A task comment says "done" but doesn't link to the commit or branch
- An MC activity event says "task moved to review" but the agent's reasoning is in
  a separate OpenClaw session file
- Changes in different repos (fleet, NNRT, AICP) have no cross-reference

## What's Needed

### M57: Commit ↔ Task Linking

**Scope:** Every agent commit references the MC task ID. Every task comment references commits.

**Tasks:**
1. Update MC_WORKFLOW.md: commit messages must include `[task:<task-id-short>]`
   ```
   feat(nnrt): add type hints to engine.py [task:ea36a032]
   ```
2. Agent task completion comment must include:
   - Branch name: `fleet/<agent>/<task-short>`
   - Commit SHAs (or count)
   - Changed files summary
3. `integrate-task.sh` already creates branches with task ID — document this pattern
4. Add to STANDARDS.md: "Every commit in a fleet worktree must reference the task ID"

### M58: Smart Links in MC Comments

**Scope:** Task comments include clickable/navigable references.

**Tasks:**
1. When agents post comments, include structured references:
   ```
   Branch: `fleet/software-engineer/ea36a032`
   Worktree: `/path/to/worktree`
   Files changed: `nnrt/core/engine.py`, `nnrt/core/contracts.py`
   ```
2. For GitHub-hosted projects, include direct links:
   ```
   Compare: https://github.com/owner/repo/compare/main...fleet/agent/task
   ```
3. Update MC_WORKFLOW.md with reference format guidelines

### M59: Activity Trail Navigation

**Scope:** From any MC activity event, trace the full context.

**Tasks:**
1. Create `scripts/trace-task.sh <task-id>` that shows:
   - Task title, description, status, assigned agent
   - All task comments (chronological)
   - Related activity events
   - Worktree location and git log
   - Board memory entries referencing this task
2. Add `make trace TASK=<uuid>` target
3. This is the "tell me everything about this task" command

### M60: Cross-Repo Reference Standard

**Scope:** Changes in NNRT reference back to fleet tasks. Fleet tasks reference NNRT commits.

**Tasks:**
1. Agent commits in project worktrees include:
   ```
   fleet(software-engineer): add type hints to engine.py

   Fleet-Task: ea36a032-8cbe-4e60-91c3-e62dc6cc1477
   Fleet-Agent: software-engineer
   Fleet-Board: Fleet Operations
   ```
2. `integrate-task.sh` enforces this format in commit messages
3. When creating PRs (`--pr` flag), PR body includes fleet task reference
4. MC task completion comment includes the PR URL when available

## What We DON'T Need

- A custom traceability database (git + MC API is enough)
- A web UI for tracing (CLI scripts are sufficient for now)
- Bidirectional sync between MC and GitHub (manual integration via scripts)

## Verification

- [ ] Agent commits contain task ID references
- [ ] Task comments contain branch/commit references
- [ ] `make trace TASK=<uuid>` shows full task context
- [ ] PRs created by `integrate-task.sh` reference the fleet task
- [ ] Human can go from any commit → task → agent conversation in <3 steps