# System 16: Model Management — Select, Benchmark, Shadow, Promote, Track

**Type:** Fleet System
**ID:** S16
**Files:** model_selection.py, model_configs.py, model_benchmark.py, model_promotion.py, shadow_routing.py, tier_progression.py + future: cluster_peering.py, dual_gpu.py, turboquant.py
**Total:** 1,767 lines (9 modules)
**Tests:** 130

## What This System Does

Full lifecycle for local AI models: SELECT the right model per task (SP + type + role → model/effort), BENCHMARK candidates against fleet-specific prompts (not generic benchmarks), SHADOW ROUTE to production + candidate simultaneously (dual-run comparison), PROMOTE when 80%+ upgrade-worthy, MONITOR post-promotion (auto-rollback if <70% baseline), TRACK confidence tier progression per model per task type (trainee → trainee-validated → standard → expert).

Provides a SAFE upgrade path — no blind promotions. PO sees shadow evidence before deciding.

## Model Selection at Dispatch

```
select_model_for_task(task, agent_name):
  SP≥8 or epic        → opus (complex)
  SP≥5 or blocker      → sonnet (substantial)
  architect/devsecops   → always higher tier (never free)
  SP<5 standard         → sonnet or hermes (when LocalAI routed)
```

## Tier Progression

Per model per task type: trainee → trainee-validated (70% approval rate, 10+ samples) → standard (85%, 10+) → expert (PO decision only). Tier drives challenge depth and review pipeline.

## Current Models (LocalAI)

| Model | Size | Cold Start | Use Case |
|-------|------|-----------|----------|
| hermes-3b | 2.0GB | ~10s | Fleet heartbeats (target) |
| hermes 7B | 4.4GB | ~80s | Complex reasoning |
| codellama 7B | 4.4GB | ~80s | Code tasks |
| phi-2 2.7B | 1.6GB | fast | CPU fallback |

Recommended upgrade: Qwen3.5-4B (replace hermes-3b), Qwen3.5-9B (primary workhorse). Neither configured yet.

## Future Modules (Schema Only)

- dual_gpu.py — 8GB+11GB, two models simultaneously
- turboquant.py — TurboQuant KV cache compression (6x, Q3 2026 in llama.cpp)
- cluster_peering.py — Machine 1 ↔ Machine 2 failover

## Relationships

- CALLED BY: dispatch.py (model selection at dispatch)
- CONSUMED BY: S14 router (model from selection → routing decision)
- CONSUMED BY: S13 labor (model in LaborStamp)
- FEEDS: tier_progression → S15 challenge (tier determines depth)
- CONNECTS TO: S12 budget (cost per model)
- CONNECTS TO: LocalAI (GPU management, single-active-backend)
- NOT YET DONE: Qwen models not configured, real benchmarks never run, shadow routing untested

## For LightRAG Entity Extraction

Key entities: ModelSelection (model+effort per task), ModelConfig (6 LocalAI configs), BenchmarkResult, ShadowResult (upgrade_worthy), PromotionRecord, TierRecord (trainee→validated→standard→expert).
