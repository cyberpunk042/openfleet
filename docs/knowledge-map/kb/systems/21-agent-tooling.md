# System 21: Agent Tooling — Per-Role Specialization via IaC

**Type:** Fleet System (SPECIFICATION — defines what each agent needs)
**ID:** S21
**Files:** skill_enforcement.py (~180 lines) + config/agent-tooling.yaml
**Tests:** Part of validate-agents.sh

## What This System Does

Specifies per-role tool specialization: which MCP servers, plugins, skills, and commands each agent gets. Currently all 10 agents share a generic mcp.json with only the fleet MCP server. The specification defines what each role NEEDS — the gap between specification and deployment is the work.

Config-driven via agent-tooling.yaml. IaC scripts deploy per-agent mcp.json, install plugins, deploy skills.

## 6 Extension Points (from Claude Code)

1. **MCP Servers** — external tool connections (fleet, filesystem, github, playwright, docker, etc.)
2. **Plugins** — capability packages (claude-mem, context7, safety-net, pyright-lsp, superpowers)
3. **Skills** — procedural knowledge (.claude/skills/ — 85 internal + ecosystem)
4. **Hooks** — deterministic lifecycle handlers (PreToolUse, PostToolUse, SessionStart, etc.)
5. **Subagents** — specialized autonomous workers (.claude/agents/)
6. **Agent Teams** — multi-agent collaboration (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS)

## Per-Role Assignments (from agent-tooling.yaml, updated this session)

72 skill assignments across 10 roles. fleet-communicate on ALL agents. Per-role MCP servers (filesystem, github, playwright, docker). Plugins: claude-mem (all), context7 (architect+engineer).

## Tool Enforcement

skill_enforcement.py: required MCP tools per task type. Tasks need fleet_read_context + fleet_task_accept + fleet_commit + fleet_task_complete. Epics MUST create subtasks. Missing tools lower confidence score in approval.

## Relationships

- CONFIGURES: every agent's workspace (MCP, plugins, skills, hooks)
- DEPLOYED BY: scripts/setup-agent-tools.sh (mcp.json), scripts/install-plugins.sh, scripts/deploy-skills.sh
- VALIDATED BY: scripts/validate-agents.sh
- CONNECTS TO: S08 MCP tools (tool enforcement at completion)
- CONNECTS TO: S09 standards (compliance in approval)
- CONNECTS TO: knowledge map (agent manuals reference available tools per role)
- CONNECTS TO: methodology manual (per-stage tool/skill/command recommendations)
