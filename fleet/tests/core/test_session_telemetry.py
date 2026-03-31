"""Tests for session telemetry adapter (W8)."""

from fleet.core.session_telemetry import (
    SessionSnapshot,
    ingest,
    to_claude_health,
    to_cost_delta,
    to_labor_fields,
    to_storm_indicators,
)


# ─── Fixtures ──────────────────────────────────────────────────────


def _full_session_json() -> dict:
    """Complete session JSON matching Claude Code schema."""
    return {
        "model": {
            "id": "claude-opus-4-6",
            "display_name": "Opus",
        },
        "context_window": {
            "context_window_size": 1_000_000,
            "used_percentage": 42,
            "remaining_percentage": 58,
            "total_input_tokens": 150_000,
            "total_output_tokens": 45_000,
            "current_usage": {
                "input_tokens": 8500,
                "output_tokens": 1200,
                "cache_creation_input_tokens": 5000,
                "cache_read_input_tokens": 2000,
            },
        },
        "cost": {
            "total_cost_usd": 0.15,
            "total_duration_ms": 180_000,
            "total_api_duration_ms": 2300,
            "total_lines_added": 256,
            "total_lines_removed": 31,
        },
        "rate_limits": {
            "five_hour": {"used_percentage": 23.5},
            "seven_day": {"used_percentage": 41.2},
        },
        "workspace": {
            "current_dir": "/home/user/project",
        },
        "exceeds_200k_tokens": False,
    }


def _minimal_session_json() -> dict:
    """Session JSON with missing/null fields."""
    return {
        "model": {"display_name": "Sonnet"},
        "context_window": {"used_percentage": 10},
        "cost": {},
    }


# ─── Ingest ────────────────────────────────────────────────────────


def test_ingest_full():
    snap = ingest(_full_session_json())
    assert snap.model_id == "claude-opus-4-6"
    assert snap.model_display_name == "Opus"
    assert snap.context_window_size == 1_000_000
    assert snap.context_used_pct == 42.0
    assert snap.context_remaining_pct == 58.0
    assert snap.input_tokens == 8500
    assert snap.output_tokens == 1200
    assert snap.cache_creation_tokens == 5000
    assert snap.cache_read_tokens == 2000
    assert snap.total_input_tokens == 150_000
    assert snap.total_output_tokens == 45_000
    assert snap.total_cost_usd == 0.15
    assert snap.total_duration_ms == 180_000
    assert snap.total_api_duration_ms == 2300
    assert snap.total_lines_added == 256
    assert snap.total_lines_removed == 31
    assert snap.five_hour_used_pct == 23.5
    assert snap.seven_day_used_pct == 41.2
    assert snap.current_dir == "/home/user/project"
    assert snap.exceeds_200k is False


def test_ingest_minimal():
    snap = ingest(_minimal_session_json())
    assert snap.model_display_name == "Sonnet"
    assert snap.model_id == ""
    assert snap.context_used_pct == 10.0
    assert snap.context_window_size == 0
    assert snap.total_cost_usd == 0.0
    assert snap.five_hour_used_pct is None
    assert snap.seven_day_used_pct is None


def test_ingest_empty():
    snap = ingest({})
    assert snap.model_id == ""
    assert snap.context_used_pct == 0.0
    assert snap.total_cost_usd == 0.0
    assert snap.five_hour_used_pct is None


def test_ingest_null_fields():
    data = {
        "model": None,
        "context_window": None,
        "cost": None,
        "rate_limits": None,
    }
    snap = ingest(data)
    assert snap.model_id == ""
    assert snap.context_used_pct == 0.0


# ─── Properties ────────────────────────────────────────────────────


def test_context_label_1m():
    snap = SessionSnapshot(context_window_size=1_000_000)
    assert snap.context_label == "1M"


def test_context_label_200k():
    snap = SessionSnapshot(context_window_size=200_000)
    assert snap.context_label == "200K"


def test_context_label_custom():
    snap = SessionSnapshot(context_window_size=50_000)
    assert snap.context_label == "50K"


def test_context_label_unknown():
    snap = SessionSnapshot(context_window_size=0)
    assert snap.context_label == "unknown"


def test_context_pressure_critical():
    snap = SessionSnapshot(context_used_pct=95)
    assert snap.context_pressure == "critical"


def test_context_pressure_high():
    snap = SessionSnapshot(context_used_pct=75)
    assert snap.context_pressure == "high"


def test_context_pressure_moderate():
    snap = SessionSnapshot(context_used_pct=55)
    assert snap.context_pressure == "moderate"


def test_context_pressure_low():
    snap = SessionSnapshot(context_used_pct=30)
    assert snap.context_pressure == "low"


def test_cache_hit_rate():
    snap = SessionSnapshot(
        input_tokens=5000,
        cache_creation_tokens=3000,
        cache_read_tokens=2000,
    )
    # 2000 / (5000 + 3000 + 2000) = 0.2
    assert abs(snap.cache_hit_rate - 0.2) < 0.001


def test_cache_hit_rate_zero():
    snap = SessionSnapshot()
    assert snap.cache_hit_rate == 0.0


def test_duration_seconds():
    snap = SessionSnapshot(total_duration_ms=180_000)
    assert snap.duration_seconds == 180


def test_api_latency():
    snap = SessionSnapshot(total_api_duration_ms=2300)
    assert snap.api_latency_ms == 2300.0


# ─── to_labor_fields ───────────────────────────────────────────────


def test_labor_fields_from_session():
    snap = ingest(_full_session_json())
    fields = to_labor_fields(snap)
    assert fields["model"] == "claude-opus-4-6"
    assert fields["model_version"] == "claude-opus-4-6"
    assert fields["duration_seconds"] == 180
    assert fields["estimated_tokens"] == 195_000  # 150K + 45K
    assert fields["estimated_cost_usd"] == 0.15
    assert fields["lines_added"] == 256
    assert fields["lines_removed"] == 31
    assert fields["cache_read_tokens"] == 2000


def test_labor_fields_session_type():
    snap = SessionSnapshot(exceeds_200k=True)
    fields = to_labor_fields(snap)
    assert fields["session_type"] == "compact"

    snap2 = SessionSnapshot(exceeds_200k=False)
    fields2 = to_labor_fields(snap2)
    assert fields2["session_type"] == "fresh"


# ─── to_claude_health ──────────────────────────────────────────────


def test_claude_health_from_session():
    snap = ingest(_full_session_json())
    fields = to_claude_health(snap)
    assert fields["quota_used_pct"] == 23.5
    assert fields["weekly_quota_used_pct"] == 41.2
    assert fields["latency_ms"] == 2300.0
    assert fields["model_available"] == "Opus"
    assert fields["context_window_size"] == 1_000_000


def test_claude_health_no_rate_limits():
    snap = ingest(_minimal_session_json())
    fields = to_claude_health(snap)
    assert "quota_used_pct" not in fields
    assert "weekly_quota_used_pct" not in fields
    assert fields["context_window_size"] == 0


# ─── to_storm_indicators ──────────────────────────────────────────


def test_storm_no_indicators_at_low_usage():
    snap = SessionSnapshot(context_used_pct=30, five_hour_used_pct=20.0)
    indicators = to_storm_indicators(snap)
    assert indicators == []


def test_storm_context_pressure():
    snap = SessionSnapshot(context_used_pct=85)
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "context_pressure" in names
    assert any("85%" in v for _, v in indicators)


def test_storm_quota_pressure_5h():
    snap = SessionSnapshot(five_hour_used_pct=90.0)
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "quota_pressure_5h" in names


def test_storm_quota_pressure_7d():
    snap = SessionSnapshot(seven_day_used_pct=85.0)
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "quota_pressure_7d" in names


def test_storm_cache_miss():
    snap = SessionSnapshot(
        total_input_tokens=50_000,
        input_tokens=45_000,
        cache_read_tokens=100,
        cache_creation_tokens=4900,
    )
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "cache_miss" in names


def test_storm_no_cache_miss_when_tokens_low():
    snap = SessionSnapshot(
        total_input_tokens=500,
        input_tokens=500,
        cache_read_tokens=0,
    )
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "cache_miss" not in names


def test_storm_combined_pressure():
    snap = SessionSnapshot(
        context_used_pct=92,
        five_hour_used_pct=85.0,
        seven_day_used_pct=90.0,
    )
    indicators = to_storm_indicators(snap)
    names = [i[0] for i in indicators]
    assert "context_pressure" in names
    assert "quota_pressure_5h" in names
    assert "quota_pressure_7d" in names
    assert len(indicators) == 3


# ─── to_cost_delta ─────────────────────────────────────────────────


def test_cost_delta_first_call():
    snap = SessionSnapshot(total_cost_usd=0.15)
    delta = to_cost_delta(snap)
    assert delta == 0.15


def test_cost_delta_incremental():
    snap = SessionSnapshot(total_cost_usd=0.25)
    delta = to_cost_delta(snap, previous_cost=0.15)
    assert abs(delta - 0.10) < 0.001


def test_cost_delta_no_negative():
    snap = SessionSnapshot(total_cost_usd=0.10)
    delta = to_cost_delta(snap, previous_cost=0.15)
    assert delta == 0.0
