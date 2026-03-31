# Implementation Roadmap — Strategic Milestones

## Created: 2026-03-31
## Status: ACTIVE PLAN

47 new milestones across 6 documents. This roadmap sequences them into
implementation waves — what gets built first, what depends on what,
and how each wave unlocks the next level of fleet capability.

---

## Guiding Principle

> Build the safety net before the trapeze.

Storm prevention and labor attribution come FIRST because they protect
everything that follows. You cannot safely route to new backends without
storm prevention. You cannot evaluate new models without labor stamps.
You cannot justify budget mode transitions without cost data.

---

## Wave 1: FOUNDATION — Safety + Observability
**Priority: CRITICAL**
**Prerequisite for: everything else**
**Estimated milestones: 10**

The fleet cannot safely evolve without these. Wave 1 makes the fleet
observable and self-protecting before we add complexity.

| Order | Milestone | Doc | Why First |
|-------|-----------|-----|-----------|
| 1.1 | **M-SP01** Storm Monitor Core | Storm | Detect problems before they cascade |
| 1.2 | **M-SP02** Automatic Graduated Response | Storm | React to problems automatically |
| 1.3 | **M-SP04** Per-Agent Circuit Breaker | Storm | Isolate misbehaving agents |
| 1.4 | **M-SP06** Gateway Duplication Detection | Storm | Prevent the #1 root cause of the March drain |
| 1.5 | **M-LA01** LaborStamp Data Model | Labor | Define the provenance structure |
| 1.6 | **M-LA02** Dispatch Records Intent | Labor | Brain records what it chose and why |
| 1.7 | **M-LA04** Stamp Assembly in fleet_task_complete | Labor | Stamps appear on completed work |
| 1.8 | **M-LA05** Updated Comment and PR Templates | Labor | Stamps visible in artifacts |
| 1.9 | **M-BM01** BudgetMode Data Model | Budget | Define the 6 modes |
| 1.10 | **M-BM02** Mode-Constrained Model Selection | Budget | Modes constrain what models are used |

**Wave 1 outcome:** The fleet can detect storms, protect itself, record
what produces every artifact, and constrain spending by mode. Every
artifact from this point forward carries provenance.

**Integration with existing work:**
- Items #17-21 (operational readiness) can proceed in parallel
- Wave 1 should complete BEFORE item #21 (resume autonomous flow)
- The fleet should NOT run autonomously without storm prevention

---

## Wave 2: ROUTING — Multi-Backend + Budget Control
**Priority: HIGH**
**Depends on: Wave 1 complete**
**Estimated milestones: 10**

With safety and observability in place, the fleet gains new backends
and intelligent routing. This is where cost reduction begins.

| Order | Milestone | Doc | Why This Wave |
|-------|-----------|-----|---------------|
| 2.1 | **M-BR01** Backend Registry | Router | Define all available backends |
| 2.2 | **M-BR02** Routing Decision Engine | Router | The brain that picks backends |
| 2.3 | **M-BR03** Fallback Chain | Router | Graceful degradation between backends |
| 2.4 | **M-SP05** Per-Backend Circuit Breaker | Storm | Protect routing from backend failures |
| 2.5 | **M-BM03** Automatic Mode Transitions | Budget | Brain adjusts budget mode on pressure |
| 2.6 | **M-BR04** OpenRouter Free Integration | Router | First free external backend |
| 2.7 | **M-LA03** Session Metrics Collection | Labor | Track token usage per session |
| 2.8 | **M-LA06** Confidence-Aware Review Gates | Labor | Trainee work gets extra scrutiny |
| 2.9 | **M-SP03** Diagnostic Snapshot | Storm | Full diagnostic on storm events |
| 2.10 | **M-BM04** Budget Mode in Fleet CLI | Budget | PO can control modes from CLI |

**Wave 2 outcome:** The fleet routes to multiple backends (Claude +
LocalAI + OpenRouter free). Budget modes auto-adjust. Trainee work
gets appropriate review. Diagnostics capture storm events.

**Cost impact:** First meaningful cost reduction. Heartbeats and simple
operations start routing to free backends. OpenRouter provides fallback
when LocalAI is swapping models.

---

## Wave 3: VALIDATION — Challenge Loops + Quality
**Priority: HIGH**
**Depends on: Wave 2 (routing must work to cross-model challenge)**
**Estimated milestones: 9**

With multiple backends available, the fleet can now challenge work
adversarially using different models. This is where quality scales.

| Order | Milestone | Doc | Why This Wave |
|-------|-----------|-----|---------------|
| 3.1 | **M-IV01** Challenge Loop Data Model | Validation | Define challenge tracking |
| 3.2 | **M-IV02** Automated Challenge Generator | Validation | Free pattern-based challenges |
| 3.3 | **M-IV03** Agent Challenge Protocol | Validation | Different agent reviews the work |
| 3.4 | **M-IV06** Challenge-Aware Readiness Progression | Validation | Challenge becomes a stage gate |
| 3.5 | **M-IV04** Cross-Model Challenge | Validation | Different AI challenges the work |
| 3.6 | **M-IV05** Scenario Challenge for Bug Fixes | Validation | Reproduce + vary for bug fixes |
| 3.7 | **M-IV07** Deferred Challenge Queue | Validation | Budget-aware skip/defer |
| 3.8 | **M-SP07** Post-Incident Report Generation | Storm | Automatic incident analysis |
| 3.9 | **M-SP08** Orchestrator Storm Integration | Storm | Storm checks in every cycle |

**Wave 3 outcome:** Every non-trivial piece of work faces adversarial
challenge before review. Bug fixes get scenario testing. The fleet
catches bugs before they cause storms. Post-incident reports capture
what went wrong and why.

**Quality impact:** The previous session's infinite loop would have
been caught at challenge time. Multiple rounds of "challenged and
challenged" become standard operating procedure.

---

## Wave 4: EVOLUTION — Better Models + Analytics
**Priority: MEDIUM**
**Depends on: Waves 1-2 (labor stamps + routing must exist)**
**Estimated milestones: 10**

With routing and attribution in place, the fleet can safely evaluate
new models, upgrade LocalAI, and track performance over time.

| Order | Milestone | Doc | Why This Wave |
|-------|-----------|-----|---------------|
| 4.1 | **M-MU01** Qwen3-8B Evaluation | Models | Benchmark the upgrade candidate |
| 4.2 | **M-MU02** Model Config Templates | Models | YAML configs for new models |
| 4.3 | **M-MU03** Shadow Routing | Models | Test new model against old in production |
| 4.4 | **M-MU04** Default Model Promotion | Models | Switch fleet default to Qwen3-8B |
| 4.5 | **M-MU07** Confidence Tier Progression | Models | Track model trust over time |
| 4.6 | **M-LA07** Labor Analytics | Labor | Cost per agent, model, tier |
| 4.7 | **M-LA08** Heartbeat Labor Stamps | Labor | Track heartbeat cost trends |
| 4.8 | **M-BM06** Budget Analytics | Budget | Cost breakdown by mode, agent, model |
| 4.9 | **M-IV08** Challenge Analytics | Validation | Pass rates per agent per tier |
| 4.10 | **M-SP09** Storm Analytics | Storm | Storm frequency, duration, cost |

**Wave 4 outcome:** LocalAI upgraded to Qwen3-8B (2.5x better). Shadow
routing validates quality before promotion. Analytics dashboards show
cost trends, quality trends, storm trends. PO has data to make
tier-promotion decisions.

**Cost impact:** Major. Qwen3-8B handles significantly more work than
hermes-3b. Combined with OpenRouter free fallback, Claude usage drops
substantially for routine operations.

---

## Wave 5: SCALE — Dual GPU + Advanced Features
**Priority: MEDIUM-LOW (depends on hardware)**
**Depends on: Waves 1-4 + second GPU**
**Estimated milestones: 8**

With the foundation proven on single GPU, the fleet scales to dual GPU,
cluster peering, and advanced integration.

| Order | Milestone | Doc | Why This Wave |
|-------|-----------|-----|---------------|
| 5.1 | **M-MU05** Dual-GPU Configuration | Models | Two models simultaneously |
| 5.2 | **M-BR05** LocalAI Model Swap Management | Router | Router-driven swaps |
| 5.3 | **M-MU08** Cluster Peering | Models | Machine 1 ↔ Machine 2 |
| 5.4 | **M-BR06** Codex CLI Adversarial Review | Router | External AI for challenges |
| 5.5 | **M-BR07** Backend Health Dashboard | Router | Real-time backend status |
| 5.6 | **M-BM05** Budget Mode in OCMC UI | Budget | Visual budget control |
| 5.7 | **M-MU06** TurboQuant Integration | Models | When ecosystem supports it |
| 5.8 | **M-BR08** AICP Router Unification | Router | Merge AICP + fleet routing |

**Wave 5 outcome:** Two GPUs running simultaneously (Qwen3-8B + Phi-4).
Cluster peering between machines. Codex as external adversarial reviewer.
Full observability dashboard. AICP and fleet share the same routing brain.

**This is where the fleet starts approaching Stage 5 of LocalAI
independence — near-autonomous operation.**

---

## Wave Map

```
WAVE 1: FOUNDATION (safety + observability)
  M-SP01, M-SP02, M-SP04, M-SP06          ← storm protection
  M-LA01, M-LA02, M-LA04, M-LA05          ← labor stamps
  M-BM01, M-BM02                          ← budget modes defined
  ─────────────────────────────────────────
  Fleet is SAFE and OBSERVABLE
                    ↓
WAVE 2: ROUTING (multi-backend + budget control)
  M-BR01, M-BR02, M-BR03, M-BR04          ← backend routing
  M-SP05, M-SP03                           ← backend circuit breakers
  M-BM03, M-BM04                          ← auto-transitions + CLI
  M-LA03, M-LA06                          ← session metrics + review gates
  ─────────────────────────────────────────
  Fleet ROUTES INTELLIGENTLY and CONTROLS COST
                    ↓
WAVE 3: VALIDATION (challenge loops)
  M-IV01–M-IV07                            ← challenge system
  M-SP07, M-SP08                           ← post-incident + integration
  ─────────────────────────────────────────
  Fleet CHALLENGES WORK ADVERSARIALLY
                    ↓
WAVE 4: EVOLUTION (better models + analytics)
  M-MU01–M-MU04, M-MU07                   ← model upgrades
  M-LA07, M-LA08                          ← labor analytics
  M-BM06, M-IV08, M-SP09                  ← all analytics
  ─────────────────────────────────────────
  Fleet LEARNS and IMPROVES
                    ↓
WAVE 5: SCALE (dual GPU + advanced)
  M-MU05, M-MU06, M-MU08                  ← hardware scaling
  M-BR05–M-BR08                           ← advanced routing
  M-BM05                                  ← UI controls
  ─────────────────────────────────────────
  Fleet operates NEAR-INDEPENDENTLY
```

---

## Integration with Existing Operational Readiness

The remaining items (#17-21) from STATUS-TRACKER integrate as follows:

```
#17: Execute one real task end-to-end     ← Can start NOW (parallel with Wave 1)
#18: PM first heartbeat with Plane        ← Can start NOW (parallel with Wave 1)
#19: AICP Stage 1 complete                ← Feeds into Wave 4 (model evaluation)
#20: Fleet 24h observation                ← Should happen AFTER Wave 1 (with storm protection)
#21: Resume autonomous flow               ← Should happen AFTER Wave 1 (with storm protection)
```

**Critical sequencing:** Do NOT resume autonomous flow (#21) without
Wave 1 complete. The March catastrophe happened during autonomous
operation without storm protection. Wave 1 IS the prerequisite for
safe autonomous operation.

---

## Integration with LocalAI Independence Stages

| LocalAI Stage | Wave | Milestones |
|---------------|------|-----------|
| Stage 1: Make functional (current) | Wave 4 | M-MU01-02 (evaluate + configs) |
| Stage 2: Route simple operations | Wave 2 | M-BR01-04 (routing engine) |
| Stage 3: Progressive offload | Wave 4 | M-MU03-04 (shadow route + promote) |
| Stage 4: Reliability and failover | Wave 2+5 | M-SP05 + M-BR03 + M-MU08 |
| Stage 5: Near-independent | Wave 5 | All milestones converge |

---

## Integration with Fleet Elevation

The 31 Fleet Elevation design documents describe the target state.
The new milestones provide the **infrastructure** that makes elevation
possible:

| Elevation Doc | Enabled By |
|---------------|-----------|
| Doc 4: The Brain | M-SP (storm checks in cycle), M-BM (budget-aware dispatch) |
| Doc 17: Standards | M-LA (labor stamp is a new artifact standard) |
| Doc 19: Flow Validation | M-IV (challenge loops are new quality gates) |
| Doc 23: Agent Lifecycle | M-BM (budget mode affects sleep/wake), M-LA (stamps track cost-per-state) |

---

## Success Criteria Per Wave

### Wave 1 is DONE when:
- [ ] Storm monitor detects session bursts and fast-climb
- [ ] Automatic response de-escalates to survival mode on 3+ indicators
- [ ] Per-agent circuit breakers isolate void-session agents
- [ ] Gateway duplication detected and cleaned automatically
- [ ] Every fleet_task_complete produces a LaborStamp
- [ ] Every PR carries model + confidence tier in references
- [ ] Every completion comment shows labor attribution table
- [ ] Budget modes defined and model selection respects them
- [ ] All new code has tests
- [ ] 24h observation with storm protection active

### Wave 2 is DONE when:
- [ ] Backend registry contains Claude, LocalAI, OpenRouter
- [ ] Router picks cheapest capable backend per task
- [ ] Fallback chain works (LocalAI down → OpenRouter → Claude)
- [ ] Budget mode auto-transitions on quota pressure
- [ ] `fleet budget` CLI shows mode, quota, cost breakdown
- [ ] Trainee-tier work gets flagged for extra review
- [ ] Session metrics (tokens, duration, cost) tracked
- [ ] Diagnostic snapshot captured on WARNING+ storms

### Wave 3 is DONE when:
- [ ] Automated challenges generated from diffs (free, no LLM)
- [ ] Agent challenges assigned to different-role reviewer
- [ ] Cross-model challenges use different backend
- [ ] Scenario challenges reproduce + vary bug conditions
- [ ] Challenge results tracked in task custom fields
- [ ] Readiness progression: 70% (work done) → 80% (challenge passed)
- [ ] Deferred challenge queue for budget-constrained skips
- [ ] Post-incident reports generated automatically

### Wave 4 is DONE when:
- [ ] Qwen3-8B benchmarked against hermes-3b on fleet prompts
- [ ] Shadow routing validates quality in production
- [ ] PO promotes Qwen3-8B from trainee to standard for specific tasks
- [ ] Analytics dashboards: cost/agent, cost/model, cost/tier
- [ ] Heartbeat cost trends visible and alerting
- [ ] Challenge pass rates tracked per agent per tier

### Wave 5 is DONE when:
- [ ] Dual GPU running two models simultaneously
- [ ] Cluster peering between two machines
- [ ] Codex CLI runs adversarial reviews on PRs
- [ ] Backend health dashboard in OCMC
- [ ] Budget mode selector in OCMC header bar
- [ ] AICP and fleet share routing engine
- [ ] Fleet operates 80%+ on local/free backends

---

## The Path to Excellence

```
TODAY: 128 milestones implemented, fleet protected but not intelligent
  ↓
WAVE 1: Fleet is SAFE — storms detected, labor tracked, budget controlled
  ↓
WAVE 2: Fleet is SMART — routes to cheapest backend, adjusts automatically
  ↓
WAVE 3: Fleet is RIGOROUS — work challenged adversarially, bugs caught early
  ↓
WAVE 4: Fleet is LEARNING — better models, data-driven decisions, improving
  ↓
WAVE 5: Fleet is INDEPENDENT — dual GPU, cluster peered, near-autonomous
  ↓
TARGET: 2 clusters, 2-3 fleets, 80%+ local, Claude for reasoning only
         Every artifact traceable. Every cost justified. Every bug caught.
         Economic. Independent. Excellent.
```