# Model Upgrade Path — LocalAI Next-Gen

## Severity: STRATEGIC
## Status: DESIGN
## Created: 2026-03-31

A plan for upgrading LocalAI models to take advantage of 2025-2026
breakthroughs in small model performance and compression. This directly
serves the LocalAI independence mission — better local models mean more
offload from Claude, lower costs, and higher fleet autonomy.

---

## Part 1: PO Requirements (Verbatim)

> "we need to think of plugins in general for claude code and things we
> might wanna also try to bring to LocalAI later even if we know the
> hard limitation, even though normally soon 8GB+11GB Graphics."

> "this is a field evolving fast and I think there is even a very recent
> size compression breakthrough that might have start to hit the community."

---

## Part 2: Current LocalAI Model Inventory

| Model | Config | Size | VRAM | Cold Start | Warm | Use Case | Quality |
|-------|--------|------|------|------------|------|----------|---------|
| hermes (7B) | hermes.yaml | 4.4GB | GPU 24 layers | ~80s | ~1s | Complex reasoning | Moderate |
| **hermes-3b (3B)** | hermes-3b.yaml | 2.0GB | GPU 32 layers | ~10s | ~1.2s | **Fleet default** | Basic |
| codellama (7B) | codellama.yaml | 4.4GB | GPU | ~80s | ~1s | Code generation | Moderate |
| phi-2 (2.7B) | phi-2.yaml | 1.6GB | CPU only | fast | fast | Fallback | Basic |

**Constraint:** `LOCALAI_SINGLE_ACTIVE_BACKEND=true` — one GPU model at a time.
**VRAM:** 8GB (current), 19GB planned (8GB + 11GB).

---

## Part 3: Research Findings — What's Available Now

### Headline: Small Models Got Much Better

The landscape has shifted dramatically since the fleet's models were chosen.
Key developments:

- **Qwen3.5-9B** beats GPT-OSS-120B (a model 13x its size) on multiple benchmarks
- **Qwen3-30B-A3B** (MoE) delivers 30B intelligence with only 3B active parameters
- **Phi-4 (14B)** beats GPT-4o-mini on math (80.4% MATH) and code (82.6% HumanEval)
- **Google TurboQuant** (March 25, 2026) compresses KV caches 6x with zero accuracy loss

### Recommended Upgrades — 8GB VRAM

| Current | Replace With | Why | VRAM (Q4_K_M) | Expected Gain |
|---------|-------------|-----|---------------|---------------|
| hermes-3b (3B) | **Qwen3-8B** | 2.5x larger, far better reasoning | ~5-6GB | Major quality jump for fleet default |
| hermes-3b (3B) | **Llama 3.3 8B** | Best all-rounder at this size | ~5-6GB | Strong alternative to Qwen3-8B |
| codellama (7B) | **Qwen3-8B** | Qwen3 is good at code too, avoids model swap | ~5-6GB | One model handles both general + code |
| phi-2 (2.7B) | **Phi-4-mini (3.8B)** | Same family, much better, 128K context | ~2-3GB | Better CPU fallback |

**Top recommendation for 8GB:** Replace hermes-3b with **Qwen3-8B** as
the fleet default. It fits comfortably in 8GB VRAM and is a generational
leap in reasoning quality. If Qwen3-8B can handle heartbeats, simple
reviews, AND some structured reasoning, the offload from Claude increases
dramatically.

### Recommended Upgrades — 19GB VRAM (8GB + 11GB)

| Slot | Model | Why | VRAM | Role |
|------|-------|-----|------|------|
| GPU 1 (8GB) | **Qwen3-8B** | Fleet default, always loaded | ~5-6GB | Heartbeats, simple tasks, structured responses |
| GPU 2 (11GB) | **Phi-4 (14B)** | Math/code specialist | ~8-10GB | Code reviews, technical analysis |
| GPU 2 alt | **Qwen3-30B-A3B** (MoE) | 30B quality, 3B compute | ~14-18GB Q3 | Complex reasoning (partial offload) |
| CPU fallback | **Phi-4-mini (3.8B)** | 128K context, edge-class | ~2-3GB | Emergency fallback |

**With 19GB:** Two models simultaneously = no swap penalty for common
cases. GPU 1 handles routine fleet operations, GPU 2 handles specialized
tasks. Model swaps only happen on GPU 2, and only for rare cases.

### Reasoning Models

| Model | Params | VRAM (Q4) | Special Capability |
|-------|--------|-----------|-------------------|
| **DeepSeek R1 8B** (distilled) | 8B | ~5-6GB | Chain-of-thought reasoning |
| **Qwen3-8B** (thinking mode) | 8B | ~5-6GB | Built-in reasoning toggle |

DeepSeek R1 8B is interesting for adversarial challenge use:
a local model that does chain-of-thought reasoning to challenge work
produced by Claude. Free, local, reasonable quality.

---

## Part 4: Compression Breakthroughs — Impact Assessment

### Google TurboQuant (March 25, 2026)

**What:** Compresses KV caches to 3 bits, NO retraining, NO accuracy loss.
6x memory reduction for KV cache, 8x attention speedup.

**Impact on fleet:**
- hermes-3b with 8192 context → could handle ~49K context in same VRAM
- Qwen3-8B with 8192 context → could handle ~49K context
- This means agents can receive MUCH larger context without running out of VRAM
- Reduces "model doesn't have enough context" as a reason to escalate to Claude

**Availability:** Research paper published, implementations expected in
llama.cpp/GGUF ecosystem within weeks-months. Watch for GGUF builds
with TurboQuant support.

**Action:** Monitor llama.cpp releases. When TurboQuant lands in GGUF,
rebuild model configs with extended context windows.

### Microsoft BitNet (2025-2026)

**What:** 1-bit quantization (ternary: -1, 0, +1). 0.4GB for 2B model.
100B model on CPU at human reading speed.

**Impact on fleet:**
- Currently only one public model: BitNet b1.58-2B-4T (MIT license)
- Models must be NATIVELY trained in 1-bit (can't convert existing)
- If ecosystem grows: a 100B BitNet model on CPU would change everything
- For now: watch, don't adopt

**Action:** Track BitNet model releases. If a 7B+ BitNet model appears
with competitive quality, it could replace the CPU fallback entirely.

### Standard GGUF Quantization

**State of the art:**
- Q4_K_M remains the sweet spot (75% VRAM reduction, 2-5% quality loss)
- Q3_K_M for tighter VRAM (85% reduction, 5-8% quality loss)
- Q2_K for extreme compression (90% reduction, 10-15% quality loss)

**For Qwen3-30B-A3B on 19GB VRAM:**
- Q4_K_M: ~18GB → tight fit, may need partial CPU offload
- Q3_K_M: ~14GB → fits comfortably on GPU 2 (11GB) + some CPU
- Q2_K: ~11GB → fits on GPU 2 alone, but quality drops

---

## Part 5: Model Config Templates

### Qwen3-8B (Fleet Default Upgrade)

```yaml
# models/qwen3-8b.yaml
name: qwen3-8b
backend: llama-cpp
parameters:
  model: qwen3-8b-q4_k_m.gguf
  temperature: 0.2
  top_p: 0.9
  top_k: 40
  context_size: 8192
  gpu_layers: 33      # Full GPU offload for 8GB VRAM
  threads: 4
  repeat_penalty: 1.1
  stop:
    - "<|im_end|>"
    - "<|endoftext|>"
template:
  chat_message: |
    <|im_start|>{{.RoleName}}
    {{.Content}}<|im_end|>
  chat: |
    {{.Input}}
    <|im_start|>assistant
```

### Phi-4-mini (CPU Fallback Upgrade)

```yaml
# models/phi-4-mini.yaml
name: phi-4-mini
backend: llama-cpp
parameters:
  model: phi-4-mini-q4_k_m.gguf
  temperature: 0.2
  context_size: 8192     # Supports up to 128K but limit for CPU
  gpu_layers: 0          # CPU only
  threads: 4
```

---

## Part 6: Migration Strategy

### Phase 1: Evaluate (non-disruptive)

1. Download Qwen3-8B Q4_K_M GGUF
2. Create model config YAML
3. Test on LocalAI alongside existing models
4. Benchmark: latency, quality, structured output compliance
5. Compare hermes-3b vs Qwen3-8B on fleet-representative prompts:
   - Heartbeat response (HEARTBEAT_OK)
   - Task acceptance (structured plan)
   - Simple review (pass/fail detection)
   - Structured JSON output
6. **No production change yet**

### Phase 2: Shadow Route (validate in production)

1. Router sends tasks to BOTH hermes-3b and Qwen3-8B
2. Compare outputs (quality, latency, structured compliance)
3. Record comparison in labor stamps (shadow model results)
4. After N successful shadow comparisons → confidence builds

### Phase 3: Promote (switch default)

1. Update `config/fleet.yaml`: `fleet_model: qwen3-8b`
2. Update backend registry: default LocalAI model = qwen3-8b
3. hermes-3b remains available as fallback
4. Monitor: approval rates for qwen3-8b work vs hermes-3b historical

### Phase 4: Expand (19GB VRAM)

1. Second GPU online → dual model loading
2. GPU 1: Qwen3-8B (always loaded)
3. GPU 2: Phi-4 or Qwen3-30B-A3B (loaded on demand)
4. Router knows which models are on which GPU → no unnecessary swaps
5. LocalAI cluster peering config (Machine 1 ↔ Machine 2)

---

## Part 7: Confidence Tier Progression

As local models improve, their confidence tier should evolve:

```
Stage 1 (now): hermes-3b = trainee (all LocalAI work needs extra review)
Stage 2 (after evaluation): Qwen3-8B = trainee (better but still unproven)
Stage 3 (after shadow routing): Qwen3-8B = trainee-validated
    (passes X% of challenges → earning trust)
Stage 4 (after N successful reviews): Qwen3-8B = standard (for specific task types)
    (PO decision to promote based on approval rate data)
```

**The PO decides when to promote.** The fleet tracks the data.
The labor attribution system provides the evidence (approval rates
per model per task type). The PO reviews the evidence and says
"Qwen3-8B is now standard tier for heartbeats and simple reviews."

This is the **training notion**: models start as trainees, earn
trust through observed performance, and get promoted by the PO.

---

## Part 8: Milestones

### M-MU01: Qwen3-8B Evaluation
- Download GGUF (Q4_K_M)
- Create LocalAI model config YAML
- Benchmark: latency, quality, structured output
- Compare against hermes-3b on fleet prompts
- Document results
- **Status:** ⏳ PENDING

### M-MU02: Model Config Templates
- Create YAML configs for: Qwen3-8B, Phi-4-mini, Llama 3.3 8B, DeepSeek R1 8B
- Template format compatible with LocalAI
- Document chat templates and stop tokens per model
- **Status:** ⏳ PENDING

### M-MU03: Shadow Routing
- Router sends tasks to both old and new model
- Compare outputs
- Record comparison in labor stamp metadata
- Dashboard: shadow comparison results
- **Status:** ⏳ PENDING

### M-MU04: Default Model Promotion
- Update fleet config to use Qwen3-8B as default
- Update backend registry
- hermes-3b as fallback
- Monitor approval rates post-promotion
- **Status:** ⏳ PENDING

### M-MU05: Dual-GPU Configuration (19GB)
- LocalAI config for two GPU backends
- GPU assignment per model
- Router knows which GPU has which model
- No-swap routing for common cases
- **Status:** ⏳ FUTURE (depends on hardware)

### M-MU06: TurboQuant Integration
- Monitor llama.cpp for TurboQuant support
- When available: rebuild model configs with extended context
- Benchmark: context window vs quality vs VRAM
- **Status:** ⏳ FUTURE (depends on ecosystem)

### M-MU07: Confidence Tier Progression Tracking
- Track approval rates per model per task type
- Dashboard: model performance over time
- PO decision interface: promote/demote model tier
- Cross-ref: labor attribution provides the data
- **Status:** ⏳ PENDING

### M-MU08: Cluster Peering (Machine 1 ↔ Machine 2)
- LocalAI cluster configuration for two machines
- Load balancing between clusters
- Failover: if Machine 1's GPU is busy, route to Machine 2
- Shared model registry across clusters
- **Status:** ⏳ FUTURE (depends on second machine)

---

## Part 9: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Multi-Backend Router | New models added to backend registry |
| Labor Attribution | Model used recorded in labor stamps, tier progression tracked |
| Budget Mode System | Better local models = more offload in frugal/survival modes |
| Iterative Validation | Local reasoning models (DeepSeek R1) used for free adversarial challenges |
| Strategic Vision LocalAI | Model upgrades directly serve Stages 2-5 |
| AICP Assessment | Stage 1 benchmarks inform model selection |
| Catastrophic Drain | Better local models reduce Claude dependency → reduce drain risk |

---

## Part 10: Why This Matters

The fleet currently runs hermes-3b (3B parameters, 2024-era model) as its
local option. The small model landscape has changed dramatically:

- **Qwen3.5-9B beats GPT-OSS-120B** (13x its size)
- **Qwen3-30B-A3B** delivers 30B quality with 3B compute cost
- **Phi-4** outperforms GPT-4o-mini on math and code
- **TurboQuant** extends context 6x with zero accuracy loss

hermes-3b was the right choice when it was chosen. It is no longer the
right choice. Upgrading to Qwen3-8B is a generational leap that directly
increases how much work LocalAI can handle, directly reduces Claude costs,
and directly advances the LocalAI independence mission.

> Better local models = more offload = lower costs = higher autonomy.
> This is the foundation of everything else.