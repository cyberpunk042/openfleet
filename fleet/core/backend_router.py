"""Multi-backend routing \u2014 use-case-aware backend selection.

Routes tasks to the cheapest capable backend based on task complexity,
budget mode, model capabilities, cost, and availability.

PO requirement (verbatim):
> "Just like we want to use methodologies and skills \u2014 Not an always in,
> more like a use case strategy logic decision."

Backends:
  claude-code     \u2014 Cloud/paid, expert/standard tier, CLI subprocess
  localai         \u2014 Local/free, trainee tier, OpenAI-compatible API
  openrouter-free \u2014 Cloud/free, community tier, OpenAI-compatible API
  direct          \u2014 No LLM, deterministic, MCP tool calls

Routing principle: cheapest capable backend wins.
Fallback: LocalAI \u2192 OpenRouter \u2192 Claude sonnet \u2192 Claude opus \u2192 queue.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from fleet.core.budget_modes import BUDGET_MODES, get_mode
from fleet.core.labor_stamp import derive_confidence_tier
from fleet.core.models import Task

if TYPE_CHECKING:
    from fleet.core.backend_health import BackendHealthDashboard
    from fleet.core.storm_monitor import StormMonitor

logger = logging.getLogger(__name__)


# \u2500\u2500\u2500 Backend Definition \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


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


# \u2500\u2500\u2500 Backend Registry \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


BACKEND_REGISTRY: dict[str, BackendDefinition] = {
    "claude-code": BackendDefinition(
        name="claude-code",
        type="cloud",
        api_format="anthropic",
        base_url=None,  # CLI subprocess \u2014 no HTTP
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


# \u2500\u2500\u2500 Routing Decision \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


@dataclass
class RoutingDecision:
    """Result of backend routing \u2014 what to use and why."""

    backend: str
    model: str
    effort: str
    reason: str
    confidence_tier: str
    estimated_cost: float = 0.0
    fallback_backend: Optional[str] = None
    fallback_model: Optional[str] = None


# \u2500\u2500\u2500 Task Complexity Assessment \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


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


# \u2500\u2500\u2500 Routing Engine \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


# Agents whose work requires deep reasoning \u2014 never route to free/trainee
_SECURITY_AGENTS = {"devsecops-expert"}
_ARCHITECTURE_AGENTS = {"architect"}


def route_task(
    task: Task,
    agent_name: str,
    budget_mode: str,
    localai_available: bool = True,
    localai_model: str = "hermes-3b",
    storm_monitor: Optional["StormMonitor"] = None,
    health_dashboard: Optional["BackendHealthDashboard"] = None,
) -> RoutingDecision:
    """Route a task to the best backend given constraints.

    Priority chain:
    1. Direct/no-LLM for pure tool calls (if applicable)
    2. LocalAI for simple structured tasks (if available)
    3. OpenRouter free for medium tasks in frugal/survival mode
    4. Claude sonnet for standard work
    5. Claude opus for complex work (if budget allows)

    If storm_monitor is provided, backends with tripped circuit breakers
    are skipped and fallback is triggered automatically.

    The cheapest capable backend wins.
    """
    complexity = _assess_complexity(task)
    required_caps = _REQUIRED_CAPABILITIES.get(complexity, ["structured"])
    mode = get_mode(budget_mode) or get_mode("standard")

    # Security and architecture agents NEVER go to free/trainee backends
    force_claude = agent_name in _SECURITY_AGENTS or agent_name in _ARCHITECTURE_AGENTS

    # \u2500\u2500\u2500 Route by budget mode \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

    if budget_mode == "blackout":
        return RoutingDecision(
            backend="direct", model="", effort="low",
            reason="blackout: fleet frozen, only direct/no-LLM allowed",
            confidence_tier="standard",
        )

    if budget_mode == "survival":
        decision = _route_survival(
            task, complexity, required_caps,
            localai_available, localai_model, force_claude,
        )
    elif budget_mode == "frugal":
        decision = _route_frugal(
            task, complexity, required_caps,
            localai_available, localai_model, force_claude,
        )
    elif budget_mode == "economic":
        decision = _route_economic(
            task, complexity, required_caps,
            localai_available, localai_model, force_claude,
        )
    elif budget_mode == "blitz":
        decision = _route_blitz(task, complexity)
    else:
        # standard mode (default)
        decision = _route_standard(
            task, complexity, required_caps,
            localai_available, localai_model, force_claude,
        )

    # \u2500\u2500\u2500 Circuit breaker check \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # ─── Health-aware override ─────────────────────────────────────
    if health_dashboard:
        decision = _apply_health_check(decision, health_dashboard)

    if storm_monitor:
        decision = _apply_circuit_breakers(decision, storm_monitor)

    return decision


# \u2500\u2500\u2500 Circuit Breaker Integration \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _apply_circuit_breakers(
    decision: RoutingDecision,
    storm_monitor: "StormMonitor",
) -> RoutingDecision:
    """Check if the chosen backend's circuit breaker is open.

    If open, attempt fallback. If fallback also open, return a queued
    decision that prevents dispatch entirely.
    """
    breaker = storm_monitor.get_backend_breaker(decision.backend)

    if breaker.check():
        # Primary backend is healthy
        return decision

    # Primary backend breaker is OPEN \u2014 attempt fallback
    logger.warning(
        "circuit breaker OPEN for %s (failures=%d, trips=%d), attempting fallback",
        decision.backend, breaker.consecutive_failures, breaker.trip_count,
    )

    fallback = execute_fallback(decision, f"circuit breaker open ({breaker.trip_count} trips)")
    if fallback is None:
        # No fallback available \u2014 queue the task
        return RoutingDecision(
            backend="direct", model="", effort="low",
            reason=(
                f"circuit breaker open for {decision.backend}, "
                f"no fallback available \u2014 task queued"
            ),
            confidence_tier="standard",
        )

    # Check fallback backend's breaker too
    fallback_breaker = storm_monitor.get_backend_breaker(fallback.backend)
    if fallback_breaker.check():
        return fallback

    # Both primary and fallback breakers open
    logger.warning(
        "fallback %s also has circuit breaker OPEN, queuing task",
        fallback.backend,
    )
    return RoutingDecision(
        backend="direct", model="", effort="low",
        reason=(
            f"circuit breakers open for {decision.backend} "
            f"and fallback {fallback.backend} \u2014 task queued"
        ),
        confidence_tier="standard",
    )


def record_backend_result(
    storm_monitor: "StormMonitor",
    backend: str,
    success: bool,
) -> None:
    """Record a backend call result on its circuit breaker.

    Called by the dispatch layer after a backend call completes
    or fails, so the breaker state stays current.
    """
    breaker = storm_monitor.get_backend_breaker(backend)
    if success:
        breaker.record_success()
    else:
        breaker.record_failure()


# \u2500\u2500\u2500 Mode-Specific Routing \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _route_survival(
    task: Task, complexity: str, required_caps: list[str],
    localai_available: bool, localai_model: str, force_claude: bool,
) -> RoutingDecision:
    """Survival mode: zero Claude spend. LocalAI + OpenRouter free only."""
    if force_claude:
        return RoutingDecision(
            backend="claude-code", model="sonnet", effort="low",
            reason="survival: forced Claude for security/architecture (override)",
            confidence_tier="standard", estimated_cost=0.009,
            fallback_backend=None,
        )

    if localai_available and complexity in ("trivial", "simple"):
        return RoutingDecision(
            backend="localai", model=localai_model, effort="low",
            reason=f"survival: LocalAI for {complexity} task",
            confidence_tier="trainee",
            fallback_backend="openrouter-free", fallback_model="openrouter/free",
        )

    return RoutingDecision(
        backend="openrouter-free", model="openrouter/free", effort="low",
        reason=f"survival: free router for {complexity} task",
        confidence_tier="community",
        fallback_backend="localai" if localai_available else None,
        fallback_model=localai_model if localai_available else None,
    )


def _route_frugal(
    task: Task, complexity: str, required_caps: list[str],
    localai_available: bool, localai_model: str, force_claude: bool,
) -> RoutingDecision:
    """Frugal mode: prefer free, Claude sonnet only when necessary."""
    if complexity in ("trivial", "simple") and localai_available:
        return RoutingDecision(
            backend="localai", model=localai_model, effort="low",
            reason=f"frugal: LocalAI for {complexity} task",
            confidence_tier="trainee",
            fallback_backend="openrouter-free", fallback_model="openrouter/free",
        )

    if complexity == "medium" and not force_claude:
        return RoutingDecision(
            backend="openrouter-free", model="openrouter/free", effort="medium",
            reason="frugal: free router for medium task",
            confidence_tier="community",
            fallback_backend="claude-code", fallback_model="sonnet",
        )

    # Complex+ or security \u2192 Claude sonnet (no opus in frugal)
    return RoutingDecision(
        backend="claude-code", model="sonnet", effort="medium",
        reason=f"frugal: Claude sonnet for {complexity} task",
        confidence_tier="standard", estimated_cost=0.009,
    )


def _route_economic(
    task: Task, complexity: str, required_caps: list[str],
    localai_available: bool, localai_model: str, force_claude: bool,
) -> RoutingDecision:
    """Economic mode: sonnet + LocalAI, no opus."""
    if complexity in ("trivial", "simple") and localai_available and not force_claude:
        return RoutingDecision(
            backend="localai", model=localai_model, effort="low",
            reason=f"economic: LocalAI for {complexity} task",
            confidence_tier="trainee",
            fallback_backend="claude-code", fallback_model="sonnet",
        )

    effort = "medium" if complexity in ("trivial", "simple", "medium") else "high"
    return RoutingDecision(
        backend="claude-code", model="sonnet", effort=effort,
        reason=f"economic: Claude sonnet for {complexity} task",
        confidence_tier="standard", estimated_cost=0.009,
    )


def _route_standard(
    task: Task, complexity: str, required_caps: list[str],
    localai_available: bool, localai_model: str, force_claude: bool,
) -> RoutingDecision:
    """Standard mode: balanced cost/capability."""
    if complexity in ("trivial",) and localai_available and not force_claude:
        return RoutingDecision(
            backend="localai", model=localai_model, effort="low",
            reason="standard: LocalAI for trivial task",
            confidence_tier="trainee",
            fallback_backend="claude-code", fallback_model="sonnet",
        )

    if complexity in ("complex", "critical"):
        return RoutingDecision(
            backend="claude-code", model="opus", effort="high",
            reason=f"standard: Claude opus for {complexity} task",
            confidence_tier="expert", estimated_cost=0.045,
        )

    effort = "medium" if complexity in ("simple", "medium") else "high"
    return RoutingDecision(
        backend="claude-code", model="sonnet", effort=effort,
        reason=f"standard: Claude sonnet for {complexity} task",
        confidence_tier="standard", estimated_cost=0.009,
    )


def _route_blitz(task: Task, complexity: str) -> RoutingDecision:
    """Blitz mode: maximum capability, ignore cost."""
    if complexity in ("trivial", "simple"):
        return RoutingDecision(
            backend="claude-code", model="sonnet", effort="high",
            reason=f"blitz: Claude sonnet (high effort) for {complexity} task",
            confidence_tier="standard", estimated_cost=0.009,
        )

    return RoutingDecision(
        backend="claude-code", model="opus", effort="max",
        reason=f"blitz: Claude opus (max effort) for {complexity} task",
        confidence_tier="expert", estimated_cost=0.045,
    )


# \u2500\u2500\u2500 Fallback Execution \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def execute_fallback(
    decision: RoutingDecision,
    failure_reason: str,
) -> Optional[RoutingDecision]:
    """Execute fallback routing when primary backend fails.

    Returns a new RoutingDecision for the fallback backend, or None
    if no fallback is available. Records fallback provenance.
    """
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
        reason=(
            f"fallback from {decision.backend}: {failure_reason} "
            f"\u2192 {decision.fallback_backend}/{fallback_model}"
        ),
        confidence_tier=tier,
        estimated_cost=fallback_def.cost_per_1k_input * 5,  # rough estimate
    )


# \u2500\u2500\u2500 Health Checks \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _apply_health_check(
    decision: RoutingDecision,
    dashboard: "BackendHealthDashboard",
) -> RoutingDecision:
    """Check if the chosen backend is healthy via BackendHealthDashboard.

    If the backend is DOWN, attempt fallback using execute_fallback().
    If no fallback available, queue the task.
    """
    from fleet.core.backend_health import BackendStatus

    state = dashboard.get(decision.backend)
    if state is None:
        return decision  # No health data — proceed as normal

    if state.status == BackendStatus.DOWN:
        fallback = execute_fallback(decision, f"health: {decision.backend} is DOWN")
        if fallback is not None:
            return fallback
        # No fallback — queue
        return RoutingDecision(
            backend="queue",
            model="",
            effort="low",
            reason=f"{decision.backend} DOWN, no healthy fallback",
            confidence_tier="standard",
        )

    return decision


async def check_backend_health(name: str) -> bool:
    """Check if a backend is reachable.

    Updates the registry's ``available`` flag.
    """
    backend = BACKEND_REGISTRY.get(name)
    if not backend:
        return False

    if not backend.health_check_url:
        return True  # No health check = assume available

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