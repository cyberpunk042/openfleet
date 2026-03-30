# Context System Milestones

**Date:** 2026-03-30
**Status:** Planning
**Part of:** Context System (document 8 of 8)

---

## Milestone Summary

### MCP Layer Foundation (ML — 5 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| ML-F01 | Data assembly module | context_assembly.py — shared aggregation functions |
| ML-F02 | Role provider registry | role_providers.py — per-role data functions |
| ML-I01 | MCP context mode | Task mode vs heartbeat mode on FleetMCPContext |
| ML-I02 | Aggregate MCP tools | fleet_task_context + fleet_heartbeat_context |
| ML-G01 | Wire assembly to all data sources | Connect to all fleet systems |

### Task × MCP (TM — 8 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| TM-F01 | Task data aggregation | Collect task + artifact + methodology + custom fields |
| TM-F02 | Comment history aggregation | OCMC + Plane comments merged |
| TM-F03 | Activity history aggregation | Events filtered for task |
| TM-I01 | MCP group call | fleet_task_context tool |
| TM-I02 | Caching strategy | Fresh vs cached per cycle |
| TM-G01 | Wire to transpose | Artifact + completeness in bundle |
| TM-G02 | Wire to methodology | Stage + instructions in bundle |
| TM-G03 | Wire to Plane | Plane state + comments in bundle |

### Task × Pre-Embedded (TP — 6 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| TP-F01 | Pre-embed data model | What's included, size budget |
| TP-F02 | Pre-embed assembly | Build compact pre-embed from task data |
| TP-I01 | Gateway injection mechanism | How pre-embed enters session |
| TP-I02 | Dispatch-time assembly | Orchestrator builds at dispatch |
| TP-G01 | Wire to orchestrator | Pre-embed in dispatch flow |
| TP-G02 | Wire to gateway | Gateway injects into session |

### Heartbeat × MCP (HM — 7 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| HM-F01 | Role data provider interface | Interface definition |
| HM-F02 | Role data providers | Per-role implementations (10 roles) |
| HM-F03 | Event filtering | Events since last heartbeat |
| HM-I01 | MCP heartbeat group call | fleet_heartbeat_context tool |
| HM-G01 | Wire to event bus | Filtered events in bundle |
| HM-G02 | Wire to agent roles | Role-specific data |
| HM-G03 | Wire to directives | Pending PO commands |

### Heartbeat × Pre-Embedded (HP — 6 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| HP-F01 | Role-specific summary | Compact one-liner per role |
| HP-F02 | Events summary formatter | Compact event summary |
| HP-I01 | Upgrade HeartbeatBundle | Add role + events fields |
| HP-I02 | Gateway heartbeat injection | Inject rendered bundle |
| HP-G01 | Wire to role providers | Compact summaries |
| HP-G02 | Wire to event bus | Compact event history |

### Testing (CT — 4 milestones)
| # | Milestone | Scope |
|---|-----------|-------|
| TM-T01 | Task aggregation unit tests | Mock sources, verify bundle |
| TM-T02 | Task integration test | End-to-end bundle assembly |
| HM-T01 | Heartbeat role provider tests | Per-role data shape |
| HP-T01 | HeartbeatBundle render tests | Output format + size |

---

## Total: 36 milestones

| Category | Count |
|----------|-------|
| MCP Layer Foundation | 5 |
| Task × MCP | 8 |
| Task × Pre-Embedded | 6 |
| Heartbeat × MCP | 7 |
| Heartbeat × Pre-Embedded | 6 |
| Testing | 4 |
| **Total** | **36** |

---

## Dependency Order

```
ML-F01, ML-F02 (Foundation: assembly + role providers)
  ↓
ML-I01, ML-I02 (Infrastructure: MCP mode + aggregate tools)
  ↓
TM-F01-F03 + HM-F01-F03 (Data aggregation for both contexts)
  ↓
TM-I01 + HM-I01 (MCP group calls)
  ↓
TP-F01-F02 + HP-F01-F02 (Pre-embed assembly)
  ↓
TP-I01-I02 + HP-I01-I02 (Gateway injection)
  ↓
All G milestones (Integration wiring)
  ↓
All T milestones (Testing)
```