# System 17: Plane Integration

**Source:** `fleet/core/plane_sync.py`, `fleet/core/plane_methodology.py`, `fleet/core/plane_watcher.py`, `fleet/core/config_sync.py`
**Status:** 🔨 Sync works. Methodology labels work. Comment sync NOT implemented.
**Design docs:** `agent-rework/11-plane-integration.md`

---

## Purpose

Bidirectional sync between Plane (project management) and OCMC (agent coordination). Plane is for humans and PO visibility. OCMC is for agents. Both stay in sync. IaC config sync ensures restart recovery.

## Key Concepts

### Plane → OCMC (plane_sync.py)

`ingest_from_plane()` — discovers new Plane issues, creates OCMC tasks with:
- `plane_issue_id` — Plane issue UUID
- `plane_project_id` — Plane project UUID
- `plane_workspace` — Plane workspace slug

### OCMC → Plane (plane_sync.py)

`push_completions_to_plane()` — OCMC tasks that reached `done` with `plane_issue_id` → Plane issue state updated.

### Methodology on Plane (plane_methodology.py)

Plane CE lacks custom fields. Hybrid approach:
- Stage → labels: `stage:conversation`, `stage:work`
- Readiness → labels: `readiness:0`, `readiness:50`, `readiness:99`
- Verbatim requirement → HTML section in description with `fleet-verbatim` span marker

Valid readiness values enforced: `0, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99, 100`

### Config Sync (config_sync.py)

When Plane watcher detects changes, updates DSPD config YAML files. PO requirement: "if we restart it will pick up where we left."

### Plane Watcher (plane_watcher.py)

Monitors Plane for changes. Feeds change_detector. Part of monitor daemon.

## NOT Implemented

- Task comment sync (OCMC comments → Plane comments) — agent work trail invisible on Plane
- PM pre-embedded Plane sprint data (AR-11)
- Plane module listing in agent context

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Plane sync runs in orchestrator/daemon cycle | Orchestrator → Plane |
| **MCP Tools** | 7 fleet_plane_* tools access Plane API | MCP → Plane |
| **Transpose** | Artifact HTML rendered to Plane descriptions | Transpose → Plane |
| **Methodology** | Stage/readiness labels on Plane issues | Methodology → Plane |
| **Events** | Plane changes emit events | Plane → Events |
| **Config Sync** | Plane changes → IaC YAML updates | Plane → Config |
| **Context Assembly** | Plane issue data in task context | Plane → Context |

## What's Needed

- [ ] Task comment sync (OCMC → Plane, bidirectional)
- [ ] PM pre-embed Plane sprint data (AR-11)
- [ ] Writer auto-update Plane pages on task completion
- [ ] Live test: Plane issue → OCMC task → agent works → Plane synced
