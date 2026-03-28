# OpenClaw Fleet

AI agent workforce powered by [OpenClaw](https://openclaw.ai) + [Mission Control](https://github.com/abhi1693/openclaw-mission-control).

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- [Claude Code](https://claude.ai/claude-code) CLI (`npm install -g @anthropic-ai/claude-code`)
- Claude Code authenticated (`claude auth login`)
- GitHub CLI authenticated (`gh auth login`)
- Git, curl, jq

## Setup

```bash
git clone <this-repo>
cd openclaw-fleet
./setup.sh
```

Setup handles everything: OpenClaw, auth, IRC, agents, Mission Control, The Lounge,
skills, templates, sync daemon, board monitor. Zero manual steps.

## Daily Operations

### 1. Open The Lounge (your command center)

```
http://localhost:9000  (user: fleet / pass: fleet)
```

Three channels:
- **#fleet** — all fleet activity (tasks, agents, status)
- **#alerts** — urgent items only (security, blockers, offline agents)
- **#reviews** — PRs ready for review, merge events

### 2. Create and dispatch work

```bash
# Create + dispatch to an agent on a project
make create-task TITLE="Fix auth bug in pipeline" AGENT=software-engineer PROJECT=nnrt DISPATCH=true

# Or separate steps
make create-task TITLE="Review architecture" AGENT=architect
make dispatch AGENT=architect TASK=<uuid>
```

### 3. Monitor progress

```bash
make status          # fleet overview (agents, tasks, activity)
make watch           # real-time agent events via WebSocket
make monitor TASK=<uuid>  # poll a specific task
make trace TASK=<uuid>    # full task context (MC + git + worktree)
make digest-preview  # preview today's daily digest
```

### 4. Review and merge

PRs appear in **#reviews** with clickable links. Click → review on GitHub → merge.

After merge, `make sync` (runs automatically every 60s) detects it and:
- Moves task to "done" in MC
- Cleans up the worktree
- Posts merge notification to IRC

Or: move task to "done" in MC → sync auto-merges the PR.

### 5. Communicate with agents

```bash
make chat MSG="What's the status of the NNRT work?"
make chat MSG="@architect review the pipeline changes"
```

Or type directly in IRC #fleet — agents see it.

## Fleet Skills (12)

| Skill | Purpose |
|-------|---------|
| `fleet-urls` | Resolve GitHub/MC URLs for cross-referencing |
| `fleet-pr` | Create publication-quality PRs with changelog |
| `fleet-comment` | Structured task comments (acceptance, progress, completion, blocker) |
| `fleet-memory` | Tagged board memory (alerts, decisions, suggestions) |
| `fleet-irc` | Structured IRC messages with emoji and URLs |
| `fleet-commit` | Conventional commits with task references |
| `fleet-task-update` | Task lifecycle (accept → progress → push → PR → review) |
| `fleet-task-create` | Create follow-up tasks for other agents |
| `fleet-alert` | Proactive alerts (security, quality, architecture) |
| `fleet-pause` | Pause and escalate when stuck or uncertain |
| `fleet-gap` | Detect missing capabilities in the fleet |
| `fleet-report` | Post structured reports to MC |

## Agents (8)

| Agent | Mode | Role |
|-------|------|------|
| architect | think | System design, architecture review |
| software-engineer | edit | Implementation, bug fixes, tests |
| qa-engineer | act | Testing, validation, coverage |
| ux-designer | think+edit | UI design, accessibility |
| devops | act | CI/CD, infrastructure, deployment |
| technical-writer | edit | Documentation |
| accountability-generator | think+edit | Accountability systems (ocf-tag) |
| fleet-ops | think+act | Governance: monitoring, digests, quality, gaps |

## Makefile Reference

### Setup & Provision
| Command | Description |
|---------|-------------|
| `make setup` | Full setup from clone |
| `make provision` | Re-sync after config changes |
| `make board-setup` | Configure board custom fields + tags |
| `make refresh-auth` | Refresh Claude Code token |

### Task Lifecycle
| Command | Description |
|---------|-------------|
| `make create-task TITLE=... AGENT=... PROJECT=... DISPATCH=true` | Create + dispatch |
| `make dispatch AGENT=... TASK=... [PROJECT=...]` | Dispatch existing task |
| `make monitor TASK=...` | Poll task progress |
| `make trace TASK=...` | Full task context |
| `make integrate TASK=... TARGET=...` | Integrate agent work |

### Observation
| Command | Description |
|---------|-------------|
| `make status` | Fleet overview |
| `make watch [AGENT=...]` | Real-time WS events |
| `make sessions` | List gateway sessions |
| `make chat MSG=...` | Board memory chat |

### Operations
| Command | Description |
|---------|-------------|
| `make sync` | One-shot task↔PR sync |
| `make sync-start` / `sync-stop` | Sync daemon |
| `make monitor-start` / `monitor-stop` | Board monitor daemon |
| `make digest` / `digest-preview` | Daily digest |
| `make quality` | Quality enforcement check |
| `make changelog` | Generate changelog |

### Skills
| Command | Description |
|---------|-------------|
| `make skills-list` | List installable marketplace skills |
| `make skills-install` | Install configured skills |
| `make skills-sync` | Re-sync skill packs |

### Infrastructure
| Command | Description |
|---------|-------------|
| `make gateway` / `gateway-stop` / `gateway-restart` | OpenClaw gateway |
| `make mc-up` / `mc-down` / `mc-logs` | Mission Control (Docker) |
| `make irc-up` / `irc-down` / `irc-connect` | IRC server |
| `make lounge-up` / `lounge-down` / `lounge-open` | The Lounge |
| `make agents` / `agents-register` | Agent management |
| `make clean` | Remove Docker volumes |

## Architecture

```
Human
  │
  ├── The Lounge (http://localhost:9000) ──→ IRC (#fleet, #alerts, #reviews)
  │                                              ↑
  ├── Mission Control (http://localhost:3000)     │ notify-irc.sh
  │     ├── Tasks, Comments, Board Memory         │
  │     ├── Custom Fields (project, branch, pr_url)
  │     └── Tags (project:*, type:*, needs-review)
  │                                              │
  ├── make create-task / dispatch ───────────────┤
  │     ↓                                        │
  │   OpenClaw Gateway (ws://localhost:18789)     │
  │     ↓ chat.send                              │
  │   Agent (Claude Code backend)                │
  │     ├── Reads TOOLS.md (credentials)         │
  │     ├── Reads SOUL.md (role + standards + workflow)
  │     ├── Uses fleet skills (12 skills)        │
  │     ├── Works in git worktree                │
  │     ├── Pushes branch + creates PR           │
  │     └── Reports to MC + IRC ─────────────────┘
  │
  ├── fleet-sync daemon (60s) ── merge/close PRs, cleanup worktrees
  ├── fleet-monitor daemon (5m) ── stale task alerts, agent health
  └── fleet-ops agent ── daily digest, quality, gap detection
```

## Project Structure

```
openclaw-fleet/
├── setup.sh                        # Full setup (11 steps)
├── Makefile                        # 35+ operation targets
├── docker-compose.yaml             # MC + The Lounge
├── agents/                         # Agent definitions
│   ├── _template/                  # Shared: STANDARDS.md, MC_WORKFLOW.md, markdown/
│   ├── architect/
│   ├── software-engineer/
│   ├── fleet-ops/                  # Governance agent
│   └── ...
├── .agents/skills/                 # Fleet skills (12, auto-discovered)
├── scripts/                        # 25+ operational scripts
├── config/
│   ├── url-templates.yaml          # Project → GitHub URL mapping
│   ├── skill-packs.yaml            # Marketplace skill sources
│   ├── skill-assignments.yaml      # Skills → agents mapping
│   ├── projects.yaml               # Project registry
│   ├── thelounge/                  # The Lounge config
│   └── ...
├── patches/                        # OCMC vendor patches
├── systemd/                        # Service template
├── docs/milestones/                # Planning documents (F1-F5)
├── projects/                       # Cloned project repos (gitignored)
├── workspace-mc-*/                 # Agent workspaces (gitignored)
└── vendor/                         # Mission Control (gitignored)
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Agent 401 errors | `make refresh-auth` |
| Agent blocked on exec | `bash scripts/configure-openclaw.sh` |
| MC not reachable | `make mc-up` |
| IRC not connected | `make irc-up && make gateway-restart` |
| The Lounge not loading | `make lounge-up` |
| Task stuck in inbox | `make dispatch AGENT=<name> TASK=<uuid>` |
| PR not merging | `make sync` (or check `make quality`) |
| Gateway down | `make gateway` |
| Stale tasks piling up | `make monitor-start` (alerts every 5min) |

## Built with AICP

Developed using [AICP](https://github.com/cyberpunk042/devops-expert-local-ai) — AI Control Platform.