# /batch

**Type:** Claude Code Built-In Skill Command
**Category:** Bundled Skills (Orchestration)
**Available to:** Architect, Engineer, DevOps

## What It Actually Does

Orchestrates large-scale parallel changes across multiple files, worktrees, and agents. Takes an instruction describing what to change, then spawns parallel subagents — each working in its own git worktree — to execute the changes simultaneously. Can produce multiple PRs from one instruction.

This is the fleet-scale refactoring tool. Instead of making 10 sequential changes, /batch makes them in parallel with isolated worktrees so changes don't conflict.

## When Fleet Agents Should Use It

**Large-scale refactors:** Rename a type used in 15 files. /batch spawns agents to handle groups of files in parallel worktrees.

**Cross-module architecture changes:** Architect restructures 5 modules simultaneously. Each module change is isolated in its own worktree.

**Multi-file infrastructure updates:** DevOps updating Docker configs across 4 projects. Each project handled in parallel.

**Pattern application:** Apply the same pattern (add type hints, add error handling, update imports) across many files.

## How It Works

```
/batch "Add type hints to all public functions in fleet/core/"
├── Agent analyzes scope (which files, what changes)
├── Creates git worktrees for parallel work
├── Spawns subagents (one per worktree or file group)
├── Each subagent:
│   ├── Checks out isolated branch
│   ├── Makes the changes in its worktree
│   ├── Runs tests
│   └── Reports results
├── Collects results from all subagents
├── Creates PRs (one per worktree or one combined)
└── Reports: what changed, what succeeded, what failed
```

## Per-Role Usage

| Role | Scenario | Scale |
|------|----------|-------|
| Architect | Architecture restructuring | Move components, update boundaries across modules |
| Engineer | Feature implementation across files | Large feature touching many modules |
| DevOps | Infrastructure updates | Docker, CI, config changes across projects |
| Engineer | Refactoring campaign | Apply pattern across 20+ files |

## Relationships

- USES: Agent Teams (parallel subagents)
- USES: git worktrees (EnterWorktree/ExitWorktree tools)
- USES: WorktreeCreate/WorktreeRemove hooks
- CONNECTS TO: fleet_commit (each subagent commits in its worktree)
- CONNECTS TO: fleet_task_complete (combined results may produce PR)
- CONNECTS TO: /simplify (quality pass after batch changes)
- CONNECTS TO: using-git-worktrees skill (Superpowers — worktree patterns)
- CONNECTS TO: dispatching-parallel-agents skill (Superpowers — parallel work)
- CONNECTS TO: methodology WORK stage (batch is execution, not planning)
- CAUTION: high token cost (multiple parallel agents). Use for tasks where parallelism saves significant time vs sequential.
- CAUTION: each subagent has its own context — they don't share state. Design changes so each subagent can work independently.
