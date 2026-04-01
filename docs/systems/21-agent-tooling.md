# Agent Tooling — Per-Role Specialization via IaC

> **Every agent is a top-tier expert. Top-tier experts have specialized tools.**
>
> Currently: all 10 agents use the same template mcp.json with only
> the fleet MCP server. No per-agent tools. No per-role skills.
> 19 generic skills configured, none role-specific. 0 of 1000+ available
> MCP servers deployed. The ecosystem gap between what's available and
> what's deployed is massive.
>
> This document specifies what each agent NEEDS — MCP servers, plugins,
> skills, configurations — and how to deploy it via IaC.

---

## 1. Current State — Everyone Gets the Same Template

```
agents/_template/mcp.json:
  mcpServers:
    fleet:                    ← the ONLY MCP server
      command: python -m fleet.mcp.server
      env: FLEET_DIR, FLEET_AGENT, ...

Result: every agent has exactly 1 MCP server (fleet tools).
  No Playwright. No filesystem. No Docker. No database.
  No security scanners. No accessibility checkers.
  No documentation generators. No dependency analyzers.

Per-agent mcp.json: NONE (0 of 10 agents have their own)
Per-agent skills: NONE beyond gateway-wide 19 generic skills
Per-agent plugins: NONE beyond codex-plugin-cc (gateway-wide)
```

---

## 2. What Each Agent Needs

### 2.1 Devsecops Expert (Cyberpunk-Zero)

**Primary domain:** Security. CVE detection. Dependency auditing. Secret scanning.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read/scan files for secrets, configs | MCP registry |
| MCP | **docker** | Container security inspection | MCP registry |
| Plugin | **codex-plugin-cc** | Adversarial security review | Already installed |
| Skill | **security-audit** | Structured security assessment | Custom or OpenClaw registry |
| Skill | **dependency-scan** | CVE database lookup | Custom |
| Config | **npm audit** / **pip audit** | Dependency vulnerability check | System tools |
| Config | **.codex/instructions.md** | Security-focused review prompts | Already created |

### 2.2 Architect

**Primary domain:** System design. Pattern selection. Complexity assessment.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Explore codebase structure, read files | MCP registry |
| MCP | **github** | Check existing PRs, branch structure | MCP registry |
| Plugin | **Context7** | Up-to-date library/framework documentation | Plugin marketplace |
| Skill | **architecture-propose** | Structured architecture documents | Custom (already in skill library) |
| Skill | **architecture-review** | Design review framework | Custom (already in skill library) |
| Config | WebSearch/WebFetch | Research frameworks, patterns, options | Claude built-in |

### 2.3 Software Engineer

**Primary domain:** Implementation. Testing. Code quality.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read/write code files | MCP registry |
| MCP | **Playwright** | Browser automation for UI testing | MCP registry |
| MCP | **github** | PR management, branch operations | MCP registry |
| Plugin | **codex-plugin-cc** | Code review (non-adversarial) | Already installed |
| Skill | **feature-implement** | Feature implementation framework | Custom (already in skill library) |
| Skill | **debug** | Debugging workflow | Claude built-in |
| Config | pytest, ruff | Test runner, linter access | System tools |

### 2.4 QA Engineer

**Primary domain:** Testing. Validation. Coverage analysis.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read test files, coverage reports | MCP registry |
| MCP | **Playwright** | End-to-end UI testing | MCP registry |
| Skill | **quality-coverage** | Coverage analysis framework | Custom (already in skill library) |
| Skill | **quality-audit** | Quality audit checklist | Custom (already in skill library) |
| Config | pytest --cov | Coverage measurement | System tools |
| Config | Test framework awareness | pytest fixtures, conftest patterns | In CLAUDE.md |

### 2.5 DevOps

**Primary domain:** Infrastructure. CI/CD. Docker. Monitoring.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **docker** | Container management, image inspection | MCP registry |
| MCP | **filesystem** | Read/write configs, scripts, Makefiles | MCP registry |
| MCP | **github** | CI/CD pipeline management | MCP registry |
| Skill | **foundation-docker** | Dockerfile/compose generation | Custom (already in skill library) |
| Skill | **foundation-ci** | CI pipeline generation | Custom (already in skill library) |
| Skill | **ops-deploy** | Deployment procedures | Custom (already in skill library) |
| Config | docker compose, make | Infrastructure tool access | System tools |

### 2.6 Technical Writer

**Primary domain:** Documentation. API docs. Guides. Changelogs.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read/write documentation files | MCP registry |
| MCP | **github** | Check existing docs, PRs | MCP registry |
| Plugin | **Claude-Mem** | Cross-session memory for doc consistency | Plugin marketplace |
| Skill | **pm-changelog** | Changelog generation from git history | Custom (already in skill library) |
| Skill | **feature-document** | Documentation framework | Custom (already in skill library) |
| Config | Plane API access | Update Plane pages automatically | Via fleet MCP tools |

### 2.7 UX Designer

**Primary domain:** Interface design. Accessibility. User flows.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read UI code, component files | MCP registry |
| MCP | **Playwright** | Visual testing, interaction verification | MCP registry |
| Skill | **quality-accessibility** | Accessibility audit framework | Custom (already in skill library) |
| Config | ARIA standards awareness | Accessibility rules | In CLAUDE.md |
| Config | Component library reference | Radix, shadcn patterns | In CLAUDE.md or Context7 |

### 2.8 Project Manager

**Primary domain:** Task management. Sprint planning. Agent coordination.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **github** | Monitor PRs across projects | MCP registry |
| Skill | **pm-plan** | Sprint planning framework | Custom (already in skill library) |
| Skill | **pm-status-report** | Status report generation | Custom (already in skill library) |
| Skill | **pm-retrospective** | Retrospective framework | Custom (already in skill library) |
| Config | Plane sprint data | Pre-embedded in heartbeat context | Via orchestrator |

### 2.9 Fleet-Ops

**Primary domain:** Quality governance. Approval processing. Board health.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **github** | PR review, CI status | MCP registry |
| Skill | **quality-audit** | Quality audit checklist | Custom (already in skill library) |
| Skill | **pm-assess** | Project state assessment | Custom (already in skill library) |
| Config | Board memory search | Tagged query for compliance | Via fleet MCP tools |

### 2.10 Accountability Generator

**Primary domain:** Evidence systems. Compliance. Governance reporting.

| Type | Tool | Purpose | Source |
|------|------|---------|--------|
| MCP | **filesystem** | Read evidence files, build chains | MCP registry |
| Skill | **quality-audit** | Audit framework | Custom (already in skill library) |
| Config | NNRT project access | Narrative transformation pipeline | Project-specific |

---

## 3. IaC Implementation

### 3.1 Per-Agent mcp.json

Each agent gets its own `agents/{name}/mcp.json` with role-specific servers:

```json
// agents/devsecops-expert/mcp.json
{
  "mcpServers": {
    "fleet": {
      "command": "{{FLEET_VENV}}/bin/python",
      "args": ["-m", "fleet.mcp.server"],
      "env": { "FLEET_DIR": "{{FLEET_DIR}}", "FLEET_AGENT": "devsecops-expert" }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "{{WORKSPACE}}"]
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    }
  }
}
```

### 3.2 Agent Setup Script

```bash
# scripts/setup-agent-tools.sh <agent-name>
# Installs role-specific MCP servers, plugins, and skills for one agent.
# Reads from config/agent-tooling.yaml for the spec.
# Idempotent: safe to re-run.

# 1. Generate per-agent mcp.json from template + role config
# 2. Install required MCP server packages (npm/npx)
# 3. Install role-specific plugins
# 4. Configure role-specific skills
# 5. Verify: agent can access all configured tools
```

### 3.3 Agent Tooling Config

```yaml
# config/agent-tooling.yaml
agents:
  devsecops-expert:
    mcp_servers:
      - name: filesystem
        package: "@modelcontextprotocol/server-filesystem"
        args: ["{{WORKSPACE}}"]
      - name: docker
        package: "@modelcontextprotocol/server-docker"
    plugins:
      - codex-plugin-cc  # already installed
    skills:
      - security-audit
      - dependency-scan
    system_tools:
      - npm audit
      - pip audit

  architect:
    mcp_servers:
      - name: filesystem
        package: "@modelcontextprotocol/server-filesystem"
        args: ["{{WORKSPACE}}"]
      - name: github
        package: "@modelcontextprotocol/server-github"
    plugins:
      - context7
    skills:
      - architecture-propose
      - architecture-review

  # ... (all 10 agents)
```

### 3.4 Makefile Integration

```makefile
agent-setup:
	bash scripts/setup-agent-tools.sh $(AGENT)

agent-setup-all:
	@for agent in architect software-engineer qa-engineer devops \
	              devsecops-expert fleet-ops project-manager \
	              technical-writer ux-designer accountability-generator; do \
	    bash scripts/setup-agent-tools.sh $$agent; \
	done
```

---

## 4. How This Connects to Everything Else

### 4.1 Agent Files (fleet-elevation/02)

```
agents/{name}/
├── agent.yaml       ← capabilities list matches tool assignments
├── CLAUDE.md        ← role-specific rules reference available tools
├── HEARTBEAT.md     ← action protocol uses role-specific tools
├── TOOLS.md         ← GENERATED: chain-aware reference of ALL available tools
│                       (fleet tools + role MCP servers + skills)
├── mcp.json         ← ROLE-SPECIFIC: fleet + role MCP servers
└── context/         ← pre-embedded data references tool capabilities
```

TOOLS.md becomes critical — it's not just the 25 fleet tools but
ALSO the role-specific MCP servers and skills. The agent needs
chain-aware documentation: "calling filesystem.read_file returns
the content; calling fleet_artifact_update with that content triggers
transpose → Plane HTML → completeness check."

### 4.2 Methodology Stages + Tools

Different stages need different tools:

```
conversation: WebSearch (research), fleet_chat (communicate)
analysis: filesystem (read code), fleet_artifact_create (analysis doc)
investigation: WebSearch (research options), Context7 (framework docs)
reasoning: fleet_artifact_create (plan), fleet_task_create (subtasks)
work: filesystem (write code), fleet_commit, Playwright (test UI),
      Docker (infra), fleet_task_complete
```

Stage instructions in CLAUDE.md should reference which tools are
AVAILABLE and APPROPRIATE for each stage.

### 4.3 Contribution Flow + Tools

When architect contributes design_input to an engineer's task:
- Architect uses: filesystem (explore code), fleet_contribute (post input)
- Engineer receives: design input in pre-embedded context
- Engineer uses: filesystem (implement), fleet_commit (code)

The tools must be available for the contribution flow to work.
Without filesystem MCP, the architect can't explore the codebase
to produce design input.

### 4.4 Challenge Types + Tools

- Automated challenge: no tools needed (pattern-based, deterministic)
- Agent challenge: challenger needs filesystem (read diff), fleet_contribute
- Cross-model challenge: needs LocalAI API (different model)
- Scenario challenge: needs Playwright (UI bugs), Docker (infra bugs)

### 4.5 Monitoring + Traceability

Every tool call should be:
- Recorded in labor stamp (tools_called field)
- Tracked by skill enforcement (required tools per task type)
- Visible in event bus (tool call events)
- Auditable by accountability generator

---

## 5. Ecosystem to Evaluate

### 5.1 MCP Servers (from 1000+ available)

Priority evaluation list:

| Server | Agents | Priority | Why |
|--------|--------|----------|-----|
| **filesystem** | All workers | HIGH | Read/write code files — fundamental |
| **github** | Engineer, DevOps, Architect, Fleet-ops | HIGH | PR management, CI status |
| **Playwright** | Engineer, QA, UX | HIGH | Browser automation, UI testing |
| **docker** | DevOps, DevSecOps | HIGH | Container management |
| **postgres** | Engineer, DevOps | MEDIUM | Database access (if fleet uses DB) |
| **slack** | Fleet-ops | MEDIUM | External communication (if integrated) |
| **linear/jira** | PM | LOW | External PM tools (Plane is primary) |

### 5.2 Plugins (from 9000+ available)

| Plugin | Agents | Priority | Why |
|--------|--------|----------|-----|
| **codex-plugin-cc** | All (adversarial review) | DONE | Already installed |
| **Claude-Mem** | All | HIGH | Cross-session semantic memory |
| **Context7** | Architect, Engineer | HIGH | Library/framework docs |
| **connect-apps** | Fleet-ops, PM | MEDIUM | 500+ SaaS integrations |
| **Local-Review** | QA, Fleet-ops | MEDIUM | Parallel diff reviews |

### 5.3 Skills (from 5400+ in OpenClaw + custom)

Already in skill library (need per-agent assignment):
- architecture-propose, architecture-review
- feature-implement, feature-review, feature-test, feature-document
- quality-coverage, quality-audit, quality-accessibility
- foundation-docker, foundation-ci, foundation-testing
- pm-plan, pm-changelog, pm-status-report, pm-retrospective
- ops-deploy, ops-incident, ops-maintenance
- security-related (need to create or find)

### 5.4 Cost Optimization

| Mechanism | Savings | Agents | Status |
|-----------|---------|--------|--------|
| Prompt caching | 90% | All | NOT enabled |
| Batch API | 50% | Non-urgent work | NOT used |
| Claude-Mem | Reduces re-learning | All | NOT installed |
| LocalAI RAG | 100% on knowledge queries | All | NOT connected |

---

## 6. Design Decisions

### Why per-agent, not gateway-wide?

Gateway-wide tools are available to ALL agents. But not every agent
should use every tool. DevSecOps shouldn't use Playwright. UX shouldn't
use Docker. Per-agent mcp.json ensures each agent has exactly the tools
they need — no more, no less. Reduces context pollution and prevents
inappropriate tool use.

### Why IaC, not manual install?

PO requirement: "it will be proper IaC with proper configs and scripts."
`make agent-setup devsecops-expert` must install everything that agent
needs. No manual npm installs. No manual config edits. Reproducible
from scratch.

### Why config-driven (agent-tooling.yaml)?

The PO might decide architect needs a new MCP server next week.
Changing a YAML line and running `make agent-setup architect` is
faster and safer than modifying scripts. Config drives behavior.

### Why connect tools to methodology stages?

A tool is only useful in the right context. filesystem.read_file
during conversation stage is wrong — the agent should be ASKING
questions, not reading code. Connecting tools to stages via CLAUDE.md
instructions guides agents to use the right tool at the right time.

---

## 7. What's Needed

### Immediate (Config Only)

1. Create `config/agent-tooling.yaml` with per-agent specs
2. Create `scripts/setup-agent-tools.sh` to deploy per-agent mcp.json
3. Add `make agent-setup` and `make agent-setup-all` targets
4. Generate per-agent mcp.json from template + config
5. Install priority MCP servers: filesystem, github, Playwright, docker

### Medium-Term (Evaluation)

6. Evaluate Claude-Mem plugin for cross-session memory
7. Evaluate Context7 plugin for library documentation
8. Evaluate OpenClaw skills registry for fleet-relevant skills
9. Enable prompt caching (90% savings, API parameter)
10. Wire AICP RAG into fleet agent context

### Strategic

11. TOOLS.md generation per agent (chain-aware, referencing ALL tools)
12. Stage-aware tool availability guidance in CLAUDE.md
13. Tool usage tracking in labor stamps and analytics

---

## 8. Test Coverage

This is configuration, not code. Testing means:
- `make agent-setup-all` succeeds from clean state
- Each agent's mcp.json is valid JSON with expected servers
- Each MCP server responds to tool list query
- Skill assignments match agent capabilities in agent.yaml
