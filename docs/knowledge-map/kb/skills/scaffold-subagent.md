# scaffold-subagent

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/scaffold-subagent/SKILL.md
**Invocation:** /scaffold-subagent
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Create a new agent inside a fleet project: agent directory, agent.yaml, CLAUDE.md, SOUL.md, IDENTITY.md, source stubs, tests, fleet manifest registration.

## Assigned Roles

Fleet-ops ESSENTIAL, Architect RECOMMENDED

## Methodology Stages

work

## Relationships

- DEPENDS ON: openclaw-setup (fleet must exist)
- CONNECTS TO: openclaw-add-agent (register in gateway), agent-yaml-standard (agent.yaml fields), identity-soul-standard (IDENTITY+SOUL format)
