# Skills and Plugins Ecosystem — Full Research

**Date:** 2026-04-07
**Status:** Research — complete ecosystem inventory and technical analysis
**Scope:** Every skill source, every relevant plugin, how discovery works, how the fleet should leverage the ecosystem
**Sources:** GitHub repos (anthropics/skills, anthropics/claude-plugins-official, obra/superpowers, obra/superpowers-marketplace), vendor/openclaw/src/agents/skills/, config/*.yaml, docs.openclaw.ai/automation/

---

## Why This Document Exists

The fleet's config/agent-tooling.yaml lists ~50 skill names per role. NONE of these exist as SKILL.md files. The current list is the PO's initial LocalAI project starting point. In reality there are 1000+ skills available across 5 sources, 32+ official Anthropic plugins, 9+ superpowers marketplace plugins, and an open ClawHub registry.

This document captures the FULL ecosystem research so the fleet can make informed decisions about what to evaluate, install, and build per role.

---

## 1. The 5 Skill Sources — How They Work

### Source 1: OpenClaw/OpenArms Bundled Skills

**Location:** vendor/openclaw/skills/*/SKILL.md
**Scope:** All agents (global)
**Count:** 51 bundled skills
**Discovery:** Automatic at session start — gateway scans skill directories

Fleet-relevant bundled skills (10 of 51):

| Skill | Description | Fleet Relevance |
|-------|-------------|-----------------|
| coding-agent | Delegate coding tasks to sub-agents | HIGH — engineer, QA |
| gh-issues | Fetch GitHub issues, spawn fix agents, open PRs | HIGH — all project work |
| github | GitHub operations via gh CLI | HIGH — all agents |
| healthcheck | Host security hardening, risk config | MEDIUM — devops |
| skill-creator | Create/edit/audit SKILL.md files | HIGH — creating fleet skills |
| tmux | Remote-control tmux sessions | MEDIUM — devops, QA |
| session-logs | Agent session log analysis (requires jq) | MEDIUM — debugging |
| clawhub | Install skills from ClawHub registry | MEDIUM — expanding skill set |
| discord | Discord messaging bridge | LOW — if Discord integration needed |
| slack | Slack workspace integration | LOW — if Slack integration needed |

Not relevant to fleet (41): 1password, apple-notes, apple-reminders, bear-notes, blogwatcher, blucli, bluebubbles, camsnap, canvas, eightctl, gemini, gifgrep, gog, goplaces, himalaya, imsg, mcporter, model-usage, nano-pdf, notion, obsidian, openai-whisper, openai-whisper-api, openhue, oracle, ordercli, peekaboo, sag, sherpa-onnx-tts, songsee, sonoscli, spotify-player, summarize, things-mac, trello, video-frames, voice-call, wacli, weather, xurl, node-connect.

### Source 2: Plugin-Bundled Skills

**Location:** Inside enabled plugins (extensions/{id}/skills/ or plugin's skill arrays)
**Scope:** Per-plugin (only active when plugin is enabled for the agent)
**Discovery:** Automatic when plugin is enabled — gateway resolves via resolvePluginSkillDirs()

Key plugin skill counts:
- superpowers: 14 skills + 1 sub-agent
- pr-review-toolkit: 0 skills, 6 sub-agents
- hookify: 3 slash commands (hookify, hookify:list, hookify:configure) + writing-rules skill
- commit-commands: 3 slash commands (commit, commit-push-pr, clean_gone)
- security-guidance: 0 skills, 9 PreToolUse hooks
- adversarial-spec: 1 primary workflow
- plannotator: 4 slash commands (annotate, last, review, archive)

### Source 3: Fleet Workspace Skills

**Location:** .claude/skills/*/SKILL.md
**Scope:** All agents (project-level — visible to any agent session in this project)
**Count:** 7

| Skill | Description | Invocable |
|-------|-------------|-----------|
| fleet-communicate | Communication surface guide (which channel for what) | No (injected) |
| fleet-plan | How to break down epics into sprint tasks | No (injected) |
| fleet-plane | How to use Plane for sprint management | No (injected) |
| fleet-review | How to review a task as board lead or QA | No (injected) |
| fleet-security-audit | How to conduct a security review | No (injected) |
| fleet-sprint | How to manage a sprint lifecycle | Yes (/fleet-sprint) |
| fleet-test | How to run and analyze test results | No (injected) |

These are WORKFLOW skills — they teach agents HOW to perform fleet-specific operations using fleet tools. They don't add new capabilities, they provide structured procedures.

### Source 4: Gateway Skills

**Location:** .agents/skills/*/SKILL.md
**Scope:** All agents (gateway-level)
**Count:** 13

| Skill | Lines | Purpose |
|-------|-------|---------|
| fleet-alert | 109 | Structured alert posting workflow |
| fleet-comment | 69 | Task comment formatting and posting |
| fleet-commit | 65 | Conventional commit with task reference |
| fleet-gap | 101 | Gap analysis workflow |
| fleet-irc | 60 | IRC message formatting |
| fleet-memory | 84 | Board memory entry creation |
| fleet-pause | 103 | Pause/blocker reporting workflow |
| fleet-pr | 148 | PR creation with proper formatting |
| fleet-report | 61 | Structured report generation |
| fleet-task-create | 95 | Task creation workflow |
| fleet-task-update | 114 | Task update workflow |
| fleet-urls | 74 | URL resolution for fleet references |
| plane-render | 94 | Plane HTML rendering |

These are OPERATIONS skills — they provide detailed procedures for using fleet MCP tools. fleet-commit teaches the agent how to use fleet_commit properly (conventional format, task reference, staged files). fleet-pr teaches how to create publication-quality PRs.

### Source 5: OCMC Marketplace

**Location:** MC database -> gateway dispatch -> workspace installation
**Scope:** Organization-wide catalog, gateway-scoped installation
**Count:** 1 pack registered (Anthropic Official, 17 skills)
**Discovery:** Pack registration -> sync -> skill discovery -> installation

How the marketplace works:
1. Register a skill pack: POST /api/v1/skills/packs with GitHub repo URL
2. Sync the pack: POST /api/v1/skills/packs/{id}/sync — clones repo, discovers SKILL.md files
3. Install a skill: POST /api/v1/skills/marketplace/{id}/install?gateway_id={id}
4. MC dispatches install instruction to Gateway Agent
5. Gateway Agent installs skill to workspace/skills/
6. Next session picks it up via workspace skill discovery

The fleet has scripts for this:
- scripts/register-skill-packs.sh — registers packs from config/skill-packs.yaml
- scripts/install-skills.sh — installs selected skills
- Vendor patch: 0001-skills-marketplace-category-risk-upsert.patch (fixes category/risk on upsert)

Currently only 1 pack registered (Anthropic Official). Additional packs to evaluate:
- ComposioHQ/awesome-claude-skills — community collection
- obra/superpowers-marketplace — 9 plugins from superpowers ecosystem

---

## 2. The Plugin Ecosystem — Full Inventory

### Anthropic Official Plugins (32 Internal)

From anthropics/claude-plugins-official:

| Plugin | Category | Description | Fleet Relevance |
|--------|----------|-------------|-----------------|
| agent-sdk-dev | Development | Claude Agent SDK development | LOW — unless building custom agents |
| clangd-lsp | Language | C/C++ language server | NONE for current fleet |
| claude-code-setup | Meta | Analyze codebase, recommend automations (hooks, skills, MCP, subagents) | HIGH — useful for fleet setup optimization |
| claude-md-management | Meta | Audit CLAUDE.md quality, capture learnings, keep memory current | HIGH — agent file quality |
| code-review | Quality | Automated code review with multiple specialized agents, confidence scoring | HIGH — fleet-ops, QA |
| code-simplifier | Quality | Simplifies code for clarity while preserving functionality | MEDIUM — engineer |
| commit-commands | Git | /commit, /commit-push-pr, /clean_gone | ASSIGNED to devops |
| csharp-lsp | Language | C# language server | NONE |
| example-plugin | Meta | Comprehensive example demonstrating all extension options | LOW — reference only |
| explanatory-output-style | Style | Educational insights about implementation choices | LOW |
| feature-dev | Development | 3 specialized agents: code-explorer (sonnet), code-architect (sonnet), code-reviewer (sonnet) | HIGH — architect, engineer |
| frontend-design | Design | Production-grade frontend avoiding "AI slop" | MEDIUM — UX, engineer |
| gopls-lsp | Language | Go language server | NONE |
| hookify | Automation | Natural-language hook creation | ASSIGNED to devops |
| jdtls-lsp | Language | Java language server | NONE |
| kotlin-lsp | Language | Kotlin language server | NONE |
| learning-output-style | Style | Interactive learning requiring code contributions | LOW |
| lua-lsp | Language | Lua language server | NONE |
| math-olympiad | Reasoning | Competition math with adversarial verification | NONE |
| mcp-server-dev | Development | Design and build MCP servers | MEDIUM — if fleet builds custom MCP |
| php-lsp | Language | PHP language server | NONE |
| playground | Development | Interactive HTML playgrounds with live preview | LOW |
| plugin-dev | Meta | Plugin development toolkit | LOW — reference only |
| pr-review-toolkit | Quality | 6 parallel review agents for PRs | ASSIGNED to fleet-ops |
| pyright-lsp | Language | Python type checking | ASSIGNED to engineer |
| ralph-loop | Experimental | Continuous self-referential AI loops | NONE |
| ruby-lsp | Language | Ruby language server | NONE |
| rust-analyzer-lsp | Language | Rust language server | NONE |
| security-guidance | Security | 9 security patterns via PreToolUse hooks | ASSIGNED to devsecops |
| skill-creator | Meta | Create, improve, eval, benchmark skills | HIGH — building fleet skills |
| swift-lsp | Language | Swift language server | NONE |
| typescript-lsp | Language | TypeScript language server | MEDIUM — if fleet has TS code |

**Not yet assigned but HIGH relevance:**
- **claude-code-setup** — could audit each agent's setup and recommend optimizations
- **claude-md-management** — could maintain CLAUDE.md quality across all agents
- **code-review** — complements pr-review-toolkit with confidence-based scoring
- **feature-dev** — 3 sub-agents (code-explorer, code-architect, code-reviewer) could benefit architect and engineer
- **skill-creator** — essential for building fleet-specific skills at scale

### Anthropic Official Plugins (17 External/Partner)

| Plugin | Author | Description | Fleet Relevance |
|--------|--------|-------------|-----------------|
| asana | Asana | Project management: tasks, projects, assignments | NONE (fleet uses Plane) |
| context7 | Upstash | Version-specific library documentation | ASSIGNED to architect, engineer, writer |
| discord | Community | Discord messaging bridge | LOW |
| fakechat | Community | Localhost chat test surface | LOW — testing only |
| firebase | Google | Firestore, auth, cloud functions, hosting, storage | NONE unless fleet uses Firebase |
| github | GitHub | Issues, PRs, code review, repo search | MEDIUM — some agents have github MCP already |
| gitlab | GitLab | MRs, CI/CD, issues, wikis | NONE (fleet uses GitHub) |
| greptile | Greptile | AI code review for GitHub/GitLab | MEDIUM — fleet-ops, QA |
| imessage | Community | iMessage bridge | NONE |
| laravel-boost | Laravel | Artisan, Eloquent, routing | NONE |
| linear | Linear | Issue tracking, projects, workflows | NONE (fleet uses Plane) |
| playwright | Microsoft | Browser automation and E2E testing | MCP version ASSIGNED; plugin may add more |
| serena | Oraios | Semantic code analysis via LSP | HIGH — could enhance architect, engineer analysis |
| slack | Slack | Workspace messaging, channel search | LOW unless Slack integration needed |
| supabase | Supabase | Database, auth, storage | NONE unless fleet uses Supabase |
| telegram | Community | Telegram messaging bridge | LOW |
| terraform | HashiCorp | IaC development and automation | MEDIUM — devops if using Terraform |

**Not yet assigned but worth evaluating:**
- **serena** — semantic code analysis could significantly enhance codebase understanding for architect and engineer during analysis stage
- **greptile** — AI code review could complement fleet-ops and QA review processes

### Superpowers Marketplace (9 Plugins)

From obra/superpowers-marketplace:

| Plugin | Stars | Description | Fleet Relevance |
|--------|-------|-------------|-----------------|
| superpowers (core) | 139K | TDD, debugging, planning, verification, collaboration | ASSIGNED to architect, engineer, QA |
| superpowers-chrome | — | Direct Chrome DevTools Protocol access, 17 CLI commands | MEDIUM — engineer, QA for debugging |
| elements-of-style | — | Writing guidance from Strunk's Elements of Style, 18 rules | MEDIUM — technical writer |
| episodic-memory | — | Semantic search for Claude Code conversations, cross-session | HIGH — all agents for memory |
| superpowers-lab | — | Experimental: tmux automation, MCP discovery, duplicate detection, Slack, headless VM | LOW — experimental |
| superpowers-developing-for-claude-code | — | Skills and resources for developing Claude Code plugins, 42+ docs | LOW — reference only |
| superpowers-dev | — | Dev branch of core (unstable) | NONE |
| claude-session-driver | — | Launch, control, monitor other Claude Code sessions as workers via tmux | MEDIUM — could be useful for fleet orchestration |
| double-shot-latte | — | Stops "Would you like me to continue?" interruptions, auto-continuation | MEDIUM — could improve agent autonomy |

**Not yet assigned but worth evaluating:**
- **episodic-memory** — semantic search over past conversations could significantly improve cross-session continuity. Complements claude-mem.
- **elements-of-style** — could improve technical writer's output quality
- **double-shot-latte** — auto-continuation could reduce wasted heartbeat cycles where agents ask to continue instead of just doing it
- **claude-session-driver** — could enable the fleet orchestrator to manage sessions more effectively

---

## 3. Superpowers Deep Dive — The Most Impactful Plugin

Superpowers is the largest non-Anthropic plugin (139K stars). It provides the most skills (14) and integrates with multiple platforms. The fleet assigns it to architect, engineer, and QA.

### 14 Skills in Detail

**Meta Skills:**
- **using-superpowers** — loaded via SessionStart hook into every session. Establishes how to discover and use other skills. Includes the flow: check for skills before ANY response, even clarifying questions.
- **writing-skills** — framework for creating new skills. Useful for building fleet-specific skills.

**Design/Planning Skills:**
- **brainstorming** — Socratic design refinement. Iterative questioning to explore problem space before committing to approach. Described as mandatory "before any creative work." Maps to conversation/analysis stages.
- **writing-plans** — Detailed implementation roadmaps. Breaks work into bite-sized tasks with dependencies. Maps to reasoning stage.
- **executing-plans** — Batch execution with human checkpoints. Runs plan steps in separate sessions. Maps to work stage.

**Quality Skills:**
- **test-driven-development** — RED-GREEN-REFACTOR cycle with testing anti-patterns reference. Maps to work stage.
- **systematic-debugging** — 4-phase root cause analysis: hypothesis formation, targeted evidence gathering, defense-in-depth fixing, condition-based verification. Maps to analysis/investigation/work.
- **verification-before-completion** — Requires running verification commands and confirming output before ANY success claims. Prevents "I think it works" without evidence. Maps to work stage pre-completion gate.

**Collaboration Skills:**
- **requesting-code-review** — Pre-review checklist and validation before submitting work for review.
- **receiving-code-review** — Technical rigor for feedback integration. Prevents "performative agreement" — the agent must genuinely engage with feedback, not just say "good point."

**Orchestration Skills:**
- **dispatching-parallel-agents** — Concurrent subagent workflows for 2+ independent tasks. Teaches when and how to spawn parallel workers.
- **subagent-driven-development** — Two-stage review: first check spec compliance, then code quality. Both in current session.

**Git Skills:**
- **using-git-worktrees** — Isolated parallel development branches with safety verification.
- **finishing-a-development-branch** — Structured decision for merge, PR, or cleanup.

### How Superpowers Integrates

The SessionStart hook injects the using-superpowers skill into every session. This skill establishes:
1. Before ANY response, check if a skill applies (even 1% chance)
2. If yes, invoke the Skill tool to load it
3. If the skill has a checklist, create TodoWrite items
4. Follow the skill exactly

This creates a skill-first workflow — the agent doesn't decide on its own approach, it checks for a structured skill first. This aligns with the fleet's autocomplete chain philosophy: correct behavior is the natural continuation.

### Superpowers Code-Reviewer Sub-Agent

A senior code reviewer agent defined in agents/code-reviewer.md. Reviews completed project steps against:
- Original plan alignment
- Code quality
- Architecture/design
- Documentation/standards
- Issue categorization (Critical/Important/Suggestion)

The fleet's fleet-ops could use this as an additional review layer alongside pr-review-toolkit's 6 parallel agents.

---

## 4. PR-Review-Toolkit Deep Dive — Fleet-Ops Review Engine

Assigned to fleet-ops. Provides 6 specialized sub-agents that review PRs in parallel:

| Agent | Model | Focus | Output |
|-------|-------|-------|--------|
| code-reviewer | opus | CLAUDE.md compliance, style, bugs, quality | 0-100 score (91+ = critical) |
| code-simplifier | inherit | Simplification preserving functionality | Qualitative recommendations |
| comment-analyzer | inherit | Comment accuracy, doc completeness, comment rot | Qualitative assessment |
| pr-test-analyzer | inherit | Behavioral coverage (not line coverage), test gaps, edge cases | 1-10 rating (10 = critical gap) |
| silent-failure-hunter | inherit | Error handling: silent catch blocks, inadequate fallbacks, missing logging | Zero-tolerance categorization |
| type-design-analyzer | inherit | Type encapsulation, invariant expression, enforcement, usefulness | 1-10 per dimension |

The /review-pr command dispatches all 6 in parallel. Each independently analyzes the same PR from a specialized lens. Results aggregated with structured output.

This maps directly to fleet-ops' core job (fleet-elevation/06): real review against verbatim, trail completeness, acceptance criteria, phase standards. The 6 sub-agents automate the technical review dimensions while fleet-ops focuses on methodology compliance and PO requirement matching.

---

## 5. Skill Loading — Technical Pipeline

### How Skills Reach Agent Sessions

At session startup, the gateway:

1. **Loads skill entries** from 4 sources with precedence:
   - Workspace skills (workspace/skills/) — HIGHEST
   - Managed/local skills (~/.openclaw/skills/)
   - Plugin skills (from enabled plugins)
   - Bundled skills — LOWEST

2. **Parses each SKILL.md** — extracts YAML frontmatter (name, description, metadata)

3. **Filters for eligibility** via shouldIncludeSkill():
   - Check metadata.openclaw.requires.bins (binaries on PATH)
   - Check metadata.openclaw.requires.env (env vars set)
   - Check metadata.openclaw.requires.config (config keys truthy)
   - Check metadata.openclaw.os (platform filter)
   - Check skills.entries.{key}.enabled in config (explicit disable)
   - Check skills.allowBundled (bundled allowlist)
   - Check metadata.openclaw.always (force-include)

4. **Builds prompt** — formatSkillsForPrompt() creates compact XML list injected into system prompt
   - Max 150 skills in prompt
   - Max 30,000 chars for skills prompt section
   - Max 256KB per SKILL.md file

5. **Snapshots** — Skills snapshotted at session start, reused across turns

### Per-Agent Skill Control

The gateway supports per-agent skill filtering:
- skills.allowBundled: restrict which bundled skills an agent sees
- agents.list[].skills: per-agent skill configuration
- Workspace-specific skills: put skills in agent's workspace only
- Plugin enable/disable: control which plugins (and their skills) are active

The fleet's config/agent-tooling.yaml declares which skills each agent SHOULD have. But the runtime enforcement depends on how skills are deployed to workspaces.

### SKILL.md Format

```markdown
---
name: skill-name
description: When to trigger this skill and what it does
user-invocable: true|false
license: Optional license reference
---

# Skill Instructions

[Markdown content the agent follows when skill is active]

## When to Use
[Conditions for invoking this skill]

## Steps
[Procedure to follow]

## Rules
[Constraints and requirements]

## Examples
[Concrete examples of correct usage]
```

user-invocable: true means the agent or user can trigger it as a /slash-command.
user-invocable: false means it's injected as context for the AI to reference when appropriate.

---

## 6. What the Fleet Has vs What's Available

### Skills Gap Analysis

| Category | Fleet Has | Available in Ecosystem | Gap |
|----------|-----------|----------------------|-----|
| Fleet operations (commit, PR, alert, etc.) | 13 gateway + 7 fleet = 20 | — (fleet-specific) | Adequate for basics. Phase-f1 designs 6 more (M81-M86). |
| TDD / debugging / verification | 0 built, superpowers plugin available | superpowers: 14 skills | INSTALL superpowers plugin |
| Code review | 0 built, pr-review-toolkit available | pr-review-toolkit: 6 agents | INSTALL pr-review-toolkit |
| Architecture design | 0 built | Need custom or evaluate serena | BUILD or EVALUATE |
| Security audit | 1 (fleet-security-audit) | security-guidance: 9 hooks | COMPLEMENT with plugin |
| Sprint management | 1 (fleet-sprint) | plannotator: 4 commands | COMPLEMENT with plugin |
| Documentation | 0 role-specific | elements-of-style, context7 | EVALUATE and BUILD |
| UX design | 0 role-specific | frontend-design plugin | EVALUATE |
| Infrastructure | 0 role-specific | terraform plugin (if relevant) | BUILD fleet-specific |
| Quality/testing | 0 role-specific | superpowers TDD, webapp-testing | INSTALL + BUILD |
| Cross-session memory | 0 | claude-mem, episodic-memory | INSTALL |
| Stage-specific methodology | 0 | Need custom | BUILD per stage per role |

### Plugin Gap Analysis

| Agent | Currently Assigned | Worth Evaluating | Reason |
|-------|-------------------|------------------|--------|
| Architect | context7, superpowers, adversarial-spec | feature-dev, serena, claude-code-setup | Sub-agents for exploration, semantic analysis |
| Engineer | context7, superpowers, pyright-lsp | feature-dev, code-review | Sub-agents, confidence-based review |
| QA | superpowers | code-review, webapp-testing (Anthropic) | Quality analysis, browser testing |
| DevOps | hookify, commit-commands | terraform (if relevant) | IaC automation |
| DevSecOps | security-guidance, sage | — | sage needs evaluation (repo not found) |
| Fleet-Ops | pr-review-toolkit | code-review, claude-md-management | Additional review, CLAUDE.md quality |
| PM | plannotator | — | Adequate |
| Writer | context7, ars-contexta | elements-of-style, episodic-memory | Writing quality, conversation memory |
| UX | (none specific) | frontend-design, playwright plugin | Design skills, visual testing |
| Accountability | (none specific) | claude-md-management | Quality auditing |
| ALL | claude-mem, safety-net | episodic-memory, double-shot-latte, claude-code-setup | Memory, auto-continuation, setup optimization |

---

## 7. The Skill Creation Strategy

### For Fleet-Specific Skills (no ecosystem equivalent)

Use the skill-creator plugin (Anthropic official) or superpowers' writing-skills skill:
1. Define the skill's purpose, trigger conditions, and procedure
2. Write SKILL.md following the established format
3. Test with an agent — does it invoke correctly? Does it produce correct output?
4. Benchmark if possible (skill-creator supports eval and benchmarking)
5. Deploy to the appropriate skill directory

### For Ecosystem Skills (install and configure)

1. Identify the plugin or skill pack that contains it
2. Register the pack in OCMC marketplace (if not already)
3. Install the plugin per agent (via install-plugins.sh)
4. Verify the skill appears in agent's skill list
5. Test with the agent — does it work in the fleet context?
6. Update config/agent-tooling.yaml with the assignment

### For Pack Aggregation (the PO's vision)

The PO described aggregating appropriate packs per role. This means:
1. Identify all packs relevant to a role
2. Install all of them for that role
3. Ensure skills don't conflict (name collisions, contradictory instructions)
4. Direct usage via methodology protocols (stage X -> use skill Y from pack Z)
5. Skills from different packs compose — superpowers' brainstorming + adversarial-spec's debate + fleet's fleet-plan all work together during reasoning stage

### Skill Categories for the Fleet

Based on the PO's description and the methodology system:

**Generic Methodology Skills (10-40, applicable across roles):**
- Per-stage skills: conversation-protocol, analysis-protocol, investigation-protocol, reasoning-protocol, work-protocol (these exist in config/methodology.yaml as protocol text — could also be skills)
- Cross-stage: brainstorming, systematic-debugging, writing-plans, executing-plans, verification-before-completion (from superpowers)
- Fleet operations: fleet-communicate, fleet-plan, fleet-review, fleet-test (exist)
- Quality: quality-audit, quality-lint, quality-coverage (to build or evaluate)
- Context management: context-awareness, smart-compaction, artifact-extraction (to build)

**Role-Specific Skills (40+ per role):**
- Architect: architecture-propose, architecture-review, design-patterns, complexity-assessment, ADR-creation, codebase-exploration, option-comparison, scaffold, dependency-analysis, technology-evaluation, ...
- Engineer: feature-implement, feature-test, refactor-extract, refactor-split, debug-systematic, contribution-consumption, PR-creation, code-review-response, conventional-commit, test-writing, ...
- QA: test-predefinition, coverage-analysis, regression-testing, test-strategy, acceptance-criteria-validation, boundary-analysis, integration-testing, load-testing, ...
- DevOps: infrastructure-analysis, docker-management, CI-pipeline, deployment-procedure, monitoring-setup, rollback-procedure, backup-procedure, config-management, ...
- DevSecOps: vulnerability-scan, dependency-audit, threat-model, compliance-check, incident-response, penetration-testing-mindset, secret-scanning, infrastructure-security, ...
- PM: sprint-planning, backlog-grooming, capacity-assessment, velocity-tracking, blocker-resolution, stakeholder-communication, epic-breakdown, retrospective, ...
- Fleet-Ops: real-review-protocol, trail-verification, methodology-compliance-check, board-health-monitoring, budget-awareness, quality-enforcement, ...
- Writer: documentation-structure, API-documentation, setup-guide, changelog-generation, terminology-consistency, audience-awareness, ...
- UX: interaction-design, accessibility-audit, component-patterns, user-flow-mapping, error-message-design, CLI-UX, API-UX, ...
- Accountability: trail-reconstruction, compliance-report, pattern-detection, audit-methodology, evidence-gathering, ...

**These are NOT specifications** — they're the TYPES of skills each role needs. The actual skill content requires per-role design work, ecosystem evaluation, and PO direction. Some will come from ecosystem packs. Some need custom building. The 40+ per role is the SCALE, not a prescriptive list.

**Task-Specific Skills:**
- Security audit workflow (for security-tagged tasks)
- Architecture review workflow (for design-tagged tasks)
- Performance analysis workflow (for performance-tagged tasks)
- Migration workflow (for migration-tagged tasks)
- Incident response workflow (for urgent/crisis tasks)

**Project Management Specific Skills:**
- Sprint planning with capacity awareness
- Epic breakdown with dependency mapping
- Retrospective facilitation
- Stakeholder status report
- Release management

These categories overlap — a PM sprint planning skill is both "project management specific" and "PM role-specific." The organization is by usage context, not rigid taxonomy.

---

## 8. Stage-Aware Skill Recommendation — The Pattern

The methodology protocol text (config/methodology.yaml) tells agents WHAT to do at each stage. Skills tell agents HOW to do it.

The connection:

```
Stage protocol says:    "Produce an analysis document with file references"
Skill teaches:          How to structure an analysis document, what to include,
                        how to reference files, what quality standards apply
Tool enables:           fleet_artifact_create("analysis_document", title)
```

Three layers: protocol (what) -> skill (how) -> tool (execute).

The agent's autocomplete chain:
1. Context includes current stage from methodology (e.g., "analysis")
2. TOOLS.md includes stage-appropriate skill recommendations
3. HEARTBEAT.md includes priority protocol for current situation
4. Agent naturally reaches for the right skill at the right time

This is NOT about blocking skills at wrong stages (tools are blocked, skills are guidance). It's about RECOMMENDING skills at the right stage so the agent's natural action is the correct workflow.

How to implement this in TOOLS.md generation:
- generate-tools-md.sh reads config/methodology.yaml for stage names
- For each stage, includes a "Recommended Skills" section with skills appropriate to that stage
- Skills are tagged by applicable stages in their metadata or in a config mapping
- The generation script produces: "At ANALYSIS stage, consider: /architecture-review, /quality-audit, /systematic-debugging"

This needs a config mapping (to be created) that connects skills to stages:
```yaml
# config/skill-stage-mapping.yaml (TO CREATE)
# Maps skills to methodology stages for TOOLS.md recommendations
conversation:
  - brainstorming
  - idea-capture
analysis:
  - systematic-debugging
  - quality-audit
  - architecture-review
investigation:
  - adversarial-spec
  - context7
reasoning:
  - writing-plans
  - architecture-propose
  - feature-plan
work:
  - test-driven-development
  - executing-plans
  - verification-before-completion
```

---

## 9. Known Issues

### Outdated References in Config

config/agent-tooling.yaml references "openclaw-health", "openclaw-fleet-status", "openclaw-setup", "openclaw-add-agent" — these reference the OpenClaw vendor name. The fleet is called OpenFleet, the vendor is OpenArms (or OpenClaw as fallback via vendor.sh). These skill names should be updated to be vendor-agnostic or reference the correct vendor.

### Plugin Marketplace Source Availability

Several plugins referenced in the fleet config have uncertain availability:
- sage (Agent Detection and Response) — repository not publicly findable
- ars-contexta — limited public information, trial vault only
- Some marketplace registrations in install-plugins.sh may reference stale GitHub URLs

These need verification before deployment.

### Skill Discovery Limits

The gateway limits skills in the system prompt:
- Max 150 skills
- Max 30,000 chars for skills section
- Max 256KB per SKILL.md file

With 40+ skills per role plus 10-40 generic skills, some agents could approach the 150 skill limit. This means skills need to be CURATED, not just accumulated. Quality over quantity — each skill should earn its place in the agent's context.

### Skills and Context Budget

Every skill injected into the system prompt consumes context tokens. More skills = less room for task context, fleet context, and dynamic data. The 4000 char limit for TOOLS.md (gateway injection) applies to the agent file, but skills are loaded SEPARATELY by the gateway's skill loading system. Still, total context budget matters.

This connects to the PO's context window awareness requirements (CW-01 through CW-06). The brain needs to be aware of how much context the skill injection consumes and factor it into session strategy decisions.
