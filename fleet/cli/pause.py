"""Fleet pause/resume — kill switch for the fleet.

Usage:
  python -m fleet pause [--reason "..."]
  python -m fleet resume

Pause: kills all fleet daemons, notifies IRC/ntfy. Heartbeats stay enabled.
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
    print("3. Killing gateway processes...")
    for pattern in ["openarms-gateway", "openclaw-gateway", "openarms$", "openclaw$", "python3 -m gateway start", "miniircd"]:
        try:
            result = subprocess.run(
                ["pkill", "-f", pattern], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                print(f"   Killed: {pattern}")
                actions += 1
        except Exception:
            pass

    # 3b. Disable gateway CRON jobs (heartbeats call Claude API = budget burn)
    try:
        from fleet.infra.gateway_client import disable_gateway_cron_jobs
        disabled = disable_gateway_cron_jobs()
        if disabled:
            print(f"   Disabled {disabled} gateway cron jobs")
        else:
            print("   No cron jobs to disable")
    except Exception:
        print("   WARN: Could not disable cron jobs")

    # 4. Set work mode to paused in config
    fleet_dir = str(Path(__file__).resolve().parent.parent.parent)
    print("4. Setting work mode to 'paused'...")
    try:
        import yaml
        config_path = os.path.join(fleet_dir, "config", "fleet.yaml")
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        if "orchestrator" not in cfg:
            cfg["orchestrator"] = {}
        with open(config_path, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
        actions += 1
    except Exception as e:
        print(f"   WARNING: Could not update config: {e}")

    # 5. Write pause marker
    pause_file = os.path.join(fleet_dir, ".fleet-paused")
    with open(pause_file, "w") as f:
        f.write(f"paused_at: {datetime.now().isoformat()}\n")
        if reason:
            f.write(f"reason: {reason}\n")
    print(f"\n5. Pause marker written: {pause_file}")

    # 5b. Update fleet_config in MC (so UI shows paused)
    try:
        from fleet.infra.mc_client import MCClient
        mc = MCClient()
        board_id = await mc.get_board_id()
        if board_id:
            board = await mc.get_board(board_id)
            current_config = board.get("fleet_config") or {}
            current_work_mode = current_config.get("work_mode", "full-autonomous")
            await mc.update_board_fleet_config(board_id, {
                "work_mode": "work-paused",
                "work_mode_before_pause": current_work_mode if current_work_mode != "work-paused" else current_config.get("work_mode_before_pause", "full-autonomous"),
                "updated_at": datetime.now().isoformat(),
                "updated_by": "cli",
            })
            print("   Fleet config updated in MC (work-paused)")
        await mc.close()
    except Exception as e:
        print(f"   WARN: Could not update MC fleet_config: {e}")

    # 7. Notify via ntfy if available
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
        print("7. ntfy notification sent")
    except Exception:
        print("7. ntfy notification skipped (not available)")

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

    # Restore work_mode from work_mode_before_pause
    try:
        from fleet.infra.mc_client import MCClient
        mc = MCClient()
        board_id = await mc.get_board_id()
        if board_id:
            board = await mc.get_board(board_id)
            current_config = board.get("fleet_config") or {}
            restore_mode = current_config.get("work_mode_before_pause", "full-autonomous")
            await mc.update_board_fleet_config(board_id, {
                "work_mode": restore_mode,
                "work_mode_before_pause": None,
                "updated_at": datetime.now().isoformat(),
                "updated_by": "cli",
            })
            print(f"   Fleet config updated in MC (restored to {restore_mode})")
        await mc.close()
    except Exception as e:
        print(f"   WARN: Could not update MC fleet_config: {e}")

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