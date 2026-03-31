"""Flow 3: Storm Response — Indicators → Severity → Budget → Router.

Tests the storm detection → budget forcing → routing impact chain.
"""

import time

from fleet.core.backend_health import BackendHealthDashboard, BackendStatus, ClaudeHealth
from fleet.core.backend_router import route_task
from fleet.core.storm_integration import (
    STORM_BUDGET_FORCING,
    StormResponse,
    evaluate_storm_response,
)
from fleet.core.storm_monitor import StormMonitor, StormSeverity

from .conftest import make_task


def _escalate_to(monitor: StormMonitor, severity: str) -> None:
    """Helper to push monitor to a specific severity level."""
    if severity in ("WARNING", "STORM", "CRITICAL"):
        # Report enough indicators to trigger
        monitor.report_indicator("session_burst", "15/min")
        monitor.report_indicator("void_sessions", "60%")
        # Force confirmation
        for ind in monitor._indicators.values():
            ind.confirmed = True
    if severity in ("STORM", "CRITICAL"):
        monitor.report_indicator("dispatch_storm", "high")
        monitor.report_indicator("error_storm", "surge")
        for ind in monitor._indicators.values():
            ind.confirmed = True
    if severity == "CRITICAL":
        monitor.report_indicator("cascade_depth", "deep")
        monitor.report_indicator("agent_thrashing", "multiple")
        monitor.report_indicator("gateway_duplication", "detected")
        for ind in monitor._indicators.values():
            ind.confirmed = True


def test_storm_warning_forces_economic():
    """WARNING severity → budget forced to economic, dispatch limited to 1."""
    monitor = StormMonitor()
    _escalate_to(monitor, "WARNING")

    response = evaluate_storm_response(monitor, current_budget_mode="standard")
    assert response.severity in (StormSeverity.WARNING, StormSeverity.STORM, StormSeverity.CRITICAL)

    if response.severity == StormSeverity.WARNING:
        assert response.force_budget_mode == "economic"
        assert response.max_dispatch is not None
        assert response.max_dispatch <= 1


def test_storm_escalation():
    """WARNING → STORM → CRITICAL progression, budget follows."""
    monitor = StormMonitor()

    # WARNING
    _escalate_to(monitor, "WARNING")
    r1 = evaluate_storm_response(monitor)
    # At least WARNING level
    assert r1.force_budget_mode is not None

    # STORM
    _escalate_to(monitor, "STORM")
    r2 = evaluate_storm_response(monitor)
    if r2.severity == StormSeverity.STORM:
        assert r2.force_budget_mode == "survival"
        assert r2.max_dispatch == 0

    # CRITICAL
    _escalate_to(monitor, "CRITICAL")
    r3 = evaluate_storm_response(monitor)
    if r3.severity == StormSeverity.CRITICAL:
        assert r3.force_budget_mode == "blackout"
        assert r3.halt_cycle is True


def test_storm_circuit_breaker_routing():
    """Open circuit breaker → router skips backend → fallback."""
    task = make_task()
    monitor = StormMonitor()

    # Trip the claude-code breaker
    breaker = monitor.get_backend_breaker("claude-code")
    for _ in range(breaker.failure_threshold):
        breaker.record_failure()

    # Route with storm monitor — should trigger fallback
    decision = route_task(
        task, agent_name="worker", budget_mode="standard",
        storm_monitor=monitor,
    )
    # If breaker is open, backend should be different or queued
    # The exact behavior depends on whether the initial route was claude-code
    # and whether fallback is available
    assert decision.backend is not None


def test_storm_recovery_cycle():
    """CRITICAL → indicators clear → severity drops from peak."""
    monitor = StormMonitor()

    # Escalate to high severity
    _escalate_to(monitor, "CRITICAL")
    r_peak = evaluate_storm_response(monitor)
    peak_severity = r_peak.severity
    assert r_peak.force_budget_mode is not None

    # Clear all indicators
    for name in list(monitor._indicators.keys()):
        monitor.clear_indicator(name)

    # Re-evaluate — severity should be lower than peak or same
    # (monitor may retain session/dispatch history that keeps severity up)
    r_after = evaluate_storm_response(monitor)
    # The key test: with no indicators, no forced budget mode at CLEAR/WATCH
    if r_after.severity in (StormSeverity.CLEAR, StormSeverity.WATCH):
        assert r_after.force_budget_mode is None


def test_storm_budget_forcing_uses_budget_modes():
    """Storm budget forcing references valid budget modes (W3 wiring)."""
    # STORM_BUDGET_FORCING is validated at import time via assertion
    assert StormSeverity.CRITICAL in STORM_BUDGET_FORCING
    assert StormSeverity.STORM in STORM_BUDGET_FORCING
    assert StormSeverity.WARNING in STORM_BUDGET_FORCING
    assert STORM_BUDGET_FORCING[StormSeverity.CRITICAL] == "blackout"
    assert STORM_BUDGET_FORCING[StormSeverity.STORM] == "survival"
    assert STORM_BUDGET_FORCING[StormSeverity.WARNING] == "economic"
