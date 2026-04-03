# System 15: Challenge Engine — Iterative Adversarial Validation

**Type:** Fleet System (LARGEST — 8 files, 2831 lines, 235 tests)
**ID:** S15
**Files:** challenge.py (353), challenge_protocol.py (596), challenge_automated.py (278), challenge_cross_model.py (346), challenge_scenario.py (299), challenge_readiness.py (281), challenge_deferred.py (337), challenge_analytics.py (341)
**Total:** 2,831 lines
**Tests:** 235 (most thorough test suite)

## What This System Does

Work doesn't go straight to fleet-ops review — it faces adversarial challenges FIRST. 4 challenge types with different cost/quality tradeoffs. Challenge depth scales by confidence tier (trainee gets mandatory 3 rounds, expert gets optional 1). Deferred challenge queue persists for when budget improves. Analytics feed teaching signals for repeated failure patterns.

Born from the March catastrophe where fleet-ops rubber-stamped approvals in <30 seconds and bugs shipped.

## 4 Challenge Types

| Type | Cost | How It Works | When Used |
|------|------|-------------|-----------|
| AUTOMATED | $0 (free) | 7 deterministic pattern checks from diff (regression, edge cases, loops, async, timeout, architecture, error handling) | Default for all tasks |
| AGENT | $$ (Claude tokens) | Domain expert agent reviews adversarially. Challenger selected by domain: security→devsecops, epic→architect, tests→QA. | Complex tasks, SP≥5 |
| CROSS-MODEL | $ (different LLM) | Different model challenges work. Simple→hermes-3b (free), medium→sonnet, complex→opus. Genuine independent verification. | Trainee/community tier work |
| SCENARIO | $ (targeted) | Reproduce-and-break for bug fixes. 5 types: reproduction, removal, regression, boundary, concurrency. | Bug fixes with SP≥3 |

## Challenge Depth by Confidence Tier

| Tier | Required? | Max Rounds | Types Available |
|------|-----------|-----------|-----------------|
| trainee/community | MANDATORY | 3 | All 4 types |
| standard | Recommended (SP≥5) | 2 | Automated + agent |
| expert | Optional | 1 | Automated only |

## Challenge Flow

```
fleet_task_complete(summary)
  ↓
evaluate_challenge(task, confidence_tier, author_agent)
  ↓ ChallengeDecision: required?, type, challenger, max_rounds
  ↓
start_challenge(task, decision)
  ├── AUTOMATED → generate 7 pattern checks → execute → boolean results
  ├── AGENT → build ChallengeContext → dispatch to challenger agent
  ├── CROSS_MODEL → send to different LLM → parse findings
  └── SCENARIO → generate 5 scenario types → execute steps
  ↓
Each finding has lifecycle: OPEN → ADDRESSED → VERIFIED → WONT_FIX → INVALID
  ↓
evaluate_round_outcome(record)
  ├── All findings verified/wont_fix/invalid → PASSED → advance to review
  ├── Open findings remain → RECHALLENGE → author reworks → next round
  └── Max rounds with open findings → ESCALATE → PO decides
  ↓
Challenge results stored on task custom fields:
  challenge_round, challenge_max_rounds, challenge_status,
  challenge_findings, challenge_challenger, challenge_type
```

## Progress Integration

Challenge results feed task_progress (the post-dispatch progression):
```
70% = WORK_COMPLETE     (agent called fleet_task_complete)
80% = CHALLENGE_PASSED  (adversarial validation survived)
90% = REVIEW_PASSED     (fleet-ops approved)
95% = PO_APPROVED       (PO signed off)
100% = DONE
```

## Deferred Challenge Queue

When budget is tight, challenges are DEFERRED not permanently skipped:
- Persisted to `state/deferred_challenges.json`
- Priority: story_points + tier_bonus + type_bonus
- Status thresholds: OK (<10 queued), WARNING (10-25), CRITICAL (>25)
- Age alert: WARNING at 24h deferred, CRITICAL at 72h
- Drain: when budget allows, dequeue highest priority first

## 7 Automated Pattern Checks (FREE)

| Pattern | What It Checks |
|---------|---------------|
| Regression | Run full test suite — any previously passing tests fail? |
| Edge cases | Boundary values (0, 1, -1, max, None) |
| Loop handling | Empty, single, large (100+) inputs |
| Async/concurrency | Race conditions, gather with failures |
| Timeout/retry | Network unavailable, extreme latency |
| Architecture | Import cycles, cross-module consistency |
| Error handling | Bare except, exception swallowing |

## Teaching Signals

challenge_analytics.py aggregates outcomes:
- Per agent: pass_rate, avg_rounds, total_findings, top_categories
- Per tier: pass_rate, avg_rounds
- teaching_signals(min_failures=3): agent with 3+ failures in same category → TeachingSignal → adapted lesson

## Relationships

- TRIGGERED BY: fleet_task_complete (evaluate_challenge after work complete)
- GATES: task_progress advancement (70→80 only after challenge passed)
- FEEDS: fleet-ops review (challenge results available during 7-step review — NOT YET WIRED)
- FEEDS: S03 teaching (teaching_signals from analytics → adapted lessons)
- CONNECTS TO: S07 orchestrator (deferred queue drain in cycle — NOT YET WIRED)
- CONNECTS TO: S08 MCP tools (fleet_task_complete triggers challenge)
- CONNECTS TO: S13 labor (challenge_rounds_survived in LaborStamp)
- CONNECTS TO: S14 router (cross-model uses different backend, confidence tier determines depth)
- CONNECTS TO: codex-plugin-cc (adversarial review — cross-provider challenge)
- CONNECTS TO: codex_review.py (tier-driven Codex adversarial trigger)
- NOT YET WIRED: challenge results not in fleet-ops review flow, automated challenges never tested against real diffs, cross-model with LocalAI not integrated, deferred queue drain not in orchestrator, teaching signals not feeding teaching system

## For LightRAG Entity Extraction

Key entities: ChallengeType (4 types), ChallengeRecord (per task), ChallengeRound (per round), ChallengeFinding (OPEN→ADDRESSED→VERIFIED), ChallengeDecision, ChallengeProtocol, DeferredChallengeQueue, ChallengeAnalytics, TeachingSignal.

Key relationships: Confidence tier DETERMINES challenge depth. Challenge EVALUATES work quality. Findings REQUIRE author response. Round outcome GATES progress (70→80). Deferred queue PERSISTS for later. Analytics FEEDS teaching signals. 3+ failures TRIGGER adapted lessons. Challenge results INFORM fleet-ops review.
