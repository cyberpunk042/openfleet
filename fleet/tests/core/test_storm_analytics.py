"""Tests for storm analytics (M-SP09)."""

import time

from fleet.core.incident_report import IncidentReport, ResponseEntry
from fleet.core.storm_analytics import (
    StormAnalytics,
    StormRecord,
)


# ─── Helpers ──────────────────────────────────────────────────────


def _record(
    severity: str = "WARNING",
    duration: float = 300.0,
    cost: float = 0.50,
    indicators: list[str] = None,
    void_sessions: int = 3,
    total_sessions: int = 10,
    response_count: int = 2,
    time_to_response: float = 5.0,
    incident_id: str = "INC-001",
) -> StormRecord:
    return StormRecord(
        incident_id=incident_id,
        peak_severity=severity,
        duration_seconds=duration,
        estimated_cost_usd=cost,
        indicators=indicators or ["session_burst"],
        void_sessions=void_sessions,
        total_sessions=total_sessions,
        response_count=response_count,
        time_to_response_seconds=time_to_response,
    )


# ─── StormRecord ────────────────────────────────────────────────


def test_record_to_dict():
    r = _record()
    d = r.to_dict()
    assert d["peak_severity"] == "WARNING"
    assert d["estimated_cost_usd"] == 0.50


def test_record_from_report():
    now = time.time()
    report = IncidentReport(
        incident_id="INC-TEST",
        peak_severity="STORM",
        started_at=now - 480,
        ended_at=now,
        duration_seconds=480,
        indicators=["session_burst: 15/min", "void_sessions: 80%"],
        estimated_cost_usd=1.40,
        void_sessions=8,
        total_sessions=10,
        responses=[
            ResponseEntry(timestamp=now - 470, action="force economic"),
            ResponseEntry(timestamp=now - 460, action="alert PO"),
        ],
    )
    record = StormRecord.from_report(report)
    assert record.incident_id == "INC-TEST"
    assert record.peak_severity == "STORM"
    assert record.duration_seconds == 480
    assert len(record.indicators) == 2
    assert "session_burst" in record.indicators
    assert record.response_count == 2
    assert record.time_to_response_seconds > 0


# ─── Recording ──────────────────────────────────────────────────


def test_record_storm():
    a = StormAnalytics()
    a.record(_record())
    assert a.total_storms == 1


def test_record_from_report():
    a = StormAnalytics()
    now = time.time()
    report = IncidentReport(
        peak_severity="WARNING",
        started_at=now - 300,
        ended_at=now,
        duration_seconds=300,
        estimated_cost_usd=0.50,
    )
    a.record_from_report(report)
    assert a.total_storms == 1


def test_record_many():
    a = StormAnalytics()
    a.record_many([_record(incident_id=f"INC-{i}") for i in range(5)])
    assert a.total_storms == 5


def test_max_records_cap():
    a = StormAnalytics(max_records=3)
    for i in range(5):
        a.record(_record(incident_id=f"INC-{i}"))
    assert a.total_storms == 3


# ─── Total Metrics ──────────────────────────────────────────────


def test_total_cost():
    a = StormAnalytics()
    a.record_many([_record(cost=0.50), _record(cost=1.00)])
    assert abs(a.total_cost_usd - 1.50) < 0.001


def test_total_void_sessions():
    a = StormAnalytics()
    a.record_many([_record(void_sessions=5), _record(void_sessions=3)])
    assert a.total_void_sessions == 8


# ─── Severity Distribution ──────────────────────────────────────


def test_severity_distribution():
    a = StormAnalytics()
    a.record_many([
        _record(severity="WARNING", incident_id="i1"),
        _record(severity="STORM", incident_id="i2"),
        _record(severity="WARNING", incident_id="i3"),
        _record(severity="CRITICAL", incident_id="i4"),
    ])
    dist = a.severity_distribution()
    assert dist["WARNING"] == 2
    assert dist["STORM"] == 1
    assert dist["CRITICAL"] == 1


# ─── Indicator Frequency ────────────────────────────────────────


def test_indicator_frequency():
    a = StormAnalytics()
    a.record_many([
        _record(indicators=["session_burst", "void_sessions"], incident_id="i1"),
        _record(indicators=["session_burst", "error_storm"], incident_id="i2"),
        _record(indicators=["session_burst"], incident_id="i3"),
    ])
    freq = a.indicator_frequency(top_n=3)
    assert freq[0] == ("session_burst", 3)
    assert len(freq) == 3


def test_indicator_frequency_empty():
    a = StormAnalytics()
    assert a.indicator_frequency() == []


# ─── Duration Stats ─────────────────────────────────────────────


def test_avg_duration():
    a = StormAnalytics()
    a.record_many([
        _record(duration=300, incident_id="i1"),
        _record(duration=600, incident_id="i2"),
    ])
    assert a.avg_duration_seconds() == 450.0


def test_max_min_duration():
    a = StormAnalytics()
    a.record_many([
        _record(duration=100, incident_id="i1"),
        _record(duration=500, incident_id="i2"),
        _record(duration=300, incident_id="i3"),
    ])
    assert a.max_duration_seconds() == 500.0
    assert a.min_duration_seconds() == 100.0


def test_duration_empty():
    a = StormAnalytics()
    assert a.avg_duration_seconds() == 0.0
    assert a.max_duration_seconds() == 0.0


# ─── Response Time ──────────────────────────────────────────────


def test_avg_time_to_response():
    a = StormAnalytics()
    a.record_many([
        _record(time_to_response=5.0, incident_id="i1"),
        _record(time_to_response=15.0, incident_id="i2"),
    ])
    assert a.avg_time_to_response() == 10.0


def test_avg_time_to_response_ignores_zero():
    a = StormAnalytics()
    a.record_many([
        _record(time_to_response=10.0, incident_id="i1"),
        _record(time_to_response=0.0, incident_id="i2"),  # No response recorded
    ])
    assert a.avg_time_to_response() == 10.0


def test_avg_time_to_response_empty():
    a = StormAnalytics()
    assert a.avg_time_to_response() == 0.0


# ─── Cost Analysis ──────────────────────────────────────────────


def test_avg_cost_per_storm():
    a = StormAnalytics()
    a.record_many([_record(cost=0.50), _record(cost=1.50)])
    assert a.avg_cost_per_storm() == 1.0


def test_cost_by_severity():
    a = StormAnalytics()
    a.record_many([
        _record(severity="WARNING", cost=0.50, incident_id="i1"),
        _record(severity="STORM", cost=1.50, incident_id="i2"),
        _record(severity="WARNING", cost=0.30, incident_id="i3"),
    ])
    costs = a.cost_by_severity()
    assert costs["STORM"] == 1.50
    assert costs["WARNING"] == 0.80


# ─── Prevention Insights ────────────────────────────────────────


def test_recurring_indicators():
    a = StormAnalytics()
    a.record_many([
        _record(indicators=["session_burst", "void_sessions"], incident_id="i1"),
        _record(indicators=["session_burst", "error_storm"], incident_id="i2"),
        _record(indicators=["gateway_duplication"], incident_id="i3"),
    ])
    recurring = a.recurring_indicators(min_count=2)
    assert len(recurring) == 1
    assert recurring[0] == ("session_burst", 2)


def test_void_session_rate():
    a = StormAnalytics()
    a.record_many([
        _record(void_sessions=5, total_sessions=10, incident_id="i1"),
        _record(void_sessions=3, total_sessions=10, incident_id="i2"),
    ])
    assert a.void_session_rate() == 0.4  # 8/20


def test_void_session_rate_empty():
    a = StormAnalytics()
    assert a.void_session_rate() == 0.0


# ─── Summary ────────────────────────────────────────────────────


def test_summary_empty():
    a = StormAnalytics()
    s = a.summary()
    assert s["total_storms"] == 0
    assert s["total_cost_usd"] == 0.0


def test_summary_with_data():
    a = StormAnalytics()
    a.record_many([
        _record(severity="WARNING", cost=0.50, indicators=["session_burst"], incident_id="i1"),
        _record(severity="STORM", cost=1.50, indicators=["session_burst", "void_sessions"], incident_id="i2"),
    ])
    s = a.summary()
    assert s["total_storms"] == 2
    assert abs(s["total_cost_usd"] - 2.00) < 0.001
    assert len(s["severity_distribution"]) == 2
    assert len(s["top_indicators"]) >= 1


# ─── Report ─────────────────────────────────────────────────────


def test_format_report():
    a = StormAnalytics()
    a.record_many([
        _record(severity="WARNING", cost=0.50, incident_id="i1"),
        _record(severity="STORM", cost=1.50, incident_id="i2"),
    ])
    report = a.format_report()
    assert "Storm Analytics Report" in report
    assert "WARNING" in report
    assert "STORM" in report
    assert "$2.00" in report


def test_format_report_empty():
    a = StormAnalytics()
    report = a.format_report()
    assert "Storm Analytics Report" in report
    assert "$0.00" in report