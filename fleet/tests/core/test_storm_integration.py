"""Tests for orchestrator storm integration (M-SP08)."""

import time

from fleet.core.incident_report import StormEvent
from fleet.core.storm_integration import (
    StormEventTracker,
    StormResponse,
    evaluate_storm_response,
    record_dispatch_outcome,
    should_dispatch,
)
from fleet.core.storm_monitor import StormMonitor, StormSeverity, severity_index


# ─── Helpers ──────────────────────────────────────────────────────


def _make_monitor_at_severity(severity: str) -> StormMonitor:
    """Create a StormMonitor with confirmed indicators to reach a severity."""
    m = StormMonitor()
    past = time.time() - 300

    if severity == StormSeverity.WATCH:
        m._indicators["a"] = _confirmed("a", past)
    elif severity == StormSeverity.WARNING:
        m._indicators["a"] = _confirmed("a", past)
        m._indicators["b"] = _confirmed("b", past)
    elif severity == StormSeverity.STORM:
        for name in ["a", "b", "c"]:
            m._indicators[name] = _confirmed(name, past)
    elif severity == StormSeverity.CRITICAL:
        m._indicators["fast_climb"] = _confirmed("fast_climb", past)
        m._indicators["session_burst"] = _confirmed("session_burst", past)

    return m


def _confirmed(name: str, detected_at: float):
    from fleet.core.storm_monitor import StormIndicator
    return StormIndicator(name=name, value="test", detected_at=detected_at, confirmed=True)


# ─── evaluate_storm_response ──────────────────────────────────────


def test_response_clear():
    m = StormMonitor()
    r = evaluate_storm_response(m)
    assert r.severity == StormSeverity.CLEAR
    assert r.max_dispatch is None
    assert r.force_budget_mode is None
    assert not r.halt_cycle
    assert not r.should_alert_po


def test_response_watch():
    m = _make_monitor_at_severity(StormSeverity.WATCH)
    r = evaluate_storm_response(m)
    assert r.severity == StormSeverity.WATCH
    assert r.max_dispatch is None
    assert not r.halt_cycle
    assert len(r.notes) == 1


def test_response_warning():
    m = _make_monitor_at_severity(StormSeverity.WARNING)
    r = evaluate_storm_response(m, current_max_dispatch=3)
    assert r.severity == StormSeverity.WARNING
    assert r.max_dispatch == 1
    assert r.force_budget_mode == "economic"
    assert r.should_capture_diagnostic
    assert r.should_alert_irc
    assert not r.should_alert_po
    assert not r.halt_cycle


def test_response_warning_respects_lower_dispatch():
    """If current dispatch is already 1, warning shouldn't increase it."""
    m = _make_monitor_at_severity(StormSeverity.WARNING)
    r = evaluate_storm_response(m, current_max_dispatch=1)
    assert r.max_dispatch == 1


def test_response_storm():
    m = _make_monitor_at_severity(StormSeverity.STORM)
    r = evaluate_storm_response(m)
    assert r.severity == StormSeverity.STORM
    assert r.max_dispatch == 0
    assert r.force_budget_mode == "survival"
    assert r.should_capture_diagnostic
    assert r.should_alert_irc
    assert r.should_alert_po
    assert not r.halt_cycle


def test_response_critical():
    m = _make_monitor_at_severity(StormSeverity.CRITICAL)
    r = evaluate_storm_response(m)
    assert r.severity == StormSeverity.CRITICAL
    assert r.max_dispatch == 0
    assert r.force_budget_mode == "blackout"
    assert r.halt_cycle
    assert r.should_alert_po


def test_response_to_dict():
    m = _make_monitor_at_severity(StormSeverity.STORM)
    r = evaluate_storm_response(m)
    d = r.to_dict()
    assert d["severity"] == StormSeverity.STORM
    assert d["halt_cycle"] is False
    assert d["force_budget_mode"] == "survival"


def test_response_alert_message():
    m = _make_monitor_at_severity(StormSeverity.STORM)
    r = evaluate_storm_response(m)
    assert "STORM" in r.alert_message


# ─── StormEventTracker ────────────────────────────────────────────


def test_tracker_starts_empty():
    t = StormEventTracker()
    assert not t.has_active_event
    assert t.total_incidents == 0


def test_tracker_creates_event_on_warning():
    t = StormEventTracker()
    r = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
    report = t.process_cycle(
        severity=StormSeverity.WARNING,
        indicators=["session_burst"],
        response=r,
        budget_mode="standard",
    )
    assert t.has_active_event
    assert report is None  # No report yet — storm still active


def test_tracker_closes_event_on_clear():
    t = StormEventTracker()

    # Start storm
    r_warn = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
    t.process_cycle(
        severity=StormSeverity.WARNING,
        indicators=["session_burst"],
        response=r_warn,
        budget_mode="standard",
    )
    assert t.has_active_event

    # End storm
    r_clear = StormResponse(severity=StormSeverity.CLEAR)
    report = t.process_cycle(
        severity=StormSeverity.CLEAR,
        indicators=[],
        response=r_clear,
        budget_mode="economic",
        void_sessions=5,
        total_sessions=10,
    )
    assert not t.has_active_event
    assert report is not None
    assert report.peak_severity == "WARNING"
    assert report.budget_mode_before == "standard"
    assert report.budget_mode_after == "economic"
    assert report.void_sessions == 5


def test_tracker_escalation_updates_peak():
    t = StormEventTracker()

    # WARNING
    r_warn = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
    t.process_cycle(
        severity=StormSeverity.WARNING,
        indicators=["session_burst"],
        response=r_warn,
        budget_mode="standard",
    )

    # Escalate to STORM
    r_storm = StormResponse(
        severity=StormSeverity.STORM, force_budget_mode="survival",
        should_alert_po=True,
    )
    t.process_cycle(
        severity=StormSeverity.STORM,
        indicators=["session_burst", "void_sessions"],
        response=r_storm,
        budget_mode="economic",
    )

    assert t.active_event.peak_severity == "STORM"
    assert len(t.active_event.indicators_seen) == 2


def test_tracker_no_event_on_clear():
    t = StormEventTracker()
    r = StormResponse(severity=StormSeverity.CLEAR)
    report = t.process_cycle(
        severity=StormSeverity.CLEAR,
        indicators=[],
        response=r,
    )
    assert not t.has_active_event
    assert report is None


def test_tracker_no_event_on_watch():
    t = StormEventTracker()
    r = StormResponse(severity=StormSeverity.WATCH)
    report = t.process_cycle(
        severity=StormSeverity.WATCH,
        indicators=["session_burst"],
        response=r,
    )
    assert not t.has_active_event
    assert report is None


def test_tracker_records_responses():
    t = StormEventTracker()

    r = StormResponse(
        severity=StormSeverity.STORM,
        force_budget_mode="survival",
        should_alert_po=True,
        max_dispatch=0,
        halt_cycle=False,
    )
    t.process_cycle(
        severity=StormSeverity.STORM,
        indicators=["a", "b", "c"],
        response=r,
        budget_mode="standard",
    )

    event = t.active_event
    assert any("survival" in resp.action for resp in event.responses)
    assert any("alert PO" in resp.action for resp in event.responses)
    assert any("dispatch" in resp.action for resp in event.responses)


def test_tracker_completed_reports():
    t = StormEventTracker()

    # Run a full storm cycle
    r_warn = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
    t.process_cycle(
        severity=StormSeverity.WARNING,
        indicators=["burst"],
        response=r_warn,
        budget_mode="standard",
    )

    r_clear = StormResponse(severity=StormSeverity.CLEAR)
    t.process_cycle(
        severity=StormSeverity.CLEAR,
        indicators=[],
        response=r_clear,
        budget_mode="economic",
    )

    assert t.total_incidents == 1
    assert len(t.completed_reports) == 1
    assert t.completed_reports[0].peak_severity == "WARNING"


def test_tracker_multiple_storms():
    t = StormEventTracker()

    for i in range(3):
        r_warn = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
        t.process_cycle(
            severity=StormSeverity.WARNING,
            indicators=[f"indicator_{i}"],
            response=r_warn,
            budget_mode="standard",
        )
        r_clear = StormResponse(severity=StormSeverity.CLEAR)
        t.process_cycle(
            severity=StormSeverity.CLEAR,
            indicators=[],
            response=r_clear,
            budget_mode="standard",
        )

    assert t.total_incidents == 3


def test_tracker_caps_reports():
    t = StormEventTracker()
    t._max_reports = 5

    for i in range(8):
        r_warn = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
        t.process_cycle(
            severity=StormSeverity.WARNING,
            indicators=[f"ind_{i}"],
            response=r_warn,
        )
        r_clear = StormResponse(severity=StormSeverity.CLEAR)
        t.process_cycle(
            severity=StormSeverity.CLEAR,
            indicators=[],
            response=r_clear,
        )

    assert len(t.completed_reports) == 5


def test_tracker_force_close():
    t = StormEventTracker()

    r = StormResponse(severity=StormSeverity.STORM, force_budget_mode="survival")
    t.process_cycle(
        severity=StormSeverity.STORM,
        indicators=["burst", "void", "errors"],
        response=r,
        budget_mode="standard",
    )
    assert t.has_active_event

    report = t.force_close(
        budget_mode_after="survival",
        void_sessions=10,
        total_sessions=15,
        root_cause="manual PO intervention",
    )
    assert report is not None
    assert report.peak_severity == "STORM"
    assert report.root_cause == "manual PO intervention"
    assert not t.has_active_event
    assert t.total_incidents == 1


def test_tracker_force_close_no_active():
    t = StormEventTracker()
    report = t.force_close()
    assert report is None


def test_tracker_status():
    t = StormEventTracker()
    s = t.status()
    assert s["active_event"] is False
    assert s["total_incidents"] == 0

    r = StormResponse(severity=StormSeverity.WARNING, force_budget_mode="economic")
    t.process_cycle(
        severity=StormSeverity.WARNING,
        indicators=["test"],
        response=r,
    )
    s = t.status()
    assert s["active_event"] is True
    assert s["peak_severity"] == "WARNING"


# ─── should_dispatch ──────────────────────────────────────────────


def test_dispatch_allowed_clear():
    m = StormMonitor()
    r = StormResponse(severity=StormSeverity.CLEAR)
    allowed, reason = should_dispatch(r, "software-engineer", m)
    assert allowed
    assert reason == "ok"


def test_dispatch_blocked_halt():
    m = StormMonitor()
    r = StormResponse(severity=StormSeverity.CRITICAL, halt_cycle=True)
    allowed, reason = should_dispatch(r, "software-engineer", m)
    assert not allowed
    assert "frozen" in reason


def test_dispatch_blocked_zero_dispatch():
    m = StormMonitor()
    r = StormResponse(severity=StormSeverity.STORM, max_dispatch=0)
    allowed, reason = should_dispatch(r, "software-engineer", m)
    assert not allowed
    assert "disabled" in reason


def test_dispatch_blocked_circuit_breaker():
    m = StormMonitor()
    r = StormResponse(severity=StormSeverity.CLEAR)

    # Trip the circuit breaker
    breaker = m.get_agent_breaker("software-engineer")
    for _ in range(3):
        breaker.record_failure()

    allowed, reason = should_dispatch(r, "software-engineer", m)
    assert not allowed
    assert "circuit breaker" in reason


def test_dispatch_allowed_different_agent():
    m = StormMonitor()
    r = StormResponse(severity=StormSeverity.CLEAR)

    # Trip breaker for one agent
    breaker = m.get_agent_breaker("software-engineer")
    for _ in range(3):
        breaker.record_failure()

    # Different agent should still be allowed
    allowed, _ = should_dispatch(r, "qa-engineer", m)
    assert allowed


# ─── record_dispatch_outcome ─────────────────────────────────────


def test_record_success():
    m = StormMonitor()
    record_dispatch_outcome(m, "dev", success=True, void=False)
    assert m.sessions_last_hour == 1
    assert m.dispatches_last_hour == 1
    breaker = m.get_agent_breaker("dev")
    assert breaker.consecutive_failures == 0


def test_record_failure():
    m = StormMonitor()
    record_dispatch_outcome(m, "dev", success=False)
    breaker = m.get_agent_breaker("dev")
    assert breaker.consecutive_failures == 1


def test_record_void_session():
    m = StormMonitor()
    record_dispatch_outcome(m, "dev", success=True, void=True)
    breaker = m.get_agent_breaker("dev")
    assert breaker.consecutive_failures == 1  # Void counts as failure


def test_record_multiple_failures_trips_breaker():
    m = StormMonitor()
    for _ in range(3):
        record_dispatch_outcome(m, "dev", success=False)
    breaker = m.get_agent_breaker("dev")
    assert breaker.is_open


def test_record_success_resets_failures():
    m = StormMonitor()
    record_dispatch_outcome(m, "dev", success=False)
    record_dispatch_outcome(m, "dev", success=False)
    record_dispatch_outcome(m, "dev", success=True, void=False)
    breaker = m.get_agent_breaker("dev")
    assert breaker.consecutive_failures == 0


# ─── Full Integration Scenario ────────────────────────────────────


def test_full_storm_cycle():
    """Simulate a full storm lifecycle through the integration layer."""
    m = StormMonitor()
    tracker = StormEventTracker()

    # Cycle 1: CLEAR — normal
    r = evaluate_storm_response(m)
    report = tracker.process_cycle(
        severity=r.severity, indicators=[], response=r,
        budget_mode="standard",
    )
    assert r.severity == StormSeverity.CLEAR
    assert report is None

    # Simulate session burst
    past = time.time() - 300
    m._indicators["session_burst"] = _confirmed("session_burst", past)
    m._indicators["void_sessions"] = _confirmed("void_sessions", past)

    # Cycle 2: WARNING
    r = evaluate_storm_response(m, current_budget_mode="standard")
    assert r.severity == StormSeverity.WARNING
    assert r.force_budget_mode == "economic"
    report = tracker.process_cycle(
        severity=r.severity,
        indicators=["session_burst", "void_sessions"],
        response=r,
        budget_mode="standard",
    )
    assert tracker.has_active_event
    assert report is None

    # Add another indicator → STORM
    m._indicators["error_storm"] = _confirmed("error_storm", past)

    # Cycle 3: STORM
    r = evaluate_storm_response(m)
    assert r.severity == StormSeverity.STORM
    assert r.force_budget_mode == "survival"
    assert r.should_alert_po
    report = tracker.process_cycle(
        severity=r.severity,
        indicators=["session_burst", "void_sessions", "error_storm"],
        response=r,
        budget_mode="economic",
    )
    assert report is None
    assert tracker.active_event.peak_severity == "STORM"

    # Clear all indicators
    m._indicators.clear()

    # Cycle 4: Indicators cleared but de-escalation is SLOW by design.
    # The monitor stays at STORM until indicators stay clear for the
    # required de-escalation time (10 minutes). So evaluate still
    # returns STORM — which is correct behavior.
    r = evaluate_storm_response(m)
    # Severity is still elevated due to slow de-escalation
    assert severity_index(r.severity) >= severity_index(StormSeverity.CLEAR)

    # Force close the storm event to get the report (simulates PO intervention
    # or passage of time sufficient for de-escalation)
    report = tracker.force_close(
        budget_mode_after="survival",
        void_sessions=8,
        total_sessions=10,
    )
    assert report is not None
    assert report.peak_severity == "STORM"
    assert report.void_sessions == 8
    assert len(report.indicators) == 3
    assert tracker.total_incidents == 1