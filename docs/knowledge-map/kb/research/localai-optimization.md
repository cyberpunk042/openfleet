# LocalAI Optimization — Complete Research Findings

**Type:** Research Finding
**Date:** 2026-04-03
**Sources:** 5 research agents covering LocalAI YAML settings, llama.cpp tuning, docker env vars, LightRAG extraction, supplemental infrastructure

## Root Causes Found

### Context Size / LLAMACPP_PARALLEL Interaction

LocalAI divides total CONTEXT_SIZE by LLAMACPP_PARALLEL slots. With PARALLEL=4 and CONTEXT=8192, each slot only gets 2048 tokens — too small for LightRAG's entity extraction prompts (~4000 tokens).

**Fix:** PARALLEL=2, CONTEXT=16384 → 8192 per slot.

### context_size YAML Location

LocalAI silently ignores `context_size` under `parameters:`. It MUST be at root level in the model YAML. The `CONTEXT_SIZE` env var is a global fallback when models don't specify their own.

### Temperature Override Chain

LightRAG sends `OPENAI_LLM_TEMPERATURE` in the API request body. LocalAI uses the request value over the YAML config. We had YAML temperature=0.1 but LightRAG was overriding it to 0.3 — causing random extraction results.

### Seed Randomness

`seed: -1` in model YAML = random seed every request. Combined with temperature 0.3, same document produced 32/0, 15/7, 21/21, 10/3 (entities/relationships) across runs.

**Fix:** seed=42 + temperature=0.0 = deterministic output.

### batch vs batch_size

LocalAI reads `batch` under `parameters:`, NOT `batch_size` at root. The root-level `batch_size` was silently ignored — nomic-embed embedding model still used default 512, causing "input too large" errors.

### mirostat Default

Some LocalAI versions default mirostat ON — causes massive speed penalty. Must explicitly set `mirostat: 0`.

## Model YAML Settings (101 documented)

### Root Level (LLMConfig)

context_size, threads, gpu_layers, f16, embeddings, reranking, batch_size (WRONG — use batch under parameters), mmap, mlock, low_vram, no_kv_offloading, no_mul_mat_q, numa, main_gpu, tensor_split, seed (WRONG — use under parameters), vocab_only, mmproj, lora_adapter, draft_model, flash_attention, cache_type_k, cache_type_v, prompt_cache_path, prompt_cache_all, prompt_cache_ro, rope_freq_base, rope_freq_scale

### Parameters Section

model, temperature, top_p, top_k, min_p, max_tokens, repeat_penalty, frequency_penalty, presence_penalty, batch, seed, typical_p, tfs_z, mirostat, mirostat_eta, mirostat_tau, penalize_nl, n_keep, ignore_eos, logit_bias

### Function Calling

function.parallel_calls, function.mixed_mode, grammar, grammar_json

### KV Cache Quantization

q4_0: 4x VRAM savings, slight quality loss at long context
q8_0: 2x VRAM savings, negligible quality loss
f16: baseline (default)

### Our Optimized Settings (via optimize-models.sh IaC)

| Setting | Value | Why |
|---------|-------|-----|
| context_size | 16384 (root) | 8192 per PARALLEL=2 slot |
| temperature | 0.0 hermes, 0.2 hermes-3b | Deterministic extraction |
| top_p | 0.85 | Tighter sampling |
| top_k | 40 | Reduce noise |
| min_p | 0.05 | Filter low-probability tokens |
| repeat_penalty | 1.1 | Prevent loops |
| mirostat | 0 | Disable speed penalty |
| max_tokens | 4096 | Enough for entities + relationships |
| batch | 2048 (under parameters) | Faster prompt ingestion |
| seed | 42 | Deterministic |
| gpu_layers | 32 | Full GPU offload (fits 8GB with q4_0 KV) |
| threads | 2 | Minimal CPU with full GPU offload |
| cache_type_k/v | q4_0 | 4x VRAM savings |
| flash_attention | true | Required for KV cache quant |
| mmap | true | Faster model loading |
| prompt_cache_all | true | Cache system prompts |

## Docker Environment Variables

| Var | Value | Why |
|-----|-------|-----|
| LLAMACPP_PARALLEL | 2 | Context divided by slots |
| CONTEXT_SIZE | 16384 | 8192 per slot |
| LOCALAI_PARALLEL_REQUESTS | true | Required for PARALLEL to work |
| LOCALAI_SINGLE_ACTIVE_BACKEND | false | Need LLM + embedding simultaneously |
| LOCALAI_MAX_ACTIVE_BACKENDS | 3 | LRU: hermes + nomic-embed + bge-reranker |
| LOCALAI_WATCHDOG_BUSY_TIMEOUT | 10m | Longer for LightRAG extraction |

## Relationships

- APPLIED TO: models/hermes.yaml, models/hermes-3b.yaml, models/nomic-embed.yaml, all model configs
- APPLIED VIA: scripts/optimize-models.sh (IaC — idempotent)
- CONNECTS TO: LightRAG extraction (entity/relationship quality depends on these settings)
- CONNECTS TO: AICP docker-compose.yaml (LocalAI environment)
- CONNECTS TO: kb/infrastructure/lightrag.md (LightRAG configuration)
