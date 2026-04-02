# Analysis 03 — Skills Branch of the Knowledge Map

**Date:** 2026-04-02
**Status:** ANALYSIS — mapping all skills into the knowledge tree
**Purpose:** Every skill has a place in the map. Where does each fit,
how does it enhance the system, what does it connect to.

> "the highest enhancement will be the win. never we will settle or minimize."
> Every skill is a leaf on the tree. The map is comprehensive.

---

## The Skills Landscape — Complete Picture

### What We Have (85 internal skills)

**37 substantive skills** with real differentiated content:
- 7 fleet-specific (fleet-review, fleet-plan, fleet-test, fleet-security-audit, fleet-sprint, fleet-communicate, fleet-plane)
- 5 OpenClaw operations (setup, add-agent, configure-mc, health, fleet-status)
- 8 foundation (deps, config, ci, docker, database, auth, logging, testing)
- 6 ops (deploy, rollback, incident, backup, scale, maintenance)
- 6 PM (assess, plan, retrospective, handoff, changelog, status-report)
- 2 architecture (propose, review)
- 3 scaffold (base, monorepo, subagent)
- 2 idea (capture, refine)

**48 template skills** with identical boilerplate but meaningful intent:
- 6 feature lifecycle (plan, implement, test, review, document, iterate)
- 7 infrastructure (search, api, networking, storage, monitoring, cache, queue)
- 6 refactor (split, rename, architecture, dependencies, extract, patterns)
- 6 quality (accessibility, audit, performance, lint, debt, coverage)
- 5 config (secrets, env, deploy, feature-flags, migrations)
- 6 evolve (api-version, internationalize, migrate, scale, plugin-system, integrate)
- 1 infra-security
- 4 MVP composites (full, api, frontend, agent)
- 5 cycle composites (full-feature, full-refactor, release, incident, onboarding)
- 2 additional (feature-iterate, infra-search)

### What the Ecosystem Offers (5000+ skills across 6 collections)

**Superpowers (132K stars) — 14 methodology skills:**
The HOW of software development. Brainstorming before code. TDD that deletes code written before tests. Systematic debugging with 4-phase root cause. Verification that actually confirms the fix works. Plans broken into 2-5 minute tasks. Subagent-driven development with two-stage review. Git worktree parallel development.

These don't replace our skills — they ADD a methodology layer. Our skills say WHAT to do (implement a feature). Superpowers says HOW to do it correctly (brainstorm → plan → TDD → verify → review).

**anthropics/skills (109K stars) — 17 official reference skills:**
The canonical examples of how skills should be built. Document creation (docx, pdf, pptx, xlsx), web artifacts, testing with Playwright, MCP server building, skill creation meta-skill. Reference quality — the standard to measure against.

**VoltAgent (14K stars) — 1,060+ vendor-official skills:**
The deepest integration layer. Skills maintained by the companies who BUILD the tools:
- Trail of Bits (21 security skills) — semgrep rules, property-based testing, variant analysis, constant-time analysis. Written by actual security researchers, not AI-generated templates.
- Microsoft (133 Azure SDK skills) — 6 languages deep.
- HashiCorp (11 Terraform skills) — infrastructure patterns from the source.
- Sentry (7 error monitoring skills) — debugging from the error tracking experts.
- Hugging Face (13 ML skills) — model training from the ML platform team.

These are the EXPERT VOICES of each domain. When our devsecops agent needs to create custom Semgrep rules, Trail of Bits' skill knows how because Trail of Bits wrote it.

**alirezarezvani (9K stars) — 223 role-based expert personas:**
The DEPTH per role. Not just "architect" but "senior-architect who knows when to apply Domain-Driven Design vs CQRS and can articulate why." The POWERFUL tier adds capabilities we don't have at all:
- agent-designer — designs agent architectures (directly relevant to our fleet)
- agent-workflow-designer — designs agent workflows
- rag-architect — designs RAG systems (directly relevant to LightRAG integration)
- mcp-server-builder — builds MCP servers (we need this for custom fleet tools)
- skill-security-auditor — scans skills for malicious code
- pr-review-expert — deep PR review methodology
- tech-debt-tracker — systematic debt tracking
- observability-designer — monitoring and alerting design
- incident-commander — incident response leadership

Each of these is a DEEP persona with domain expertise that goes beyond our template skills.

**plugins-plus-skills (2K stars) — 2,811 atomic task generators:**
The BREADTH of specific operations. Dockerfile generator, Helm chart generator, GitHub Actions starter, Terraform module creator, Prometheus config generator. These are atomic tools — you invoke them for a specific output. Less methodology, more "generate this artifact."

Organized in 20 packs of 25 skills each:
01-DevOps-Basics, 02-DevOps-Advanced, 03-Security-Fundamentals, 04-Security-Advanced, 05-Frontend, 06-Backend, 07-ML-Training, 08-ML-Deployment, 09-Test-Automation, 10-Performance-Testing, 11-Data-Pipelines, 12-Data-Analytics, 13-AWS, 14-GCP, 15-API-Development, 16-API-Integration, 17-Technical-Docs, 18-Visual-Content, 19-Business-Automation, 20-Enterprise-Workflows

**antigravity (30K stars) — 1,340+ bundled skills:**
Wide aggregation with bundle installer. Agent-orchestrator, agent-memory-systems, agent-evaluation, SPDD (subagent-parallel-driven-development), plus hundreds of domain-specific skills. The installer CLI (`npx antigravity-awesome-skills --claude`) makes deployment easy.

---

## How Skills Map to the Knowledge Tree

### The Skills Manual Branch Structure

Every skill occupies a position defined by THREE coordinates:
1. **Domain** — what area of expertise (security, architecture, testing, ops, PM, fleet)
2. **Role** — which agents use it (can be multiple)
3. **Stage** — when in the methodology it's invoked (conversation→analysis→investigation→reasoning→work)

```
Skills Manual/
│
├── METHODOLOGY (how to work — cross-cutting, all agents)
│   │
│   ├── Superpowers methodology layer
│   │   ├── brainstorming — Socratic design before code
│   │   │   Roles: ALL | Stage: conversation, reasoning
│   │   │   Connects to: idea-capture, architecture-propose
│   │   │   Enhancement: prevents jumping to implementation
│   │   │
│   │   ├── test-driven-development — RED-GREEN-REFACTOR
│   │   │   Roles: ENG, QA | Stage: work
│   │   │   Connects to: feature-test, feature-implement, quality-coverage
│   │   │   Enhancement: enforces test-first, deletes code without tests
│   │   │
│   │   ├── writing-plans — 2-5 min tasks with exact files
│   │   │   Roles: ALL | Stage: reasoning
│   │   │   Connects to: feature-plan, pm-plan, fleet-plan
│   │   │   Enhancement: plans specific enough for junior dev to execute
│   │   │
│   │   ├── systematic-debugging — 4-phase root cause
│   │   │   Roles: ENG, QA, DEVOPS | Stage: investigation, work
│   │   │   Connects to: ops-incident, /debug command
│   │   │   Enhancement: structured debugging vs random guessing
│   │   │
│   │   ├── verification-before-completion — ensure actually fixed
│   │   │   Roles: ALL | Stage: work
│   │   │   Connects to: fleet-review, fleet_task_complete
│   │   │   Enhancement: prevents "it compiles" = done
│   │   │
│   │   ├── subagent-driven-development — fresh context per task
│   │   │   Roles: ALL | Stage: work
│   │   │   Connects to: orchestrator dispatch, Agent Teams
│   │   │   Enhancement: maps to fleet dispatch model
│   │   │
│   │   ├── requesting-code-review — pre-review checklist
│   │   │   Roles: ALL | Stage: work (before fleet_task_complete)
│   │   │   Connects to: fleet-review, fleet_task_complete
│   │   │   Enhancement: review readiness gate
│   │   │
│   │   ├── receiving-code-review — process feedback
│   │   │   Roles: ALL | Stage: work (after rejection)
│   │   │   Connects to: readiness regression, trail events
│   │   │   Enhancement: structured response to feedback
│   │   │
│   │   ├── using-git-worktrees — parallel branches
│   │   │   Roles: ENG, DEVOPS | Stage: work
│   │   │   Connects to: dispatch worktree setup, /batch
│   │   │   Enhancement: parallel development patterns
│   │   │
│   │   └── finishing-a-development-branch — merge/PR decisions
│   │       Roles: ENG, DEVOPS | Stage: work
│   │       Connects to: fleet_task_complete, PR workflow
│   │       Enhancement: clean branch completion protocol
│   │
│   ├── Fleet methodology (our 5-stage protocol)
│   │   ├── Stage instructions from stage_context.py
│   │   │   CONVERSATION: understand, don't build
│   │   │   ANALYSIS: examine what exists
│   │   │   INVESTIGATION: explore options
│   │   │   REASONING: plan approach
│   │   │   WORK: execute the plan
│   │   │
│   │   └── Per-stage tool/skill/command recommendations
│   │       (This is what the intent-map drives)
│   │
│   └── anthropics/skills reference patterns
│       ├── skill-creator — meta-skill for building new skills
│       ├── mcp-builder — create MCP servers for external APIs
│       └── webapp-testing — testing with Playwright
│
├── FLEET OPERATIONS (fleet-specific skills)
│   │
│   ├── Sprint & Task Management
│   │   ├── fleet-plan — break epic into sprint tasks with deps
│   │   ├── fleet-sprint — sprint lifecycle (load→dispatch→track→retro)
│   │   ├── fleet-plane — Plane bidirectional sync
│   │   └── fleet-communicate — which surface for which message
│   │
│   ├── Quality & Review
│   │   ├── fleet-review — 7-step review checklist
│   │   ├── fleet-test — run + analyse tests for review decisions
│   │   └── fleet-security-audit — code, infra, supply chain review
│   │
│   └── Infrastructure
│       ├── openclaw-setup — initialize OpenClaw
│       ├── openclaw-add-agent — register new agent
│       ├── openclaw-configure-mc — connect MC to gateway
│       ├── openclaw-health — comprehensive health check
│       └── openclaw-fleet-status — operational status
│
├── PROJECT LIFECYCLE (AICP substantive skills)
│   │
│   ├── Ideation
│   │   ├── idea-capture — structured idea document
│   │   └── idea-refine — critical analysis of idea gaps
│   │
│   ├── Architecture
│   │   ├── architecture-propose — concrete buildable architecture
│   │   └── architecture-review — completeness + quality check
│   │
│   ├── Scaffolding
│   │   ├── scaffold — full project structure from architecture
│   │   ├── scaffold-monorepo — multi-package workspace
│   │   └── scaffold-subagent — new fleet agent
│   │
│   ├── Foundation
│   │   ├── foundation-deps — dependency management
│   │   ├── foundation-config — configuration management
│   │   ├── foundation-ci — CI/CD pipeline
│   │   ├── foundation-docker — containerization
│   │   ├── foundation-database — schema + migrations
│   │   ├── foundation-auth — authentication + RBAC
│   │   ├── foundation-logging — structured logging
│   │   └── foundation-testing — test infrastructure
│   │
│   ├── Operations
│   │   ├── ops-deploy — deployment with pre-flight checks
│   │   ├── ops-rollback — rollback to last known good
│   │   ├── ops-incident — incident response + RCA
│   │   ├── ops-backup — backup/restore procedures
│   │   ├── ops-scale — runtime scaling
│   │   └── ops-maintenance — routine maintenance
│   │
│   └── Project Management
│       ├── pm-assess — project state assessment
│       ├── pm-plan — milestone planning
│       ├── pm-retrospective — what went well/poorly
│       ├── pm-handoff — handoff documentation
│       ├── pm-changelog — changelog generation
│       └── pm-status-report — stakeholder report
│
├── DOMAIN EXPERTISE (from ecosystem — expert voices)
│   │
│   ├── Security (Trail of Bits — 21 skills)
│   │   ├── semgrep-rule-creator — custom SAST rules for our codebase
│   │   │   Roles: DEVSEC | Stage: work
│   │   │   Connects to: infra-security, Semgrep MCP
│   │   │   Enhancement: codebase-specific security patterns
│   │   │
│   │   ├── property-based-testing — generative test approach
│   │   │   Roles: DEVSEC, QA | Stage: work
│   │   │   Connects to: feature-test, TDD
│   │   │   Enhancement: finds edge cases humans miss
│   │   │
│   │   ├── variant-analysis — find similar vulnerabilities
│   │   │   Roles: DEVSEC | Stage: investigation
│   │   │   Connects to: fleet-security-audit
│   │   │   Enhancement: one vuln found → scan for variants
│   │   │
│   │   └── constant-time-analysis — crypto/security-critical code
│   │       Roles: DEVSEC | Stage: analysis, work
│   │       Connects to: architecture-review
│   │       Enhancement: timing attack prevention
│   │   (+ 17 more Trail of Bits skills)
│   │
│   ├── Architecture (alirezarezvani POWERFUL)
│   │   ├── agent-designer — design agent architectures
│   │   │   Roles: ARCH, FLEET-OPS | Stage: reasoning
│   │   │   Connects to: scaffold-subagent, fleet agent refactor
│   │   │   Enhancement: we're building an agent fleet — this is core
│   │   │
│   │   ├── rag-architect — design RAG systems
│   │   │   Roles: ARCH | Stage: reasoning
│   │   │   Connects to: LightRAG, AICP rag.py, knowledge map
│   │   │   Enhancement: our RAG integration needs architecture
│   │   │
│   │   ├── mcp-server-builder — build MCP servers
│   │   │   Roles: ARCH, ENG | Stage: work
│   │   │   Connects to: fleet MCP server, custom tools
│   │   │   Enhancement: build new fleet tools
│   │   │
│   │   └── observability-designer — monitoring + alerting
│   │       Roles: DEVOPS | Stage: reasoning, work
│   │       Connects to: infra-monitoring, storm system
│   │       Enhancement: fleet observability design
│   │
│   ├── Review (alirezarezvani + ecosystem)
│   │   ├── pr-review-expert — deep PR review methodology
│   │   │   Roles: FLEET-OPS | Stage: work (review)
│   │   │   Connects to: fleet-review, fleet_approve
│   │   │   Enhancement: deeper than our 7-step checklist
│   │   │
│   │   └── tech-debt-tracker — systematic debt tracking
│   │       Roles: QA, ACCT | Stage: analysis
│   │       Connects to: quality-debt, quality-audit
│   │       Enhancement: debt as first-class tracked entity
│   │
│   ├── DevOps (HashiCorp + ecosystem)
│   │   ├── 11 Terraform skills — infrastructure patterns
│   │   │   Roles: DEVOPS | Stage: work
│   │   │   Connects to: foundation-docker, ops-deploy
│   │   │   Enhancement: IaC expertise from HashiCorp themselves
│   │   │
│   │   └── playwright-pro (9 sub-skills) — deep browser testing
│   │       Roles: QA, UX | Stage: work
│   │       Connects to: Playwright MCP, foundation-testing
│   │       Enhancement: 9 specialized browser testing patterns
│   │
│   └── PM & Product (alirezarezvani)
│       ├── senior-pm — deep PM methodology
│       ├── scrum-master — Scrum expertise
│       ├── agile-product-owner — PO methodology
│       └── product-manager-toolkit — product management
│       Roles: PM | Stage: any
│       Connects to: pm-plan, fleet-sprint
│       Enhancement: PM as top-tier expert, not generic manager
│
├── TASK GENERATORS (atomic, per-need)
│   │
│   ├── Feature lifecycle (48 template skills — need differentiation)
│   │   ├── feature-plan, feature-implement, feature-test, etc.
│   │   └── Enhancement path: differentiate top 15 with real content,
│   │       or let Superpowers methodology layer drive HOW to execute
│   │
│   ├── Infrastructure generators (from plugins-plus-skills)
│   │   ├── DevOps-Basics (25): dockerfile-generator, github-actions-starter, etc.
│   │   ├── DevOps-Advanced (25): terraform-module-creator, helm-chart-generator, etc.
│   │   ├── Security-Fundamentals (25): sql-injection-detector, secret-scanner, etc.
│   │   └── ... (20 packs × 25 = 500 atomic generators)
│   │   Enhancement: pick specific generators per role when needed
│   │
│   └── Composites (9 — chain multiple skills)
│       ├── mvp-full, mvp-api, mvp-frontend, mvp-agent
│       └── full-feature-cycle, full-refactor-cycle, release-cycle, incident-cycle, onboarding-cycle
│       Enhancement: orchestration-level skills for complex workflows
│
└── REFERENCE (learning, meta-skills, standards)
    ├── anthropics/skills — canonical skill examples
    ├── Superpowers writing-skills — meta-skill for creating skills
    ├── skill-security-auditor — scan skills for malicious code
    └── hooks-mastery — educational hook patterns
```

---

## How Skills Connect to Other Map Branches

| Skill Category | Connects To |
|---------------|------------|
| Methodology (Superpowers) | → Commands (/plan, /debug), → Hooks (PreToolUse), → Agent CLAUDE.md (stage protocol) |
| Fleet Operations | → Tool Manuals (fleet MCP 29 tools), → Agent HEARTBEAT.md (action protocol) |
| Project Lifecycle | → Standards Manual (artifact types), → Methodology Manual (stage→skill) |
| Security (Trail of Bits) | → MCP Servers (Semgrep, Trivy, Snyk), → Agent CLAUDE.md (security rules) |
| Architecture (alirezarezvani) | → System Manuals (22 systems), → Module Manuals (94 modules) |
| Task Generators | → Tool Chains (fleet-elevation/24), → Standards (artifact schemas) |

---

## What This Means for Injection

The intent-map uses skills as part of the injection profile:

**Opus 1M context:** Full skill descriptions + methodology layer + domain expertise
**Sonnet 200K:** Skill names + key instructions + methodology highlights
**LocalAI 8K:** "Available skills: /feature-implement, /fleet-review" (names only)
**Heartbeat:** No skills injected (heartbeat protocol drives behavior)

---

## Enhancement Potential

The skills branch is where the fleet goes from "agents that follow instructions" to "top-tier experts with deep domain knowledge." Each layer adds capability:

1. **Fleet core** → agents operate in the fleet
2. **Project lifecycle** → agents build software
3. **Methodology** → agents build software CORRECTLY
4. **Domain expertise** → agents are EXPERTS in their domain
5. **Task generators** → agents produce specific artifacts efficiently

The knowledge map makes all of this navigable and injectable. An architect in REASONING stage gets: architecture-propose + brainstorming + writing-plans + agent-designer + rag-architect. Not because we hardcode it, but because the map's intent-map says "architect + reasoning = these skills."

---

## PO Decision Points

1. **Superpowers:** Install as plugin and adapt autonomy? Or cherry-pick the 6 methodology skills into our own skills system?
2. **Trail of Bits (21 skills):** Install for devsecops? These are the highest quality security skills in the ecosystem.
3. **alirezarezvani role-depth:** Which POWERFUL skills to adopt? agent-designer, rag-architect, mcp-server-builder are directly relevant.
4. **48 template skills:** Differentiate the top 15? Let Superpowers replace some? Both?
5. **Task generators (500+ from plugins-plus-skills):** Cherry-pick per role? Or reference in the map without installing?
6. **Skill deployment architecture:** How do all these layers get into each agent's workspace?
