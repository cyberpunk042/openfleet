---
title: "Operational Depth Gaps — What Structural Compliance Doesn't Measure"
type: reference
domain: planning
status: active
created: 2026-04-18
updated: 2026-04-18
tags: [planning, operational-depth, structural-compliance, gaps, adherence, brain-integration]
confidence: high
sources:
  - id: brain-principle-declarations
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/lessons/04_principles/hypothesis/declarations-are-aspirational-until-infrastructure-verifies-them.md
    title: "Principle — Declarations Are Aspirational Until Infrastructure Verifies Them"
  - id: brain-structural-vs-operational
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/lessons/02_synthesized
    title: "Structural Compliance Is Not Operational Compliance"
  - id: session-2026-04-17
    type: documentation
    file: docs/milestones/active/session-handoff-2026-04-17.md
    title: "Session Handoff 2026-04-17"
---

# Operational Depth Gaps — What Structural Compliance Doesn't Measure

## Summary

OpenFleet has achieved Tier 4/4 STRUCTURAL adoption per the brain's compliance checker. Operationally we're closer to Tier 2+ — the structural declaration is aspirational until the gaps below are closed. This page catalogues the operational debt, distinguishes it from structural compliance, names the infrastructure gate each gap needs, and assigns priorities for closure. Directly applies brain's [[declarations-are-aspirational-until-infrastructure-verifies-them|Principle 4 — Declarations Aspirational Until Infrastructure Verifies]] at the compliance-measurement layer (Instance #5 in the brain's 5-layer evidence chain for that principle).

## Why This Page Exists

The brain's `gateway compliance` command reports Tier 4/4. That measurement is correct: structural files exist (CLAUDE.md, wiki-schema.yaml, methodology.yaml, lessons/patterns/decisions dirs, export-profiles, .mcp.json). But a structural checker CANNOT verify operational depth — how faithfully the structure is USED, how current the content is, how many pages actually meet the standards they declare.

This is not a criticism of the compliance checker. Per brain's own labeling, the command is `Super-Model Compliance`, not `Operational Depth Audit`. The label prevents consumers from misreading structural presence as operational rigor. This page makes operational depth explicit so it's not invisible.

## Gap Categories

### Frontmatter-level gaps

| Gap | Current | Target | Gate needed |
|-----|---------|--------|------------|
| Readiness / progress separation | Single `readiness` field | Two independent 0-100 fields per brain spec | Schema update (PO approval); all backlog frontmatter migration |
| Impediment-type systematic use | Not applied | Enum (technical/dependency/decision/environment/clarification/scope/external/quality) on blocked tasks | Frontmatter requirement for `status: blocked` tasks |
| Maturity lifecycle on lessons/patterns/decisions | `maturity: seed` on our 1 lesson | seed → growing → mature → canonical with promotion criteria per maturity folder | Authoring discipline + promotion review cadence |
| Sources field completeness | Many pages have empty `sources: []` | ≥1 source with type + url/file per page | Author-time checklist; lint rule that flags empty sources for non-index types |

### Domain-population gaps

| Domain | Page count | Target | Notes |
|--------|-----------|--------|-------|
| architecture | ~26 | healthy — domain is mature | no gap |
| log | 8 | ≥3 | no gap |
| backlog | 17+ | ≥3 | no gap |
| **planning** | **3** (after this page) | **≥3** | threshold met with this page |
| **ecosystem** | **1** | **≥3** | `_index.md` exists but only identity-profile is content; needs 2 more pages |
| **cross-domain** | **1** (the `verify-before-contributing` lesson) | **≥3** | reserved-domain per our `domains.yaml`; either author 2+ more cross-domain principles/patterns or move the lesson to an active domain |

### Relationship-density gaps

| Metric | Current | Brain target | Notes |
|--------|---------|-------------|-------|
| Avg typed relationships per content page | ~2.2 | ≥6 for healthy pages | 23 of 54 pages have 0 typed relationships; all 17 epics have 0 relationships with brain-standard verbs |
| Cross-domain wikilinks | Many undercounted | ≥2 per small domain | Linter requires exact title match; em-dash titles and compound suffixes cause silent undercount |
| Backlink density (inbound links per page) | Not measured locally | Visible via brain's Obsidian graph | Would require running pipeline post + Obsidian sync to measure accurately |

### Content-quality gaps

| Gap | Scope | Target |
|-----|-------|--------|
| Thin pages (no Deep Analysis) | Several architecture pages | ≥100 words of Deep Analysis with ≥2 subsections per concept page |
| Unverified claims in existing pages | Audit not yet run | Every factual assertion sources-backed or `confidence: low` declared |
| Walkthrough C (brain's description of us) | 3 claims outdated/incorrect | Correction filed 2026-04-17, brain review pending |
| Stage-vocabulary alignment | 7 models × 6 stages (ours) vs 9 models × 5 stages (brain) | Either adopt brain vocabulary, or author a `wiki/config/methodology-profiles/openfleet.yaml` declaring our adaptation formally |

### Tool-level gaps

| Gap | Surface | Fix status |
|-----|---------|-----------|
| Gateway identity-parser fragility | Synonym headings ("Project Identity") silently fail | Remark filed to brain 2026-04-17; we renamed our heading to workaround |
| Forwarder contribute-target | `tools/gateway.py` forwarder used to route contribute to us | Fixed upstream in brain commit `154bc58` — contribute now defaults to `target=brain` |
| `pipeline scan ../openfleet/` staleness | Last run on older infrastructure | Needs re-run post-2026-04-17 restructure |
| Per-domain profile overrides | `wiki/config/domain-profiles/` has brain defaults | OpenFleet-specific overrides not authored |

## Prioritization

### P1 (foundational; blocks quality of everything downstream)

- Readiness / progress separation (frontmatter + backlog migration)
- Impediment-type adoption
- Stage-vocabulary declaration (either realign or declare our adaptation formally)

### P2 (close visible lint/compliance gaps)

- Author 2+ ecosystem-domain pages
- Author 2+ cross-domain principles or migrate the lesson out of cross-domain
- Relationship density pass on 23 zero-relationship pages
- Re-run `pipeline scan ../openfleet/` from brain side

### P3 (polish + compliance-checker accuracy)

- Migrate thin pages UP to concept/lesson/decision standards (not schema DOWN to pages — that's minimization)
- Fix linter title-matching so em-dash wikilinks count correctly (brain side)
- Per-domain profile overrides in `wiki/config/domain-profiles/`

## Principle Applied

> [!tip] This page is evidence for the Declarations-Aspirational principle
>
> The brain's Principle 4 says: any declaration downstream code trusts is aspirational until infrastructure verifies it. Our "Tier 4/4" compliance label IS such a declaration. Left alone, downstream consumers would read it as "operational depth Tier 4." This page is the counter-declaration: structural Tier 4, operational Tier 2+. The brain's checker is honest because it calls itself `Super-Model Compliance`, not `Operational Depth Audit`. This page is the honest counterpart on our side.
>
> The long-term fix is infrastructure: ship the operational-depth gaps ABOVE into specific lint rules, frontmatter requirements, and CI gates. Each gap that becomes a gate is a declaration that stops being aspirational. Each gap that stays unverified is a future source of false confidence.

## Relationships

- BUILDS ON: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- BUILDS ON: [[Path-to-Live Reconciliation — Where We Are]]
- DERIVED FROM: [[Verify Before Contributing to External Knowledge Systems]]
- RELATES TO: [[OpenFleet — Identity Profile]]
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Critical Review Findings — Context Injection Scenarios]]
- FEEDS INTO: future P1 work (readiness/progress, impediment-type, stage-vocabulary)
- CONSTRAINED BY: PO approval for schema and vocabulary changes
