# Control Surface — PO Command & Control

> **3 files. 305 lines. The PO controls the fleet through three independent axes.**
>
> Three independent control axes determine fleet behavior: Work Mode
> (where work comes from), Cycle Phase (what kind of work agents do),
> and Backend Mode (which AI processes requests). Plus effort profiles
> that throttle intensity, and directives that route PO commands to
> specific agents. Read from the OCMC board's fleet_config JSON field
> every orchestrator cycle.

---

## 1. Why It Exists

Without the control surface, the PO has no way to:
- Pause the fleet during a crisis
- Restrict which agents are active
- Switch between Claude and LocalAI
- Send direct commands to specific agents
- Throttle spending when budget is tight

The control surface gives the PO real-time, fine-grained control
over fleet behavior — without modifying code or config files.

### PO Requirements (Verbatim)

> "I should be able to say go to the fleet / the project manager and
> tell him he can start working on the first priority. I should be able
> to Pause and even Stop and I should be able to see the stream of
> events and their impacts"

> "I can even chose a cycle and force being in planning or analysis
> or investigation or crisis management....."

> "I have to be in charge and yet be able to let them work and then
> again be able to chose the mode of work"

---

## 2. How It Works

### 2.1 The Three Axes

```
┌─────────────────────────────────────────────────────────────┐
│                    FLEET CONTROL SURFACE                     │
│                                                              │
│  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │     WORK MODE       │  │  CYCLE PHASE    │  │ BACKEND │ │
│  │                     │  │                 │  │  MODE   │ │
│  │ full-autonomous     │  │ execution       │  │ claude  │ │
│  │ pm-work             │  │ planning        │  │ localai │ │
│  │ local-work-only     │  │ analysis        │  │ hybrid  │ │
│  │ finish-current      │  │ investigation   │  │         │ │
│  │ work-paused         │  │ review          │  │         │ │
│  │                     │  │ crisis-mgmt     │  │         │ │
│  └─────────────────────┘  └─────────────────┘  └─────────┘ │
│                                                              │
│  Axes are INDEPENDENT. Any combination is valid.             │
│  E.g., local-work-only + planning + hybrid = PM and          │
│  architect plan from OCMC tasks using both Claude and LocalAI│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Work Mode — Where Work Comes From

| Mode | What It Means | Dispatch? | Plane Pull? |
|------|-------------|-----------|-------------|
| `full-autonomous` | All agents active, PM pulls from Plane | Yes | Yes |
| `project-management-work` | PM drives, no Plane pulling | Yes | No |
| `local-work-only` | OCMC tasks only, no external work | Yes | No |
| `finish-current-work` | No new dispatch, finish what's in progress | No | No |
| `work-paused` | Nothing runs | No | No |

**Important:** "Local Work Only" does NOT mean LocalAI. It means
OCMC-local (only tasks on the Mission Control board). Plane sync
still runs — it just doesn't pull new work.

### 2.3 Cycle Phase — What Agents Do

| Phase | Active Agents | What They Do |
|-------|--------------|-------------|
| `execution` | All | Normal work — all stages |
| `planning` | PM + Architect | Sprint planning, task breakdown |
| `analysis` | Architect + PM | Codebase analysis, investigation |
| `investigation` | Any assigned | Research, exploration |
| `review` | Fleet-ops only | Approval processing, quality checks |
| `crisis-management` | Fleet-ops + DevSecOps | Incident response, security triage |

Phase filtering applied by orchestrator at dispatch time:
`get_active_agents_for_phase(state)` returns which agents can work.

### 2.4 Effort Profiles — Throttle Intensity

| Profile | Dispatch | Driver HB | Worker HB | Opus? | Active Agents |
|---------|----------|-----------|-----------|-------|---------------|
| `full` | 2/cycle | 30min | 60min | Yes | all |
| `conservative` | 1/cycle | 60min | 120min | No | PM, fleet-ops, devsecops |
| `minimal` | 0 | 120min | disabled | No | fleet-ops only |
| `paused` | 0 | disabled | disabled | No | none |

Active profile read from `config/fleet.yaml`:
```yaml
orchestrator:
  effort_profile: "conservative"  # currently set after March drain
```

### 2.5 Directives — PO Commands to Agents

PO posts to board memory with tags:
```
content: "PM: start working on AICP Stage 1"
tags: ["directive", "to:project-manager", "from:human"]
```

Orchestrator reads every cycle → routes to target agent's heartbeat context.

Directive tags:
- `directive` — identifies as directive (required)
- `to:{agent-name}` — target agent (optional, default = all)
- `from:human` — source (always human)
- `urgent` — high priority flag (optional)
- `processed` — marks as handled (added after processing)

### 2.6 Reading State — Every Cycle

```
Board fleet_config JSON
  ↓
read_fleet_control(board_data) → FleetControlState
  ↓
Orchestrator checks:
  ├── should_dispatch(state) → False if paused/finish-current
  ├── should_pull_from_plane(state) → False if local/paused/finish
  ├── get_active_agents_for_phase(state) → agent filter
  └── Mode change detected? → emit event + IRC notification
```

---

## 3. File Map

```
fleet/core/
├── fleet_mode.py       Work mode, cycle phase, backend mode  (99 lines)
├── effort_profiles.py  4 throttle profiles                   (116 lines)
└── directives.py       PO command parsing and formatting     (90 lines)

config/
└── fleet.yaml          Active effort profile                 (references)
```

Total: **305 lines** across 3 focused modules.

---

## 4. Per-File Documentation

### 4.1 `fleet_mode.py` — Three Axes (99 lines)

#### Constants

| Name | Type | Values |
|------|------|--------|
| `WORK_MODES` | list[str] | full-autonomous, project-management-work, local-work-only, finish-current-work, work-paused |
| `CYCLE_PHASES` | list[str] | execution, planning, analysis, investigation, review, crisis-management |
| `BACKEND_MODES` | list[str] | claude, localai, hybrid |

#### Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `FleetControlState` | 44-51 | Dataclass: work_mode, cycle_phase, backend_mode, updated_at, updated_by |

#### Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `read_fleet_control(board_data)` | 54-70 | Reads fleet_config from board dict → FleetControlState. Defaults: full-autonomous, execution, claude. |
| `should_dispatch(state)` | 73-75 | Returns False if work-paused or finish-current-work. |
| `should_pull_from_plane(state)` | 78-84 | Returns False if local-work-only, work-paused, or finish-current-work. |
| `get_active_agents_for_phase(state)` | 87-100 | Returns agent filter list per phase. None = all agents active. Crisis = fleet-ops + devsecops only. Planning = PM + architect. Review = fleet-ops only. |

### 4.2 `effort_profiles.py` — Throttle Profiles (116 lines)

#### Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `EffortProfile` | 20-31 | Dataclass: name, description, max_dispatch_per_cycle, heartbeat_drivers_min, heartbeat_workers_min, allow_opus, allow_dispatch, allow_heartbeats, active_agents |

#### Constants

| Name | Type | Purpose |
|------|------|---------|
| `PROFILES` | dict[str, EffortProfile] | 4 profiles: full, conservative, minimal, paused |

#### Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `get_profile(name)` | 82-84 | Get profile by name. Returns None if not found. |
| `get_active_profile_name(fleet_dir)` | 87-105 | Read active profile from config/fleet.yaml → orchestrator.effort_profile. Default: "full". |
| `should_dispatch(profile)` | 108-110 | Check if dispatching allowed (allow_dispatch AND max_dispatch > 0). |
| `is_agent_active(profile, agent_name)` | 113-116 | Check if agent allowed under profile. "all" in active_agents = everyone allowed. |

### 4.3 `directives.py` — PO Commands (90 lines)

#### Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `Directive` | 27-35 | Dataclass: id, content, target_agent (None=all), source, urgent, created_at |

#### Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `parse_directives(memory_entries)` | 38-82 | Scans board memory for "directive" tagged entries not yet "processed". Extracts target from "to:{agent}" tag. Returns list[Directive]. |
| `format_directive_for_agent(directive)` | 85-90 | Formats for heartbeat context: "🚨 URGENT DIRECTIVE from human:\n{content}" or without urgent prefix. |

---

## 5. Dependency Graph

```
fleet_mode.py       ← standalone (dataclasses only)

effort_profiles.py  ← standalone (reads config/fleet.yaml via yaml)

directives.py       ← standalone (dataclasses, logging)
```

All three modules are independent. No circular dependencies.
No imports from each other. All consumed by the orchestrator.

---

## 6. Consumers

| Layer | Module | What It Imports | How It Uses It |
|-------|--------|----------------|---------------|
| **Orchestrator** | `orchestrator.py` | `FleetControlState, read_fleet_control, should_dispatch, get_active_agents_for_phase` | Reads state every cycle. Gates dispatch. Filters agents by phase. Detects mode changes → emits events. |
| **Orchestrator** | `orchestrator.py` | `get_active_profile_name, get_profile` | Reads active profile. Applies dispatch rate limit. Overrides max_dispatch. |
| **Orchestrator** | `orchestrator.py` | `parse_directives, format_directive_for_agent` | Step 6: parses PO directives from board memory. Step 0: includes in agent heartbeat context. |
| **Context Assembly** | `context_assembly.py` | `parse_directives` | Includes directives in heartbeat context assembly. |
| **Storm Integration** | `storm_integration.py` | — (indirect) | Storm forces budget mode, which is stored in fleet_config alongside control state. |

---

## 7. Design Decisions

### Why three independent axes?

Each axis answers a different question:
- Work Mode: "Where does new work come from?"
- Cycle Phase: "What kind of work should happen?"
- Backend Mode: "Which AI processes it?"

Making them independent means any combination is valid. The PO can
run in planning mode with Claude (PM + architect design with full
power) or in crisis mode with LocalAI (fleet-ops + devsecops respond
using free backend). Coupling them would reduce flexibility.

### Why effort profiles separate from work mode?

Work mode is about WHAT happens. Effort profiles are about HOW MUCH.
"Full autonomous" with "conservative" profile = all agents active
but slower heartbeats and no opus. "Local work only" with "full"
profile = only OCMC tasks but maximum power. Different controls
for different needs.

### Why directives via board memory, not a special API?

Board memory is already the PO's communication surface. Directives
are just tagged board memory entries. This means:
1. The PO doesn't need a new tool — same surface they already use
2. Directives are visible to all agents (transparency)
3. Directives are persistent (survive restarts)
4. Directives are auditable (board memory is logged)

### Why is the profile read from YAML, not from board?

Effort profiles are infrastructure configuration, not runtime control.
The PO sets them less frequently than work mode. YAML in git means
the profile is part of IaC — version-controlled, reproducible.
Work mode changes happen via the OCMC UI (runtime). Profiles change
via config commits (infrastructure).

### Why does crisis-management activate fleet-ops + devsecops only?

During a crisis, the fleet needs focused response, not 10 agents
competing for attention. Fleet-ops monitors and triages. DevSecOps
investigates and mitigates. Other agents would consume tokens without
contributing to crisis resolution.

---

## 8. State Flow Diagram

```
PO sets work mode via OCMC UI
  ↓
board.fleet_config.work_mode = "work-paused"
  ↓
Orchestrator cycle reads board:
  read_fleet_control(board_data) → FleetControlState(work_mode="work-paused")
  ↓
should_dispatch(state) → False
  ↓
Orchestrator skips dispatch step
  ↓
Mode change detected (previous was "full-autonomous"):
  → Emit fleet.system.mode_changed event
  → IRC: "[orchestrator] work_mode: full-autonomous → work-paused"
  ↓
Next cycle: still paused → still no dispatch
  ↓
PO changes to "full-autonomous":
  → Dispatch resumes
  → Event emitted
  → IRC notification
```

---

## 9. Data Shapes

### FleetControlState

```python
FleetControlState(
    work_mode="full-autonomous",
    cycle_phase="execution",
    backend_mode="claude",
    updated_at="2026-03-31T15:00:00",
    updated_by="po",
)
```

### EffortProfile

```python
EffortProfile(
    name="conservative",
    description="Budget-conscious — drivers only, sonnet only, less frequent",
    max_dispatch_per_cycle=1,
    heartbeat_drivers_min=60,
    heartbeat_workers_min=120,
    allow_opus=False,
    allow_dispatch=True,
    allow_heartbeats=True,
    active_agents=["project-manager", "fleet-ops", "devsecops-expert"],
)
```

### Directive

```python
Directive(
    id="mem-uuid-here",
    content="PM: start working on AICP Stage 1",
    target_agent="project-manager",
    source="human",
    urgent=False,
    created_at="2026-03-31T15:00:00",
)
```

### Board fleet_config (stored in OCMC)

```json
{
    "work_mode": "full-autonomous",
    "cycle_phase": "execution",
    "backend_mode": "claude",
    "budget_mode": "standard",
    "updated_at": "2026-03-31T15:00:00",
    "updated_by": "po"
}
```

---

## 10. What's Needed

### Frontend (M-CS01–10)

| Milestone | What | Status |
|-----------|------|--------|
| M-CS01 | Backend patch: fleet_config JSON field on Board model | 📐 Design |
| M-CS02 | FleetControlBar component in DashboardShell.tsx | 📐 Design |
| M-CS03–05 | Work Mode, Cycle Phase, Backend Mode dropdowns | 📐 Design |
| M-CS06–08 | Orchestrator integration for each axis | 🔨 Code exists |
| M-CS09–10 | Agent count badge, directive input | 📐 Design |

The backend code exists (fleet_mode.py works). The frontend does
not — the PO currently changes modes via config or API, not UI.

### Integration Gaps

- Budget mode dropdown (M-BM05) — TSX patch exists but not deployed
- Directive processing in orchestrator Step 6 — implemented but
  directive "processed" tagging may not work reliably
- Mode change events — emitted but not tested end-to-end

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_fleet_mode.py` | 15+ | Modes, phases, dispatch gates, agent filters |
| `test_effort_profiles.py` | 10+ | Profiles, dispatch checks, agent active checks |
| `test_directives.py` | 10+ | Parsing, formatting, tag extraction |
| **Total** | **35+** | Core logic covered. Missing: mode change event flow |
