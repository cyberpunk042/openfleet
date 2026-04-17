---
title: "Validation Issues Catalog — Every Problem Found"
type: reference
domain: architecture
status: active
created: 2026-04-09
updated: 2026-04-09
tags: [validation, issues, heartbeat, task, preembed, autocomplete, quality]
sources:
  - id: source
    type: documentation
    file: validation-matrix/*.md
  - id: po-review-session-2026-04-09
    type: documentation
    file: PO review session 2026-04-09
confidence: medium
---

# Validation Issues Catalog

Problems found by line-by-line inspection of 15 validation scenarios.

## Category A: Structural — Heartbeat Preembed

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| A1 | HEARTBEAT.md is one static file for all states — idle agent gets task-work instructions, working agent gets idle instructions | CRITICAL | agents/_template/heartbeats/*.md |
| A2 | fleet-context.md sections appear/disappear based on data — HEARTBEAT.md references sections that may not exist (PO DIRECTIVES, MESSAGES) | CRITICAL | fleet/core/preembed.py build_heartbeat_preembed() |
| A3 | Role data is raw Python dict dump — `{'id': 'appr-001', 'task_id': ...}` instead of human-readable format | CRITICAL | fleet/core/preembed.py role_data rendering |
| A4 | PM's unassigned tasks are in ROLE DATA but HEARTBEAT.md says "Read your ASSIGNED TASKS section" — wrong location reference | HIGH | agents/_template/heartbeats/project-manager.md |
| A5 | No EVENTS section in any heartbeat — PO vision includes "events since last heartbeat" | MEDIUM | fleet/core/preembed.py |
| A6 | No CONTEXT AWARENESS section — 7%/5% context rules and rate limit not visible to agent | MEDIUM | fleet/core/preembed.py |
| A7 | Standing orders shown for every state including when irrelevant (idle agent with no tasks sees work-stage standing order) | LOW | fleet/core/preembed.py |
| A8 | Heartbeat preembed has no consistent section order — sections appear in arbitrary order based on data presence | HIGH | fleet/core/preembed.py |

## Category B: Structural — Task Preembed

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| B1 | Contribution content is "check task comments" placeholder, not actual pre-embedded content | CRITICAL | fleet/core/preembed.py build_task_preembed() |
| B2 | Heartbeat mode for agent WITH in-progress task shows no task-context.md — the autocomplete chain is absent | CRITICAL | validation-matrix/HB-02 |
| B3 | No artifact state in any context — task at 40% progress should show what's done, what's missing, completeness | HIGH | fleet/core/preembed.py |
| B4 | No knowledge-context.md (Navigator output) shown in any scenario — skills, sub-agents, MCP servers invisible | HIGH | validation matrix generation |
| B5 | Verbatim may be truncated in heartbeat view — full verbatim only in task-context.md | MEDIUM | fleet/core/preembed.py format_task_full() |

## Category C: Runtime / Deployment

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| C1 | Runtime HEARTBEAT.md files are OLD versions — template rewrites not pushed to agents/{name}/ | CRITICAL | agents/*/HEARTBEAT.md vs agents/_template/heartbeats/*.md |
| C2 | Runtime CLAUDE.md may also be stale — template changes not propagated | HIGH | agents/*/CLAUDE.md |
| C3 | IDENTITY.md and SOUL.md templates have {{placeholders}} but runtime files have resolved values — validation script was reading wrong files | FIXED | scripts/generate-validation-matrix.py |
| C4 | push-agent-framework.sh hasn't been run to deploy new templates | HIGH | scripts/push-agent-framework.sh |

## Category D: HEARTBEAT.md Content

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| D1 | PM HEARTBEAT.md (runtime) is OLD — 12 sections (0-11 + Rules), not the rewritten 5-section priority format | CRITICAL | agents/project-manager/HEARTBEAT.md |
| D2 | Fleet-ops HEARTBEAT.md (runtime) is OLD — different structure than rewritten template | CRITICAL | agents/fleet-ops/HEARTBEAT.md |
| D3 | PM HEARTBEAT.md §2 says "Look for tasks with Agent: UNASSIGNED" in ASSIGNED TASKS — but unassigned are in ROLE DATA | HIGH | agents/_template/heartbeats/project-manager.md (even new version may have this) |
| D4 | PM HEARTBEAT.md references "devops-expert" — wrong agent name, should be "devops" | MEDIUM | OLD runtime file |
| D5 | Engineer HEARTBEAT.md preamble says "assigned tasks with stages, readiness, verbatim requirements, artifact state" — misleading when idle with no tasks | MEDIUM | agents/_template/heartbeats/software-engineer.md |
| D6 | HEARTBEAT.md doesn't tell the agent HOW to skip irrelevant sections — no "if None, proceed to next priority" guidance | HIGH | all heartbeat templates |

## Category E: CLAUDE.md / Methodology

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| E1 | CLAUDE.md at position 3 said "pre-embedded above" — data comes AFTER at positions 6-7 | FIXED | agents/_template/CLAUDE.md/*.md → changed to "in your context" |
| E2 | methodology.yaml work protocol said "Call fleet_read_context first" — wrong for full injection | FIXED | config/methodology.yaml |
| E3 | CLAUDE.md mode awareness block references injection level but the actual task data section order isn't guaranteed from CLAUDE.md's perspective | MEDIUM | agents/_template/CLAUDE.md/*.md |

## Category F: Data Formatting

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| F1 | Role data rendered as raw Python dicts — ALL roles affected | CRITICAL | fleet/core/preembed.py build_heartbeat_preembed() role_data section |
| F2 | Contribution status in role data is nested dict — `{'task-a1b': [{'type': 'design_input'...}]}` | CRITICAL | fleet/core/role_providers.py worker_provider() |
| F3 | Approval details are raw dicts — fleet-ops needs formatted review items | HIGH | fleet/core/role_providers.py fleet_ops_provider() |
| F4 | Unassigned task details are raw dicts — PM needs formatted triage items | HIGH | fleet/core/role_providers.py project_manager_provider() |

## Category G: Missing Context

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| G1 | Fleet-ops review queue shows title + agent but NOT verbatim requirement, acceptance criteria, PR URL, trail — the actual data needed for review | CRITICAL | fleet/core/role_providers.py fleet_ops_provider() |
| G2 | No Plane connection status visible — HEARTBEAT.md §9 (PM) references Plane but no indication if Plane is connected | MEDIUM | fleet/core/preembed.py |
| G3 | No sprint name/velocity/timeline in PM data — just "12/25 done (48%)" | MEDIUM | fleet/core/role_providers.py project_manager_provider() |
| G4 | No reference to available group calls in context — agent doesn't know ops_real_review(), pm_sprint_standup() etc. exist unless they read TOOLS.md | MEDIUM | fleet/core/preembed.py |

## Summary

| Category | Critical | High | Medium | Low | Fixed |
|----------|---------|------|--------|-----|-------|
| A: Heartbeat preembed structure | 2 | 2 | 2 | 1 | 0 |
| B: Task preembed structure | 2 | 2 | 1 | 0 | 0 |
| C: Runtime/deployment | 1 | 2 | 0 | 0 | 1 |
| D: HEARTBEAT.md content | 2 | 2 | 2 | 0 | 0 |
| E: CLAUDE.md/methodology | 0 | 0 | 1 | 0 | 2 |
| F: Data formatting | 2 | 2 | 0 | 0 | 0 |
| G: Missing context | 1 | 0 | 3 | 0 | 0 |
| **Total** | **10** | **10** | **9** | **1** | **3** |

**10 critical, 10 high, 9 medium, 1 low. 3 already fixed.**

## Category H: Task Preembed Content (from TK scenarios)

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| H1 | Task data is flat bullets — missing story points, parent task, Plane link | MEDIUM | fleet/core/preembed.py format_task_full() |
| H2 | Progress % shown but no artifact state — "40% done" with no detail of what's done/remaining | HIGH | fleet/core/preembed.py build_task_preembed() |
| H3 | "Call fleet_task_accept with your plan" shown even at progress 40% — should only appear at progress 0% (start of work) | HIGH | config/methodology.yaml work protocol |
| H4 | Contribution requirements checklist appears AFTER actual contribution content — confusing order | MEDIUM | fleet/core/preembed.py §7 |
| H5 | No confirmed plan visible in context — agent told to "Execute the confirmed plan" but plan content absent | CRITICAL | fleet/core/preembed.py |
| H6 | No previous stage findings — task at reasoning (85%) shows no analysis/investigation output | HIGH | fleet/core/preembed.py |
| H7 | Contribution requirements shown at conversation stage (10% readiness) — premature, contributions created at reasoning | MEDIUM | fleet/core/preembed.py §7 |
| H8 | WHAT HAPPENS section for conversation shows fleet_artifact_create — conversation should be fleet_chat only | MEDIUM | fleet/core/preembed.py |
| H9 | injection:none mode still produces full task context — contradicts "NO pre-embedded data" header | HIGH | fleet/core/preembed.py |
| H10 | methodology.yaml work protocol doesn't adapt to injection level — says "pre-embedded" even in injection:none | HIGH | config/methodology.yaml |
| H11 | Rejection rework (iteration 2+) shows NO iteration number, NO rejection feedback, NO eng_fix_task_response reference | CRITICAL | fleet/core/preembed.py |
| H12 | Rejection rework context is IDENTICAL to first attempt — autocomplete chain doesn't differentiate | CRITICAL | fleet/core/preembed.py |

## Updated Summary

| Category | Critical | High | Medium | Low | Fixed |
|----------|---------|------|--------|-----|-------|
| A: Heartbeat preembed structure | 2 | 2 | 2 | 1 | 0 |
| B: Task preembed structure | 2 | 2 | 1 | 0 | 0 |
| C: Runtime/deployment | 1 | 2 | 0 | 0 | 1 |
| D: HEARTBEAT.md content | 2 | 2 | 2 | 0 | 0 |
| E: CLAUDE.md/methodology | 0 | 0 | 1 | 0 | 2 |
| F: Data formatting | 2 | 2 | 0 | 0 | 0 |
| G: Missing context | 1 | 0 | 3 | 0 | 0 |
| H: Task preembed content | 3 | 4 | 4 | 0 | 0 |
| **Total** | **13** | **14** | **13** | **1** | **3** |

**13 critical, 14 high, 13 medium, 1 low. 3 fixed. 41 open issues.**

## Category I: Contribution Tasks (TK-07, TK-08)

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| I1 | Contribution tasks don't show TARGET task's verbatim/context — contributor can't see what they're contributing FOR | CRITICAL | fleet/core/preembed.py |
| I2 | contribution_type and contribution_target fields not rendered | HIGH | fleet/core/preembed.py format_task_full() |
| I3 | fleet_contribute() not mentioned in WHAT TO DO NOW or WHAT HAPPENS for contribution tasks | HIGH | fleet/core/preembed.py §9, §10 |
| I4 | Role-specific group calls (arch_design_contribution, qa_test_predefinition) not referenced | MEDIUM | fleet/core/preembed.py |
| I5 | Methodology reasoning protocol is engineer-generic ("implementation plan") — QA should see "test criteria", architect should see "design input" | CRITICAL | config/methodology.yaml reasoning protocol |
| I6 | Target task's delivery phase not visible to contributor — can't produce phase-appropriate output | HIGH | fleet/core/preembed.py |

## Category J: State-Specific Context Failures

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| J1 | Work protocol doesn't adapt to progress — same "Execute plan" at 0%, 40%, 70% | HIGH | config/methodology.yaml + fleet/core/preembed.py §9 |
| J2 | Plane connection status invisible — task has plane_issue_id but agent doesn't know | MEDIUM | fleet/core/preembed.py format_task_full() |
| J3 | Verbatim appears truncated in some scenarios — different lengths for same task | MEDIUM | validation scenario data (may be test fixture issue) |

## FINAL SUMMARY

| Category | Critical | High | Medium | Low | Fixed |
|----------|---------|------|--------|-----|-------|
| A: Heartbeat preembed structure | 2 | 2 | 2 | 1 | 0 |
| B: Task preembed structure | 2 | 2 | 1 | 0 | 0 |
| C: Runtime/deployment | 1 | 2 | 0 | 0 | 1 |
| D: HEARTBEAT.md content | 2 | 2 | 2 | 0 | 0 |
| E: CLAUDE.md/methodology | 0 | 0 | 1 | 0 | 2 |
| F: Data formatting | 2 | 2 | 0 | 0 | 0 |
| G: Missing context | 1 | 0 | 3 | 0 | 0 |
| H: Task preembed content | 3 | 4 | 4 | 0 | 0 |
| I: Contribution tasks | 2 | 3 | 1 | 0 | 0 |
| J: State-specific failures | 0 | 1 | 2 | 0 | 0 |
| **TOTAL** | **15** | **18** | **16** | **1** | **3** |

**50 issues total. 15 critical, 18 high, 16 medium, 1 low. 3 fixed.**

The critical issues cluster around:
1. Heartbeat preembed is structurally broken (A1, A2)
2. Role data formatting is unusable (F1, F2)
3. Contribution tasks can't see what they're contributing FOR (I1, I5)
4. Rejection rework is invisible to the agent (H11, H12)
5. Confirmed plan and previous stage findings absent from context (H5, H6)
6. methodology.yaml protocols are role-generic when they should be role-specific (I5)

## Relationships

- RELATES TO: [[Critical Review Findings — Context Injection Scenarios]]
- RELATES TO: [[15 Anti-Patterns from TierRenderer Session]]
- FEEDS INTO: [[Plan: Context Injection Pipeline Blocker Fixes]]
- FEEDS INTO: [[Plan: TK-01 Golden Path — 200+ Lines of High-Value Output]]
