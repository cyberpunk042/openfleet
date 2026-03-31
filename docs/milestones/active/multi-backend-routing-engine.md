# Multi-Backend Routing Decision Engine

## Severity: STRATEGIC
## Status: DESIGN
## Created: 2026-03-31

A use-case-aware routing engine that selects the right backend and model
for each operation — not "always Claude" but a strategy that considers
task type, budget mode, model capabilities, cost, and availability.

---

## Part 1: PO Requirements (Verbatim)

> "Just like we want to use methodologies and skills — Not an always in,
> more like a use case strategy logic decision."

> "MiMo-V2-Pro is just an idea but we need to think of plugins in general
> for claude code and things we might wanna also try to bring to LocalAI
> later even if we know the hard limitation, even though normally soon
> 8GB+11GB Graphics."

> "I know some endpoint are route through a loadbalancer of free models
> with autorouting to the one available to the level you want if its not
> too busy."

> "Not an always in, more like a use case strategy logic decision."

---

## Part 2: Research Findings

### Available Backends (Current + Near-Term)

| Backend | Type | Cost | Quality | Speed | Integration |
|---------|------|------|---------|-------|-------------|
| **Claude opus** | Cloud/paid | High ($$$) | Expert | Medium | Existing — Claude Code CLI |
| **Claude sonnet** | Cloud/paid | Medium ($$) | Standard | Fast | Existing — Claude Code CLI |
| **LocalAI hermes-3b** | Local/free | $0 | Trainee | 1.2s warm | Existing — OpenAI-compatible API |
| **LocalAI hermes-7b** | Local/free | $0 | Trainee | 1s warm, 80s cold | Existing — needs model swap |
| **LocalAI codellama-7b** | Local/free | $0 | Trainee (code) | 1s warm, 80s cold | Existing — needs model swap |
| **OpenRouter free** | Cloud/free | $0 | Community | Variable | New — OpenAI-compatible API |
| **OpenRouter auto** | Cloud/paid | Variable | Standard-Expert | Variable | New — auto-selects best model |
| **Codex CLI** | Local/paid | $ (OpenAI API) | Standard | Variable | New — separate tool, not plugin |
| **Direct/no-LLM** | Local/free | $0 | Deterministic | Instant | Existing — MCP tool calls |

### Models That Fit 8GB VRAM (LocalAI upgrades)

| Model | Params | VRAM (Q4) | Upgrade Over | Best For |
|-------|--------|-----------|-------------|----------|
| **Qwen3-8B** | 8B | ~5-6GB | hermes-3b (3B) | General reasoning, 2.5x bigger |
| **Llama 3.3 8B** | 8B | ~5-6GB | hermes-3b | All-rounder |
| **DeepSeek R1 8B** | 8B | ~5-6GB | hermes-3b | Chain-of-thought reasoning |
| **Mistral Small 3 7B** | 7B | ~5-6GB | hermes-7b | Highest tokens/sec |

### Models for 19GB VRAM (8GB + 11GB future)

| Model | Params | VRAM (Q4) | Game-Changer Because |
|-------|--------|-----------|---------------------|
| **Qwen3-30B-A3B** (MoE) | 30B total / 3B active | ~14-18GB | 30B intelligence, 3B compute |
| **Phi-4** | 14B | ~8-10GB | Beats GPT-4o-mini on math and code |
| **Qwen3.5-9B** | 9B | ~6-7GB | Beats GPT-OSS-120B (13x its size) |

### Compression Breakthroughs

- **Google TurboQuant** (March 25, 2026): 6x KV cache reduction, 8x attention
  speedup, NO retraining needed. Means longer contexts on same VRAM.
- **Microsoft BitNet**: 1-bit quantization, 0.4GB for 2B model. Natively trained
  only — can't convert existing models yet. Watch for ecosystem growth.
- **GGUF Q4_K_M**: Remains the practical standard. 75% VRAM reduction, 2-5% quality loss.

### Free Model Routers

- **OpenRouter** (`openrouter.ai`): 200+ models, 29 free models, `openrouter/free`
  auto-routes to available free model matching your requirements. OpenAI-compatible
  API. No credit card required for free tier.
- **LiteLLM** (open-source, self-hosted): Proxy/gateway with budget/rate limiting,
  fallback logic. Could sit between fleet router and all backends.

---

## Part 3: Routing Architecture

### Current Architecture (Two backends)

```
Task → model_selection.py → opus/sonnet → Claude Code CLI → result
                          → LocalAI (AICP Stage 2, not built)
```

### Target Architecture (Multi-backend)

```
Task + Budget Mode
    ↓
Backend Router (fleet/core/backend_router.py)
    ↓
    ├── Can this be done without an LLM?
    │   YES → Direct/MCP (cost: $0, confidence: deterministic)
    │         Examples: fleet_read_context, fleet_agent_status, status checks
    │
    ├── Is budget mode survival/frugal?
    │   YES → Try LocalAI first
    │         ├── Is LocalAI model loaded and warm? → LocalAI (cost: $0, confidence: trainee)
    │         ├── Is task simple enough for free tier? → OpenRouter free (cost: $0, confidence: community)
    │         └── Must use Claude? → sonnet only, low effort (cost: $, confidence: standard)
    │
    ├── Is budget mode economic?
    │   YES → LocalAI for simple, Claude sonnet for rest
    │         ├── Heartbeats → LocalAI (cost: $0)
    │         ├── Simple reviews → LocalAI (cost: $0)
    │         ├── Standard work → Claude sonnet (cost: $$)
    │         └── Complex work → Claude sonnet high effort (cost: $$)
    │
    ├── Is budget mode standard?
    │   YES → Normal routing
    │         ├── Simple/fleet ops → LocalAI (cost: $0)
    │         ├── Standard work → Claude sonnet (cost: $$)
    │         └── Complex work → Claude opus (cost: $$$)
    │
    └── Is budget mode blitz?
        YES → Claude for everything, max capability
              ├── Standard work → Claude sonnet high (cost: $$)
              └── Complex work → Claude opus max (cost: $$$)
```

### Routing Decision Function

```python
@dataclass
class RoutingDecision:
    """Result of backend routing."""
    backend: str          # "claude-code", "localai", "openrouter", "direct"
    model: str            # Specific model to use
    effort: str           # Effort level
    reason: str           # Why this backend was chosen
    confidence_tier: str  # Derived from backend+model
    estimated_cost: float # Estimated cost in USD
    fallback: str | None  # Backup backend if primary fails


def route_task(
    task: Task,
    agent_name: str,
    budget_mode: str,
    localai_status: dict,    # {"loaded_model": "hermes-3b", "warm": True, ...}
    quota_reading: QuotaReading | None,
) -> RoutingDecision:
    """Route a task to the best backend given constraints.

    Priority chain:
    1. Direct/no-LLM for pure tool calls
    2. LocalAI for simple structured tasks (if available)
    3. OpenRouter free for medium tasks in frugal/survival mode
    4. Claude sonnet for standard work
    5. Claude opus for complex work (if budget allows)

    The cheapest backend that can handle the task wins.
    """
```

### Backend Registry (Plugin Architecture)

```python
@dataclass
class BackendDefinition:
    """A registered backend that can serve requests."""
    name: str                    # "claude-code", "localai", "openrouter-free"
    type: str                    # "cloud", "local", "hybrid"
    api_format: str              # "anthropic", "openai-compatible"
    base_url: str | None         # e.g., "http://localhost:8090/v1"
    cost_per_1k_input: float     # USD
    cost_per_1k_output: float    # USD
    capabilities: list[str]      # ["reasoning", "code", "structured", "vision"]
    max_context: int             # Token limit
    confidence_tier: str         # Default tier for this backend
    available: bool              # Is it currently reachable?
    models: list[str]            # Available models on this backend
    health_check_url: str | None # Endpoint to verify availability


BACKEND_REGISTRY: dict[str, BackendDefinition] = {
    "claude-code": BackendDefinition(
        name="claude-code",
        type="cloud",
        api_format="anthropic",
        base_url=None,  # CLI subprocess
        cost_per_1k_input=0.015,  # opus pricing
        cost_per_1k_output=0.075,
        capabilities=["reasoning", "code", "structured", "vision", "tools"],
        max_context=200000,
        confidence_tier="expert",
        available=True,
        models=["opus-4-6", "sonnet-4-6", "haiku-4-5"],
        health_check_url=None,
    ),
    "localai": BackendDefinition(
        name="localai",
        type="local",
        api_format="openai-compatible",
        base_url="http://localhost:8090/v1",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        capabilities=["structured", "code"],  # limited reasoning
        max_context=8192,
        confidence_tier="trainee",
        available=True,  # checked via health endpoint
        models=["hermes-3b", "hermes", "codellama", "phi-2"],
        health_check_url="http://localhost:8090/v1/models",
    ),
    "openrouter-free": BackendDefinition(
        name="openrouter-free",
        type="cloud",
        api_format="openai-compatible",
        base_url="https://openrouter.ai/api/v1",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        capabilities=["reasoning", "code", "structured"],
        max_context=32768,  # varies by model
        confidence_tier="community",
        available=True,  # depends on API key
        models=["openrouter/free"],  # auto-routed
        health_check_url=None,
    ),
}
```

### Fallback Chain

When a backend fails, the router tries the next option:

```
LocalAI fails → OpenRouter free → Claude sonnet (minimum viable)
OpenRouter free fails → Claude sonnet
Claude sonnet fails → Claude opus (if budget allows)
Claude opus fails → queue task, alert PO

LocalAI cold (model swapping) → skip, try next backend
OpenRouter busy (no free model available) → skip, try next backend
```

Fallback is **always recorded** in the labor stamp:
`backend: "claude-code", fallback_from: "localai", fallback_reason: "model swap in progress"`

---

## Part 4: LocalAI Model Management

### Single-Active Backend Problem

LocalAI can only have one GPU model loaded at a time (8GB VRAM).
Cold start for model swap: 10-80s.

**Strategy:**
- Keep hermes-3b (or its upgrade) as the **default loaded model**
- Only swap models when a specific capability is needed (e.g., codellama for code)
- Swap decisions are made by the router, not the agent
- If a swap is needed but budget is tight → skip LocalAI, use next backend

### Model Hot-Swap Protocol

```
Router decides: task needs codellama, but hermes-3b is loaded
  → Is there a queued task that needs hermes-3b soon?
    YES → skip swap, use next backend
    NO → initiate swap
      1. Record swap start in metrics
      2. POST /v1/models/apply (or restart LocalAI with target model)
      3. Wait for health check to pass
      4. Record swap duration in metrics
      5. Route task to newly loaded model
      6. Labor stamp records: model_swap_time_s in metadata
```

### Future: 19GB VRAM (8GB + 11GB)

With dual GPUs, the single-active limitation relaxes:
- GPU 1 (8GB): hermes-3b or Qwen3-8B — always loaded, fleet default
- GPU 2 (11GB): codellama or Phi-4 — loaded on demand for specialized tasks
- Two models simultaneously = no swap penalty for the common case

---

## Part 5: OpenRouter Integration

### Configuration

```yaml
# config/backends.yaml
openrouter:
  enabled: true
  api_key_env: "OPENROUTER_API_KEY"  # can be empty for free tier
  base_url: "https://openrouter.ai/api/v1"
  free_router: "openrouter/free"
  auto_router: "openrouter/auto"  # paid, uses NotDiamond
  capabilities_filter:
    - tool_calling
    - structured_output
  max_retries: 2
  timeout_seconds: 30
```

### Free Tier Usage

OpenRouter's free router (`openrouter/free`) auto-selects a free model
matching requested capabilities. No API key required.

**When to use:**
- Budget mode is frugal or survival
- LocalAI is unavailable (swapping models, offline)
- Task is medium complexity (not trivial, not critical)
- Agent needs reasoning but cost must be zero

**When NOT to use:**
- Security analysis (can't trust free model)
- Architecture decisions (need deep reasoning)
- Code that will go to production without expert review
- Any task where trainee/community tier triggers a mandatory review
  that costs MORE than just using Claude in the first place

### LiteLLM as Local Gateway (Future)

LiteLLM can sit between the fleet and all backends as a unified proxy:

```
Fleet Router → LiteLLM Gateway → LocalAI
                               → OpenRouter
                               → Claude API
                               → (future backends)
```

Benefits:
- Unified API format (OpenAI-compatible for everything)
- Built-in rate limiting, budget tracking, fallback logic
- Logging and observability
- Model aliasing (e.g., "fleet-default" → hermes-3b today, Qwen3-8B tomorrow)

This is a **Stage 3-4** consideration. For Stage 2, direct integration
with each backend is simpler and more controllable.

---

## Part 6: Codex CLI Integration

### Reality Check

Codex CLI is NOT a Claude Code plugin. It's a separate standalone tool
(OpenAI's open-source CLI agent). It:
- Requires OpenAI API credits (not free)
- Has no MCP support
- Operates independently on the filesystem
- Uses o4-mini/o3 models

### Viable Use Case: Adversarial Reviews

> "I think we need to use Codex for certain task like adversarial reviews"

Pattern: after an agent produces work with Claude, run Codex CLI as a
**second opinion** to challenge the implementation:

```
Agent completes task (Claude opus) → fleet_task_complete → PR created
    ↓
Adversarial review triggered (if confidence tier warrants it)
    ↓
Codex CLI runs against the diff:
  codex --model o4-mini "Review this PR for bugs, security issues,
  and architectural problems. Be adversarial. Find flaws."
    ↓
Codex output → posted as review comment on PR
    ↓
fleet-ops evaluates both the work AND the adversarial review
```

**Cost consideration:** Codex uses OpenAI API ($). For adversarial reviews
to be cost-effective, they should only trigger for:
- trainee/community tier work (LocalAI/free model output)
- High story-point tasks (≥5 SP)
- Security-sensitive work
- When budget mode is standard or blitz (not frugal/survival)

### Integration Path

Codex CLI could theoretically point at LocalAI's OpenAI-compatible API:
```
OPENAI_BASE_URL=http://localhost:8090/v1 codex "Review this code"
```
This gives a **free adversarial review** using LocalAI, but quality
depends entirely on the local model's capability.

---

## Part 7: AICP Router Evolution

### Current AICP Router (aicp/core/router.py)

Keyword-based classification: simple/complex/fleet operations.
Mode enforcement: ACT/EDIT → Claude, THINK → local.

### Target: Unified Routing

The AICP router and the fleet backend router should share the same
decision engine. AICP handles individual user requests; the fleet
handles agent operations. Both need the same:
- Backend registry
- Budget awareness
- Capability matching
- Fallback chains
- Labor attribution

```
AICP router (user requests) ─┐
                              ├→ Shared routing engine → Backend
Fleet router (agent ops)   ───┘
```

This unification is a **Stage 3** goal. For Stage 2, the fleet gets
its own router first, then we merge the logic.

---

## Part 8: Milestones

### M-BR01: Backend Registry
- Define `BackendDefinition` dataclass
- Create `BACKEND_REGISTRY` with claude-code, localai, openrouter-free
- Health check for each backend (is it reachable?)
- Config-driven: backends.yaml
- Tests for registry CRUD and health checks
- **Status:** ⏳ PENDING

### M-BR02: Routing Decision Engine
- Implement `route_task()` function
- Budget mode constrains backend selection
- Task complexity determines minimum capability
- Cheapest capable backend wins
- Returns `RoutingDecision` with backend, model, effort, confidence_tier
- Tests for every budget mode × task type combination
- **Status:** ⏳ PENDING

### M-BR03: Fallback Chain
- If primary backend fails → try next in chain
- Record fallback in labor stamp
- Max 2 fallback attempts before queuing task
- Alert on repeated fallbacks (backend may be down)
- **Status:** ⏳ PENDING

### M-BR04: OpenRouter Free Integration
- Add OpenRouter as a backend in the registry
- Implement OpenAI-compatible client for OpenRouter
- Free tier routing: `openrouter/free` with capability filters
- Rate limiting and timeout handling
- Tests with mock responses
- **Status:** ⏳ PENDING

### M-BR05: LocalAI Model Swap Management
- Router-initiated model swaps (not agent-initiated)
- Swap protocol: check queue → initiate → wait → verify → route
- Swap metrics (duration, frequency, which models)
- Skip-swap logic when next task needs current model
- **Status:** ⏳ PENDING

### M-BR06: Codex CLI Adversarial Review Integration
- Codex CLI wrapper for adversarial reviews
- Triggered by confidence tier and budget mode
- Output posted as PR review comment
- Optional: point Codex at LocalAI for free adversarial review
- **Status:** ⏳ PENDING (depends on Codex availability + cost analysis)

### M-BR07: Backend Health Dashboard
- Real-time status of all backends (up/down/degraded)
- Model currently loaded on LocalAI
- OpenRouter free tier availability
- Claude quota status
- Integrated into fleet-ops monitoring
- **Status:** ⏳ PENDING

### M-BR08: AICP Router Unification (Stage 3)
- Merge AICP router logic with fleet backend router
- Shared routing engine, shared backend registry
- AICP handles user requests, fleet handles agent ops
- Same budget awareness, same fallback chains
- **Status:** ⏳ FUTURE (Stage 3)

---

## Part 9: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Budget Mode System | Budget mode constrains which backends the router can use |
| Labor Attribution | Router decision recorded in labor stamp |
| Storm Prevention | Router respects budget pressure, downgrades backends automatically |
| Iterative Validation | Router used for adversarial review backend selection |
| Model Upgrade Path | New LocalAI models added to backend registry |
| Strategic Vision LocalAI | Stages 2-5 of LocalAI independence ARE the routing evolution |
| AICP core/router.py | Current AICP routing logic to be unified in Stage 3 |
| Catastrophic Drain | Direct/no-LLM routing prevents unnecessary Claude sessions |

---

## Part 10: Why This Matters

Today the fleet has exactly two gears: Claude (expensive) and off.
LocalAI exists but isn't wired into the fleet. OpenRouter's 29 free
models sit unused. The router makes a binary choice and records nothing.

With multi-backend routing:
- **Heartbeats cost $0** — routed to LocalAI or direct/no-LLM
- **Simple reviews cost $0** — LocalAI handles pattern matching
- **Budget pressure triggers free-tier fallback** — fleet stays alive
- **Every routing decision is recorded** — observable and auditable
- **New backends are plugins** — add them to the registry, the router finds them
- **The cheapest capable backend always wins** — by design, not by accident