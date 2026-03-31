"""Session telemetry adapter (W8).

Parses Claude Code JSON session data and distributes real values
to existing fleet modules: LaborStamp, CostTicker, ClaudeHealth,
StormMonitor.

The JSON is the same data exposed to the IDE statusline on every turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ─── Session Snapshot ──────────────────────────────────────────────


@dataclass
class SessionSnapshot:
    """Typed parse of Claude Code session JSON.

    Fields mirror the JSON schema documented in
    docs/milestones/active/context-window-awareness-and-control.md § 3.3.
    """

    # Model
    model_id: str = ""
    model_display_name: str = ""

    # Context window
    context_window_size: int = 0        # 200000 or 1000000
    context_used_pct: float = 0.0
    context_remaining_pct: float = 0.0

    # Current turn usage
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    # Cumulative session totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Cost & duration
    total_cost_usd: float = 0.0
    total_duration_ms: int = 0
    total_api_duration_ms: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0

    # Rate limits (may be absent for non-subscribers)
    five_hour_used_pct: Optional[float] = None
    seven_day_used_pct: Optional[float] = None

    # Workspace
    current_dir: str = ""

    # Flags
    exceeds_200k: bool = False

    @property
    def context_label(self) -> str:
        """Human-readable context window size."""
        if self.context_window_size >= 900_000:
            return "1M"
        if self.context_window_size >= 180_000:
            return "200K"
        if self.context_window_size > 0:
            return f"{self.context_window_size // 1000}K"
        return "unknown"

    @property
    def context_pressure(self) -> str:
        """Severity label for context usage."""
        if self.context_used_pct >= 90:
            return "critical"
        if self.context_used_pct >= 70:
            return "high"
        if self.context_used_pct >= 50:
            return "moderate"
        return "low"

    @property
    def cache_hit_rate(self) -> float:
        """Fraction of input tokens served from cache (0.0–1.0)."""
        total = self.cache_read_tokens + self.cache_creation_tokens + self.input_tokens
        if total <= 0:
            return 0.0
        return self.cache_read_tokens / total

    @property
    def duration_seconds(self) -> int:
        return self.total_duration_ms // 1000

    @property
    def api_latency_ms(self) -> float:
        return float(self.total_api_duration_ms)


# ─── Parse ─────────────────────────────────────────────────────────


def ingest(data: dict) -> SessionSnapshot:
    """Parse Claude Code session JSON into a typed snapshot.

    Handles missing/null fields gracefully — all default to zero/empty.
    """
    model = data.get("model", {}) or {}
    ctx = data.get("context_window", {}) or {}
    usage = ctx.get("current_usage", {}) or {}
    cost = data.get("cost", {}) or {}
    rate = data.get("rate_limits", {}) or {}
    five_h = rate.get("five_hour", {}) or {}
    seven_d = rate.get("seven_day", {}) or {}
    ws = data.get("workspace", {}) or {}

    return SessionSnapshot(
        # Model
        model_id=model.get("id", ""),
        model_display_name=model.get("display_name", ""),

        # Context
        context_window_size=int(ctx.get("context_window_size", 0) or 0),
        context_used_pct=float(ctx.get("used_percentage", 0) or 0),
        context_remaining_pct=float(ctx.get("remaining_percentage", 0) or 0),

        # Current turn
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        cache_creation_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
        cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),

        # Cumulative
        total_input_tokens=int(ctx.get("total_input_tokens", 0) or 0),
        total_output_tokens=int(ctx.get("total_output_tokens", 0) or 0),

        # Cost
        total_cost_usd=float(cost.get("total_cost_usd", 0) or 0),
        total_duration_ms=int(cost.get("total_duration_ms", 0) or 0),
        total_api_duration_ms=int(cost.get("total_api_duration_ms", 0) or 0),
        total_lines_added=int(cost.get("total_lines_added", 0) or 0),
        total_lines_removed=int(cost.get("total_lines_removed", 0) or 0),

        # Rate limits
        five_hour_used_pct=(
            float(five_h["used_percentage"])
            if "used_percentage" in five_h else None
        ),
        seven_day_used_pct=(
            float(seven_d["used_percentage"])
            if "used_percentage" in seven_d else None
        ),

        # Workspace
        current_dir=ws.get("current_dir", ""),

        # Flags
        exceeds_200k=bool(data.get("exceeds_200k_tokens", False)),
    )


# ─── Distribution Helpers ──────────────────────────────────────────


def to_labor_fields(snap: SessionSnapshot) -> dict:
    """Fields to merge into LaborStamp assembly.

    Returns a dict matching LaborStamp field names so callers can do:
        stamp = LaborStamp(**base_fields, **to_labor_fields(snap))
    """
    return {
        "model": snap.model_id or "",
        "model_version": snap.model_id,
        "duration_seconds": snap.duration_seconds,
        "estimated_tokens": snap.total_input_tokens + snap.total_output_tokens,
        "estimated_cost_usd": snap.total_cost_usd,
        "session_type": "compact" if snap.exceeds_200k else "fresh",
        # New fields (require LaborStamp additions)
        "lines_added": snap.total_lines_added,
        "lines_removed": snap.total_lines_removed,
        "cache_read_tokens": snap.cache_read_tokens,
    }


def to_claude_health(snap: SessionSnapshot) -> dict:
    """Fields to update ClaudeHealth state.

    Returns a dict matching ClaudeHealth field names so callers can do:
        health = ClaudeHealth(**to_claude_health(snap))
    """
    result: dict = {
        "latency_ms": snap.api_latency_ms,
        "model_available": snap.model_display_name,
    }

    # Quota: prefer 5-hour as primary (more granular)
    if snap.five_hour_used_pct is not None:
        result["quota_used_pct"] = snap.five_hour_used_pct

    # New fields (require ClaudeHealth additions)
    if snap.seven_day_used_pct is not None:
        result["weekly_quota_used_pct"] = snap.seven_day_used_pct
    result["context_window_size"] = snap.context_window_size

    return result


def to_storm_indicators(snap: SessionSnapshot) -> list[tuple[str, str]]:
    """Storm indicators derived from session telemetry.

    Returns list of (indicator_name, value) tuples for
    StormMonitor.report_indicator().
    """
    indicators: list[tuple[str, str]] = []

    # Context pressure
    if snap.context_used_pct >= 70:
        indicators.append((
            "context_pressure",
            f"{snap.context_used_pct:.0f}%",
        ))

    # Quota pressure (5-hour window)
    if snap.five_hour_used_pct is not None and snap.five_hour_used_pct >= 80:
        indicators.append((
            "quota_pressure_5h",
            f"{snap.five_hour_used_pct:.0f}%",
        ))

    # Quota pressure (7-day window)
    if snap.seven_day_used_pct is not None and snap.seven_day_used_pct >= 80:
        indicators.append((
            "quota_pressure_7d",
            f"{snap.seven_day_used_pct:.0f}%",
        ))

    # Cache miss warning (cache not working = silent cost inflation)
    if snap.total_input_tokens > 10_000 and snap.cache_hit_rate < 0.1:
        indicators.append((
            "cache_miss",
            f"hit_rate={snap.cache_hit_rate:.1%}",
        ))

    return indicators


def to_cost_delta(snap: SessionSnapshot, previous_cost: float = 0.0) -> float:
    """Cost delta for CostTicker.add_cost().

    Pass the previous snapshot's total_cost_usd to get the incremental cost.
    On first call, pass 0.0 to get the full session cost.
    """
    return max(snap.total_cost_usd - previous_cost, 0.0)
