# Unified Implementation Plan — Waves 6-11

**Date:** 2026-03-31
**Status:** PLANNING — merging AR milestones with extension milestones
**Predecessor:** 47 strategic milestones (Waves 1-5, COMPLETE), 8 integration wires (COMPLETE)

---

## 1. The Problem

Two parallel milestone tracks were designed independently:
- **AR-01 to AR-20** — from agent-rework design docs (2026-03-30), based on 45 fleet elevation + agent-rework documents
- **M-AI01 to M-IP05** — from extension milestones (2026-03-31), based on PO requirements and research

These overlap, conflict, and leave gaps. This document merges them into a single unified plan.

---

## 2. Milestone Mapping

### Overlap (AR milestone covers same ground as extension milestone)

| AR Milestone | Extension Milestone | Resolution |
|---|---|---|
| AR-09: Update agent.yaml per agent | M-AI01: Agent Identity System | **Merge → U-01** — AR-09 spec is more detailed, drives implementation |
| AR-10: Per-agent CLAUDE.md | M-AI01: Agent Identity System | **Merge → U-01** — same work, AR-10 spec includes anti-corruption rules |
| AR-04–08: Heartbeat rewrites | M-AT01: Heartbeat Calibration | **Merge → U-04 to U-08** — AR specs define content, M-AT01 adds timing tuning |
| AR-13: Inter-agent comms | M-AI03: Agent Communication Protocol | **Merge → U-12** — AR-13 spec + Agent Teams evaluation from M-AI03 |
| AR-11: Plane data for PM | M-IP01: Plane Auto-Update | **Partial overlap → U-14, U-24** — AR-11 is read, M-IP01 is write. Both needed. |

### Unique to AR (not covered by extensions)

| AR Milestone | What It Adds | Unified ID |
|---|---|---|
| AR-01: Fix preembed — full data | Rewrite preembed.py, remove compression | **U-02** |
| AR-02: Orchestrator wakes PM | Detect unassigned → wake PM session | **U-03** |
| AR-03: Orchestrator wakes fleet-ops | Detect approvals → wake fleet-ops session | **U-03** (combined) |
| AR-12: Pre-embed task artifact | Workers get artifact state pre-embedded | **U-13** |
| AR-14: Standards in context | Standards injected by task type | **U-15** |
| AR-15–20: Live tests | 35+ live test scenarios, real agents | **U-26 to U-31** |

### Unique to Extensions (not covered by AR)

| Extension Milestone | What It Adds | Unified ID |
|---|---|---|
| M-AI02: Agent Self-Knowledge | USER.md, TOOLS.md, MEMORY.md populated | **U-09** |
| M-AI04: Agent Research | WebSearch, code exploration capabilities | **U-10** |
| M-AI05: Agent Memory Lifecycle | Memory persistence, archival, cross-session | **U-11** |
| M-AI06: Context Injection Standard | Standardize FleetContext fields | **U-16** |
| M-AT02: No-Agent Decision Layer | Direct HTTP, MCP, templates — no LLM | **U-17** |
| M-AT03: Context-Aware Lifecycle | Agents monitor own context, strategic compact | **U-18** |
| M-AT04: Escalation Engine | Dynamic effort/model/backend escalation | **U-19** |
| M-AT05: Silent Heartbeat | Zero-cost idle heartbeats | **U-20** |
| M-KB01–05: Knowledge & RAG | AICP RAG → fleet, domain KBs, persistence | **U-21 to U-23** |
| M-TS01–04: Tools & Skills | MCP registry, SKILL.md, stack config, IaC | **U-09** (merged with self-knowledge) |
| M-MO01–05: Model Optimization | KV cache, Qwen 2.5, benchmarks, dual GPU | **Partially done** (M-MO01 applied), rest → U-32 to U-35 |
| M-IP02: Writer Notification | Notify writer on content changes | **U-25** |
| M-IP03: AICP ↔ Fleet Bridge | router_unification → AICP controller | **U-36** |
| M-IP04: Fleet Runtime | Actually run the orchestrator | **U-37** |
| M-IP05: Cost Optimization | Prompt caching 90%, Batch API 50% | **U-38** |

---

## 3. Unified Milestones

### Phase A: Agent Foundation (AR-driven, extends with research)

These must come first. Agents need to know who they are before they can do anything.

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-01** | Agent Identity & Config | AR-09 + AR-10 + M-AI01 | Update all agent.yaml (mission, capabilities, model). Write CLAUDE.md for all 10 agents per fleet-elevation role specs. Include 10 anti-corruption rules. Max 4000 chars each. |
| **U-02** | Fix Preembed — Full Data | AR-01 | Rewrite preembed.py. Full context assembly per role (PM gets all tasks, fleet-ops gets approval queue, workers get assigned tasks + artifact state). No compression. |
| **U-03** | Orchestrator Wake Logic | AR-02 + AR-03 + fleet-elevation/23 | Orchestrator detects work → wakes PM (unassigned inbox) and fleet-ops (pending approvals). DROWSY state. Content-aware sleep. Brain-evaluated heartbeats (free). |

### Phase B: Heartbeat Rewrites (AR-driven, extends with autonomy tuning)

Each role gets a complete heartbeat rewrite following the fleet-elevation specs.

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-04** | PM Heartbeat Rewrite | AR-04 + fleet-elevation/05 | Full rewrite: PO directives → unassigned tasks → stage progression → epic breakdown → sprint management → Plane sync → inter-agent communication. |
| **U-05** | Fleet-Ops Heartbeat Rewrite | AR-05 + fleet-elevation/06 | Full rewrite: PO directives → approval processing (REAL review, not rubber stamp) → methodology compliance → board health → budget monitoring → immune system awareness. |
| **U-06** | Architect Heartbeat Rewrite | AR-06 + fleet-elevation/07 | Design contributions, complexity assessment, ADRs, progressive artifact work through stages. |
| **U-07** | DevSecOps Heartbeat Rewrite | AR-07 + fleet-elevation/08 | Security contributions BEFORE implementation, PR review, infrastructure health, crisis response. security_hold mechanism. |
| **U-08** | Worker Template Heartbeat | AR-08 + fleet-elevation/09–14 | Stage-aware: conversation (ask) → analysis (examine) → investigation (research) → reasoning (plan) → work (execute). Progressive artifacts. Per-role variants for engineer, devops, QA, writer, UX, accountability. |

### Phase C: Agent Self-Knowledge & Communication

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-09** | Agent Self-Knowledge | M-AI02 + M-TS01–04 | Populate USER.md (who they serve), TOOLS.md (chain-aware tool reference per fleet-elevation/02), AGENTS.md (knowledge of other agents per fleet-elevation/15). MCP server configs per agent. Skill assignments enforced via SKILL.md. |
| **U-10** | Agent Research Capability | M-AI04 | Define research tools per role: architect gets WebSearch + code exploration, DevSecOps gets CVE databases, QA gets test framework docs. Via `allowed-tools` in skill configs. |
| **U-11** | Agent Memory Lifecycle | M-AI05 | Populate initial MEMORY.md per agent. Define daily log format (memory/YYYY-MM-DD.md). Archival rules. Cross-session persistence via git commit. |
| **U-12** | Inter-Agent Communication | AR-13 + M-AI03 | Wire fleet_chat into heartbeats. Evaluate Agent Teams (swarm mode) vs existing protocol. Task comments → Plane sync. @mention routing to pre-embedded data. Parent task comment propagation. |

### Phase D: Data Integration

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-13** | Pre-embed Task Artifacts | AR-12 | Workers get in-progress artifact state pre-embedded. Completeness %, what's done, what's missing. Drives autocomplete chain. |
| **U-14** | Pre-embed Plane Data | AR-11 | PM gets Plane sprint data. Workers get Plane issue data if task linked. fleet-ops gets Plane state for review. |
| **U-15** | Standards in Agent Context | AR-14 | Relevant standards injected based on current task artifact type. Engineer in work stage sees pull_request + completion_claim standards. |
| **U-16** | Context Injection Standard | M-AI06 | Standardize FleetContext fields, validation, guaranteed structure. Every agent gets consistent context every cycle. |

### Phase E: Autonomy & Intelligence

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-17** | No-Agent Decision Layer | M-AT02 | What doesn't need an agent: direct HTTP, MCP tool calls, template responses. Route to `direct` backend. Zero agent cost. |
| **U-18** | Context-Aware Agent Lifecycle | M-AT03 + fleet-elevation/23 | Agents monitor context via session telemetry. Trigger strategic compact, extract artifacts, recchain. DROWSY → SLEEPING with brain evaluation. Strategic Claude call matrix (model/effort/session per situation). |
| **U-19** | Escalation Engine | M-AT04 | Dynamic escalation: task complexity drives effort level, model tier, backend. Budget mode constrains. Confidence tier influences. Settings-adaptive. |
| **U-20** | Silent Heartbeat Protocol | M-AT05 + fleet-elevation/23 | Zero-cost idle: no LLM call, just API checks. LLM only when work found. Brain evaluates sleeping agents deterministically. 70% cost reduction on idle fleet. |

### Phase F: Knowledge & RAG

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-21** | Connect AICP RAG to Fleet | M-KB01 | Wire `aicp/core/kb.py` via MCP server or direct API. Agents query project knowledge. SQLite-backed (persists through docker purge). |
| **U-22** | Domain Knowledge Bases | M-KB02 | Per-project KBs: fleet, AICP, DSPD, NNRT. Ingest design docs, code comments, architecture decisions. |
| **U-23** | Knowledge Persistence & Sharing | M-KB03 + M-KB05 | SQLite RAG DBs in git-tracked `data/`. Cross-agent sharing: one agent's findings ingested for all. IaC backup/restore. |

### Phase G: Plane & Writer Integration

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-24** | Plane Auto-Update | M-IP01 | When milestones complete, auto-update Plane pages via API. |
| **U-25** | Writer Notification | M-IP02 + fleet-elevation/12 | Notify technical-writer when content changes. Writer scans stale pages every heartbeat. Multi-block artifact compatibility. |

### Phase H: Live Tests (AR-driven)

No mocks. Real agents, real tasks, real data flowing.

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-26** | Live Test: PM Heartbeat | AR-15 | PM wakes, sees unassigned, assigns agents. 10 test scenarios. |
| **U-27** | Live Test: Fleet-Ops Heartbeat | AR-16 | fleet-ops wakes, processes approval, approves/rejects. 7 scenarios. |
| **U-28** | Live Test: Worker Heartbeat | AR-17 | Worker follows methodology stage, updates artifact. 8 scenarios. |
| **U-29** | Live Test: Inter-Agent Flow | AR-18 | PM assigns → worker works → fleet-ops reviews → done. Full cycle. |
| **U-30** | Live Test: Progressive Work | AR-19 | Task spans 3+ cycles. Artifact grows. Readiness increases. |
| **U-31** | Live Test: Plane Integration | AR-20 | Plane issue → OCMC task → agent works → Plane synced. |

### Phase I: Model & Cost Optimization

| ID | Title | Source | Scope |
|----|-------|--------|-------|
| **U-32** | Add Qwen 2.5 Models | M-MO02 | Qwen 2.5 7B Instruct + Coder GGUF configs. Benchmark against Hermes. |
| **U-33** | Run Real Benchmarks | M-MO03 | Execute model_benchmark.py against actual LocalAI. Real numbers. |
| **U-34** | Multi-Model Router Strategy | M-MO04 | Hermes for function calling, Qwen for general, Qwen Coder for code. |
| **U-35** | Dual GPU Preparation | M-MO05 | When hardware arrives: tensor split, 14B configs. |
| **U-36** | AICP ↔ Fleet Bridge | M-IP03 | router_unification.py → AICP controller. |
| **U-37** | Fleet Runtime Deployment | M-IP04 | Actually run the orchestrator with agents. Operational readiness. |
| **U-38** | Cost Optimization | M-IP05 | Prompt caching 90% off, Batch API 50% off. Claude-Mem plugin. |

---

## 4. Implementation Order

```
Phase A: Agent Foundation (U-01 to U-03)        ← MUST come first
  ↓
Phase B: Heartbeat Rewrites (U-04 to U-08)      ← agents need identity before heartbeats
  ↓
Phase C: Self-Knowledge & Comms (U-09 to U-12)  ← heartbeats need tools and comms
  ↓
Phase D: Data Integration (U-13 to U-16)        ← comms need data flowing
  ↓
Phase E: Autonomy & Intelligence (U-17 to U-20) ← can start with Phase D
  ↓
Phase F: Knowledge & RAG (U-21 to U-23)         ← can start with Phase D
  ↓
Phase G: Plane & Writer (U-24 to U-25)          ← needs Phase D
  ↓
Phase H: Live Tests (U-26 to U-31)              ← needs Phases A-D minimum
  ↓
Phase I: Model & Cost (U-32 to U-38)            ← independent, can run in parallel
```

**Phase I can run in parallel with everything** — model optimization and cost reduction are independent of agent work.

**M-MO01 (KV cache quantization) already applied** — not in this plan.

---

## 5. Summary

| Phase | Milestones | Priority | Source |
|-------|-----------|----------|--------|
| A: Agent Foundation | U-01 to U-03 (3) | Critical | AR-01,02,03,09,10 + M-AI01 |
| B: Heartbeat Rewrites | U-04 to U-08 (5) | Critical | AR-04–08 |
| C: Self-Knowledge & Comms | U-09 to U-12 (4) | High | AR-13 + M-AI02–05, M-TS01–04 |
| D: Data Integration | U-13 to U-16 (4) | High | AR-11,12,14 + M-AI06 |
| E: Autonomy & Intelligence | U-17 to U-20 (4) | High | M-AT02–05 + fleet-elevation/23 |
| F: Knowledge & RAG | U-21 to U-23 (3) | Medium | M-KB01–05 |
| G: Plane & Writer | U-24 to U-25 (2) | Medium | M-IP01–02 + fleet-elevation/12 |
| H: Live Tests | U-26 to U-31 (6) | High | AR-15–20 |
| I: Model & Cost | U-32 to U-38 (7) | Medium | M-MO02–05 + M-IP03–05 |
| **Total** | **38** | | |

Combined with Waves 1-5 (47 milestones): **85 total milestones**.

---

## 6. Design Doc References

Every unified milestone traces to a design document. NEVER build from milestone names alone.

| Phase | Primary Design Docs |
|-------|--------------------|
| A | fleet-elevation/02 (architecture), agent-rework/02 (preembed), agent-rework/03 (waking) |
| B | fleet-elevation/05–14 (per-role specs), agent-rework/04–08 (heartbeat details) |
| C | fleet-elevation/15 (synergy), fleet-elevation/20 (behavior), agent-rework/09 (comms) |
| D | agent-rework/02 (preembed), agent-rework/11 (Plane), agent-rework/10 (standards) |
| E | fleet-elevation/23 (lifecycle), fleet-elevation/04 (brain) |
| F | AICP modules (rag.py, kb.py, stores.py), LocalAI capabilities research |
| G | agent-rework/11 (Plane), fleet-elevation/12 (technical-writer) |
| H | agent-rework/13 (live test plan) |
| I | Model compression research, ecosystem capabilities research |

---

## 7. What's Already Done

- [x] M-MO01: KV cache quantization applied to all model YAMLs
- [x] Docker-compose `/data` volume mount for persistence
- [x] Function calling grammar on hermes models
- [x] Prompt caching on hermes models
- [x] `.claudeignore` on all 4 projects
- [x] Statusline IaC (`make install-statusline`)
- [x] Session telemetry adapter (`session_telemetry.py`)
- [x] 8 cross-system integration wires (W1-W8)
- [x] 767 tests (744 unit + 23 integration)
