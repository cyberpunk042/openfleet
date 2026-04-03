# /simplify

**Type:** Claude Code Built-In Skill Command
**Category:** Bundled Skills (Quality)
**Available to:** Engineer, QA

## What It Actually Does

Reviews changed files and fixes quality issues using 3 parallel agents. Takes an optional focus area. Each agent independently reviews the changes for different quality dimensions, then results are consolidated. Think of it as an automated quality pass — 3 reviewers working in parallel.

## When Fleet Agents Should Use It

**Post-implementation quality pass:** Engineer finishes implementing a feature → /simplify before fleet_task_complete. The 3 agents catch issues the implementing agent missed: code style inconsistencies, unused imports, over-complicated logic, missing error handling.

**After large refactors:** /batch produced many changes across files. /simplify reviews the results for consistency.

**Before PR:** A final quality gate before the work goes to fleet-ops review. Catches issues that would cause rejection.

## Practical Considerations

- 3 parallel agents = 3x token cost for this operation
- Each agent reviews the diff independently (no shared state)
- Results consolidated into a single report
- Uses the /simplify skill's focus to prioritize what to fix
- May produce edits — not read-only (unlike /plan)

## Relationships

- CONNECTS TO: fleet_task_complete (use /simplify BEFORE completing)
- CONNECTS TO: fleet-ops review (catches issues before fleet-ops sees them)
- CONNECTS TO: quality-lint skill (linting is one dimension of simplification)
- CONNECTS TO: quality-audit skill (broader quality assessment)
- CONNECTS TO: verification-before-completion skill (Superpowers — verify before submitting)
- CONNECTS TO: Agent Teams (uses parallel subagents internally)
- CONNECTS TO: /diff (review what changed AFTER simplification)
- CAUTION: 3 agents = 3x token cost. Use selectively, not on every small change.
