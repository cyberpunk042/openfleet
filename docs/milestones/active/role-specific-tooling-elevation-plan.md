 Role-Specific Tooling Elevation — Top-Tier Experts With Their Own Tools

**Date:** 2026-04-07
**Status:** Investigation + Reasoning — full analysis before implementation
**Scope:** Every agent's complete capability surface — MCP servers, plugins, skills, CRONs, sub-agents, hooks, standing orders, stage-aware recommendations
**Depends on:** fleet-elevation/02 (architecture), fleet-elevation/05-14 (per-role specs), fleet-elevation/23 (lifecycle + strategic calls), fleet-elevation/24 (tool call trees), systems/21 (agent tooling), systems/08 (MCP tools), ecosystem-deployment-plan.md, skills-ecosystem.md, phase-f1-foundation-skills.md, context-system/01-08, methodology-system/01-06
**Companion to:** tool-chain-elevation-plan.md (fleet group calls — Document 1)
**Part of:** Path-to-live Phase B (Agent Identity) + Phase C (Brain Evolution) + Phase E (Cross-Agent Synergy)

---

## PO Requirements (Verbatim)

> "every role are top tier expert of their profession"

> "the engineer has to be to my image... a senior devops software
> engineer with network background and PM, Scrum Master replacement
> capabilities... evolved to architect and fullstack and security...
> a very humble no matter how knowledgable and always in respect of
> other people roles"

> "The words and titles I used are not for nothing. there is a huge
> difference between any general agent..... those are top tier wise
> agent. they dont need overconfidence, no self-confirmed bias, no
> cheating, no getting lost or derailing"

> "we need to do the right directive so the AI know if it need to use
> this bus or this bus and know that it will do this chain naturally and
> do this and that and so on."

> "we dont do claude call just for fun... we do them strategically
> with the right configurations appropriate to the case, this include
> everything including the effort setting and if we need to compact
> to start a plan or something else and whatnot"

> "all I said about making it smart and tooling for the agent and making
> it easy... you have to make things fluid and clear and tag things and
> make sure that the flow everywhere at all level is top notch"

> "its important to respect pattern and to know when to evolve and
> refactor, and when to change and when to remove and when to upgrade
> and when to update"

> "at some point its force compact lol...the agent can only prepare
> or declare with a till that its ready but we have to be sure that
> it doesn't do it prematuraly either"

> "if you are over 40 to 80 000 tokens or that you do not need to
> persist your session context (useless predicted cost for the sole
> purpose of being ready for a next job later...), dump (as smart
> artifacts) it for a synthesised re-injection later if needed"

> "we need to revise everything about all agents, not just one of their
> files, the whole things and the templating and the injection and the
> structure and pattern explanation before autocomplete and so on..."

---

## What This Document Is

Document 1 (tool-chain-elevation-plan.md) covers the **shared fleet MCP tools** — the group calls with trees, cross-platform propagation, and event chains that ALL agents share.

This document covers everything ELSE that makes each agent a top-tier expert with their own specialized toolkit. A top-tier architect doesn't just call fleet_contribute — they use filesystem MCP to explore the codebase, context7 to check library docs, adversarial-spec to debate design options, a code-explorer sub-agent for parallel research, an architecture-propose skill for structured output, and a weekly CRON for architecture health checks. All adapted per methodology stage, per model/effort strategy, per budget constraints.

This is NOT a prescriptive specification. Many of the specific skills, CRONs, sub-agents, and hooks do not exist yet and need to be designed, researched, evaluated, and built. This document maps the LAYERS of capability, the CURRENT STATE of each layer, the KNOWN GAPS, and the ARCHITECTURE for how it all connects. Specific implementations are scaffolds and examples — the actual content requires per-role design sessions.

---

## The 7 Capability Layers

Each top-tier expert agent has 7 layers of capability. Each layer serves a distinct purpose. Together they form the complete capability surface.

### Layer 1: Fleet MCP Tools (Shared Group Calls)

**What:** The 25+ fleet tools all agents share. Each is a group call — one agent-facing tool triggers a tree of operations across 6 surfaces.

**Purpose:** Standard fleet operations — read context, accept tasks, commit, complete, chat, alert, escalate, create tasks, approve, contribute, transfer, request input, request gates, create/update artifacts.

**Covered by:** Document 1 (tool-chain-elevation-plan.md). Per-role filtering via config/tool-roles.yaml.

**Current state:** Tools exist. Trees partially wired (1 of 8 builders through ChainRunner). Role filtering not applied in TOOLS.md generation. Chain descriptions in tool-chains.yaml describe elevated trees, not current reality.

### Layer 2: Role-Specific MCP Servers

**What:** External tool servers that give agents direct access to platforms and services. Each MCP server provides a set of tools the agent can call.

**Purpose:** Raw capabilities specific to the role's domain — file access, GitHub operations, browser automation, container management, security scanning, project management.

**Current state in config/agent-tooling.yaml:**

| Agent | MCP Servers | Purpose |
|-------|------------|---------|
| Architect | filesystem, github | Explore codebase, check PRs/branches |
| Software Engineer | filesystem, github, playwright, pytest-mcp | Read/write code, browser test, run tests |
| QA Engineer | filesystem, playwright, pytest-mcp | Read test files, browser test, run tests |
| DevOps | filesystem, github, docker, github-actions | IaC files, CI/CD, container management |
| DevSecOps | filesystem, docker, semgrep | Scan code, inspect containers, security analysis |
| Fleet-Ops | github | PR review, CI status |
| PM | github, plane MCP | Monitor PRs, Plane sprint management |
| Technical Writer | filesystem, github | Read/write docs, check existing docs |
| UX Designer | filesystem, playwright | Read UI code, visual testing |
| Accountability | filesystem | Read evidence files |

**Current state of deployment:**
- setup-agent-tools.sh generates per-agent mcp.json from config — WORKS
- Per-agent mcp.json stored at agents/{name}/mcp.json — EXISTS
- push-soul.sh deploys TEMPLATE mcp.json to workspaces (NOT per-agent) — **GAP**: per-agent MCP servers not reaching workspaces
- Semgrep MCP requires semgrep binary installed — not verified
- Plane MCP (`makeplane/plane-mcp-server`) — not verified if compatible with self-hosted Plane

**Known gaps:**
- Workspace deployment doesn't use per-agent mcp.json
- Some MCP server packages may need evaluation for compatibility
- LightRAG MCP server listed in defaults but not deployed (LocalAI dependency)
- No per-agent MCP server health verification

### Layer 3: Plugins

**What:** Bundled packages that provide skills + hooks + sub-agents + MCP tools as a unit. Installed via `claude plugin install` or gateway marketplace.

**Purpose:** High-level capabilities that combine multiple features. A plugin like superpowers provides 14 skills + 1 sub-agent + 1 SessionStart hook. A plugin like pr-review-toolkit provides 6 parallel review sub-agents.

**Current state in config/agent-tooling.yaml:**

| Agent | Plugins | What They Provide |
|-------|---------|-------------------|
| ALL (defaults) | claude-mem | Cross-session semantic memory |
| ALL (defaults) | safety-net | PreToolUse hook catches destructive commands |
| Architect | context7, superpowers, adversarial-spec | Library docs, TDD/debugging/planning skills, multi-LLM spec debate |
| Software Engineer | context7, superpowers, pyright-lsp | Library docs, TDD/debugging/planning skills, Python type checking |
| QA Engineer | superpowers | TDD/debugging skills |
| DevOps | hookify, commit-commands | Natural-language hook creation, git commit workflows |
| DevSecOps | security-guidance, sage | 9 security PreToolUse hooks, Agent Detection and Response |
| Fleet-Ops | pr-review-toolkit | 6 parallel review sub-agents (code-reviewer, silent-failure-hunter, type-design-analyzer, comment-analyzer, code-simplifier, pr-test-analyzer) |
| PM | plannotator | Visual plan/diff annotation with team feedback |
| Technical Writer | context7, ars-contexta | Library docs, knowledge systems from conversation |
| UX Designer | (none beyond defaults) | |
| Accountability | (none beyond defaults) | |

**Current state of deployment:**
- install-plugins.sh exists and reads from config — WORKS in principle
- Marketplace registration for 6 plugin sources — may need updating
- Plugin installation requires `claude` CLI available in agent workspaces
- Whether plugins are actually installed on any agent workspace — UNVERIFIED
- Whether all marketplace sources still exist at listed URLs — UNVERIFIED

**What superpowers provides (the most impactful plugin, 139K stars):**
- 14 skills: using-superpowers, test-driven-development, systematic-debugging, verification-before-completion, brainstorming, writing-plans, executing-plans, dispatching-parallel-agents, subagent-driven-development, requesting-code-review, receiving-code-review, using-git-worktrees, finishing-a-development-branch, writing-skills
- 1 sub-agent: code-reviewer (senior code reviewer that checks plan alignment, code quality, architecture, documentation)
- 1 hook: SessionStart → injects superpowers skill instructions into every session
- Cross-platform: works in Claude Code, Cursor, Copilot CLI, Codex, Gemini CLI

**What pr-review-toolkit provides (official Anthropic, for fleet-ops):**
- 6 parallel sub-agents: code-reviewer (opus), code-simplifier, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer
- Each reviews the same PR from a different specialized perspective
- Results aggregated with structured output, severity prioritization, file/line references

**What security-guidance provides (official Anthropic, for devsecops):**
- 9 PreToolUse hook patterns that fire on every Edit/Write tool call
- Checks for: GitHub Actions command injection, child_process.exec, new Function, eval, dangerouslySetInnerHTML, document.write, innerHTML, pickle deserialization, os.system injection
- Session-scoped warnings (shown once per rule per session)

**Known gaps:**
- UX Designer and Accountability Generator have no role-specific plugins
- sage plugin source repository not publicly accessible — needs evaluation
- ars-contexta limited public information — needs evaluation
- No evaluation of which Anthropic official plugins (32 available) would benefit which agents beyond current assignments
- feature-dev plugin (3 sub-agents: code-explorer, code-architect, code-reviewer) not assigned to any agent — could benefit architect and engineer

### Layer 4: Skills

**What:** Prompt instructions in SKILL.md format that teach agents HOW and WHEN to use tools. Skills are knowledge, not callable functions. They teach workflows, patterns, and approaches.

**Purpose:** Make agents work like top-tier experts by giving them structured workflows for every type of work they do. A skill doesn't add a new tool — it teaches the agent how to use existing tools effectively for a specific purpose.

**The scope the PO described:**
- 10-40 generic methodology skills (applicable across roles)
- 40+ per role per methodology stage and case/situation
- Task-specific skills (security audit, architecture review, test predefinition, etc.)
- Project management skills (sprint planning, retrospective, changelog, etc.)
- Fleet operation skills (review protocol, communication guide, etc.)
- Packs aggregated per role with directed usage per stage

**5 skill sources exist:**

| Source | Location | Scope | Current Count |
|--------|----------|-------|---------------|
| OpenClaw/OpenArms bundled | vendor/openclaw/skills/ | All agents (global) | 51 (10 fleet-relevant) |
| Plugin-bundled | Inside enabled plugins | Per-plugin | Varies (superpowers: 14, pr-review-toolkit: 0 skills / 6 agents) |
| Fleet workspace skills | .claude/skills/ | All agents (project-level) | 7 (fleet-communicate, fleet-plan, fleet-plane, fleet-review, fleet-security-audit, fleet-sprint, fleet-test) |
| Gateway skills | .agents/skills/ | All agents (gateway-level) | 13 (fleet-alert, fleet-comment, fleet-commit, fleet-gap, fleet-irc, fleet-memory, fleet-pause, fleet-pr, fleet-report, fleet-task-create, fleet-task-update, fleet-urls, plane-render) |
| OCMC marketplace | MC database → gateway → workspace | Org-wide catalog | 1 pack registered (Anthropic Official, 17 skills) |

**What's declared in config/agent-tooling.yaml but DOES NOT EXIST as SKILL.md files:**

~50+ skills are listed per role. These are the PO's initial LocalAI project skill list — a starting point, not the final scope. Examples:

- architecture-propose, architecture-review, scaffold (architect)
- feature-implement, feature-plan, feature-test, refactor-extract, refactor-split, foundation-deps, quality-lint (engineer)
- quality-coverage, quality-audit, quality-debt, foundation-testing, feature-review, fleet-test (QA)
- foundation-docker, foundation-ci, foundation-config, ops-deploy, ops-rollback, ops-incident, ops-backup, ops-maintenance, config-deploy, infra-monitoring (devops)
- infra-security, quality-audit, config-secrets, foundation-auth, fleet-security-audit (devsecops)
- pm-plan, pm-assess, pm-status-report, pm-retrospective, pm-changelog, pm-handoff, idea-capture, fleet-plan, fleet-sprint, fleet-plane (PM)
- feature-document, pm-changelog, pm-handoff, quality-debt (writer)
- quality-accessibility (UX)
- quality-audit, quality-debt, quality-coverage, pm-status-report (accountability)
- openclaw-health, openclaw-fleet-status, openclaw-setup, openclaw-add-agent, scaffold-subagent (fleet-ops)

**NONE of these exist.** They need to be designed, built, and validated. Some may come from the Anthropic official pack or other marketplace packs. Some need to be fleet-custom. Some may already exist in the 5400+ OpenClaw skill registry or the broader ecosystem and need evaluation.

**Existing skill design docs:**
- phase-f1-foundation-skills.md — designs for fleet-urls (M81), markdown template library (M82), PR composer (M83), task comment formatter (M84), board memory composer (M85), IRC message formatter (M86)
- skills-ecosystem.md — milestones M48-M52 for inventory, registration, installation, fleet-specific skills, per-agent association

**Stage-aware skill recommendation pattern:**

Skills map to methodology stages. At each stage, certain skills are appropriate and others are not. This is the "directed usage per stage" the PO described.

| Stage | Generic Skills | Role-Specific Examples |
|-------|---------------|----------------------|
| conversation | brainstorming (superpowers), idea-capture | PM: pm-assess. Architect: architecture-review (understanding existing). |
| analysis | (skills for examining codebases, documenting findings) | Engineer: code-explorer sub-agent. DevSecOps: security scan skills. QA: quality-audit. |
| investigation | adversarial-spec (multi-LLM debate), context7 (library docs), web research | Architect: architecture-propose (exploring options). PM: pm-plan (evaluating approaches). |
| reasoning | writing-plans (superpowers), verification-before-completion | Architect: scaffold (structuring implementation). Engineer: feature-plan. PM: fleet-sprint. |
| work | test-driven-development (superpowers), executing-plans (superpowers), verification-before-completion | Engineer: feature-implement, quality-lint. QA: feature-test. DevOps: ops-deploy, foundation-docker. |

This mapping is NOT hardcoded — it's injected through the methodology protocol text (config/methodology.yaml) and the TOOLS.md/context. The autocomplete chain naturally leads agents to the right skills because the stage instructions reference them.

**The skill creation pipeline:**
1. Identify need (from role specs, methodology protocols, or PO direction)
2. Check if skill exists in ecosystem (bundled, marketplace, community)
3. If exists → evaluate, install, configure per role
4. If not → design SKILL.md, build, validate
5. Assign to roles in config/agent-tooling.yaml
6. Install via marketplace or workspace deployment
7. Verify: agent can invoke, skill produces correct output
8. Document in TOOLS.md (generation script picks up from config)

### Layer 5: CRONs (Scheduled Operations)

**What:** Gateway-native scheduled jobs that fire at configured times with specific agent, model, effort, context strategy. Persisted, retryable, budget-aware.

**Purpose:** Top-tier experts don't just react to tasks — they have scheduled responsibilities. A DevSecOps expert runs nightly security scans. A PM runs daily standup summaries. Fleet-ops sweeps the review queue. QA generates weekly coverage reports. Architecture does health checks.

**Current state:** The gateway has full CRON support built in (vendor/openclaw/src/cron/). Persisted at ~/.openclaw/cron/jobs.json. Supports:
- Schedule types: at (one-shot), every (interval), cron (5-field expressions + timezone)
- Execution styles: main session, isolated, custom session
- Model/thinking overrides per job
- Retry with exponential backoff
- Delivery: announce to channel, webhook, silent
- Tool restrictions per job
- Light context mode (skip workspace bootstrap, reduce cost)
- Failure notifications

**Zero CRONs are configured for fleet agents.** The capability exists but hasn't been wired.

**Scaffold examples (these are NOT specifications — they need proper design):**

```yaml
# config/agent-crons.yaml (TO BE CREATED)
# This is a SCAFFOLD showing the pattern, not final configuration.
# Each CRON needs proper design: what exactly to scan, what model,
# what effort, what context strategy, what standing orders to reference.

devsecops-expert:
  - name: nightly-security-scan
    schedule: "0 1 * * *"
    timezone: America/New_York
    session: isolated
    model: opus
    thinking: high
    message: "Execute nightly security scan per standing orders."
    budget_gate: true  # skip if fleet over budget threshold

project-manager:
  - name: daily-standup
    schedule: "0 9 * * 1-5"
    timezone: America/New_York
    session: isolated
    model: sonnet
    message: "Generate daily standup summary per standing orders."
    budget_gate: true

fleet-ops:
  - name: review-queue-sweep
    schedule: "0 */2 * * *"
    session: isolated
    model: sonnet
    message: "Process pending review queue per standing orders."
    budget_gate: true

# Additional candidates (need design):
# qa-engineer: weekly test coverage report
# architect: weekly architecture health check
# technical-writer: weekly stale documentation scan (when Plane connected)
# accountability-generator: sprint boundary compliance report
```

**What needs to be built:**
- config/agent-crons.yaml — YAML config driving CRON creation
- scripts/sync-agent-crons.sh — reads config, creates/updates/removes CRONs via gateway CLI
- Fleet state integration — CRONs pause when fleet paused, skip when over budget
- Standing orders per agent — CRONs reference standing orders for their instructions (the CRON message says "per standing orders", the standing order in AGENTS.md defines the full scope and procedure)
- Heartbeat CRON coordination — CRONs and heartbeats must not conflict (the gateway handles this natively via isolated sessions)

### Layer 6: Sub-Agents

**What:** Specialized Claude instances that run in separate context windows for isolated/parallel work. Defined in .claude/agents/{name}.md with model, tools, isolation, skills, permissions.

**Purpose:** A top-tier expert delegates specialized subtasks. An architect spawns a code-explorer to examine a codebase area while continuing design work. A QA engineer spawns a test-runner for parallel test execution. A PM spawns a sprint-analyzer for data aggregation.

**Current state:**
- The gateway supports sub-agent definitions via .claude/agents/{name}.md — BUILT
- Plugins provide sub-agents: superpowers (code-reviewer), pr-review-toolkit (6 review agents) — AVAILABLE
- Zero fleet-custom sub-agent definitions exist
- Agent Teams experimental feature available via CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

**Sub-agents vs Agent Teams:**

| Dimension | Sub-Agents | Agent Teams |
|-----------|-----------|-------------|
| Execution | Sequential in single session | Parallel across multiple sessions |
| Context | Own window, results return to main | Fully independent windows |
| Communication | Report back to main agent only | Direct peer-to-peer messaging + shared task list |
| Cost | Lower (results summarized) | Higher (each teammate = full instance) |
| Use case | Focused delegation, isolated research | Complex parallel work needing coordination |

**Scaffold examples (these need proper design per role):**

Sub-agent definitions would be placed in agents/{name}/.claude/agents/ and deployed to workspaces. Each needs careful design of:
- What model (cost-appropriate for the subtask)
- What tools (restricted to what's needed — principle of least privilege)
- What isolation mode (worktree for code work, none for analysis)
- What skills to preload
- What the description says (drives when the main agent auto-delegates)

Examples of sub-agent TYPES that could exist (not prescriptive):
- **code-explorer**: read-only codebase navigation (filesystem + grep, sonnet, no write)
- **test-runner**: execute and report test results (filesystem + pytest-mcp, sonnet)
- **parallel-researcher**: web research in isolated context (web search + web fetch, sonnet, worktree)
- **security-scanner**: scan files for vulnerabilities (filesystem + semgrep, sonnet, no write)
- **documentation-checker**: verify docs match code (filesystem + grep, haiku)

The actual sub-agent definitions for each role need dedicated design work — understanding what each role actually needs to delegate, when, and with what constraints.

### Layer 7: Hooks + Standing Orders + Extended Thinking

**What:** Three related mechanisms that shape HOW agents work beyond what they CAN do.

**Hooks:** Lifecycle event handlers — fire before/after tool calls, on session events, on file changes. Can block, allow, warn, or modify operations.

**Standing Orders:** Persistent autonomous authority programs defined in agent files. Scope, triggers, approval gates, escalation rules. The gateway reads them from bootstrap files and they persist across sessions.

**Extended Thinking:** Adaptive reasoning depth controlled by effort level. Higher effort = more thinking tokens = better output = more cost.

**Current state:**

Hooks:
- Template settings.json allows Bash, Read, Write, Edit, Glob, Grep, fleet MCP tools
- safety-net plugin provides PreToolUse destructive command detection (configured for all agents in agent-tooling.yaml)
- security-guidance plugin provides 9 security pattern PreToolUse hooks (configured for devsecops)
- hookify plugin enables natural-language hook creation (configured for devops)
- No per-role custom hooks beyond plugin-provided ones
- No hook-based monitoring/streaming configured

Extended Thinking:
- configure-agent-settings.sh sets per-role effort levels:
  - architect: high, devsecops-expert: high, project-manager: high, accountability-generator: high
  - software-engineer: medium, qa-engineer: medium, devops: medium, fleet-ops: medium, ux-designer: medium
  - technical-writer: low
- NOT stage-aware (same effort regardless of methodology stage)
- NOT task-aware (same effort regardless of task complexity)
- The brain's model_selection.py and backend_router.py make per-dispatch decisions — but these don't flow through to heartbeat effort levels
- Gateway supports per-heartbeat model/thinking override and per-CRON model/thinking override

Standing Orders:
- Not explicitly defined in any agent file
- The concept maps to HEARTBEAT.md priority protocol + CLAUDE.md rules — but standing orders are a more structured formalism with scope/triggers/gates/escalation
- Gateway documentation describes standing orders as programs in AGENTS.md — but fleet AGENTS.md currently only contains synergy relationships

**What needs to be designed:**

Hooks — per-role hook configurations:
- What PreToolUse hooks make sense per role? (security checks for all? linting for engineers? format validation for writers?)
- What PostToolUse hooks could improve quality? (commit message validation, PR body validation)
- How to implement PO's idea of connecting to see agent's current feed? (HTTP hooks posting to monitoring endpoint on every tool call — async, non-blocking)
- How to integrate with fleet trail system? (hook fires on every operation → trail event recorded externally)

Extended Thinking — stage-aware effort:
- Conversation stage → high effort (understanding requirements needs deep reasoning)
- Analysis stage → high effort (examining codebases needs thoroughness)
- Investigation stage → high effort (exploring options needs breadth)
- Reasoning stage → high effort (planning needs precision)
- Work stage → medium effort (executing a confirmed plan is more mechanical)
- Heartbeat with no work → low effort (status check doesn't need deep reasoning)
- CRON scheduled tasks → varies by CRON type (security scan: high, status summary: low)

This is currently NOT configurable in a unified way. The brain decides model/effort at dispatch. Heartbeats use static effort from settings.json. CRONs can override per job. A unified stage-aware effort system would connect these.

Standing Orders — need to be designed per role:
- What autonomous authority does each agent have?
- What are the triggers for autonomous action?
- What requires PO approval before acting?
- What is the escalation protocol when uncertain?
- How do standing orders interact with CRONs? (CRON fires → standing order defines what to do)

---

## How The Layers Connect

### The Autocomplete Chain

The TOOLS.md at injection position 4 is where the agent learns its complete capability surface. After reading IDENTITY (who I am), SOUL (my values), CLAUDE (my rules), the agent reads TOOLS.md and knows:
- What fleet group calls are available and what trees they fire
- What MCP servers give them raw capabilities
- What plugins provide skills, hooks, and sub-agents
- What skills are available for what stages and situations
- What CRONs handle scheduled responsibilities
- What sub-agents can be delegated to
- What hooks enforce quality

Then at position 6, the dynamic context tells the agent their current task, methodology stage, and what's happening in the fleet. The agent already knows their capabilities (from TOOLS.md) and naturally applies the right ones to the current situation. This is the autocomplete chain — the correct action is the natural continuation.

### The Generation Pipeline

```
CONFIG SOURCES:
  config/agent-tooling.yaml    → MCP servers, plugins, skills per role
  config/tool-chains.yaml      → fleet tool chain descriptions
  config/tool-roles.yaml       → fleet tools per role with usage/when
  config/agent-crons.yaml      → scheduled operations per role (TO CREATE)
  config/methodology.yaml      → stage-aware tool/skill recommendations
  fleet/mcp/tools.py           → fleet tool names (source of truth)
  .claude/agents/              → sub-agent definitions per role
  .claude/skills/              → available skills
  .agents/skills/              → gateway skills

GENERATION:
  scripts/generate-tools-md.sh → reads all config sources
                               → produces per-role TOOLS.md
                               → role-filtered fleet tools
                               → role MCP servers
                               → role plugins with bundled skills
                               → role skills
                               → role CRONs summary
                               → role sub-agents
                               → stage-aware recommendations

DEPLOYMENT:
  scripts/provision-agent-files.sh → agents/{name}/TOOLS.md
  scripts/push-soul.sh            → workspace TOOLS.md (needs fix for per-agent)
```

### The Deployment Pipeline

Today there are gaps in how role-specific tooling reaches workspaces:

```
WHAT WORKS:
  setup-agent-tools.sh  → generates per-agent mcp.json to agents/{name}/
  install-plugins.sh    → installs plugins per agent (if CLI available)
  configure-agent-settings.sh → sets effort/permissions per agent

WHAT'S BROKEN:
  push-soul.sh deploys TEMPLATE mcp.json to workspaces
    → OVERWRITES per-agent mcp.json with template
    → Per-agent MCP servers never reach workspaces
  
  push-soul.sh symlinks fleet skills to workspaces
    → Only .agents/skills/ (13 gateway skills)
    → .claude/skills/ (7 fleet skills) NOT symlinked to workspaces

WHAT'S MISSING:
  Per-agent skill deployment to workspaces
  Per-agent sub-agent definitions in workspaces
  Per-agent hook configurations in workspaces
  Per-agent CRON creation/sync
  Per-agent standing orders in workspace files
  Verification that all components are deployed and functional
```

---

## The Skill Ecosystem — What Exists vs What's Needed

### Available Ecosystem (researched)

| Source | Count | Description |
|--------|-------|-------------|
| Anthropic official plugin directory | 32 internal + 17 external | Full plugins with skills, agents, hooks, MCP |
| Superpowers marketplace | 9 plugins | Core skills, Chrome DevTools, episodic memory, session driver, etc. |
| OpenClaw bundled skills | 51 | Gateway-level, mostly personal assistant (51, 10 fleet-relevant) |
| ClawHub registry | Unlimited (public registry) | External skill store with CLI install |
| OCMC marketplace | 1 pack registered | Catalog layer for org-wide skill management |
| Community (awesome-claude-code) | 150+ resources | Skills, workflows, hooks, slash commands, tools |

### What the Fleet Currently Has

| Layer | Count | Status |
|-------|-------|--------|
| Gateway skills (.agents/skills/) | 13 | Built, deployed |
| Fleet skills (.claude/skills/) | 7 | Built, not deployed to workspaces |
| Declared role skills (config) | ~50+ | Names only, NO SKILL.md files exist |
| Plugin-bundled skills | ~30+ (from superpowers, etc.) | Available IF plugins installed |
| OCMC marketplace skills | 17 (Anthropic pack) | Registered, not installed |

### What's Needed (the PO's scope)

The PO described 10-40 generic + 40+ per role. This is NOT prescriptive numbers — it's the scale of the effort. The actual skill set needs to be:

1. **Evaluated** — what exists in the ecosystem that fits?
2. **Designed** — what fleet-specific skills need to be custom-built?
3. **Organized** — by methodology stage, by task type, by role, by situation
4. **Installed** — via marketplace, workspace, or plugin deployment
5. **Directed** — stage-aware recommendations in methodology protocols and TOOLS.md
6. **Maintained** — as the fleet evolves, skills evolve with it

This is a significant research and design effort PER ROLE. Each role needs its own skill audit:
- What does this role do at each methodology stage?
- What skills exist in the ecosystem for those activities?
- What skills need to be custom-built?
- How should skills be recommended per stage in the autocomplete chain?

---

## What This Document Does NOT Define

This document maps layers, current state, known gaps, and architecture. It deliberately does NOT:

- **Prescribe specific skill content** — each of the 40+ per-role skills needs its own design
- **Specify exact CRON schedules** — each CRON needs its own design session with proper standing orders
- **Define sub-agent specifications** — each sub-agent needs careful tool/model/isolation design
- **Write hook configurations** — each hook needs evaluation against the role's actual workflow
- **Set final effort levels per stage** — needs live testing and tuning
- **Choose which ecosystem skills to install** — needs per-role evaluation
- **Design standing orders** — each role's autonomous authority needs PO-directed scoping

These are each their own work items — some requiring PO input, some requiring ecosystem research, some requiring implementation and testing.

---

## Implementation Phases (Scaffold — Not Prescriptive Order)

### Phase 1: Fix Deployment Pipeline
- Fix push-soul.sh to deploy per-agent mcp.json (not template)
- Deploy .claude/skills/ to workspaces (symlink or copy)
- Verify MCP server packages available (npm/npx accessible in agent workspaces)
- Verify plugin installation works end-to-end

### Phase 2: Evaluate Ecosystem
- Inventory all available skills from all 5 sources
- Per-role evaluation: what existing skills fit?
- Per-role gap analysis: what needs custom building?
- Plugin evaluation: which of 32+ official plugins benefit which roles?
- Marketplace: register additional packs (community, superpowers marketplace)

### Phase 3: Build Foundation Skills
- Per phase-f1-foundation-skills.md: URL builder, markdown templates, PR composer, comment formatter, board memory composer, IRC formatter
- These are infrastructure skills that other skills build on

### Phase 4: Build Role-Specific Skills
- Per role, per methodology stage
- Following the skill creation pipeline: identify need → check ecosystem → evaluate/build → assign → install → verify → document
- This is the largest phase — 40+ skills per role

### Phase 5: Configure CRONs
- Design per-agent CRONs with standing orders
- Create config/agent-crons.yaml
- Build scripts/sync-agent-crons.sh
- Wire fleet state awareness (pause/budget)

### Phase 6: Define Sub-Agents
- Per-role sub-agent definitions
- Evaluate Agent Teams for within-task collaboration
- Deploy to workspaces

### Phase 7: Configure Hooks + Standing Orders
- Per-role hook configurations
- Standing orders in agent files
- Extended thinking stage-aware configuration

### Phase 8: Upgrade Generation Pipeline
- generate-tools-md.sh reads ALL config sources
- Produces complete TOOLS.md covering all 7 layers
- Role-filtered, stage-aware, accurate to what's actually deployed
- Validation: TOOLS.md matches reality

---

## Effort Assessment

The PO said "over 42 hours of effort only for tools, considering it aggregates a bunch of things." This aligns with the scope:

| Work Area | Estimated Scale | Notes |
|-----------|----------------|-------|
| Deployment pipeline fixes | Small | Fix push-soul.sh, verify MCP servers |
| Ecosystem evaluation | Medium | Evaluate 1000+ skills across 5 sources × 10 roles |
| Foundation skills (6) | Medium | Per phase-f1 design doc |
| Role-specific skills (~400+) | Large | 40+ per role × 10 roles, many from ecosystem evaluation |
| CRONs per role | Medium | Design + standing orders + config + sync script |
| Sub-agents per role | Medium | Design + definitions + deployment |
| Hooks + standing orders | Medium | Per-role design + configuration |
| Generation pipeline upgrade | Medium | generate-tools-md.sh comprehensive rewrite |
| Testing and verification | Large | End-to-end: skill installed → agent invokes → correct output |

This is not a single sprint. It's an ongoing capability buildout that evolves as the fleet matures and the PO's vision crystallizes through live operation.

---

## Relationship to Other Work

| Work Item | Relationship |
|-----------|-------------|
| Document 1 (fleet group calls) | Layer 1 of 7. Must be wired before TOOLS.md can document group call chains accurately. |
| Agent elevation (Phase B) | TOOLS.md is one of 8 agent files. Layers 2-7 feed into TOOLS.md content. |
| Brain evolution (Phase C) | Strategic calls, session management, effort selection connect to Layers 5-7. |
| Contribution flow (Phase E) | Skills guide HOW agents produce contributions (architecture-propose → design_input). |
| Phase system (Phase E) | Phase standards affect what skills/depth are appropriate. |
| First live test (Phase D) | Tests whether the capability surface actually works end-to-end. |
| Context system | TOOLS.md injection at position 4 is part of the autocomplete chain architecture. |
| Immune system | Skills reduce disease by making correct behavior easy (structural prevention). |
| Methodology system | Stage-aware skill recommendations feed the autocomplete chain. |

---

## Files Affected or To Be Created

| File | Status | Description |
|------|--------|-------------|
| config/agent-tooling.yaml | EXISTS, EVOLVE | Add evaluated skills, verify MCP servers, update plugins |
| config/agent-crons.yaml | TO CREATE | Per-agent CRON definitions |
| config/skill-assignments.yaml | EXISTS, EVOLVE | Update with evaluated marketplace skills |
| config/skill-packs.yaml | EXISTS, EVOLVE | Register additional packs |
| scripts/push-soul.sh | EXISTS, FIX | Deploy per-agent mcp.json, not template |
| scripts/sync-agent-crons.sh | TO CREATE | CRON creation/sync from config |
| scripts/generate-tools-md.sh | EXISTS, REWRITE | Read all 7 layers, produce complete TOOLS.md |
| scripts/install-plugins.sh | EXISTS, VERIFY | Verify marketplace sources, test installation |
| scripts/install-skills.sh | EXISTS (referenced), VERIFY | Skill installation automation |
| agents/{name}/.claude/agents/ | TO CREATE | Per-role sub-agent definitions |
| agents/{name}/.claude/settings.json | EXISTS, EVOLVE | Stage-aware effort, per-role hooks |
| .claude/skills/*/ | 7 EXIST, 40+ TO CREATE | Role-specific skills |
| .agents/skills/*/ | 13 EXIST, evolve as needed | Gateway-level skills |
| docs/skills-inventory.md | EXISTS, UPDATE | After ecosystem evaluation |