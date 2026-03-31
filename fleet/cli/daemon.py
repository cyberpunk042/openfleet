"""Fleet daemons — background services for sync and monitoring.

Replaces: scripts/fleet-sync-daemon.sh, scripts/fleet-monitor-daemon.sh
Usage:
  python -m fleet daemon sync [--interval 60]
  python -m fleet daemon monitor [--interval 300]
  python -m fleet daemon all [--sync-interval 60] [--monitor-interval 300]
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

from fleet.cli.sync import _run_sync
from fleet.cli.quality import _run_quality
from fleet.cli.orchestrator import run_orchestrator_daemon


async def _run_sync_daemon(interval: int = 60) -> None:
    """Run fleet sync in a loop."""
    print(f"[sync] Daemon started (interval={interval}s)")
    while True:
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            result = await _run_sync()
        except Exception as e:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [sync] Error: {e}")
        await asyncio.sleep(interval)


async def _run_monitor_daemon(interval: int = 300) -> None:
    """Run board state monitor in a loop."""
    from fleet.infra.config_loader import ConfigLoader
    from fleet.infra.mc_client import MCClient
    from fleet.infra.irc_client import IRCClient
    from fleet.templates.irc import format_event
    import json

    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")

    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    print(f"[monitor] Daemon started (interval={interval}s)")

    while True:
        try:
            if not token:
                await asyncio.sleep(interval)
                continue

            mc = MCClient(token=token)
            board_id = await mc.get_board_id()
            if not board_id:
                await mc.close()
                await asyncio.sleep(interval)
                continue

            tasks = await mc.list_tasks(board_id)
            agents = await mc.list_agents()
            irc = IRCClient(gateway_token=gateway_token)
            now = datetime.now()
            alerts = 0

            for task in tasks:
                updated = task.updated_at
                if not updated:
                    continue

                hours = (now - updated).total_seconds() / 3600

                # Stale inbox
                if task.status.value == "inbox" and hours > 1:
                    try:
                        await irc.notify(
                            "#fleet",
                            format_event("fleet-ops", f"⏰ STALE INBOX", f"{task.title[:50]} ({int(hours)}h)"),
                        )
                    except Exception:
                        pass
                    alerts += 1

                # Stale review
                elif task.status.value == "review" and hours > 24:
                    channel = "#reviews" if task.custom_fields.pr_url else "#fleet"
                    try:
                        await irc.notify(
                            channel,
                            format_event("fleet-ops", f"⏰ STALE REVIEW", f"{task.title[:50]} ({int(hours)}h)", task.custom_fields.pr_url or ""),
                        )
                    except Exception:
                        pass
                    alerts += 1

            # Agent health
            for a in agents:
                if "Gateway" in a.name:
                    continue
                if a.status == "offline" and a.last_seen:
                    hours = (now - a.last_seen).total_seconds() / 3600
                    if hours > 2:
                        try:
                            await irc.notify(
                                "#alerts",
                                format_event("fleet-ops", "🔴 AGENT OFFLINE", f"{a.name} ({int(hours)}h)"),
                            )
                        except Exception:
                            pass
                        alerts += 1

            # OCMC watcher — detect state changes and emit events
            try:
                from fleet.core.ocmc_watcher import OCMCWatcher
                ocmc_watcher = OCMCWatcher()
                approvals_list = []
                try:
                    approvals_list = await mc.list_approvals(board_id, status="pending")
                except Exception:
                    pass
                ocmc_events = ocmc_watcher.poll(tasks, agents, approvals_list)
                if ocmc_events:
                    for oe in ocmc_events[:3]:
                        print(f"[{ts}] [monitor] Event: {oe.get('type', '?')}")
            except Exception:
                pass

            # Config watcher — detect manual config changes
            try:
                from fleet.core.config_watcher import ConfigWatcher
                config_watcher = ConfigWatcher()
                config_events = config_watcher.check()
                if config_events:
                    for ce in config_events:
                        print(f"[{ts}] [monitor] Config changed: {ce.get('file', '?')} ({ce.get('config_type', '?')})")
            except Exception:
                pass

            # Config sync — export Plane state to YAML configs + git commit
            try:
                from fleet.core.config_sync import ConfigSync
                syncer = ConfigSync()
                sync_result = syncer.export_and_commit()
                if sync_result.get("committed"):
                    print(f"[{ts}] [monitor] Config synced to git: {sync_result.get('files', [])}")
                elif sync_result.get("error"):
                    pass  # Silent — not all cycles need a sync
            except Exception:
                pass

            ts = datetime.now().strftime("%H:%M:%S")
            if alerts:
                print(f"[{ts}] [monitor] {alerts} alerts")
            else:
                print(f"[{ts}] [monitor] Board healthy")

            await mc.close()

        except Exception as e:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [monitor] Error: {e}")

        # Self-healing: check gateway health — but ONLY restart if MC is up.
        # If MC is down, the fleet is OFF. Do NOT restart the gateway.
        # Restarting the gateway when MC is down causes the gateway's cron
        # jobs to fire Claude heartbeats with no MC to talk to, burning
        # tokens for nothing.
        try:
            import subprocess
            import httpx as _httpx

            # First: is MC reachable? If not, fleet is OFF — do nothing.
            mc_up = False
            try:
                async with _httpx.AsyncClient(timeout=3) as _mc_check:
                    mc_resp = await _mc_check.get("http://localhost:8000/healthz")
                    mc_up = mc_resp.status_code == 200
            except Exception:
                mc_up = False

            if not mc_up:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] [monitor] MC is DOWN — fleet is OFF. NOT restarting gateway.")
            else:
                # MC is up — check if gateway needs restart
                try:
                    async with _httpx.AsyncClient(timeout=5) as _hc:
                        resp = await _hc.get("http://localhost:18789/")
                        # Gateway is alive
                except Exception:
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] [monitor] Gateway DOWN (MC is UP) — restarting...")
                    fleet_dir = os.environ.get("FLEET_DIR", str(Path(__file__).resolve().parent.parent.parent))
                    start_script = os.path.join(fleet_dir, "scripts", "start-fleet.sh")
                    if os.path.exists(start_script):
                        result = subprocess.run(
                            ["bash", start_script],
                            capture_output=True, text=True, timeout=120,
                        )
                        ts = datetime.now().strftime("%H:%M:%S")
                        if result.returncode == 0:
                            print(f"[{ts}] [monitor] Gateway restarted successfully")
                        else:
                            print(f"[{ts}] [monitor] Gateway restart FAILED: {result.stderr[:200]}")
        except Exception:
            pass

        await asyncio.sleep(interval)


async def _run_auth_daemon(interval: int = 120) -> None:
    """Auto-refresh auth token and restart gateway if needed."""
    from fleet.core.auth import refresh_token, token_needs_refresh
    from fleet.infra.gh_client import GHClient

    print(f"[auth] Daemon started (interval={interval}s)")
    while True:
        try:
            if token_needs_refresh():
                updated = refresh_token()
                if updated:
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] [auth] Token rotated — refreshed in ~/.openclaw/.env")

                    # Only restart gateway if MC is UP.
                    # If MC is down, fleet is OFF — don't restart gateway
                    # because the cron jobs would fire Claude calls for nothing.
                    mc_up = False
                    try:
                        import httpx as _httpx
                        async with _httpx.AsyncClient(timeout=3) as _mc_check:
                            mc_resp = await _mc_check.get("http://localhost:8000/healthz")
                            mc_up = mc_resp.status_code == 200
                    except Exception:
                        mc_up = False

                    if mc_up:
                        gh = GHClient()
                        await gh._run(["pkill", "-f", "openclaw-gateway"])
                        await asyncio.sleep(3)
                        await gh._run(["openclaw", "gateway", "run", "--port", "18789"])
                        await asyncio.sleep(5)
                        print(f"[{ts}] [auth] Gateway restarted with new token (MC is UP)")
                    else:
                        print(f"[{ts}] [auth] Token refreshed but MC is DOWN — NOT restarting gateway")
        except Exception as e:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [auth] Error: {e}")

        await asyncio.sleep(interval)


async def _run_plane_watcher_daemon(interval: int = 120) -> None:
    """Poll Plane for changes and emit events."""
    from fleet.infra.config_loader import ConfigLoader
    from fleet.infra.plane_client import PlaneClient

    loader = ConfigLoader()
    env = loader.load_env()
    plane_url = env.get("PLANE_URL", "")
    plane_key = env.get("PLANE_API_KEY", "")
    plane_ws = env.get("PLANE_WORKSPACE", "fleet")

    if not plane_url or not plane_key:
        print("[plane-watcher] Plane not configured — skipping")
        return

    print(f"[plane-watcher] Daemon started (interval={interval}s)")

    from fleet.core.plane_watcher import PlaneWatcher
    plane = PlaneClient(base_url=plane_url, api_key=plane_key)
    watcher = PlaneWatcher(plane, workspace_slug=plane_ws)

    while True:
        try:
            events = await watcher.poll()
            if events:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] [plane-watcher] {len(events)} changes detected")
                for e in events[:3]:
                    print(f"  {e.get('type', '?')}: {e.get('title', e.get('name', '?'))[:50]}")
        except Exception as e:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [plane-watcher] Error: {e}")

        await asyncio.sleep(interval)


async def _check_mc_alive() -> bool:
    """Check if MC is reachable. If not, fleet is OFF."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get("http://localhost:8000/healthz")
            return resp.status_code == 200
    except Exception:
        return False


async def _run_all(
    sync_interval: int = 60,
    monitor_interval: int = 300,
    orchestrator_interval: int = 30,
) -> None:
    """Run all daemons concurrently.

    If the orchestrator exits (MC down → fleet OFF), ALL daemons stop.
    When any task in the gather completes, we cancel the rest and
    kill the gateway. ZERO consumption when fleet is OFF.
    """
    print(
        f"Fleet daemons starting (sync={sync_interval}s, monitor={monitor_interval}s, "
        f"auth=120s, orchestrator={orchestrator_interval}s, plane-watcher=120s)"
    )

    # Verify MC is alive before starting anything
    if not await _check_mc_alive():
        print("[daemon] MC is DOWN. Cannot start fleet. Start Docker first.")
        return

    tasks = [
        asyncio.create_task(_run_sync_daemon(sync_interval), name="sync"),
        asyncio.create_task(_run_auth_daemon(120), name="auth"),
        asyncio.create_task(_run_monitor_daemon(monitor_interval), name="monitor"),
        asyncio.create_task(run_orchestrator_daemon(orchestrator_interval), name="orchestrator"),
        asyncio.create_task(_run_plane_watcher_daemon(120), name="plane-watcher"),
    ]

    # Wait for ANY task to complete (the orchestrator exits when MC goes down)
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # One daemon exited — fleet is OFF. Cancel everything else.
    for task in done:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [daemon] {task.get_name()} exited")

    for task in pending:
        task.cancel()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [daemon] Cancelling {task.get_name()}")

    # Kill gateway — no daemon = no fleet = no Claude calls
    import subprocess
    try:
        subprocess.run(["pkill", "-f", "openclaw-gateway"], capture_output=True, timeout=5)
        subprocess.run(["pkill", "-f", "openclaw$"], capture_output=True, timeout=5)
        print(f"[daemon] Gateway killed. Fleet is OFF. ZERO consumption.")
    except Exception:
        pass

    # Disable cron jobs — safety net
    try:
        from fleet.infra.gateway_client import disable_gateway_cron_jobs
        disable_gateway_cron_jobs()
    except Exception:
        pass

    print("[daemon] All daemons stopped. Start Docker, then: make daemons-start")


def run_daemon(args: list[str] | None = None) -> int:
    """Entry point for fleet daemon."""
    argv = args if args is not None else sys.argv[2:]

    if not argv:
        print("Usage: fleet daemon <sync|monitor|orchestrator|all> [--interval N]")
        return 1

    mode = argv[0]
    interval = 60
    sync_interval = 60
    monitor_interval = 300

    i = 1
    while i < len(argv):
        if argv[i] == "--interval" and i + 1 < len(argv):
            interval = int(argv[i + 1]); i += 2
        elif argv[i] == "--sync-interval" and i + 1 < len(argv):
            sync_interval = int(argv[i + 1]); i += 2
        elif argv[i] == "--monitor-interval" and i + 1 < len(argv):
            monitor_interval = int(argv[i + 1]); i += 2
        else:
            i += 1

    # SAFETY: refuse to start if fleet is paused
    fleet_dir = os.environ.get("FLEET_DIR", str(Path(__file__).resolve().parent.parent.parent))
    pause_file = os.path.join(fleet_dir, ".fleet-paused")
    if os.path.exists(pause_file):
        print("ERROR: Fleet is PAUSED. Cannot start daemon.")
        with open(pause_file) as f:
            print(f"  {f.read().strip()}")
        print("Run 'python -m fleet resume' first.")
        return 1

    # Write PID file
    pid_file = os.path.join(fleet_dir, f".{mode}.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    def cleanup(*_):
        # Disable gateway cron jobs on shutdown — fleet is going OFF.
        # This prevents the gateway from firing Claude heartbeats
        # after the daemon stops.
        try:
            from fleet.infra.gateway_client import disable_gateway_cron_jobs
            disabled = disable_gateway_cron_jobs()
            if disabled:
                print(f"[daemon] Shutdown: disabled {disabled} gateway cron jobs")
        except Exception:
            pass
        try:
            os.remove(pid_file)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    try:
        if mode == "sync":
            asyncio.run(_run_sync_daemon(interval))
        elif mode == "monitor":
            asyncio.run(_run_monitor_daemon(interval or monitor_interval))
        elif mode == "orchestrator":
            asyncio.run(run_orchestrator_daemon(interval or 30))
        elif mode == "all":
            asyncio.run(_run_all(sync_interval, monitor_interval))
        else:
            print(f"Unknown daemon mode: {mode}")
            return 1
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

    return 0