---
title: "Path-to-Live Reconciliation — Where We Are"
type: reference
domain: planning
status: active
created: 2026-04-09
updated: 2026-04-09
tags: [planning, reconciliation, path-to-live, epics, status, progress]
sources:
  - id: path-to-live
    type: documentation
    file: docs/milestones/active/path-to-live.md
  - id: index
    type: documentation
    file: wiki/backlog/_index.md
confidence: medium
---

# Path-to-Live Reconciliation — Where We Are

## Summary

Reconciliation of two parallel plans toward fleet-live operation: the original path-to-live.md (24 operational steps across 8 phases A-H, focused on infrastructure + provisioning) and the evolving methodology-integration plan (second-brain adoption + context injection + validation matrix). Names overlaps, divergences, and the single merged sequence.

## Two Plans, One Goal

**path-to-live.md** (2026-04-02) — 24 operational steps across 8 phases (A-H) to reach fleet live operation. Focused on fixing blockers, building agent files, wiring brain modules.

**wiki/backlog/ 17 epics** (2026-04-08) — PO evolution vision. Broader scope: RAG, multi-model, federation, autocomplete web, autonomous mode. Subsumes and extends path-to-live.

This document maps path-to-live steps to epics and marks what's done.

## Phase A: Foundation (Steps 1-4)

| Step | What | Epic | Status |
|------|------|------|--------|
| **1. Fix Gateway Injection** | executor.py reads all 8 files, fix char limits | E001 | **DONE** — executor.py fixed to 20K/file, 150K total, .env configurable, bloat warnings |
| **2. Fix Stage Gating** | fleet_commit allowed in stages 2-5, not just work | E001 | **DONE** — methodology.yaml correctly blocks fleet_commit ONLY in conversation. Analysis/investigation/reasoning/work all allow it. MCP enforcement is config-driven via _check_stage_allowed() |
| **3. Build IaC Scripts** | provision-agents.sh, setup-agent-tools.sh, install-plugins.sh, generate scripts, validate-agents.sh | E001, E007 | **DONE** — generate-tools-md.py rewritten, generate-agents-md.py verified, provision-agent-yaml.py built, validate-agents.sh enhanced (339/340 pass). install-plugins.sh needs gateway |
| **4. Deploy Ecosystem Tier 1** | Prompt caching, Claude-Mem, Context7, Filesystem MCP | E007 | **NOT DONE** — configured in agent-tooling.yaml but needs gateway running to install |

## Phase B: Agent Identity (Steps 5-9)

| Step | What | Epic | Status |
|------|------|------|--------|
| **5. agent.yaml ×10** | 14 required fields, fleet identity, roles | E001 | **DONE** — provision-agent-yaml.py generates all 14 fields from config. fleet_id, roles, heartbeat_config, capabilities all set |
| **6. IDENTITY.md + SOUL.md ×10** | Inner layer files, anti-corruption rules | E001 | **DONE** — 10 IDENTITY.md (1.4-2.7K, fleet refs), 10 SOUL.md (2.6-3.6K, 9 anti-corruption rules each) |
| **7. CLAUDE.md ×10** | 8 sections, 4000 chars max, per-role | E001 | **DONE** — all 10 rewritten to standard (2.9-3.7K, 8 sections, role-specific) |
| **8. HEARTBEAT.md ×5** | 5 types, universal priority order | E001 | **DONE** — all 11 rewritten (PM, fleet-ops, architect, devsecops, worker + 6 variants) |
| **9. Generate TOOLS.md + AGENTS.md ×10** | IaC generation from config | E001 | **DONE** — TOOLS.md 77% reduction (167K→38K), AGENTS.md verified (3.4-4.5K) |

## Phase C: Brain Evolution (Steps 10-14)

| Step | What | Epic | Status |
|------|------|------|--------|
| **10. Autocomplete Chain Builder** | autocomplete.py, context_writer update | E001, E014 | **DONE** — preembed.py rewritten to 10-section autocomplete chain standard (identity→task→stage→readiness→verbatim→protocol→contributions→phase→action→consequences). Navigator (45 intents) assembles knowledge-context.md. context_writer writes 3 files |
| **11. Trail Recorder** | trail_recorder.py, trail events in MCP tools | E002, E009 | **DONE** — trail_recorder.py (292 lines, 34 event types, completeness checking). Wired into orchestrator dispatch + contribution creation. PostToolUse hook also records trail |
| **12. Wire Fleet Settings** | backend_mode→router, budget_mode→tempo, CRON sync | E003, E006 | **NOT DONE** — settings exist in MC/OCMC but don't fully propagate to orchestrator dispatch decisions |
| **13. Enhance Pre-Embed Per Role** | role_providers.py update | E001 | **PARTIAL** — 6 role providers (PM, fleet-ops, architect, devsecops, workers with contribution awareness). Registry fixed. Missing: PM Plane sprint data, context % metrics |
| **14. Wire Session Telemetry** | session_telemetry.py adapter | E003 | **NOT DONE** — adapter exists (230 lines, 30 tests) but not wired into orchestrator |

## Phase D: First Live Test (Step 15)

| Step | What | Epic | Status |
|------|------|------|--------|
| **15. Minimum Viable Live Test** | Dispatch → agent works → review → approve → done | ALL | **NOT DONE** — 0 live tests. Requires gateway running, MC up, agent provisioned |

## Phase E: Cross-Agent Synergy (Steps 16-18)

| Step | What | Epic | Status |
|------|------|------|--------|
| **16. Contribution Flow** | fleet_contribute, fleet_request_input, brain auto-creates contributions | E003, E012 | **DONE** — contributions.py built, orchestrator Step 2.5 auto-creates contribution subtasks from synergy matrix, dispatch gate blocks work without required contributions |
| **17. Phase System** | fleet_gate_request, fleet_phase_advance, phases.yaml enforcement | E010 | **PARTIAL** — phases.yaml defined, fleet_gate_request/fleet_phase_advance MCP tools exist in tools.py, phase gate enforcement NOT in orchestrator |
| **18. Session Management** | session_manager.py, context countdowns, compaction strategy | E003, E008 | **NOT DONE** — spec exists but no implementation |

## Phase F: Full Lifecycle Test (Step 19)

| Step | What | Epic | Status |
|------|------|------|--------|
| **19. Full Lifecycle Test** | PM assigns → stages → contributions → work → review → done | ALL | **NOT DONE** — requires all previous phases |

## Phase G: Hardening (Steps 20-22)

| Step | What | Epic | Status |
|------|------|------|--------|
| **20. Brain Idle Evaluation** | heartbeat_gate.py evaluation in orchestrator | E003, E008 | **DONE** — brain_writer.py writes .brain-decision.json, heartbeat_gate.py evaluates wake/silent/strategic, orchestrator Step A runs every cycle |
| **21. Expand Disease Detections** | 7 missing doctor detections | E003 | **NOT DONE** — 4/11 implemented |
| **22. Readiness Regression + Cowork + Transfer** | 3 operational protocols | E010, E003 | **NOT DONE** |

## Phase H: Ecosystem & Optimization (Steps 23-24)

| Step | What | Epic | Status |
|------|------|------|--------|
| **23. Deploy Ecosystem Tier 2** | Per-agent MCP servers, skills, LocalAI RAG, Batch API | E007, E004, E005 | **NOT DONE** — ecosystem researched (1,100+ skills, 6 packs identified), configs ready, needs gateway |
| **24. 24-Hour Observation** | Fleet runs autonomously for 24h | E012 | **NOT DONE** — the endgame |

## Progress Summary

| Phase | Steps | Done | Partial | Not Done |
|-------|-------|------|---------|----------|
| A: Foundation | 4 | 3 | 0 | 1 |
| B: Agent Identity | 5 | 5 | 0 | 0 |
| C: Brain Evolution | 5 | 2 | 1 | 2 |
| D: First Live Test | 1 | 0 | 0 | 1 |
| E: Cross-Agent Synergy | 3 | 1 | 1 | 1 |
| F: Full Lifecycle Test | 1 | 0 | 0 | 1 |
| G: Hardening | 3 | 1 | 0 | 2 |
| H: Ecosystem | 2 | 0 | 0 | 2 |
| **TOTAL** | **24** | **12** | **3** | **9** |

**12 done, 3 partial, 9 remaining.** ~52% complete by step count.

## Critical Path to First Live Test (Step 15)

To reach the minimum viable live test, these must be done:

| Blocking Step | Status | What Remains |
|---------------|--------|-------------|
| 1. Gateway injection | DONE | — |
| 2. Stage gating | DONE | Verified: config-driven, conversation-only block |
| 3. IaC scripts | PARTIAL | Verify provision/install/validate scripts work |
| 4. Ecosystem Tier 1 | BLOCKED | Needs gateway running |
| 5. agent.yaml | NOT DONE | Add fleet_id, roles, capabilities per standard |
| 6. IDENTITY+SOUL | DONE | — |
| 7. CLAUDE.md | DONE | — |
| 8. HEARTBEAT.md | DONE | — |
| 9. TOOLS.md+AGENTS.md | DONE | — |
| 10. Autocomplete chain | PARTIAL | Navigator works, needs autocomplete.py ordering |
| 11. Trail recorder | PARTIAL | Hook-based trail exists, needs module |
| 12. Wire settings | NOT DONE | backend_mode, budget_mode propagation |
| 13. Enhance pre-embed | PARTIAL | Role providers exist, need Plane/completeness data |
| 14. Session telemetry | NOT DONE | Adapter exists, needs wiring |

**Minimum path to Step 15:** Complete steps 2, 3, 5, 10-14. Steps 4 needs gateway. Steps 10-14 are Phase C brain work.

## What the Epics Add Beyond Path-to-Live

| Epic | Beyond Path-to-Live |
|------|-------------------|
| E004 (LightRAG) | Knowledge graph, persistent KB, indexing pipeline |
| E005 (Multi-Model) | Codex adversarial reviews, MiMo, Qwen, TurboQuant |
| E007 (Ecosystem) | 1,100+ skills from 6 packs, full plugin deployment |
| E014 (Autocomplete Web) | Multiple overlapping maps, RAG map, knowledge navigation |
| E015 (S→F→I→F Pattern) | Methodology pattern at every level |
| E016 (Claw Code Parity) | AICP LocalAI independence features |
| E017 (Federation) | Multi-fleet, shared Plane, agent namespacing |

These are EVOLUTION beyond the live fleet baseline. Path-to-live gets the fleet running. Epics make it intelligent, knowledgeable, independent, and scalable.

## Relationships

- RELATES TO: [[Wiki Structure Gaps — LLM Wiki Model Alignment]]
- RELATES TO: [[OpenFleet — Identity Profile]]
- FEEDS INTO: all epics E001-E017 (work ordering)
