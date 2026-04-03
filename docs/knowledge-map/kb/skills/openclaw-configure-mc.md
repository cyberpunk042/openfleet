# openclaw-configure-mc

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/openclaw-configure-mc/SKILL.md
**Invocation:** /openclaw-configure-mc
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Connect Mission Control to an OpenClaw gateway: verify both running, read config, run setup module, verify registration.

## Assigned Roles

Fleet-ops ESSENTIAL, DevOps ESSENTIAL

## Methodology Stages

work

## Relationships

- DEPENDS ON: openclaw-setup (gateway running)
- CONNECTS TO: openclaw-add-agent (agents registered before MC connects), openclaw-health (verify after configure)
