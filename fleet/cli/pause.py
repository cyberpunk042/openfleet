"""Fleet pause/resume — kill switch for the fleet.

Usage:
  python -m fleet pause [--reason "..."]
  python -m fleet resume

Pause: kills all fleet daemons, stops gateway heartbeats, notifies IRC/ntfy.
Resume: restarts daemons (must be done explicitly — no auto-resume).
"""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path


async def _pause(reason: str = "") -> int:
    """Pause the fleet — stop all processes that consume tokens."""
    print("=== FLEET PAUSE ===")
    print()

    actions = 0

    # 1. Kill fleet daemon processes
    print("1. Killing fleet daemon processes...")
    try:
        result = subprocess.run(
            ["pkill", "-f", "fleet daemon"], capture_output=True, timeout=5
        )
        print(f"   Fleet daemons: {'killed' if result.returncode == 0 else 'not running'}")
        actions += 1
    except Exception:
        print("   Fleet daemons: could not kill")

    # 2. Kill MCP server processes
    print("2. Killing MCP server processes...")
    try:
        result = subprocess.run(
            ["pkill", "-f", "fleet.mcp.server"], capture_output=True, timeout=5
        )
        print(f"   MCP servers: {'killed' if result.returncode == 0 else 'not running'}")
        actions += 1
    except Exception:
        print("   MCP servers: could not kill")

    # 3. Kill ALL gateway and openclaw processes
    print("3. Killing gateway and openclaw processes...")
    for pattern in ["openclaw-gateway", "openclaw$", "python3 -m gateway start", "miniircd"]:
        try:
            result = subprocess.run(
                ["pkill", "-f", pattern], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                print(f"   Killed: {pattern}")
                actions += 1
        except Exception:
            pass

    # 4. Write pause marker
    fleet_dir = str(Path(__file__).resolve().parent.parent.parent)
    pause_file = os.path.join(fleet_dir, ".fleet-paused")
    with open(pause_file, "w") as f:
        f.write(f"paused_at: {datetime.now().isoformat()}\n")
        if reason:
            f.write(f"reason: {reason}\n")
    print(f"\n4. Pause marker written: {pause_file}")

    # 5. Notify via ntfy if available
    try:
        from fleet.infra.ntfy_client import NtfyClient
        ntfy = NtfyClient()
        await ntfy.publish(
            title="Fleet PAUSED",
            message=f"Fleet paused{': ' + reason if reason else ''}. All processes stopped.",
            priority="important",
            tags=["pause_button", "fleet"],
        )
        await ntfy.close()
        print("5. ntfy notification sent")
    except Exception:
        print("5. ntfy notification skipped (not available)")

    print(f"\nFleet PAUSED. {actions} process groups killed.")
    print("To resume: python -m fleet resume")
    return 0


async def _resume() -> int:
    """Resume the fleet — check safety, then allow restart."""
    fleet_dir = str(Path(__file__).resolve().parent.parent.parent)
    pause_file = os.path.join(fleet_dir, ".fleet-paused")

    if os.path.exists(pause_file):
        with open(pause_file) as f:
            print(f"Fleet was paused:")
            print(f"  {f.read().strip()}")
        os.remove(pause_file)
        print()

    print("Fleet resumed. Pause marker removed.")
    print()
    print("To start daemons: python -m fleet daemon all")
    print("To start gateway: make gateway")
    print()
    print("IMPORTANT: Verify before restarting:")
    print("  1. Gateway heartbeat intervals are reasonable (30m+ for workers)")
    print("  2. No duplicate agents in gateway config")
    print("  3. No stale processes running")
    print("  4. Orchestrator has no _send_chat calls")
    return 0


def run_pause(args: list[str] | None = None) -> int:
    """Entry point for fleet pause/resume."""
    argv = args if args is not None else sys.argv[2:]

    if not argv or argv[0] == "pause":
        reason = ""
        if "--reason" in argv:
            idx = argv.index("--reason")
            if idx + 1 < len(argv):
                reason = argv[idx + 1]
        return asyncio.run(_pause(reason))
    elif argv[0] == "resume":
        return asyncio.run(_resume())
    else:
        print("Usage: fleet pause [--reason '...'] | fleet resume")
        return 1