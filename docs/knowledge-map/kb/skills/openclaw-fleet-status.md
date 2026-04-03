# openclaw-fleet-status

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/openclaw-fleet-status/SKILL.md
**Invocation:** /openclaw-fleet-status
**Effort:** low
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Check fleet operational status: run make status, check pending tasks, agent status, recent activity. Read-only — no modifications.

## Assigned Roles

Fleet-ops ESSENTIAL, PM ESSENTIAL

## Methodology Stages

analysis

## Relationships

- DEPENDS ON: openclaw-setup (fleet exists)
- CONNECTS TO: fleet_agent_status tool (similar data via MCP), openclaw-health (infrastructure vs operational status)
