# System 18: Notifications — Multi-Channel Routing & Cross-References

**Type:** Fleet System
**ID:** S18
**Files:** notification_router.py (~200 lines), cross_refs.py (~200 lines), urls.py (~136 lines)
**Total:** 536 lines
**Tests:** 35+

## What This System Does

Routes fleet events to the right channel at the right priority. Cross-references automatically link related items across ALL surfaces. Notifications are the VISIBILITY layer — when an agent completes a task with a PR, the Plane issue gets the PR link, IRC shows the review request, ntfy pings the PO, board memory records the completion — all automatically.

## 3 Priority Levels

| Level | ntfy Topic | Phone Behavior |
|-------|-----------|---------------|
| INFO | fleet-progress | Silent badge |
| IMPORTANT | fleet-review | Badge + sound |
| URGENT | fleet-alert | Full-screen + sound + Windows toast |

Deduplication: same event_type + source_agent within 300s cooldown suppressed (prevents heartbeat spam).

## IRC Channels (6 designed)

| Channel | Purpose | Status |
|---------|---------|--------|
| #fleet | General fleet activity | EXISTS |
| #alerts | Critical/high severity | EXISTS |
| #reviews | Review requests, approvals | EXISTS |
| #sprint | Sprint milestones | EXISTS |
| #gates | Gate requests and PO decisions | NOT CREATED |
| #contributions | Contribution posts and completions | NOT CREATED |

## Cross-Reference Engine

Pure function `generate_cross_refs(event)` → list of CrossReference actions. 9 event types handled:
- task.completed → Plane comment + IRC #reviews + board memory
- plane.issue_created → board memory + IRC
- github.pr_merged → Plane + IRC
- chat.mention / plane.commented → IRC cross-post
- cycle_started/completed → IRC + board memory
- alert.posted → IRC #alerts
- task.blocked → IRC
- escalation → IRC #alerts + board memory

**EXECUTION GAP:** generate_cross_refs RETURNS references but NO CALLER EXECUTES them. The generator is built, the executor is not.

## Relationships

- CONSUMED BY: S04 event bus (events route through notifications)
- CONSUMED BY: S07 orchestrator (IRC notifications on dispatch, transitions)
- CONNECTS TO: S08 MCP tools (fleet_alert, fleet_escalate, fleet_notify_human)
- CONNECTS TO: ntfy_client.py (push notifications to PO phone)
- CONNECTS TO: irc_client.py (IRC channel notifications)
- CONNECTS TO: urls.py (config-driven URL resolution for cross-references)
- NOT YET IMPLEMENTED: The Lounge web IRC deployment, #gates and #contributions channels, ntfy topic configuration, cross-reference EXECUTION, daily digest generation
