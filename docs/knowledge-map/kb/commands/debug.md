# /debug

**Type:** Claude Code Built-In Skill Command
**Category:** Bundled Skills
**Available to:** ALL agents (especially Engineer, DevOps, QA)

## What It Actually Does

Enables debug logging and enters a systematic troubleshooting workflow. Takes an optional description of what's wrong. This is a bundled skill — not just a flag toggle. It activates a structured debugging approach: reproduce the issue, isolate the cause, verify the fix.

Under the hood, /debug increases logging verbosity and focuses Claude's attention on diagnostic information: error messages, stack traces, variable states, execution flow. It's the equivalent of "put on your debugging hat."

## When Fleet Agents Should Use It

**Test failures with unclear cause:** Tests fail but the error message doesn't point to the obvious fix. /debug → read the test → read the implementation → trace the data flow → find the mismatch.

**Runtime errors during implementation:** Code throws an exception during fleet_commit's test run or during manual testing. /debug → read the traceback → find the root cause → fix.

**Integration issues between components:** Two modules that should work together don't. /debug → trace data from module A to module B → find where it breaks.

**When stuck for more than a few minutes:** The methodology says "if stuck, don't guess." /debug is the structured alternative to guessing.

## The Debugging Approach

Without /debug, agents often:
1. Read the error → guess the fix → try it → wrong → guess again → waste tokens

With /debug (or systematic-debugging from Superpowers):
1. **Reproduce:** confirm the issue exists, get exact error
2. **Isolate:** narrow down where in the code the issue occurs
3. **Understand:** read the actual logic at the failure point
4. **Fix:** make the specific change that addresses the root cause
5. **Verify:** confirm the fix works AND no regressions

## Per-Role Usage

| Role | When | What They Debug |
|------|------|----------------|
| Engineer | work stage | Implementation bugs, test failures, integration issues |
| DevOps | work stage | Deployment failures, infrastructure issues, CI problems |
| QA | work stage | Test framework issues, flaky tests, environment problems |
| DevSecOps | investigation | Security vulnerability reproduction, exploit verification |

## Relationships

- CONNECTS TO: systematic-debugging skill (Superpowers — 4-phase root cause process)
- CONNECTS TO: /debug flag in Claude Code (increases logging verbosity)
- CONNECTS TO: pytest-mcp server (get_failures, analyze_error, debug_trace tools)
- CONNECTS TO: fleet_pause (if debugging reveals a blocker, pause and escalate)
- CONNECTS TO: fleet_alert (if debugging reveals a security issue)
- CONNECTS TO: ops-incident skill (debug is part of incident response)
- CONNECTS TO: doctor.py detect_stuck (agent debugging for >60 minutes → doctor notices)
- CONNECTS TO: teaching system — "code_without_reading" disease: /debug forces reading before fixing
- ANTI-PATTERN: debugging by guessing wastes tokens and context. /debug forces structured investigation.
- PAIRS WITH: /compact (after long debug session, compact to keep findings, drop exploration)
