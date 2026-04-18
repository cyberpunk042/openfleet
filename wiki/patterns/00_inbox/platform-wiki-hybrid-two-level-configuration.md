---
title: "Platform-Wiki Hybrid Two-Level Configuration"
type: pattern
domain: cross-domain
layer: 5
status: synthesized
confidence: medium
maturity: seed
created: 2026-04-18
updated: 2026-04-18
tags: [pattern, configuration, methodology, platform, wiki, hybrid, openfleet, orthogonality]
derived_from:
  - "OpenFleet two-level configuration directive 2026-04-17"
instances:
  - page: "OpenFleet"
    context: "config/methodology.yaml holds the fleet/runtime methodology dispatched agents execute; wiki/config/methodology.yaml holds the wiki-authoring methodology the repo itself uses. Explicit PO directive 2026-04-17 codified this as intentional architecture rather than drift."
sources:
  - id: po-directive-2026-04-17
    type: documentation
    file: wiki/log/2026-04-17-directive-two-methodologies.md
    title: "PO clarification — OpenFleet has two methodologies (intentional)"
  - id: brain-model-methodology
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/models/foundation/model-methodology.md
    title: "Model — Methodology"
  - id: brain-model-llm-wiki
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/models/foundation/model-llm-wiki.md
    title: "Model — LLM Wiki"
---

# Platform-Wiki Hybrid Two-Level Configuration

## Summary

A project that is BOTH a runtime platform AND an LLM Wiki needs TWO distinct methodology configurations at TWO distinct paths — one for the PLATFORM (what dispatched runtime agents execute) and one for the WIKI (what authoring a repo-level page follows). Collapsing them into one path produces either a methodology that fits the runtime but not the wiki (wiki pages get ceremony they don't need) or fits the wiki but not the runtime (platform agents get a too-simple methodology). The pattern: keep them orthogonal — each lives at its own path, each owned by its own domain, each adapted per its own scale and consumers.

## Pattern Description

### The structural problem

Brain's LLM Wiki model assumes ONE `wiki/config/methodology.yaml` per project — the methodology that governs wiki-content authoring. Brain's Methodology model assumes ONE methodology per project — the one consumers execute.

For pure-wiki projects (research wiki, knowledge-base projects): same `wiki/config/methodology.yaml`, same thing.

For pure-runtime projects (a single-assistant harness, a service): no wiki methodology; only a runtime one in `config/` or code.

For HYBRID projects (platform + wiki coexisting): ONE config file at ONE path is wrong. The platform runtime's methodology (multi-stage agent dispatch with immune system, quality tiers, contribution gating) is not the same as the wiki's methodology (lint pages, promote lessons, migrate standards). Forcing them to share structure produces Mountain-tier work in one of the two layers.

### The pattern

Keep two orthogonal configs:

| Config | Path (convention) | Governs | Consumers |
|--------|------------------|---------|-----------|
| **Platform / runtime methodology** | `config/methodology.yaml` (project root) | What dispatched runtime agents execute — stages, protocols, tools_blocked, completion tools | Platform orchestrator + dispatched agents |
| **Wiki / authoring methodology** | `wiki/config/methodology.yaml` | What repo-level wiki-content authoring follows — document/design/scaffold/implement/test-style stages on wiki pages | Solo agent on the repo + any harness working on the repo |

Each config is adapted independently. Each consumer reads the config relevant to its role. Neither is a subset of the other — they solve different problems at different scales.

### Why not unify

Because their inputs differ:
- Platform methodology inputs: task from Plane, contribution matrix, tier profile, role, immune-system state
- Wiki methodology inputs: page type, maturity folder, source provenance, quality gates

Their outputs differ:
- Platform output: commits, artifacts, fleet_contribute, fleet_approve
- Wiki output: `pipeline post` clean, `lint` clean, promotion recommendation

Their cadences differ:
- Platform methodology runs 100s of times per day (per dispatched task)
- Wiki methodology runs on manual authoring cadence (sporadic, human-driven)

A unified config either overfits to one cadence (hurting the other) or fragments into conditional branches (hurting readability).

## Instances

> [!example] OpenFleet (2026-04-17 onward)
>
> - `config/methodology.yaml` — fleet runtime methodology: 7 named models (feature-development, contribution, rework, research, documentation, review, hotfix) × 6 stages (conversation → analysis → investigation → reasoning → work → review). Selected by conditions including contribution_type, labor_iteration, task_type, urgency, reviewing-agent. See [[Methodology Models Rationale]].
> - `wiki/config/methodology.yaml` — wiki authoring methodology: brain-seeded verbatim 2026-04-17 (9 models × 5 stages document/design/scaffold/implement/test). Used when authoring a wiki page in this repo.
>
> PO directive 2026-04-17 verbatim: *"of course there is two methodology... one is for the repo by default in solo agent + based of the repo and then if a harness start working on it in V2 its also using it, but the openfleet is a whole system. not only a wiki... the fleet live independed than the project and already has methodology itself.... it just mean that openfleet since its a whole system is going to have two level of config. for the wiki, like any project, and for the platform / solution / full system."*

> [!example]- Hypothetical: OpenArms-extended-with-own-wiki
>
> If OpenArms-the-harness adopted its own LLM Wiki (for runtime-operational knowledge, incidents, evolution), it would become a platform-wiki hybrid too. Its harness methodology (v2/v3 lives in code + hooks) stays in `src/` or `.claude/hooks/`. Its wiki authoring methodology would live at `wiki/config/methodology.yaml`. Same pattern.

## When To Apply

Apply when ALL of:
- The project has a runtime that dispatches work AND a knowledge base that grows via authoring
- Runtime agents have their own lifecycle distinct from wiki-page lifecycle
- The two cadences (runtime dispatch, wiki authoring) are measurably different
- Single-config would force branching logic to keep them separated

## When Not To Apply

Do NOT apply when:
- The project is a pure wiki (only `wiki/config/methodology.yaml`; no runtime methodology beyond wiki-content work)
- The project is a pure runtime (no wiki; methodology lives in code or a single runtime config)
- The project is small and one layer dominates — premature split creates more maintenance than it saves

## Structural Consequences

- Each methodology evolves independently. A wiki-methodology update doesn't regress runtime behavior and vice versa.
- Documentation has two clear targets. Brain's `model-methodology.md` reference applies to the wiki-layer. Runtime methodology documentation lives in platform-level architecture pages.
- Consumer forwarders must not conflate the two. A generic `--wiki-root` that auto-targets one layer can silently misroute commands meant for the other (see [[Forwarder Semantics at Contribution Boundaries]] for an analogous bug).
- Compliance checkers should detect which layer is being audited. A single "methodology compliance" score for a hybrid is misleading.

## Relationships

- BUILDS ON: brain's [[model-methodology|Model — Methodology]] (platform runtime layer)
- BUILDS ON: brain's [[model-llm-wiki|Model — LLM Wiki]] (wiki authoring layer)
- RELATES TO: [[OpenFleet — Identity Profile]] (`Type: system` that runs a fleet AND contains a wiki)
- RELATES TO: [[Sister Project Map — OpenFleet Ecosystem Relationships]]
- RELATES TO: [[Methodology Models Rationale]] (the 7 platform-runtime models)
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- CONSTRAINS: compliance checker design — hybrid projects need layer-specific audit
