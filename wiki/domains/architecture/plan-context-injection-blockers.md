---
title: "Plan: Context Injection Pipeline Blocker Fixes"
type: reference
domain: architecture
status: draft
created: 2026-04-11
updated: 2026-04-11
tags: [plan, context-injection, blockers]
epic: E001
related:
  - analysis-context-injection-blockers.md
  - investigation-context-injection-blockers.md
confidence: medium
sources: []
---

# Plan: Context Injection Pipeline Blocker Fixes

## Summary

Reasoning-stage plan to fix the 4 context-injection-pipeline blockers identified in analysis + investigation: repair model-selection condition evaluator in config/methodology.yaml, align generator fixtures to real provider data shapes, raise tier-rendering coverage, and close the validation matrix gap. Operations-plan in style since the blockers are bugfixes with known root causes.

## Step 1: Fix model selection

### config/methodology.yaml
- Line 382: `"task_type = blocker AND urgency = critical"` → `"task_type = blocker AND priority = urgent"`

### fleet/core/methodology_config.py
- Add `priority: str = ""` to `select_model_for_task()` signature
- Replace the 5 if-blocks (lines 145-167) with a clause evaluator:
  - `_evaluate_condition(condition, fields)` — splits on ` AND `, all clauses must match
  - `_evaluate_clause(clause, fields)` — handles `is set`, `>= N`, `= value`, `in [a, b]`
  - Fields dict maps condition field names to parameter values, including aliases (`task.status` → `task_status`, `agent` → `agent_name`)

### fleet/core/preembed.py
- Line 117: add `priority=task.priority` to the `cfg.select_model_for_task()` call

### fleet/tests/core/test_methodology_models.py (new)
8 tests:
1. contribution_type set → contribution
2. labor_iteration >= 2 → rework
3. spike → research
4. concern → research
5. blocker + urgent → hotfix
6. blocker + high → feature-development (NOT hotfix)
7. fleet-ops + review status → review
8. no match → feature-development

## Step 2: Fix generator fixtures

### scripts/generate-validation-matrix.py
- HB-02 line 176: `contributions_received` → dict keyed by `task_id[:8]`
- HB-05 line 249: add `blocked_details` list
- HB-04 line 219: use IDs that are 8+ chars so `[:8]` truncation is realistic
- TK-01 line 307: add `parent_task_title="Epic: Fleet UI Components"`
- TK-25 line 508: add `parent_task_title="Add fleet health dashboard"`

## Step 3: Add tier rendering tests

### fleet/tests/core/test_tier_renderer.py (append)
12 tests:
1. `must_must_not` trim on analysis protocol — CAN/advance stripped, MUST/MUST NOT kept
2. `must_must_not` trim on work protocol — returned unchanged (no CAN/advance sections)
3. `short_rules` trim on reasoning protocol — 2-3 lines output
4. `short_rules` trim on work protocol — MUST/MUST NOT from `### MUST:` format
5. `is_contribution=True` on reasoning — PO references replaced with contribution language
6. `protocol_adaptations` from contribution model on analysis — model text inserted
7. architect `format_role_data` — design_tasks + high_complexity formatted
8. devsecops `format_role_data` — security_tasks + prs_needing_security_review formatted
9. `counts_plus_top3` on fleet-ops data — count shown, max 3 items
10. `counts_plus_top5` on PM data — count shown, max 5 items
11. `one_line` + `contributions_missing` — short BLOCKED line
12. Source strings used in contribution replacements exist in methodology.yaml

## Step 4: Regenerate and verify

- Run `scripts/generate-validation-matrix.py`
- Run full test suite — 2423 existing + 20 new must pass
- Inspect TK-01 output to confirm parent title, contribution shapes, model name are correct

## Execution order

Step 1 → Step 2 → Step 3 → Step 4.

## Acceptance criteria

- blocker + non-urgent priority does NOT match hotfix model
- All 6 YAML rules evaluate correctly including AND
- Generator fixtures match real provider shapes
- 12 new tier rendering tests pass
- Regenerated scenarios reflect fixed code
- All existing tests still pass

## Relationships

- DERIVED FROM: [[Analysis: Context Injection Pipeline Blockers]]
- DERIVED FROM: [[Investigation: Context Injection Pipeline Blocker Solutions]]
- RELATES TO: [[Context Injection Decision Tree]]
- FEEDS INTO: epic E003 (Brain Evolution) + E014 (Autocomplete Web / Map / Net)
