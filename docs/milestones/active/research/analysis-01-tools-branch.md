# Analysis 01 — Tools Branch of the Knowledge Map

**Date:** 2026-04-02
**Status:** ANALYSIS — conclusions from research groups 01-04
**Purpose:** Define exactly which MCP servers populate the Tools Manual branch

> Research gathered the raw data. This analysis draws conclusions.
> Conclusions define what goes into agent-tooling.yaml, what gets
> documented in the Tools Manual, and what milestones follow.

---

## Current State

We have configured 5 MCP server types in agent-tooling.yaml:
- fleet (29 tools — our custom MCP server)
- filesystem (@modelcontextprotocol/server-filesystem)
- github (@modelcontextprotocol/server-github)
- playwright (@playwright/mcp@latest)
- docker (@modelcontextprotocol/server-docker)

Research cataloged 38 relevant servers. Analysis question:
**Which of the remaining 33 do we adopt, for which roles, at what priority?**

---

## Analysis by Category

### Category 1: Already Configured (5 servers) — NO ACTION

| Server | Roles | Status |
|--------|-------|--------|
| fleet | ALL | Configured, 29 tools |
| filesystem | ENG, QA, WRITER, DEVOPS, DEVSEC, UX, ACCT | Configured |
| github | ARCH, ENG, DEVOPS, FLEET-OPS, PM, WRITER | Configured |
| playwright | ENG, QA, UX | Configured |
| docker | DEVOPS, DEVSEC | Configured |

### Category 2: ADOPT — High value, low friction, aligns with our stack

| Server | Package | Why Adopt | Roles | Priority | Dependencies |
|--------|---------|-----------|-------|----------|-------------|
| **Context7** | `@upstash/context7-mcp` | 47K stars. Library/framework docs prevent hallucinated APIs. Already have plugin — this is the MCP server version. | ENG, ARCH, WRITER | HIGH | None (optional API key) |
| **Pytest MCP** | `pytest-mcp-server` (pip) | Our stack is Python. 8 tools for failure analysis, coverage, debug trace. Direct value for QA and engineer. | QA, ENG | HIGH | Python, pytest |
| **Plane MCP** | `makeplane/plane-mcp-server` | Official Plane MCP. We self-host Plane (DSPD). Could replace direct API calls with standard MCP integration. | PM, FLEET-OPS | HIGH | Plane API key |
| **Trivy** | `trivy` + MCP plugin | Open source vulnerability scanner. Free. Containers, filesystems, repos, IaC configs. No token needed. | DEVSEC, DEVOPS | HIGH | trivy binary |
| **Git MCP** | `mcp-server-git` (pip) | Git operations as MCP tools. Agents currently use Bash for git. MCP gives structured output. | ENG, DEVOPS, ARCH | MEDIUM | Python, git |
| **SQLite MCP** | `mcp-server-sqlite` (pip) | We use SQLite for RAG, event store, various data. Read/write + schema inspection. | ENG, QA | MEDIUM | Python |

### Category 3: EVALUATE — Potentially valuable, needs PO decision

| Server | Package | Why Evaluate | Roles | Consideration |
|--------|---------|-------------|-------|--------------|
| **Semgrep** | `semgrep` (pip) | SAST across 30+ languages. Free tier. But: do we need it alongside Trivy? Or is Trivy enough for our scope? | DEVSEC | Trivy covers containers+deps. Semgrep covers CODE patterns. Different layers — both may be needed. |
| **Snyk** | `snyk` CLI | Most comprehensive security MCP (11 tools). But: requires SNYK_TOKEN (freemium). Overlaps with Trivy. | DEVSEC | If budget allows, Snyk is the best. If free-only, Trivy + Semgrep covers the same ground. |
| **ESLint MCP** | `@eslint/mcp` | Our fleet is Python, not JS. Only useful if agents work on frontend/Node projects. | ENG, QA | Only if we have JS/TS projects in the fleet. |
| **GitHub Actions MCP** | `github-actions-mcp-server` | CI/CD management. But: GitHub MCP server (already configured) includes Actions. Redundant? | DEVOPS | Check if github/github-mcp-server already covers Actions. If yes, skip. |
| **Brave Search** | `@modelcontextprotocol/server-brave-search` | Web search for research. But: Claude Code has built-in WebSearch tool. Redundant? | ARCH, WRITER | Built-in WebSearch may be sufficient. Brave adds local search. |
| **Sequential Thinking** | `@modelcontextprotocol/server-sequential-thinking` | Structured step-by-step reasoning. 72K weekly downloads. But: does it add value when agents already have methodology stages? | ARCH, PM | Could help architect with complex design decisions. Evaluate if methodology stages already cover this. |
| **Diagram Bridge** | `diagram-bridge-mcp` | Generate diagrams (Mermaid, PlantUML, C4, etc.). But: agents can already write Mermaid in markdown. | ARCH, WRITER | Value is in rendering, not syntax. If we need diagram images, adopt. If markdown diagrams are enough, skip. |

### Category 4: DEFER — Valuable but not needed now

| Server | Why Defer |
|--------|----------|
| **kubectl** (253 tools) | No K8s cluster yet. Adopt when infrastructure scales. |
| **K8s Secure** | Same — no K8s. |
| **Terraform** | No Terraform in current stack. Adopt when infra-as-code expands. |
| **Redis MCP** | No Redis in fleet stack (OCMC uses PostgreSQL). |
| **PostgreSQL MCP** | Potential for direct OCMC DB queries. But: agents should use MC API, not direct DB. Defer. |
| **DBHub** | Multi-DB — defer until we have multiple databases. |
| **Puppeteer** | Playwright already configured. Redundant. |
| **Tavily** | Search API — requires paid key. WebSearch built-in is sufficient. |
| **Fetch MCP** | Claude Code has built-in WebFetch. Redundant. |
| **Notion/Confluence/Jira/Linear** | We use Plane, not these tools. |
| **Slack** | We use IRC (miniircd) + ntfy. No Slack. |
| **GitLab** | We use GitHub. No GitLab. |

### Category 5: SKIP — Not relevant to our stack

| Server | Why Skip |
|--------|---------|
| **DevSecOps-MCP aggregator** | Aggregates tools we'd install individually. Adds complexity without value over individual tools. |

---

## Conclusions: Tools Manual Content

The Tools Manual branch of the knowledge map should document:

### Tier 1: Core (always available, every agent gets fleet MCP)

| Server | Agents | Tools Count |
|--------|--------|------------|
| fleet MCP | ALL | 29 |
| filesystem | 8 of 10 | 8 |
| github | 7 of 10 | 80+ |

### Tier 2: Role-Specific (configured per role)

| Server | Agents | Tools Count |
|--------|--------|------------|
| playwright | ENG, QA, UX | 6 |
| docker | DEVOPS, DEVSEC | 25 |
| Context7 | ENG, ARCH, WRITER | 2 |
| pytest-mcp | QA, ENG | 8 |
| Plane MCP | PM, FLEET-OPS | 6+ |
| Trivy | DEVSEC, DEVOPS | 5 |

### Tier 3: Evaluated (pending PO decision)

| Server | Agents | Decision Needed |
|--------|--------|----------------|
| Semgrep | DEVSEC | Alongside Trivy or redundant? |
| Snyk | DEVSEC | Budget for token or free-only? |
| Git MCP | ENG, DEVOPS, ARCH | Value over built-in Bash git? |
| SQLite MCP | ENG, QA | Value for RAG/event DB access? |
| Sequential Thinking | ARCH, PM | Methodology stages sufficient? |

### Tier 4: Deferred (adopt when stack grows)

kubectl, Terraform, Redis, PostgreSQL, K8s, Notion, Confluence, Jira, Linear, Slack, GitLab

---

## What This Means for agent-tooling.yaml

**Immediate updates (Tier 2 adoptions):**
1. Add Context7 MCP server to ENG, ARCH, WRITER (in addition to plugin)
2. Add pytest-mcp-server to QA, ENG
3. Add Plane MCP to PM, FLEET-OPS
4. Add Trivy to DEVSEC, DEVOPS

**After PO decisions (Tier 3):**
5. Possibly add Semgrep to DEVSEC
6. Possibly add Snyk to DEVSEC
7. Possibly add Git MCP to ENG, DEVOPS, ARCH
8. Possibly add SQLite MCP to ENG, QA

---

## What This Means for the Map

Each adopted server becomes a node in the Tools Manual:
```
Tool Manuals/
├── fleet-mcp/
│   ├── _map.yaml (29 tools, ALL agents, every stage)
│   └── full.md (complete tool reference with chains from fleet-elevation/24)
├── filesystem/
│   ├── _map.yaml (8 tools, 8 agents, work stage primarily)
│   └── full.md
├── github/
│   ├── _map.yaml (80+ tools, 7 agents, work+review stages)
│   └── full.md
├── playwright/
│   ├── _map.yaml (6 tools, ENG+QA+UX, work+investigation stages)
│   └── full.md
├── docker/
│   ├── _map.yaml (25 tools, DEVOPS+DEVSEC, work stage)
│   └── full.md
├── context7/
│   ├── _map.yaml (2 tools, ENG+ARCH+WRITER, investigation+work stages)
│   └── full.md
├── pytest-mcp/
│   ├── _map.yaml (8 tools, QA+ENG, work stage)
│   └── full.md
├── plane-mcp/
│   ├── _map.yaml (6+ tools, PM+FLEET-OPS, any stage)
│   └── full.md
└── trivy/
    ├── _map.yaml (5 tools, DEVSEC+DEVOPS, investigation+work stages)
    └── full.md
```

---

## PO Decision Points

1. **Context7:** MCP server AND plugin, or just plugin? (MCP server gives tool access, plugin gives context injection — they're different)
2. **Plane MCP:** Replace our direct API calls with MCP server, or use alongside?
3. **Trivy vs Semgrep vs Snyk:** Which security stack? Free-only (Trivy+Semgrep) or premium (Snyk)?
4. **Git MCP:** Worth adding when agents already have Bash + git?
5. **SQLite MCP:** Useful for agent access to fleet's own SQLite stores?
