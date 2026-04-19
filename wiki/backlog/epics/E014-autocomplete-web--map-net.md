---
title: "Autocomplete Web / Map Net"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [autocomplete, map, metadata, rag-map, knowledge, navigation, navigator, intent-map, injection]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Autocomplete Web / Map Net

## Summary

The most advanced metadata and maps net. Multiple maps that overlap, connect, and aggregate. A RAG Map that acts as a magic book unlocking knowledge about the self and systems in all layers. Shrink knowledge down so injections adapt to model capacity. A paths and travels problem — the autocomplete web organically accesses the right branches and leaves.

> "We are going to create the most advanced and sophisticated metadata and maps net in order to create our own autocomplete web that organically and very easily access the right branches and leaves of the tree."

> "Imagine all the notions about the systems, the knowledges, the functioning of the fleet and the agents and brought together and then cross-referenced and associated with a map file, like for javascript or similar language in order to create a virtual map of this / those said trees, now not only the things we defined and the directives and dynamic content is present, there is also and RAG Map that is like a manual / a magic book that unlock the knowledge about the self and the system(s) in all its layer, and the modules and everything shrinked down so that we can adapt the injections."

> "things you could never inject into a cheap model for example but could still be strategically integrated into the feed as per still what is present and the map act as a facilitator with clear intents. it also help any conversation / agent feed in general but this goes in pair with the memory idea and then the RAG idea and the lightRAG and the dynamic files and pre-embedding and injections."

> "Its important to declare that the kB are not set in stone and things can update. and its important to have multiples map that can all overlap, connect and aggregate. Its a paths and travels problem. Once its there its about trying to go through those paths and find the right travel."

## Current State — More Foundation Than Expected

The Navigator system already exists (1087 lines in fleet/core/navigator.py) and is wired into the orchestrator's 30s refresh cycle. The metadata layer exists:

| Component | Status | Size |
|-----------|--------|------|
| intent-map.yaml | 33/80 intents (41%) | 322 lines |
| injection-profiles.yaml | 4 tiers (opus/sonnet/localai/heartbeat) | 6.3K |
| cross-references.yaml | 20 systems mapped | 14.7K |
| agent-manuals.md | All 10 agents | 24.2K |
| module-manuals.md | 94 modules | 53K |
| system-manuals (3 depths) | full/condensed/minimal | 14.6K + 6.4K + condensed |
| methodology-manual.md | 5 stages | 12.2K |
| standards-manual.md | 8 standards | 19.6K |
| KB directory | 13 subdirectories | ~50+ files |

The Navigator reads all of this and assembles per-agent context into knowledge-context.md. The brain writes it every 30s.

See: [wiki/domains/architecture/navigator-intent-gap-analysis.md](../../domains/architecture/navigator-intent-gap-analysis.md)

## Goals

- Fill 19 missing Navigator intents (P1: 8, P2: 7, P3: 4)
- Add pack skills (superpowers, ring, trailofbits) to ALL intents
- Add sub-agent recommendations to relevant intents
- Connect LightRAG for graph-based knowledge queries (entity relationships)
- Connect claude-mem for agent-specific cross-session observations
- Build the indexing process that populates LightRAG from fleet docs
- Create multiple overlapping maps (system map, role map, task map, knowledge map)
- Adapt injection depth per model capacity (opus: full, sonnet: condensed, localai: minimal)
- Make the map a living system — updates as fleet docs and code change

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Fill 19 missing Navigator intents (P1: 8, P2: 7, P3: 4)
- [ ] Add pack skills (superpowers, ring, trailofbits) to ALL intents
- [ ] Add sub-agent recommendations to relevant intents
- [ ] Connect LightRAG for graph-based knowledge queries (entity relationships)
- [ ] Connect claude-mem for agent-specific cross-session observations
- [ ] Build the indexing process that populates LightRAG from fleet docs
- [ ] Create multiple overlapping maps (system map, role map, task map, knowledge map)
- [ ] Adapt injection depth per model capacity (opus: full, sonnet: condensed, localai: minimal)
- [ ] Make the map a living system — updates as fleet docs and code change

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Document & Research

- [x] Audit Navigator coverage — 33/80 intents, 41%
- [x] Identify 19 missing intents by priority
- [x] Document pack skill gaps in intents (zero pack skills referenced)
- [ ] Research LightRAG current API for graph queries
- [ ] Research claude-mem search capabilities for Navigator integration
- [ ] Document what "multiple overlapping maps" means concretely
- [ ] Audit KB content quality and completeness

### Phase 1: Design

- [ ] Design the 19 missing intents with pack skills and sub-agent recommendations
- [ ] Design LightRAG integration in Navigator (query format, response handling)
- [ ] Design claude-mem integration in Navigator (per-agent observations)
- [ ] Design the indexing pipeline (what gets indexed, frequency, triggers)
- [ ] Design map overlap architecture (how system map + role map + knowledge map connect)
- [ ] Design injection adaptation algorithm (model capacity → depth selection)

### Phase 2: Implement

- [ ] Add 19 missing intents to intent-map.yaml
- [ ] Add pack skills to all intents (existing + new)
- [ ] Wire LightRAG graph queries into Navigator.assemble()
- [ ] Wire claude-mem observations into Navigator.assemble()
- [ ] Build indexing pipeline for LightRAG (scripts/index-knowledge.sh)
- [ ] Test Navigator output for all 10 roles × relevant stages

### Phase 3: Test & Validate

- [ ] Verify Navigator delivers useful context for every role×stage
- [ ] Verify injection depth adapts correctly per model
- [ ] Verify LightRAG queries return relevant context
- [ ] Verify TOOLS.md redesign works WITH Navigator enrichment
- [ ] Verify agents perform better with Navigator context vs without

## Existing Foundation

- fleet/core/navigator.py — 1087 lines, core autocomplete web assembly
- docs/knowledge-map/ — intent-map, profiles, cross-references, 8 content files, KB with 13 dirs
- fleet/core/context_writer.py — writes knowledge-context.md per agent
- Orchestrator Step 0 — calls Navigator.assemble() every 30s cycle
- LightRAG MCP server — commented out in agent-tooling.yaml (needs LocalAI)
- claude-mem plugin — configured for all agents (not installed yet)

## Relationships

- BUILDS ON: [[RAG/Knowledge System (LightRAG)]] (LightRAG provides graph backend)
- BUILDS ON: [[Plugin/Skill/Command Ecosystem]] (pack skills feed into intents)
- ENABLES: [[Agent Directive Chain Evolution]] (TOOLS.md redesign trusts Navigator delivery)
- ENABLES: [[Brain Evolution]] (brain's context refresh drives Navigator)
- ENABLES: [[Full Autonomous Mode]] (agents need focused, adaptive context for autonomous work)
- RELATES TO: [[IaC & Persistence]] (knowledge map and LightRAG must persist)
- RELATES TO: [[Navigator Intent-Map Gap Analysis]]
- RELATES TO: [[Navigator Intent-Map Expansion — 19 Missing Intents + Pack Skills]]
- RELATES TO: [[Context Injection Decision Tree]]
