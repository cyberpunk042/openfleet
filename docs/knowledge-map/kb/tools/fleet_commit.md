# fleet_commit

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** Allowed in stages 2-5 (analysis, investigation, reasoning, work). Blocked in CONVERSATION only.

## Purpose

Commit changes with conventional format and task reference. Agents produce artifacts in all post-conversation stages — analysis documents, investigation reports, design plans, code. Each commit carries a task reference tag for traceability.

## Parameters

- `files` (list[string]) — File paths to stage (relative to worktree)
- `message` (string) — Conventional commit message (e.g., "feat(core): add type hints")

## Chain Operations

```
fleet_commit(files, message)
├── GATE: _check_stage_allowed("fleet_commit")
│   ├── conversation → BLOCKED (protocol violation)
│   ├── analysis, investigation, reasoning, work → ALLOWED
│   └── violation → fleet.methodology.protocol_violation event → doctor
├── GIT ADD: git add {files}
├── GIT COMMIT: git commit -m "{message} [task:{short_id}]"
│   └── Task reference appended automatically
├── TRAIL: trail.commit.created event (SHA, message, files, agent)
├── PLANE SYNC: update Plane issue comment with commit summary
├── EVENT: fleet.task.commit (agent, task_id, commit_sha, message)
└── RETURN: {ok: true, sha: "abc1234", message: "feat(core): ..."}
```

## Conventional Commit Format

```
type(scope): description [task:short_id]

Types: feat, fix, docs, test, refactor, chore, style
Scope: module or area (e.g., core, mcp, cli, gateway)
```

Enforced by: fleet-ops review Step 4 (trail check — conventional commits required).

## Who Uses It

| Role | Stage | What They Commit |
|------|-------|-----------------|
| Engineer | work | Implementation code |
| Engineer | reasoning | Implementation plan |
| Architect | analysis | Analysis document |
| Architect | investigation | Investigation report with options |
| Architect | reasoning | Design plan |
| DevOps | work | IaC files (Docker, CI, scripts) |
| QA | work | Test code |
| Writer | work | Documentation files |
| DevSecOps | work | Security fixes |
| Any agent | analysis+ | Stage-appropriate artifacts |

## Relationships

- DEPENDS ON: fleet_read_context (context must be loaded — task_id required)
- GATES: _check_stage_allowed — conversation stage blocks commit
- PRECEDES: fleet_task_complete (commits accumulate, then complete triggers PR)
- TRAIL: trail.commit.created event per commit
- PLANE: commit summary posted as issue comment
- EVENT: fleet.task.commit emitted
- CONNECTS TO: git worktree (commits go to task-specific branch)
- CONNECTS TO: PR creation (fleet_task_complete pushes all commits)
- CONNECTS TO: labor attribution (commit count in LaborStamp)
- VERIFIED BY: fleet-ops review Step 4 (conventional format, task reference)
- CONNECTS TO: lines_added/removed (git diff stats feed LaborStamp)

## Stage Gating History

Previously (B-01 bug): fleet_commit was WORK_ONLY — blocked in stages 2-4. Agents couldn't commit analysis documents or investigation reports. Fixed: now allowed in stages 2-5 (analysis through work). Conversation remains blocked — agents must understand before producing.
