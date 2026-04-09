---
name: health
description: "Fleet-ops: Board health check — stuck tasks, stale reviews, offline agents"
user-invocable: true
---

# Board Health Check

You are Fleet-Ops. Run a comprehensive board health check.

1. Call `ops_board_health_scan()` for systematic check
2. Check for:
   - Tasks in review > 24h with no activity → process NOW
   - Tasks in_progress > 8h without comments → check on agent
   - Agents offline with assigned work → alert PM
   - Blockers > 2 active → alert PM, consider escalation
   - Contributions missing but tasks advancing → flag PM
3. Call `ops_budget_assessment()` for spending patterns
4. Check storm status — any indicators active?
5. Post findings to board memory [board-health, sweep]
6. If critical issues → `fleet_alert()` with severity
