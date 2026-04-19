---
title: "RAG/Knowledge System (LightRAG)"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [rag, lightrag, knowledge-base, memory, indexing, persistence, fleet-compose]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# RAG/Knowledge System (LightRAG)

## Summary

Integrate LightRAG as the fleet's knowledge graph system. Build indexing processes, connect to Claude Code and LocalAI, create persistent knowledge bases that survive Docker purges, and enable sharing research, FAQs, PM documents, and artifacts into a structured RAG mesh.

> "I also want to look to integrate https://github.com/hkuds/lightrag as part of ocmc... there is a basic Memory / Knowledge base collection control but lightrag bring another level, another depth to it and a full UI."

> "Imagine I make research on Shaders, then I would wanna share my research there. Imagine I have FAQs / Frequent Confusions / Front Facing doc or information about the other projects or tools and their usages. Imagine sharing the Plane / PM documents & artifacts into this properly structured RAG. to have a view. a mesh of everything."

> "we would also need to make sure that those Memories / Knowledge Base Collections would persist as I purge all the docker, constantly saving itself to IaC to not be lost so that when I make again it hasn't lost anything."

> "we are going to prepare the fleet compose with now lightRAG and create our indexing process that we will also integrate into the setup. we will then connect this to our claude code and setup the plugins and do the same and test the quality of the environment and the MAP(s)."

## Goals

- Add LightRAG to fleet Docker compose
- Build indexing process for fleet documentation, system docs, Plane artifacts
- Ensure KB persistence through Docker purge (IaC backup/restore)
- Connect to Claude Code agents via MCP or plugin
- Connect to LocalAI when available (dual backend)
- Enable cross-project knowledge sharing (fleet, AICP, DSPD, NNRT)
- Build multiple overlapping maps that aggregate

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Add LightRAG to fleet Docker compose
- [ ] Build indexing process for fleet documentation, system docs, Plane artifacts
- [ ] Ensure KB persistence through Docker purge (IaC backup/restore)
- [ ] Connect to Claude Code agents via MCP or plugin
- [ ] Connect to LocalAI when available (dual backend)
- [ ] Enable cross-project knowledge sharing (fleet, AICP, DSPD, NNRT)
- [ ] Build multiple overlapping maps that aggregate

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Research Needed

- LightRAG's current API and integration patterns (OpenSearch backend, March 2026)
- RAG-Anything multi-modal extension
- How claude-mem and LightRAG complement each other
- LocalAI's memory/collection features vs LightRAG
- Persistence patterns for Docker environments (volume mounts, IaC export)

## Phases

### Phase 0: Document & Research

- [ ] Deep research on LightRAG current state (post March 2026 updates)
- [ ] Document LocalAI memory/collection features and compare
- [ ] Document claude-mem's persistence model and how it complements LightRAG
- [ ] Design the knowledge architecture: what goes in LightRAG vs claude-mem vs wiki
- [ ] Document IaC persistence requirements

### Phase 1: Design

- [ ] Design fleet compose addition (LightRAG service)
- [ ] Design indexing pipeline (what gets indexed, how, when)
- [ ] Design persistence/backup strategy (survives Docker purge)
- [ ] Design MCP integration for agent access
- [ ] Design the map structure (multiple maps, overlap, aggregation)

### Phase 2: Scaffold

- [ ] Add LightRAG to docker-compose.yaml
- [ ] Create scripts/setup-lightrag.sh (IaC)
- [ ] Create indexing script skeleton
- [ ] Create backup/restore scripts

### Phase 3: Implement

- [ ] Deploy LightRAG in fleet compose
- [ ] Implement indexing for fleet system docs
- [ ] Implement indexing for Plane documents (when connected)
- [ ] Implement persistence/backup to IaC
- [ ] Connect to agent MCP (lightrag MCP server)
- [ ] Connect to LocalAI when available

### Phase 4: Test & Validate

- [ ] Test indexing produces correct knowledge graph
- [ ] Test agent can query LightRAG through MCP
- [ ] Test persistence survives Docker purge
- [ ] Test cross-project knowledge queries
- [ ] Evaluate retrieval quality vs direct file reading

## Existing Foundation

- devops-solutions-research-wiki/ — LLM wiki pattern already running
- fleet/infra/config_loader.py — YAML config loading
- Docker compose infrastructure (MC, Plane already containerized)
- LocalAI integration (AICP project)
- claude-mem plugin (cross-session memory)

## Relationships

- ENABLES: [[Autocomplete Web / Map Net]] (LightRAG feeds the map net)
- ENABLES: [[Brain Evolution]] (brain consumes LightRAG for knowledge-aware dispatch)
- RELATES TO: [[IaC & Persistence]] (KB must survive purges)
- RELATES TO: [[Multi-Model Strategy]] (LocalAI provides embeddings)
- RELATES TO: [[Plugin/Skill/Command Ecosystem]] (LightRAG MCP server)
- RELATES TO: [[Claw Code Parity Research]] (AICP hosts LocalAI for embeddings)
