# openclaw-add-agent

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/openclaw-add-agent/SKILL.md
**Invocation:** /openclaw-add-agent
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Add a new agent to an OpenClaw deployment: create agent directory with agent.yaml, CLAUDE.md, SOUL.md, register with openclaw agents add.

## Assigned Roles

Fleet-ops ESSENTIAL

## Methodology Stages

work

## Relationships

- DEPENDS ON: openclaw-setup (OpenClaw must be running)
- CONNECTS TO: scaffold-subagent (creates the files), openclaw-configure-mc (agent needs MC connection)
