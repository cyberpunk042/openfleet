# foundation-deps

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/foundation-deps/SKILL.md
**Invocation:** /foundation-deps
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Install and configure all project dependencies. Pin versions, separate dev/test from production, resolve conflicts, set up lock files, create virtual environment. Smoke test after install.

## Assigned Roles

Engineer ESSENTIAL, DevOps RECOMMENDED

## Methodology Stages

work

## Relationships

- DEPENDS ON: scaffold (project must exist), foundation-config (config after deps)
- CONNECTS TO: Context7 MCP (check library docs), package-registry MCP (search packages), mcp-pypi (Python dep security audit)
