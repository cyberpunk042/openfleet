"""Fleet IRC notify — send messages to IRC channels.

Replaces: scripts/notify-irc.sh
Usage: python -m fleet notify "message"
       python -m fleet notify --agent sw-eng --event "PR READY" --title "Fix" --url "..."
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from fleet.infra.irc_client import IRCClient
from fleet.templates.irc import format_event


async def _run_notify(args: list[str]) -> int:
    """Send an IRC notification."""
    # Load gateway token
    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    irc = IRCClient(gateway_token=gateway_token)

    # Parse args
    agent = ""
    event = ""
    title = ""
    url = ""
    channel = "#fleet"
    plain = ""

    i = 0
    while i < len(args):
        if args[i] == "--agent" and i + 1 < len(args):
            agent = args[i + 1]; i += 2
        elif args[i] == "--event" and i + 1 < len(args):
            event = args[i + 1]; i += 2
        elif args[i] == "--title" and i + 1 < len(args):
            title = args[i + 1]; i += 2
        elif args[i] == "--url" and i + 1 < len(args):
            url = args[i + 1]; i += 2
        elif args[i] == "--channel" and i + 1 < len(args):
            channel = args[i + 1]; i += 2
        else:
            plain = f"{plain} {args[i]}".strip() if plain else args[i]
            i += 1

    if event and agent:
        msg = format_event(agent, event, title, url)
    elif plain:
        msg = plain
    else:
        print("Usage: fleet notify 'message' or --agent X --event Y --title Z --url U")
        return 1

    ok = await irc.notify(channel, msg)
    if ok:
        print(f"Sent to {channel}")
        return 0
    else:
        print("Send failed")
        return 1


def run_notify(args: list[str] | None = None) -> int:
    """Entry point for fleet notify."""
    return asyncio.run(_run_notify(args or sys.argv[2:]))