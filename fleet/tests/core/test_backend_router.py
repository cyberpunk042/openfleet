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


def test_four_backends_registered():
    assert len(BACKEND_REGISTRY) == 4
    for name in ["claude-code", "localai", "openrouter-free", "direct"]:
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
    assert len(backends) == 4


def test_list_backends_available_only():
    backends = list_backends(available_only=True)
    assert len(backends) == 4  # All default to available


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


# ─── Routing: Blackout Mode ────────────────────────────────────────


def test_blackout_always_direct():
    decision = route_task(_task(sp=13, task_type="epic"), "architect", "blackout")
    assert decision.backend == "direct"
    assert "blackout" in decision.reason


# ─── Routing: Survival Mode ───────────────────────────────────────


def test_survival_trivial_uses_localai():
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", "survival")
    assert decision.backend == "localai"
    assert decision.confidence_tier == "trainee"
    assert decision.fallback_backend == "openrouter-free"


def test_survival_medium_uses_openrouter():
    decision = route_task(_task(sp=3), "worker", "survival")
    assert decision.backend == "openrouter-free"
    assert decision.confidence_tier == "community"


def test_survival_security_agent_forces_claude():
    decision = route_task(_task(sp=1, task_type="subtask"), "devsecops-expert", "survival")
    assert decision.backend == "claude-code"
    assert "override" in decision.reason


def test_survival_no_localai_falls_to_openrouter():
    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker", "survival",
        localai_available=False,
    )
    assert decision.backend == "openrouter-free"


# ─── Routing: Frugal Mode ─────────────────────────────────────────


def test_frugal_simple_uses_localai():
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", "frugal")
    assert decision.backend == "localai"


def test_frugal_medium_uses_openrouter():
    decision = route_task(_task(sp=3), "worker", "frugal")
    assert decision.backend == "openrouter-free"


def test_frugal_complex_uses_sonnet():
    decision = route_task(_task(sp=8), "worker", "frugal")
    assert decision.backend == "claude-code"
    assert decision.model == "sonnet"


def test_frugal_medium_security_uses_claude():
    decision = route_task(_task(sp=3), "devsecops-expert", "frugal")
    assert decision.backend == "claude-code"
    assert decision.model == "sonnet"


# ─── Routing: Economic Mode ───────────────────────────────────────


def test_economic_trivial_uses_localai():
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", "economic")
    assert decision.backend == "localai"


def test_economic_complex_uses_sonnet():
    decision = route_task(_task(sp=8), "worker", "economic")
    assert decision.backend == "claude-code"
    assert decision.model == "sonnet"
    assert decision.effort == "high"


def test_economic_security_skips_localai():
    decision = route_task(_task(sp=1, task_type="subtask"), "architect", "economic")
    assert decision.backend == "claude-code"


# ─── Routing: Standard Mode ───────────────────────────────────────


def test_standard_trivial_uses_localai():
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", "standard")
    assert decision.backend == "localai"


def test_standard_complex_uses_opus():
    decision = route_task(_task(sp=8), "worker", "standard")
    assert decision.backend == "claude-code"
    assert decision.model == "opus"
    assert decision.confidence_tier == "expert"


def test_standard_medium_uses_sonnet():
    decision = route_task(_task(sp=3), "worker", "standard")
    assert decision.backend == "claude-code"
    assert decision.model == "sonnet"


def test_standard_critical_uses_opus():
    decision = route_task(_task(task_type="epic"), "worker", "standard")
    assert decision.backend == "claude-code"
    assert decision.model == "opus"


# ─── Routing: Blitz Mode ──────────────────────────────────────────


def test_blitz_trivial_uses_sonnet_high():
    decision = route_task(_task(sp=1, task_type="subtask"), "worker", "blitz")
    assert decision.backend == "claude-code"
    assert decision.model == "sonnet"
    assert decision.effort == "high"


def test_blitz_complex_uses_opus_max():
    decision = route_task(_task(sp=8), "worker", "blitz")
    assert decision.backend == "claude-code"
    assert decision.model == "opus"
    assert decision.effort == "max"


# ─── Fallback Execution ───────────────────────────────────────────


def test_fallback_returns_new_decision():
    original = RoutingDecision(
        backend="localai", model="hermes-3b", effort="low",
        reason="survival: LocalAI for trivial task",
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
        reason="standard: Claude opus for complex task",
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
        _task(sp=1, task_type="subtask"), "worker", "standard",
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
        _task(sp=1, task_type="subtask"), "worker", "standard",
        storm_monitor=monitor,
    )
    # Should have fallen back from localai to claude-code/sonnet
    assert decision.backend != "localai"
    assert "circuit breaker" in decision.reason or "fallback" in decision.reason


def test_both_breakers_open_queues_task():
    """When primary AND fallback breakers are both OPEN, task is queued."""
    monitor = StormMonitor()
    # Trip localai breaker
    localai_breaker = monitor.get_backend_breaker("localai")
    for _ in range(3):
        localai_breaker.record_failure()
    # Trip claude-code breaker (the fallback for standard/localai)
    claude_breaker = monitor.get_backend_breaker("claude-code")
    for _ in range(3):
        claude_breaker.record_failure()

    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker", "standard",
        storm_monitor=monitor,
    )
    assert decision.backend == "direct"
    assert "queued" in decision.reason


def test_breaker_open_no_fallback_queues():
    """Backend with no fallback + open breaker = queued."""
    monitor = StormMonitor()
    # Trip claude-code breaker — blitz has no fallback
    breaker = monitor.get_backend_breaker("claude-code")
    for _ in range(3):
        breaker.record_failure()

    decision = route_task(
        _task(sp=8), "worker", "blitz",
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
        _task(sp=1, task_type="subtask"), "worker", "standard",
    )
    assert decision.backend == "localai"


def test_survival_breaker_open_fallback_chain():
    """In survival mode, localai open -> fallback to openrouter-free."""
    monitor = StormMonitor()
    breaker = monitor.get_backend_breaker("localai")
    for _ in range(3):
        breaker.record_failure()

    decision = route_task(
        _task(sp=1, task_type="subtask"), "worker", "survival",
        storm_monitor=monitor,
    )
    assert decision.backend == "openrouter-free"
    assert "circuit breaker" in decision.reason or "fallback" in decision.reason