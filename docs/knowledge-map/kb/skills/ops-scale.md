# ops-scale

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/ops-scale/SKILL.md
**Invocation:** /ops-scale
**Effort:** medium
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Runtime scaling: assess current load (CPU, memory, request rate), determine scaling action, execute changes, monitor stability, update autoscaling rules.

## Assigned Roles

DevOps OPTIONAL

## Methodology Stages

work

## Relationships

- DEPENDS ON: ops-deploy (service must be deployed)
- CONNECTS TO: infra-monitoring (load metrics), kubectl MCP (K8s scaling)
