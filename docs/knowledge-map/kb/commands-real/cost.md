# /cost

**Type:** Claude Code Built-In Command
**Category:** Context & Cost
**Available to:** ALL agents (especially PM, Fleet-ops, Accountability)

## What It Actually Does

Shows token usage statistics for the current session: total input tokens, output tokens, estimated cost in USD, session duration, lines added/removed. This is the SESSION-level cost view — what THIS session has consumed.

Different from /usage which shows rate limit position (fleet-wide quota). /cost shows what THIS agent in THIS session has spent.

## When Fleet Agents Should Use It

**Budget awareness during work:** Engineer mid-implementation checks /cost to see how much this task is costing. If a routine 2-SP task is consuming more than expected, something might be wrong (too many file reads, scope creep, going in circles).

**Sprint cost tracking (PM):** PM checks /cost across agent sessions to understand sprint token consumption. Feeds into pm-status-report metrics.

**Fleet cost auditing (Accountability):** Accountability reviews session costs for compliance reporting. Are agents efficient? Is the budget being used wisely?

**Before heavy operations:** About to run /batch or /simplify (3x agents)? /cost shows current consumption — helps decide if budget allows it.

## What It Shows

```
Session cost:
  Input tokens:  45,231
  Output tokens: 12,847
  Total tokens:  58,078
  Estimated cost: $0.87
  Duration: 12m 34s
  Lines: +256 / -31
```

## Relationships

- COMPLEMENTS: /usage (session cost vs fleet-wide quota position)
- COMPLEMENTS: /context (context size vs cost — correlated)
- CONNECTS TO: LaborStamp (session cost feeds estimated_cost_usd field)
- CONNECTS TO: session_telemetry.py (to_cost_delta extracts same data)
- CONNECTS TO: budget_analytics.py (cost per task type, per agent, per model)
- CONNECTS TO: heartbeat_stamp.py (heartbeat cost tracking — alert if >$0.10)
- CONNECTS TO: pm-status-report skill (metrics section includes cost data)
- CONNECTS TO: §47 economic model (cost-per-task breakdown)
- CONNECTS TO: budget_mode (tempo affects cost — turbo = more operations = higher cost)
- CONNECTS TO: LaborAnalytics (rolling 500 stamps, per-agent cost breakdowns)
