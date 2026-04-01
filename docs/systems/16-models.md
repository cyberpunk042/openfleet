# System 16: Model Management

**Source:** `fleet/core/model_selection.py`, `fleet/core/model_configs.py`, `fleet/core/model_benchmark.py`, `fleet/core/model_promotion.py`, `fleet/core/tier_progression.py`
**Status:** 🔨 Unit tests (130). KV cache optimization applied. No real benchmarks run.
**Design docs:** `model-upgrade-path.md` (M-MU01-08)

---

## Purpose

Select, benchmark, shadow-route, promote, and track confidence tiers for LocalAI models. Progressive upgrade path: hermes-3b → Qwen3-8B → future 14B models. PO decides promotions — this system provides data.

## Key Concepts

### Model Selection (model_selection.py)

Selects model based on task complexity, budget mode, agent type. Budget mode constrains (via `constrain_model_by_budget`). Architect/security agents get higher-tier models.

### Model Configs (model_configs.py)

Registry of 6 LocalAI models with GGUF configs, stop tokens, chat templates, GPU layers. Models: hermes-3b, hermes, qwen3-8b, phi-4-mini, llama-3.3-8b, deepseek-r1-8b.

### Shadow Routing (shadow_routing.py)

Dual-route tasks: production model + candidate model. Compare outputs. `ShadowRouter` tracks agreement_rate, candidate_pass_rate, upgrade_worthy_rate. Promotion verdict at 80% threshold.

### Model Promotion (model_promotion.py)

`ModelPromotionManager`: promote/rollback with shadow data. `promote_from_shadow(model, shadow)` captures comparison stats (W4 wiring). `routing_model()` returns current default for router (W6 wiring). Health monitoring compares pre vs post approval rates.

### Tier Progression (tier_progression.py)

4 tiers: trainee → trainee-validated → standard → expert. Per-model per-task-type approval rates. Readiness thresholds: 70% for validation, 85% for standard, min 10 samples. PO decides promotions.

### FUTURE Modules

- `dual_gpu.py` — GPUSlot, DualGPUConfig (schema only, needs hardware)
- `turboquant.py` — KV cache 6x compression (schema only, needs ecosystem)
- `cluster_peering.py` — multi-machine failover (schema only, needs Machine 2)

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Backend Router** | Model selection feeds routing decision | Models → Router |
| **Backend Router** | Promoted model enters routing table (W6) | Promotion → Router |
| **Shadow Routing** | Shadow results feed promotion decisions (W4) | Shadow → Promotion |
| **Tier Progression** | Tier drives codex review trigger (W7) | Tier → Review |
| **Labor Stamps** | Model recorded in stamp | Models → Stamps |
| **Budget** | Budget constrains allowed models | Budget → Models |
| **LocalAI** | Models run on LocalAI via GGUF configs | Models → LocalAI |

## What's Needed

- [ ] Run real benchmarks (model_benchmark.py against actual LocalAI)
- [ ] Add Qwen 2.5 models to registry
- [ ] Shadow routing live test with real inference
- [ ] Dual GPU config when hardware arrives
