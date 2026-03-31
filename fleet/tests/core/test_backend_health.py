"""Tests for backend health dashboard (M-BR07)."""

import time

from fleet.core.backend_health import (
    BackendHealthDashboard,
    BackendHealthState,
    BackendStatus,
    ClaudeHealth,
    LocalAIHealth,
    OpenRouterHealth,
)


# ─── BackendHealthState ────────────────────────────────────────


def test_state_defaults():
    s = BackendHealthState(name="test")
    assert s.status == BackendStatus.UNKNOWN
    assert not s.is_healthy


def test_state_healthy():
    s = BackendHealthState(name="test", status=BackendStatus.UP)
    assert s.is_healthy


def test_state_stale():
    s = BackendHealthState(name="test", last_check=time.time() - 600)
    assert s.stale


def test_state_not_stale():
    s = BackendHealthState(name="test", last_check=time.time())
    assert not s.stale


def test_state_stale_never_checked():
    s = BackendHealthState(name="test")
    assert s.stale


def test_state_to_dict():
    s = BackendHealthState(
        name="test", status=BackendStatus.UP,
        last_check=time.time(), latency_ms=42.5,
    )
    d = s.to_dict()
    assert d["name"] == "test"
    assert d["status"] == "up"
    assert d["latency_ms"] == 42.5


# ─── LocalAIHealth ─────────────────────────────────────────────


def test_localai_defaults():
    h = LocalAIHealth()
    assert h.name == "localai"
    assert h.loaded_model == ""


def test_localai_gpu_utilization():
    h = LocalAIHealth(gpu_memory_used_mb=5000, gpu_memory_total_mb=8000)
    assert abs(h.gpu_utilization_pct - 62.5) < 0.1


def test_localai_gpu_utilization_zero():
    h = LocalAIHealth()
    assert h.gpu_utilization_pct == 0.0


def test_localai_to_dict():
    h = LocalAIHealth(
        status=BackendStatus.UP,
        loaded_model="hermes-3b",
        available_models=["hermes-3b", "codellama"],
        gpu_memory_used_mb=2000, gpu_memory_total_mb=8000,
    )
    d = h.to_dict()
    assert d["loaded_model"] == "hermes-3b"
    assert len(d["available_models"]) == 2
    assert d["gpu_utilization_pct"] == 25.0


# ─── ClaudeHealth ──────────────────────────────────────────────


def test_claude_defaults():
    h = ClaudeHealth()
    assert h.name == "claude-code"
    assert not h.quota_warning
    assert not h.quota_critical


def test_claude_quota_warning():
    h = ClaudeHealth(quota_used_pct=85.0)
    assert h.quota_warning
    assert not h.quota_critical


def test_claude_quota_critical():
    h = ClaudeHealth(quota_used_pct=96.0)
    assert h.quota_warning
    assert h.quota_critical


def test_claude_to_dict():
    h = ClaudeHealth(
        status=BackendStatus.UP,
        quota_used_pct=50.0, quota_remaining_usd=25.0,
        model_available="opus-4-6",
    )
    d = h.to_dict()
    assert d["quota_used_pct"] == 50.0
    assert d["quota_remaining_usd"] == 25.0
    assert not d["quota_warning"]
    assert d["model_available"] == "opus-4-6"


# ─── OpenRouterHealth ──────────────────────────────────────────


def test_openrouter_defaults():
    h = OpenRouterHealth()
    assert h.name == "openrouter-free"
    assert not h.free_tier_active


def test_openrouter_to_dict():
    h = OpenRouterHealth(
        status=BackendStatus.UP,
        free_tier_active=True,
        free_models_available=["qwen3-8b", "llama-3.3"],
    )
    d = h.to_dict()
    assert d["free_tier_active"] is True
    assert len(d["free_models_available"]) == 2


# ─── BackendHealthDashboard ───────────────────────────────────


def test_dashboard_empty():
    d = BackendHealthDashboard()
    assert not d.all_healthy
    assert not d.any_healthy
    assert d.availability_score == 0.0


def test_dashboard_update():
    d = BackendHealthDashboard()
    d.update(BackendHealthState(name="test", status=BackendStatus.UP))
    assert d.get("test") is not None
    assert d.get("test").is_healthy


def test_dashboard_all_healthy():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(status=BackendStatus.UP))
    d.update(ClaudeHealth(status=BackendStatus.UP))
    assert d.all_healthy


def test_dashboard_not_all_healthy():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(status=BackendStatus.UP))
    d.update(ClaudeHealth(status=BackendStatus.DOWN))
    assert not d.all_healthy
    assert d.any_healthy


def test_dashboard_healthy_backends():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(status=BackendStatus.UP))
    d.update(ClaudeHealth(status=BackendStatus.DOWN))
    d.update(OpenRouterHealth(status=BackendStatus.UP))
    assert set(d.healthy_backends()) == {"localai", "openrouter-free"}
    assert d.unhealthy_backends() == ["claude-code"]


def test_dashboard_stale_backends():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(
        status=BackendStatus.UP, last_check=time.time() - 600,
    ))
    d.update(ClaudeHealth(
        status=BackendStatus.UP, last_check=time.time(),
    ))
    assert d.stale_backends() == ["localai"]


def test_dashboard_availability_score():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(status=BackendStatus.UP))
    d.update(ClaudeHealth(status=BackendStatus.UP))
    d.update(OpenRouterHealth(status=BackendStatus.DOWN))
    assert abs(d.availability_score - 2 / 3) < 0.01


# ─── Routing Options ──────────────────────────────────────────


def test_routing_options():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(status=BackendStatus.UP))
    d.update(ClaudeHealth(status=BackendStatus.DOWN))
    opts = d.routing_options()
    assert opts["localai"] is True
    assert opts["claude-code"] is False
    assert opts["direct"] is True  # Always available


def test_routing_options_empty():
    d = BackendHealthDashboard()
    opts = d.routing_options()
    assert opts["localai"] is False
    assert opts["claude-code"] is False
    assert opts["direct"] is True


# ─── Summary & Report ─────────────────────────────────────────


def test_summary():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(
        status=BackendStatus.UP, loaded_model="hermes-3b",
        last_check=time.time(), latency_ms=15.0,
    ))
    d.update(ClaudeHealth(
        status=BackendStatus.UP, quota_used_pct=40.0,
        last_check=time.time(), latency_ms=200.0,
    ))
    s = d.summary()
    assert s["total_backends"] == 2
    assert s["healthy"] == 2
    assert s["availability_score"] == 1.0
    assert "localai" in s["backends"]
    assert "claude-code" in s["backends"]


def test_format_report():
    d = BackendHealthDashboard()
    d.update(LocalAIHealth(
        status=BackendStatus.UP, loaded_model="hermes-3b",
        last_check=time.time(), latency_ms=15.0,
    ))
    d.update(ClaudeHealth(
        status=BackendStatus.UP, quota_used_pct=85.0,
        last_check=time.time(), latency_ms=200.0,
    ))
    d.update(OpenRouterHealth(
        status=BackendStatus.DOWN, error="timeout",
        last_check=time.time(),
    ))
    report = d.format_report()
    assert "Backend Health Dashboard" in report
    assert "hermes-3b" in report
    assert "quota: 85%" in report
    assert "DOWN" in report
    assert "Routing Options" in report


def test_format_report_empty():
    d = BackendHealthDashboard()
    report = d.format_report()
    assert "Backend Health Dashboard" in report
    assert "0/0 healthy" in report