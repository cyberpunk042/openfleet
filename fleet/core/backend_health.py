"""Backend health dashboard (M-BR07).

Real-time status of all fleet backends — up/down/degraded,
model currently loaded on LocalAI, OpenRouter availability,
and Claude quota status.

Design doc requirement:
> Real-time status of all backends (up/down/degraded).
> Model currently loaded on LocalAI.
> OpenRouter free tier availability.
> Claude quota status.
> Integrated into fleet-ops monitoring.

This module aggregates health state. The actual health checks
(HTTP probes, quota reads) are performed by the caller.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── Backend Status ────────────────────────────────────────────


class BackendStatus(Enum):
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    SWAPPING = "swapping"       # LocalAI: model swap in progress


@dataclass
class BackendHealthState:
    """Health state for a single backend."""

    name: str = ""
    status: BackendStatus = BackendStatus.UNKNOWN
    last_check: float = 0.0
    last_success: float = 0.0
    latency_ms: float = 0.0
    error: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == BackendStatus.UP

    @property
    def seconds_since_check(self) -> float:
        if not self.last_check:
            return float("inf")
        return time.time() - self.last_check

    @property
    def stale(self) -> bool:
        """Health data is stale if older than 5 minutes."""
        return self.seconds_since_check > 300

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check,
            "last_success": self.last_success,
            "latency_ms": round(self.latency_ms, 1),
            "stale": self.stale,
            "error": self.error,
            "metadata": self.metadata,
        }


# ─── LocalAI Health ────────────────────────────────────────────


@dataclass
class LocalAIHealth(BackendHealthState):
    """LocalAI-specific health state."""

    loaded_model: str = ""
    available_models: list[str] = field(default_factory=list)
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    swap_in_progress: bool = False

    def __post_init__(self) -> None:
        self.name = "localai"

    @property
    def gpu_utilization_pct(self) -> float:
        if not self.gpu_memory_total_mb:
            return 0.0
        return (self.gpu_memory_used_mb / self.gpu_memory_total_mb) * 100

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "loaded_model": self.loaded_model,
            "available_models": self.available_models,
            "gpu_memory_used_mb": round(self.gpu_memory_used_mb, 0),
            "gpu_memory_total_mb": round(self.gpu_memory_total_mb, 0),
            "gpu_utilization_pct": round(self.gpu_utilization_pct, 1),
            "swap_in_progress": self.swap_in_progress,
        })
        return d


# ─── Claude Health ─────────────────────────────────────────────


@dataclass
class ClaudeHealth(BackendHealthState):
    """Claude backend health state with quota tracking."""

    quota_used_pct: float = 0.0
    quota_remaining_usd: float = 0.0
    rate_limited: bool = False
    model_available: str = ""         # Which Claude model is accessible
    weekly_quota_used_pct: float = 0.0  # 7-day window (from session telemetry)
    context_window_size: int = 0      # 200000 or 1000000 (from session telemetry)

    def __post_init__(self) -> None:
        self.name = "claude-code"

    @property
    def quota_warning(self) -> bool:
        return self.quota_used_pct >= 80.0

    @property
    def quota_critical(self) -> bool:
        return self.quota_used_pct >= 95.0

    @property
    def weekly_quota_warning(self) -> bool:
        return self.weekly_quota_used_pct >= 80.0

    @property
    def weekly_quota_critical(self) -> bool:
        return self.weekly_quota_used_pct >= 95.0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "quota_used_pct": round(self.quota_used_pct, 1),
            "quota_remaining_usd": round(self.quota_remaining_usd, 2),
            "quota_warning": self.quota_warning,
            "quota_critical": self.quota_critical,
            "rate_limited": self.rate_limited,
            "model_available": self.model_available,
            "weekly_quota_used_pct": round(self.weekly_quota_used_pct, 1),
            "weekly_quota_warning": self.weekly_quota_warning,
            "weekly_quota_critical": self.weekly_quota_critical,
            "context_window_size": self.context_window_size,
        })
        return d


# ─── OpenRouter Health ─────────────────────────────────────────


@dataclass
class OpenRouterHealth(BackendHealthState):
    """OpenRouter backend health state."""

    free_models_available: list[str] = field(default_factory=list)
    free_tier_active: bool = False
    rate_limited: bool = False

    def __post_init__(self) -> None:
        self.name = "openrouter-free"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "free_models_available": self.free_models_available,
            "free_tier_active": self.free_tier_active,
            "rate_limited": self.rate_limited,
        })
        return d


# ─── Health Dashboard ──────────────────────────────────────────


class BackendHealthDashboard:
    """Aggregates health state across all fleet backends.

    Provides a unified view for fleet-ops monitoring.
    """

    def __init__(self) -> None:
        self._backends: dict[str, BackendHealthState] = {}
        self._check_history: list[dict] = []
        self._max_history = 100

    def update(self, state: BackendHealthState) -> None:
        """Update health state for a backend."""
        self._backends[state.name] = state
        self._check_history.append({
            "name": state.name,
            "status": state.status.value,
            "timestamp": state.last_check,
            "latency_ms": state.latency_ms,
        })
        if len(self._check_history) > self._max_history:
            self._check_history = self._check_history[-self._max_history:]

    def get(self, name: str) -> Optional[BackendHealthState]:
        return self._backends.get(name)

    @property
    def backends(self) -> list[BackendHealthState]:
        return list(self._backends.values())

    @property
    def all_healthy(self) -> bool:
        if not self._backends:
            return False
        return all(b.is_healthy for b in self._backends.values())

    @property
    def any_healthy(self) -> bool:
        return any(b.is_healthy for b in self._backends.values())

    def healthy_backends(self) -> list[str]:
        return [b.name for b in self._backends.values() if b.is_healthy]

    def unhealthy_backends(self) -> list[str]:
        return [b.name for b in self._backends.values() if not b.is_healthy]

    def stale_backends(self) -> list[str]:
        return [b.name for b in self._backends.values() if b.stale]

    # ─── Availability Score ─────────────────────────────────────

    @property
    def availability_score(self) -> float:
        """0.0-1.0 score of how many backends are healthy."""
        if not self._backends:
            return 0.0
        healthy = sum(1 for b in self._backends.values() if b.is_healthy)
        return healthy / len(self._backends)

    # ─── Fleet Routing Readiness ────────────────────────────────

    def routing_options(self) -> dict[str, bool]:
        """Which routing options are available right now."""
        localai = self._backends.get("localai")
        claude = self._backends.get("claude-code")
        openrouter = self._backends.get("openrouter-free")

        return {
            "localai": localai.is_healthy if localai else False,
            "claude-code": claude.is_healthy if claude else False,
            "openrouter-free": openrouter.is_healthy if openrouter else False,
            "direct": True,  # Direct/no-LLM is always available
        }

    # ─── Summary ────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "total_backends": len(self._backends),
            "healthy": len(self.healthy_backends()),
            "unhealthy": len(self.unhealthy_backends()),
            "stale": len(self.stale_backends()),
            "availability_score": round(self.availability_score, 3),
            "routing_options": self.routing_options(),
            "backends": {
                name: state.to_dict()
                for name, state in self._backends.items()
            },
        }

    def format_report(self) -> str:
        """Format health dashboard as markdown for fleet-ops monitoring."""
        s = self.summary()
        lines = [
            "## Backend Health Dashboard",
            "",
            f"**Backends:** {s['healthy']}/{s['total_backends']} healthy",
            f"**Availability:** {s['availability_score']:.0%}",
            "",
            "### Backend Status",
            "",
            "| Backend | Status | Latency | Notes |",
            "|---------|--------|---------|-------|",
        ]

        for name, data in s["backends"].items():
            status = data["status"].upper()
            latency = f"{data['latency_ms']:.0f}ms" if data["latency_ms"] else "—"
            notes_parts: list[str] = []

            if data.get("stale"):
                notes_parts.append("STALE")
            if data.get("error"):
                notes_parts.append(data["error"][:40])

            # Backend-specific notes
            if name == "localai" and data.get("loaded_model"):
                notes_parts.append(f"model: {data['loaded_model']}")
            if name == "claude-code" and data.get("quota_warning"):
                notes_parts.append(f"quota: {data['quota_used_pct']:.0f}%")
            if name == "openrouter-free" and data.get("free_tier_active"):
                notes_parts.append(
                    f"{len(data.get('free_models_available', []))} free models"
                )

            notes = ", ".join(notes_parts) if notes_parts else "—"
            lines.append(f"| {name} | {status} | {latency} | {notes} |")

        lines.append("")

        # Routing options
        lines.append("### Routing Options")
        for backend, available in s["routing_options"].items():
            icon = "OK" if available else "UNAVAILABLE"
            lines.append(f"- {backend}: {icon}")

        return "\n".join(lines)