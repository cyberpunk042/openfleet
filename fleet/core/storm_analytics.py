"""Storm analytics (M-SP09).

Tracks storm frequency, duration, cost impact, and indicator trends
over time. Feeds into prevention improvements and PO reporting.

Design doc requirement:
> Track: storm frequency, duration, cost impact.
> Track: which indicators trigger most often.
> Track: time to detection, time to response.
> Feed into prevention improvements.
> Cross-ref: labor stamps provide cost data.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.incident_report import IncidentReport


# ─── Storm Record ───────────────────────────────────────────────


@dataclass
class StormRecord:
    """A historical storm event for analytics."""

    incident_id: str
    peak_severity: str
    duration_seconds: float
    estimated_cost_usd: float
    indicators: list[str] = field(default_factory=list)
    void_sessions: int = 0
    total_sessions: int = 0
    response_count: int = 0
    time_to_detection_seconds: float = 0.0
    time_to_response_seconds: float = 0.0

    @classmethod
    def from_report(cls, report: IncidentReport) -> "StormRecord":
        """Create a StormRecord from an IncidentReport."""
        time_to_response = 0.0
        if report.responses:
            first_response_time = report.responses[0].timestamp
            time_to_response = first_response_time - report.started_at

        return cls(
            incident_id=report.incident_id,
            peak_severity=report.peak_severity,
            duration_seconds=report.duration_seconds,
            estimated_cost_usd=report.estimated_cost_usd,
            indicators=[i.split(":")[0].strip() for i in report.indicators],
            void_sessions=report.void_sessions,
            total_sessions=report.total_sessions,
            response_count=len(report.responses),
            time_to_detection_seconds=0.0,  # Set by caller if known
            time_to_response_seconds=max(0.0, time_to_response),
        )

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "peak_severity": self.peak_severity,
            "duration_seconds": round(self.duration_seconds, 1),
            "estimated_cost_usd": round(self.estimated_cost_usd, 2),
            "indicators": self.indicators,
            "void_sessions": self.void_sessions,
            "total_sessions": self.total_sessions,
            "response_count": self.response_count,
            "time_to_detection_seconds": round(self.time_to_detection_seconds, 1),
            "time_to_response_seconds": round(self.time_to_response_seconds, 1),
        }


# ─── Storm Analytics Engine ─────────────────────────────────────


class StormAnalytics:
    """Aggregates storm incident data for trend analysis.

    Answers:
    - How often do storms happen?
    - What severity levels are most common?
    - Which indicators trigger storms most?
    - How long do storms last on average?
    - What is the total cost impact?
    - Is detection getting faster over time?
    """

    def __init__(self, max_records: int = 100) -> None:
        self._records: list[StormRecord] = []
        self._max_records = max_records

    def record(self, storm: StormRecord) -> None:
        """Record a storm event."""
        self._records.append(storm)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

    def record_from_report(self, report: IncidentReport) -> None:
        """Record from an IncidentReport directly."""
        self.record(StormRecord.from_report(report))

    def record_many(self, records: list[StormRecord]) -> None:
        for r in records:
            self.record(r)

    @property
    def total_storms(self) -> int:
        return len(self._records)

    @property
    def total_cost_usd(self) -> float:
        return sum(r.estimated_cost_usd for r in self._records)

    @property
    def total_void_sessions(self) -> int:
        return sum(r.void_sessions for r in self._records)

    # ─── Severity Distribution ───────────────────────────────────

    def severity_distribution(self) -> dict[str, int]:
        """Count of storms per severity level."""
        counts: dict[str, int] = {}
        for r in self._records:
            counts[r.peak_severity] = counts.get(r.peak_severity, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    # ─── Indicator Frequency ─────────────────────────────────────

    def indicator_frequency(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Most common indicators across all storms."""
        counter: Counter = Counter()
        for r in self._records:
            counter.update(r.indicators)
        return counter.most_common(top_n)

    # ─── Duration Stats ──────────────────────────────────────────

    def avg_duration_seconds(self) -> float:
        if not self._records:
            return 0.0
        return sum(r.duration_seconds for r in self._records) / len(self._records)

    def max_duration_seconds(self) -> float:
        if not self._records:
            return 0.0
        return max(r.duration_seconds for r in self._records)

    def min_duration_seconds(self) -> float:
        if not self._records:
            return 0.0
        return min(r.duration_seconds for r in self._records)

    # ─── Response Time Stats ─────────────────────────────────────

    def avg_time_to_response(self) -> float:
        """Average time from storm detection to first automatic response."""
        records_with_response = [
            r for r in self._records if r.time_to_response_seconds > 0
        ]
        if not records_with_response:
            return 0.0
        return (
            sum(r.time_to_response_seconds for r in records_with_response)
            / len(records_with_response)
        )

    # ─── Cost Analysis ───────────────────────────────────────────

    def avg_cost_per_storm(self) -> float:
        if not self._records:
            return 0.0
        return self.total_cost_usd / len(self._records)

    def cost_by_severity(self) -> dict[str, float]:
        """Total cost grouped by severity."""
        costs: dict[str, float] = {}
        for r in self._records:
            costs[r.peak_severity] = (
                costs.get(r.peak_severity, 0.0) + r.estimated_cost_usd
            )
        return {k: round(v, 2) for k, v in sorted(
            costs.items(), key=lambda x: x[1], reverse=True,
        )}

    # ─── Prevention Insights ─────────────────────────────────────

    def recurring_indicators(self, min_count: int = 2) -> list[tuple[str, int]]:
        """Indicators that appear in multiple storms — prevention targets."""
        freq = self.indicator_frequency()
        return [(ind, count) for ind, count in freq if count >= min_count]

    def void_session_rate(self) -> float:
        """Overall void session rate across all storms."""
        total_void = sum(r.void_sessions for r in self._records)
        total_sessions = sum(r.total_sessions for r in self._records)
        return total_void / total_sessions if total_sessions else 0.0

    # ─── Summary ─────────────────────────────────────────────────

    def summary(self) -> dict:
        """Full storm analytics summary."""
        return {
            "total_storms": self.total_storms,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "avg_cost_per_storm": round(self.avg_cost_per_storm(), 2),
            "total_void_sessions": self.total_void_sessions,
            "void_session_rate": round(self.void_session_rate(), 3),
            "severity_distribution": self.severity_distribution(),
            "top_indicators": self.indicator_frequency(top_n=5),
            "avg_duration_seconds": round(self.avg_duration_seconds(), 1),
            "max_duration_seconds": round(self.max_duration_seconds(), 1),
            "avg_time_to_response": round(self.avg_time_to_response(), 1),
            "recurring_indicators": self.recurring_indicators(),
        }

    def format_report(self) -> str:
        """Format storm analytics as markdown."""
        s = self.summary()
        lines = [
            "## Storm Analytics Report",
            "",
            f"**Total storms:** {s['total_storms']}",
            f"**Total cost:** ${s['total_cost_usd']:.2f}",
            f"**Avg cost/storm:** ${s['avg_cost_per_storm']:.2f}",
            f"**Void session rate:** {s['void_session_rate']:.1%}",
            f"**Avg duration:** {s['avg_duration_seconds']:.0f}s",
            f"**Avg response time:** {s['avg_time_to_response']:.0f}s",
            "",
        ]

        lines.append("### Severity Distribution")
        for sev, count in s["severity_distribution"].items():
            lines.append(f"- {sev}: {count}")
        lines.append("")

        lines.append("### Top Indicators")
        for ind, count in s["top_indicators"]:
            lines.append(f"- {ind}: {count} storms")
        lines.append("")

        if s["recurring_indicators"]:
            lines.append("### Prevention Targets (recurring indicators)")
            for ind, count in s["recurring_indicators"]:
                lines.append(f"- {ind}: appeared in {count} storms")

        return "\n".join(lines)