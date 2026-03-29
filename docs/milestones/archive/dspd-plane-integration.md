# DSPD — DevOps Solution Product Development via Plane

## User Requirements

> "we are now going to do the DSPD, we are going to use https://github.com/makeplane/plane"

> "this is going to be a vendor and we will setup ourself in it and weave ourself and do our own cause and own interface via cli like the fleet is doing with ocmc a bit"

> "The ocmc is a board for the AI but it has just a fleet select and then 4 stage process with a few detail, but that is no in way a project management tool. the project manager need a real tool and everyone."

> "mostly the project manager because he is going to do the bridge for anyone who doesn't work directly with the project management tool and kindly remind them"

## The Problem

OCMC (OpenClaw Mission Control) is an **AI agent operations board** — good for:
- Agent task dispatch (inbox → in_progress → review → done)
- Agent-to-human communication (board memory, comments)
- Approval gates, heartbeat monitoring

But OCMC is NOT a project management tool. It lacks:
- Sprints / cycles with burn-down
- Modules / epics / initiatives
- Timeline and calendar views
- Story points and velocity tracking
- Cross-project dependency mapping
- Analytics and productivity metrics
- Pages / wiki for documentation
- Labels, priorities, custom workflows beyond 4 stages

The project-manager agent needs a REAL tool. The fleet needs organized
development across multiple projects (fleet, NNRT, DSPD itself, AICP, future).

## The Solution: Plane

**Plane** (https://github.com/makeplane/plane) — open-source project management.

### Why Plane

| Requirement | Plane |
|------------|-------|
| Open source | ✅ AGPLv3 |
| Self-hosted | ✅ Docker Compose |
| REST API | ✅ Full API with API keys |
| MCP support | ✅ Built-in MCP server |
| Sprints/cycles | ✅ With burn-down charts |
| Modules/epics | ✅ Hierarchical organization |
| Views | ✅ Kanban, list, timeline, calendar |
| Analytics | ✅ Real-time insights |
| Webhooks | ✅ Full event system |
| Cost | ✅ Free (self-hosted, no per-seat) |
| Tech stack | ✅ Django + React (we know Python) |
| Import | ✅ Jira, Linear, Asana importers |

### Architecture: Three Surfaces

```
OCMC (Mission Control)          — AI agent operations
  ├── Agent dispatch, heartbeat, board memory
  ├── Task lifecycle for AGENTS (inbox → done)
  └── Approval gates

Plane (DSPD)                    — Project management
  ├── Sprints, cycles, modules, epics
  ├── Cross-project work items
  ├── Analytics, velocity, burn-down
  ├── Pages/wiki for specs and docs
  └── Human + PM agent primary surface

Fleet CLI                       — Orchestration bridge
  ├── Syncs between OCMC and Plane
  ├── PM creates Plane items → dispatches via OCMC to agents
  ├── Agent completes → PM updates Plane item
  └── Human works in Plane, agents work in OCMC
```

### The Bridge: Project Manager

The PM agent is the bridge:
1. Human creates work items in Plane (sprints, stories, epics)
2. PM reads Plane → creates corresponding OCMC tasks for agents
3. Agent completes OCMC task → PM updates Plane item with results
4. Human sees progress in Plane (burn-down, velocity, analytics)

Agents don't need to use Plane directly. PM handles the translation.
But anyone CAN use Plane — it's the source of truth for project state.

## Implementation Plan

### Phase 1: Self-Host Plane (Docker)

**What:**
- Add Plane to docker-compose.yaml (or separate compose)
- Configure workspace, project, API key
- Script in setup.sh

**Requirements:**
- 4GB+ RAM (Plane needs PostgreSQL, Redis, worker, web, API)
- Port 8080 (or configurable)
- Separate PostgreSQL instance or shared with MC

**Milestones:**
| # | Milestone | Scope |
|---|-----------|-------|
| M184 | Research Plane Docker setup | Test locally, understand config |
| M185 | Add Plane to fleet docker-compose | Self-hosted, scripted |
| M186 | Configure workspace + project | fleet workspace, NNRT project |
| M187 | Generate API key + test API | Verify work item CRUD |

### Phase 2: Fleet CLI Integration

**What:**
- `fleet/infra/plane_client.py` — Plane REST API client
- `fleet/cli/plane.py` — CLI commands for Plane operations
- `fleet plan create "title"` → creates Plane work item
- `fleet plan list` → shows current sprint
- `fleet plan sync` → syncs Plane ↔ OCMC

**Milestones:**
| # | Milestone | Scope |
|---|-----------|-------|
| M188 | fleet/infra/plane_client.py | Plane REST API wrapper |
| M189 | fleet/cli/plane.py | create, list, sync commands |
| M190 | Plane ↔ OCMC sync | Work items → OCMC tasks, results back |
| M191 | PM agent Plane integration | PM reads/writes Plane via MCP |

### Phase 3: MCP Integration

**What:**
- Plane has built-in MCP support — agents can interact with Plane directly
- Add Plane MCP server to agent config
- PM agent uses Plane MCP for sprint management

**Milestones:**
| # | Milestone | Scope |
|---|-----------|-------|
| M192 | Research Plane MCP server | What tools does it expose? |
| M193 | Configure Plane MCP for PM agent | PM gets native Plane tools |
| M194 | PM drives sprints via Plane | Sprint planning, velocity, burn-down |

### Phase 4: Full DSPD Product

**What:**
- Plane as the project management surface for all fleet development
- Human uses Plane for planning, agents execute via OCMC
- PM bridges the gap
- Analytics, velocity tracking, cross-project dependencies
- Custom workflows per project

**Milestones:**
| # | Milestone | Scope |
|---|-----------|-------|
| M195 | Multi-project setup in Plane | fleet, NNRT, AICP, DSPD projects |
| M196 | Sprint workflow | PM creates sprints, assigns, tracks |
| M197 | Cross-project dependencies | fleet depends on NNRT, etc. |
| M198 | Analytics dashboard | Velocity, burn-down, agent productivity |
| M199 | DSPD v1.0 | Full project management surface operational |

## What OCMC Remains For

OCMC doesn't go away. The surfaces have distinct purposes:

| Surface | Purpose | Primary Users |
|---------|---------|--------------|
| **Plane** | Project management, planning, analytics | Human, PM agent |
| **OCMC** | Agent operations, dispatch, approvals | Agents, fleet-ops |
| **IRC** | Real-time alerts and interaction | Human, all agents |
| **GitHub** | Code review, PRs, CI | Human, all agents |

## Plane Docker Details (from research)

```bash
# One-line install
curl -fsSL https://prime.plane.so/install/ | sh -

# Or Docker Compose
# Needs: PostgreSQL, Redis, API, Web, Worker, Beat
# Ports: 80/443 (configurable)
# RAM: 4GB minimum, 8GB recommended
```

### API Authentication

```bash
# API Key in header
curl -H "X-API-Key: <key>" https://plane.local/api/v1/workspaces/
```

### Key API Endpoints

| Resource | Endpoint |
|----------|----------|
| Projects | `/api/v1/workspaces/{slug}/projects/` |
| Work Items | `/api/v1/workspaces/{slug}/projects/{id}/issues/` |
| Cycles | `/api/v1/workspaces/{slug}/projects/{id}/cycles/` |
| Modules | `/api/v1/workspaces/{slug}/projects/{id}/modules/` |
| Labels | `/api/v1/workspaces/{slug}/projects/{id}/labels/` |
| States | `/api/v1/workspaces/{slug}/projects/{id}/states/` |

### Webhooks

Events: project.*, issue.*, cycle.*, module.*, comment.*
Payload includes HMAC-SHA256 signature for verification.

## Open Questions

1. **Separate Docker Compose or same?** Plane needs its own PostgreSQL + Redis.
   Running in same compose would be heavy. Separate compose = cleaner isolation.

2. **Port allocation?** MC on 8000/3000, Plane on 8080? Configurable.

3. **Data sync strategy?** One-way (Plane → OCMC) or bidirectional?
   Start one-way: PM creates OCMC tasks from Plane items.
   Later: bidirectional sync for status updates.

4. **Plane MCP vs fleet CLI?** Both. MCP for PM agent native access.
   Fleet CLI for human and scripted operations.

5. **Migration of existing OCMC tasks?** Import current board state into Plane?
   Or start fresh in Plane and keep OCMC for agent operations only?