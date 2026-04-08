"""Tests for multi-backend routing — registry, routing, fallback, circuit breakers."""

from fleet.core.backend_router import (
    BACKEND_REGISTRY,
    BackendDefinition,
    RoutingDecision,
    execute_fallback,
    get_backend,
    list_backends,
    list_free_backends,
    record_backend_result,
    route_task,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.storm_monitor import StormMonitor


def _task(
    sp: int = 0, task_type: str = "task",
) -> Task:
    return Task(
        id="t1", board_id="b1", title="Test", status=TaskStatus.INBOX,
        custom_fields=TaskCustomFields(
            story_points=sp, task_type=task_type,
        ),
    )


# ─── Backend Registry ──────────────────────────────────────────────


def test_five_backends_registered():
    assert len(BACKEND_REGISTRY) == 5
    for name in ["claude-code", "localai", "openrouter-free", "openrouter-qwen36plus", "direct"]:
        assert name in BACKEND_REGISTRY


def test_get_backend_returns_definition():
    b = get_backend("claude-code")
    assert b is not None
    assert b.name == "claude-code"
    assert b.type == "cloud"


def test_get_backend_unknown_returns_none():
    assert get_backend("nonexistent") is None


def test_list_backends_all():
    backends = list_backends()
    assert len(backends) == 5


def test_list_backends_available_only():
    backends = list_backends(available_only=True)
    assert len(backends) == 5  # All default to available


def test_list_free_backends():
    free = list_free_backends()
    names = {b.name for b in free}
    assert "localai" in names
    assert "openrouter-free" in names
    assert "direct" in names
    assert "claude-code" not in names


def test_claude_code_is_not_free():
    b = get_backend("claude-code")
    assert b.is_free is False


def test_localai_is_free():
    b = get_backend("localai")
    assert b.is_free is True


def test_backend_has_capability():
    b = get_backend("claude-code")
    assert b.has_capability("reasoning") is True
    assert b.has_capability("nonexistent") is False


def test_localai_lacks_reasoning():
    b = get_backend("localai")
    assert b.has_capability("reasoning") is False
    assert b.has_capability("code") is True


# ─── Routing: Complexity-based (no budget mode) ─────────────────────
# route_task no longer takes budget_mode — it routes by cheapest
# capable backend based on task complexity and agent role.


def test_trivial_task_uses_localai():
    """Trivial subtask routes to LocalAI (cheapest capable) when enabled."""
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", backend_mode="claude+localai")
    assert decision.backend == "localai"
    assert decision.confidence_tier == "trainee"
    assert decision.fallback_backend == "claude-code"


def test_medium_task_routes():
    """Medium complexity task routes to cheapest capable backend."""
    decision = route_task(_task(sp=3), "worker")
    # Medium requires ["structured", "code"] — localai has both
    assert decision.backend in ("localai", "openrouter-free", "claude-code")


def test_complex_task_uses_capable_backend():
    """Complex task requires reasoning — routes to a backend with reasoning capability."""
    decision = route_task(_task(sp=8), "worker")
    # Both openrouter-free and claude-code have reasoning; cheapest wins
    assert decision.backend in ("openrouter-free", "claude-code")


def test_critical_epic_uses_capable_backend():
    """Epic (critical) routes to a backend with reasoning capability."""
    decision = route_task(_task(task_type="epic"), "worker")
    assert decision.backend in ("openrouter-free", "claude-code")


def test_security_agent_skips_trainee_community():
    """Security agent never routed to trainee/community backends."""
    decision = route_task(_task(sp=1, task_type="subtask"), "devsecops-expert")
    assert decision.confidence_tier not in ("trainee", "community")


def test_architecture_agent_skips_trainee_community():
    """Architect agent never routed to trainee/community backends."""
    decision = route_task(_task(sp=1, task_type="subtask"), "architect")
    assert decision.confidence_tier not in ("trainee", "community")


def test_no_localai_trivial_falls_to_next():
    """When LocalAI unavailable, trivial task falls to next capable backend."""
    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        localai_available=False,
    )
    # Should fall to openrouter-free or claude-code
    assert decision.backend != "localai"


def test_story_sp5_routes_to_reasoning_backend():
    """Complex story (SP>=5) requires reasoning — routes to capable backend."""
    decision = route_task(_task(sp=5, task_type="story"), "worker")
    # Both openrouter-free and claude-code have reasoning capability
    assert decision.backend in ("openrouter-free", "claude-code")


# ─── Fallback Execution ───────────────────────────────────────────


def test_fallback_returns_new_decision():
    original = RoutingDecision(
        backend="localai", model="hermes-3b", effort="low",
        reason="trivial task → localai/hermes-3b (cheapest capable)",
        confidence_tier="trainee",
        fallback_backend="openrouter-free", fallback_model="openrouter/free",
    )
    fallback = execute_fallback(original, "localai unreachable")
    assert fallback is not None
    assert fallback.backend == "openrouter-free"
    assert fallback.model == "openrouter/free"
    assert "fallback from localai" in fallback.reason


def test_fallback_no_fallback_returns_none():
    original = RoutingDecision(
        backend="claude-code", model="opus", effort="high",
        reason="complex task → claude-code/opus",
        confidence_tier="expert",
    )
    assert execute_fallback(original, "timeout") is None


def test_fallback_unavailable_backend_returns_none():
    # Temporarily mark openrouter-free as unavailable
    orig_available = BACKEND_REGISTRY["openrouter-free"].available
    BACKEND_REGISTRY["openrouter-free"].available = False
    try:
        original = RoutingDecision(
            backend="localai", model="hermes-3b", effort="low",
            reason="test", confidence_tier="trainee",
            fallback_backend="openrouter-free", fallback_model="openrouter/free",
        )
        assert execute_fallback(original, "fail") is None
    finally:
        BACKEND_REGISTRY["openrouter-free"].available = orig_available


# ─── Complexity Assessment ─────────────────────────────────────────


def test_epic_is_critical():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(task_type="epic")) == "critical"


def test_blocker_is_complex():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(task_type="blocker")) == "complex"


def test_high_sp_is_complex():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(sp=8)) == "complex"


def test_medium_sp_is_medium():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(sp=3)) == "medium"


def test_subtask_sp1_is_trivial():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(sp=1, task_type="subtask")) == "trivial"


def test_story_sp5_is_complex():
    from fleet.core.backend_router import _assess_complexity
    assert _assess_complexity(_task(sp=5, task_type="story")) == "complex"


# ─── Circuit Breaker Integration (M-SP05) ─────────────────────────


def test_healthy_breaker_no_change():
    """When backend breaker is CLOSED, routing decision unchanged."""
    monitor = StormMonitor()
    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        backend_mode="claude+localai",
        storm_monitor=monitor,
    )
    assert decision.backend == "localai"


def test_open_breaker_triggers_fallback():
    """When primary backend breaker is OPEN, route to fallback."""
    monitor = StormMonitor()
    breaker = monitor.get_backend_breaker("localai")
    # Trip the breaker
    for _ in range(3):
        breaker.record_failure()
    assert breaker.is_open

    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        backend_mode="claude+localai",
        storm_monitor=monitor,
    )
    # Should have fallen back from localai
    assert decision.backend != "localai"
    assert "circuit breaker" in decision.reason or "fallback" in decision.reason


def test_both_breakers_open_queues_task():
    """When primary AND fallback breakers are both OPEN, task is queued."""
    monitor = StormMonitor()
    # Trip localai breaker
    localai_breaker = monitor.get_backend_breaker("localai")
    for _ in range(3):
        localai_breaker.record_failure()
    # Trip claude-code breaker (the fallback for localai)
    claude_breaker = monitor.get_backend_breaker("claude-code")
    for _ in range(3):
        claude_breaker.record_failure()

    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        storm_monitor=monitor,
    )
    assert decision.backend == "direct"
    assert "queued" in decision.reason


def test_breaker_open_no_fallback_queues():
    """Backend with no fallback + open breaker = queued."""
    monitor = StormMonitor()
    # Trip claude-code breaker — complex tasks have no fallback from claude
    breaker = monitor.get_backend_breaker("claude-code")
    for _ in range(3):
        breaker.record_failure()

    decision = route_task(
        _task(sp=8), "worker",
        storm_monitor=monitor,
    )
    assert decision.backend == "direct"
    assert "queued" in decision.reason


def test_record_backend_result_success_resets():
    """record_backend_result with success resets the breaker."""
    monitor = StormMonitor()
    breaker = monitor.get_backend_breaker("localai")
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.consecutive_failures == 2

    record_backend_result(monitor, "localai", success=True)
    assert breaker.consecutive_failures == 0


def test_record_backend_result_failure_increments():
    """record_backend_result with failure increments the breaker."""
    monitor = StormMonitor()
    record_backend_result(monitor, "localai", success=False)
    record_backend_result(monitor, "localai", success=False)
    breaker = monitor.get_backend_breaker("localai")
    assert breaker.consecutive_failures == 2


def test_no_storm_monitor_skips_breaker_check():
    """Without storm_monitor, routing proceeds normally (no breaker check)."""
    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        backend_mode="claude+localai",
    )
    assert decision.backend == "localai"


def test_localai_breaker_open_fallback_chain():
    """LocalAI breaker open -> fallback to claude-code."""
    monitor = StormMonitor()
    breaker = monitor.get_backend_breaker("localai")
    for _ in range(3):
        breaker.record_failure()

    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker",
        backend_mode="claude+localai",
        storm_monitor=monitor,
    )
    assert decision.backend != "localai"
    assert "circuit breaker" in decision.reason or "fallback" in decision.reason
