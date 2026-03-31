# Master Milestone Index — All Fleet Work

**Date:** 2026-03-31
**Status:** Active — living index of all milestone documents

---

## Milestone Sets

### 1. Immune System, Teaching System, Methodology System
**Document:** `milestone-plan-three-systems.md`
**Milestones:** 44 (A01-A08, B01-B09, C01-C06, D01-D10, E01-E06, G01-G05)
**Estimated effort:** 2000+ hours
**Status:** 44/44 — ALL COMPLETE

These are PREREQUISITES for autonomous fleet operation. Must be
designed and built before agents run unsupervised.

| Category | Count | Scope |
|----------|-------|-------|
| A. Foundation | 8 | Custom fields on OCMC + Plane, sync evolution |
| B. Methodology | 9 | Stages, protocols, observability, standards |
| C. Teaching | 6 | Lessons, injection, practice, tracking |
| D. Immune | 10 | Doctor, detection, response |
| E. Platform | 6 | Orchestrator, gateway, events, heartbeat, sync, MCP |
| G. OCMC UI | 5 | Three systems visibility, dashboard, events |

Design documents:
- `immune-system/` — 7 documents
- `teaching-system/` — 1 document
- `methodology-system/` — 8 documents
- `three-systems-runtime.md` — how the three systems interact

### 2. Fleet Control Surface
**Document:** `fleet-control-surface.md`
**Milestones:** M-CS01 through M-CS10 (7 prioritized)
**Status:** Design complete

Three independent control axes in the OCMC header bar:
- Work Mode (where new work comes from)
- Cycle Phase (what kind of work)
- Backend Mode (which AI)

Implemented by injecting FleetControlBar component into DashboardShell.tsx
header, after OrgSwitcher. Backend patch for fleet_config JSON field on
Board model.

### 3. Event Bus (The Nervous System)
**Document:** `fleet-event-bus-architecture.md`
**Milestones:** M-EB01 through M-EB20
**Status:** 17/20 complete, 3 remaining

Built: CloudEvents store, event router, chain runner, 6 surfaces,
plane watcher, OCMC watcher, config watcher, config sync.

Remaining:
- M-EB02: CloudEvents SDK integration
- M-EB03: Agent feed design doc
- M-EB04: Sync map doc
- M-EB05: Mention design doc

### 4. Fleet Autonomy (Hierarchical Task Management)
**Document:** Plan file (in .claude/plans/)
**Phases:** 5 phases
**Status:** Design complete, not implemented

- Phase 1: Expand data model (fields, parsing, approvals)
- Phase 2: Missing MCP tools (fleet_task_create, fleet_approve, fleet_agent_status)
- Phase 3: Orchestrator daemon (the brain)
- Phase 4: Agent heartbeats (make agents alive)
- Phase 5: Sprint plan model

### 5. Operational Readiness
**Document:** `STATUS-TRACKER.md` (items 17-21)
**Status:** Pending

- #17: Execute one real task end-to-end
- #18: PM first heartbeat with Plane
- #19: AICP Stage 1 complete
- #20: Fleet 24h observation
- #21: Resume autonomous flow

---

## Dependency Map

```
Event Bus (mostly done)
  ↓ events infrastructure used by everything
Fleet Autonomy (Phase 1-3)
  ↓ orchestrator, MCP tools, data model
Foundation (A01-A08)
  ↓ custom fields on both platforms
Methodology (B01-B09)
  ↓ stages, protocols, standards
Control Surface (M-CS01-10)
  ↓ PO can see and control the fleet
Teaching (C01-C06)
  ↓ lessons, practice, verification
Immune System (D01-D10)
  ↓ doctor, detection, response
Platform Evolution (E01-E06)
  ↓ orchestrator, gateway, events, MCP integration
OCMC UI Integration (G01-G05)
  ↓ everything visible in the UI
Operational Readiness (#17-21)
  ↓ fleet running with all systems
Autonomous Operation
```

The event bus is mostly built — it provides the infrastructure
everything else publishes through. Fleet autonomy gives the fleet
its brain (orchestrator, MCP tools). Foundation gives the data model
the three systems need. The three systems (methodology, teaching,
immune) make the fleet safe to run autonomously. The control surface
gives the PO real-time control. Operational readiness validates
everything works end-to-end.

---

## Total Milestones Across All Sets

| Set | Count | Status |
|-----|-------|--------|
| Three Systems (A-G) | 44 | **44 done — COMPLETE** |
| Control Surface (M-CS) | 7 | **7 done — COMPLETE** |
| Event Bus (M-EB) | 20 | **20 done — COMPLETE** |
| Fleet Autonomy | ~15 (5 phases) | **All 5 phases COMPLETE** |
| Transpose Layer | 7 | **7 done — COMPLETE** |
| Context System | 36 | **34 done**, 2 nice-to-haves remaining |
| Operational Readiness | 5 | Pending (needs fleet running) |
| **Labor Attribution (M-LA)** | **8** | **8 done — COMPLETE** |
| **Budget Mode System (M-BM)** | **6** | **6 done — COMPLETE** |
| **Multi-Backend Router (M-BR)** | **8** | **8 done — COMPLETE** (4 FUTURE schema-ready) |
| **Iterative Validation (M-IV)** | **8** | **8 done — COMPLETE** |
| **Model Upgrade Path (M-MU)** | **8** | **8 done — COMPLETE** (3 FUTURE schema-ready) |
| **Storm Prevention (M-SP)** | **9** | **9 done — COMPLETE** |
| **Total** | **~181** | **~175 implemented, 47 strategic milestones COMPLETE** |

---

### 6. Labor Attribution and Provenance System
**Document:** `labor-attribution-and-provenance.md`
**Milestones:** M-LA01 through M-LA08
**Status:** COMPLETE — all 8 milestones implemented (Wave 1 + Wave 4)

Every fleet artifact carries a labor stamp: agent, backend, model, effort,
skills, confidence tier, cost. Trainee/community tier work gets extra review.

### 7. Budget Mode System for OCMC Orders
**Document:** `budget-mode-system.md`
**Milestones:** M-BM01 through M-BM06
**Status:** COMPLETE — all 6 milestones implemented (Wave 1 + Wave 2 + Wave 4 + Wave 5)

Graduated budget modes: blitz, standard, economic, frugal, survival, blackout.
Per-order cost envelopes. Auto-transitions based on quota pressure.

### 8. Multi-Backend Routing Decision Engine
**Document:** `multi-backend-routing-engine.md`
**Milestones:** M-BR01 through M-BR08
**Status:** COMPLETE — all 8 milestones implemented (Wave 2 + Wave 5; M-BR08 FUTURE schema-ready)

Plugin-style backend registry. Claude + LocalAI + OpenRouter free + Codex CLI.
Budget-constrained routing. Fallback chains. Cheapest capable backend wins.

### 9. Iterative Validation and Challenge Loops
**Document:** `iterative-validation-and-challenge-loops.md`
**Milestones:** M-IV01 through M-IV08
**Status:** COMPLETE — all 8 milestones implemented (Wave 3)

Multi-round adversarial challenges. Automated + agent + cross-model + scenario.
Confidence tier determines challenge depth. Budget-aware skip/defer logic.

### 10. Model Upgrade Path — LocalAI Next-Gen
**Document:** `model-upgrade-path.md`
**Milestones:** M-MU01 through M-MU08
**Status:** COMPLETE — all 8 milestones implemented (Wave 4 + Wave 5; M-MU05/06/08 FUTURE schema-ready)

Upgrade hermes-3b → Qwen3-8B. Plan for 19GB dual-GPU. Shadow routing.
TurboQuant and BitNet monitoring. Confidence tier progression tracking.

### 11. Storm Prevention System
**Document:** `storm-prevention-system.md`
**Milestones:** M-SP01 through M-SP09
**Status:** COMPLETE — all 9 milestones implemented (Wave 1 + Wave 2 + Wave 3)

Automatic graduated response. 9 indicators, 5 severity levels. Circuit
breakers per-agent and per-backend. Diagnostic snapshots. Post-incident reports.

---

### 12. Implementation Roadmap
**Document:** `implementation-roadmap.md`
**Status:** ACTIVE PLAN

5 implementation waves sequencing all 47 new milestones:
- Wave 1: Foundation (safety + observability) — 10 milestones, CRITICAL
- Wave 2: Routing (multi-backend + budget control) — 10 milestones, HIGH
- Wave 3: Validation (challenge loops) — 9 milestones, HIGH
- Wave 4: Evolution (better models + analytics) — 10 milestones, MEDIUM
- Wave 5: Scale (dual GPU + advanced) — 8 milestones, MEDIUM-LOW

Integration with operational readiness (#17-21), LocalAI stages, and
Fleet Elevation. Success criteria per wave. Critical rule: do NOT resume
autonomous flow without Wave 1 complete.

---

## Dependency Map (Updated 2026-03-31)

```
Event Bus (done) ─── events infrastructure
  ↓
Fleet Autonomy (done) ─── orchestrator, MCP tools
  ↓
Foundation + Methodology + Teaching + Immune (done)
  ↓
Control Surface (done) ─── PO visibility
  ↓
Operational Readiness (#17-21)
  ↓
┌─────────────────────────────────────────────────┐
│  NEW STRATEGIC MILESTONES (2026-03-31)          │
│                                                 │
│  Storm Prevention (M-SP) ← infrastructure guard │
│    ↓                                            │
│  Budget Mode System (M-BM) ← spending strategy  │
│    ↓                                            │
│  Multi-Backend Router (M-BR) ← cheapest backend │
│    ↓                                            │
│  Labor Attribution (M-LA) ← provenance chain    │
│    ↓                                            │
│  Iterative Validation (M-IV) ← challenge loops  │
│    ↓                                            │
│  Model Upgrade Path (M-MU) ← better local AI   │
└─────────────────────────────────────────────────┘
  ↓
LocalAI Independence (Stages 2-5)
  ↓
Autonomous Operation at Scale
```

---

## Documents in This Directory

```
active/
├── MASTER-INDEX.md                         ← this file
├── fleet-control-surface.md                ← control surface design
├── fleet-event-bus-architecture.md         ← event bus milestones
├── fleet-event-bus-audit.md                ← event bus audit
├── milestone-plan-three-systems.md         ← 44 milestones detailed
├── three-systems-runtime.md                ← how 3 systems interact
├── labor-attribution-and-provenance.md     ← NEW: labor stamps
├── budget-mode-system.md                   ← NEW: budget modes
├── multi-backend-routing-engine.md         ← NEW: multi-backend router
├── iterative-validation-and-challenge-loops.md ← NEW: challenge loops
├── model-upgrade-path.md                   ← NEW: LocalAI model upgrades
├── storm-prevention-system.md              ← NEW: storm prevention
├── immune-system/
│   ├── 01-overview.md ... 07-integration.md
├── teaching-system/
│   └── 01-overview.md
├── methodology-system/
│   ├── 01-overview.md ... new-custom-fields.md
└── fleet-elevation/
    ├── 01-overview.md ... 31-transition.md
```