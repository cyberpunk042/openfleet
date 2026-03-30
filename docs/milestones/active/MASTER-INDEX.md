# Master Milestone Index — All Fleet Work

**Date:** 2026-03-30
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
| Operational Readiness | 5 | Pending (needs fleet running) |
| **Total** | **~91** | **~86 implemented** |

---

## Documents in This Directory

```
active/
├── MASTER-INDEX.md                    ← this file
├── fleet-control-surface.md           ← control surface design
├── fleet-event-bus-architecture.md    ← event bus milestones
├── fleet-event-bus-audit.md           ← event bus audit
├── milestone-plan-three-systems.md    ← 44 milestones detailed
├── three-systems-runtime.md           ← how 3 systems interact
├── immune-system/
│   ├── 01-overview.md
│   ├── 02-the-doctor.md
│   ├── 03-disease-catalogue.md
│   ├── 04-research-findings.md
│   ├── 05-detection.md
│   ├── 06-response.md
│   └── 07-integration.md
├── teaching-system/
│   └── 01-overview.md
└── methodology-system/
    ├── 01-overview.md
    ├── 02-conversation-protocol.md
    ├── 03-analysis-protocol.md
    ├── 04-investigation-protocol.md
    ├── 05-reasoning-protocol.md
    ├── 06-work-protocol.md
    ├── 07-standards-and-examples.md
    └── new-custom-fields.md
```