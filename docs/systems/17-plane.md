# Plane Integration — PM Surface ↔ Ops Surface

> **4 files. 1208 lines. Two surfaces for two audiences: Plane for the PO, OCMC for agents.**
>
> Plane is the PROJECT MANAGEMENT surface — all issues, sprints, modules,
> backlog. The PO and stakeholders work here. OCMC is the OPERATIONAL
> surface — current work queue for agents. The PM selects what's relevant
> from Plane and creates PM tasks on OCMC. Each PM task may spawn dozens
> of ops tasks, each going through full methodology stages, producing
> artifacts, facing challenges, getting reviewed. Ops task progress
> reflects back to the PM task and to the Plane issue automatically.

---

## 1. Why It Exists

Two audiences need different views:

- **PO sees Plane:** "Issue #42: Add fleet controls" — strategic view,
  sprint progress, module ownership, stakeholder comments
- **Agents see OCMC:** Their assigned ops tasks with stage instructions,
  verbatim requirements, artifact state, colleague contributions

Without Plane integration:
- PO creates issues that agents never see
- Agent completions that PO never sees
- Manual copy-paste between surfaces ("every manual step is a bug")

---

## 2. How It Works

### 2.1 The Two-Level Task Model

```
PLANE (Project Management)
┌──────────────────────────────────────────────────┐
│  Issue #42: "Add fleet controls to header"       │
│  Sprint: S3 │ Module: OCMC │ Priority: High      │
│  Labels: stage:reasoning, readiness:80            │
│  Description: verbatim requirement + artifact HTML │
│                                                    │
│  ← Progress updates flow UP from ops tasks        │
│  ← Artifact HTML rendered by transpose layer      │
│  ← Comments from ops task completions             │
└──────────────────────┬───────────────────────────┘
                       │ PM creates PM task linked
                       │ to this Plane issue
                       ▼
OCMC (Operations)
┌──────────────────────────────────────────────────┐
│  PM Task: "Add fleet controls to header"         │
│  plane_issue_id: #42 │ Stage: reasoning           │
│  Readiness: 80% │ Agent: (PM manages)             │
│                                                    │
│  This PM task spawns DOZENS of ops tasks:          │
│                                                    │
│  ├── Ops: architect design_input                   │
│  │   └── FULL stages: analysis → reasoning         │
│  │       └── Artifact: analysis_document            │
│  │           (scope, findings, implications)        │
│  │       └── Contribution posted to PM task         │
│  │                                                  │
│  ├── Ops: qa-engineer test_definition              │
│  │   └── FULL stages: analysis → reasoning          │
│  │       └── Artifact: qa_test_definition           │
│  │           (test criteria, edge cases, priorities) │
│  │       └── Contribution posted to PM task          │
│  │                                                   │
│  ├── Ops: devsecops security_requirement             │
│  │   └── FULL stages: analysis → reasoning           │
│  │       └── Artifact: security_assessment           │
│  │       └── Contribution posted to PM task          │
│  │                                                   │
│  ├── Ops: software-engineer implementation           │
│  │   └── FULL stages: reasoning → work               │
│  │       └── Consumes: architect design, QA tests,   │
│  │           devsecops requirements                   │
│  │       └── Produces: code, commits, PR             │
│  │       └── Faces: adversarial challenges           │
│  │       └── Labor stamp: model, cost, tier          │
│  │                                                   │
│  ├── Ops: fleet-ops review                           │
│  │   └── Real review against verbatim + criteria     │
│  │   └── Approve/reject with reasoning               │
│  │                                                   │
│  ├── Ops: technical-writer documentation             │
│  │   └── Updates Plane pages after completion        │
│  │                                                   │
│  └── ... (10-20+ ops tasks per PM task)              │
│                                                      │
│  Each ops task:                                      │
│    - Has its OWN stage progression                   │
│    - Produces its OWN artifacts (tracked, complete)   │
│    - Has its OWN readiness (0 → 99 → 100)            │
│    - Gets its OWN labor stamp                         │
│    - May face its OWN challenges                      │
│    - Leaves trail on PM task (comments + artifacts)   │
│                                                      │
│  PM task advances as ops tasks complete:              │
│    All contributions received → reasoning complete   │
│    Implementation done → work stage complete          │
│    All children done → PM task → review → done        │
│    Done → Plane issue state updated                   │
└──────────────────────────────────────────────────┘
```

### 2.2 What Flows Between Surfaces

**Plane → PM (PM-driven, not automatic sync):**
```
PM heartbeat: pre-embedded Plane sprint data
  ↓
PM evaluates: which Plane issues are priority NOW?
  ↓
PM creates OCMC PM task linked to Plane issue
  (plane_issue_id, plane_project_id, plane_workspace)
  ↓
PM assigns agents, sets stages, breaks down work
```

This is NOT automatic mirroring. The PM DECIDES what enters OCMC.
Not every Plane issue becomes an OCMC task. Only what's relevant
to the current sprint and priorities.

**Ops → PM → Plane (automatic propagation):**
```
Ops task completed (e.g., architect posts design_input)
  ↓
Comment posted on PM task: "Design input from architect: ..."
  ↓
PM task artifact updated (contribution received)
  ↓
PM task readiness increases (artifact completeness)
  ↓
When PM task reaches done:
  ↓
Plane issue state updated to "done"
Plane labels updated (stage, readiness)
Plane description updated (artifact HTML via transpose)
```

**Methodology on Plane (labels + HTML):**
```
Stage    → labels: stage:conversation, stage:work, etc.
Readiness → labels: readiness:0, readiness:50, readiness:99
Verbatim  → HTML section with fleet-verbatim span markers
Artifacts → HTML sections with fleet-artifact markers (transpose)
```

### 2.3 What Plane Shows the PO

For Issue #42, the PO sees on Plane:
- Labels: `stage:work`, `readiness:99`, `priority:high`
- Description: verbatim requirement + rendered artifact HTML
  (analysis findings, plan with steps, acceptance criteria mapping)
- Comments: ops task completions, design contributions, QA findings
- Sprint: which sprint it's in, progress relative to other issues
- Module: which module owns it

The PO NEVER needs to look at OCMC. Everything flows to Plane.

### 2.4 Config Sync (IaC)

When Plane watcher detects changes → update DSPD config YAML.
PO requirement: "if we restart it will pick up where we left."

---

## 3. File Map

```
fleet/core/
├── plane_sync.py          PM-driven ingest + completion push    (varies)
├── plane_methodology.py   Stage/readiness labels, verbatim HTML  (varies)
├── plane_watcher.py       Monitor Plane for changes              (varies)
└── config_sync.py         IaC YAML updates from Plane state      (varies)
```

Total: **1208 lines** across 4 modules.

---

## 4. Per-File Key Functions

### plane_sync.py — PlaneSyncer

| Function | What It Does |
|----------|-------------|
| `ingest_from_plane()` | Discover new Plane issues not yet linked. Create PM tasks with plane_issue_id. Returns (created, skipped). |
| `push_completions_to_plane()` | Find done PM tasks with plane_issue_id. Update Plane issue state. |

### plane_methodology.py — Labels + HTML

| Function | What It Does |
|----------|-------------|
| `extract_stage_from_labels(labels)` | Read stage:X from Plane labels |
| `extract_readiness_from_labels(labels)` | Read readiness:N from Plane labels |
| `build_label_updates(stage, readiness)` | Generate label add/remove for Plane API |
| `inject_verbatim_into_html(html, verbatim)` | Inject verbatim into description with fleet-verbatim markers |
| `extract_methodology_state(issue)` | Extract stage + readiness + verbatim from Plane issue |

### plane_watcher.py — Change Monitor

Monitors Plane for: new issues, state changes, label changes, comment additions. Feeds change_detector. Runs as part of monitor daemon.

### config_sync.py — IaC State Persistence

When Plane changes detected → update DSPD config YAML files → optionally git commit. Ensures restart recovery.

---

## 5. Consumers

| Layer | Module | What It Uses |
|-------|--------|-------------|
| **MCP Tools** | `tools.py` | 7 fleet_plane_* tools: status, sprint, sync, create/comment/update/modules |
| **Orchestrator** | `orchestrator.py` | Plane sync in daemon cycle |
| **Transpose** | `transpose.py` | Artifact HTML rendered to Plane descriptions |
| **Context Assembly** | `context_assembly.py` | Plane issue data included in task context |
| **Events** | `events.py` | Plane change events (issue_created, updated, commented) |

---

## 6. Design Decisions

### Why PM-driven selection, not automatic sync?

Not every Plane issue is current work. The backlog has hundreds of
issues. Automatically syncing all to OCMC would flood agents with
irrelevant tasks. The PM evaluates sprint priority and creates OCMC
tasks for what matters NOW. Intelligence is in the PM, not in the sync.

### Why labels for methodology on Plane?

Plane CE has no custom fields. Labels are the only structured
metadata. Prefix convention (stage:, readiness:) prevents collision.
Valid readiness values match methodology.py exactly.

### Why verbatim in HTML, not labels?

Verbatim requirements are long text. Labels have length limits.
Hidden span markers in description_html allow full verbatim while
keeping it machine-parseable by transpose layer.

### Why one PM task → many ops tasks?

A PM task ("Add fleet controls") is STRATEGIC — it represents a
deliverable. Ops tasks are OPERATIONAL — they represent individual
work units. Each specialist contributes through their own ops task
with full stage progression. This separation lets specialists work
in parallel (architect designs while QA predefines tests) while
the PM task tracks overall progress.

---

## 7. NOT Implemented

- **Ops comment → Plane comment sync:** When ops tasks complete, the
  comment should appear on the Plane issue. Currently ops completions
  update the PM task but don't propagate to Plane comments.
- **PM pre-embed Plane sprint data (AR-11):** PM should see current
  sprint issues, priorities, module progress in heartbeat context.
- **Writer auto-update Plane pages:** When work completes, technical
  writer should scan Plane pages for staleness and update.
- **Artifact HTML on Plane issues:** Transpose renders artifacts but
  integration with Plane issue description updates is partial.

## 8. Test Coverage: **40+ tests**
