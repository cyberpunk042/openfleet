# System 14: Multi-Backend Router — Cheapest Capable Backend Wins

**Type:** Fleet System
**ID:** S14
**Files:** backend_router.py (~570 lines), backend_health.py (~325 lines), model_swap.py (~345 lines), codex_review.py (~315 lines), router_unification.py (~60 lines)
**Total:** 1,611 lines
**Tests:** 141

## What This System Does

Routes tasks to the cheapest backend that can handle them. 4 backends: Claude (paid, expert/standard tier), LocalAI (free, trainee tier), OpenRouter-free (free, community tier), direct (no LLM, deterministic). Routing: assess task complexity → filter by backend_mode → cheapest capable → health check → circuit breaker check → RoutingDecision.

Security and architecture agents NEVER go to free/trainee backends — always Claude. Fallback chain: LocalAI → OpenRouter → Claude sonnet → Claude opus → queue.

## 4 Backends

| Backend | Type | Cost | Confidence Tier | Models |
|---------|------|------|----------------|--------|
| claude-code | Cloud/paid | $$$ | expert (opus), standard (sonnet) | opus-4-6, sonnet-4-6, haiku-4-5 |
| localai | Local/free | $0 | trainee | hermes-3b, hermes, codellama, phi-2 |
| openrouter-free | Cloud/free | $0 | community | 29 free models via load balancer |
| direct | Local/none | $0 | standard | No LLM — MCP tool calls, templates |

## Routing Decision Flow

```
route_task(task, agent, backend_mode, localai_available)
├── ASSESS COMPLEXITY: SP + task_type → trivial/simple/medium/complex/critical
│   ├── epic → critical
│   ├── blocker or SP≥8 → complex
│   ├── story + SP≥5 → complex
│   ├── SP≥3 → medium
│   ├── subtask or SP≤1 → trivial
│   └── default → simple
├── FILTER BY BACKEND_MODE: backends_for_mode("claude+localai") → ["claude-code", "localai"]
│   7 possible combos from FleetControlState
├── FILTER BY CAPABILITIES: complex needs "reasoning" → localai doesn't have it → filtered out
├── FILTER BY SECURITY: devsecops/architect → NEVER free/trainee
├── CHEAPEST CAPABLE: sort by cost → pick cheapest that passed all filters
├── HEALTH CHECK: is selected backend alive? LocalAI: GET /v1/models
├── CIRCUIT BREAKER: is breaker OPEN? → fallback to next backend
├── FALLBACK CHAIN: LocalAI → OpenRouter → sonnet → opus → queue
└── RETURN: RoutingDecision(backend, model, effort, reason, confidence_tier, fallback)
```

## Model Swap Management (LocalAI)

Single-active-backend: only ONE GPU model loaded at a time (8GB VRAM). Model swap takes 10-80s depending on model size.

```
SwapDecision:
├── Is the needed model already loaded? → NO SWAP (fast)
├── Skip-swap logic: are next 3 tasks in queue for current model? → DON'T SWAP for one task
├── Swap needed: unload current → load new (10-80s cold start)
├── Warm inference after swap: ~1.2s
└── Track swap frequency → alert if thrashing (>3 swaps/hour)
```

## Codex Review Trigger

Not a "trainee check" — codex_review.py decides when to trigger adversarial review:
- Confidence tier in REVIEW_TIERS (trainee, trainee-validated, community, hybrid) → trigger
- Force flag → always trigger
- Expert/standard → don't trigger automatically

Provides: CodexReviewRequest (PR, repo, tier, files_changed, instructions), CodexReviewResult (issues, severity, approved, duration), CodexReviewTracker (approval_rate, avg_issues).

## Backend Health Dashboard

BackendHealthDashboard tracks per-backend:
- LocalAIHealth: loaded model, GPU memory, swap state
- ClaudeHealth: quota (5h/7d), context window, rate limited
- OpenRouterHealth: free models available, response time

## Relationships

- CALLED BY: dispatch.py (route_task at dispatch time)
- READS: fleet_mode.py (backend_mode from FleetControlState)
- CHECKS: LocalAI health (GET localhost:8090/v1/models)
- USES: circuit breakers from storm_integration.py
- DERIVES: confidence_tier → feeds S13 labor (LaborStamp), S15 challenge (depth), review_gates.py (pipeline)
- CONNECTS TO: S05 control surface (backend_mode axis)
- CONNECTS TO: S07 orchestrator (dispatch uses router)
- CONNECTS TO: S11 storm (circuit breakers per backend)
- CONNECTS TO: S12 budget (cost per backend)
- CONNECTS TO: S13 labor (confidence tier in LaborStamp)
- CONNECTS TO: S15 challenge (tier determines challenge depth)
- CONNECTS TO: S16 models (model configs, benchmarks, promotion)
- CONNECTS TO: codex-plugin-cc (adversarial review via Codex)
- FUTURE: router_unification.py (AICP ↔ Fleet bridge — schema only)
- NOT YET DONE: connected to real dispatch (wired this session), LocalAI live test, OpenRouter client, AICP bridge

## For LightRAG Entity Extraction

Key entities: BackendDefinition (4 backends), RoutingDecision (backend, model, effort, reason, tier), BackendHealthDashboard, SwapDecision (skip-swap logic), CodexReviewRequest/Result/Tracker, confidence_tier (expert/standard/trainee/community).

Key relationships: Router ASSESSES complexity. Router FILTERS by backend_mode. Router SELECTS cheapest capable. Health check VALIDATES availability. Circuit breaker GATES on failure. Fallback chain CASCADES on unavailability. Confidence tier DRIVES challenge depth + review pipeline. Model swap MANAGES single-active-backend.
