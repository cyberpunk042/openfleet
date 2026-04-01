# Model Management — Select, Benchmark, Shadow, Promote, Track

> **9 files. 1767 lines. Progressive model upgrade path for LocalAI independence.**
>
> The model management system handles the entire lifecycle of local AI
> models: select the right model per task, benchmark candidates against
> fleet-specific prompts, shadow-route tasks to production + candidate
> simultaneously, promote when evidence shows readiness, track confidence
> tiers per model per task type, and roll back if post-promotion quality
> degrades. Future modules for dual GPU (19GB), TurboQuant (6x KV cache
> compression), and cluster peering (multi-machine failover).

---

## 1. Why It Exists

The fleet's LocalAI independence mission requires progressively better
local models. hermes-3b (3B) was the right starting choice but better
options exist now. The model management system provides a SAFE upgrade
path — no blind promotions, no quality regressions:

```
UNSAFE: "Qwen3-8B seems good" → swap → hope it works → find out in production

SAFE:   benchmark(Qwen3-8B, fleet_prompts) → quality data
        → shadow_route(production=hermes-3b, candidate=Qwen3-8B) → comparison data
        → 80% upgrade-worthy → PO reviews evidence → promote()
        → monitor post-promotion approval rates → healthy? keep. degraded? rollback()
```

### PO Requirements (Verbatim)

> "we need to think of plugins in general for claude code and things
> we might wanna also try to bring to LocalAI later"

> "this is a field evolving fast and I think there is even a very recent
> size compression breakthrough that might have start to hit the community."

---

## 2. How It Works

### 2.1 The Full Model Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│                MODEL LIFECYCLE                            │
│                                                           │
│  1. CONFIGURE                                             │
│     model_configs.py: GGUF file, stop tokens, GPU layers  │
│     models/*.yaml: LocalAI model YAML configs             │
│     optimize-models.sh: KV cache quant, Flash Attn, etc.  │
│                                                           │
│  2. BENCHMARK                                             │
│     model_benchmark.py: fleet-specific prompts             │
│     ├── heartbeat prompt (structured response)            │
│     ├── task acceptance prompt (plan quality)              │
│     ├── review prompt (finding quality)                   │
│     └── structured JSON output prompt                     │
│     evaluate_response() → pass rate, compliance, latency  │
│     compare_models() → winner with delta percentages      │
│                                                           │
│  3. SHADOW ROUTE                                          │
│     shadow_routing.py: run task on BOTH models             │
│     ShadowResult: both passed? agree? who's faster?       │
│     ShadowRouter: track agreement_rate, pass_rates         │
│     upgrade_worthy_rate ≥ 80% → READY verdict             │
│                                                           │
│  4. PROMOTE (PO decides based on shadow evidence)          │
│     model_promotion.py: promote_from_shadow(model, shadow) │
│     PromotionRecord: shadow data + pre-promotion baseline  │
│     routing_model() → router uses promoted model (W6)      │
│                                                           │
│  5. MONITOR                                               │
│     promotion_health(): compare pre vs post approval rates │
│     healthy (≥90% of baseline) → keep                     │
│     degraded (≥70%) → warning                             │
│     unhealthy (<70%) → rollback()                         │
│                                                           │
│  6. TIER PROGRESSION                                      │
│     tier_progression.py: per-model per-task-type tracking  │
│     trainee → trainee-validated (70% approval, 10+ samples)│
│     trainee-validated → standard (85% approval, 10+ samples)│
│     standard → expert (PO decision only)                  │
│     Tier drives: challenge depth, codex review trigger (W7)│
└──────────────────────────────────────────────────────────┘
```

### 2.2 Model Selection at Dispatch Time

```
Task arrives with story_points, task_type, agent_name, budget_mode
  ↓
model_selection.py evaluates:
  ├── SP ≥ 8 or type=epic/blocker → opus (complex reasoning needed)
  ├── SP ≥ 5 or type=story → sonnet (standard reasoning)
  ├── SP < 5 or type=task/subtask → sonnet or hermes (simpler work)
  ├── architect/devsecops agent → higher tier (quality critical)
  └── Explicit model override on task → use that model
  ↓
Budget constrains (constrain_model_by_budget from budget_modes):
  economic → blocks opus → falls back to sonnet
  frugal/survival → blocks ALL Claude → caller routes to LocalAI
  ↓
Returns ModelConfig(model, effort, reason)
  ↓
Recorded in labor stamp → provenance chain
```

### 2.3 Shadow Routing

```
ShadowRouter(production_model="hermes-3b", candidate_model="qwen3-8b")

For each task:
  ├── Run on production model → production_response, latency, passed
  └── Run on candidate model → candidate_response, latency, passed
  ↓
ShadowResult:
  production_passed: True
  candidate_passed: True
  responses_agree: True (both contain expected output)
  candidate_faster: True (0.8s vs 1.0s)
  ↓
candidate_upgrade_worthy = candidate_passed AND responses_agree
  ↓
ShadowRouter tracks across many comparisons:
  agreement_rate: 92%       (how often they agree)
  candidate_pass_rate: 88%  (how often candidate passes alone)
  upgrade_worthy_rate: 85%  (passed AND agree)
  by_task_type: {"task": 90%, "story": 78%}  (per-type breakdown)
  ↓
format_report():
  "Total comparisons: 50"
  "Agreement rate: 92%"
  "Upgrade-worthy rate: 85%"
  "Verdict: READY"  (≥80% upgrade-worthy)
```

### 2.4 Promotion with Evidence

```
PO sees shadow report → decides to promote
  ↓
mgr = ModelPromotionManager(current_default="hermes-3b")
record = mgr.promote_from_shadow("qwen3-8b", shadow_router)
  ↓
PromotionRecord:
  promoted_model: "qwen3-8b"
  previous_model: "hermes-3b"
  shadow_comparisons: 50
  shadow_agreement_rate: 0.92
  pre_promotion_approval_rate: 0.85 (hermes-3b's rate before promotion)
  ↓
mgr.routing_model() returns "qwen3-8b"
  → router uses this for localai_model parameter (W6 wiring)
  ↓
Post-promotion monitoring:
  mgr.promotion_health():
    post_rate = approval_rate since promotion
    pre_rate = pre_promotion_approval_rate
    
    post ≥ 90% of pre → "healthy"
    post ≥ 70% of pre → "degraded" (warning)
    post < 70% of pre → "unhealthy" → trigger rollback()
```

### 2.5 Confidence Tiers

```
4 tiers per model, tracked per task type:

trainee            → needs validation. Mandatory challenge. 3 rounds.
                      Threshold to advance: 70% approval, 10+ samples.

trainee-validated  → proven on simple tasks. Still needs challenge.
                      Threshold: 85% approval, 10+ samples.
                      Codex review triggered (W7 wiring).

standard           → proven on most tasks. Challenge recommended for SP≥5.
                      Threshold: PO decision.

expert             → trusted. Challenge optional. PO-granted only.
                      No automatic promotion to expert.

TierProgressionTracker:
  Per model, per task type:
    record_result(model, task_type, approved)
    approval_rate(model, task_type)
    tier_readiness(model) → per-task-type breakdown
    performance_window(model, hours) → recent trend
```

---

## 3. File Map

```
fleet/core/
├── model_selection.py    Task→model mapping, budget constraints       (190 lines)
├── model_configs.py      6 LocalAI model configs (GGUF, GPU, templates) (225 lines)
├── model_benchmark.py    Fleet-specific benchmarks, evaluation         (258 lines)
├── shadow_routing.py     Dual-route comparison, upgrade verdict        (310 lines)
├── model_promotion.py    Promote/rollback lifecycle, health monitoring (305 lines)
├── tier_progression.py   Per-model per-task-type tier tracking         (353 lines)
├── dual_gpu.py           FUTURE: 8GB+11GB GPU slot management          (78 lines)
├── turboquant.py         FUTURE: KV cache 6x compression calcs        (48 lines)
└── cluster_peering.py    FUTURE: multi-machine model failover          (varies)
```

Total: **1767 lines** across 9 modules (6 active + 3 future).

---

## 4. Per-File Key Functions

### 4.1 `model_selection.py` (190 lines)

| Function | What It Does |
|----------|-------------|
| `select_model(task, budget_mode, agent)` | Pick model by SP + type + agent role. Budget constrains via `constrain_model_by_budget()`. |
| `ModelConfig` | Dataclass: model name, effort level, selection reason. |

### 4.2 `model_configs.py` (225 lines)

6 model configs with: name, GGUF file, stop tokens, chat template, context size, GPU layers, temperature.

| Model | Size | GPU Layers | Use Case |
|-------|------|-----------|----------|
| hermes-3b | 2.0GB | 32 (full) | Heartbeats, simple structured |
| hermes (7B) | 4.4GB | 24 | Complex reasoning |
| qwen3-8b | ~5GB | 32 | Upgrade candidate (better quality) |
| phi-4-mini | ~3GB | varies | CPU fallback |
| llama-3.3-8b | ~5GB | 32 | Alternative 8B |
| deepseek-r1-8b | ~5GB | 32 | Reasoning specialist |

### 4.3 `model_benchmark.py` (258 lines)

| Function | What It Does |
|----------|-------------|
| `FLEET_BENCHMARKS` | 4 fleet-specific prompts: heartbeat, acceptance, review, structured output |
| `evaluate_response(response, expected)` | Check: expected strings present? JSON keys present? Latency acceptable? |
| `BenchmarkResult` | Per-prompt: passed, latency, compliance_score |
| `compare_models(results_a, results_b)` | Winner determination with delta percentages. Markdown report. |

### 4.4 `shadow_routing.py` (310 lines)

| Class/Function | What It Does |
|---------------|-------------|
| `ShadowResult` | Single comparison: both models' responses, agree?, faster?, upgrade_worthy? |
| `ShadowRouter` | Track many comparisons: agreement_rate, pass_rates, upgrade_worthy_rate, by_task_type |
| `format_report()` | Markdown report with READY/NOT READY verdict at 80% threshold |

### 4.5 `model_promotion.py` (305 lines)

| Class/Function | What It Does |
|---------------|-------------|
| `PromotionRecord` | promoted/previous model, shadow data, pre_promotion_approval_rate, rollback info |
| `ApprovalTracker` | Per-model approval rates, per-task-type breakdown |
| `ModelPromotionManager` | promote(), promote_from_shadow() (W4), rollback(), promotion_health(), routing_model() (W6) |

### 4.6 `tier_progression.py` (353 lines)

| Class/Function | What It Does |
|---------------|-------------|
| `VALID_TIERS` | ("trainee", "trainee-validated", "standard", "expert") |
| `TierProgressionTracker` | Per-model per-task-type: approval_rate, set_tier, tier_readiness, performance_window |

### 4.7 FUTURE Modules (schema only)

| Module | What It Will Do | Blocked By |
|--------|----------------|-----------|
| `dual_gpu.py` | GPUSlot(gpu_id, vram_mb), DualGPUConfig(8GB+11GB) | Second GPU hardware |
| `turboquant.py` | TurboQuantConfig(6x compression, extended context) | Ecosystem maturity |
| `cluster_peering.py` | ClusterNode, model availability across machines | Second machine |

---

## 5. Dependency Graph

```
model_selection.py    ← budget_modes (constrain_model_by_budget)
model_configs.py      ← standalone
model_benchmark.py    ← standalone
shadow_routing.py     ← standalone
model_promotion.py    ← shadow_routing (TYPE_CHECKING for ShadowRouter, W4)
tier_progression.py   ← standalone
dual_gpu.py           ← standalone (schema only)
turboquant.py         ← standalone (schema only)
cluster_peering.py    ← standalone (schema only)
```

Cross-system connections:
- W4: model_promotion.promote_from_shadow() accepts ShadowRouter
- W6: model_promotion.routing_model() → router's localai_model parameter
- W7: codex_review imports VALID_TIERS from tier_progression

---

## 6. Consumers

| Layer | Module | Connection |
|-------|--------|-----------|
| **Backend Router** | backend_router.py | Model selection feeds routing decision |
| **Backend Router** | W6 | routing_model() returns promoted model |
| **Codex Review** | W7 | VALID_TIERS drives review trigger for trainee-validated |
| **Labor Stamps** | labor_stamp.py | Model name recorded in stamp |
| **Budget** | budget_modes.py | Budget constrains allowed models |
| **Challenge** | — | Tier drives challenge depth (mandatory for trainee) |

---

## 7. Design Decisions

### Why shadow routing before promotion?

Promotion without evidence is gambling. Shadow routing provides
quantitative data: agreement rate, candidate pass rate, per-task-type
breakdown. The PO sees "85% upgrade-worthy across 50 comparisons"
not "it seems better." Evidence-based decisions.

### Why 4 tiers, not 2 (trusted/untrusted)?

The progression trainee → validated → standard → expert maps to
growing trust through evidence. A model that passes 70% on simple
tasks earns "validated" but shouldn't handle complex architecture
work yet. 2 tiers would lose this granularity.

### Why PO decides promotions, not automatic?

Model promotion affects EVERY agent. If a promoted model is worse,
the entire fleet degrades. This is too impactful for automatic
decisions. The system provides data (shadow report), the PO
reviews and decides. Automatic rollback is acceptable because
it's a SAFETY mechanism (quality degraded), not a strategic choice.

### Why per-task-type tier tracking?

A model might be excellent at heartbeats (simple structured output)
but terrible at code review (complex reasoning). Per-task-type
tracking reveals these differences. A model can be "standard" for
heartbeats but "trainee" for architecture tasks.

### Why benchmark with fleet-specific prompts?

Generic benchmarks (MMLU, HumanEval) don't predict fleet performance.
Fleet tasks are specific: structured JSON for heartbeats, conventional
commits, acceptance criteria evaluation. Fleet-specific benchmarks
test what the fleet actually needs.

---

## 8. Model Landscape (Updated April 2026)

### 8.1 What Fits 8GB VRAM Now

| Model | Size (Q4_K_M) | Strengths | Status |
|-------|---------------|-----------|--------|
| hermes-3b | 2.0GB | Fast, function calling trained | Current default |
| hermes (7B) | 4.4GB | Complex reasoning, Hermes 2 Pro | Configured |
| **Qwen3.5-4B** | **~2.5GB** | **15+ pts ahead of Qwen3-4B reasoning. Gated DeltaNet.** | **NOT configured** |
| **Qwen3.5-9B** | **~5GB** | **Best 9B available. MMLU-Pro 79.1%, GPQA 76.2%.** | **NOT configured** |
| Qwen3-8B | ~5GB | Strong general 8B | NOT configured |
| Qwen 2.5 7B | ~5GB | Strong instruction following | NOT configured |
| Qwen 2.5 Coder 7B | ~5GB | Best coding 8B | NOT configured |
| DeepSeek R1 8B | ~5GB | Strong reasoning (chain-of-thought, verbose) | NOT configured |

**Recommended upgrade path:**
1. **Qwen3.5-4B** as new default (replaces hermes-3b) — faster, smarter, 2.5GB leaves room for context
2. **Qwen3.5-9B** as primary workhorse — significantly better than any 7-8B model, fits 8GB at Q4_K_M
3. Keep **hermes (7B)** for function calling (Hermes 2 Pro still best for tool use)

### 8.2 Qwen3.5-Omni — NOT For Local

Qwen3.5-Omni (multimodal, omni-modal) is **PROPRIETARY** (API only).
Cannot be downloaded or run locally. Not relevant to LocalAI independence.
The open-source Qwen3-Omni-30B-A3B is too large for 8GB VRAM.

### 8.3 TurboQuant — Coming Q3 2026

Google Research, ICLR 2026. KV cache compression (NOT weight quantization):
- TQ4 (4-bit): **3.8x compression**, quality indistinguishable from FP16
- TQ3 (3-bit): **4.9x compression**, degrades on <8B models
- TurboQuant+ (community): **up to 6.4x compression**

**Impact for our 8GB VRAM:**
```
CURRENT (with our Q4_0 KV cache):
  Qwen3.5-9B Q4_K_M (~5GB weights) + Q4_0 KV → ~16-24K context

WITH TurboQuant TQ4 (when available):
  Qwen3.5-9B Q4_K_M (~5GB weights) + TQ4 KV → ~48-64K context
  
WITH TurboQuant+ TQ3:
  Qwen3.5-9B Q4_K_M (~5GB weights) + TQ3 KV → ~64-96K context
```

**Status:** NOT in llama.cpp main. Q3 2026 roadmap. Community forks
exist (`spiritbuun/llama-cpp-turboquant-cuda`). LocalAI will get it
automatically when llama.cpp merges. Our `turboquant.py` schema module
is ready for when this lands.

**We already applied Q4_0 KV cache quantization** (M-MO01) which gives
~4x KV compression. TurboQuant TQ4 would not replace this — it would
be a DIFFERENT approach to the same problem, potentially giving better
quality at similar compression or better compression at same quality.

### 8.4 RAM/VRAM Market

Global memory supply shortage (2024-2026). HBM for AI GPUs consuming
wafer capacity. Brief 22% dip after TurboQuant announcement but NOT
sustained. Earliest meaningful price relief: late 2027.

**Plan around current 8GB VRAM.** Techniques (quantization, KV cache
compression, TurboQuant when it lands) are more effective than waiting
for cheaper hardware.

### 8.5 Dual GPU (19GB)

Would enable: Qwen3.5-27B at Q4_K_M or Qwen3.5-9B at FP16.
Both massive quality jumps. Hardware dependent.

---

## 9. Data Shapes

### ShadowResult

```python
ShadowResult(
    task_id="T-42",
    task_type="task",
    production_model="hermes-3b",
    production_response="ok",
    production_latency_seconds=1.0,
    production_passed=True,
    candidate_model="qwen3-8b",
    candidate_response="ok",
    candidate_latency_seconds=0.8,
    candidate_passed=True,
    responses_agree=True,
    # candidate_upgrade_worthy = True (passed AND agree)
)
```

### PromotionRecord

```python
PromotionRecord(
    promoted_model="qwen3-8b",
    previous_model="hermes-3b",
    reason="Shadow routing: 85% upgrade-worthy",
    shadow_comparisons=50,
    shadow_agreement_rate=0.92,
    pre_promotion_approval_rate=0.85,
    rollback=False,
)
```

---

## 10. What's Needed

### Immediate
- **Add Qwen3.5-4B and Qwen3.5-9B** to config registry — GGUF available, Apache 2.0
- **Run REAL benchmarks** against actual LocalAI (model_benchmark.py exists, never run against real inference)
- **Shadow routing live test** — compare Qwen3.5-9B against hermes-3b on real fleet prompts

### Short-Term
- **Multi-model strategy in router:** Qwen3.5-4B for heartbeats (fast, tiny), Qwen3.5-9B for reasoning (smart), hermes for function calling (trained for it)
- **Monitor TurboQuant** llama.cpp integration (Q3 2026 roadmap) — when merged, update model YAMLs and context configs
- **Update turboquant.py** schema module with real TQ4/TQ3 parameters from paper

### Strategic
- **Dual GPU** when hardware arrives — Qwen3.5-27B at Q4_K_M or Qwen3.5-9B at FP16
- **Qwen3-Coder-30B-A3B** (MoE, 3B active) — evaluate if MoE models work well on 8GB with offloading

### Test Coverage: **130 tests** across 6 active modules + 21 for FUTURE schemas.
