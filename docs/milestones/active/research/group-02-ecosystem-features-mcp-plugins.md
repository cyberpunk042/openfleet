# Research Group 02 — Full Ecosystem: Claude Code Features + MCP Servers + Plugins

**Date:** 2026-04-02
**Status:** RESEARCHED — findings ready for PO review and classification
**Workflow step:** 1/4 (Research → Classify → Document → Build)

> This research defines what our agents CAN use. Every command, every tool,
> every plugin, every MCP server. The agent files (CLAUDE.md, TOOLS.md,
> HEARTBEAT.md) will reference these capabilities. Nothing gets built
> until this is classified per role and documented.

---

## Part 1: Claude Code Built-In Features (50+ commands, 33 tools, 26 hooks)

### Slash Commands — Complete List

**Session Management:**
| Command | What It Does |
|---------|-------------|
| `/clear` | Clear conversation, free context |
| `/compact [focus]` | Compact with optional preservation instructions |
| `/resume [id]` | Resume session by ID or name |
| `/rewind` | Rewind to previous checkpoint |
| `/branch [name]` | Branch conversation at this point |
| `/rename [name]` | Rename session |
| `/export [file]` | Export as plain text |
| `/exit` | Exit CLI |

**Model & Effort:**
| Command | What It Does |
|---------|-------------|
| `/model [model]` | Select model, slider adjusts effort |
| `/effort [level]` | Set: low, medium, high, max (opus only), auto |
| `/fast [on\|off]` | Toggle fast mode (same Opus, speed-optimized API) |

**Context & Cost:**
| Command | What It Does |
|---------|-------------|
| `/context` | Visualize context as colored grid with suggestions |
| `/cost` | Token usage statistics |
| `/usage` | Plan usage limits + rate limit status |

**Configuration:**
| Command | What It Does |
|---------|-------------|
| `/config` | Open settings |
| `/permissions` | Manage allow/ask/deny rules |
| `/hooks` | View hook configurations |
| `/statusline` | Configure status line |
| `/init` | Initialize project with CLAUDE.md |
| `/memory` | Edit CLAUDE.md, toggle auto-memory |
| `/sandbox` | Toggle sandbox mode |

**Git & Code:**
| Command | What It Does |
|---------|-------------|
| `/diff` | Interactive diff viewer |
| `/plan [desc]` | Enter plan mode |
| `/pr-comments [PR]` | Fetch GitHub PR comments |
| `/security-review` | Analyze branch changes for vulnerabilities |

**Agents & Tasks:**
| Command | What It Does |
|---------|-------------|
| `/agents` | Manage subagent configurations |
| `/skills` | List available skills |
| `/tasks` | List/manage background tasks |
| `/plugin` | Manage plugins |

**Bundled Skills (invoked with /):**
| Command | What It Does |
|---------|-------------|
| `/batch <instruction>` | Orchestrate parallel changes (worktrees, agents, PRs) |
| `/claude-api` | Load Claude API reference |
| `/debug [desc]` | Enable debug logging, troubleshoot |
| `/loop [interval] <prompt>` | Run prompt repeatedly (default 10m) |
| `/simplify [focus]` | Review changed files, fix quality (3 parallel agents) |

### Built-In Tools — 33 Total

`Agent`, `AskUserQuestion`, `Bash`, `CronCreate`, `CronDelete`, `CronList`,
`Edit`, `EnterPlanMode`, `EnterWorktree`, `ExitPlanMode`, `ExitWorktree`,
`Glob`, `Grep`, `ListMcpResourcesTool`, `LSP`, `NotebookEdit`, `PowerShell`,
`Read`, `ReadMcpResourceTool`, `SendMessage`, `Skill`, `TaskCreate`, `TaskGet`,
`TaskList`, `TaskOutput`, `TaskStop`, `TaskUpdate`, `TeamCreate`, `TeamDelete`,
`TodoWrite`, `ToolSearch`, `WebFetch`, `WebSearch`, `Write`

### Hook Event Types — 26 Total

| Hook | When | Can Block? |
|------|------|-----------|
| `SessionStart` | Session begins/resumes | No |
| `SessionEnd` | Session closes | No |
| `InstructionsLoaded` | CLAUDE.md parsed | No |
| `UserPromptSubmit` | User sends prompt | Yes |
| `PreToolUse` | Before tool executes | Yes (allow/deny/ask) |
| `PostToolUse` | After tool succeeds | Yes |
| `PostToolUseFailure` | After tool fails | No |
| `PermissionRequest` | Permission dialog appears | Yes |
| `PermissionDenied` | Auto mode denies tool | No |
| `Notification` | Notification sent | No |
| `SubagentStart` | Subagent spawns | No |
| `SubagentStop` | Subagent finishes | Yes |
| `TaskCreated` | Task created | Yes |
| `TaskCompleted` | Task completed | Yes |
| `Stop` | Claude finishes responding | Yes |
| `StopFailure` | Turn ends from API error | No |
| `TeammateIdle` | Teammate about to idle | Yes |
| `ConfigChange` | Config file changes | Yes |
| `CwdChanged` | Working directory changes | No |
| `FileChanged` | Watched file changes | No |
| `WorktreeCreate` | Worktree created | Yes |
| `WorktreeRemove` | Worktree removed | No |
| `PreCompact` | Before compaction | No |
| `PostCompact` | After compaction | No |
| `Elicitation` | MCP requests user input | Yes |
| `ElicitationResult` | User responds to MCP | Yes |

**Handler types:** command (shell), http (POST), prompt (LLM), agent (subagent)

### Permission Modes — 6

| Mode | Description |
|------|-------------|
| `default` | Prompts on first use |
| `acceptEdits` | Auto-accepts file edits |
| `plan` | Read-only |
| `auto` | Background classifier auto-approves |
| `dontAsk` | Auto-denies unless pre-approved |
| `bypassPermissions` | Skips all prompts (protected dirs still prompt) |

### Effort Levels — 4

| Level | Persistence | Availability |
|-------|-------------|-------------|
| `low` | Across sessions | Opus, Sonnet |
| `medium` | Across sessions (default) | Opus, Sonnet |
| `high` | Across sessions | Opus, Sonnet |
| `max` | Current session only | Opus ONLY |

Trigger: "ultrathink" in prompt for one-turn high effort.

### Agent Teams (Experimental)

- Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Components: Team Lead + Teammates + shared Task List + Mailbox
- Display: `in-process`, `tmux`, `auto` (split panes)
- Sweet spot: 3-5 teammates, 5-6 tasks each
- Token cost: ~7x single session
- Hooks: `TeammateIdle`, `TaskCreated`, `TaskCompleted`
- Tools: `TeamCreate`, `TeamDelete`, `SendMessage`

### Memory System

- **CLAUDE.md:** Project rules (managed policy > project > user)
- **`.claude/rules/`:** Modular instructions, path-specific frontmatter
- **Auto memory:** `~/.claude/projects/<project>/memory/MEMORY.md` (200 lines loaded)
- **Subagent memory:** user/project/local scopes

### Skills System

- Locations: Enterprise, Personal, Project, Plugin
- Frontmatter: model, effort, context (fork), agent, hooks, paths, shell
- Dynamic context: `` !`command` `` — shell output as context
- Substitutions: `$ARGUMENTS`, `$N`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`

---

## Part 2: MCP Server Ecosystem (11,870+ servers, 32 cataloged)

### Filesystem & Git

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 1 | Filesystem | `@modelcontextprotocol/server-filesystem` | read/write/move/search/list (8) | ENG, QA, WRITER, DEVOPS | None |
| 2 | Git | `mcp-server-git` (pip) | status/diff/commit/branch/log (9) | ENG, QA, DEVOPS, ARCH | None |
| 3 | GitHub | `github/github-mcp-server` (Go/Docker) | 80+ tools (issues, PRs, Actions, search, Dependabot) | ALL | PAT/OAuth |
| 4 | GitLab | `@modelcontextprotocol/server-gitlab` | issues, MRs, files, search | ENG, DEVOPS, PM | PAT |

### Containers & Infrastructure

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 5 | Docker | `mcp-server-docker` | 25 tools (containers, images, networks, volumes) | DEVOPS, ENG | Socket |
| 6 | kubectl | `kubectl-mcp-server` | 253 tools (pods, deployments, Helm, GitOps) | DEVOPS, ARCH | kubeconfig |
| 7 | K8s Secure | `alexei-led/k8s-mcp-server` | kubectl/helm/istio/argocd in sandbox | DEVOPS, ARCH | kubeconfig |
| 8 | Terraform | `hashicorp/terraform-mcp-server` | provider docs, module search, validate | DEVOPS, ARCH | None |

### Databases

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 9 | PostgreSQL | `@modelcontextprotocol/server-postgres` | query, schema, tables (read-only) | ENG, QA, ARCH | connstr |
| 10 | SQLite | `mcp-server-sqlite` (pip) | read/write query, tables, insights | ENG, QA, PM | file path |
| 11 | Redis | `redis/mcp-redis` | get/set/search/hash ops | ENG, DEVOPS | Redis URL |
| 12 | DBHub | `bytebase/dbhub` | unified PG/MySQL/MSSQL/SQLite | ENG, QA | connstrs |

### Browser & Web

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 13 | Playwright | `@playwright/mcp` | navigate, click, type, snapshot (headless) | QA, ENG, UX | None |
| 14 | Puppeteer | `@modelcontextprotocol/server-puppeteer` | navigate, screenshot, click, eval | QA, ENG, UX | None |
| 15 | Brave Search | `@modelcontextprotocol/server-brave-search` | web search, local search | ENG, WRITER, ARCH | API key |
| 16 | Fetch | `mcp-server-fetch` (pip) | fetch URL → markdown | ALL | None |
| 17 | Tavily | `tavily-mcp` | search, extract, crawl, map | ENG, WRITER, ARCH | API key |

### Code Quality & Security

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 18 | ESLint | `@eslint/mcp` | lint, rule docs, fix | ENG, QA | None |
| 19 | Semgrep | `semgrep` (pip, MCP mode) | scan 30+ languages, custom rules | DEVSEC, QA | Optional |
| 20 | Snyk | `snyk` CLI (built-in MCP) | 11 tools: SAST, SCA, IaC, container, SBOM | DEVSEC, DEVOPS | Token |
| 21 | Trivy | `trivy` + MCP plugin | container/filesystem/repo/config scan | DEVSEC, DEVOPS | None |
| 22 | DevSecOps-MCP | `devsecops-mcp` (pip) | aggregates Semgrep+Bandit+ZAP+Trivy | DEVSEC | Varies |

### Testing

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 23 | Test Runner | `@iflow-mcp/mcp-test-runner` | unified pytest/jest/bats/go/rust | QA, ENG | None |
| 24 | Pytest MCP | `pytest-mcp-server` (pip) | failures, analysis, coverage, debug trace | QA, ENG | None |

### Documentation & Knowledge

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 25 | Context7 | `@upstash/context7-mcp` | library/framework docs (47K stars) | ENG, ARCH, WRITER | Optional |

### Project Management

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 26 | Notion | Remote MCP | search, pages, databases | PM, WRITER | OAuth |
| 27 | Confluence | `@aashari/mcp-server-atlassian-confluence` | spaces, pages, search | WRITER, PM | Token |
| 28 | GitHub Actions | `github-actions-mcp-server` | workflows, runs, logs, artifacts | DEVOPS, QA | PAT |
| 29 | Linear | Remote MCP | issues, projects, comments | PM, ENG | OAuth |
| 30 | Jira | `@aashari/mcp-server-atlassian-jira` | projects, issues, JQL, dev info | PM, ENG | Token |
| 31 | Plane | `makeplane/plane-mcp-server` | issues, cycles, modules | PM, ENG, FLEET | API key |

### Communication

| # | Server | Package | Tools | Roles | Auth |
|---|--------|---------|-------|-------|------|
| 32 | Slack | (official plugin) | messaging | ALL | OAuth |

---

## Part 3: Plugin Ecosystem (40+ significant plugins)

### Tier 1 — Mega-Popular (10K+ stars)

| Plugin | Stars | What It Does | Roles |
|--------|-------|-------------|-------|
| **Superpowers** (`obra/superpowers`) | 132K | TDD methodology, 20+ skills for planning/debugging/review/collab | ALL dev |
| **claude-mem** (`thedotmack/claude-mem`) | 45K | Cross-session memory, SQLite+ChromaDB, 4 MCP search tools | ALL |
| **Agents** (`wshobson/agents`) | 33K | Multi-agent orchestration | FLEET-OPS |
| **Ruflo** (`ruvnet/ruflo`) | 29K | Swarm orchestration, RAG, Codex integration | FLEET-OPS |
| **codex-plugin-cc** (`openai/codex-plugin-cc`) | 11K | Cross-provider review, task delegation to Codex | REVIEW |

### Tier 2 — Very Popular (1K-10K stars)

| Plugin | Stars | What It Does | Roles |
|--------|-------|-------------|-------|
| **claude-skills** (`alirezarezvani`) | 9K | 220+ skills for 10+ coding agents | ALL |
| **plannotator** (`backnotprop`) | 4K | Visual plan/diff annotation, team feedback | PM, REVIEW |
| **hooks-mastery** (`disler`) | 3K | Production hook patterns | DEVOPS |
| **ars contexta** (`agenticnotetaking`) | 3K | Knowledge systems from conversation | WRITER |
| **claude-octopus** (`nyldn`) | 2K | Multi-model review (up to 8 AIs) | QA, REVIEW |
| **plugins-plus-skills** (`jeremylongshore`) | 2K | 340 plugins + 1,367 skills, CCPI manager | ALL |
| **pg-aiguide** (`timescale`) | 2K | PostgreSQL optimization | ENG, DATA |
| **harness** (`revfactory`) | 2K | Meta-skill: designs agent teams | ARCH, FLEET |
| **pro-workflow** (`rohitg00`) | 2K | Self-correcting 50+ session memory, parallel worktrees | SENIOR DEV |
| **safety-net** (`kenryu42`) | 1K | Hook catches destructive git/fs commands | ALL (safety) |
| **memsearch** (`zilliztech`) | 1K | Markdown-first memory for any agent | FLEET |

### Tier 3 — Notable (100-1K stars)

| Plugin | Stars | What It Does | Roles |
|--------|-------|-------------|-------|
| **adversarial-spec** (`zscole`) | 518 | Multi-LLM debate for spec refinement | ARCH, PM |
| **total-recall** (`davegoldblatt`) | 189 | Tiered memory with write gates | ALL |
| **sage** (`gendigitalinc`) | 162 | Agent Detection and Response (ADR) | DEVSEC |
| **plan-cascade** (`Taoidle`) | 149 | Cascading parallel task decomposition | PM, ARCH |
| **code-container** (`kevinMEH`) | 202 | Run agents safely in containers | DEVSEC, DEVOPS |
| **smart-ralph** (`tzachbon`) | 271 | Spec-driven autonomous loop with smart compaction | AUTO DEV |
| **orchestrator-supaconductor** (`Ibrahim-3d`) | 303 | Multi-agent + quality gates + Board of Directors | FLEET-OPS |

### Development Workflow Plugins (Official Anthropic)

| Plugin | What It Does | Key Commands |
|--------|-------------|-------------|
| **commit-commands** | Git commit workflows | `/commit-commands:commit` |
| **pr-review-toolkit** | PR review with 5 parallel Sonnet agents | `/pr-review-toolkit:review-pr` |
| **feature-dev** | Guided feature development | `code-explorer`, `code-architect`, `code-reviewer` agents |
| **hookify** | Natural-language hook creation | `/hookify` |
| **security-guidance** | Security pattern monitoring (9 patterns) | Hook-based |
| **plugin-dev** | Plugin creation toolkit (8-phase) | `/plugin-dev:create-plugin` |

---

## Part 4: Per-Role Classification

### Every role mapped to their tools, skills, plugins, commands, MCP servers

#### Project Manager

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet (29 tools), github, Plane, Linear/Jira (if used) |
| **Plugins** | claude-mem, plannotator, plan-cascade |
| **Skills** | pm-plan, pm-status-report, pm-retrospective, pm-changelog, fleet-plan, fleet-sprint, fleet-plane |
| **Commands** | /plan (sprint planning), /compact (between sprints), /context (before heavy planning) |
| **Key Tools** | fleet_task_create, fleet_gate_request, fleet_plane_*, fleet_chat, fleet_escalate |

#### Fleet-Ops / Board Lead

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, github |
| **Plugins** | claude-mem, safety-net, pr-review-toolkit, claude-octopus (multi-model review) |
| **Skills** | pm-assess, quality-audit, fleet-review |
| **Commands** | /plan (review planning), /compact (between review sessions) |
| **Key Tools** | fleet_approve, fleet_alert, fleet_agent_status, fleet_chat |
| **Codex** | codex:adversarial-review (cross-provider quality gate) |

#### Architect

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, github, Context7 |
| **Plugins** | claude-mem, context7, superpowers, adversarial-spec, feature-dev, harness |
| **Skills** | architecture-propose, architecture-review, scaffold |
| **Commands** | /plan (design work), /context (before heavy reads), /debug (architecture investigation) |
| **Key Tools** | fleet_contribute (design_input), fleet_artifact_create, fleet_task_accept |

#### DevSecOps (Cyberpunk-Zero)

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, docker, Snyk, Semgrep, Trivy, DevSecOps-MCP |
| **Plugins** | claude-mem, security-guidance, sage (ADR), code-container |
| **Skills** | infra-security, quality-audit, fleet-security-audit |
| **Commands** | /security-review (branch analysis), /plan (security assessment), /debug (vuln investigation) |
| **Key Tools** | fleet_contribute (security_requirement), fleet_alert, fleet_approve (security review) |
| **Codex** | codex:adversarial-review (security-focused) |

#### Software Engineer

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, github, playwright, Context7, ESLint, pytest-mcp |
| **Plugins** | claude-mem, context7, superpowers, pyright-lsp |
| **Skills** | feature-implement, refactor-extract, fleet-test |
| **Commands** | /plan (before complex impl), /debug (when stuck), /compact (near context limit), /diff (review changes), /batch (parallel worktree changes) |
| **Key Tools** | fleet_task_accept, fleet_commit, fleet_task_complete, fleet_request_input |

#### DevOps Engineer

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, github, docker, kubectl, Terraform, GitHub Actions |
| **Plugins** | claude-mem, hookify, commit-commands |
| **Skills** | foundation-docker, foundation-ci, ops-deploy, ops-maintenance |
| **Commands** | /plan (infra design), /debug (deployment issues), /loop (monitoring) |
| **Key Tools** | fleet_commit, fleet_task_complete, fleet_contribute (application_requirements) |

#### QA Engineer

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, playwright, pytest-mcp, test-runner, ESLint |
| **Plugins** | claude-mem, claude-octopus (multi-model validation) |
| **Skills** | quality-coverage, quality-audit, foundation-testing, fleet-test |
| **Commands** | /debug (test failures), /plan (test strategy) |
| **Key Tools** | fleet_contribute (qa_test_definition), fleet_artifact_create, fleet_commit |

#### Technical Writer

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, github, Context7, Confluence/Notion |
| **Plugins** | claude-mem, context7, ars-contexta |
| **Skills** | feature-document, pm-changelog, pm-handoff |
| **Commands** | /plan (doc structure), /compact (between doc sections) |
| **Key Tools** | fleet_artifact_create (documentation_outline), fleet_commit, fleet_plane_* |

#### UX Designer

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem, playwright |
| **Plugins** | claude-mem |
| **Skills** | quality-accessibility |
| **Commands** | /plan (UX design), /context (before large UI analysis) |
| **Key Tools** | fleet_contribute (ux_spec), fleet_artifact_create |

#### Accountability Generator

| Category | Items |
|----------|-------|
| **MCP Servers** | fleet, filesystem |
| **Plugins** | claude-mem |
| **Skills** | quality-audit |
| **Commands** | /compact (between audit cycles) |
| **Key Tools** | fleet_artifact_create (compliance_report), fleet_chat, fleet_alert |

---

## Part 5: Key Findings

### What Changes from This Research

1. **MCP servers are far richer than we configured.** We have 5 types in agent-tooling.yaml. There are 32+ relevant servers. DevSecOps especially needs Snyk/Semgrep/Trivy.

2. **Plugins are more than claude-mem + context7.** Superpowers (132K stars) provides TDD methodology. safety-net catches destructive commands. pr-review-toolkit gives 5-agent parallel review. These should be evaluated.

3. **Commands are a full toolkit not documented in any agent file.** /batch, /loop, /debug, /diff, /security-review, /simplify — none referenced in agent CLAUDE.md or TOOLS.md.

4. **26 hook types available** — we use 0 custom hooks. The review gate pattern, security monitoring hooks, pre-compact state saving, file change watching — all available.

5. **Skills system is more powerful than we use.** Dynamic context via shell commands, per-path targeting, effort/model overrides, agent spawning from skills.

6. **Agent Teams is production-ready.** 3-5 teammates, shared task list, mailbox messaging. Could complement (not replace) our orchestrator for within-task parallelism.

7. **Plane has an official MCP server.** We're using direct API calls but could switch to `makeplane/plane-mcp-server` for standard MCP integration.

### What This Means for Agent Files

Every agent CLAUDE.md and TOOLS.md must reference:
- Their specific MCP servers (not just "fleet + filesystem")
- Their available skills (with per-stage recommendations)
- Their plugins and what they provide
- The built-in commands relevant to their work
- The hooks that protect their work (safety-net at minimum)
- Their tool chains from fleet-elevation/24

This is why the autocomplete chain can't be built yet — the inputs aren't classified and documented.

---

## Open Questions for PO

1. **Superpowers (132K stars):** Install for all dev agents? It provides TDD methodology that aligns with our quality standards.
2. **safety-net:** Install for ALL agents? Catches destructive commands before execution.
3. **Security MCP servers:** Which for devsecops? Snyk (most comprehensive, needs token) vs Trivy (open source) vs Semgrep (free)?
4. **pr-review-toolkit:** Use for fleet-ops reviews? 5 parallel Sonnet agents per review.
5. **Plane MCP server:** Switch from direct API to official MCP server?
6. **Agent Teams:** Pilot for architect+engineer collaboration on complex tasks?
7. **pyright-lsp:** Install for all Python agents? Automatic type error detection.
8. **How many plugins per agent?** Expert recommendation is 2-3 max. Which ones are highest value per role?
9. **Hooks:** Implement any custom hooks? safety-net pattern, review gate pattern, pre-compact state save?
10. **Skills from ecosystem:** Evaluate claude-skills (220+) and plugins-plus-skills (1,367) for per-role adoption?

---

## Next Steps

1. PO reviews and answers open questions
2. Update config/agent-tooling.yaml with full per-role tooling
3. Research group 03: classify our 85 existing skills per role + evaluate ecosystem skills
4. Write agent files (CLAUDE.md, TOOLS.md) that reference REAL capabilities
5. Update complete-roadmap.md with all new milestones from this research
