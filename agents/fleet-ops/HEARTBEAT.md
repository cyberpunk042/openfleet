# HEARTBEAT.md — Fleet Ops Governance

On each heartbeat, perform governance checks. Use fleet tools when available.

## Tasks

### 1. Board Health Check

Call `fleet_read_context()` to get board state. Check:
- Tasks in inbox > 1 hour without assignment → post alert
- Tasks in review > 24 hours without activity → post alert
- Pending approvals > 48 hours → escalate to IRC #alerts

If all clear: HEARTBEAT_OK

### 2. Daily Digest (once per day)

Check board memory for today's digest (tag: `daily`).
If none exists, generate and post a digest with:
- Task counts by status
- Active work list
- Pending reviews with PR URLs
- Agent health (online/offline)

Post to board memory with tags [report, digest, daily].

### 3. Quality Spot Check (every 3rd heartbeat)

Check recent task completions for:
- Structured comment format (## headers present?)
- PR URL in custom fields (review tasks)
- Conventional commit format (in worktrees)

Post findings only if violations found.

## Rules

- Keep responses SHORT
- Only alert if something is wrong
- If everything is fine: HEARTBEAT_OK
- Use fleet_alert for issues, fleet_read_context for state
- Do NOT create tasks on heartbeat — only monitor and alert