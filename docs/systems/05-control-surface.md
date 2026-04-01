# System 5: Control Surface

**Source:** `fleet/core/fleet_mode.py` (100 lines), `fleet/core/effort_profiles.py` (80 lines), `fleet/core/directives.py` (60+ lines)
**Status:** 🔨 Code exists, orchestrator reads it every cycle. Frontend NOT built.
**Design docs:** `fleet-control-surface.md` (M-CS01–10)

---

## Purpose

PO command & control. Three independent axes control fleet behavior. PO can pause, restrict, redirect, or override from the OCMC header bar. Directives route PO commands to specific agents.

## Key Concepts

### Three Axes (fleet_mode.py:20-41)

**Work Mode** (5 options):
- `full-autonomous` — all agents active, Plane pulling
- `project-management-work` — PM drives, no Plane pulling
- `local-work-only` — OCMC tasks only
- `finish-current-work` — no new dispatch
- `work-paused` — nothing runs

**Cycle Phase** (6 options):
- `execution` — all agents
- `planning` — project-manager + architect only
- `analysis` — architect + project-manager only
- `investigation` — any assigned agent
- `review` — fleet-ops only
- `crisis-management` — fleet-ops + devsecops only

**Backend Mode** (3 options):
- `claude` / `localai` / `hybrid`

Axes are independent. Any combination is valid.

### Effort Profiles (effort_profiles.py:34-79)

| Profile | Dispatch | Driver HB | Worker HB | Opus | Active Agents |
|---------|----------|-----------|-----------|------|---------------|
| full | 2/cycle | 30min | 60min | Yes | all |
| conservative | 1/cycle | 60min | 120min | No | PM, fleet-ops, devsecops |
| minimal | 0 | 120min | disabled | No | fleet-ops only |
| paused | 0 | disabled | disabled | No | none |

### Directives (directives.py)

PO posts to board memory: `tags: ["directive", "to:agent-name", "from:human"]`
Orchestrator parses each cycle, routes to target agent's heartbeat context.
Processed directives tagged with "processed" to avoid re-processing.

### Fleet State Reading (fleet_mode.py:54-70)

Read from board's `fleet_config` JSON field every orchestrator cycle:
```python
FleetControlState(work_mode, cycle_phase, backend_mode, updated_at, updated_by)
```

### Phase-Specific Agent Filtering (fleet_mode.py:87-100)

Cycle phase determines which agents are active:
- crisis-management: only fleet-ops + devsecops
- planning: only PM + architect
- review: only fleet-ops
- execution: all

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Reads fleet state every cycle, gates dispatch | Control → Orchestrator |
| **Effort Profiles** | Limits dispatch rate, heartbeat frequency, model access | Profiles → Orchestrator |
| **Directives** | PO commands parsed and routed to agents | Directives → Preembed |
| **Budget** | Budget pressure can force mode transitions | Budget → Control |
| **Storm** | Storm forcing overrides budget mode | Storm → Control |
| **Events** | Mode changes emit events | Control → Events |

### PO Requirement (Verbatim)

> "I should be able to say go to the fleet / the project manager and tell him he can start working on the first priority. I should be able to Pause and even Stop and I should be able to see the stream of events and their impacts"

## What's Needed

- [ ] FleetControlBar frontend component (M-CS02)
- [ ] Backend patch for fleet_config on Board model (M-CS01)
- [ ] UI integration in DashboardShell.tsx header
- [ ] Budget mode dropdown in control bar (M-BM05 patch exists)
