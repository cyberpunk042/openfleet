# /diff

**Type:** Claude Code Built-In Command
**Category:** Git & Code
**Available to:** ALL agents (especially Engineer, QA, Fleet-ops)

## What It Actually Does

Opens an interactive diff viewer showing both uncommitted changes AND per-turn diffs (what Claude changed in each response). Two views:
1. **Uncommitted changes** — everything modified since last commit (like `git diff`)
2. **Per-turn diffs** — what changed in each assistant response (tracks Claude's modifications)

This gives agents a clear picture of what they've done before committing. No more blind commits — the agent can review their own work.

## When Fleet Agents Should Use It

**Before fleet_commit:** Engineer should review their changes before committing. /diff shows exactly what's being committed. This catches: accidental scope creep (changed files outside the plan), unintended modifications, debug code left in, forgotten TODO comments.

**Fleet-ops review Step 2 ("Read the FULL PR diff"):** Fleet-ops reviewing a completed task should read the actual diff, not just the summary. While fleet-ops typically reads the PR diff on GitHub, /diff can show local changes during the review process.

**After implementation, before fleet_task_complete:** Final check — does the diff match the plan? Did I change only the target files specified in the plan? Any surprises?

**During debugging:** Check what changed between working and broken state. Per-turn diffs show exactly which change introduced the issue.

## Per-Role Usage

| Role | When | What They Check |
|------|------|----------------|
| Engineer | Before fleet_commit | Verify changes match plan, no scope creep, no debug leftovers |
| QA | During test review | Understand what code changed to inform test strategy |
| Fleet-ops | Review Step 2 | Read actual code changes, not just summary |
| Architect | Design review | Verify implementation matches design specification |

## Anti-Corruption Connection

/diff directly supports three anti-corruption checks:
- **Scope creep:** Did the agent modify files outside the plan's target_files list?
- **Deviation:** Do the changes implement the verbatim requirement or something different?
- **Laziness:** Are the changes substantial enough for the story points?

Fleet-ops should cross-reference the diff against:
1. The verbatim requirement (does the diff implement what was asked?)
2. The accepted plan (does the diff follow the planned steps?)
3. The target files list (does the diff only touch planned files?)

## Relationships

- USED IN: fleet_task_complete (agent should /diff before completing)
- USED IN: fleet-ops review Step 2 ("Read the FULL PR diff")
- CONNECTS TO: fleet_commit (review diff → then commit the reviewed changes)
- CONNECTS TO: /rewind command (if diff reveals a problem, rewind to last checkpoint)
- CONNECTS TO: pr_hygiene.py (PR diff analysis for hygiene checks)
- CONNECTS TO: LaborStamp (lines_added/lines_removed come from diff stats)
- CONNECTS TO: challenge_automated.py (automated challenges analyze the diff for patterns)
- CONNECTS TO: doctor detect_scope_creep (committed files vs plan target_files — diff reveals creep)
- CONNECTS TO: verification-before-completion skill (Superpowers — verify diff before completing)
