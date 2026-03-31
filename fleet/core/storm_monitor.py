"""Storm monitor — detect and respond to process storms automatically.

Monitors 9 indicators for storm conditions. When indicators exceed
thresholds, automatically escalates severity and triggers protective
responses (budget mode de-escalation, heartbeat disabling, dispatch
limiting, PO alerting).

Severity levels:
  CLEAR    — 0 indicators, normal operation
  WATCH    — 1 indicator, logging + monitoring
  WARNING  — 2 indicators or 1 sustained, force economic mode
  STORM    — 3+ indicators, force survival mode, alert PO
  CRITICAL — fast climb + burst, force blackout, kill sessions

De-escalation is slower than escalation (prevent oscillation).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─── Severity Levels ────────────────────────────────────────────────────


class StormSeverity:
    CLEAR = "CLEAR"
    WATCH = "WATCH"
    WARNING = "WARNING"
    STORM = "STORM"
    CRITICAL = "CRITICAL"


SEVERITY_ORDER = [
    StormSeverity.CLEAR,
    StormSeverity.WATCH,
    StormSeverity.WARNING,
    StormSeverity.STORM,
    StormSeverity.CRITICAL,
]


def severity_index(level: str) -> int:
    try:
        return SEVERITY_ORDER.index(level)
    except ValueError:
        return 0


# ─── Storm Indicator ────────────────────────────────────────────────────


@dataclass
class StormIndicator:
    """A detected storm condition."""

    name: str
    value: str
    detected_at: float = 0.0      # time.time() when first detected
    confirmed: bool = False        # True after confirmation window

    def __post_init__(self) -> None:
        if not self.detected_at:
            self.detected_at = time.time()


# ─── Diagnostic Snapshot ────────────────────────────────────────────────


@dataclass
class StormDiagnostic:
    """Captured when storm conditions detected (WARNING+)."""

    timestamp: str = ""
    severity: str = ""
    indicators: list[str] = field(default_factory=list)
    budget_reading: Optional[dict] = None
    active_sessions: int = 0
    sessions_last_hour: int = 0
    dispatches_last_hour: int = 0
    void_session_pct: float = 0.0
    agent_states: dict = field(default_factory=dict)
    error_count_last_20: int = 0
    budget_mode: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "indicators": self.indicators,
            "active_sessions": self.active_sessions,
            "sessions_last_hour": self.sessions_last_hour,
            "dispatches_last_hour": self.dispatches_last_hour,
            "void_session_pct": self.void_session_pct,
            "error_count_last_20": self.error_count_last_20,
            "budget_mode": self.budget_mode,
        }

    def format_summary(self) -> str:
        """Format for ntfy/IRC alert."""
        indicator_str = ", ".join(self.indicators) if self.indicators else "none"
        return (
            f"Storm {self.severity}: {indicator_str} | "
            f"Sessions/hr: {self.sessions_last_hour} | "
            f"Void: {self.void_session_pct:.0f}% | "
            f"Mode: {self.budget_mode}"
        )


# ─── Circuit Breaker ────────────────────────────────────────────────────


@dataclass
class CircuitBreaker:
    """Per-agent or per-backend circuit breaker.

    States: CLOSED (normal) → OPEN (tripped) → HALF_OPEN (testing)
    """

    name: str
    state: str = "CLOSED"              # CLOSED, OPEN, HALF_OPEN
    consecutive_failures: int = 0
    failure_threshold: int = 3         # Failures before tripping
    cooldown_seconds: float = 300.0    # 5 minutes default
    cooldown_multiplier: float = 2.0   # Doubles on repeated trips
    last_trip_time: float = 0.0
    trip_count: int = 0                # Total times tripped
    max_cooldown: float = 3600.0       # 1 hour max

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.consecutive_failures = 0
        elif self.state == "CLOSED":
            self.consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.consecutive_failures += 1
        if self.state == "HALF_OPEN":
            # Failed test → re-open with doubled cooldown
            self._trip()
            self.cooldown_seconds = min(
                self.cooldown_seconds * self.cooldown_multiplier,
                self.max_cooldown,
            )
        elif self.consecutive_failures >= self.failure_threshold:
            self._trip()

    def _trip(self) -> None:
        self.state = "OPEN"
        self.last_trip_time = time.time()
        self.trip_count += 1

    def check(self) -> bool:
        """Check if operations are allowed.

        Returns True if the circuit is closed or half-open (allow one test).
        """
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            elapsed = time.time() - self.last_trip_time
            if elapsed >= self.cooldown_seconds:
                self.state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN — allow one test
        return True

    @property
    def is_open(self) -> bool:
        return self.state == "OPEN"


# ─── Storm Monitor ──────────────────────────────────────────────────────


# Confirmation windows — how long an indicator must persist before confirmed
CONFIRMATION_SECONDS = {
    "session_burst": 60,
    "fast_climb": 300,       # Confirmed by two readings 5 min apart
    "void_sessions": 120,
    "dispatch_storm": 30,
    "cascade_depth": 30,
    "agent_thrashing": 120,
    "error_storm": 60,
    "gateway_duplication": 0,  # Immediate — always a problem
}

# De-escalation times (seconds indicator-free before dropping severity)
DEESCALATION_TIMES = {
    StormSeverity.CRITICAL: 600,    # 10 min → STORM (requires manual resume)
    StormSeverity.STORM: 600,       # 10 min → WARNING
    StormSeverity.WARNING: 900,     # 15 min → WATCH
    StormSeverity.WATCH: 1800,      # 30 min → CLEAR
}


class StormMonitor:
    """Monitors fleet for storm conditions and triggers responses."""

    def __init__(self) -> None:
        self._severity = StormSeverity.CLEAR
        self._indicators: dict[str, StormIndicator] = {}
        self._last_escalation: float = 0
        self._last_deescalation_check: float = 0
        self._indicators_clear_since: float = 0
        self._diagnostics: list[StormDiagnostic] = []
        self._agent_breakers: dict[str, CircuitBreaker] = {}
        self._backend_breakers: dict[str, CircuitBreaker] = {}
        self._session_times: list[float] = []     # Timestamps of recent sessions
        self._void_sessions: int = 0              # Count of void sessions
        self._total_sessions: int = 0             # Total session count
        self._dispatch_times: list[float] = []    # Timestamps of dispatches
        self._error_count: int = 0

    # ─── Indicator Reporting ────────────────────────────────────────

    def report_indicator(self, name: str, value: str = "") -> None:
        """Report a storm indicator. Called by orchestrator, gateway, etc."""
        if name not in self._indicators:
            self._indicators[name] = StormIndicator(name=name, value=value)
        else:
            self._indicators[name].value = value

        # Check confirmation
        confirm_window = CONFIRMATION_SECONDS.get(name, 60)
        indicator = self._indicators[name]
        elapsed = time.time() - indicator.detected_at
        if elapsed >= confirm_window:
            indicator.confirmed = True

        self._indicators_clear_since = 0  # Reset clear timer

    def clear_indicator(self, name: str) -> None:
        """Clear a storm indicator."""
        self._indicators.pop(name, None)

    def report_session(self, void: bool = False) -> None:
        """Report a session start. Used for burst detection."""
        now = time.time()
        self._session_times.append(now)
        self._total_sessions += 1
        if void:
            self._void_sessions += 1

        # Trim to last hour
        cutoff = now - 3600
        self._session_times = [t for t in self._session_times if t > cutoff]

        # Check for session burst: > 10 sessions in last 60 seconds
        recent = sum(1 for t in self._session_times if t > now - 60)
        if recent > 10:
            self.report_indicator("session_burst", f"{recent} sessions/min")

        # Check void session rate
        if self._total_sessions >= 10:
            void_pct = (self._void_sessions / self._total_sessions) * 100
            if void_pct > 50:
                self.report_indicator("void_sessions", f"{void_pct:.0f}%")

    def report_dispatch(self) -> None:
        """Report a task dispatch."""
        now = time.time()
        self._dispatch_times.append(now)
        cutoff = now - 3600
        self._dispatch_times = [t for t in self._dispatch_times if t > cutoff]

    def report_error(self) -> None:
        """Report an error."""
        self._error_count += 1

    # ─── Evaluation ─────────────────────────────────────────────────

    def evaluate(self) -> str:
        """Evaluate current storm severity.

        Called by the orchestrator at the start of every cycle.
        Returns the current severity level.
        """
        now = time.time()

        # Count confirmed indicators
        confirmed = [i for i in self._indicators.values() if i.confirmed]
        active_count = len(confirmed)

        # Remove stale unconfirmed indicators (older than 5 min)
        stale = [
            name for name, ind in self._indicators.items()
            if not ind.confirmed and (now - ind.detected_at) > 300
        ]
        for name in stale:
            del self._indicators[name]

        # Determine target severity
        has_fast_climb = any(i.name == "fast_climb" for i in confirmed)
        has_burst = any(i.name == "session_burst" for i in confirmed)

        if has_fast_climb and has_burst:
            target = StormSeverity.CRITICAL
        elif active_count >= 3:
            target = StormSeverity.STORM
        elif active_count >= 2:
            target = StormSeverity.WARNING
        elif active_count >= 1:
            target = StormSeverity.WATCH
        else:
            target = StormSeverity.CLEAR

        # Escalation: immediate
        if severity_index(target) > severity_index(self._severity):
            self._severity = target
            self._last_escalation = now
            self._indicators_clear_since = 0

        # De-escalation: slow
        elif severity_index(target) < severity_index(self._severity):
            if self._indicators_clear_since == 0:
                self._indicators_clear_since = now
            else:
                clear_duration = now - self._indicators_clear_since
                required = DEESCALATION_TIMES.get(self._severity, 900)
                if clear_duration >= required:
                    # Drop one level
                    current_idx = severity_index(self._severity)
                    self._severity = SEVERITY_ORDER[max(0, current_idx - 1)]
                    self._indicators_clear_since = now  # Reset for next level

        return self._severity

    @property
    def severity(self) -> str:
        return self._severity

    @property
    def confirmed_indicators(self) -> list[StormIndicator]:
        return [i for i in self._indicators.values() if i.confirmed]

    @property
    def sessions_last_hour(self) -> int:
        cutoff = time.time() - 3600
        return sum(1 for t in self._session_times if t > cutoff)

    @property
    def dispatches_last_hour(self) -> int:
        cutoff = time.time() - 3600
        return sum(1 for t in self._dispatch_times if t > cutoff)

    @property
    def void_session_pct(self) -> float:
        if self._total_sessions == 0:
            return 0.0
        return (self._void_sessions / self._total_sessions) * 100

    # ─── Circuit Breakers ───────────────────────────────────────────

    def get_agent_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for an agent."""
        if agent_name not in self._agent_breakers:
            self._agent_breakers[agent_name] = CircuitBreaker(
                name=f"agent:{agent_name}",
                failure_threshold=3,
                cooldown_seconds=300,
            )
        return self._agent_breakers[agent_name]

    def get_backend_breaker(self, backend_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a backend."""
        if backend_name not in self._backend_breakers:
            self._backend_breakers[backend_name] = CircuitBreaker(
                name=f"backend:{backend_name}",
                failure_threshold=3,
                cooldown_seconds=120,
            )
        return self._backend_breakers[backend_name]

    # ─── Diagnostics ────────────────────────────────────────────────

    def capture_diagnostic(self, budget_mode: str = "") -> StormDiagnostic:
        """Capture a diagnostic snapshot."""
        diag = StormDiagnostic(
            severity=self._severity,
            indicators=[f"{i.name}: {i.value}" for i in self.confirmed_indicators],
            active_sessions=0,  # Populated by orchestrator
            sessions_last_hour=self.sessions_last_hour,
            dispatches_last_hour=self.dispatches_last_hour,
            void_session_pct=self.void_session_pct,
            error_count_last_20=self._error_count,
            budget_mode=budget_mode,
        )
        self._diagnostics.append(diag)
        if len(self._diagnostics) > 20:
            self._diagnostics = self._diagnostics[-20:]
        return diag

    # ─── Status ─────────────────────────────────────────────────────

    def format_status(self) -> str:
        """Format current storm status for display."""
        indicators = [f"{i.name}" for i in self.confirmed_indicators]
        indicator_str = ", ".join(indicators) if indicators else "none"
        breakers_open = sum(1 for b in self._agent_breakers.values() if b.is_open)
        return (
            f"Storm: {self._severity} | "
            f"Indicators: {indicator_str} | "
            f"Sessions/hr: {self.sessions_last_hour} | "
            f"Void: {self.void_session_pct:.0f}% | "
            f"Breakers open: {breakers_open}"
        )