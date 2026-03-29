"""Agent error reporting — record errors for the orchestrator to detect.

When agents or MCP tools hit errors (rate limits, API failures, timeouts),
they write to a shared error log file. The orchestrator reads this file
each cycle to detect outages without needing the agent to be alive.

This is a file-based approach because:
1. It works even when the agent crashes (last error is still in the file)
2. The orchestrator can read it without API calls (direct file read)
3. No tokens consumed — just file I/O
4. Survives process restarts
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


ERROR_LOG_PATH = ".fleet-errors.json"


@dataclass
class AgentError:
    """A recorded error from an agent or tool."""

    timestamp: str
    agent: str
    source: str       # "mcp_tool", "heartbeat", "dispatch", "api_call"
    error_type: str   # "rate_limit", "timeout", "auth", "connection", "unknown"
    message: str
    tool_name: str = ""


def report_error(
    agent: str,
    source: str,
    error_type: str,
    message: str,
    tool_name: str = "",
    fleet_dir: str = "",
) -> None:
    """Write an error to the shared error log. No AI, no API — just file I/O."""
    if not fleet_dir:
        fleet_dir = os.environ.get("FLEET_DIR", ".")

    error = AgentError(
        timestamp=datetime.now().isoformat(),
        agent=agent,
        source=source,
        error_type=error_type,
        message=str(message)[:500],
        tool_name=tool_name,
    )

    log_path = os.path.join(fleet_dir, ERROR_LOG_PATH)

    try:
        errors = []
        if os.path.exists(log_path):
            with open(log_path) as f:
                errors = json.load(f)

        errors.append({
            "timestamp": error.timestamp,
            "agent": error.agent,
            "source": error.source,
            "error_type": error.error_type,
            "message": error.message,
            "tool_name": error.tool_name,
        })

        # Keep last 100 errors
        errors = errors[-100:]

        with open(log_path, "w") as f:
            json.dump(errors, f, indent=2)
    except Exception:
        pass  # Can't report errors about error reporting


def read_recent_errors(
    fleet_dir: str = "",
    since_minutes: int = 30,
) -> list[AgentError]:
    """Read recent errors from the shared log. Used by orchestrator."""
    if not fleet_dir:
        fleet_dir = os.environ.get("FLEET_DIR", ".")

    log_path = os.path.join(fleet_dir, ERROR_LOG_PATH)

    if not os.path.exists(log_path):
        return []

    try:
        with open(log_path) as f:
            errors = json.load(f)

        cutoff = time.time() - (since_minutes * 60)
        recent = []
        for e in errors:
            try:
                ts = datetime.fromisoformat(e["timestamp"])
                if ts.timestamp() >= cutoff:
                    recent.append(AgentError(**e))
            except Exception:
                continue

        return recent
    except Exception:
        return []


def detect_rate_limit(fleet_dir: str = "", window_minutes: int = 10) -> bool:
    """Check if any agent hit a rate limit recently."""
    errors = read_recent_errors(fleet_dir, since_minutes=window_minutes)
    return any(e.error_type == "rate_limit" for e in errors)


def detect_api_outage(fleet_dir: str = "", threshold: int = 3, window_minutes: int = 10) -> bool:
    """Check if multiple agents are reporting errors (likely API outage)."""
    errors = read_recent_errors(fleet_dir, since_minutes=window_minutes)
    agents_with_errors = set(e.agent for e in errors)
    return len(agents_with_errors) >= threshold