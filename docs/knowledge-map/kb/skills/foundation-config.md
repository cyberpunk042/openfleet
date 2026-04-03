# foundation-config

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/foundation-config/SKILL.md
**Invocation:** /foundation-config
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Set up config management: .env.example with all vars, config loader with env var fallbacks, multi-environment support (dev/staging/prod), config validation at startup, typed config objects. Never commit secrets. Every option has default or explicit error.

## Assigned Roles

Engineer ESSENTIAL, DevOps ESSENTIAL

## Methodology Stages

work

## Relationships

- DEPENDS ON: foundation-deps (dependencies first)
- CONNECTS TO: config-secrets skill (secret management), fleet config loader (config_loader.py), IaC principle (config in git)
