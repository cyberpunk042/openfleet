# StopFailure

**Type:** Claude Code Hook (lifecycle event)
**Category:** Error Handling (fires when a turn ends from API error)
**Handler types:** command, http, prompt, agent
**Can block:** NO — the failure already happened
**Matcher:** `rate_limit`, `authentication_failed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, `unknown`

## What It Actually Does

Fires when Claude's turn ends NOT because Claude chose to stop, but because an API error occurred — rate limit hit, auth failure, server error, billing issue, or max output tokens exceeded. The handler can detect WHICH error type and take appropriate fleet-level action.

This is the fleet's ERROR DETECTION PIPELINE. When an agent hits a rate limit, the fleet needs to know — not just the agent's session.

## Handler Input

```json
{
  "hook_event_name": "StopFailure",
  "session_id": "...",
  "agent_name": "software-engineer",
  "error_type": "rate_limit",
  "error_message": "Rate limit exceeded. Try again in 5 minutes."
}
```

## Fleet Use Cases

### Rate Limit Detection → Notify Brain

```
StopFailure fires with error_type="rate_limit"
├── Write signal file: state/rate_limit_signal.json
│   └── {agent: "software-engineer", time: "...", window: "5h"}
├── Orchestrator reads signal at next cycle
│   ├── storm_monitor: report_indicator("fast_climb")
│   ├── budget_monitor: update rate limit position
│   └── Dispatch paused if threshold exceeded
├── IRC: "[alert] Rate limit hit by software-engineer"
└── ntfy to PO (if critical)
```

Without this hook, rate limits are invisible to the fleet. The agent's session fails silently. The orchestrator doesn't know. Other agents keep consuming quota. With this hook, rate limits become fleet-wide signals.

### Auth Failure → Alert for Human

```
StopFailure fires with error_type="authentication_failed"
├── Write alert to IRC #alerts
├── ntfy to PO: "Auth failure for {agent} — token may need refresh"
├── Log for ops investigation
└── Do NOT retry — human intervention needed
```

### Max Output Tokens → Context Too Large

```
StopFailure fires with error_type="max_output_tokens"
├── Signal to session_manager: agent's context is too large
├── Force compact on next cycle
└── Log the overflow for context strategy tuning
```

## Configuration

```json
{
  "hooks": {
    "StopFailure": [
      {
        "type": "command",
        "command": "python -m fleet.hooks.stop_failure_handler",
        "match": ["rate_limit", "authentication_failed"],
        "timeout": 5000
      }
    ]
  }
}
```

## Relationships

- FIRES ON: API errors that end a turn (NOT tool errors — those are PostToolUseFailure)
- CANNOT BLOCK: the failure already happened
- CONNECTS TO: storm_monitor.py (rate_limit → fast_climb indicator)
- CONNECTS TO: budget_monitor.py (rate limit position update)
- CONNECTS TO: session_manager.py (max_output_tokens → force compact)
- CONNECTS TO: outage_detector.py (repeated failures → outage detection → disable CRONs)
- CONNECTS TO: error_reporter.py (agent error reporting for orchestrator)
- CONNECTS TO: /usage command (rate limit information)
- CONNECTS TO: fleet_escalate (auth failures escalated to PO)
- CONNECTS TO: notification_router.py (route error notifications appropriately)
- CONNECTS TO: circuit_breaker (per-agent breaker may trip on repeated failures)
- KEY INSIGHT: this hook turns INVISIBLE per-agent API errors into VISIBLE fleet-wide signals. Rate limits, auth failures, server errors — all become actionable fleet events instead of silent session failures.
