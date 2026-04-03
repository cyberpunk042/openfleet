# openclaw-health

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/openclaw-health/SKILL.md
**Invocation:** /openclaw-health
**Effort:** low (read-only checks, fast)
**Allowed tools:** Read, Bash, Glob, Grep

## Purpose

Comprehensive health check of the OpenClaw ecosystem: gateway, Mission Control backend + frontend, Docker services, registered agents, error logs. Produces a clear summary of what's running, what's not, what needs attention. Read-only — no modifications.

## Process

1. Check OpenClaw gateway: `openclaw status`
2. Check MC backend: `curl http://localhost:8000/health`
3. Check MC frontend: `curl http://localhost:3000`
4. Check Docker services: `docker compose ps`
5. List registered agents: `openclaw agents list`
6. Check for error logs: gateway log, MC backend log
7. Report overall health status

## Output

Clear summary: what's running, what's not, what needs attention. Per-service status.

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| Fleet-ops | ESSENTIAL | Fleet health is fleet-ops core responsibility |
| DevOps | ESSENTIAL | Infrastructure health monitoring |
| ALL | OPTIONAL | Any agent can check fleet health for awareness |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| analysis | Health assessment during heartbeat |
| any | On-demand health check when issues suspected |

## Relationships

- READ-ONLY: no modifications, no events (just checks and reports)
- CHECKS: gateway (port 9400 HTTP, 18789 WS), MC backend (port 8000), MC frontend (port 3000), Docker services, registered agents
- CONNECTS TO: fleet_agent_status tool (agent-level health — this skill is infrastructure-level)
- CONNECTS TO: outage_detector.py (brain's automatic outage detection)
- CONNECTS TO: storm_monitor.py (storm detects gateway duplication, this checks manually)
- CONNECTS TO: §49 canonical deployment specification (ports, services, health checks)
- CONNECTS TO: §50 crisis response playbook (health check is first diagnostic step in every crisis)
- CONNECTS TO: fleet-ops heartbeat (health monitoring is priority 4 in heartbeat protocol)
- CONNECTS TO: DevOps heartbeat (monitor fleet infrastructure every heartbeat)
- VARIANT: openclaw-fleet-status (operational status — tasks, agents, activity — vs this = infrastructure health)
