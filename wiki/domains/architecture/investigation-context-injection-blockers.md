---
title: "Investigation: Context Injection Pipeline Blocker Solutions"
type: reference
domain: architecture
status: draft
confidence: medium
created: 2026-04-11
updated: 2026-04-11
tags: [investigation, context-injection, blockers, model-selection, tier-rendering, data-shapes, options]
epic: E001
related:
  - analysis-context-injection-blockers.md
sources: []
---

# Investigation: Context Injection Pipeline Blocker Solutions

## Summary

Investigation stage output for the context-injection-pipeline track: for each blocker identified in the analysis phase (model selection evaluator bug, generator fixtures, tier rendering coverage, validation matrix gap), enumerates solution options with tradeoffs and cites evidence. Reasoning-stage input, not a plan.

## Finding 1: Model Selection Condition Evaluator

### Additional discovery during investigation

`Task.priority` is a free string (models.py:159, default "medium"). The task_scoring system (task_scoring.py:24-29) uses values: "urgent", "high", "medium", "low". The methodology.yaml rule says `urgency = critical` — **two mismatches**: wrong field name (`urgency` vs `priority`) AND wrong value (`critical` vs `urgent`).

Events use a different priority space: "urgent", "important", "info" (event_router.py:196). AlertSeverity enum (models.py:27-33) uses "critical", "high", "medium", "low". So "critical" is an alert severity, not a task priority.

The intent of Rule 4 is: "when a blocker is so urgent it needs immediate fixing, skip stages." The existing data that captures this: `Task.priority == "urgent"` (from task_scoring) or the combination of `task_type == "blocker"` + `priority == "urgent"`.

### Option A: Proper clause evaluator with priority passthrough

Replace the 5 if-blocks with a generic evaluator that splits on AND and evaluates each clause against a fields dict. Change YAML from `urgency = critical` to `priority = urgent`. Add `priority` parameter to `select_model_for_task()`. Add it to the call site in preembed.py.

Clause types to support:
- `field is set` → truthy check
- `field >= N` → numeric comparison
- `field = value` → equality
- `field in [a, b, c]` → membership
- `clause AND clause` → all must match

**Tradeoff:** Correct and extensible. ~30 lines for the evaluator. The evaluator is isolated and testable. YAML conditions stay human-readable strings.

### Option B: Structured YAML conditions

Replace string conditions with structured YAML:
```yaml
model_selection:
  - conditions:
      - field: task_type
        op: eq
        value: blocker
      - field: priority
        op: eq
        value: urgent
    model: hotfix
```

**Tradeoff:** No parser needed — YAML does the parsing. But changes the config format the PO designed. More verbose YAML. Harder to read at a glance.

### Option C: Simplify — no compound conditions

Remove AND support entirely. Each rule is one field check. Rule 4 becomes just `task_type = blocker` → hotfix (all blockers, regardless of priority).

**Tradeoff:** Simplest code. Loses the ability to distinguish urgent blockers from non-urgent ones. Every blocker would skip all stages — which is already what's happening due to the bug, but would now be intentional.

### Prior art in codebase

No existing condition evaluator in the fleet codebase. The closest pattern is `task_scoring.py` which uses a dict lookup (`PRIORITY_SCORES.get(task.priority, 50)`) — simple, no parsing.

---

## Finding 2: Generator Data Shape Mismatches

### Option A: Fix fixtures to match real providers

Go through each fixture in generate-validation-matrix.py and align it to the real provider return shape from role_providers.py.

Specific changes:
- HB-02 `contributions_received`: change from flat list to dict keyed by task_id[:8]
- HB-05: add `blocked_details` list matching project_manager_provider shape
- HB-04: truncate fixture IDs to 8 chars
- TK-01, TK-25: add `parent_task_title` parameter

**Tradeoff:** Straightforward. One-time fix. But the generator and orchestrator remain two independent paths — they can drift again.

### Option B: Shared fixture factories

Create a `fleet/tests/fixtures.py` module with factory functions that mirror real provider output shapes. Both the generator and tests use these factories.

**Tradeoff:** Prevents future drift. More setup. Factories need to stay in sync with providers — but at least there's one place to update instead of N.

### Option C: Generator calls real providers with mock MC

Instead of hardcoded dicts, the generator instantiates real Task objects and calls real provider functions with a mock MC client. The output is guaranteed to match production shape.

**Tradeoff:** Strongest guarantee. But providers are async and need an MC client mock. More complex setup. The generator becomes an integration test rather than a pure rendering exercise.

---

## Finding 3: Untested Tier Rendering Paths

### Test strategy investigation

Full combinatorial: 4 tiers × 5 stages × 10 roles × 3 task natures = 600 combinations. Not feasible. Need to identify the right cross-sections.

### Which cross-sections give maximum coverage?

**`_trim_protocol_for_tier`** — 3 depths (full, must_must_not, short_rules) × 2 protocol formats (work stage uses `### MUST:` headers, other stages use `### What you MUST do:` headers). That's 6 paths but `full` is identity so 4 real paths. The work vs non-work distinction matters because the parser looks for different header patterns.

**`format_stage_protocol` with adaptations** — 2 adaptation types (contribution replacements, model protocol_adaptations) × any stage = 2 tests minimum. The contribution replacements use literal string matching against methodology.yaml protocol text — if that text changes, the replacements silently stop working.

**`format_role_data` by role** — 5 role renderers (fleet_ops, pm, architect, devsecops, worker). fleet_ops and pm and worker are tested. architect and devsecops are not. That's 2 missing.

**`format_role_data` by depth** — 4 depths (full_formatted, counts_plus_top5, counts_plus_top3, counts_only). full_formatted and counts_only are tested. counts_plus_top3 and counts_plus_top5 are not. That's 2 missing.

**`format_action_directive` edge cases** — `one_line` + `contributions_missing` is untested. 1 test needed.

**Total minimum tests for coverage:** 4 (trim) + 2 (adaptations) + 2 (roles) + 2 (depths) + 1 (action edge) = 11 tests.

### Fragility concern: string replacement in format_stage_protocol

The contribution adaptation at tier_renderer.py:621-635 does:
```python
protocol.replace("Present findings to the PO via task comments", ...)
protocol.replace("Present the plan to the PO for confirmation", ...)
```

These match EXACT strings from methodology.yaml protocol text. If the PO edits methodology.yaml (which they're supposed to be able to — "PO can modify this file"), these replacements break silently. 

Options:
- **A1**: Keep string replacement, add tests that verify the source strings still exist in methodology.yaml. Tests break when config changes — intentional early warning.
- **A2**: Replace string matching with marker-based substitution. methodology.yaml protocols contain markers like `{PO_REVIEW_TARGET}` that the renderer replaces based on context. Config-driven, not fragile.
- **A3**: Move all adaptation logic to protocol_adaptations in the model definition. The contribution model already has `protocol_adaptations` — extend this pattern so ALL adaptations are config-driven. No code-level string matching.

---

## Finding 4: Validation Matrix Coverage Gap (29 of 91+)

### Option A: Expand generator incrementally

Add scenarios as needed during PO leaf review. When the PO wants to review a leaf that doesn't have a generated scenario, add it to the generator first.

**Tradeoff:** Minimal upfront work. Scenarios are validated as they're created. But the gap stays large until all 91+ are reviewed.

### Option B: Generate all 91+ scenarios upfront

Map every leaf in context-injection-tree.md to a generator scenario. Produce all outputs before PO review begins.

**Tradeoff:** Complete coverage. But producing 60+ new scenarios before validation means potentially generating 60+ outputs with known bugs. Fix blockers first, then generate.

### Option C: Generate by tier slice

Group scenarios by tier. Generate all expert scenarios first (largest group, most detail). Validate expert tier completely. Then generate capable, then lightweight.

**Tradeoff:** Aligned with the progressive rollout plan in the decision tree (Phase 1: expert only). Validates what matters first. But doesn't surface cross-tier bugs until later phases.

---

## Relationships

- BUILDS ON: [[Analysis: Context Injection Pipeline Blockers]]
- FEEDS INTO: [[Plan: Context Injection Pipeline Blocker Fixes]]
- RELATES TO: [[Context Injection Decision Tree]]
- RELATES TO: [[Critical Review Findings — Context Injection Scenarios]]
- RELATES TO: [[Tier Rendering Design Rationale]]
- RELATES TO: [[Methodology Models Rationale]]
