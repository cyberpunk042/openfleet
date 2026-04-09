# CLAUDE.md — OpenFleet

## Project Overview

OpenFleet is an autonomous AI agent workforce — 10 specialized agents managed through Open gateway and Mission Control (OCMC). Agents collaborate to build software, conduct analysis, and execute missions across 4 projects.

Part of the fleet ecosystem:

| Project | Repo | Purpose |
|---------|------|---------|
| **Fleet** | `openfleet` | Agent operations, MCP tools, orchestrator, infrastructure |
| **AICP** | `devops-expert-local-ai` | AI Control Platform, LocalAI independence |
| **DSPD** | `devops-solution-product-development` | Project management via self-hosted Plane |
| **NNRT** | `Narrative-to-Neutral-Report-Transformer` | Report transformation NLP pipeline |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Plane (DSPD)                  Project Management Surface    │
│  sprints · epics · analytics   Primary: human, PM agent      │
└─────────────────────┬────────────────────────────────────────┘
                      │  PM bridges
┌─────────────────────▼────────────────────────────────────────┐
│  OCMC (Mission Control)        Agent Operations Surface      │
│  dispatch · heartbeat · approvals · board memory             │
│  Primary: fleet agents                                       │
└─────────────────────┬────────────────────────────────────────┘
                      │  agents execute
┌─────────────────────▼────────────────────────────────────────┐
│  GitHub + IRC + ntfy           Code + Comms Surface          │
│  PRs · CI · #fleet · #reviews · #alerts                      │
└──────────────────────────────────────────────────────────────┘
```

### Services

| Service | URL | Purpose |
|---------|-----|---------|
| Mission Control API | http://localhost:8000 | Task dispatch, agents, approvals |
| Mission Control UI | http://localhost:3000 | Web dashboard |
| Open Gateway | ws://localhost:18789 | Agent sessions, heartbeats, Claude Code |
| IRC Server | localhost:6667 | Real-time agent communication |
| The Lounge | http://localhost:9000 | Web IRC client (fleet/fleet) |
| LocalAI | http://localhost:8090 | Local inference (AICP project) |

### IRC Channels

`#fleet` `#alerts` `#reviews` `#sprint` `#agents` `#security` `#human` `#builds` `#memory` `#plane`

## Agent Roster

| Agent | Role | Heartbeat | Mode |
|-------|------|-----------|------|
| fleet-ops | Board lead, reviews, operations, quality | 30m | acceptEdits |
| project-manager | Sprint planning, task assignment, Plane bridge | 35m | acceptEdits |
| devsecops-expert | Security reviews, vulnerability scanning | 55m | default |
| architect | System design, technical decisions | 60m | plan |
| software-engineer | Implementation | 65m | acceptEdits |
| qa-engineer | Testing, quality assurance | 70m | acceptEdits |
| devops | Infrastructure, CI/CD, IaC | 75m | acceptEdits |
| technical-writer | Documentation, specs | 80m | acceptEdits |
| ux-designer | UI/UX design, user flows | 85m | acceptEdits |
| accountability-generator | Governance, compliance, accountability | 90m | acceptEdits |

## MCP Tools (13)

Agents interact with the fleet through these tools:

| Tool | Purpose |
|------|---------|
| `fleet_read_context` | Read task details, sprint context, board state |
| `fleet_task_accept` | Accept a task with a plan |
| `fleet_task_progress` | Report progress on current task |
| `fleet_commit` | Commit files with conventional message |
| `fleet_task_complete` | Complete task — runs tests, creates PR, notifies IRC |
| `fleet_alert` | Post alert to IRC channel |
| `fleet_pause` | Pause work, report blocker |
| `fleet_escalate` | Escalate to human or senior agent |
| `fleet_notify_human` | Send ntfy notification to human |
| `fleet_chat` | Post to internal chat (IRC) with @mentions |
| `fleet_task_create` | Create subtask with dependencies |
| `fleet_approve` | Approve/reject a review task |
| `fleet_agent_status` | Get fleet-wide agent and task status |

## Project Structure

```
fleet/                         # Main Python package (71 modules)
  core/                        # Domain logic
    models.py                  # Task, Agent, TaskStatus, TaskCustomFields
    orchestrator (cli/)        # The brain — 30s cycle, 6 steps
    budget_monitor.py          # Real Claude OAuth quota monitoring
    budget_modes.py            # Fleet tempo setting (speed/frequency)
    task_scoring.py            # Priority scoring for dispatch
    agent_lifecycle.py         # ACTIVE → IDLE → SLEEPING → OFFLINE
    agent_roles.py             # Roles, PR authority, secondary roles
    behavioral_security.py     # Behavioral analysis
    board_cleanup.py           # Archive noise tasks
    error_reporter.py          # File-based error log for orchestrator
    outage_detector.py         # MC/gateway/GitHub health tracking
    federation.py              # Multi-machine fleet identity
    heartbeat_context.py       # Pre-compute context without AI
    smart_chains.py            # Dispatch context pre-compute
    model_selection.py         # Opus vs sonnet by complexity
    plan_quality.py            # Plan quality enforcement
    remote_watcher.py          # PR comment detection from GitHub
    plane_sync.py              # Plane ↔ OCMC bidirectional sync
    velocity.py                # Sprint velocity tracking
    urls.py                    # URL resolver for cross-references
  infra/                       # External service clients
    mc_client.py               # Mission Control REST API (async)
    irc_client.py              # IRC via gateway
    gh_client.py               # GitHub CLI wrapper
    ntfy_client.py             # ntfy notification client
    plane_client.py            # Plane REST API (async)
    config_loader.py           # YAML + .env config
    cache_sqlite.py            # SQLite response cache
  mcp/                         # MCP server (13 tools)
    server.py                  # FastMCP server
    tools.py                   # Tool implementations
    context.py                 # Shared MCP context
  cli/                         # CLI commands
    orchestrator.py            # Orchestrator daemon
    daemon.py                  # All daemons (sync, monitor, auth, orchestrator)
    dispatch.py                # Task dispatch to agents
    sync.py                    # Board sync
    plane.py                   # Plane CLI (create/list/sync)
    sprint.py                  # Sprint plan loader
    status.py                  # Fleet status display
    pause.py                   # Pause/resume fleet
    ...
  templates/                   # Output templates (IRC, PR, comments, memory)
  tests/                       # 39 test files
agents/                        # Agent definitions (10 agents)
  {name}/SOUL.md               # Agent identity and mission
  {name}/HEARTBEAT.md          # Heartbeat instructions
  _template/                   # Template for new agents
config/                        # Fleet configuration
  fleet.yaml                   # Orchestrator, tempo, notifications
  agent-identities.yaml        # Agent roster and roles
  projects.yaml                # Project registry
scripts/                       # IaC scripts (42 scripts)
  setup.sh                     # Master setup — zero to running fleet
  start-fleet.sh               # Gateway startup
  setup-mc.sh                  # Mission Control setup
  clean-gateway-config.sh      # Dedup agents, stagger heartbeats
  configure-agent-settings.sh  # Per-agent Claude Code settings
  push-agent-framework.sh      # Push SOUL.md + STANDARDS.md to workspaces
  verify-communications.sh     # 8-point communication check
  ...
gateway/                       # MC setup and gateway configuration
  setup.py                     # MC registration (gateway, board, agents)
vendor/                        # Mission Control (Docker build context)
  openclaw-mission-control/    # Patched MC source
patches/                       # Vendor patches (survive git clone)
  0001-skills-marketplace-category-risk-upsert.patch
  0002-fix-tools-md-parser-markdown-format.patch
  0003-fix-agent-last-seen-at-on-provision-complete.patch
docs/milestones/               # Planning and tracking
  STATUS-TRACKER.md            # Source of truth — what's done, what's not
  README.md                    # Index to all docs
  active/                      # Work with remaining items (13 docs)
  design/                      # Architecture reference (16 docs)
  archive/                     # Completed/superseded (7 docs)
```

## Orchestrator (The Brain)

Runs every 30 seconds. 6 steps per cycle:

1. **Security scan** — check for anomalies
2. **Ensure approvals** — create approval requests for review tasks
3. **Wake lead** — alert fleet-ops about pending reviews
4. **Dispatch** — find unblocked inbox tasks, dispatch to agents (max 2/cycle)
5. **Evaluate parents** — all children done → parent to review
6. **Health check** — stuck tasks, offline agents

Safety:
- Budget monitor reads real Claude OAuth quota before every dispatch
- Work mode controls dispatch (work-paused, finish-current-work, etc.)
- Max 2 dispatches per cycle
- Error reporter + outage detector with exponential backoff

## Setup

```bash
# Full setup from zero (IaC — no manual steps)
./setup.sh

# Individual operations
make status        # Fleet overview
make gateway       # Start gateway
make mc-up         # Start Mission Control
make logs          # View gateway logs
make sync          # Sync tasks ↔ PRs

# Fleet commands
fleet pause        # Pause all dispatches
fleet resume       # Resume dispatches
fleet status       # Agent and task status
fleet budget set <mode>  # Set fleet tempo mode
fleet plane list-projects  # List Plane projects
```

## Development Conventions

- Python 3.11+, type hints everywhere
- Conventional commits: `type(scope): description [task:id]`
- Tests: `pytest fleet/tests/ -v`
- Lint: `ruff check fleet/`
- Format: `ruff format fleet/`
- No secrets in code — `.env` (gitignored)
- All config changes in scripts — zero manual steps after checkout
- Vendor patches in `patches/` — applied by `scripts/apply-patches.sh`

## Key Principles

1. **User is the leader** — agents execute, user decides direction
2. **Mission Control is the center** — feed it, don't replace it
3. **fleet-ops reviews everything** — no auto-approve, agents earn approval
4. **IaC only** — no manual commands, everything scripted
5. **Standards first** — conventional commits, changelogs, good patterns
6. **Local-first** — LocalAI for routine, Claude for complex (AICP mission)

## Documentation — 3 Layers

### Wiki (LLM-friendly, start here for planning)
- **Backlog**: `wiki/backlog/_index.md` — 17 epics (E001-E017), modules, tasks
- **Log**: `wiki/log/` — PO directives verbatim, chronological, sacrosanct
- **Domains**: `wiki/domains/` — knowledge pages by domain
- Pattern: LLM wiki (Karpathy) — YAML frontmatter, typed relationships, status lifecycle
- Feeds into: `../devops-solutions-research-wiki` (cross-project second brain)

### Docs (front-facing, architecture and systems)
- **Navigation**: `docs/README.md` — master index for ~100 docs, 5-layer hierarchy
- **Architecture**: `docs/ARCHITECTURE.md` — 20 systems, how they relate
- **Integration**: `docs/INTEGRATION.md` — 12 cross-system data flows
- **Spec vs Code**: `docs/SPEC-TO-CODE.md` — 69 specs mapped to 94 modules
- **System Docs**: `docs/systems/01-22` — per-system reference (10,283 lines)
- **Milestones**: `docs/milestones/active/MASTER-INDEX.md` — 255 milestones

### Code docs (inner, in the code)
- Module docstrings, type hints, inline comments
- Lives with the code it documents

## Config

- **Agent tooling**: `config/agent-tooling.yaml` — per-role MCP/plugins/skills
- **Agent autonomy**: `config/agent-autonomy.yaml` — per-role lifecycle thresholds
- **Phases**: `config/phases.yaml` — PO-defined delivery phases
- **Skills**: `config/skill-stage-mapping.yaml` — skills → methodology stages × roles
- **CRONs**: `config/agent-crons.yaml` — 17 scheduled operations
- **Standing orders**: `config/standing-orders.yaml` — per-role autonomous authority
- **Hooks**: `config/agent-hooks.yaml` — structural enforcement per role
- **Synergy matrix**: `config/synergy-matrix.yaml` — contribution requirements

## Related

- **Research Wiki**: `../devops-solutions-research-wiki` — LLM wiki second brain (cross-project)
- **OpenArms**: `../openarms` — gateway fork with wiki/backlog pattern
- **DSPD mission**: `../devops-solution-product-development/config/mission.yaml`
- **AICP LocalAI**: `../devops-expert-local-ai/CLAUDE.md`
- **Strategic vision**: `docs/milestones/active/strategic-vision-localai-independence.md`