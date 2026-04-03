# System 17: Plane Integration — PM Surface ↔ Ops Surface

**Type:** Fleet System
**ID:** S17
**Files:** plane_sync.py (~400 lines), plane_watcher.py (~250 lines), plane_methodology.py (~260 lines), config_sync.py (~300 lines)
**Total:** 1,208 lines
**Tests:** 40+

## What This System Does

Bridges two surfaces for two audiences: Plane (PO's strategic view — issues, sprints, modules, backlog) and OCMC (agents' operational view — current work queue with stages, artifacts, challenges). The PM selectively promotes Plane issues into OCMC PM tasks. Each PM task may spawn 10-20+ ops tasks (architect design_input, QA test_definition, devsecops security, engineer implementation, fleet-ops review, writer docs).

## The Two-Level Task Model

```
Plane (PO surface)                OCMC (Agent surface)
  Issue: "Add auth"          →    PM Task: "Add auth" (linked via plane_issue_id)
                                  ├── Architect: design_input (contribution)
                                  ├── QA: qa_test_definition (contribution)
                                  ├── DevSecOps: security_req (contribution)
                                  ├── Engineer: implementation (work task)
                                  ├── Fleet-ops: review (approval)
                                  └── Writer: documentation (follow-up)
```

PM selects Plane issues → creates OCMC PM tasks → PM creates ops tasks from PM tasks. NOT automatic mirroring — PM intelligence decides what enters OCMC.

## Bidirectional Sync

- **Plane → OCMC:** PlaneSyncer.ingest_from_plane() discovers new Plane issues, creates OCMC tasks with plane_issue_id, plane_project_id, plane_workspace.
- **OCMC → Plane:** PlaneSyncer.push_completions_to_plane() updates Plane issues when OCMC tasks complete (state → "Done").
- **Methodology on Plane:** Labels for stage (stage:conversation) and readiness (readiness:50). Verbatim in description HTML via hidden span markers.

## Plane CE Limitations

Plane Community Edition has NO custom fields. Fleet uses:
- Labels for methodology state (stage:X, readiness:N, phase:Y)
- Hidden spans in description HTML for verbatim (fleet-verbatim class, display:none)
- Comments for trail events and completion summaries

## Relationships

- SYNCED BY: sync daemon (60s loop) + fleet_plane_sync MCP tool
- READS: plane_client.py (issues, cycles, states, labels)
- WRITES: plane_client.py (update issue state, labels, description, comments)
- CONSUMED BY: PM heartbeat (Plane sprint data in pre-embed — NOT YET IMPLEMENTED)
- CONNECTS TO: S07 orchestrator (sync daemon, context refresh)
- CONNECTS TO: S08 MCP tools (7 fleet_plane_* tools)
- CONNECTS TO: S10 transpose (artifact HTML on Plane issues)
- CONNECTS TO: Plane MCP server (makeplane/plane-mcp-server — evaluated, not deployed)
- NOT YET IMPLEMENTED: ops comment → Plane comment sync, PM pre-embed Plane sprint data, writer auto-update pages, full artifact HTML push, bidirectional Plane comment sync
