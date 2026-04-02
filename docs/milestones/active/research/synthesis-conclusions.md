# Synthesis — Conclusions from All Research and Analysis

**Date:** 2026-04-02
**Status:** SYNTHESIS — all decision points consolidated
**Source:** Research groups 01-04, Analysis 01-05 (2,493 lines)

> This document consolidates every decision point from the research
> and analysis phases. PO decisions here drive the roadmap, the
> knowledge map content, and the implementation order.

---

## How the 5 Branches Connect

```
                    Knowledge Map (root)
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    CAPABILITIES    KNOWLEDGE       ENFORCEMENT
         │               │               │
    ┌────┴────┐    ┌─────┴─────┐    ┌───┴────┐
    │         │    │           │    │        │
  Tools    Skills  Systems   Agents Hooks  Standards
  (MCP)   (slash)  (22 docs) (10)  (26)   (8+13)
    │         │    │           │    │        │
  Plugins  Commands Modules  Roles  Anti-   Methodology
  (bundles) (50+)  (94)    (matrix) corrupt (5 stages)
    │         │    │           │    │        │
    └────┬────┘    └─────┬─────┘    └───┬────┘
         │               │              │
    AGENT FILES     MAP CONTENT    INJECTION LOGIC
   (CLAUDE.md,     (manuals,      (intent-map,
    TOOLS.md,      condensed,      profiles,
    HEARTBEAT)     minimal)        navigator)
```

**Capabilities** (Tools + Skills + Plugins + Commands) define WHAT agents can do.
**Knowledge** (Systems + Agents + Modules) define what agents KNOW.
**Enforcement** (Hooks + Standards + Methodology) ensure agents DO IT RIGHT.

All three feed into agent files (the output) via the knowledge map
(the navigator) through injection logic (the brain).

---

## PO Decision Points — Consolidated

### D1: Memory Architecture

| Option | What | Pros | Cons |
|--------|------|------|------|
| A | claude-mem SQLite-only mode | 45K stars, proven, 4 MCP search tools, 10x token savings, OpenClaw integration | WSL2 ChromaDB risks (mitigated by SQLite-only), costs Claude tokens for compression |
| B | total-recall | Write gates, correction propagation, tiered storage | 189 stars, less proven |
| C | memsearch | Markdown-first, git-trackable | 1K stars, simpler but less capable |
| D | Built-in .claude/memory/ only | Zero cost, rock solid, git-tracked | No search, 200-line cap, no auto-capture |

**Question:** claude-mem in SQLite-only mode (option A) as primary, with built-in .claude/memory/ as the lightweight complement? Or different combination?

**Source:** analysis-02-plugins §Memory

---

### D2: Methodology Layer

| Option | What | Pros | Cons |
|--------|------|------|------|
| A | Install Superpowers whole | 132K stars, TDD enforcement, 14 proven skills, most starred plugin | Assumes autonomous execution — needs fleet guardrail adaptation |
| B | Cherry-pick 6 methodology skills | brainstorming, TDD, systematic-debugging, verification, writing-plans, subagent-driven | Manual extraction, miss plugin updates |
| C | No ecosystem methodology | Our 5-stage protocol is sufficient | Misses TDD enforcement, brainstorming structure, systematic debugging |

**Question:** Install Superpowers and adapt autonomy model for fleet guardrails? Or cherry-pick the methodology skills?

**Interaction:** Superpowers methodology + our 5-stage protocol + fleet control guardrails = THREE layers. Together they're the most rigorous development workflow in the ecosystem. Separately each has gaps.

**Source:** analysis-02-plugins §Methodology, analysis-03-skills §Methodology

---

### D3: Safety Layer

| Component | What | Stars | Roles | Decision |
|-----------|------|-------|-------|----------|
| safety-net | PreToolUse hook — blocks destructive commands | 1K | ALL | Install on ALL agents? |
| security-guidance | PostToolUse hook — detects insecure code patterns (9 OWASP patterns) | official | ALL (esp DEVSEC, ENG) | Install alongside safety-net? |
| sage (ADR) | Agent Detection and Response — policy-based command/file/web guards | 162 | ALL | Evaluate after safety-net? |
| code-container | Run agents in Docker containers for isolation | 202 | ALL | Consider for fleet security model? |

**Question:** safety-net + security-guidance as the baseline safety layer for ALL agents? Sage and code-container as future evaluation?

**Source:** analysis-02-plugins §Safety, analysis-05-hooks §Structural Prevention

---

### D4: Code Intelligence

| Component | What | Roles | Decision |
|-----------|------|-------|----------|
| pyright-lsp | Continuous Python type checking + diagnostics | ALL Python agents | Install on all agents? |

**Question:** Install pyright-lsp on all agents? Our entire codebase is Python. Zero downside beyond pyright binary installation.

**Source:** analysis-02-plugins §Development Workflow

---

### D5: Security MCP Stack

| Option | What | Cost | Coverage |
|--------|------|------|----------|
| A | Trivy only | Free (open source) | Containers, filesystems, repos, IaC configs |
| B | Trivy + Semgrep | Free | A + code-level vulnerability patterns (30+ languages) |
| C | Trivy + Semgrep + mcp-pypi | Free | B + Python package vulnerability scanning + license audit |
| D | Snyk | Freemium (token) | All-in-one: SAST + SCA + IaC + container + SBOM + AI-BOM (11 tools) |
| E | Trivy + Semgrep + mcp-pypi + Snyk | Mixed | Maximum coverage across all layers |

**Question:** Which security stack for devsecops? Free baseline (B or C) or comprehensive (D or E)?

**Interaction:** These MCP servers connect to Trail of Bits skills (21 security skills from VoltAgent). Together = MCP tools + expert methodology.

**Source:** analysis-01-tools §Security, analysis-03-skills §Security

---

### D6: Testing MCP

| Component | What | Roles | Decision |
|-----------|------|-------|----------|
| pytest-mcp-server | 8 tools: failures, analysis, coverage, debug trace, compare runs | QA, ENG | Install? Our stack is Python. |
| test-runner-mcp | Unified interface for pytest/jest/bats/go/rust | QA, ENG | Install if multi-language? |

**Question:** pytest-mcp for our Python stack? test-runner-mcp if projects expand to other languages?

**Source:** analysis-01-tools §Testing

---

### D7: Plane Integration

| Option | What | Pros | Cons |
|--------|------|------|------|
| A | Keep direct API (plane_sync.py) | Working now, tested, custom logic | Not standard MCP, harder to maintain |
| B | Add Plane MCP alongside direct API | Standard MCP for agents, direct API for brain | Two integration paths to maintain |
| C | Replace direct API with Plane MCP | Standard, single path | Migration effort, may lose custom logic |

**Question:** Add official Plane MCP server alongside existing direct API? Or evaluate replacing?

**Source:** analysis-01-tools §Project Management

---

### D8: GitHub MCP Upgrade

| Option | What |
|--------|------|
| Current | @modelcontextprotocol/server-github (basic) |
| Upgrade | github/github-mcp-server (official, 80+ tools, prompt injection protection, Dependabot, Actions) |

**Question:** Upgrade to GitHub's official 80+ tool MCP server?

**Source:** analysis-01-tools §Filesystem & Source Control

---

### D9: Review Enhancement

| Option | What | Token Cost | Quality |
|--------|------|-----------|---------|
| A | Fleet-ops 7-step review only | 1x | Good (our protocol) |
| B | A + codex adversarial-review | 1x Claude + 1x OpenAI | High (cross-provider) |
| C | A + pr-review-toolkit (5 parallel agents) | 5x | Very high (multi-angle) |
| D | A + claude-octopus (up to 8 models) | Nx | Maximum (multi-model) |
| E | A + native review gate (implement codex pattern locally) | 1x | Good (independent check, no OpenAI cost) |

**Question:** Which review enhancement? Budget-conscious (E) vs maximum quality (C or D)? Or start with our 7-step and add layers later?

**Source:** analysis-02-plugins §Quality & Review

---

### D10: Expert Persona Skills (alirezarezvani)

Fleet-relevant POWERFUL tier skills:

| Skill | Role | What It Adds |
|-------|------|-------------|
| agent-designer | ARCH | Design agent architectures (directly relevant — we're building a fleet) |
| rag-architect | ARCH | Design RAG systems (directly relevant — LightRAG integration) |
| mcp-server-builder | ARCH, ENG | Build MCP servers (relevant — custom fleet tools) |
| pr-review-expert | FLEET-OPS | Deep PR review methodology |
| observability-designer | DEVOPS | Monitoring/alerting design |
| tech-debt-tracker | QA, ACCT | Systematic debt tracking |
| incident-commander | DEVOPS, FLEET-OPS | Incident response leadership |
| skill-security-auditor | DEVSEC | Scan skills for malicious code |
| senior-architect | ARCH | Deep architecture expertise persona |
| playwright-pro (9 sub-skills) | QA | Deep browser testing |

**Question:** Which of these to adopt per role? All of them? Or prioritize the ones directly relevant to fleet building (agent-designer, rag-architect, mcp-server-builder)?

**Source:** analysis-03-skills §Domain Expertise, analysis-02-plugins §claude-skills

---

### D11: Trail of Bits Security Skills

21 security skills from actual security researchers:

| Skill | What |
|-------|------|
| semgrep-rule-creator | Custom SAST rules for our codebase |
| property-based-testing | Generative test approach |
| variant-analysis | Find similar vulnerabilities |
| constant-time-analysis | Timing attack prevention |
| + 17 more | Various security specializations |

**Question:** Install Trail of Bits skills for devsecops? These are the highest quality security skills in the ecosystem — written by real security researchers.

**Source:** analysis-03-skills §Security

---

### D12: HashiCorp Terraform Skills

11 Terraform skills from HashiCorp:

**Question:** Install for devops when IaC expands beyond Docker Compose? Or now for future readiness?

**Source:** analysis-03-skills §DevOps

---

### D13: Template Skills (48)

48 AICP skills share identical boilerplate. Three paths:

| Option | Effort | Quality |
|--------|--------|---------|
| A | Differentiate all 48 | 48h | Highest |
| B | Differentiate top 15, keep rest | 15h | Good |
| C | Let Superpowers methodology replace their function | 0h (if Superpowers adopted) | Different approach |

**Question:** Which path? If Superpowers adopted (D2), its methodology skills cover the HOW that template skills were supposed to provide.

**Source:** analysis-03-skills §Template Skills

---

### D14: Diagram Rendering

| Component | What | Formats |
|-----------|------|---------|
| diagram-bridge-mcp | Render diagrams via Kroki | 10+ (Mermaid, PlantUML, C4, D2, GraphViz, BPMN, etc.) |
| mermaid-mcp | Render Mermaid only | Mermaid → PNG |
| excalidraw-mcp | Programmatic canvas | Hand-drawn style, SVG/PNG export |

**Question:** Any diagram rendering for architect/writer? diagram-bridge covers the most formats. Or is markdown-based Mermaid sufficient without rendering?

**Source:** analysis-01-tools §Design & Diagrams

---

### D15: Additional MCP Servers

| Server | Roles | Question |
|--------|-------|---------|
| Git MCP | ENG, DEVOPS, ARCH | Structured git output vs Bash — worth adding? |
| SQLite MCP | ENG, QA | Agent access to fleet's own data stores? |
| Sequential Thinking | ARCH, PM | Structured reasoning for complex design decisions? |
| Context7 MCP | ENG, ARCH, WRITER | Add MCP server version alongside existing plugin? |
| Memory MCP | FLEET-OPS, ARCH | Lightweight knowledge graph alongside LightRAG? |

**Source:** analysis-01-tools various sections

---

### D16: Hooks Implementation

Tier 1 hooks (structural prevention + trail):

| Hook | What | Priority |
|------|------|----------|
| PreToolUse | Safety gate + stage enforcement + contribution gate | CRITICAL |
| PostToolUse | Trail recording (every tool call → audit event) | HIGH |
| SessionStart | Knowledge map injection + claude-mem load | CRITICAL |
| Stop | Review gate + state save | HIGH |
| StopFailure | Rate limit detection → notify brain | HIGH |

**Question:** Confirm Tier 1 hooks as first implementation? These are the enforcement layer that makes everything else reliable.

**Source:** analysis-05-hooks §Tier 1

---

### D17: Skill Deployment Architecture

How do AICP skills (78) + fleet skills (7) + ecosystem skills get into each agent's workspace?

| Option | How |
|--------|-----|
| A | Symlink from source repos to agent .claude/skills/ |
| B | Copy via IaC script (scripts/deploy-skills.sh) |
| C | Plugin-based (skills inside plugins, installed via /plugin install) |
| D | Hybrid (our skills via symlink, ecosystem via plugin install) |

**Question:** Which deployment model? Hybrid (D) seems natural — our skills are local files, ecosystem skills come as plugins.

**Source:** analysis-03-skills §Deployment

---

## Implementation Order (Dependencies)

Based on the analysis connections, the build order after PO decisions:

```
Phase 1: Safety + Memory (no dependencies)
  ├── Install safety-net on ALL agents
  ├── Install pyright-lsp on ALL Python agents
  ├── Install claude-mem (SQLite-only mode)
  └── Configure security-guidance hook

Phase 2: Methodology + Skills (depends on Phase 1 decisions)
  ├── Install/adapt Superpowers (if D2 decided)
  ├── Deploy fleet skills to agent workspaces
  ├── Deploy ecosystem skills per role (D10, D11, D12)
  └── Differentiate template skills (D13)

Phase 3: MCP Servers (independent of Phase 2)
  ├── Upgrade GitHub MCP (if D8 decided)
  ├── Install security MCP stack (D5)
  ├── Install pytest-mcp (if D6 decided)
  ├── Install Plane MCP (if D7 decided)
  └── Install additional MCPs (D15)

Phase 4: Hooks Infrastructure (depends on safety-net experience)
  ├── Implement Tier 1 hooks (D16)
  ├── Wire hooks to trail system
  ├── Wire hooks to knowledge map injection
  └── Wire hooks to anti-corruption enforcement

Phase 5: Knowledge Map Content (depends on all above decisions)
  ├── Build system manuals (condensed + minimal)
  ├── Build agent manuals (from fleet-elevation specs)
  ├── Build tool/skill/command manuals
  ├── Build cross-references (_map.yaml)
  ├── Build injection profiles (opus/sonnet/localai/heartbeat)
  └── Build intent-map (situation → what to inject)

Phase 6: Agent Files (depends on ALL above)
  ├── Write CLAUDE.md ×10 (references real tools, skills, commands)
  ├── Write HEARTBEAT.md ×5 (references real workflows)
  ├── Regenerate TOOLS.md ×10 (from map tool manuals)
  ├── Regenerate AGENTS.md ×10 (from map agent manuals)
  └── Validate all against standards
```

**Why this order:** Agent files (Phase 6) reference tools, skills, commands,
plugins, hooks. If we write agent files first, they reference things that
don't exist or aren't configured. If we build the capabilities first
(Phases 1-4), then the knowledge map (Phase 5), then agent files are
written from REAL, verified, documented capabilities.

---

## What Happens After PO Decisions

1. PO reviews each D1-D17 decision point
2. Decisions recorded in this document
3. Roadmap (complete-roadmap.md) updated with concrete milestones from decisions
4. Knowledge map construction begins (manuals, metadata, injection profiles)
5. Agent files written from the completed map
6. Live testing with real agents using real capabilities
