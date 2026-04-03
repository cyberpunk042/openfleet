# openclaw-setup

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/openclaw-setup/SKILL.md
**Invocation:** /openclaw-setup
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Set up OpenClaw in a project workspace. Install if missing, run setup.sh or openclaw onboard, configure gateway (bind mode, auth, control UI), verify openclaw status healthy, start Mission Control docker-compose, verify all components running. Back up before overwriting config. Script all changes.

## Assigned Roles

Fleet-ops ESSENTIAL, DevOps ESSENTIAL

## Methodology Stages

work

## Relationships

- DEPENDS ON: None (first fleet setup step)
- CONNECTS TO: openclaw-add-agent (add agents after setup), openclaw-configure-mc (connect MC after setup), openclaw-health (verify after setup), §49 deployment spec (ports, services, startup sequence)
