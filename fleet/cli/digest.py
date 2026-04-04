"""Fleet daily digest — summarize fleet activity.

Replaces: scripts/fleet-digest.sh
Usage: python -m fleet digest [--dry-run]
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

from fleet.infra.config_loader import ConfigLoader, resolve_vendor_config
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient
from fleet.templates.irc import format_digest_summary
from fleet.templates.memory import pr_tags


async def _run_digest(dry_run: bool = False) -> int:
    """Generate and post daily digest."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")

    if not token:
        print("ERROR: No LOCAL_AUTH_TOKEN")
        return 1

    mc = MCClient(token=token)
    board_id = await mc.get_board_id()

    if not board_id:
        print("ERROR: No board found")
        await mc.close()
        return 1

    # Gather data
    tasks = await mc.list_tasks(board_id)
    agents = await mc.list_agents()
    approvals = await mc.list_approvals(board_id)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    # Count by status
    counts: dict[str, int] = {}
    for t in tasks:
        s = t.status.value
        counts[s] = counts.get(s, 0) + 1

    # Active work
    active = [t for t in tasks if t.status.value == "in_progress"]
    review = [t for t in tasks if t.status.value == "review"]
    pending_approvals = [a for a in approvals if a.status == "pending"]

    # Agent health
    non_gw = [a for a in agents if "Gateway" not in a.name]
    online = sum(1 for a in non_gw if a.status == "online")

    # Build digest
    lines = [
        f"## 📊 Fleet Daily Digest — {date_str}\n",
        f"### Board Status\n",
        f"| Status | Count |",
        f"|--------|-------|",
    ]
    for status in ["inbox", "in_progress", "review", "done"]:
        count = counts.get(status, 0)
        if count > 0:
            emoji = {"inbox": "📥", "in_progress": "🔵", "review": "🟡", "done": "✅"}.get(status, "")
            lines.append(f"| {emoji} {status} | {count} |")

    if active:
        lines.append(f"\n### Active Work ({len(active)})\n")
        for t in active:
            lines.append(f"- {t.title[:60]}")

    if review:
        lines.append(f"\n### Pending Review ({len(review)})\n")
        for t in review:
            pr = f" — [{t.custom_fields.pr_url}]({t.custom_fields.pr_url})" if t.custom_fields.pr_url else ""
            lines.append(f"- {t.title[:50]}{pr}")

    if pending_approvals:
        lines.append(f"\n### Pending Approvals ({len(pending_approvals)})\n")
        for a in pending_approvals:
            lines.append(f"- ⏳ {a.action_type} (confidence: {a.confidence:.0f}%) — task `{a.task_id[:8]}`")

    lines.append(f"\n### Health\n")
    lines.append(f"- Agents: {online}/{len(non_gw)} online")
    lines.append(f"\n---\n<sub>fleet-ops · {now.strftime('%Y-%m-%d %H:%M UTC')}</sub>")

    digest = "\n".join(lines)

    if dry_run:
        print(digest)
        await mc.close()
        return 0

    # Post to board memory
    await mc.post_memory(
        board_id,
        content=digest,
        tags=["report", "digest", "daily"],
        source="fleet-ops",
    )

    # Post summary to IRC
    import json
    oc_path = resolve_vendor_config()
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    irc = IRCClient(gateway_token=gateway_token)
    tasks_done = counts.get("done", 0)
    irc_msg = format_digest_summary(
        tasks_done=tasks_done, prs_merged=0,
        review_count=len(review),
        agents_online=online, agents_total=len(non_gw),
    )
    try:
        await irc.notify("#fleet", irc_msg)
    except Exception:
        pass

    print(f"Digest posted for {date_str}")
    await mc.close()
    return 0


def run_digest(args: list[str] | None = None) -> int:
    """Entry point for fleet digest."""
    dry_run = "--dry-run" in (args or sys.argv[2:])
    return asyncio.run(_run_digest(dry_run))