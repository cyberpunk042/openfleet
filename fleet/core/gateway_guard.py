"""Gateway duplication guard — detect and clean stale gateway processes.

The March 2026 catastrophe was caused by multiple gateway processes
running simultaneously, each spawning independent MCP sessions and
burning tokens in parallel. 2123 MCP server starts from duplicate
processes that went undetected.

This module detects stale gateway processes and reports to the storm
monitor. Called by the orchestrator at startup and every N cycles.

Root causes addressed:
- Stale gateway from previous day still running after restart
- Multiple gateway instances after crash-recovery
- Ghost processes holding WebSocket connections open
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GatewayProcess:
    """A detected gateway process."""

    pid: int
    start_time: str = ""
    command: str = ""
    elapsed: str = ""


@dataclass
class GatewayGuardResult:
    """Result of a gateway duplication check."""

    ok: bool
    processes_found: int = 0
    processes_killed: int = 0
    stale_pids: list[int] = field(default_factory=list)
    message: str = ""


def find_gateway_processes() -> list[GatewayProcess]:
    """Find all running OpenClaw gateway processes.

    Looks for node processes running the OpenClaw gateway server.
    Uses 'ps' on Linux/WSL.
    """
    processes = []
    try:
        # Look for node processes with openclaw/gateway in the command line
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return processes

        for line in result.stdout.splitlines():
            # Match gateway processes — OpenClaw runs as a node process
            if "openclaw" in line.lower() and ("gateway" in line.lower() or "server" in line.lower()):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        processes.append(GatewayProcess(
                            pid=pid,
                            command=line.strip(),
                            start_time=parts[8] if len(parts) > 8 else "",
                            elapsed=parts[9] if len(parts) > 9 else "",
                        ))
                    except (ValueError, IndexError):
                        continue
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        logger.warning("Could not scan for gateway processes: %s", e)

    return processes


def find_mcp_server_processes() -> list[GatewayProcess]:
    """Find MCP server processes spawned by the gateway.

    During the March catastrophe, 2123 MCP server processes were
    spawned. This detects runaway MCP process counts.
    """
    processes = []
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return processes

        for line in result.stdout.splitlines():
            if "mcp" in line.lower() and ("server" in line.lower() or "claude" in line.lower()):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        processes.append(GatewayProcess(
                            pid=pid,
                            command=line.strip(),
                        ))
                    except (ValueError, IndexError):
                        continue
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass

    return processes


def check_gateway_duplication(
    max_allowed: int = 1,
    max_mcp_servers: int = 20,
) -> GatewayGuardResult:
    """Check for gateway duplication — the #1 storm root cause.

    Args:
        max_allowed: Maximum number of gateway processes allowed.
        max_mcp_servers: Maximum MCP server processes before flagging.

    Returns:
        GatewayGuardResult with detection status.
    """
    gateways = find_gateway_processes()
    mcp_servers = find_mcp_server_processes()

    messages = []
    stale_pids = []

    if len(gateways) > max_allowed:
        # Sort by PID — highest PID is usually newest
        gateways.sort(key=lambda g: g.pid)
        stale = gateways[:-max_allowed]  # Keep the newest
        stale_pids = [g.pid for g in stale]
        messages.append(
            f"DUPLICATION: {len(gateways)} gateway processes found, "
            f"expected {max_allowed}. Stale PIDs: {stale_pids}"
        )

    if len(mcp_servers) > max_mcp_servers:
        messages.append(
            f"MCP STORM: {len(mcp_servers)} MCP server processes "
            f"(threshold: {max_mcp_servers})"
        )

    if messages:
        return GatewayGuardResult(
            ok=False,
            processes_found=len(gateways),
            stale_pids=stale_pids,
            message=" | ".join(messages),
        )

    return GatewayGuardResult(
        ok=True,
        processes_found=len(gateways),
        message=f"Gateway OK: {len(gateways)} process(es), "
                f"{len(mcp_servers)} MCP server(s)",
    )


def kill_stale_gateways(stale_pids: list[int], dry_run: bool = True) -> int:
    """Kill stale gateway processes.

    SAFETY: Default is dry_run=True. The orchestrator must explicitly
    opt in to killing processes. This is a destructive operation.

    Args:
        stale_pids: PIDs to kill.
        dry_run: If True, only log what would be killed.

    Returns:
        Number of processes killed (0 if dry_run).
    """
    killed = 0
    for pid in stale_pids:
        if dry_run:
            logger.warning("DRY RUN: Would kill stale gateway PID %d", pid)
        else:
            try:
                os.kill(pid, 15)  # SIGTERM — graceful
                logger.warning("Killed stale gateway PID %d (SIGTERM)", pid)
                killed += 1
            except ProcessLookupError:
                logger.info("PID %d already gone", pid)
            except PermissionError:
                logger.error("No permission to kill PID %d", pid)
            except OSError as e:
                logger.error("Failed to kill PID %d: %s", pid, e)
    return killed