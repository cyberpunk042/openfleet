"""Fleet status — comprehensive fleet overview.

Replaces: scripts/fleet-status.sh
Usage: python -m fleet status
"""

from __future__ import annotations

import asyncio
import sys

from fleet.infra.config_loader import ConfigLoader
from fleet.infra.mc_client import MCClient


BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
NC = "\033[0m"


async def _run_status() -> int:
    """Execute fleet status check."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")

    if not token:
        print(f"{RED}No LOCAL_AUTH_TOKEN in .env{NC}")
        return 1

    client = MCClient(token=token)

    print(f"{BOLD}╔══════════════════════════════════════╗{NC}")
    print(f"{BOLD}║     OpenClaw Fleet Status            ║{NC}")
    print(f"{BOLD}╚══════════════════════════════════════╝{NC}")

    # Infrastructure
    print(f"\n{BOLD}Infrastructure{NC}")
    import httpx
    for name, url in [
        ("Gateway", "http://localhost:18789"),
        ("MC Backend", "http://localhost:8000/health"),
        ("MC Frontend", "http://localhost:3000"),
        ("The Lounge", "http://localhost:9000"),
    ]:
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(url, timeout=3)
                status = f"{GREEN}UP{NC}" if resp.status_code < 400 else f"{RED}DOWN{NC}"
        except Exception:
            status = f"{RED}DOWN{NC}"
        print(f"  {name:20s} {status}")

    # Check IRC
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("localhost", 6667))
        s.close()
        print(f"  {'IRC':20s} {GREEN}UP{NC}")
    except Exception:
        print(f"  {'IRC':20s} {RED}DOWN{NC}")

    # Agents
    print(f"\n{BOLD}Agents{NC}")
    try:
        agents = await client.list_agents()
        for a in agents:
            if "Gateway" in a.name:
                continue
            color = GREEN if a.status == "online" else RED if a.status == "offline" else YELLOW
            print(f"  {a.name:25s} {color}{a.status}{NC}")
        non_gw = [a for a in agents if "Gateway" not in a.name]
        print(f"  {DIM}Total: {len(non_gw)} agents{NC}")
    except Exception as e:
        print(f"  {RED}Error: {e}{NC}")

    # Tasks
    print(f"\n{BOLD}Tasks{NC}")
    try:
        board_id = await client.get_board_id()
        if board_id:
            tasks = await client.list_tasks(board_id)
            status_colors = {
                "inbox": YELLOW, "in_progress": CYAN,
                "review": MAGENTA, "done": GREEN,
            }
            counts: dict[str, int] = {}
            for t in tasks:
                s = t.status.value
                counts[s] = counts.get(s, 0) + 1
                color = status_colors.get(s, NC)
                pr = ""
                if t.custom_fields.pr_url:
                    pr = f" → {DIM}{t.custom_fields.pr_url}{NC}"
                print(f"  {color}{s:15s}{NC} {t.title[:50]}{pr}")

            summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
            print(f"\n  {DIM}Summary: {summary} ({len(tasks)} total){NC}")
    except Exception as e:
        print(f"  {RED}Error: {e}{NC}")

    # Recent activity
    print(f"\n{BOLD}Recent Activity{NC}")
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://localhost:8000/api/v1/activity?limit=5"
        )
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json
            data = json.loads(resp.read())
            for e in data.get("items", []):
                ts = e.get("created_at", "")[:19].replace("T", " ")
                evt = e.get("event_type", "")
                msg = str(e.get("message", ""))[:80]
                print(f"  {DIM}{ts}{NC}  {evt:25s} {msg}")
    except Exception:
        pass

    await client.close()
    return 0


def run_status() -> int:
    """Entry point for fleet status."""
    return asyncio.run(_run_status())


if __name__ == "__main__":
    sys.exit(run_status())