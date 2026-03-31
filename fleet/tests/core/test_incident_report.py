"""Tests for post-incident report generation (M-SP07)."""

import time

from fleet.core.incident_report import (
    IncidentReport,
    ResponseEntry,
    StormEvent,
    build_incident_report,
    _generate_prevention_recommendations,
)


# ─── ResponseEntry ─────────────────────────────────────────────────


def test_response_entry_to_dict():
    r = ResponseEntry(timestamp=1711900800.0, action="force economic mode")
    d = r.to_dict()
    assert d["action"] == "force economic mode"
    assert "time" in d


def test_response_entry_with_detail():
    r = ResponseEntry(
        timestamp=time.time(), action="alert PO",
        detail="via ntfy URGENT",
    )
    d = r.to_dict()
    assert d["detail"] == "via ntfy URGENT"


# ─── IncidentReport: Creation ──────────────────────────────────────


def test_report_auto_generates_id():
    r = IncidentReport()
    assert r.incident_id.startswith("INC-")
    assert r.generated_at != ""


def test_report_auto_computes_duration():
    r = IncidentReport(started_at=100.0, ended_at=580.0)
    assert r.duration_seconds == 480.0


def test_report_manual_fields():
    r = IncidentReport(
        peak_severity="STORM",
        started_at=1000.0,
        ended_at=1480.0,
        indicators=["session_burst", "void_sessions"],
        void_sessions=8,
        total_sessions=10,
        estimated_cost_usd=1.12,
    )
    assert r.peak_severity == "STORM"
    assert r.void_session_pct == 0.0  # Not auto-computed from fields
    assert r.estimated_cost_usd == 1.12


# ─── Duration Display ─────────────────────────────────────────────


def test_duration_display_seconds():
    r = IncidentReport(duration_seconds=45)
    assert r.duration_display == "45s"


def test_duration_display_minutes():
    r = IncidentReport(duration_seconds=480)
    assert r.duration_display == "8m 0s"


def test_duration_display_hours():
    r = IncidentReport(duration_seconds=3720)
    assert r.duration_display == "1h 2m"


# ─── Serialization ────────────────────────────────────────────────


def test_to_dict():
    r = IncidentReport(
        peak_severity="WARNING",
        indicators=["fast_climb"],
        responses=[ResponseEntry(timestamp=time.time(), action="force economic")],
        estimated_cost_usd=0.56,
    )
    d = r.to_dict()
    assert d["peak_severity"] == "WARNING"
    assert d["estimated_cost_usd"] == 0.56
    assert len(d["responses"]) == 1
    assert len(d["indicators"]) == 1


def test_to_dict_empty():
    r = IncidentReport()
    d = r.to_dict()
    assert d["peak_severity"] == ""
    assert d["estimated_cost_usd"] == 0.0
    assert d["void_sessions"] == 0


# ─── Markdown Formatting ──────────────────────────────────────────


def test_format_markdown_contains_severity():
    r = IncidentReport(
        peak_severity="STORM",
        started_at=100.0,
        ended_at=580.0,
        indicators=["session_burst: 15/min", "void_sessions: 80%"],
        estimated_cost_usd=1.40,
    )
    md = r.format_markdown()
    assert "STORM" in md
    assert "session_burst" in md
    assert "$1.40" in md


def test_format_markdown_contains_timeline():
    r = IncidentReport(
        peak_severity="WARNING",
        responses=[
            ResponseEntry(timestamp=time.time(), action="force economic mode"),
            ResponseEntry(timestamp=time.time(), action="alert PO"),
        ],
    )
    md = r.format_markdown()
    assert "force economic mode" in md
    assert "alert PO" in md


def test_format_markdown_contains_prevention():
    r = IncidentReport(
        peak_severity="STORM",
        prevention_recommendations=[
            "Stagger heartbeats after restart",
            "Reduce concurrency",
        ],
    )
    md = r.format_markdown()
    assert "Stagger heartbeats" in md
    assert "Reduce concurrency" in md


def test_format_markdown_budget_mode():
    r = IncidentReport(
        peak_severity="WARNING",
        budget_mode_before="standard",
        budget_mode_after="economic",
    )
    md = r.format_markdown()
    assert "standard" in md
    assert "economic" in md


def test_format_markdown_void_sessions():
    r = IncidentReport(
        peak_severity="STORM",
        void_sessions=8,
        total_sessions=10,
        void_session_pct=80.0,
        estimated_cost_usd=1.12,
    )
    md = r.format_markdown()
    assert "8 void sessions" in md
    assert "10 total" in md


def test_format_markdown_root_cause():
    r = IncidentReport(
        peak_severity="STORM",
        root_cause="Gateway restart fired 11 heartbeats simultaneously.",
    )
    md = r.format_markdown()
    assert "Root Cause" in md
    assert "Gateway restart" in md


def test_format_markdown_labor_cost():
    r = IncidentReport(
        peak_severity="STORM",
        void_sessions=10,
        estimated_cost_usd=1.40,
    )
    md = r.format_markdown()
    assert "Storm response: $0 (deterministic)" in md


def test_format_markdown_no_responses():
    r = IncidentReport(peak_severity="WARNING")
    md = r.format_markdown()
    assert "No automatic responses recorded" in md


# ─── Summary and Board Memory ─────────────────────────────────────


def test_format_summary():
    r = IncidentReport(
        incident_id="INC-20260331-142300",
        peak_severity="STORM",
        duration_seconds=480,
        estimated_cost_usd=1.40,
        indicators=["session_burst", "void_sessions"],
    )
    summary = r.format_summary()
    assert "INC-20260331-142300" in summary
    assert "STORM" in summary
    assert "$1.40" in summary
    assert "2 indicators" in summary


def test_format_board_memory():
    r = IncidentReport(
        incident_id="INC-20260331-142300",
        peak_severity="STORM",
        duration_seconds=480,
        estimated_cost_usd=1.40,
        indicators=["session_burst", "void_sessions"],
        void_sessions=8,
        total_sessions=10,
    )
    bm = r.format_board_memory()
    assert "[storm-incident]" in bm
    assert "STORM" in bm
    assert "$1.40" in bm
    assert "8/10" in bm


# ─── build_incident_report ─────────────────────────────────────────


def test_build_report_basic():
    now = time.time()
    report = build_incident_report(
        peak_severity="WARNING",
        started_at=now - 300,
        ended_at=now,
        indicators=["session_burst: 12/min"],
        responses=[ResponseEntry(timestamp=now - 250, action="force economic")],
        budget_mode_before="standard",
        budget_mode_after="economic",
        void_sessions=5,
        total_sessions=10,
    )
    assert report.peak_severity == "WARNING"
    assert report.duration_seconds == 300.0
    assert report.void_session_pct == 50.0
    assert report.estimated_cost_usd == 5 * 0.14  # 5 void × $0.14


def test_build_report_custom_cost():
    now = time.time()
    report = build_incident_report(
        peak_severity="STORM",
        started_at=now - 600,
        ended_at=now,
        indicators=["fast_climb", "session_burst"],
        responses=[],
        void_sessions=10,
        total_sessions=12,
        estimated_cost_per_void_session=0.20,
    )
    assert report.estimated_cost_usd == 10 * 0.20


def test_build_report_zero_sessions():
    now = time.time()
    report = build_incident_report(
        peak_severity="WARNING",
        started_at=now - 60,
        ended_at=now,
        indicators=["gateway_duplication"],
        responses=[],
        void_sessions=0,
        total_sessions=0,
    )
    assert report.void_session_pct == 0.0
    assert report.estimated_cost_usd == 0.0


def test_build_report_includes_prevention():
    now = time.time()
    report = build_incident_report(
        peak_severity="STORM",
        started_at=now - 600,
        ended_at=now,
        indicators=["session_burst: 15/min", "void_sessions: 80%"],
        responses=[],
    )
    assert len(report.prevention_recommendations) > 0


def test_build_report_with_root_cause():
    now = time.time()
    report = build_incident_report(
        peak_severity="STORM",
        started_at=now - 300,
        ended_at=now,
        indicators=["session_burst"],
        responses=[],
        root_cause="Gateway restart fired all heartbeats simultaneously.",
    )
    assert report.root_cause == "Gateway restart fired all heartbeats simultaneously."


def test_build_report_with_diagnostics_count():
    now = time.time()
    report = build_incident_report(
        peak_severity="STORM",
        started_at=now - 300,
        ended_at=now,
        indicators=["session_burst"],
        responses=[],
        diagnostics_count=5,
    )
    assert report.diagnostics_count == 5


# ─── Prevention Recommendations ───────────────────────────────────


def test_prevention_session_burst():
    recs = _generate_prevention_recommendations(
        indicators=["session_burst: 15/min"],
        peak_severity="WARNING",
        void_sessions=0,
        total_sessions=10,
    )
    assert any("heartbeat" in r.lower() for r in recs)


def test_prevention_void_sessions():
    recs = _generate_prevention_recommendations(
        indicators=["void_sessions: 80%"],
        peak_severity="WARNING",
        void_sessions=8,
        total_sessions=10,
    )
    assert any("void" in r.lower() for r in recs)


def test_prevention_gateway_duplication():
    recs = _generate_prevention_recommendations(
        indicators=["gateway_duplication"],
        peak_severity="WARNING",
        void_sessions=0,
        total_sessions=0,
    )
    assert any("gateway" in r.lower() for r in recs)


def test_prevention_critical_adds_systemic():
    recs = _generate_prevention_recommendations(
        indicators=["fast_climb"],
        peak_severity="CRITICAL",
        void_sessions=0,
        total_sessions=0,
    )
    assert any("systemic" in r.lower() for r in recs)


def test_prevention_high_void_pct():
    recs = _generate_prevention_recommendations(
        indicators=[],
        peak_severity="WARNING",
        void_sessions=8,
        total_sessions=10,
    )
    assert any("void session rate" in r.lower() for r in recs)


def test_prevention_no_duplicates():
    recs = _generate_prevention_recommendations(
        indicators=["session_burst", "session_burst: 12/min"],
        peak_severity="WARNING",
        void_sessions=0,
        total_sessions=0,
    )
    # Should not have duplicate recommendations
    assert len(recs) == len(set(recs))


def test_prevention_unknown_indicator():
    recs = _generate_prevention_recommendations(
        indicators=["unknown_indicator"],
        peak_severity="WARNING",
        void_sessions=0,
        total_sessions=0,
    )
    # Should not crash, may or may not have recommendations
    assert isinstance(recs, list)


# ─── StormEvent Tracker ───────────────────────────────────────────


def test_storm_event_creation():
    e = StormEvent(budget_mode_at_start="standard")
    assert e.started_at > 0
    assert not e.closed
    assert e.budget_mode_at_start == "standard"


def test_storm_event_record_severity():
    e = StormEvent()
    e.record_severity("WARNING")
    assert e.peak_severity == "WARNING"
    e.record_severity("STORM")
    assert e.peak_severity == "STORM"
    e.record_severity("WARNING")  # Should not downgrade
    assert e.peak_severity == "STORM"


def test_storm_event_record_indicator():
    e = StormEvent()
    e.record_indicator("session_burst")
    e.record_indicator("void_sessions")
    e.record_indicator("session_burst")  # Duplicate — should not add again
    assert len(e.indicators_seen) == 2


def test_storm_event_record_response():
    e = StormEvent()
    e.record_response("force economic mode", "budget pressure")
    e.record_response("alert PO", "via ntfy")
    assert len(e.responses) == 2
    assert e.responses[0].action == "force economic mode"


def test_storm_event_close():
    e = StormEvent()
    e.close()
    assert e.closed
    assert e.ended_at > 0


def test_storm_event_to_report():
    e = StormEvent(budget_mode_at_start="standard")
    e.record_severity("STORM")
    e.record_indicator("session_burst: 15/min")
    e.record_response("force economic mode")
    e.record_response("force survival mode")
    e.close()

    report = e.to_report(
        budget_mode_after="survival",
        void_sessions=8,
        total_sessions=10,
    )
    assert report.peak_severity == "STORM"
    assert report.budget_mode_before == "standard"
    assert report.budget_mode_after == "survival"
    assert report.void_sessions == 8
    assert len(report.responses) == 2
    assert len(report.indicators) == 1


def test_storm_event_to_report_open():
    """Can generate report even if storm hasn't ended yet."""
    e = StormEvent()
    e.record_severity("WARNING")
    e.record_indicator("fast_climb")
    # Don't close — still in progress
    report = e.to_report()
    assert report.peak_severity == "WARNING"
    assert report.ended_at > 0  # Uses time.time() as fallback


def test_storm_event_full_lifecycle():
    """Full lifecycle: create → escalate → respond → close → report."""
    e = StormEvent(budget_mode_at_start="standard")

    # Escalation
    e.record_severity("WATCH")
    e.record_indicator("session_burst: 12/min")

    e.record_severity("WARNING")
    e.record_indicator("void_sessions: 80%")
    e.record_response("force economic mode")

    e.record_severity("STORM")
    e.record_response("force survival mode")
    e.record_response("disable heartbeats")
    e.record_response("alert PO", "ntfy URGENT")

    # De-escalation
    e.close()

    report = e.to_report(
        budget_mode_after="survival",
        void_sessions=8,
        total_sessions=10,
        root_cause="Gateway restart fired all heartbeats simultaneously.",
        diagnostics_count=3,
    )

    assert report.peak_severity == "STORM"
    assert report.duration_seconds > 0
    assert len(report.indicators) == 2
    assert len(report.responses) == 4
    assert report.root_cause != ""
    assert report.diagnostics_count == 3

    # Verify all formats work
    md = report.format_markdown()
    assert "STORM" in md
    assert "Gateway restart" in md

    summary = report.format_summary()
    assert "STORM" in summary

    bm = report.format_board_memory()
    assert "[storm-incident]" in bm

    d = report.to_dict()
    assert d["peak_severity"] == "STORM"