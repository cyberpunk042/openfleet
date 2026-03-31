# Iterative Validation and Challenge Loops

## Severity: STRATEGIC
## Status: DESIGN
## Created: 2026-03-31

Single-pass validation is not enough. The fleet must support multi-round
adversarial challenge loops where work is tested, challenged, re-tested,
and challenged again until it truly meets the requirements. This applies
to bug fixes, feature implementation, and milestone execution.

---

## Part 1: PO Requirements (Verbatim)

> "in situation like we just experience we really have to be ready to do
> multiple agent iteration where the validation and testing had to be
> challenged and challenged in order to really fix the bugs and meet the
> requirements."

> "to think about when evolving the milestones and writing the new ones."

> "we have a series of milestones planned and we need to make sure they
> are bulletproof and we cover everything properly."

---

## Part 2: The Problem — What Single-Pass Looks Like

### What Happened (Previous Session)

1. Bug detected: agents in infinite loop, not settling
2. Fix attempted: modify orchestrator
3. Test: "does it start?" → yes → "fix works"
4. Reality: different failure mode, process storms, high costs
5. Another fix attempted
6. Another test: surface-level check
7. Reality: still broken, different way
8. Repeat until catastrophic token drain

**The failure pattern:** Each fix was tested only once, at the surface
level, against the symptom that was visible at that moment. Nobody
challenged the fix with adversarial scenarios. Nobody asked "what if
this fix creates a new failure mode?"

### Current Quality Gates (Single-Pass)

| Gate | What It Checks | Limitation |
|------|---------------|------------|
| `plan_quality.py` | Plan score ≥ 40 (steps, verify, risk) | Checks plan text, not execution |
| `fleet_task_complete` | Tests pass (pytest) | Runs once, no adversarial cases |
| fleet-ops review | Verbatim match, approval | One reviewer, one pass |
| Doctor (immune system) | Protocol violations | Catches process errors, not logic errors |
| PO gate at 90% readiness | Human approval | Catches requirements gaps, not bugs |

**What's missing:** Nobody runs the fix with deliberately hostile inputs.
Nobody checks "does this fix break something else?" Nobody asks a second
model to challenge the first model's work. Nobody iterates until the
fix survives adversarial scrutiny.

---

## Part 3: Challenge Loop Design

### The Loop

```
Agent produces work
    ↓
Quality Gate 1: Basic (automated)
  - Tests pass?
  - Lint passes?
  - No regressions?
    ↓ PASS
Challenge Gate: Adversarial (agent or model)
  - Challenge the implementation with hostile scenarios
  - Try to break it
  - Find edge cases the author missed
  - Check: does this fix create new failure modes?
    ↓ ISSUES FOUND
Author addresses issues
    ↓
Challenge Gate: Round 2 (same or different challenger)
  - Re-challenge with original issues + new scenarios
  - Verify fixes didn't introduce regressions
    ↓ PASS
Quality Gate 2: Review (fleet-ops)
  - Standard review with labor attribution
  - Confidence tier determines depth
    ↓ APPROVED
Done (or PO gate if readiness ≥ 90%)
```

### Challenge Depth by Confidence Tier

| Confidence Tier | Challenge Required? | Challenger | Max Rounds |
|----------------|--------------------|-----------:|------------|
| expert (opus) | Optional — PO/fleet-ops decides | Different agent or Codex | 1 |
| standard (sonnet) | Recommended for SP ≥ 5 | Different agent or Codex | 2 |
| trainee (LocalAI) | **Mandatory** | Claude sonnet (minimum) | 3 |
| community (free) | **Mandatory** | Claude sonnet + fleet-ops | 3 |
| hybrid | **Mandatory** for trainee/community components | Per-component | 3 |

### Challenge Depth by Task Type

| Task Type | Challenge Required? | Rationale |
|-----------|--------------------|-----------:|
| Security-related | **Always mandatory** | Cannot compromise |
| Architecture decisions | **Always mandatory** | Cascading impact |
| Bug fixes | **Mandatory if SP ≥ 3** | Previous session proved surface fixes fail |
| New features (SP ≥ 5) | Recommended | Complex work benefits from challenge |
| Simple tasks (SP ≤ 2) | Optional | Cost of challenge may exceed value |
| Documentation | Optional | Low risk |
| Heartbeats | Never | Zero-value challenge |

---

## Part 4: Challenge Types

### Type 1: Automated Challenge (cheapest)

The brain generates challenge scenarios deterministically (no LLM cost):

```python
def generate_automated_challenges(task: Task, diff: str) -> list[str]:
    """Generate challenge scenarios from task metadata and diff.

    No LLM needed — pattern-based.
    """
    challenges = []

    # Regression check
    challenges.append("Run full test suite including previously passing tests")

    # Edge case generation from diff
    if "if " in diff or "else" in diff:
        challenges.append("Test with boundary values at every conditional")
    if "loop" in diff or "for " in diff or "while " in diff:
        challenges.append("Test with empty input, single item, max items")
    if "async" in diff or "await" in diff:
        challenges.append("Test concurrent execution — race conditions?")
    if "timeout" in diff or "retry" in diff:
        challenges.append("Test with network unavailable, extreme latency")

    # Architecture check
    if len(diff.split("+++")) > 5:  # multi-file change
        challenges.append("Check for import cycles and circular dependencies")

    return challenges
```

### Type 2: Agent Challenge (medium cost)

A **different agent** reviews the work adversarially:

```
software-engineer completes task
    ↓
Brain assigns challenge to:
  - QA engineer (for test adequacy)
  - devsecops-expert (for security implications)
  - architect (for architectural fit)
    ↓
Challenger agent receives:
  - The diff
  - The original requirement (verbatim)
  - The author's summary
  - Instruction: "Find flaws. Be adversarial. Try to break this."
    ↓
Challenger posts findings as contribution (contribution_type: challenge_review)
    ↓
If issues found → author addresses → challenger re-reviews
```

### Type 3: Cross-Model Challenge (low cost, high value)

Use a **different model** to challenge the work:

```
Claude opus produced the implementation
    ↓
Challenge via:
  - Claude sonnet (cheaper model, different perspective)
  - Codex CLI (different AI entirely — adversarial by design)
  - LocalAI (free, may catch obvious issues)
    ↓
Challenger model reviews the diff and asks:
  1. "Does this actually solve the stated requirement?"
  2. "What failure modes does this introduce?"
  3. "What edge cases are not handled?"
  4. "Is there a simpler solution?"
    ↓
Findings posted → author addresses or justifies
```

### Type 4: Scenario Challenge (highest value for bug fixes)

For bug fixes specifically, the challenger must **reproduce the original
bug** and verify the fix works, then try **variations**:

```
Bug: "agents stuck in infinite loop"
Fix: "added max_iterations guard"
    ↓
Scenario challenge:
  1. Reproduce original bug conditions → verify fix works
  2. Try: what if max_iterations is reached? Does it degrade gracefully?
  3. Try: what if two agents hit max_iterations simultaneously?
  4. Try: what if the guard itself has a bug? (edge: max_iterations = 0)
  5. Try: does this fix interact with other recent changes?
  6. Try: remove the fix → does the original bug return? (confirms root cause)
    ↓
Each scenario: PASS or FAIL with evidence
    ↓
If any FAIL → back to author
```

---

## Part 5: Iteration Tracking

### TaskCustomFields Extension

```python
# Challenge loop tracking
challenge_round: int = 0                    # Current challenge round (0 = not started)
challenge_max_rounds: int = 3               # Max rounds before human escalation
challenge_status: Optional[str] = None      # "pending", "in_progress", "passed", "failed"
challenge_findings: Optional[list] = None   # Findings from each round
challenge_challenger: Optional[str] = None  # Who/what is challenging
challenge_type: Optional[str] = None        # "automated", "agent", "cross-model", "scenario"
```

### Labor Stamp Extension

The labor stamp records iteration context:

```python
# In LaborStamp:
iteration: int                    # Which attempt (1 = first pass)
challenge_rounds_survived: int    # How many challenge rounds this passed
challenge_types_faced: list[str]  # ["automated", "agent:qa-engineer", "cross-model:codex"]
previous_attempt_id: str | None   # Link to prior attempt if this is a retry
```

### Board Memory Trail

Each challenge round is recorded:

```
[challenge:round-1] QA challenged software-engineer's auth middleware:
  FOUND: JWT expiry edge case not handled (token expires mid-request)
  FOUND: No rate limiting on token refresh endpoint
  VERDICT: 2 issues, sent back for fixes

[challenge:round-2] QA re-challenged after fixes:
  VERIFIED: JWT expiry now handled (graceful 401 + refresh)
  VERIFIED: Rate limiting added (10 req/min per IP)
  NEW: Race condition when two requests refresh simultaneously
  VERDICT: 1 issue remaining

[challenge:round-3] QA final challenge:
  VERIFIED: Race condition fixed (atomic compare-and-swap on refresh)
  VERDICT: PASSED — all scenarios survived
```

---

## Part 6: Integration with Existing Systems

### Immune System

The doctor can detect **challenge avoidance patterns**:
- Agent completes task without waiting for mandatory challenge
- Agent marks challenge as passed without evidence
- Agent addresses surface issues but ignores deeper findings

Disease: `challenge_avoidance` → teaching intervention:
"Challenges exist to catch bugs before they reach production. Review
the challenge protocol and demonstrate comprehension."

### Methodology System

Challenge loops integrate with the stage protocol:
- **Work stage** → produce the work
- **Challenge stage** (new) → work faces adversarial review
- **Review stage** → fleet-ops reviews work + challenge results

The readiness progression:
- 70% → work complete, ready for challenge
- 80% → challenge passed (or waived for simple tasks)
- 90% → fleet-ops review passed → PO gate

### Contribution System

Challenge findings are **contributions** with type `challenge_review`:
- Challenger posts contribution on the target task
- Author sees the contribution in their context
- Author addresses each finding
- Brain tracks: "all challenge findings addressed?" before advancing

---

## Part 7: Budget-Aware Challenge Decisions

Challenges cost tokens. The brain must balance thoroughness with cost:

| Budget Mode | Challenge Strategy |
|------------|-------------------|
| blitz | Full challenges: agent + cross-model for SP ≥ 5, automated for rest |
| standard | Agent challenge for SP ≥ 5 or trainee tier, automated for rest |
| economic | Automated challenge only (free), agent challenge for security tasks |
| frugal | Automated challenge only, skip agent challenges entirely |
| survival | No challenges — cost of challenge exceeds value. Flag for later review. |
| blackout | No work, no challenges |

When a challenge is skipped due to budget:
- Labor stamp records: `challenge_skipped: true, reason: "frugal mode"`
- Task is tagged: `needs-deferred-challenge`
- When budget mode improves → brain queues deferred challenges

---

## Part 8: Milestones

### M-IV01: Challenge Loop Data Model
- Add challenge fields to `TaskCustomFields`
- Add challenge tracking to `LaborStamp`
- Define challenge types (automated, agent, cross-model, scenario)
- Tests for data model
- **Status:** ⏳ PENDING

### M-IV02: Automated Challenge Generator
- Pattern-based challenge generation from diffs
- No LLM cost — deterministic rules
- Edge case detection, regression checks, architectural checks
- Tests for generator coverage
- **Status:** ⏳ PENDING

### M-IV03: Agent Challenge Protocol
- Brain assigns challenger agent based on task domain
- Challenger receives diff + requirement + summary
- Challenger posts findings as `challenge_review` contribution
- Author addresses findings
- Brain tracks: "all findings addressed?"
- **Status:** ⏳ PENDING

### M-IV04: Cross-Model Challenge
- Different model reviews the work
- Codex CLI integration for adversarial review (cross-ref: multi-backend router M-BR06)
- LocalAI as free challenger for simple tasks
- Claude sonnet as challenger for trainee-tier work
- **Status:** ⏳ PENDING

### M-IV05: Scenario Challenge for Bug Fixes
- Reproduction of original bug conditions
- Variation testing (boundary, concurrent, removal)
- Evidence collection (logs, test output)
- Pass/fail per scenario with trail
- **Status:** ⏳ PENDING

### M-IV06: Challenge-Aware Readiness Progression
- New readiness checkpoints: 70% (work done), 80% (challenge passed)
- Stage protocol update: work → challenge → review
- Brain enforces: no review until challenge passed (or waived)
- **Status:** ⏳ PENDING

### M-IV07: Deferred Challenge Queue
- When challenge skipped due to budget → tag task
- When budget mode improves → brain queues deferred challenges
- Track: how many tasks have pending deferred challenges?
- Alert if deferred queue grows too large
- **Status:** ⏳ PENDING

### M-IV08: Challenge Analytics
- Track: challenge pass rate per agent (who produces work that survives challenge?)
- Track: challenge pass rate per confidence tier
- Track: average rounds to pass
- Track: most common findings (what do agents keep getting wrong?)
- Feed into teaching system: if agent repeatedly fails same challenge type → lesson
- **Status:** ⏳ PENDING

---

## Part 9: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Labor Attribution | Labor stamps record challenge rounds survived |
| Budget Mode System | Budget mode determines challenge depth |
| Multi-Backend Router | Cross-model challenge uses different backend |
| Storm Prevention | Challenge loops catch bugs before they cause storms |
| Fleet Elevation Doc 17 | Standards framework — challenge is a new quality dimension |
| Fleet Elevation Doc 19 | Flow validation — challenge is a new gate in the lifecycle |
| Immune System | Doctor detects challenge avoidance |
| Teaching System | Repeated challenge failures trigger teaching |
| Methodology System | Challenge stage added to stage protocol |
| Catastrophic Drain | Challenges would have caught the orchestrator _send_chat bug |

---

## Part 10: Why This Matters

The previous session's catastrophic drain was caused by a fix that was
"tested" once — "does it start? yes → ship it." The fix created a new
failure mode (process storms) that was worse than the original bug.

If challenge loops had existed:
1. Fix produced → automated challenge: "what happens on restart?"
   → FOUND: module globals reset, triggers immediate wake
2. Fix addresses restart → agent challenge: "what about concurrent sessions?"
   → FOUND: no rate limiting, gateway fires all heartbeats simultaneously
3. Fix addresses concurrency → scenario challenge: "remove fix, does
   original bug return?"
   → FOUND: yes, confirming root cause. Fix is correct but incomplete.
4. Fix expanded → cross-model challenge: "is there a simpler design?"
   → FOUND: orchestrator should not call _send_chat at all. Revert.

Four rounds would have caught what weeks of debugging eventually revealed.
The cost of four challenge rounds: ~$2-5. The cost of the catastrophic
drain: 20% of a weekly Claude plan.

> Challenges are not overhead. They are insurance. The most expensive bug
> is the one that passes review and runs in production.