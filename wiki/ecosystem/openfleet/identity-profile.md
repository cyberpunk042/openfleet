---
title: "OpenFleet — Identity Profile"
aliases:
  - "OpenFleet — Identity Profile"
  - "OpenFleet Identity"
type: reference
domain: ecosystem
status: synthesized
confidence: high
maturity: seed
created: 2026-04-16
updated: 2026-04-16
sources:
  - id: claude-md
    type: documentation
    file: CLAUDE.md
  - id: methodology-yaml
    type: documentation
    file: config/methodology.yaml
  - id: openfleet-fleet-architecture
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/sources/ecosystem-projects/src-openfleet-fleet-architecture.md
  - id: brain-profile-of-us
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/ecosystem/project_profiles/openfleet/identity-profile.md
  - id: execution-mode-consumer-property
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/lessons/01_drafts/execution-mode-is-consumer-property-not-project-property.md
tags:
  - ecosystem
  - openfleet
  - identity
  - goldilocks
  - self-declaration
  - platform
---

# OpenFleet — Identity Profile

## Summary

OpenFleet's self-declared Goldilocks identity profile — authored from our own perspective (contrast: the second brain maintains its own retrospective view of us at `devops-solutions-research-wiki/wiki/ecosystem/project_profiles/openfleet/identity-profile.md`, distilled from what it has learned FROM us). This profile declares only the STABLE project-level fields per the `execution-mode-is-consumer-property` lesson. Consumer/task-level properties (execution mode, SDLC profile selected for a given task, methodology model chosen, current stage, trust tier for a specific agent) are NOT declared here — they are per-connection / per-task properties declared by each consumer at runtime.

## Reference Content

### Stable Identity (declared, rarely changes)

> [!info] The fields this profile DOES declare
>
> | Dimension | Value | Evidence |
> |-----------|-------|---------|
> | **Type** | system (platform that runs a fleet; also solo-developable on main) | Orchestrator + 10 agents + Mission Control + Open Gateway + IRC + Plane + knowledge base — a platform, not a product or library |
> | **Domain** | mixed — Python (orchestrator, MCP server, fleet/*) + TypeScript/Node (gateway, Mission Control UI runtime) + Bash (IaC scripts in scripts/) + Markdown (wiki/) | 71 Python modules, multiple TS workspaces, 42+ Bash scripts, ~3,815 .md files |
> | **Second Brain** | connected (sister project at `../devops-solutions-research-wiki`) | wiki/config/ seeded 2026-04-16; gateway + view + lint + evolve forwarders in tools/; `.mcp.json` MCP integration; scan + contribute flow verified |
> | **Compliance Tier** | Tier 4 / 4 STRUCTURAL | Per `gateway compliance` 2026-04-16. Operationally still Tier 2+ (31 lint/validation issues across 51 existing wiki pages, 0.7 avg relationships/page vs ≥6 healthy, 358-line CLAUDE.md vs <200 target). |

### What is EXPLICITLY NOT declared here

> [!warning] Consumer/task properties belong at the consumer, not in this profile
>
> The following vary per connection, per session, per task — they are NOT project properties:
>
> | Consumer/task property | Where it's declared |
> |---|---|
> | **Execution Mode** (solo / harness v1-v3 / full-system) | The consumer at connect time. Solo developer on main = solo mode. Fleet agent dispatched by orchestrator = full-system mode. Sub-agent = trustless. Same repo, different consumers, different modes. |
> | **SDLC Profile** (simplified / default / full) | Per-task. A hotfix in a production project runs simplified; a new feature runs full. The project's typical profile is guidance, not a hardcoded constraint. |
> | **Methodology Model** (feature-development, contribution, rework, research, documentation, review, hotfix) | Per-task, per our `config/methodology.yaml` model-selection rules. Task type + contribution type + labor iteration + delivery phase + urgency = selected model. |
> | **Current Stage** (conversation / analysis / investigation / reasoning / work / review) | Per-task frontmatter or heartbeat context. |
> | **Trust Tier** (expert / capable / lightweight / flagship-local / direct) | Per-agent-per-task-type. Tier-progressive: earned through approval rates. |
>
> Source: `execution-mode-is-consumer-property-not-project-property` lesson (second brain, 2026-04-15). Conflating these into the project profile is the named "conflation drift" failure mode.

### Phase × Scale (declared, reviewed periodically)

> [!info] Current phase and scale — review roughly quarterly
>
> | Dimension | Value | Last reviewed |
> |---|---|---|
> | **Phase** | production (fleet runs daily; platform itself still evolves) | 2026-04-16 |
> | **Scale** | large (~3,815 .md files, 2,246-line orchestrator, 71 Python modules, ~50k+ LOC total across Python + TS + Bash) | 2026-04-16 |

### Architecture Distinction — Platform vs Runtime

> [!abstract] OpenFleet is two things at once — both matter
>
> | Aspect | Platform (the repo) | Runtime (fleet operation) |
> |---|---|---|
> | **What it is** | Python orchestrator + TS gateway + IaC scripts + config + wiki + agent templates | 10 agents dispatched by orchestrator on a 30s cycle, each running Claude Code in a workspace |
> | **Who works on it** | Solo developer (PO + Claude on main) | Fleet of 10 specialized agents, each with SOUL.md + HEARTBEAT.md |
> | **Execution mode for work here** | solo (no harness, no orchestrator wraps the development session) | full-system (orchestrator OWNS the dispatch loop; agents never self-direct) |
> | **SDLC default** | default profile (PO supervises; hooks optional) | full profile (MCP tool blocking per stage + immune system + contribution gating) |
> | **Methodology** | 7 named models at `config/methodology.yaml`, 6 stages (conversation → analysis → investigation → reasoning → work → review) | Same methodology, enforced by orchestrator MCP server |
>
> Both exist in the same repo. Different consumers. Different modes. One profile wouldn't describe both.

### Methodology Divergence from Second Brain

> [!info] Deliberate divergences — per "Methodology Is a Framework, Not a Fixed Pipeline"
>
> | Aspect | Second Brain | OpenFleet |
> |---|---|---|
> | Stages | document → design → scaffold → implement → test (5) | conversation → analysis → investigation → reasoning → work → review (6) |
> | Quality tiers | Skyscraper / Pyramid / Mountain | Expert / Capable / Flagship-local / Lightweight / Direct |
> | Methodology models | 9 (feature-dev, research, knowledge-evolution, documentation, bug-fix, refactor, hotfix, integration, project-lifecycle) | 7 (feature-development, contribution, rework, research, documentation, review, hotfix) |
> | Model selection | Conditions: task_type + novelty + phase + domain + scale + urgency | Conditions: task_type + contribution_type + labor_iteration + delivery_phase + priority + agent |
> | PM level target | L1 (wiki backlog) | L3 (orchestrator deterministic dispatch + Plane bidirectional sync) |
> | Enforcement | instructions + pipeline post + evolve | MCP tool blocking per stage + 30s doctor cycle + tier progression + contribution gating + storm graduation + standing orders |
>
> These divergences are legitimate fleet-specific evolutions that the brain acknowledges and has learned from. See `devops-solutions-research-wiki/wiki/comparisons/openarms-vs-openfleet-enforcement.md` for the operational comparison.

### Patterns OpenFleet Contributes to the Ecosystem

> [!success] Already extracted by the second brain as patterns derived from us
>
> | Pattern | Status in brain |
> |---|---|
> | Three Lines of Defense — Immune System for Agent Quality | `wiki/patterns/03_validated/enforcement/three-lines-of-defense-immune-system-for-agent-quality.md` |
> | Harness-Owned Loop — Deterministic Agent Execution | `wiki/patterns/03_validated/enforcement/harness-owned-loop-deterministic-agent-execution.md` |
> | Contribution Gating — Cross-Agent Inputs Before Work | `wiki/patterns/03_validated/enforcement/contribution-gating-cross-agent-inputs-before-work.md` |
> | Tier-Based Context Depth — Trust Earned Through Approval Rates | `wiki/patterns/03_validated/knowledge/tier-based-context-depth-trust-earned-through-approval-rates.md` |
> | Validation Matrix — Test Suite for Context Injection | `wiki/patterns/03_validated/knowledge/validation-matrix-test-suite-for-context-injection.md` |
> | Deterministic Shell, LLM Core | `wiki/patterns/03_validated/architecture/deterministic-shell-llm-core.md` |
> | Enforcement Hook Patterns | `wiki/patterns/03_validated/enforcement/enforcement-hook-patterns.md` |
>
> These were extracted by the brain from source material (our architecture scans, methodology scans) WITHOUT a direct `gateway contribute` flow from us. The bidirectional loop is now active as of 2026-04-16 — future contributions flow through `gateway contribute`.

## Relationships

- BUILDS ON: [[methodology-framework|Methodology Framework]]
- BUILDS ON: [[project-self-identification-protocol|Project Self-Identification Protocol — The Goldilocks Framework]]
- RELATES TO: [[execution-mode-is-consumer-property-not-project-property|Execution Mode Is a Consumer Property, Not a Project Property]]
- RELATES TO: [[methodology-is-a-framework-not-a-fixed-pipeline|Methodology Is a Framework, Not a Fixed Pipeline]]
- CONTRASTS WITH: brain's retrospective profile of OpenFleet at `devops-solutions-research-wiki/wiki/ecosystem/project_profiles/openfleet/identity-profile.md` — same project, different perspective (retrospective brain view vs self-declared platform view)
- FEEDS INTO: `../../../CLAUDE.md` — the identity fields declared here are the source of truth our CLAUDE.md should route to
- RELATES TO: [[Tier Rendering Design Rationale]]
- RELATES TO: [[Methodology Models Rationale]]
- RELATES TO: [[Context Injection Decision Tree]]
