---
title: "Sister Project Map — OpenFleet Ecosystem Relationships"
type: reference
domain: ecosystem
status: active
created: 2026-04-18
updated: 2026-04-18
tags: [ecosystem, sister-projects, openarms, aicp, dspd, nnrt, second-brain, integration]
confidence: high
sources:
  - id: our-claude-md
    type: documentation
    file: CLAUDE.md
    title: "OpenFleet CLAUDE.md"
  - id: our-agents-md
    type: documentation
    file: AGENTS.md
    title: "OpenFleet AGENTS.md"
  - id: brain-super-model
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/super-model/super-model.md
    title: "Super-Model — Research Wiki as Ecosystem Intelligence Hub"
---

# Sister Project Map — OpenFleet Ecosystem Relationships

## Summary

OpenFleet operates within a 5-project ecosystem plus adjacent projects, each with a specific relationship to our platform. This page names each project, its role, how OpenFleet depends on or integrates with it, and the local filesystem path. Derived from our AGENTS.md ecosystem table + brain's super-model project listing; kept in sync as sister-project identity profiles evolve.

## The Five-Project Core

| Project | Role | Relationship to OpenFleet | Local path |
|---------|------|--------------------------|------------|
| **OpenArms** | Single AI-assistant runtime (harness v1→v2→v3) | Our fleet's per-agent runtime technology. Each OpenFleet agent workspace embeds OpenArms-style templates (SOUL.md, HEARTBEAT.md, WORKSPACE.md). | `../openarms` (if cloned) |
| **OpenFleet** | Fleet orchestration platform (this project) | IS this project. A platform that manages 10 role-specific AI assistants with immune system, contribution gating, tier-based context depth. | `/home/jfortin/openfleet` |
| **AICP** | AI Control Platform — complexity-based inference routing (LocalAI for routine, Claude for complex) | Source-of-truth for AI capability profiles (`default`, `code-review`, `dual-gpu`, `fleet-light`, `fast`). Our `config/tier-profiles.yaml` maps to AICP profile names. 5-stage roadmap targets 80%+ Claude API cost reduction. | `../devops-expert-local-ai` (AICP is the product name; devops-expert-local-ai is the repo) |
| **devops-control-plane** | Operational governance origin — 16 post-mortems → 24 rules → OpenFleet's immune system | Origin of `doctor.py`'s 24 governance rules. Rules are static files imported at runtime, not an API. | `../devops-control-plane` |
| **Research Wiki (second brain)** | Shared LLM Wiki / knowledge hub | Master knowledge source — 360+ pages, 2,400+ relationships, 16 models, 22 standards, 4 principles, 57 lessons. Our `tools/lint.py`, `tools/gateway.py`, `tools/evolve.py` forward to brain's venv. | `../devops-solutions-research-wiki` |

## Adjacent Projects

| Project | Role | Relationship to OpenFleet | Local path |
|---------|------|--------------------------|------------|
| **OpenClaw** | WebSocket gateway connecting agents + Mission Control | Vendored into OpenFleet at `vendor/openclaw/`. Agents connect as clients. | (vendored) |
| **Mission Control** | Fleet command surface | Companion to OpenFleet for orchestrator observability. Referenced in openclaw-* fleet skills. | — |
| **Plane** | Project management tool | Bidirectional sync via `fleet/cli/plane.py`. Backlog entries synced to Plane issues; fleet-side agents update Plane as work progresses. | — |
| **LightRAG** | Graph-enhanced retrieval layer | Scripts at `scripts/setup-lightrag.sh`, `scripts/lightrag-index.sh`. Additive to wiki navigation once pages cross the ~200-page index-navigation ceiling (brain is at ~317, approaching). | — |
| **devops-solutions-information-hub** | Information hub within devops-solutions product family | Sibling project under the devops-solutions umbrella. Integration specifics not yet documented here. | `../devops-solutions-information-hub` |
| **DSPD** (devops-solution-product-development) | Self-hosted Plane host — PM integration | Hosts the Plane instance the fleet syncs to. Cross-project PM integration already operational. | `../devops-solution-product-development` |
| **NNRT** | Narrative-to-Neutral-Report-Transformer NLP pipeline | Report transformation NLP. Referenced in AGENTS.md as ecosystem project. Integration specifics not yet documented here. | `../Narrative-to-Neutral-Report-Transformer` |

## How OpenFleet Relates to Each

### To OpenArms

OpenArms is our runtime TECHNOLOGY for individual agents. Each OpenFleet agent (10 roles: architect, devops, devsecops-expert, fleet-ops, project-manager, qa-engineer, software-engineer, technical-writer, ux-designer, accountability-generator) runs under an OpenArms-style harness with workspace, heartbeat, soul, per-role context. The fleet ORCHESTRATES these agents; OpenArms PROVIDES the per-agent runtime loop.

Divergence: OpenArms optimizes for single-assistant solo/harness work. OpenFleet optimizes for multi-agent coordination, contribution gating, immune system. Both inherit from the brain's Methodology model but adapt its stages, quality dimensions, and enforcement to their scale.

### To AICP (devops-expert-local-ai)

AICP is the product name; the repo is `devops-expert-local-ai`. AICP owns capability profiles and complexity-based inference routing. Our 5-tier vocabulary (Expert/Capable/Flagship-local/Lightweight/Direct) maps to AICP profile names. A fleet dispatch selects a tier; the tier selects an AICP profile; the profile configures the actual inference backend (Claude Opus/Sonnet for Expert, qwen3-8b/gemma4-26b/qwen3-4b for local tiers). Brain's model-ecosystem describes the economic dimension: 5-stage AICP roadmap targets 80%+ Claude API cost reduction — critical to fleet economics at 10 continuous agents.

### To devops-control-plane

devops-control-plane is our operational-governance DNA donor. 16 post-mortems across its operational history produced 24 rules that became OpenFleet's immune system. The knowledge flow: failure → post-mortem → rule → enforcement. Our `fleet/core/doctor.py` imports those 24 rules as static files — no API, no runtime service dependency. When a new failure occurs in OpenFleet operation, the lesson flows BACK: post-mortem → rule update → next generation of immune-system detection.

### To devops-solutions umbrella projects (DSPD + information-hub)

OpenFleet sits within the broader devops-solutions product family. DSPD (devops-solution-product-development) hosts the Plane instance the fleet PM-syncs with — that integration is operational today. devops-solutions-information-hub is a sibling under the same umbrella; integration specifics not yet formalized. Note: AICP is separately housed at `devops-expert-local-ai` but is treated as a core project (not umbrella sibling) because of its direct fleet-runtime role.

### To the Second Brain

The brain is the master knowledge source. OpenFleet is a consumer + contributor:

| Direction | Mechanism | Current state |
|-----------|-----------|---------------|
| Brain → OpenFleet (knowledge in) | Forwarders in `tools/` execute brain's gateway/lint/evolve against our wiki with `--wiki-root /openfleet`; templates + schema seeded from brain into `wiki/config/` | ✅ active |
| OpenFleet → Brain (knowledge out) | `gateway contribute --target=brain` creates pending-review entries in brain's `log/` or `lessons/00_inbox/` | ✅ active (5 contributions pending-review as of 2026-04-18) |
| Brain → OpenFleet (operational scans) | `pipeline scan ../openfleet/` from brain side pulls our key files into `raw/articles/` for brain ingestion | ⚠️ stale (last run pre-2026-04-17 infrastructure changes) |

See [[Integration Chain Mapping — OpenFleet Position 2026-04-18]] for the 17-step scorecard.

## Identity Ownership

Each project owns its own identity profile (the stable fields — type/domain/phase/scale/second-brain). Consumer/runtime properties (execution mode/PM level/trust tier/SDLC profile) are NOT owned by the project — they're declared by each consumer at connect time per brain's `execution-mode-is-consumer-property-not-project-property` principle.

| Project | Identity profile |
|---------|-----------------|
| OpenFleet | [[OpenFleet — Identity Profile]] (this wiki) |
| OpenArms | `../openarms/.../identity-profile.md` + brain's `wiki/ecosystem/project_profiles/openarms/identity-profile.md` |
| Research Wiki | brain's own `wiki/ecosystem/project_profiles/research-wiki/identity-profile.md` |
| AICP, DSPD, NNRT | Brain has placeholder or partial identity profiles; not owned locally in OpenFleet |

## Ecosystem Feedback Loop

Per brain's [[Ecosystem Feedback Loop — Wiki as Source of Truth]]:
1. Brain aggregates knowledge from all projects.
2. Brain processes, validates, and synthesizes into models / standards / lessons / patterns / decisions.
3. Brain feeds back to projects via forwarders + templates + contribution-policy.
4. Projects evolve, produce operational data, contribute learnings back.
5. Cycle repeats.

OpenFleet's role: as a fleet-scale operator, we generate MORE operational data per unit time than solo/harness projects. The brain already extracted 7 patterns from OpenFleet (immune system, contribution gating, tier-based context depth, validation matrix, deterministic shell, storm graduation, sprint planning with capacity). Continued operation should produce more.

## Relationships

- PART OF: [[Ecosystem]]
- BUILDS ON: [[OpenFleet — Identity Profile]]
- RELATES TO: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- RELATES TO: [[Operational Depth Gaps — What Structural Compliance Doesn't Measure]]
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- FEEDS INTO: future cross-project integration work
