---
title: "Critical Review Findings — Context Injection Scenarios"
type: reference
domain: architecture
status: processing
confidence: high
created: 2026-04-10
updated: 2026-04-10
tags: [review, findings, scenarios, context-injection, validation, issues]
sources: []
---

# Critical Review Findings — Context Injection Scenarios

## Summary

Catalog of ~25 issues found during the 2026-04-09 line-by-line review of 11 context-injection validation scenarios (TK-01, TK-06, TK-07, TK-34, HB-04, HB-05, and others). Categorizes findings by status: fixed-in-session, pending, deferred. Source material for subsequent plan authoring and anti-pattern extraction. Evidence that the rendering pipeline ADAPTS — whether it adapts CORRECTLY requires per-scenario PO review, which this catalog drives.

## Fixed in Session

| Issue | Scenario | Fix |
|-------|----------|-----|
| Raw Python dicts in role data | HB-04, HB-05 | TierRenderer format_role_data with 5 role formatters |
| Rejection rework invisible | TK-06 | Iteration marker, rejection context, eng_fix_task_response |
| Contribution task can't see target | TK-07 | format_contribution_task_context with target verbatim |
| Role-generic reasoning protocol | TK-34 | Role-specific substitutions in format_stage_protocol |
| Progress-static action directive | TK-01 | format_action_directive adapts to progress % |
| Story points missing | TK-01 | Added to §2 |
| Parent task opaque ID | TK-01 | Resolve title from task list |
| Contribution ordering backwards | TK-01 | Marker-based insertion, ✓/awaiting checklist |
| Protocol too long (25 lines static) | TK-01 | Slimmed to 13 lines, standards in CLAUDE.md |
| fleet_read_context mentioned 3 times | TK-01 | Once in §0, removed from protocol |
| injection:none still full context | TK-05 | Hard branch, 8 lines |
| Contributions at conversation stage | TK-04 | Stage-filtered to reasoning + work |
| HTML marker leak | TK-03,04,07 | Stripped when no contributions |
| "Present to PO" on contribution task | TK-07 | Contribution-aware protocol adaptation |
| Missing contributions = "start working" | TK-02 | BLOCKED directive with specific missing types |
| Rework says "execute plan" + "fix root cause" | TK-06 | Protocol adapts for iteration ≥ 2 |

## Remaining (Not Fixed)

| Issue | Scenario | Status |
|-------|----------|--------|
| No change awareness across cycles | All | Wired (EventStore) but untested with real data |
| No record of previous commits in rework | TK-06 | PR/branch shown, actual commits not loaded |
| Fleet-ops review items missing verbatim+PR | HB-04 | FIXED (providers enriched) |
| PM can't triage from title+priority | HB-05 | FIXED (providers enriched) |
| No sprint context for PM | HB-05 | Sprint name, end date, velocity not in provider |
| No agent workload for PM | HB-05 | Agent → task count not in provider |
| Contribution warning present when all received | TK-01 | Harmless but noisy. Conditional hide TBD. |
| No mapping between plan steps and TC criteria | TK-01 | Design decision needed |
| Contribution content not tier-adapted | TK-30,31 | Orchestrator inserts full for all tiers |

## Structural Issues Discovered

1. **Five files gave contradictory fleet_read_context guidance** — resolved by establishing file ownership
2. **STANDARDS.md and MC_WORKFLOW.md were legacy surfaces** — 19K of duplication removed
3. **Methodology protocols were static per stage, not per model** — resolved by named models
4. **Stage boundaries (tools_blocked) may be too coarse** — needs per-model-per-stage design (open)
5. **Three documentation surfaces were wrong** — corrected to five layers per PO directive

## Relationships

- RELATES TO: [[Validation Issues Catalog — Every Problem Found]]
- RELATES TO: [[15 Anti-Patterns from TierRenderer Session]]
- FEEDS INTO: [[OpenFleet — Identity Profile]]
- FEEDS INTO: [[Session: Context Injection System Evolution]]
