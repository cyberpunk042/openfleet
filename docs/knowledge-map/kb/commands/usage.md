# /usage

**Type:** Claude Code Built-In Command
**Category:** Context & Cost
**Available to:** ALL agents

## What It Actually Does

Shows plan usage limits and rate limit status. Displays two rate limit windows:
- **5-hour window:** tokens consumed in the current 5-hour session, percentage used, time until reset
- **7-day window:** tokens consumed in the rolling 7-day period, percentage used

This is the SECOND countdown that agents need to be aware of. /context shows context window remaining (per-agent). /usage shows rate limit remaining (fleet-wide — all agents share the same quota).

## When Fleet Agents Should Use It

**Near rate limit boundaries:** If the statusline shows 5h usage approaching 80%+, /usage gives exact numbers and time until reset.

**Before heavy operations:** About to start a complex implementation that will consume many tokens? /usage tells you if you have the budget.

**When the brain pauses dispatch:** If dispatch is paused due to budget, /usage shows why — which limit was hit, when it resets.

**Sprint cost awareness:** PM checking fleet token consumption for sprint cost tracking.

## The Two Parallel Countdowns

```
COUNTDOWN 1: Context remaining (per agent)
  Shown by: /context
  Controlled by: /compact
  PO tipping points: 7% = prepare, 5% = force

COUNTDOWN 2: Rate limit remaining (fleet-wide)
  Shown by: /usage
  Controlled by: budget_mode (tempo), dispatch pause
  PO tipping points: 85% = prepare (no heavy dispatches), 90% = force action
  Hard stops: 90% weekly → pause, 95% session → pause
```

Both matter. Heavy context NEAR rate limit rollover = 20% quota spike. The brain's session_manager should manage both simultaneously.

## What It Shows

```
Plan Usage:
  5-hour window: 24% used (resets in 3h 12m)
  7-day window:  41% used

Model: claude-opus-4-6 [1M]
```

## Relationships

- COMPLEMENTS: /context (context = per-agent capacity, usage = fleet-wide quota)
- COMPLEMENTS: /cost (cost = session tokens, usage = rate limit position)
- CONNECTS TO: budget_monitor.py (reads same OAuth API data)
- CONNECTS TO: session_manager.py (brain Step 10 — rate limit awareness)
- CONNECTS TO: storm_monitor.py (fast_climb indicator — budget +5% in 10min)
- CONNECTS TO: CW-07 (rate limit rollover awareness in brain)
- CONNECTS TO: CW-08 (pre-rollover preparation — compact before reset)
- CONNECTS TO: CLAUDE.md Section 7 (context awareness — both countdowns)
- CONNECTS TO: statusline (rate limit % displayed: "5h:24% 7d:41%")
- CONNECTS TO: budget_mode (tempo affects how fast quota is consumed)
- DATA FROM: Claude OAuth API (/usage endpoint, cached 5 minutes by budget_monitor.py)
