# ops-maintenance

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/ops-maintenance/SKILL.md
**Invocation:** /ops-maintenance
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Routine maintenance: dependency security patches, security audits, log/artifact cleanup, certificate expiry checks, secret rotation, documentation updates.

## Assigned Roles

DevOps RECOMMENDED

## Methodology Stages

work

## Relationships

- DEPENDS ON: ops-deploy (service running)
- CONNECTS TO: ops-backup (backup before maintenance), config-secrets (secret rotation), mcp-pypi (dependency audit)
