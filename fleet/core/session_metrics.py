"""Session metrics collection (M-LA03).

Tracks per-session telemetry: timing, tools called, token estimates,
and errors. These metrics feed into the LaborStamp via assemble_stamp()
when a task completes.

Usage:
    session = SessionMetrics(task_id="abc", agent_name="software-engineer")
    session.record_tool_call("fleet_read_context")
    session.record_tool_call("fleet_commit")
    session.record_tokens(input_tokens=500, output_tokens=1200)
    session.finish()
    # session.to_stamp_kwargs() returns dict for assemble_stamp()
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionMetrics:
    """Per-session telemetry collected during task execution."""

    task_id: str
    agent_name: str
    session_type: str = "fresh"         # "fresh", "resume", "retry"
    iteration: int = 1                  # Attempt number

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0

    # Tools
    tools_called: list[str] = field(default_factory=list)
    tool_call_count: int = 0

    # Tokens (estimated — exact counts come from API response)
    input_tokens: int = 0
    output_tokens: int = 0

    # Errors
    errors: list[str] = field(default_factory=list)
    error_count: int = 0

    # Backend (recorded when known)
    backend: str = ""
    model: str = ""

    @property
    def duration_seconds(self) -> int:
        """Wall-clock duration in seconds."""
        end = self.end_time or time.time()
        return max(0, int(end - self.start_time))

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def is_finished(self) -> bool:
        return self.end_time > 0

    def record_tool_call(self, tool_name: str) -> None:
        """Record a tool invocation."""
        if tool_name not in self.tools_called:
            self.tools_called.append(tool_name)
        self.tool_call_count += 1

    def record_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Accumulate token usage from an API response."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def record_error(self, error: str) -> None:
        """Record an error that occurred during the session."""
        self.errors.append(error)
        self.error_count += 1

    def finish(self) -> None:
        """Mark the session as finished."""
        self.end_time = time.time()

    def to_stamp_kwargs(self) -> dict:
        """Return kwargs suitable for assemble_stamp().

        This bridges session metrics into the labor stamp pipeline.
        """
        return {
            "duration_seconds": self.duration_seconds,
            "estimated_tokens": self.total_tokens,
            "tools_called": list(self.tools_called),
            "session_type": self.session_type,
            "iteration": self.iteration,
        }

    def to_dict(self) -> dict:
        """Serialize for persistence or logging."""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "session_type": self.session_type,
            "iteration": self.iteration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "tools_called": self.tools_called,
            "tool_call_count": self.tool_call_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "backend": self.backend,
            "model": self.model,
        }


# ─── Session Store ─────────────────────────────────────────────────


class SessionStore:
    """In-memory store of active and recent sessions.

    Provides lookup by task_id so fleet_task_complete can retrieve
    the metrics for stamp assembly.
    """

    def __init__(self, max_completed: int = 100) -> None:
        self._active: dict[str, SessionMetrics] = {}
        self._completed: list[SessionMetrics] = []
        self._max_completed = max_completed

    def start_session(
        self,
        task_id: str,
        agent_name: str,
        session_type: str = "fresh",
        iteration: int = 1,
        backend: str = "",
        model: str = "",
    ) -> SessionMetrics:
        """Create and register a new session."""
        session = SessionMetrics(
            task_id=task_id,
            agent_name=agent_name,
            session_type=session_type,
            iteration=iteration,
            backend=backend,
            model=model,
        )
        self._active[task_id] = session
        return session

    def get_active(self, task_id: str) -> Optional[SessionMetrics]:
        """Get the active session for a task."""
        return self._active.get(task_id)

    def finish_session(self, task_id: str) -> Optional[SessionMetrics]:
        """Finish and archive a session. Returns the finished session."""
        session = self._active.pop(task_id, None)
        if session:
            session.finish()
            self._completed.append(session)
            if len(self._completed) > self._max_completed:
                self._completed = self._completed[-self._max_completed:]
        return session

    def get_completed(self, task_id: str) -> Optional[SessionMetrics]:
        """Find the most recent completed session for a task."""
        for s in reversed(self._completed):
            if s.task_id == task_id:
                return s
        return None

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    def summary(self) -> dict:
        """Summary stats for monitoring."""
        total_tokens = sum(s.total_tokens for s in self._completed)
        total_errors = sum(s.error_count for s in self._completed)
        return {
            "active_sessions": self.active_count,
            "completed_sessions": self.completed_count,
            "total_tokens": total_tokens,
            "total_errors": total_errors,
        }