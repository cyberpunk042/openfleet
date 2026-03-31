"""Tests for storm monitor — detection, severity, circuit breakers."""

import time

from fleet.core.storm_monitor import (
    CONFIRMATION_SECONDS,
    CircuitBreaker,
    StormDiagnostic,
    StormIndicator,
    StormMonitor,
    StormSeverity,
    severity_index,
)


# ─── Severity Ordering ──────────────────────────────────────────────


def test_severity_order():
    assert severity_index(StormSeverity.CLEAR) == 0
    assert severity_index(StormSeverity.CRITICAL) == 4
    assert severity_index(StormSeverity.WARNING) < severity_index(StormSeverity.STORM)


def test_severity_unknown_returns_zero():
    assert severity_index("UNKNOWN") == 0


# ─── StormIndicator ─────────────────────────────────────────────────


def test_indicator_auto_timestamps():
    ind = StormIndicator(name="test", value="val")
    assert ind.detected_at > 0
    assert ind.confirmed is False


# ─── StormMonitor: Basic Evaluation ─────────────────────────────────


def test_monitor_starts_clear():
    m = StormMonitor()
    assert m.severity == StormSeverity.CLEAR
    assert m.evaluate() == StormSeverity.CLEAR


def test_monitor_unconfirmed_indicator_stays_clear():
    """Unconfirmed indicators don't escalate severity."""
    m = StormMonitor()
    m.report_indicator("test", "val")
    assert m.evaluate() == StormSeverity.CLEAR  # Not yet confirmed


def test_monitor_confirmed_indicator_escalates():
    """One confirmed indicator → WATCH."""
    m = StormMonitor()
    # Manually confirm by backdating
    m._indicators["test"] = StormIndicator(
        name="test", value="val",
        detected_at=time.time() - 120, confirmed=True,
    )
    assert m.evaluate() == StormSeverity.WATCH


def test_monitor_two_confirmed_is_warning():
    m = StormMonitor()
    past = time.time() - 300
    m._indicators["a"] = StormIndicator(name="a", value="", detected_at=past, confirmed=True)
    m._indicators["b"] = StormIndicator(name="b", value="", detected_at=past, confirmed=True)
    assert m.evaluate() == StormSeverity.WARNING


def test_monitor_three_confirmed_is_storm():
    m = StormMonitor()
    past = time.time() - 300
    for name in ["a", "b", "c"]:
        m._indicators[name] = StormIndicator(
            name=name, value="", detected_at=past, confirmed=True,
        )
    assert m.evaluate() == StormSeverity.STORM


def test_monitor_fast_climb_plus_burst_is_critical():
    m = StormMonitor()
    past = time.time() - 300
    m._indicators["fast_climb"] = StormIndicator(
        name="fast_climb", value="", detected_at=past, confirmed=True,
    )
    m._indicators["session_burst"] = StormIndicator(
        name="session_burst", value="", detected_at=past, confirmed=True,
    )
    assert m.evaluate() == StormSeverity.CRITICAL


def test_monitor_clear_indicator_removes():
    m = StormMonitor()
    m.report_indicator("test", "val")
    assert "test" in m._indicators
    m.clear_indicator("test")
    assert "test" not in m._indicators


# ─── Session Tracking ────────────────────────────────────────────────


def test_session_counting():
    m = StormMonitor()
    for _ in range(5):
        m.report_session()
    assert m.sessions_last_hour == 5


def test_void_session_percentage():
    m = StormMonitor()
    for _ in range(8):
        m.report_session(void=False)
    for _ in range(2):
        m.report_session(void=True)
    assert m.void_session_pct == 20.0


def test_session_burst_triggers_indicator():
    """More than 10 sessions in 60 seconds triggers session_burst."""
    m = StormMonitor()
    for _ in range(12):
        m.report_session()
    assert "session_burst" in m._indicators


def test_void_rate_triggers_indicator():
    """>50% void sessions triggers void_sessions indicator."""
    m = StormMonitor()
    for _ in range(6):
        m.report_session(void=True)
    for _ in range(4):
        m.report_session(void=False)
    assert "void_sessions" in m._indicators


# ─── Dispatch Tracking ──────────────────────────────────────────────


def test_dispatch_counting():
    m = StormMonitor()
    for _ in range(3):
        m.report_dispatch()
    assert m.dispatches_last_hour == 3


# ─── Diagnostics ────────────────────────────────────────────────────


def test_diagnostic_capture():
    m = StormMonitor()
    diag = m.capture_diagnostic(budget_mode="standard")
    assert diag.severity == StormSeverity.CLEAR
    assert diag.budget_mode == "standard"
    assert diag.timestamp != ""


def test_diagnostic_to_dict():
    diag = StormDiagnostic(
        severity="WARNING",
        indicators=["session_burst: 15/min"],
        sessions_last_hour=20,
        budget_mode="economic",
    )
    d = diag.to_dict()
    assert d["severity"] == "WARNING"
    assert "session_burst: 15/min" in d["indicators"]


def test_diagnostic_format_summary():
    diag = StormDiagnostic(
        severity="STORM",
        indicators=["session_burst", "fast_climb"],
        sessions_last_hour=50,
        void_session_pct=40.0,
        budget_mode="economic",
    )
    summary = diag.format_summary()
    assert "STORM" in summary
    assert "economic" in summary


# ─── Circuit Breaker ────────────────────────────────────────────────


def test_breaker_starts_closed():
    cb = CircuitBreaker(name="test")
    assert cb.state == "CLOSED"
    assert cb.check() is True


def test_breaker_trips_after_threshold():
    cb = CircuitBreaker(name="test", failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.check() is True  # Still closed
    cb.record_failure()  # Third failure → trips
    assert cb.state == "OPEN"
    assert cb.check() is False


def test_breaker_resets_on_success():
    cb = CircuitBreaker(name="test", failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()  # Reset
    assert cb.consecutive_failures == 0
    assert cb.state == "CLOSED"


def test_breaker_half_open_after_cooldown():
    cb = CircuitBreaker(name="test", failure_threshold=1, cooldown_seconds=0.01)
    cb.record_failure()  # Trips
    assert cb.state == "OPEN"
    time.sleep(0.02)  # Wait for cooldown
    assert cb.check() is True  # Should be HALF_OPEN now
    assert cb.state == "HALF_OPEN"


def test_breaker_half_open_success_closes():
    cb = CircuitBreaker(name="test", failure_threshold=1, cooldown_seconds=0.01)
    cb.record_failure()
    time.sleep(0.02)
    cb.check()  # → HALF_OPEN
    cb.record_success()  # → CLOSED
    assert cb.state == "CLOSED"
    assert cb.consecutive_failures == 0


def test_breaker_half_open_failure_reopens():
    cb = CircuitBreaker(name="test", failure_threshold=1, cooldown_seconds=0.01)
    cb.record_failure()
    time.sleep(0.02)
    cb.check()  # → HALF_OPEN
    cb.record_failure()  # → OPEN again with doubled cooldown
    assert cb.state == "OPEN"
    assert cb.trip_count == 2


def test_breaker_cooldown_multiplier():
    cb = CircuitBreaker(
        name="test", failure_threshold=1,
        cooldown_seconds=10.0, cooldown_multiplier=2.0,
    )
    cb.record_failure()  # Trip 1
    assert cb.cooldown_seconds == 10.0
    # Simulate cooldown expiry → half-open → fail again
    cb.state = "HALF_OPEN"
    cb.record_failure()  # Trip 2 → doubles cooldown
    assert cb.cooldown_seconds == 20.0


def test_breaker_max_cooldown():
    cb = CircuitBreaker(
        name="test", failure_threshold=1,
        cooldown_seconds=2000.0, cooldown_multiplier=2.0, max_cooldown=3600.0,
    )
    cb.record_failure()
    cb.state = "HALF_OPEN"
    cb.record_failure()  # Would be 4000 but capped at 3600
    assert cb.cooldown_seconds == 3600.0


def test_breaker_is_open_property():
    cb = CircuitBreaker(name="test", failure_threshold=1)
    assert cb.is_open is False
    cb.record_failure()
    assert cb.is_open is True


# ─── Agent and Backend Breakers ──────────────────────────────────────


def test_agent_breaker_creation():
    m = StormMonitor()
    cb = m.get_agent_breaker("software-engineer")
    assert cb.name == "agent:software-engineer"
    assert cb.failure_threshold == 3
    # Same instance on second call
    cb2 = m.get_agent_breaker("software-engineer")
    assert cb is cb2


def test_backend_breaker_creation():
    m = StormMonitor()
    cb = m.get_backend_breaker("localai")
    assert cb.name == "backend:localai"
    assert cb.cooldown_seconds == 120


# ─── Status Formatting ──────────────────────────────────────────────


def test_format_status():
    m = StormMonitor()
    status = m.format_status()
    assert "CLEAR" in status
    assert "Sessions/hr" in status


# ─── Diagnostic Persistence (M-SP03) ──────────────────────────────


def test_diagnostic_persistence(tmp_path):
    """Diagnostic snapshots persist to disk as JSON."""
    import json

    from fleet.cli.orchestrator import _persist_diagnostic

    m = StormMonitor()
    diag = m.capture_diagnostic(budget_mode="economic")
    fleet_dir = str(tmp_path)

    _persist_diagnostic(diag, fleet_dir)

    diag_dir = tmp_path / "state" / "diagnostics"
    assert diag_dir.exists()
    files = list(diag_dir.iterdir())
    assert len(files) == 1

    with open(files[0]) as f:
        data = json.load(f)
    assert data["severity"] == "CLEAR"
    assert data["budget_mode"] == "economic"


def test_diagnostic_persistence_caps_at_50(tmp_path):
    """Only the last 50 diagnostics are kept on disk."""
    from fleet.cli.orchestrator import _persist_diagnostic

    m = StormMonitor()
    fleet_dir = str(tmp_path)

    for i in range(55):
        diag = m.capture_diagnostic(budget_mode="standard")
        # Fake unique timestamps
        diag.timestamp = f"2026-03-31T00:{i:02d}:00"
        _persist_diagnostic(diag, fleet_dir)

    diag_dir = tmp_path / "state" / "diagnostics"
    files = list(diag_dir.iterdir())
    assert len(files) == 50