# pm-assess

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/pm-assess/SKILL.md
**Invocation:** /pm-assess
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Comprehensive assessment of where the project stands. Scans codebase (what exists, what passes, what's stubbed), reads git log for recent activity, compares against milestones and plan, and produces a structured assessment: accomplished, current state, blocked, risks, next actions.

## Process

1. Read project state (.aicp/state.yaml), architecture doc, README
2. Scan codebase: what modules exist, what tests pass, what's stubbed
3. Read git log for recent activity
4. Compare against milestones and plan
5. Produce assessment:
   - **Accomplished** — what's done and working
   - **Current state** — what's in progress
   - **Blocked** — what's stuck and WHY
   - **Risks** — what could go wrong
   - **Next actions** — specific, prioritized steps
6. Update .aicp/state.yaml with assessment findings

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| PM | ESSENTIAL | Core PM skill — understand project state before planning |
| Fleet-ops | ESSENTIAL | Health assessment for fleet operations |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| analysis | Primary — assess before planning or deciding |
| reasoning | Inform planning decisions with current state |

## Relationships

- PRECEDES: pm-plan (assess state BEFORE creating/updating plan)
- PRECEDES: pm-status-report (assessment feeds the status report)
- READS: .aicp/state.yaml (project state), docs/architecture.md, README.md, git log
- SCANS: codebase (modules, tests, stubs — actual file system examination)
- PRODUCES: structured assessment + updated state.yaml
- CONNECTS TO: fleet_agent_status tool (fleet-level assessment complements project assessment)
- CONNECTS TO: openclaw-fleet-status skill (fleet operational status)
- CONNECTS TO: quality-debt skill (assessment identifies technical debt)
- CONNECTS TO: PM heartbeat (PM assesses during heartbeat to decide what to assign/unblock)
- CONNECTS TO: pm-retrospective (assessment of past work feeds retrospective)
- KEY INSIGHT: assessment must SCAN ACTUAL CODE (grep, glob, read tests) — not rely on documentation or assumptions. The code is the truth.
