# Challenge Engine — Iterative Adversarial Validation

> **8 files. 2831 lines. Multi-round challenges before approval. The largest system.**
>
> Work doesn't go straight to review. It faces adversarial challenges
> first. 4 challenge types with different cost/quality tradeoffs:
> automated (free, pattern-based), agent (domain expert), cross-model
> (different LLM), scenario (reproduce-and-break for bugs). Budget mode
> determines challenge depth. Deferred challenges queue for later when
> budget is tight. Challenge readiness gates task progression.

### PO Requirement (Verbatim)

> "we really have to be ready to do multiple agent iteration where the
> validation and testing had to be challenged and challenged in order
> to really fix the bugs and meet the requirements."

> "we need to avoid brainless loop and recursive chain that don't end"

---

## 1. Why It Exists

Single-pass review missed critical issues. Fleet-ops reviewed in <30s
(rubber stamp). The challenge engine adds adversarial validation
BEFORE review — work must survive challenges to reach fleet-ops.

```
BEFORE: work → review (rubber stamp) → done → bugs in production

AFTER:  work → challenge (adversarial) → findings → fixes →
        re-challenge → pass → review (evidence-backed) → done
```

## 2. How It Works

### 2.1 Challenge Flow

```
Agent completes work
  ↓
evaluate_challenge(task, tier, budget_mode)
  ↓
If not required → proceed to review
If deferred → queue for later, tag task
If required:
  ↓
Challenge type selected:
  ├── automated  — FREE pattern checks (no LLM)
  ├── agent      — domain expert reviews adversarially
  ├── cross-model — different LLM challenges work
  └── scenario   — reproduce-and-break for bugs
  ↓
Findings posted → author addresses each
  ↓
Round outcome: passed / rechallenge / escalate
  ↓
If passed → advance to review (readiness 80%)
If rechallenge → repeat (up to max_rounds)
```

### 2.2 Challenge Depth by Budget (W1)

| Budget Mode | Strategy |
|------------|----------|
| blitz | Full: agent + cross-model for SP≥5, automated for rest |
| standard | Agent for SP≥5 or trainee, automated for rest |
| economic | Automated only (free), agent for security only |
| frugal | Automated only, challenges deferred |
| survival | No challenges — defer all |
| blackout | No work |

### 2.3 Challenge by Tier

| Tier | Required? | Max Rounds | Types |
|------|-----------|-----------|-------|
| expert | Optional | 1 | Automated |
| standard | Recommended SP≥5 | 2 | Automated + agent |
| trainee | **Mandatory** | 3 | Automated + agent + cross-model |
| community | **Mandatory** | 3 | All types |

### 2.4 Readiness Checkpoints

```
70% → WORK_COMPLETE    80% → CHALLENGE_PASSED
90% → REVIEW_PASSED    95% → PO_APPROVED    100% → DONE
```

### 2.5 Deferred Queue

Budget tight → defer challenge → queue in `state/deferred_challenges.json`.
When budget improves → drain queue (FIFO + priority). Drain batch:
blitz=10, standard=5, economic=3.

---

## 3. File Map

```
fleet/core/
├── challenge.py            Data model: types, statuses, findings       (353 lines)
├── challenge_protocol.py   Decision: evaluate, select type/challenger   (596 lines)
├── challenge_automated.py  Pattern checks: regression, edge, async      (278 lines)
├── challenge_cross_model.py Different LLM reviews work                  (346 lines)
├── challenge_scenario.py   Reproduce-and-break for bug fixes            (299 lines)
├── challenge_readiness.py  Readiness gates: 70→80→90→95→100             (281 lines)
├── challenge_deferred.py   Budget-aware queue, drain logic              (337 lines)
└── challenge_analytics.py  Pass rates, trends, teaching signals         (341 lines)
```

Total: **2831 lines** — the largest system.

## 4. Per-File Key Functions

### challenge.py — Enums: ChallengeType (4), ChallengeStatus (6), FindingStatus (5). Classes: ChallengeFinding, ChallengeRound, ChallengeRecord.

### challenge_protocol.py — `evaluate_challenge()`: combined decision. `is_challenge_required()`: tier+type+budget. `select_challenge_type()`: bugs→scenario, trainee→cross_model. `max_rounds_for_tier()`: trainee=3, standard=2, expert=1.

### challenge_automated.py — 7 pattern checks: regression, edge cases, async/concurrency, loops, network timeout, import cycles, error handling. All FREE (no LLM).

### challenge_cross_model.py — Select model by complexity, build challenge message, parse findings. `CrossModelConfig`: models per complexity level.

### challenge_scenario.py — 5 scenario types: reproduction, removal, regression, boundary, concurrency. Generate and evaluate per scenario.

### challenge_readiness.py — 5 checkpoints with readiness values. `check_readiness()` maps work/challenge/review status to readiness.

### challenge_deferred.py — `should_defer_challenge()`: True for frugal/survival/blackout (W1 uses MODE_ORDER). Queue with FIFO + priority boost for high SP. Persistence to JSON.

### challenge_analytics.py — ChallengeEvent tracking. Per-agent/tier pass rates. TeachingSignal from repeated failures.

## 5. Dependencies

challenge.py ← standalone. challenge_protocol ← imports challenge + models. challenge_deferred ← imports budget_modes.MODE_ORDER (W1). Others standalone.

## 6. Design Decisions

**Why 4 types?** Different validation for different situations. Automated is free. Agent catches design issues. Cross-model catches blind spots. Scenario catches regressions.

**Why deferred, not skip?** Skipping permanently = trainee work never validated. Deferring = validate when budget allows.

**Why max_rounds by tier?** Expert (opus) rarely needs >1 round. Trainee (LocalAI) needs 3 — lower initial quality needs more validation.

## 7. Test Coverage: **235 tests** — most thorough in the fleet.

## 8. What's Needed

- Connect to fleet-ops review flow
- Automated challenge live test against real diffs
- Cross-model with LocalAI as free challenger
- Deferred queue drain in orchestrator
- Teaching signals feeding teaching system
