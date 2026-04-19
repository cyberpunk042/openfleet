---
title: "IaC & Persistence"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [iac, persistence, docker, backup, kb, setup, lightrag, compose]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# IaC & Persistence

## Summary

Knowledge base and memory persistence through Docker purge. Constant IaC backup so nothing is lost. Setup integration for all new services (LightRAG, plugins, skill packs). When you `make again`, everything comes back — no data loss, no manual steps.

> "we would also need to make sure that those Memories / Knowledge Base Collections would persist as I purge all the docker, constantly saving itself to IaC to not be lost so that when I make again it hasn't lost anything."

> "we are going to prepare the fleet compose with now lightRAG and create our indexing process that we will also integrate into the setup. we will then connect this to our claude code and setup the plugins and do the same and test the quality of the environment and the MAP(s)."

> "Its important to declare that the kB are not set in stone and things can update. and its important to have multiples map that can all overlap, connect and aggregate. Its a paths and travels problem."

## Goals

- All fleet state persists through Docker purge (volumes, IaC export, git-tracked config)
- LightRAG KB data backed up to IaC automatically
- claude-mem data survives purge (SQLite file in git-tracked location)
- Board memory exportable and restorable
- Agent session data (context/, artifacts) backed up before purge
- Fleet compose includes all services (MC, LightRAG, IRC, Plane)
- setup.sh restores full state from IaC — zero data loss

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] All fleet state persists through Docker purge (volumes, IaC export, git-tracked config)
- [ ] LightRAG KB data backed up to IaC automatically
- [ ] claude-mem data survives purge (SQLite file in git-tracked location)
- [ ] Board memory exportable and restorable
- [ ] Agent session data (context/, artifacts) backed up before purge
- [ ] Fleet compose includes all services (MC, LightRAG, IRC, Plane)
- [ ] setup.sh restores full state from IaC — zero data loss

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- setup.sh — 17-step master orchestration (from zero to running fleet)
- Docker compose for MC (compose.yml in vendor/)
- scripts/setup-lightrag.sh — LightRAG setup (background knowledge sync)
- .aicp/state.yaml — setup state persistence
- config/ — all YAML configs git-tracked
- agents/_template/ — agent templates git-tracked
- patches/ — vendor patches survive git clone

## Phases

### Phase 0: Document & Research

- [ ] Audit what data is ephemeral vs persistent today
- [ ] Audit Docker volume mounts — what survives `docker compose down -v`?
- [ ] Document LightRAG storage model (OpenSearch? local files? volumes?)
- [ ] Document claude-mem storage (SQLite path, git-tracked?)
- [ ] Map board memory export/import capabilities

### Phase 1: Design

- [ ] Design persistence strategy per data type (KB, memory, context, artifacts, board)
- [ ] Design IaC backup scripts (automatic, cron-based, before purge)
- [ ] Design fleet compose expansion (MC + LightRAG + IRC + monitoring)
- [ ] Design restore-from-IaC sequence (setup.sh imports backed-up data)

### Phase 2: Implement

- [ ] Build backup scripts per data type
- [ ] Expand docker-compose.yaml with all services
- [ ] Wire backup into setup.sh (backup before teardown, restore after build)
- [ ] Wire LightRAG persistence (volume mounts, IaC export)
- [ ] Wire claude-mem persistence

### Phase 3: Test & Validate

- [ ] Test full purge + rebuild cycle — verify zero data loss
- [ ] Test LightRAG KB survives purge
- [ ] Test board memory restored correctly
- [ ] Test setup.sh from fresh clone reproduces full state

## Relationships

- RELATES TO: [[RAG/Knowledge System (LightRAG)]] (LightRAG persistence is here)
- RELATES TO: [[Plugin/Skill/Command Ecosystem]] (plugin/skill installation must be repeatable)
- ENABLES: [[Full Autonomous Mode]] (autonomous fleet can't lose data on restart)
- ENABLES: [[Federation & Multi-Fleet]] (federation config must persist)
- RELATES TO: [[Signatures & Transparency]] (provenance must survive purge)
- RELATES TO: [[Config Evolution]] (config is a persistence concern)
