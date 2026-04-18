---
title: "OpenFleet in the Goldilocks Ecosystem — Walkthrough C Reconciled"
type: reference
domain: ecosystem
status: active
created: 2026-04-18
updated: 2026-04-18
tags: [ecosystem, goldilocks, walkthrough-c, identity, fleet-scale, full-system, tier-profile]
confidence: high
sources:
  - id: brain-goldilocks-flow
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/goldilocks-flow.md
    title: "Goldilocks Flow — From Identity to Action"
  - id: brain-walkthrough-c
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/spine/goldilocks-flow.md
    title: "Walkthrough C: Full System — OpenFleet (10-Agent Fleet)"
  - id: correction-filed
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/log/walkthrough-c-(openfleet)-ground-truth-verification-2026-04-.md
    title: "Walkthrough C (OpenFleet) ground-truth verification 2026-04-17"
---

# OpenFleet in the Goldilocks Ecosystem — Walkthrough C Reconciled

## Summary

The brain's `goldilocks-flow.md` contains Walkthrough C — an explicit step-by-step description of how the 8-step identity-to-action flow runs on OpenFleet. This page reconciles Walkthrough C's claims against OpenFleet's ground-truth state as of 2026-04-18, names what's accurate / aspirational / incorrect, and establishes OpenFleet's declared Goldilocks position. Complements the brain-side correction filed 2026-04-17.

## The Goldilocks 8-Step Flow Applied to OpenFleet

### Step 1 — DETECT

Gateway auto-detects (per-agent and fleet-level):

| Dimension | Detection | OpenFleet Value |
|-----------|-----------|-----------------|
| Domain | package.json, pyproject.toml, main.tf, wiki/config/ | **mixed** — Python orchestrator + TS/Node gateway + Bash IaC + Markdown wiki |
| Scale | source file count | **large** — ~3,815 .md files, 2,246-line orchestrator, ~50k LOC+ |
| Phase | CI + tests + Docker | **production** — fleet runs daily; platform still evolves |
| Second brain | sibling dir + manifest | **connected** — sister project at `../devops-solutions-research-wiki`, `.mcp.json` wired |

### Step 2 — DECLARE

OpenFleet's CLAUDE.md declares STABLE fields only:

```yaml
Identity Profile (Goldilocks — stable fields only):
  Type: system (platform running a fleet; also solo-developable)
  Domain: mixed
  Phase: production
  Scale: large
  Second Brain: connected
```

Consumer/runtime properties (Execution Mode / PM Level / Trust Tier / SDLC Profile) are deliberately NOT in CLAUDE.md — they're per-consumer per brain's `execution-mode-is-consumer-property` principle. A harness connecting to OpenFleet declares its own execution mode at connect time via `MCP_CLIENT_RUNTIME` or equivalent.

### Step 3 — SELECT PROFILE

Brain recommends for `Production + large`: **Full** SDLC profile. Readiness gate = 99. Full infrastructure enforcement (immune system, tier blocking, heartbeat enforcement, contribution gating).

OpenFleet status: we operate at that depth on the fleet runtime side. The Wiki side of this repo (authoring the pages you're reading now) is closer to `Production + medium` → Default profile. The two sides use different methodologies (see [[OpenFleet has two methodologies]]).

### Step 4 — SELECT MODEL

The orchestrator selects a methodology model per dispatched task. Our 7 models per [[Methodology Models Rationale]]:
feature-development, contribution, rework, research, documentation, review, hotfix.

Selection rules (first-match-wins):
1. `contribution_type` set → contribution
2. `labor_iteration ≥ 2` → rework
3. `task_type in [spike, concern]` → research
4. `blocker + critical` → hotfix
5. fleet-ops reviewing → review
6. default → feature-development

Divergence from brain's 9-model catalogue is legitimate domain adaptation. Alignment-declaration is pending.

### Step 5 — ENTER STAGE

Stage sequence: conversation → analysis → investigation → reasoning → work → review. Protocol (MUST/MUST NOT/CAN/Advance) defined in `config/methodology.yaml` per stage. Stage-aware skill injection via `skill-stage-mapping.yaml`.

Divergence from brain's document/design/scaffold/implement/test is acknowledged in [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]].

### Step 6 — PRODUCE

Per tier (Expert/Capable/Flagship-local/Lightweight/Direct), context rendered at appropriate depth via `fleet/core/tier_renderer.py`. Same structural skeleton at every tier — only content depth varies. This IS brain's [[Tier-Based Context Depth — Trust Earned Through Approval Rates]] pattern (one of the 7 patterns brain already extracted from OpenFleet).

### Step 7 — TRACK

L3 PM integration via `fleet/cli/plane.py` (402L). Backlog readiness/progress partially tracked in frontmatter. Gap: readiness and progress are not yet split into two independent dimensions per brain's spec — single `readiness` field conflates them. See [[Operational Depth Gaps — What Structural Compliance Doesn't Measure]] for the schema-change roadmap.

### Step 8 — FEEDBACK

`kb_sync.py` (851L at `fleet/core/`) aggregates fleet operational data. `gateway contribute` writes lessons back to brain (5 contributions pending-review as of 2026-04-18). Evolution pipeline in the brain scores fleet-generated content alongside human-generated content.

## Walkthrough C Claims vs Ground Truth

The brain's description of OpenFleet in goldilocks-flow.md was ground-truthed 2026-04-17. Full correction filed to brain. Summary:

| Claim | Verdict | Verified at |
|-------|---------|-------------|
| `doctor.py (24 rules)` | ✅ exists | `fleet/core/doctor.py` (679L, 18 top-level fns; "24 rules" not directly countable by naming pattern) |
| `1033-line MCP validator` | ❌ incorrect | No file matches that description. `fleet/mcp/tools.py` is 3,915L — much larger. No separate validator file. |
| `kb_sync.py + LightRAG` | ✅ exists | `fleet/core/kb_sync.py` (851L); `scripts/setup-lightrag.sh`; `scripts/lightrag-index.sh` |
| `Plane integration bidirectional` | ✅ exists (direction not verified) | `fleet/cli/plane.py` (402L) |
| `per-agent AGENTS.md` | ⚠️ migration in progress | 10 live agents retain `AGENTS.md`; `_template/` migrated to `WORKSPACE.md` (2026-04-17) per Three-Layer Agent Context Architecture. Live agents pending. |
| `stage-files.log` | ❌ not found | No file by that name. Likely cross-project conflation with OpenArms. |
| Tier-based context depth (Expert/Capable/Lightweight) | ✅ matches (simplification) | Our 5-tier config (`config/tier-profiles.yaml`); brain's 3-tier description is accurate simplification. |

## OpenFleet's Declared Goldilocks Position

> [!info] As of 2026-04-18
>
> **Stable (project-level, in CLAUDE.md):** Type=system, Domain=mixed, Phase=production, Scale=large, Second-Brain=connected
>
> **Runtime (consumer-declared at connect time, NOT in CLAUDE.md):** Execution Mode, PM Level, Trust Tier, SDLC Profile
>
> **Fleet-runtime typical dispatch (example consumer values for a dispatched agent):** Execution Mode=full-system, PM Level=L3, Trust Tier=data-driven (per approval rate per agent per task type), SDLC Profile=Full
>
> **Solo-on-main typical (example consumer values for this CLAUDE.md session):** Execution Mode=solo, PM Level=L1, Trust Tier=operator-supervised, SDLC Profile=default

## Relationships

- PART OF: [[Ecosystem]]
- BUILDS ON: [[OpenFleet — Identity Profile]]
- BUILDS ON: [[Sister Project Map — OpenFleet Ecosystem Relationships]]
- RELATES TO: [[Methodology Models Rationale]]
- RELATES TO: [[Tier Rendering Design Rationale]]
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- FEEDS INTO: brain's Walkthrough C (pending brain-side update from 2026-04-17 correction)
