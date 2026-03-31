"""Post-incident report generation (M-SP07).

Automatic report after every WARNING+ storm event:
  - Severity, duration, cost impact
  - Which indicators triggered
  - What automatic responses fired
  - Prevention recommendations
  - Labor cost breakdown

Reports are generated from StormDiagnostic snapshots and storm
monitor state. Posted to board memory, saved to logs, available
to fleet-ops for post-incident analysis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─── Response Timeline Entry ───────────────────────────────────────


@dataclass
class ResponseEntry:
    """A single automatic response action taken during a storm."""

    timestamp: float
    action: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "time": datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S"),
            "action": self.action,
            "detail": self.detail,
        }


# ─── Incident Report ──────────────────────────────────────────────


@dataclass
class IncidentReport:
    """Post-incident report generated after a WARNING+ storm event.

    Captures what happened, what the system did, and what should
    be done to prevent recurrence.
    """

    # Identity
    incident_id: str = ""
    generated_at: str = ""

    # Severity and timing
    peak_severity: str = ""
    started_at: float = 0.0
    ended_at: float = 0.0
    duration_seconds: float = 0.0

    # What triggered the storm
    indicators: list[str] = field(default_factory=list)
    root_cause: str = ""

    # What the system did
    responses: list[ResponseEntry] = field(default_factory=list)
    budget_mode_before: str = ""
    budget_mode_after: str = ""

    # Cost impact
    estimated_cost_usd: float = 0.0
    void_sessions: int = 0
    total_sessions: int = 0
    void_session_pct: float = 0.0

    # Prevention
    prevention_recommendations: list[str] = field(default_factory=list)

    # Context
    agent_states: dict = field(default_factory=dict)
    diagnostics_count: int = 0

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()
        if not self.incident_id:
            self.incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if self.started_at and self.ended_at:
            self.duration_seconds = self.ended_at - self.started_at

    @property
    def duration_display(self) -> str:
        """Human-readable duration."""
        seconds = int(self.duration_seconds)
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining = seconds % 60
        if minutes < 60:
            return f"{minutes}m {remaining}s"
        hours = minutes // 60
        remaining_min = minutes % 60
        return f"{hours}h {remaining_min}m"

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "generated_at": self.generated_at,
            "peak_severity": self.peak_severity,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "indicators": self.indicators,
            "root_cause": self.root_cause,
            "responses": [r.to_dict() for r in self.responses],
            "budget_mode_before": self.budget_mode_before,
            "budget_mode_after": self.budget_mode_after,
            "estimated_cost_usd": round(self.estimated_cost_usd, 2),
            "void_sessions": self.void_sessions,
            "total_sessions": self.total_sessions,
            "void_session_pct": round(self.void_session_pct, 1),
            "prevention_recommendations": self.prevention_recommendations,
            "diagnostics_count": self.diagnostics_count,
        }

    def format_markdown(self) -> str:
        """Format the report as markdown for board memory or file storage."""
        lines = [
            f"## Storm Incident Report — {self.incident_id}",
            "",
            f"### Severity: {self.peak_severity}",
            f"### Duration: {self.duration_display}",
            f"### Cost Impact: ~${self.estimated_cost_usd:.2f} estimated",
            "",
        ]

        # Indicators
        lines.append("### Indicators")
        if self.indicators:
            for ind in self.indicators:
                lines.append(f"- {ind}")
        else:
            lines.append("- (none recorded)")
        lines.append("")

        # Root cause
        if self.root_cause:
            lines.append("### Root Cause")
            lines.append(self.root_cause)
            lines.append("")

        # Automatic response timeline
        lines.append("### Automatic Response")
        if self.responses:
            for i, resp in enumerate(self.responses, 1):
                detail = f" — {resp.detail}" if resp.detail else ""
                lines.append(f"{i}. {resp.to_dict()['time']} — {resp.action}{detail}")
        else:
            lines.append("- No automatic responses recorded")
        lines.append("")

        # Budget mode transition
        if self.budget_mode_before or self.budget_mode_after:
            lines.append("### Budget Mode")
            lines.append(
                f"- Before: {self.budget_mode_before or 'unknown'}"
            )
            lines.append(
                f"- After: {self.budget_mode_after or 'unknown'}"
            )
            lines.append("")

        # Session impact
        if self.total_sessions > 0:
            lines.append("### Session Impact")
            lines.append(
                f"- {self.void_sessions} void sessions "
                f"of {self.total_sessions} total ({self.void_session_pct:.0f}%)"
            )
            lines.append("")

        # Prevention
        lines.append("### Prevention")
        if self.prevention_recommendations:
            for rec in self.prevention_recommendations:
                lines.append(f"- {rec}")
        else:
            lines.append("- No specific recommendations")
        lines.append("")

        # Labor cost
        lines.append("### Labor Cost")
        if self.void_sessions > 0 and self.estimated_cost_usd > 0:
            per_session = self.estimated_cost_usd / self.void_sessions
            lines.append(
                f"- {self.void_sessions} void sessions "
                f"x ~${per_session:.2f} each = ~${self.estimated_cost_usd:.2f} wasted"
            )
        else:
            lines.append(f"- Estimated: ~${self.estimated_cost_usd:.2f}")
        lines.append("- Storm response: $0 (deterministic)")

        return "\n".join(lines)

    def format_summary(self) -> str:
        """Short one-line summary for IRC/ntfy alerts."""
        return (
            f"[incident] {self.incident_id}: {self.peak_severity} "
            f"for {self.duration_display}, "
            f"~${self.estimated_cost_usd:.2f} cost, "
            f"{len(self.indicators)} indicators"
        )

    def format_board_memory(self) -> str:
        """Format for posting to board memory."""
        indicators_str = ", ".join(self.indicators) if self.indicators else "none"
        return (
            f"[storm-incident] {self.incident_id}: "
            f"{self.peak_severity} for {self.duration_display} | "
            f"Indicators: {indicators_str} | "
            f"Cost: ~${self.estimated_cost_usd:.2f} | "
            f"Void sessions: {self.void_sessions}/{self.total_sessions}"
        )


# ─── Report Builder ───────────────────────────────────────────────


def build_incident_report(
    peak_severity: str,
    started_at: float,
    ended_at: float,
    indicators: list[str],
    responses: list[ResponseEntry],
    budget_mode_before: str = "",
    budget_mode_after: str = "",
    void_sessions: int = 0,
    total_sessions: int = 0,
    estimated_cost_per_void_session: float = 0.14,
    root_cause: str = "",
    agent_states: Optional[dict] = None,
    diagnostics_count: int = 0,
) -> IncidentReport:
    """Build an incident report from storm event data.

    Args:
        peak_severity: Highest severity reached during the storm.
        started_at: Unix timestamp when storm was first detected.
        ended_at: Unix timestamp when storm ended (indicators cleared).
        indicators: List of indicator names that triggered.
        responses: Timeline of automatic responses taken.
        budget_mode_before: Budget mode before storm started.
        budget_mode_after: Budget mode after storm ended.
        void_sessions: Number of sessions that produced no useful work.
        total_sessions: Total sessions during the storm period.
        estimated_cost_per_void_session: Estimated cost per void session in USD.
        root_cause: Optional root cause analysis.
        agent_states: Optional per-agent state snapshot.
        diagnostics_count: Number of diagnostic snapshots captured.

    Returns:
        IncidentReport ready for formatting and persistence.
    """
    void_pct = 0.0
    if total_sessions > 0:
        void_pct = (void_sessions / total_sessions) * 100

    estimated_cost = void_sessions * estimated_cost_per_void_session

    prevention = _generate_prevention_recommendations(
        indicators, peak_severity, void_sessions, total_sessions,
    )

    return IncidentReport(
        peak_severity=peak_severity,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=ended_at - started_at,
        indicators=indicators,
        root_cause=root_cause,
        responses=responses,
        budget_mode_before=budget_mode_before,
        budget_mode_after=budget_mode_after,
        estimated_cost_usd=estimated_cost,
        void_sessions=void_sessions,
        total_sessions=total_sessions,
        void_session_pct=void_pct,
        prevention_recommendations=prevention,
        agent_states=agent_states or {},
        diagnostics_count=diagnostics_count,
    )


# ─── Prevention Recommendations ───────────────────────────────────


_INDICATOR_RECOMMENDATIONS: dict[str, list[str]] = {
    "session_burst": [
        "Stagger heartbeats after gateway restart (max 3 simultaneous)",
        "Reduce default heartbeat concurrency",
    ],
    "void_sessions": [
        "Check agent heartbeat configuration — are agents waking with no work?",
        "Review heartbeat intervals — reduce frequency for idle agents",
    ],
    "fast_climb": [
        "Review dispatch frequency — too many tasks dispatched per cycle?",
        "Check for recursive task creation patterns",
    ],
    "gateway_duplication": [
        "Verify gateway startup script kills stale processes",
        "Add PID lock file to prevent duplicate gateways",
    ],
    "dispatch_storm": [
        "Reduce max_dispatch_per_cycle in fleet config",
        "Check for task auto-creation loops",
    ],
    "cascade_depth": [
        "Set hard limit on task-creates-task depth",
        "Review task dependency chains for cycles",
    ],
    "agent_thrashing": [
        "Increase heartbeat interval for idle agents",
        "Check if agents are repeatedly waking with no assignable work",
    ],
    "error_storm": [
        "Check backend availability — are API calls failing?",
        "Review error logs for common root cause",
    ],
}


def _generate_prevention_recommendations(
    indicators: list[str],
    peak_severity: str,
    void_sessions: int,
    total_sessions: int,
) -> list[str]:
    """Generate prevention recommendations based on storm indicators.

    Returns a deduplicated list of actionable recommendations.
    """
    recommendations: list[str] = []
    seen: set[str] = set()

    for indicator in indicators:
        # Strip value part (e.g., "session_burst: 15/min" → "session_burst")
        indicator_name = indicator.split(":")[0].strip()
        for rec in _INDICATOR_RECOMMENDATIONS.get(indicator_name, []):
            if rec not in seen:
                recommendations.append(rec)
                seen.add(rec)

    # Severity-based recommendations
    if peak_severity in ("STORM", "CRITICAL"):
        generic = "Review fleet configuration for systemic issues causing repeated storms"
        if generic not in seen:
            recommendations.append(generic)

    # Void session ratio
    if total_sessions > 0:
        void_pct = (void_sessions / total_sessions) * 100
        if void_pct > 50:
            rec = "High void session rate — investigate why agents start sessions with no work"
            if rec not in seen:
                recommendations.append(rec)

    return recommendations


# ─── Storm Event Tracker ──────────────────────────────────────────


@dataclass
class StormEvent:
    """Tracks an ongoing or completed storm event.

    The orchestrator creates a StormEvent when severity escalates to
    WARNING+, and closes it when severity drops back to CLEAR/WATCH.
    """

    started_at: float = 0.0
    peak_severity: str = ""
    indicators_seen: list[str] = field(default_factory=list)
    responses: list[ResponseEntry] = field(default_factory=list)
    budget_mode_at_start: str = ""
    ended_at: float = 0.0
    closed: bool = False

    def __post_init__(self) -> None:
        if not self.started_at:
            self.started_at = time.time()

    def record_severity(self, severity: str) -> None:
        """Update peak severity if this is higher."""
        from fleet.core.storm_monitor import severity_index
        if severity_index(severity) > severity_index(self.peak_severity):
            self.peak_severity = severity

    def record_indicator(self, indicator: str) -> None:
        """Record an indicator that triggered during this storm."""
        if indicator not in self.indicators_seen:
            self.indicators_seen.append(indicator)

    def record_response(self, action: str, detail: str = "") -> None:
        """Record an automatic response action."""
        self.responses.append(ResponseEntry(
            timestamp=time.time(),
            action=action,
            detail=detail,
        ))

    def close(self) -> None:
        """Mark the storm event as ended."""
        self.ended_at = time.time()
        self.closed = True

    def to_report(
        self,
        budget_mode_after: str = "",
        void_sessions: int = 0,
        total_sessions: int = 0,
        root_cause: str = "",
        diagnostics_count: int = 0,
    ) -> IncidentReport:
        """Generate an incident report from this storm event."""
        return build_incident_report(
            peak_severity=self.peak_severity,
            started_at=self.started_at,
            ended_at=self.ended_at or time.time(),
            indicators=self.indicators_seen,
            responses=self.responses,
            budget_mode_before=self.budget_mode_at_start,
            budget_mode_after=budget_mode_after,
            void_sessions=void_sessions,
            total_sessions=total_sessions,
            root_cause=root_cause,
            diagnostics_count=diagnostics_count,
        )