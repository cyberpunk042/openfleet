# /loop

**Type:** Claude Code Built-In Skill Command
**Category:** Bundled Skills (Automation)
**Available to:** DevOps (primary), Fleet-ops, PM

## What It Actually Does

Runs a prompt repeatedly on a schedule, default every 10 minutes. Creates a persistent loop that executes the given instruction, checks the result, and repeats. Think of it as an agent-level cron — scheduled task execution within a Claude Code session.

Usage: `/loop [interval] <prompt>`
Examples:
- `/loop 5m check if deployment is healthy`
- `/loop 10m check sprint progress and report blockers`
- `/loop check docker container status` (default 10m)

The loop continues until explicitly stopped or the session ends.

## When Fleet Agents Should Use It

**Deployment monitoring (DevOps):** After ops-deploy, run `/loop 5m check deployment health and report any errors`. Watches the deployment automatically, alerts if something goes wrong.

**Build/CI watching (DevOps):** After triggering a CI pipeline, `/loop 2m check GitHub Actions workflow status`. Waits for completion without manual polling.

**Sprint tracking (PM):** During active sprint, `/loop 30m check sprint progress — completed tasks, blockers, velocity`. Periodic awareness without manual checks.

**Health monitoring (Fleet-ops):** `/loop 15m run openclaw-health and report any unhealthy services`. Continuous fleet health awareness.

## Practical Considerations

- Loop runs WITHIN the session — consumes context with each iteration
- Each iteration is a full prompt→response cycle (costs tokens)
- Long loops + many iterations = context fills up → need /compact
- Loop stops when session ends (not persistent across sessions)
- For persistent scheduling, use CronCreate tool or gateway CRONs instead

## Relationships

- CONNECTS TO: ops-deploy skill (monitor after deployment)
- CONNECTS TO: openclaw-health skill (periodic health checks)
- CONNECTS TO: fleet-sprint skill (sprint progress tracking)
- CONNECTS TO: /compact (context fills during long loops — compact between iterations)
- CONNECTS TO: /context (check context usage during loop)
- DIFFERENT FROM: gateway CRONs (CRONs are persistent, survive session end; /loop is session-only)
- DIFFERENT FROM: CronCreate tool (creates persistent scheduled tasks; /loop is ephemeral)
- CONNECTS TO: heartbeat concept (agent heartbeat IS a loop — gateway CRON fires, agent checks, reports)
- CONNECTS TO: session_manager.py (long loops near rate limit rollover need awareness)
