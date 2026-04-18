---
title: "Analysis: Context Injection Pipeline Blockers"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-11
updated: 2026-04-11
tags: [analysis, context-injection, blockers, model-selection, tier-rendering, data-shapes, validation]
epic: E001
sources: []
---

# Analysis: Context Injection Pipeline Blockers

## Summary

The context injection rendering pipeline has 29 generated scenarios and 0 PO-confirmed leaves. Before leaf-by-leaf validation can begin, the pipeline itself must be trustworthy. This analysis examines what's broken and where.

## Finding 1: Model Selection Condition Evaluator Is Broken

### What exists

`MethodologyConfig.select_model_for_task()` at fleet/core/methodology_config.py:132-167. Takes 5 parameters: `contribution_type`, `labor_iteration`, `task_type`, `agent_name`, `task_status`. Evaluates 6 rules from config/methodology.yaml model_selection section (lines 375-388). Each rule has a condition string and a model name. First match wins.

The parser is 5 independent if-blocks, each handling one condition pattern via string splitting.

### What's broken

**Rule 4** (methodology.yaml:367): `"task_type = blocker AND urgency = critical"` → hotfix

- `urgency` does not exist in `TaskCustomFields` (models.py:98-148). No field, no enum, nothing.
- `Task.priority` exists (models.py:159) as a string ("high", "medium", "low", "critical") — but it is never passed to `select_model_for_task`.
- The parser at methodology_config.py:157-160 does `cond.split("=")[1].strip().split(" ")[0]` which extracts `"blocker"` and discards everything after the first space — the entire AND clause is dead code.
- **Impact**: Every blocker task matches hotfix → stages=[work], completion_tool=fleet_task_complete, gates=po. Non-critical blockers that should go through conversation → reasoning → work instead skip straight to work.

**Rule 5** (methodology.yaml:369): `"agent = fleet-ops AND task.status = review"` → review

- Parser at methodology_config.py:161-164: checks `"review" in cond` which matches the substring "review" in the condition string itself, not the `task_status` parameter value.
- Works by coincidence. The check `task_status == "review"` on the same line is what actually validates the field.
- Fragile but currently correct.

**The parser has no AND support.** There is no clause splitting, no field-value evaluation, no shared logic. Each if-block pattern-matches one condition format.

### Call site

preembed.py:108-119 calls `cfg.select_model_for_task()` passing:
- `contribution_type=cf.contribution_type or ""`
- `labor_iteration=cf.labor_iteration or 1`
- `task_type=cf.task_type or ""`
- `agent_name=agent_name`
- `task_status=task.status.value if task.status else ""`

Does NOT pass `task.priority`. No way for the evaluator to check priority even if it could parse AND.

### Test coverage

Zero. The 18 tests in fleet/tests/core/test_model_selection.py test `fleet.core.model_selection.select_model_for_task` — a completely different function that selects opus vs sonnet. The methodology model selector has no tests at all.

---

## Finding 2: Generator Fixtures Don't Match Real Provider Data Shapes

### What exists

scripts/generate-validation-matrix.py creates hardcoded dicts for role_data and passes them to `build_heartbeat_preembed`. In production, fleet/cli/orchestrator.py:524-537 calls real providers from fleet/core/role_providers.py which return specific shapes.

### Mismatches

**contributions_received (structural)**
- Generator HB-02 (generate-validation-matrix.py:176-179): flat list `[{"type": ..., "from": ..., "status": ...}]`
- Real worker_provider (role_providers.py:184-197): dict keyed by task_id[:8] `{"task-a1b": [{"type": ..., "from": ..., "status": ...}]}`
- tier_renderer.py:283 has `isinstance(received, dict)` check to handle both — but the generator exercises only the list branch, leaving the dict branch (production path) untested in scenarios.

**blocked_details (missing field)**
- Generator HB-05 (generate-validation-matrix.py:237-254): no `blocked_details` key.
- Real project_manager_provider (role_providers.py:86-93): always returns `blocked_details` list.
- tier_renderer.py:215-218 renders it when present — never exercised by generator.

**ID truncation (minor drift)**
- Generator HB-04 (generate-validation-matrix.py:219): `"task-abc1"` (9 chars).
- Real fleet_ops_provider (role_providers.py:42): `t.id[:8]` (8 chars).

**parent_task_title (missing parameter)**
- Generator: never passes `parent_task_title` to `build_task_preembed`.
- Orchestrator (orchestrator.py:652-659): resolves parent title from task list, passes it.
- TK-01 sets `parent_task="epic-fleet-ui-001"` but rendered output shows raw ID fragment `epic-fle` instead of the epic title.

---

## Finding 3: Tier Rendering Has 8 Untested Code Paths

### What exists

fleet/tests/core/test_tier_renderer.py: 29 tests covering profile loading (6), role data (6), rejection context (3), action directive (7), contribution context (3), stage protocol (4).

### What's not covered

1. **`_trim_protocol_for_tier` with `must_must_not` depth** (tier_renderer.py:778-793) — capable and flagship_local tiers. Strips "What you CAN" and "How to advance" sections. Never tested.

2. **`_trim_protocol_for_tier` with `short_rules` depth** (tier_renderer.py:749-776) — lightweight tier. Condenses to MUST/MUST NOT lines. Never tested. Parser logic traced as correct against real protocol text but no regression protection.

3. **`format_stage_protocol` with `is_contribution=True`** (tier_renderer.py:619-635) — 4 `str.replace()` calls adapting protocol for contribution lifecycle. If source strings in methodology.yaml change, replacements silently stop matching. Never tested.

4. **`format_stage_protocol` Priority 1 block** (tier_renderer.py:593-613) — config-driven protocol adaptations from `model.protocol_adaptations`. Wrapped in bare `except Exception: pass`. Any bug is invisible. Never tested.

5. **`format_role_data` for architect** (tier_renderer.py:225-243) — renders `design_tasks` and `high_complexity` lists. Never tested.

6. **`format_role_data` for devsecops-expert** (tier_renderer.py:245-264) — renders `security_tasks` and `prs_needing_security_review`. Never tested.

7. **`format_role_data` at capable tier** (`counts_plus_top3` depth) and flagship (`counts_plus_top5`) — the item_limit logic at tier_renderer.py:147-154 is exercised only at `counts_only` (lightweight) and `full_formatted` (expert). Middle depths never tested.

8. **`format_action_directive` `one_line` + `contributions_missing`** — tier_renderer.py:394 returns a short BLOCKED line. Never tested.

---

## Finding 4: Validation Matrix Coverage Gap

### What exists

29 scenarios in validation-matrix/. 91+ leaves mapped in wiki/domains/architecture/context-injection-tree.md.

### What's missing

The generator covers:
- 9 heartbeat scenarios (HB-01 through HB-06, HB-20)
- 18 task scenarios (TK-01 through TK-42, non-contiguous)
- 2 fleet-level scenarios (FL-01, FL-03)

Not covered at all:
- Any stage × capable tier (only TK-30 is work × capable)
- Any stage × flagship_local tier (zero scenarios)
- Analysis/investigation/reasoning × lightweight tier
- Heartbeat × capable tier
- Multiple contribution types partially received
- Any documentation model scenario
- Any review model scenario (fleet-ops reviewing via fleet_approve)
- Crisis/planning phase × task dispatch
- Blocked task × contribution missing (compound state)
- Progress milestones other than 0%, 40%, 60%, 70% (no 80% challenged, no 90% reviewed)

---

## Relationships

- FEEDS INTO: [[Investigation: Context Injection Pipeline Blocker Solutions]]
- FEEDS INTO: [[Plan: Context Injection Pipeline Blocker Fixes]]
- RELATES TO: [[Context Injection Decision Tree]] (the 91+ leaves that need validation)
- RELATES TO: [[Critical Review Findings — Context Injection Scenarios]] (earlier findings from scenario review)
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Methodology Models Rationale]]
