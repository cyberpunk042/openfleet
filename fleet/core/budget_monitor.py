"""Token budget monitoring — read REAL Claude quota via OAuth usage API.

Uses the undocumented but functional endpoint:
  GET https://api.anthropic.com/api/oauth/usage
  Authorization: Bearer <oauth_token>
  anthropic-beta: oauth-2025-04-20

Returns real-time utilization percentages and reset times for:
  - five_hour: session window utilization
  - seven_day: weekly all-models utilization
  - seven_day_sonnet: weekly Sonnet utilization

The orchestrator calls check_quota() before dispatching work.
If thresholds exceeded → refuse dispatch, alert human via ntfy.
Detects fast climbs (budget draining too quickly).

NOTE: This endpoint is rate-limited. Don't call more than once per minute.
The orchestrator caches readings and only re-checks every 5 minutes.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


USAGE_API = "https://api.anthropic.com/api/oauth/usage"
CACHE_TTL_SECONDS = 300  # Only check every 5 minutes (rate-limit protection)


@dataclass
class QuotaReading:
    """Real-time quota reading from Claude API."""

    timestamp: datetime
    session_pct: float = 0.0         # five_hour utilization
    weekly_all_pct: float = 0.0      # seven_day utilization
    weekly_sonnet_pct: float = 0.0   # seven_day_sonnet utilization
    session_resets_at: str = ""
    weekly_resets_at: str = ""


@dataclass
class BudgetAlert:
    """A budget alert to communicate to human."""

    severity: str      # critical, high, medium, info
    title: str
    message: str
    action: str        # pause, warn, inform


class BudgetMonitor:
    """Monitors Claude plan usage via OAuth API."""

    def __init__(self) -> None:
        self._last_reading: Optional[QuotaReading] = None
        self._last_check_time: float = 0
        self._history: list[QuotaReading] = []
        self._alerts_fired: set[str] = set()
        self._should_pause: bool = False
        self._pause_reason: str = ""

    def _get_oauth_token(self) -> str:
        """Read OAuth token from Claude credentials."""
        creds_path = Path.home() / ".claude" / ".credentials.json"
        if not creds_path.exists():
            return ""
        try:
            with open(creds_path) as f:
                creds = json.load(f)
            return creds.get("claudeAiOauth", {}).get("accessToken", "")
        except Exception:
            return ""

    def _fetch_quota(self) -> Optional[QuotaReading]:
        """Fetch quota from Claude OAuth API. Rate-limited to 1 call per CACHE_TTL."""
        now = time.time()
        if now - self._last_check_time < CACHE_TTL_SECONDS and self._last_reading:
            return self._last_reading

        token = self._get_oauth_token()
        if not token:
            return None

        try:
            import urllib.request
            req = urllib.request.Request(
                USAGE_API,
                headers={
                    "Authorization": f"Bearer {token}",
                    "anthropic-beta": "oauth-2025-04-20",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            reading = QuotaReading(
                timestamp=datetime.now(),
                session_pct=data.get("five_hour", {}).get("utilization", 0) or 0,
                weekly_all_pct=data.get("seven_day", {}).get("utilization", 0) or 0,
                weekly_sonnet_pct=data.get("seven_day_sonnet", {}).get("utilization", 0) or 0,
                session_resets_at=data.get("five_hour", {}).get("resets_at", ""),
                weekly_resets_at=data.get("seven_day", {}).get("resets_at", ""),
            )

            self._last_reading = reading
            self._last_check_time = now
            self._history.append(reading)
            if len(self._history) > 50:
                self._history = self._history[-50:]

            return reading
        except Exception:
            return self._last_reading  # Return cached on error

    def check_quota(self) -> tuple[bool, str]:
        """Check if it's safe to dispatch work.

        Returns (safe_to_dispatch, reason).
        """
        reading = self._fetch_quota()
        if not reading:
            return True, ""  # No data = assume safe (can't block on missing data)

        # Hard limits
        if reading.weekly_all_pct >= 90:
            self._should_pause = True
            self._pause_reason = f"Weekly budget at {reading.weekly_all_pct:.0f}%"
            return False, self._pause_reason

        if reading.session_pct >= 95:
            return False, f"Session budget at {reading.session_pct:.0f}% — wait for reset at {reading.session_resets_at}"

        if reading.weekly_sonnet_pct >= 90:
            return False, f"Sonnet budget at {reading.weekly_sonnet_pct:.0f}%"

        # Fast climb detection
        if len(self._history) >= 2:
            prev = self._history[-2]
            climb = reading.weekly_all_pct - prev.weekly_all_pct
            elapsed = (reading.timestamp - prev.timestamp).total_seconds()
            if climb >= 5 and elapsed < 600:  # 5% in 10 minutes
                self._should_pause = True
                self._pause_reason = f"Fast climb: +{climb:.0f}% in {elapsed:.0f}s"
                return False, self._pause_reason

        return True, ""

    def get_alerts(self) -> list[BudgetAlert]:
        """Check for budget alerts. Only fires each alert once."""
        alerts = []
        reading = self._last_reading
        if not reading:
            return alerts

        thresholds = [(50, "medium"), (70, "high"), (80, "high"), (90, "critical")]
        for threshold, severity in thresholds:
            if reading.weekly_all_pct >= threshold:
                key = f"weekly_{threshold}"
                if key not in self._alerts_fired:
                    self._alerts_fired.add(key)
                    alerts.append(BudgetAlert(
                        severity=severity,
                        title=f"Weekly budget at {reading.weekly_all_pct:.0f}%",
                        message=(
                            f"Session: {reading.session_pct:.0f}%, "
                            f"Weekly: {reading.weekly_all_pct:.0f}%, "
                            f"Sonnet: {reading.weekly_sonnet_pct:.0f}%. "
                            f"Weekly resets: {reading.weekly_resets_at}"
                        ),
                        action="pause" if threshold >= 90 else "warn",
                    ))

        return alerts

    def format_status(self) -> str:
        """Format current budget status."""
        reading = self._last_reading
        if not reading:
            return "Budget: no data (OAuth token missing or API unreachable)"

        return (
            f"Budget: session={reading.session_pct:.0f}% "
            f"weekly={reading.weekly_all_pct:.0f}% "
            f"sonnet={reading.weekly_sonnet_pct:.0f}% "
            f"resets={reading.weekly_resets_at[:16]}"
            f"{' ⚠️ PAUSE' if self._should_pause else ''}"
        )

    @property
    def should_pause(self) -> bool:
        return self._should_pause

    @property
    def pause_reason(self) -> str:
        return self._pause_reason