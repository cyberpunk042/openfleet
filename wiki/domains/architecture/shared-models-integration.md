---
title: "Shared Models Integration — LLM Wiki + Methodology in OpenFleet"
type: concept
domain: architecture
status: processing
confidence: medium
created: 2026-04-09
updated: 2026-04-09
tags: [methodology, llm-wiki, shared-models, integration, context-injection, stage-gate, task-types, execution-modes, tracks]
sources:
  - id: src-model-llm-wiki
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/spine/model-llm-wiki.md
    title: "Model: LLM Wiki"
  - id: src-model-methodology
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/spine/model-methodology.md
    title: "Model: Methodology"
  - id: src-methodology-framework
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/domains/cross-domain/methodology-framework.md
    title: "Methodology Framework"
  - id: src-task-type-artifact-matrix
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/domains/devops/task-type-artifact-matrix.md
    title: "Task Type Artifact Matrix"
  - id: src-execution-modes
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/domains/devops/execution-modes-and-end-conditions.md
    title: "Execution Modes and End Conditions"
  - id: src-backlog-hierarchy
    type: documentation
    file: /home/jfortin/devops-solutions-research-wiki/wiki/domains/devops/backlog-hierarchy-rules.md
    title: "Backlog Hierarchy Rules"
---

# Shared Models Integration — LLM Wiki + Methodology in OpenFleet

> "For things to become simple in programming they have to become complex first." — PO, 2026-04-09

## Summary

The research wiki defines two foundational models — LLM Wiki (what knowledge IS) and Methodology (how work PROCEEDS) — that apply at every level: solo session, single assistant, fleet of assistants, full platform. OpenFleet already implements many of these concepts under different names. This page maps the shared model vocabulary to OpenFleet's existing architecture, identifies where they already align, where they diverge, and what evolving toward the shared models means for the context injection system and beyond.

## What Already Aligns

OpenFleet independently built many of the same patterns. The shared models give them names and structure.

### Stage-Gate System

| Shared Model Concept | OpenFleet Implementation | Where |
|---------------------|------------------------|-------|
| Stage sequence | conversation → analysis → investigation → reasoning → work | config/methodology.yaml |
| Per-stage protocols (MUST/MUST NOT) | protocol field per stage in methodology.yaml | config/methodology.yaml |
| Tools blocked per stage | tools_blocked field per stage | config/methodology.yaml |
| Stage-aware context injection | Stage protocol in task-context.md §6 | fleet/core/preembed.py |
| Readiness ranges per stage | readiness_range per stage | config/methodology.yaml |

### Task Type to Stage Mapping

| Shared Model | OpenFleet |
|-------------|-----------|
| 7 task types (epic/module/task/bug/spike/docs/refactor) | 9 task types (epic/story/task/subtask/bug/spike/blocker/request/concern) |
| Task type → required stages subset | task_types → required_stages in methodology.yaml |
| Type selection shapes execution path | get_initial_stage() uses task_type to determine entry point |

### Backlog Hierarchy

| Shared Model | OpenFleet |
|-------------|-----------|
| EPIC → MODULE → TASK | Epic → Story → Task/Subtask (Plane + OCMC) |
| Readiness flows upward (average of children) | _evaluate_parents() in orchestrator |
| Status flows upward | Parent task moves to review when all children done |
| Work happens at task level | Agents dispatched to individual tasks |
| Epic max status = review (human confirms done) | fleet-ops reviews, PO confirms gates |

### Three Parallel Tracks

| Track | Shared Model | OpenFleet Implementation |
|-------|-------------|------------------------|
| Execution | brainstorm → spec → plan → implement | orchestrator dispatch → agent stages → fleet_task_complete |
| PM | epics → modules → tasks with stage gates | Plane integration, PM agent, sprint planning |
| Knowledge | ingest → synthesize → cross-reference → evolve | Navigator, knowledge-context.md, wiki/ (nascent) |

### Execution Modes

| Shared Model Mode | OpenFleet Equivalent | Where |
|------------------|---------------------|-------|
| autonomous | full-autonomous (work_mode) | fleet/core/fleet_mode.py |
| semi-autonomous | project-management-work | fleet/core/fleet_mode.py |
| document-only / design-only | planning (cycle_phase) | fleet/core/fleet_mode.py |
| — | review (cycle_phase) | fleet/core/fleet_mode.py |
| — | crisis-management (cycle_phase) | fleet/core/fleet_mode.py |
| custom | — | not implemented |

### Quality Dimension

| Shared Model | OpenFleet |
|-------------|-----------|
| Skyscraper (full process) | Expert tier — full context, all stages, all gates |
| Pyramid (deliberate compression) | Capable/Flagship-Local tier — condensed, adapted |
| Mountain (accidental chaos) | Lightweight tier without proper guidance = risk |

## Where They Diverge

### Stage Names

| Shared Model (OpenArms) | OpenFleet | Semantic Match |
|------------------------|-----------|----------------|
| document | conversation + analysis | Understanding the problem |
| design | investigation + reasoning | Exploring options, making decisions |
| scaffold | — (no explicit scaffold stage) | Creating skeleton before implementation |
| implement | work | Producing the deliverable |
| test | — (tests within work stage) | Verifying correctness |

OpenFleet has 5 stages. OpenArms has 5 stages. But they split differently. OpenFleet's conversation + analysis covers OpenArms' document. OpenFleet's investigation + reasoning covers OpenArms' design. OpenFleet lacks an explicit scaffold stage. OpenFleet's work stage combines implement + test.

This is not wrong — it's a domain adaptation. Fleet agents work differently from solo agents. But the shared vocabulary should be acknowledged so cross-project communication is clear.

### Multiple Methodology Models

The shared model defines 9+ named models (feature-development, research, hotfix, bug-fix, refactor, documentation, ingestion, SFIF, knowledge-evolution). OpenFleet has ONE model in methodology.yaml with different stage subsets per task type.

The evolution: OpenFleet's methodology.yaml should support NAMED MODELS, not just stage subsets. A contribution task runs the "contribution" model. A rework task runs the "rework" model. A spike runs the "research" model. Each model has its own stage sequence, protocols, artifacts, and gates — defined in config, not hardcoded in preembed.py.

### Stage Boundary Enforcement

The shared model has explicit ALLOWED and FORBIDDEN artifact lists per stage per model. OpenFleet has tools_blocked per stage — which blocks tool CALLS but not artifact TYPES. An agent in analysis stage can't call fleet_commit, but there's nothing stopping it from producing solution-oriented content (which the analysis protocol says MUST NOT).

The evolution: stage boundaries need both tool blocking AND artifact type checking. The doctor/immune system already detects protocol violations — it should also check artifact types against ALLOWED/FORBIDDEN lists per model per stage.

### Contribution Tasks as a Separate Model

Currently: contribution tasks go through the same methodology stages as regular tasks. The preembed adds a CONTRIBUTION TASK section, but the protocol is the same (analysis says "present to PO" which is wrong for contributions).

The shared model says: contributions are a DIFFERENT methodology model. They have different stages (analyze target task → produce contribution → deliver via fleet_contribute), different gates (no PO gates — contribution flows to target agent), different protocols (role-specific: architect produces design_input, QA produces test criteria).

### Rework Tasks as a Separate Model

Currently: rework tasks (iteration ≥ 2) get adapted protocol text ("Fix ROOT CAUSE") and a rejection context section. But structurally they're still the "work" stage of the regular model.

The shared model says: bug-fix is a separate model (document → implement → test, NO design stage). Rework is even simpler — the problem IS documented (the rejection feedback), so it's closer to hotfix (implement → test). The model should be selected by the condition (labor_iteration ≥ 2 → rework model), not patched onto the regular model.

## What This Means for Context Injection

The context injection system IS the delivery mechanism for methodology model instances. Every scenario in the decision tree (91 mapped) is a specific model instance rendered for a specific agent situation.

### Model-Driven Rendering

Instead of one `build_task_preembed` with task-nature detection and if/elif branches, the rendering should be:

1. **Select model** — conditions (task_type, contribution_type, labor_iteration, stage, role) determine which methodology model applies
2. **Instantiate model** — the model definition (from config) provides: stage sequence, protocols, artifacts, gates, completion tool
3. **Render model instance** — the renderer (TierRenderer) produces context at the appropriate depth for the capability tier, using the model instance's protocols and artifacts

The model selection is the "task nature" we identified earlier (regular/contribution/rework). But it extends to: research/spike, documentation, hotfix, review. Each is a named model with its own rendering strategy.

### Track-Aware Context

The three parallel tracks should be visible in the agent's context:

- **Execution track**: task-context.md — what you're building, which stage, what protocol
- **PM track**: fleet-context.md role data — sprint state, backlog health, epic readiness
- **Knowledge track**: knowledge-context.md — relevant wiki pages, patterns, lessons

Currently, only the execution track is well-represented. The PM track is partially there (PM role data). The knowledge track is partially there (Navigator). The evolution is making all three tracks explicitly visible and properly populated.

### Quality as a Parameter

The capability tier (expert/capable/lightweight) IS the quality dimension applied to rendering:
- Expert = skyscraper rendering (full content, trust the agent)
- Capable/Flagship-Local = pyramid rendering (condensed, deliberate compression)
- Lightweight = pyramid rendering at minimum (focused, simple, brain supervises)
- Direct = no rendering (brain handles deterministically)

The choice is EXPLICIT per dispatch, not accidental. The tier selection logic in the orchestrator makes this choice based on backend_mode + task complexity + agent role.

## Open Questions

- Should OpenFleet's methodology.yaml adopt the shared model's stage names (document/design/scaffold/implement/test) or keep its own (conversation/analysis/investigation/reasoning/work)? Both are valid domain adaptations. The shared vocabulary helps cross-project communication. The existing names are already embedded in code and agent templates.

- How do multiple methodology models coexist in one methodology.yaml? One approach: a `models` section with named model definitions, each with its own stages/protocols/artifacts. The current `stages` section becomes the "feature-development" model. New models are added alongside.

- How does model selection interact with the orchestrator's dispatch logic? Currently dispatch assigns a task_stage from readiness. With multiple models, dispatch also assigns a methodology_model from conditions. The preembed renders the selected model's context.

- The shared model's 14-step work loop assumes a solo agent working through a backlog. Fleet agents work on ASSIGNED tasks dispatched by the orchestrator. How does the work loop adapt for fleet context? Steps 1-3 (find task, read task, determine next stage) are done by the orchestrator, not the agent. Steps 4-8 (execute, update, commit, verify) are the agent's job.

- The ALLOWED/FORBIDDEN artifact lists per stage per model — where do these live? In methodology.yaml alongside the protocol text? In a separate config? In the stage_context module?

## Relationships

- BUILDS ON: [Context Injection Decision Tree](context-injection-tree.md) — the tree's scenarios are methodology model instances
- BUILDS ON: [Context Injection Tiered Rendering Design](../../docs/superpowers/specs/2026-04-09-context-injection-tiered-rendering-design.md) — tier rendering = quality dimension
- RELATES TO: [Validation Issues Catalog](validation-issues-catalog.md) — many issues trace to missing model awareness
- FEEDS INTO: config/methodology.yaml — evolution toward named models
- FEEDS INTO: fleet/core/preembed.py — model-driven rendering
- FEEDS INTO: fleet/core/tier_renderer.py — quality dimension implementation
