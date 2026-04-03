# pm-changelog

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/pm-changelog/SKILL.md
**Invocation:** /pm-changelog
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Generate human-readable changelog from git history: group commits by features/fixes/breaking changes, link to PRs/issues, append to CHANGELOG.md.

## Assigned Roles

PM RECOMMENDED, Writer RECOMMENDED

## Methodology Stages

work

## Relationships

- DEPENDS ON: None (reads git log)
- CONNECTS TO: fleet_commit (conventional commits enable grouping), release-cycle composite (changelog before deploy)
