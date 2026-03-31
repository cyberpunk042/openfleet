"""Tests for heartbeat labor stamps (M-LA08)."""

import time

from fleet.core.heartbeat_stamp import (
    HeartbeatCostEntry,
    HeartbeatCostTracker,
    create_heartbeat_stamp,
)
from fleet.core.labor_stamp import LaborStamp


# ─── create_heartbeat_stamp ──────────────────────────────────────


def test_heartbeat_stamp_basic():
    s = create_heartbeat_stamp(agent_name="dev", backend="localai", model="hermes-3b")
    assert s.agent_name == "dev"
    assert s.agent_role == "heartbeat"
    assert s.backend == "localai"
    assert s.model == "hermes-3b"
    assert s.effort == "low"
    assert "heartbeat" in s.skills_used


def test_heartbeat_stamp_cost():
    s = create_heartbeat_stamp(
        agent_name="dev", estimated_cost_usd=0.15, duration_seconds=5,
    )
    assert s.estimated_cost_usd == 0.15
    assert s.duration_seconds == 5


def test_heartbeat_stamp_budget_mode():
    s = create_heartbeat_stamp(agent_name="dev", budget_mode="survival")
    assert s.budget_mode == "survival"


def test_heartbeat_stamp_is_labor_stamp():
    s = create_heartbeat_stamp(agent_name="dev")
    assert isinstance(s, LaborStamp)
    assert s.timestamp != ""


# ─── HeartbeatCostEntry ──────────────────────────────────────────


def test_entry_auto_timestamp():
    e = HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    )
    assert e.timestamp > 0


# ─── HeartbeatCostTracker: Recording ─────────────────────────────


def test_record_entry():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    assert t.total_entries == 1


def test_record_from_stamp():
    t = HeartbeatCostTracker()
    stamp = create_heartbeat_stamp(
        agent_name="dev", estimated_cost_usd=0.05, duration_seconds=3,
        backend="localai", model="hermes-3b",
    )
    t.record_from_stamp(stamp)
    assert t.total_entries == 1
    assert abs(t.total_cost_usd - 0.05) < 0.001


def test_max_entries_cap():
    t = HeartbeatCostTracker(max_entries=5)
    for _ in range(10):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.01, duration_seconds=1,
            backend="localai", model="hermes-3b", void=False,
        ))
    assert t.total_entries == 5


# ─── Cost Metrics ───────────────────────────────────────────────


def test_total_cost():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.05, duration_seconds=3,
        backend="claude-code", model="sonnet", void=False,
    ))
    assert abs(t.total_cost_usd - 0.15) < 0.001


def test_avg_cost():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.20, duration_seconds=3,
        backend="claude-code", model="sonnet", void=False,
    ))
    assert abs(t.avg_cost_per_heartbeat - 0.15) < 0.001


def test_avg_cost_empty():
    t = HeartbeatCostTracker()
    assert t.avg_cost_per_heartbeat == 0.0


# ─── Void Rate ──────────────────────────────────────────────────


def test_void_rate_zero():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    assert t.void_rate == 0.0


def test_void_rate_all_void():
    t = HeartbeatCostTracker()
    for _ in range(3):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.10, duration_seconds=5,
            backend="claude-code", model="sonnet", void=True,
        ))
    assert t.void_rate == 1.0


def test_void_rate_mixed():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=True,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    assert t.void_rate == 0.5


def test_void_rate_empty():
    t = HeartbeatCostTracker()
    assert t.void_rate == 0.0


# ─── Last Hour Metrics ──────────────────────────────────────────


def test_entries_last_hour():
    t = HeartbeatCostTracker()
    # Recent entry
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    # Old entry
    old = HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.20, duration_seconds=3,
        backend="claude-code", model="sonnet", void=False,
    )
    old.timestamp = time.time() - 7200  # 2 hours ago
    t.record(old)

    assert len(t.entries_last_hour()) == 1
    assert abs(t.cost_last_hour() - 0.10) < 0.001
    assert t.rate_last_hour() == 1


# ─── Anomaly Detection ──────────────────────────────────────────


def test_no_anomalies():
    t = HeartbeatCostTracker(cost_threshold_usd=0.10, rate_threshold_per_hour=30)
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.01, duration_seconds=1,
        backend="localai", model="hermes-3b", void=False,
    ))
    assert not t.is_cost_anomaly()
    assert not t.is_rate_anomaly()
    assert len(t.check_anomalies()) == 0


def test_cost_anomaly():
    t = HeartbeatCostTracker(cost_threshold_usd=0.05)
    for _ in range(5):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.15, duration_seconds=5,
            backend="claude-code", model="opus", void=False,
        ))
    assert t.is_cost_anomaly()
    anomalies = t.check_anomalies()
    assert any("cost anomaly" in a for a in anomalies)


def test_rate_anomaly():
    t = HeartbeatCostTracker(rate_threshold_per_hour=5)
    for _ in range(10):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.01, duration_seconds=1,
            backend="localai", model="hermes-3b", void=False,
        ))
    assert t.is_rate_anomaly()
    anomalies = t.check_anomalies()
    assert any("rate anomaly" in a for a in anomalies)


def test_void_rate_anomaly():
    t = HeartbeatCostTracker()
    for _ in range(6):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.01, duration_seconds=1,
            backend="localai", model="hermes-3b", void=True,
        ))
    anomalies = t.check_anomalies()
    assert any("void rate" in a for a in anomalies)


def test_void_rate_anomaly_needs_minimum():
    """Void rate anomaly requires at least 5 entries."""
    t = HeartbeatCostTracker()
    for _ in range(3):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.01, duration_seconds=1,
            backend="localai", model="hermes-3b", void=True,
        ))
    anomalies = t.check_anomalies()
    assert not any("void rate" in a for a in anomalies)


# ─── Per-Agent Breakdown ────────────────────────────────────────


def test_cost_by_agent():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.05, duration_seconds=3,
        backend="claude-code", model="sonnet", void=False,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.02, duration_seconds=2,
        backend="localai", model="hermes-3b", void=False,
    ))
    costs = t.cost_by_agent()
    assert costs["dev"] == 0.15
    assert costs["qa"] == 0.02


def test_rate_by_agent():
    t = HeartbeatCostTracker()
    for _ in range(3):
        t.record(HeartbeatCostEntry(
            agent_name="dev", cost_usd=0.01, duration_seconds=1,
            backend="localai", model="hermes-3b", void=False,
        ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.01, duration_seconds=1,
        backend="localai", model="hermes-3b", void=False,
    ))
    rates = t.rate_by_agent()
    assert rates["dev"] == 3
    assert rates["qa"] == 1


def test_cost_by_backend():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.10, duration_seconds=5,
        backend="claude-code", model="sonnet", void=False,
    ))
    t.record(HeartbeatCostEntry(
        agent_name="qa", cost_usd=0.00, duration_seconds=1,
        backend="localai", model="hermes-3b", void=False,
    ))
    costs = t.cost_by_backend()
    assert costs["claude-code"] == 0.10
    assert costs["localai"] == 0.0


# ─── Summary ────────────────────────────────────────────────────


def test_summary():
    t = HeartbeatCostTracker()
    t.record(HeartbeatCostEntry(
        agent_name="dev", cost_usd=0.05, duration_seconds=3,
        backend="claude-code", model="sonnet", void=False,
    ))
    s = t.summary()
    assert s["total_heartbeats"] == 1
    assert s["total_cost_usd"] == 0.05
    assert isinstance(s["anomalies"], list)
    assert "cost_by_agent" in s
    assert "cost_by_backend" in s


def test_summary_empty():
    t = HeartbeatCostTracker()
    s = t.summary()
    assert s["total_heartbeats"] == 0
    assert s["total_cost_usd"] == 0.0