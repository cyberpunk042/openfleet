---
title: "Methodology Models Rationale"
type: concept
domain: architecture
status: processing
confidence: medium
created: 2026-04-10
updated: 2026-04-10
tags: [methodology, models, rationale, config, selection, contribution, rework, research]
sources:
  - id: src-model-methodology
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/model-methodology.md
    title: "Model: Methodology"
---

# Methodology Models Rationale

## Summary

OpenFleet's methodology.yaml now defines 7 named models instead of one stage sequence. This page explains WHY these models, how they derive from the shared Methodology Framework, and the design decisions behind the selection rules.

## Key Insights

1. **One stage-sequence with task-type subsets fails when tasks have fundamentally different lifecycles.** Contributions don't need PO gates. Rework doesn't need reasoning. Reviews aren't linear work. Research never produces code. A single model with subsets produces wrong protocols, wrong completion tools, and wrong gates for each.

2. **OpenFleet's 7 models derive from the brain's Methodology Framework but adapt the stage vocabulary.** We keep conversation/analysis/investigation/reasoning/work/review as stage names (6, vs brain's 5). We recombine them per task's actual lifecycle.

3. **Selection is first-match-wins across 6 rules in priority order.** contribution_type > labor_iteration > task_type (spike/concern) > urgency (blocker+critical) > reviewing-agent > default. This makes selection deterministic and prevents a task from matching two models.

4. **Protocol adaptations are DATA, not code.** Each model can define per-stage `protocol_adaptations` in `methodology.yaml`. Adding a new model with custom protocols is a config change. No code edits to methodology_config.py needed.

5. **Review is NOT a stage within feature-development — it's its own model.** Fleet-ops reviewing is a fundamentally different activity with its own protocol and completion tool (`fleet_approve`, not `fleet_task_complete`). Collapsing review into feature-dev blurs the boundary.

## Deep Analysis

### Why Multiple Models

The shared Methodology Framework (research wiki) defines 9+ named models. OpenFleet previously had one stage sequence (conversation → analysis → investigation → reasoning → work) with task_types mapping to stage subsets. This is the Task Type Artifact Matrix pattern — but limited to ONE model with different subsets.

The problem: contribution tasks, rework tasks, review tasks, and research tasks have fundamentally different lifecycles. A contribution task doesn't go through PO gates. A rework task doesn't need reasoning — the plan exists, the rejection tells you what to fix. A spike never produces code. Forcing all of these through subset selections of one model meant the protocols, completion tools, and gate mechanisms were wrong for non-standard tasks.

### The 7 Models

| Model | Stages | Completion | Gates | Selected When |
|-------|--------|------------|-------|---------------|
| feature-development | conversation → analysis → investigation → reasoning → work | fleet_task_complete | PO | Default |
| contribution | analysis → reasoning | fleet_contribute | None | contribution_type set |
| rework | work | fleet_task_complete | PO | labor_iteration ≥ 2 |
| research | conversation → investigation → reasoning | fleet_task_complete | PO | spike, concern |
| documentation | analysis → work | fleet_task_complete | PO | docs type, writer contribution |
| review | review | fleet_approve | None | fleet-ops reviewing |
| hotfix | work | fleet_task_complete | PO | blocker + critical urgency |

### Selection Rules

Evaluated in order. First match wins. This prevents ambiguity — a task can only match one model.

1. contribution_type set → contribution (highest priority — contribution nature overrides everything)
2. labor_iteration ≥ 2 → rework (rework overrides task type)
3. task_type in [spike, concern] → research
4. blocker + critical → hotfix
5. fleet-ops reviewing → review
6. default → feature-development

### Config-Driven Protocol Adaptations

Each model can define per-stage protocol_adaptations in YAML. These are injected as the FIRST MUST item in the stage protocol, before the code-driven adaptations (role-specific, contribution-aware, rework-aware). This means adding a new model with custom protocols is a config change — no code modifications.

### Design Decisions

**Why contribution model has only analysis + reasoning:** A contributor examines the target task's domain (analysis) then produces their contribution artifact (reasoning). There's no conversation (the target task already has the requirement), no investigation (the contributor is a specialist — they know their domain), no work (the contribution IS the artifact, not code).

**Why rework model has only work:** The problem is documented (rejection feedback). The plan exists (from the first attempt). Analysis and reasoning were already done. The agent just needs to fix and re-submit.

**Why hotfix model has only work:** Same reasoning as rework but for urgent bugs where the cause and fix are already understood. Skip everything, fix it, test it, ship it. This is explicitly a Pyramid quality choice — deliberate compression, not accidental.

**Why review is its own model:** Fleet-ops reviewing is a fundamentally different activity — reading work, comparing to requirements, checking methodology compliance, deciding approve/reject. It doesn't fit any stage in the feature-development model. It's its own process with its own protocol and completion tool (fleet_approve, not fleet_task_complete).

## Relationships

- BUILDS ON: Brain's `model-methodology.md` — the shared Methodology Framework defining the 9 named model pattern
- BUILDS ON: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Tier Rendering Design Rationale]] — tier depth applies per stage per model
- RELATES TO: [[Context Injection Decision Tree]] — the tree branches on selected model
- IMPLEMENTS: `config/methodology.yaml` (7 models + 6 selection rules + protocol adaptations)
- FEEDS INTO: every task-level context injection in OpenFleet (model selection is the first branch of the autocomplete chain after identity)
