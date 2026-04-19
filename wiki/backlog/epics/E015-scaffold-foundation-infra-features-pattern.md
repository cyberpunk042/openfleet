---
title: "Scaffold→Foundation→Infra→Features Pattern"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [scaffold, foundation, infrastructure, features, skyscraper, methodology, pattern, order]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Scaffold→Foundation→Infra→Features Pattern

## Summary

The repeated pattern at every level of building. Scaffold is the basics (config, structure, stack). Foundation is the spine (modules, design system, architecture docs). Infrastructure is building on the foundation. Features are the special capabilities. The skyscraper vs pyramid vs mountain analogy. This pattern applies to tasks, epics, projects, and the fleet itself.

> "There is also the very important notion of the order of things and the repeated scaffold, foundation, infrastructure, features chain of evolution and design and engineering. This is important because it apply to almost any domain and any task when you think about it"

> "Scaffolding is just the basics: the core configuration files, the project structure, the technology stack... Foundation is about choosing the modules/packages, design system, project spine/column structure, diagrams, and architecture documents... Infrastructure is where you build on the foundation... Features are usually the special features of your product"

> "To build a skyscraper like we aim or any decent building or construction or product, there is always an order. We love the skyscraper analogy, we use it into the systems-course. its about the ideal being the skyscraper and the pyramid being the compromise between it and the mountain which is the spaghetti and deprecated patterns and solutions."

## Goals

- Codify the scaffold→foundation→infrastructure→features progression in methodology
- Agents understand which phase their task belongs to and what standards apply
- PM uses this pattern when breaking epics into work
- Architect uses this when designing systems
- Engineer follows the order when implementing
- The fleet itself follows this pattern in its own evolution (E001-E017 follow this order)

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Codify the scaffold→foundation→infrastructure→features progression in methodology
- [ ] Agents understand which phase their task belongs to and what standards apply
- [ ] PM uses this pattern when breaking epics into work
- [ ] Architect uses this when designing systems
- [ ] Engineer follows the order when implementing
- [ ] The fleet itself follows this pattern in its own evolution (E001-E017 follow this order)

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- config/phases.yaml — delivery phases (idea→conceptual→poc→mvp→staging→production) — related but not the same pattern
- config/methodology.yaml — 5 methodology stages (conversation→work) — task execution, not delivery pattern
- fleet-elevation/15 — synergy matrix implies contribution ordering
- path-to-live.md — 8 phases (A-H) follow scaffold→foundation→features implicitly

## Phases

### Phase 0: Document & Research

- [ ] Document how the pattern manifests in current fleet work
- [ ] Map path-to-live phases to scaffold/foundation/infra/features
- [ ] Identify where agents currently skip stages (building features on no foundation)

### Phase 1: Design

- [ ] Design how the pattern integrates into task metadata (custom field? tag? phase attribute?)
- [ ] Design PM guidance for applying the pattern to epic breakdown
- [ ] Design architect guidance for phase-appropriate architecture depth
- [ ] Document the skyscraper/pyramid/mountain analogy for agent context

### Phase 2: Implement

- [ ] Add pattern awareness to PM skills (fleet-epic-breakdown)
- [ ] Add pattern awareness to architect skills (fleet-design-contribution)
- [ ] Wire pattern into Navigator intent-map for stage recommendations

### Phase 3: Test & Validate

- [ ] Test PM applies pattern when breaking epics
- [ ] Test architect references pattern in design input
- [ ] Validate pattern doesn't add overhead on small tasks

## Relationships

- RELATES TO: [[Agent Directive Chain Evolution]] (pattern awareness in agent files)
- RELATES TO: [[Brain Evolution]] (brain can use pattern to prioritize work)
- RELATES TO: [[Config Evolution]] (phases and patterns are complementary concepts)
