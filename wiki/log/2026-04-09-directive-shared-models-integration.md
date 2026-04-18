---
title: "Directive: Integrate Shared Models (LLM Wiki + Methodology)"
type: note
domain: log
status: active
note_type: directive
created: 2026-04-09
updated: 2026-04-09
tags: [directive, methodology, llm-wiki, shared-models, vision, integration, modes, PO]
confidence: medium
sources: []
---

# Directive: Integrate Shared Models (LLM Wiki + Methodology)

## Summary

PO directive to integrate two foundational shared models from the research wiki (LLM Wiki + Methodology) into OpenFleet as the standard ecosystem vocabulary. The models apply at four levels — solo / assistant / fleet / full-platform — with the context injection system as the delivery mechanism for methodology model instances. Integration means adopting shared vocabulary where it aligns, evolving methodology.yaml from one model to multiple named models, and treating OpenFleet's validation matrix as test suite for methodology-model context injection.

## PO Directives (Verbatim)

> "Its not perfect yet but its a good start to a shared vision. soon we will have models for everything and at least one super-model"

> "it fits at all level. solo, Assistant, Assistants Fleet / Assistant Fleet Full Platform"

> "things just overlap and become more naturally. no need to force things but at the same times I am not saying it makes things simpler... for things to become simple in programming they have to become complex first"

> "we will adhere to the vision that there are multiple operation modes and multiple settings possible and current the way we work is in semi-autonomous and the default workspace mode"

> "I would not overwhelm my trainee"

> "its time we start integrating the Wiki LLM model and methodology model"

## Context

During the context injection tree work (E001), the PO directed integration of two foundational models from the research wiki (`devops-solutions-research-wiki/wiki/spine/`):

1. **model-llm-wiki.md** — defines what a wiki IS (16 page types, YAML frontmatter, typed relationships, quality gates, density layers, three operations)
2. **model-methodology.md** — the super-model defining how ALL work proceeds (9+ named models, multi-dimensional selection, 4 composition modes, 3 parallel tracks, quality dimension, recursive at every scale)

Supporting pages: Methodology Framework, Task Type Artifact Matrix, Execution Modes and End Conditions, Backlog Hierarchy Rules.

## Interpretation

The shared models apply at FOUR levels:
- **Solo** — a coding session (like this one) follows a methodology model
- **Assistant** — a single OpenArms agent follows methodology.yaml + agent-directive.md
- **Fleet** — 10 OpenFleet agents each run their own methodology model instances simultaneously
- **Full Platform** — OpenFleet + OpenArms + AICP + DSPD + Plane all share the same framework vocabulary

OpenFleet already implements many shared model concepts under different names. The integration is about:
- Adopting shared vocabulary where it aligns
- Evolving methodology.yaml from one model to multiple named models
- Making the context injection system the delivery mechanism for methodology model instances
- Treating capability tiers as the quality dimension (expert=skyscraper, lightweight=pyramid)
- Not forcing — letting the overlaps become natural

The PO explicitly stated this is progressive, not a sudden rewrite. The models are "not perfect yet" and "a good start."

## Relationships

- FEEDS INTO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- FEEDS INTO: [[Methodology Models Rationale]]
- FEEDS INTO: [[Tier Rendering Design Rationale]]
- FEEDS INTO: [[Integration Chain Mapping — OpenFleet Position 2026-04-18]]
- FEEDS INTO: [[OpenFleet in the Goldilocks Ecosystem — Walkthrough C Reconciled]]
- RELATES TO: [[Directive: Five Documentation Layers]]
- RELATES TO: [[Directive: OpenFleet Has Two Methodologies (Intentional)]]
