# Plane Integration — Bidirectional Sync

> **4 files. 1208 lines. Keeps Plane and OCMC in sync. Methodology labels on Plane issues.**
>
> Plane is for humans (PO, stakeholders). OCMC is for agents. Both
> must show the same state. Plane → OCMC: new issues become tasks.
> OCMC → Plane: completed tasks update issue state. Methodology
> (stage, readiness) tracked via Plane labels since CE lacks custom fields.
> IaC config sync ensures state survives restarts.

## 1. Why It Exists

Without sync, the PO sees one state in Plane and agents see another in
OCMC. Tasks created in Plane wouldn't reach agents. Completions by
agents wouldn't appear in Plane. The PO would need to manually update
both surfaces — "every manual step is a bug."

## 2. How It Works

### 2.1 Plane → OCMC

```
PlaneSyncer.ingest_from_plane()
  ↓
Discover new Plane issues (not yet linked to OCMC tasks)
  ↓
Create OCMC task with:
  plane_issue_id, plane_project_id, plane_workspace
  ↓
PM sees new task in heartbeat → assigns agent
```

### 2.2 OCMC → Plane

```
PlaneSyncer.push_completions_to_plane()
  ↓
Find OCMC tasks in "done" status with plane_issue_id
  ↓
Update Plane issue state to configured "done" state
```

### 2.3 Methodology on Plane (No Custom Fields)

Plane CE lacks custom fields. Hybrid approach:
```
Stage    → labels: stage:conversation, stage:analysis, stage:work
Readiness → labels: readiness:0, readiness:50, readiness:99
Verbatim  → HTML section with fleet-verbatim span markers
```

Valid readiness labels: 0, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99, 100

### 2.4 Config Sync (IaC)

When Plane watcher detects changes → update DSPD config YAML files.
PO requirement: "if we restart it will pick up where we left."

## 3. File Map

```
fleet/core/
├── plane_sync.py          Bidirectional sync: ingest + push      (varies)
├── plane_methodology.py   Stage/readiness labels, verbatim HTML   (varies)
├── plane_watcher.py       Monitor Plane for changes               (varies)
└── config_sync.py         IaC YAML updates from Plane state       (varies)
```

## 4. Consumers

MCP tools (7 fleet_plane_* tools), orchestrator (sync cycle), transpose (artifact HTML), context assembly (Plane data in task context), events (Plane events).

## 5. Design Decisions

**Why labels for methodology?** Plane CE has no custom fields. Labels are the only structured metadata available. Prefix convention (stage:, readiness:) prevents collision with other labels.

**Why verbatim in HTML, not labels?** Verbatim requirements are long text. Labels have length limits. Hidden span markers in description_html allow full verbatim text while keeping it machine-parseable.

**Why config sync to YAML?** IaC principle: "if we restart it will pick up where we left." YAML files in git mean the state is version-controlled and reproducible.

## 6. NOT Implemented

- Task comment sync (OCMC comments → Plane comments)
- PM pre-embed Plane sprint data (AR-11)
- Writer auto-update Plane pages on completion

## 7. Test Coverage: **40+ tests**
