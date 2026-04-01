# System 14: Multi-Backend Router

**Source:** `fleet/core/backend_router.py`, `fleet/core/backend_health.py`, `fleet/core/model_swap.py`, `fleet/core/codex_review.py`, `fleet/core/router_unification.py`
**Status:** 🔨 Unit + integration tests. Not connected to real dispatch.
**Design docs:** `multi-backend-routing-engine.md` (M-BR01-08)

---

## Purpose

Route tasks to the cheapest capable backend. Budget mode constrains options. Fallback chains handle failures. Health dashboard tracks backend availability. Model swap manages LocalAI single-active-backend limitation.

### PO Requirement (Verbatim)

> "Just like we want to use methodologies and skills — Not an always in, more like a use case strategy logic decision."

## Key Concepts

### Backend Registry (backend_router.py)

4 backends:
- `claude-code` — Cloud/paid, expert/standard tier
- `localai` — Local/free, trainee tier, single-active GPU model
- `openrouter-free` — Cloud/free, community tier, 29 free models
- `direct` — No LLM, deterministic MCP tool calls

### Routing Decision (backend_router.py:201-269)

`route_task(task, agent, budget_mode, localai_available, storm_monitor, health_dashboard)`

Route by budget mode:
- blackout → direct only
- survival → LocalAI + direct
- frugal → LocalAI + OpenRouter free
- economic → sonnet only (no opus)
- standard → LocalAI for simple, Claude for complex
- blitz → opus for everything

Security/architecture agents NEVER go to free/trainee backends.

### Health-Aware Routing (W5 wiring)

`_apply_health_check(decision, dashboard)` — if backend DOWN, trigger `execute_fallback()`. If no fallback, queue task.

### Circuit Breaker Integration (W3, storm)

`_apply_circuit_breakers(decision, storm_monitor)` — if backend's breaker OPEN, fallback. If primary AND fallback both OPEN, queue.

### Backend Health (backend_health.py)

Per-backend health states:
- `LocalAIHealth` — loaded_model, gpu_memory, swap_in_progress
- `ClaudeHealth` — quota_used_pct, weekly_quota_used_pct, context_window_size, rate_limited
- `OpenRouterHealth` — free_models_available, free_tier_active

`BackendHealthDashboard` — aggregates all, availability_score, routing_options.

### Model Swap (model_swap.py)

LocalAI single-active-backend: only one GPU model at a time. SwapDecision evaluates: should we swap? Checks queued tasks — if they need current model, skip swap.

### Codex Review (codex_review.py)

Trigger/decision layer for adversarial reviews. `should_trigger_review(tier, budget_mode)` — trainee/trainee-validated/community/hybrid tiers trigger review. Budget mode determines backend (codex-plugin vs localai).

### Router Unification (router_unification.py)

FUTURE: `UnifiedRoutingRequest(source: "aicp" | "fleet")` → bridge between AICP and fleet routing.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Budget** | Budget mode constrains allowed models/backends | Budget → Router |
| **Storm** | Circuit breakers affect routing | Storm → Router |
| **Backend Health** | Health state drives fallback decisions (W5) | Health → Router |
| **Model Promotion** | Promoted model enters routing table (W6) | Promotion → Router |
| **Labor Stamps** | Routing decision recorded in stamp | Router → Stamps |
| **Tier Progression** | Tier drives codex review trigger (W7) | Tier → Review |
| **Session Telemetry** | Real API latency feeds health (W8) | Telemetry → Health |
| **AICP Router** | FUTURE: unified routing bridge | Router ↔ AICP |

## What's Needed

- [ ] Connect to real dispatch (orchestrator uses routing decision)
- [ ] LocalAI routing live test
- [ ] OpenRouter free tier integration
- [ ] AICP bridge (router_unification.py)
