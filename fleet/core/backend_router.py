"""Multi-backend routing — use-case-aware backend selection.

Routes tasks to the cheapest capable backend based on task complexity,
agent role, model capabilities, cost, and availability.

PO requirement (verbatim):
> "Just like we want to use methodologies and skills — Not an always in,
> more like a use case strategy logic decision."

Backends:
  claude-code     — Cloud/paid, expert tier, CLI subprocess
  localai         — Local/free, trainee tier, OpenAI-compatible API
  openrouter-free — Cloud/free, community tier, OpenAI-compatible API
  direct          — No LLM, deterministic, MCP tool calls

Routing principle: cheapest capable backend wins.
Fallback: LocalAI → OpenRouter → Claude sonnet → Claude opus → queue.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from fleet.core.labor_stamp import derive_confidence_tier
from fleet.core.models import Task

if TYPE_CHECKING:
    from fleet.core.backend_health import BackendHealthDashboard
    from fleet.core.storm_monitor import StormMonitor

logger = logging.getLogger(__name__)


# ─── Backend Definition ──────────────────────────────────────────────


@dataclass
class BackendDefinition:
    """A registered backend that can serve requests."""

    name: str
    type: str                    # "cloud", "local", "hybrid"
    api_format: str              # "anthropic", "openai-compatible"
    base_url: Optional[str]      # e.g., "http://localhost:8090/v1"
    cost_per_1k_input: float     # USD
    cost_per_1k_output: float    # USD
    capabilities: list[str]      # ["reasoning", "code", "structured", "vision"]
    max_context: int             # Token limit
    confidence_tier: str         # Default tier for this backend
    available: bool              # Is it currently reachable?
    models: list[str]            # Available models on this backend
    health_check_url: Optional[str] = None

    @property
    def is_free(self) -> bool:
        return self.cost_per_1k_input == 0.0 and self.cost_per_1k_output == 0.0

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities


# ─── Backend Registry ────────────────────────────────────────────────


BACKEND_REGISTRY: dict[str, BackendDefinition] = {
    "claude-code": BackendDefinition(
        name="claude-code",
        type="cloud",
        api_format="anthropic",
        base_url=None,  # CLI subprocess — no HTTP
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        capabilities=["reasoning", "code", "structured", "vision", "tools"],
        max_context=200_000,
        confidence_tier="expert",
        available=True,
        models=["opus-4-6", "sonnet-4-6", "haiku-4-5"],
    ),
    "localai": BackendDefinition(
        name="localai",
        type="local",
        api_format="openai-compatible",
        base_url="http://localhost:8090/v1",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        capabilities=["structured", "code"],
        max_context=8192,
        confidence_tier="trainee",
        available=True,
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
        max_context=32768,
        confidence_tier="community",
        available=True,
        models=["openrouter/free"],
    ),
    "openrouter-qwen36plus": BackendDefinition(
        name="openrouter-qwen36plus",
        type="cloud",
        api_format="openai-compatible",
        base_url="https://openrouter.ai/api/v1",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        capabilities=["reasoning", "code", "structured"],
        max_context=32768,
        confidence_tier="community",
        available=True,
        models=["qwen/qwen3-235b-a22b"],
    ),
    "direct": BackendDefinition(
        name="direct",
        type="local",
        api_format="none",
        base_url=None,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        capabilities=["tools", "structured"],
        max_context=0,
        confidence_tier="standard",
        available=True,
        models=[],
    ),
}


def get_backend(name: str) -> Optional[BackendDefinition]:
    """Get a backend by name."""
    return BACKEND_REGISTRY.get(name)


def list_backends(available_only: bool = False) -> list[BackendDefinition]:
    """List all registered backends."""
    backends = list(BACKEND_REGISTRY.values())
    if available_only:
        backends = [b for b in backends if b.available]
    return backends


def list_free_backends() -> list[BackendDefinition]:
    """List all free backends (cost = $0)."""
    return [b for b in BACKEND_REGISTRY.values() if b.is_free and b.available]


# ─── Routing Decision ───────────────────────────────────────────────


@dataclass
class RoutingDecision:
    """Result of backend routing — what to use and why."""

    backend: str
    model: str
    effort: str
    reason: str
    confidence_tier: str
    estimated_cost: float = 0.0
    fallback_backend: Optional[str] = None
    fallback_model: Optional[str] = None


# ─── Task Complexity Assessment ──────────────────────────────────────


def _assess_complexity(task: Task) -> str:
    """Assess task complexity for routing decisions.

    Returns: "trivial", "simple", "medium", "complex", "critical"
    """
    sp = task.custom_fields.story_points or 0
    task_type = task.custom_fields.task_type or "task"

    if task_type in ("epic",):
        return "critical"
    if task_type in ("blocker",) or sp >= 8:
        return "complex"
    if task_type in ("story",) and sp >= 5:
        return "complex"
    if sp >= 3:
        return "medium"
    if task_type in ("subtask",) or sp <= 1:
        return "trivial"
    return "simple"


# Capabilities required by complexity level
_REQUIRED_CAPABILITIES: dict[str, list[str]] = {
    "trivial": ["structured"],
    "simple": ["structured"],
    "medium": ["structured", "code"],
    "complex": ["reasoning", "code"],
    "critical": ["reasoning", "code"],
}


# ─── Routing Engine ─────────────────────────────────────────────────


# Agents whose work requires deep reasoning — never route to free/trainee
_SECURITY_AGENTS = {"devsecops-expert"}
_ARCHITECTURE_AGENTS = {"architect"}


# backend_mode → which backends are enabled
_BACKEND_MODE_MAP: dict[str, list[str]] = {
    "claude": ["claude-code"],
    "localai": ["localai"],
    "openrouter": ["openrouter-free"],
    "claude+localai": ["claude-code", "localai"],
    "claude+openrouter": ["claude-code", "openrouter-free"],
    "localai+openrouter": ["localai", "openrouter-free"],
    "claude+localai+openrouter": ["claude-code", "localai", "openrouter-free"],
    # backward compat for existing config
    "hybrid": ["claude-code", "localai"],
}


def backends_for_mode(backend_mode: str) -> list[str]:
    """Map a backend_mode setting to the list of enabled backend names."""
    return _BACKEND_MODE_MAP.get(backend_mode, ["claude-code"])


def route_task(
    task: Task,
    agent_name: str,
    backend_mode: str = "claude",
    localai_available: bool = True,
    localai_model: str = "hermes-3b",
    storm_monitor: Optional["StormMonitor"] = None,
    health_dashboard: Optional["BackendHealthDashboard"] = None,
) -> RoutingDecision:
    """Route a task to the best backend given constraints.

    Only routes to backends enabled by backend_mode (from FleetControlState).
    Cheapest capable enabled backend wins. Security and architecture
    agents are never routed to free/trainee backends.
    """
    complexity = _assess_complexity(task)
    required_caps = _REQUIRED_CAPABILITIES.get(complexity, ["structured"])

    enabled_backends = backends_for_mode(backend_mode)

    # Security and architecture agents NEVER go to free/trainee backends
    force_claude = agent_name in _SECURITY_AGENTS or agent_name in _ARCHITECTURE_AGENTS

    # Find cheapest capable backend from ENABLED backends only
    candidates = []
    for backend in BACKEND_REGISTRY.values():
        if backend.name not in enabled_backends:
            continue
        if not backend.available:
            continue
        if backend.name == "localai" and not localai_available:
            continue
        if not all(backend.has_capability(c) for c in required_caps):
            continue
        if force_claude and backend.confidence_tier in ("trainee", "community"):
            continue
        candidates.append(backend)

    if not candidates:
        # Nothing available — fall back to claude-code
        return RoutingDecision(
            backend="claude-code", model="sonnet", effort="medium",
            reason="no capable backends available, falling back to Claude",
            confidence_tier="standard",
        )

    # Sort by cost (cheapest first)
    candidates.sort(key=lambda b: b.cost_per_1k_input)
    best = candidates[0]

    # Select model and effort based on backend and complexity
    if best.name == "claude-code":
        if complexity in ("complex", "critical"):
            model, effort = "opus", "high"
        elif complexity == "medium":
            model, effort = "sonnet", "medium"
        else:
            model, effort = "sonnet", "low"
    elif best.name == "localai":
        model, effort = localai_model, "low"
    elif best.name == "openrouter-free":
        model = "openrouter/free"
        effort = "medium" if complexity in ("medium", "complex") else "low"
    else:
        model = best.models[0] if best.models else ""
        effort = "medium"

    # Set fallback
    fallback_backend = None
    fallback_model = None
    if best.name != "claude-code":
        fallback_backend = "claude-code"
        fallback_model = "sonnet"

    decision = RoutingDecision(
        backend=best.name,
        model=model,
        effort=effort,
        reason=f"{complexity} task → {best.name}/{model} (cheapest capable)",
        confidence_tier=best.confidence_tier,
        estimated_cost=best.cost_per_1k_input * 5,
        fallback_backend=fallback_backend,
        fallback_model=fallback_model,
    )

    # Health and circuit breaker checks
    if health_dashboard:
        decision = _apply_health_check(decision, health_dashboard)
    if storm_monitor:
        decision = _apply_circuit_breakers(decision, storm_monitor)

    return decision


# ─── Circuit Breaker Integration ─────────────────────────────────────


def _apply_circuit_breakers(
    decision: RoutingDecision,
    storm_monitor: "StormMonitor",
) -> RoutingDecision:
    """Check if the chosen backend's circuit breaker is open."""
    breaker = storm_monitor.get_backend_breaker(decision.backend)

    if breaker.check():
        return decision

    logger.warning(
        "circuit breaker OPEN for %s (failures=%d, trips=%d), attempting fallback",
        decision.backend, breaker.consecutive_failures, breaker.trip_count,
    )

    fallback = execute_fallback(decision, f"circuit breaker open ({breaker.trip_count} trips)")
    if fallback is None:
        return RoutingDecision(
            backend="direct", model="", effort="low",
            reason=f"circuit breaker open for {decision.backend}, no fallback — task queued",
            confidence_tier="standard",
        )

    fallback_breaker = storm_monitor.get_backend_breaker(fallback.backend)
    if fallback_breaker.check():
        return fallback

    logger.warning(
        "fallback %s also has circuit breaker OPEN, queuing task",
        fallback.backend,
    )
    return RoutingDecision(
        backend="direct", model="", effort="low",
        reason=f"circuit breakers open for {decision.backend} and {fallback.backend} — task queued",
        confidence_tier="standard",
    )


def record_backend_result(
    storm_monitor: "StormMonitor",
    backend: str,
    success: bool,
) -> None:
    """Record a backend call result on its circuit breaker."""
    breaker = storm_monitor.get_backend_breaker(backend)
    if success:
        breaker.record_success()
    else:
        breaker.record_failure()


# ─── Fallback Execution ─────────────────────────────────────────────


def execute_fallback(
    decision: RoutingDecision,
    failure_reason: str,
) -> Optional[RoutingDecision]:
    """Execute fallback routing when primary backend fails."""
    if not decision.fallback_backend:
        return None

    fallback_def = BACKEND_REGISTRY.get(decision.fallback_backend)
    if not fallback_def or not fallback_def.available:
        return None

    fallback_model = decision.fallback_model or (
        fallback_def.models[0] if fallback_def.models else ""
    )

    tier, _ = derive_confidence_tier(decision.fallback_backend, fallback_model)

    return RoutingDecision(
        backend=decision.fallback_backend,
        model=fallback_model,
        effort=decision.effort,
        reason=f"fallback from {decision.backend}: {failure_reason} → {decision.fallback_backend}/{fallback_model}",
        confidence_tier=tier,
        estimated_cost=fallback_def.cost_per_1k_input * 5,
    )


# ─── Health Checks ───────────────────────────────────────────────────


def _apply_health_check(
    decision: RoutingDecision,
    dashboard: "BackendHealthDashboard",
) -> RoutingDecision:
    """Check if the chosen backend is healthy."""
    from fleet.core.backend_health import BackendStatus

    state = dashboard.get(decision.backend)
    if state is None:
        return decision

    if state.status == BackendStatus.DOWN:
        fallback = execute_fallback(decision, f"health: {decision.backend} is DOWN")
        if fallback is not None:
            return fallback
        return RoutingDecision(
            backend="queue", model="", effort="low",
            reason=f"{decision.backend} DOWN, no healthy fallback",
            confidence_tier="standard",
        )

    return decision


async def check_backend_health(name: str) -> bool:
    """Check if a backend is reachable."""
    backend = BACKEND_REGISTRY.get(name)
    if not backend:
        return False

    if not backend.health_check_url:
        return True

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                backend.health_check_url, timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                backend.available = resp.status == 200
                return backend.available
    except Exception:
        backend.available = False
        return False
