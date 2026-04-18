---
title: "Directive: OpenFleet Has Two Methodologies (Intentional)"
type: note
domain: log
note_type: directive
status: active
created: 2026-04-17
updated: 2026-04-17
tags: [directive, methodology, configuration, platform, wiki, hybrid, two-level, PO]
confidence: medium
sources: []
---

# Directive: OpenFleet Has Two Methodologies (Intentional)

## Summary

PO clarification 2026-04-17 that OpenFleet's two-level configuration layout (`config/methodology.yaml` for fleet/platform, `wiki/config/methodology.yaml` for repo/wiki) is intentional architecture — not a gap requiring rename or unification. OpenFleet is a whole SYSTEM (fleet + platform + wiki), not only a wiki. The fleet runtime lives independently of the project-as-repo and has its own methodology already. Being a hybrid means having two levels of config: one for the wiki (like any project) and one for the platform / solution / full system.

## PO Directive (verbatim)

> "it was actually intentially that the second-brain would come pic them up but it seem it was too confusing so now when the seonc-brain is present we will contribute directly to it. it should already have ingested and processed and fixed"

> "of course there is two methodology... one is for the repo by default in solo agent + based of the repo and then if a harness start working on it in V2 its also using it, but the openfleet is a whole system. not only a wiki... the fleet live independed than the project and already has methodology itself.... it just mean that openfleet since its a whole system is going to have two level of config. for th wiki, like any project, and for the platform / solution / full system."

## Interpretation

### Two methodologies, two roles

| Config | Role | Consumers |
|--------|------|-----------|
| `wiki/config/methodology.yaml` (seeded from brain 2026-04-17) | Wiki/repo authoring methodology — how a solo agent or any harness working on THIS repo produces wiki content | Solo session (like this conversation) + any harness working on the repo |
| `config/methodology.yaml` (fleet runtime) | Platform/fleet methodology — how dispatched fleet agents execute their assigned tasks | Platform orchestrator + dispatched fleet agents |

### Why this is not a gap

A pure-wiki project has ONE methodology (wiki-authoring). A pure-platform project has ONE methodology (runtime). OpenFleet is BOTH — hence two. Treating the existence of both as "drift from brain's single-config layout" misreads brain's layout: brain is a pure wiki, so it has one config. Hybrid projects have two because they have two distinct consumer domains.

### Brain-contribution routing (separate clarification from same directive)

PO also clarified: originally, contributions filed via a consumer forwarder landed in the consumer's own log, and the brain was expected to pick them up later (pull model). That proved confusing. Now: when the brain is present, contribute directly to the brain. Brain has already been updated (commit `154bc58` on the brain's gateway.py — `op_contribute` now defaults `target="brain"` and writes to `paths["brain_wiki"]` unless `--target local` is passed). Consumer forwarders no longer need the fix on their side.

## Consequence for OpenFleet Structure

- `config/` at project root remains the fleet-runtime home (fleet.yaml, agent-identities.yaml, skill-stage-mapping.yaml, methodology.yaml, standing-orders.yaml, tier-profiles.yaml, tool-chains.yaml, etc.)
- `wiki/config/` at repo-wiki home (wiki-schema.yaml, artifact-types.yaml, domains.yaml, templates/, methodology-profiles/, sdlc-profiles/, domain-profiles/, mcp-runtime-values.yaml, sister-projects.yaml, contribution-policy.yaml, export-profiles.yaml, quality-standards.yaml, and now methodology.yaml).
- No rename or consolidation. The pattern is documented as [[Platform-Wiki Hybrid Two-Level Configuration]] for future reference and for sister-project recognition.

## Relationships

- FEEDS INTO: [[Platform-Wiki Hybrid Two-Level Configuration]]
- FEEDS INTO: [[Methodology Models Rationale]]
- FEEDS INTO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- RELATES TO: [[Sister Project Map — OpenFleet Ecosystem Relationships]]
