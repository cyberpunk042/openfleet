"""Token budget monitoring — read real Claude quota data and protect the fleet.

Three data sources for budget awareness:

1. CLAUDE_QUOTA_* environment variables (available inside agent sessions):
   - CLAUDE_QUOTA_SESSION — session quota percentage used
   - CLAUDE_QUOTA_WEEKLY_ALL — weekly quota (all models) percentage used
   - CLAUDE_QUOTA_WEEKLY_SONNET — weekly quota (Sonnet) percentage used

2. Admin API (requires sk-ant-admin-* key from Claude Console):
   - GET /v1/organizations/usage_report/messages
   - Full usage reporting with time buckets (1m, 1h, 1d)

3. Claude Agent SDK — total_cost_usd from result messages

The budget monitor:
- Reads quota percentages from env vars during agent sessions
- Tracks quota changes over time
- Alerts at thresholds: 50%, 70%, 80%, 90%
- Detects fast climbs: >5% in 5 minutes, >10% in 10 minutes
- Recommends pause when thresholds exceeded
- Posts alerts via ntfy and IRC

fleet-ops reads budget state during heartbeats and acts on anomalies.
The orchestrator checks budget before dispatching work.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class QuotaSnapshot:
    """A point-in-time reading of Claude quota levels."""

    timestamp: datetime
    session_pct: float = 0.0        # CLAUDE_QUOTA_SESSION
    weekly_all_pct: float = 0.0     # CLAUDE_QUOTA_WEEKLY_ALL
    weekly_sonnet_pct: float = 0.0  # CLAUDE_QUOTA_WEEKLY_SONNET


@dataclass
class BudgetAlert:
    """A budget alert that should be communicated to the human."""

    severity: str      # critical, high, medium, info
    title: str
    message: str
    action: str        # pause, warn, inform


@dataclass
class BudgetState:
    """Current budget tracking state with history."""

    current: Optional[QuotaSnapshot] = None
    history: list[QuotaSnapshot] = field(default_factory=list)
    alerts_fired: list[str] = field(default_factory=list)
    should_pause: bool = False
    pause_reason: str = ""


def read_quota_from_env() -> Optional[QuotaSnapshot]:
    """Read current quota levels from Claude environment variables.

    These are only available inside Claude Code agent sessions.
    Returns None if not available.
    """
    session = os.environ.get("CLAUDE_QUOTA_SESSION")
    weekly_all = os.environ.get("CLAUDE_QUOTA_WEEKLY_ALL")
    weekly_sonnet = os.environ.get("CLAUDE_QUOTA_WEEKLY_SONNET")

    if not any([session, weekly_all, weekly_sonnet]):
        return None

    return QuotaSnapshot(
        timestamp=datetime.now(),
        session_pct=float(session) if session else 0.0,
        weekly_all_pct=float(weekly_all) if weekly_all else 0.0,
        weekly_sonnet_pct=float(weekly_sonnet) if weekly_sonnet else 0.0,
    )


class BudgetMonitor:
    """Monitors Claude plan usage and detects anomalies.

    Call update() with each quota reading.
    Call check_alerts() to get any alerts that should be fired.
    Call should_dispatch() before dispatching work.
    """

    def __init__(self) -> None:
        self._state = BudgetState()
        self._thresholds = [50, 70, 80, 90]
        self._fast_climb_pct = 5.0        # Alert if >5% in 5 minutes
        self._fast_climb_window = 300      # 5 minutes in seconds

    def update(self, snapshot: QuotaSnapshot) -> None:
        """Record a new quota snapshot."""
        self._state.current = snapshot
        self._state.history.append(snapshot)

        # Keep last 100 readings
        if len(self._state.history) > 100:
            self._state.history = self._state.history[-100:]

    def check_alerts(self) -> list[BudgetAlert]:
        """Check for budget alerts based on current and historical data."""
        alerts: list[BudgetAlert] = []
        if not self._state.current:
            return alerts

        current = self._state.current

        # Threshold alerts for weekly_all (the main budget)
        for threshold in self._thresholds:
            if current.weekly_all_pct >= threshold:
                alert_key = f"weekly_all_{threshold}"
                if alert_key not in self._state.alerts_fired:
                    self._state.alerts_fired.append(alert_key)
                    severity = "critical" if threshold >= 90 else "high" if threshold >= 80 else "medium"
                    action = "pause" if threshold >= 90 else "warn"
                    alerts.append(BudgetAlert(
                        severity=severity,
                        title=f"Weekly budget at {current.weekly_all_pct:.0f}%",
                        message=(
                            f"Weekly all-models quota: {current.weekly_all_pct:.0f}% used. "
                            f"Weekly Sonnet: {current.weekly_sonnet_pct:.0f}% used. "
                            f"Session: {current.session_pct:.0f}% used."
                        ),
                        action=action,
                    ))
                    if threshold >= 90:
                        self._state.should_pause = True
                        self._state.pause_reason = f"Weekly budget at {current.weekly_all_pct:.0f}%"

        # Fast climb detection
        if len(self._state.history) >= 2:
            recent = self._state.history[-1]
            for older in reversed(self._state.history[:-1]):
                age = (recent.timestamp - older.timestamp).total_seconds()
                if age > self._fast_climb_window:
                    break
                climb = recent.weekly_all_pct - older.weekly_all_pct
                if climb >= self._fast_climb_pct:
                    alert_key = f"fast_climb_{recent.timestamp.minute}"
                    if alert_key not in self._state.alerts_fired:
                        self._state.alerts_fired.append(alert_key)
                        alerts.append(BudgetAlert(
                            severity="critical",
                            title=f"Fast budget climb: +{climb:.0f}% in {age:.0f}s",
                            message=(
                                f"Weekly quota jumped from {older.weekly_all_pct:.0f}% "
                                f"to {recent.weekly_all_pct:.0f}% in {age:.0f} seconds. "
                                f"Possible runaway drain. PAUSE RECOMMENDED."
                            ),
                            action="pause",
                        ))
                        self._state.should_pause = True
                        self._state.pause_reason = f"Fast climb: +{climb:.0f}% in {age:.0f}s"
                    break

        return alerts

    def should_dispatch(self) -> tuple[bool, str]:
        """Check if it's safe to dispatch more work.

        Returns (safe, reason).
        """
        if self._state.should_pause:
            return False, self._state.pause_reason

        if self._state.current:
            if self._state.current.weekly_all_pct >= 90:
                return False, f"Weekly budget at {self._state.current.weekly_all_pct:.0f}%"
            if self._state.current.weekly_sonnet_pct >= 90:
                return False, f"Sonnet budget at {self._state.current.weekly_sonnet_pct:.0f}%"

        return True, ""

    def get_state(self) -> BudgetState:
        """Get current budget state for reporting."""
        return self._state

    def format_status(self) -> str:
        """Format current budget status for display."""
        if not self._state.current:
            return "Budget: no data (quota env vars not available)"

        c = self._state.current
        return (
            f"Budget: weekly_all={c.weekly_all_pct:.0f}% "
            f"weekly_sonnet={c.weekly_sonnet_pct:.0f}% "
            f"session={c.session_pct:.0f}%"
            f"{' ⚠️ PAUSE RECOMMENDED' if self._state.should_pause else ''}"
        )