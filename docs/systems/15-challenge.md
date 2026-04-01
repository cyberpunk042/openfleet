# System 15: Challenge Engine

**Source:** `fleet/core/challenge.py`, `challenge_protocol.py`, `challenge_automated.py`, `challenge_cross_model.py`, `challenge_scenario.py`, `challenge_readiness.py`, `challenge_deferred.py`, `challenge_analytics.py`
**Status:** 🔨 Unit tests (178). Not connected to real agent review flow.
**Design docs:** `iterative-validation-and-challenge-loops.md` (M-IV01-08)

---

## Purpose

Multi-round adversarial validation before approval. Not single-pass — challenges CHALLENGE the work. 4 types with different cost/quality tradeoffs. Budget-aware: expensive challenges deferred when tight.

### PO Requirement (Verbatim)

> "we really have to be ready to do multiple agent iteration where the validation and testing had to be challenged and challenged in order to really fix the bugs"

## Key Concepts

### 4 Challenge Types

1. **automated** — pattern-based from diffs (FREE, no LLM)
2. **agent** — different agent reviews (standard cost)
3. **cross-model** — different backend reviews (varies)
4. **scenario** — reproduce + vary bugs (varies)

### Challenge Decision (challenge_protocol.py:171-220)

`evaluate_challenge(task, confidence_tier, budget_mode)` → ChallengeDecision:
- required: bool
- challenge_type: which type
- deferred: bool (budget too tight)
- max_rounds: per tier (more for trainee)

### Budget-Aware (W1 wiring)

Challenge depth by budget mode:
- blitz: full (agent + cross-model for SP≥5)
- standard: agent for SP≥5 or trainee
- economic: automated only (free)
- frugal: automated only, deferred queue
- survival: no challenges
- blackout: no work

Uses `MODE_ORDER` from budget_modes (W1 wiring — no hardcoded constants).

### Deferred Queue (challenge_deferred.py)

When budget tight, challenges tagged for later: `should_defer_challenge(budget_mode)`. Queue persists to `state/deferred_challenges.json`. When budget improves, brain drains queue (FIFO + priority).

### Challenge Readiness (challenge_readiness.py)

5 checkpoints: WORK_COMPLETE (70), CHALLENGE_PASSED (80), REVIEW_PASSED (90), PO_APPROVED (95), DONE (100).

### Challenge Analytics (challenge_analytics.py)

Per-agent pass rates, per-tier metrics, common finding categories, teaching signals from repeated failures.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Budget** | Budget mode constrains challenge depth (W1) | Budget → Challenge |
| **Labor Stamps** | challenge_skipped field records deferral (W2) | Challenge → Stamps |
| **Codex Review** | Cross-model challenges can use codex plugin | Challenge → Review |
| **Methodology** | Challenge readiness feeds task readiness | Challenge → Methodology |
| **Doctor** | Challenge avoidance detected as disease | Challenge → Doctor |

## What's Needed

- [ ] Connect to fleet-ops review flow (challenges run before/during review)
- [ ] Automated challenge generator live test
- [ ] Cross-model challenge with real LocalAI inference
- [ ] Deferred queue drain logic in orchestrator
