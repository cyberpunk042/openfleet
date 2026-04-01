# Model Management — Select, Benchmark, Promote, Track

> **9 files. 1767 lines. Progressive model upgrade from hermes-3b to better local models.**
>
> Selects the right model per task complexity and budget. Benchmarks
> candidates against fleet-specific prompts. Shadow-routes tasks to
> production + candidate simultaneously. Promotes when shadow results
> reach 80% upgrade-worthy. Tracks confidence tiers per model per
> task type. Future modules for dual GPU, TurboQuant, cluster peering.

---

## 1. Why It Exists

hermes-3b (3B) was the right choice when it was chosen. Better models
exist now (Qwen 2.5 7B, DeepSeek R1 8B). The model management system
provides a safe upgrade path: benchmark → shadow route → promote →
monitor — without risking fleet quality during the transition.

## 2. How It Works

### 2.1 Model Selection

```
Task arrives with complexity + budget_mode
  ↓
model_selection.py evaluates:
  ├── Story points → complexity (SP≥8 = opus, SP≥5 = sonnet, SP<5 = sonnet/hermes)
  ├── Agent role (architect/devsecops → higher tier)
  ├── Budget constraint (economic blocks opus, frugal blocks all Claude)
  └── Explicit override (task has model field set)
  ↓
Returns: ModelConfig(model, effort, reason)
  ↓
Budget constrains: constrain_model_by_budget() from budget_modes
```

### 2.2 Shadow Routing

```
ShadowRouter(production="hermes-3b", candidate="qwen3-8b")
  ↓
For each task: run on BOTH models
  ↓
ShadowResult: production_passed, candidate_passed, responses_agree,
              production_latency, candidate_latency
  ↓
Track: agreement_rate, candidate_pass_rate, upgrade_worthy_rate
  ↓
upgrade_worthy_rate ≥ 80% → READY verdict
  ↓
PO decides to promote (promote_from_shadow — W4 wiring)
```

### 2.3 Promotion Lifecycle

```
ModelPromotionManager(current_default="hermes-3b")
  ↓
promote_from_shadow("qwen3-8b", shadow_router)
  ↓
PromotionRecord: shadow_comparisons, agreement_rate,
                 pre_promotion_approval_rate
  ↓
routing_model() returns "qwen3-8b" for router (W6 wiring)
  ↓
Monitor: promotion_health() compares pre vs post approval rates
  ├── healthy: post ≥ 90% of pre
  ├── degraded: post ≥ 70% of pre
  └── unhealthy: post < 70% → rollback()
```

### 2.4 Tier Progression

```
4 tiers: trainee → trainee-validated → standard → expert

TierProgressionTracker:
  Per model, per task type:
    approval_rate, challenge_pass_rate
  
  Readiness signals:
    trainee → trainee-validated: 70% approval, 10+ samples
    trainee-validated → standard: 85% approval, 10+ samples
    standard → expert: PO decision only
```

W7 wiring: codex_review imports VALID_TIERS, adds trainee-validated to review trigger.

## 3. File Map

```
fleet/core/
├── model_selection.py     Task→model mapping, budget constraints    (190 lines)
├── model_configs.py       6 LocalAI model YAML configs in code      (225 lines)
├── model_benchmark.py     Fleet-specific benchmark prompts           (258 lines)
├── model_promotion.py     Promote/rollback lifecycle, health         (305 lines)
├── tier_progression.py    Per-model per-task approval tracking       (353 lines)
├── shadow_routing.py      Dual-route comparison, upgrade verdict     (310 lines)
├── dual_gpu.py            FUTURE: 8GB+11GB GPU config               (78 lines)
├── turboquant.py          FUTURE: KV cache 6x compression           (48 lines)
└── cluster_peering.py     FUTURE: multi-machine failover            (varies)
```

## 4. Key Functions

| Module | Function | What It Does |
|--------|----------|-------------|
| model_selection | `select_model(task, budget_mode, agent)` | Pick model by complexity+budget+role |
| model_configs | `ModelConfig` registry | 6 models with GGUF, stop tokens, GPU layers |
| model_benchmark | `evaluate_response()`, `compare_models()` | Benchmark against fleet prompts |
| shadow_routing | `ShadowRouter.record()`, `format_report()` | Track shadow results, READY/NOT READY |
| model_promotion | `promote_from_shadow()`, `rollback()`, `promotion_health()` | Lifecycle with shadow data (W4) |
| tier_progression | `set_tier()`, `tier_readiness()` | Per-model tier tracking, readiness signals |

## 5. Consumers

Backend router (model selection), codex review (tier→review trigger W7), labor stamps (model recorded), budget (constrains models).

## 6. Design Decisions

**Why shadow routing before promotion?** Promotion without evidence is gambling. Shadow routing provides quantitative evidence (agreement rate, pass rate) before the PO decides.

**Why 4 tiers?** trainee→trainee-validated→standard→expert maps to growing trust. New models start as trainee (needs validation), earn validated (proven on simple tasks), then standard (proven on most tasks). Expert is PO-granted only.

**Why PO decides promotions?** Model promotion affects fleet quality globally. This is not an agent decision. The system provides data (shadow report), the PO decides.

## 7. Test Coverage: **130 tests** across 6 modules.

## 8. What's Needed

- Run REAL benchmarks (model_benchmark.py against actual LocalAI)
- Add Qwen 2.5 models to registry
- Shadow routing live test with real inference
- Dual GPU config when hardware arrives
- KV cache quantization already applied (M-MO01 done)
