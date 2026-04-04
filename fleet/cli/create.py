"""Fleet task creation — create and optionally dispatch tasks.

Replaces: scripts/create-task.sh
Usage: python -m fleet create "title" [options]
"""

from __future__ import annotations

import asyncio
import os
import sys

from fleet.infra.config_loader import ConfigLoader, resolve_vendor_config
from fleet.infra.mc_client import MCClient
from fleet.templates.irc import format_event


async def _run_create(
    title: str,
    agent_name: str = "",
    project: str = "",
    description: str = "",
    priority: str = "medium",
    dispatch: bool = False,
) -> int:
    """Create a task and optionally dispatch it."""
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

    # Resolve agent ID
    agent_id = ""
    if agent_name:
        agents = await mc.list_agents()
        agent = next((a for a in agents if a.name == agent_name), None)
        if not agent:
            print(f"ERROR: Agent '{agent_name}' not found")
            await mc.close()
            return 1
        agent_id = agent.id

    # Resolve project tag
    tag_ids: list[str] = []
    if project:
        import urllib.request
        import json
        req = urllib.request.Request(
            f"http://localhost:8000/api/v1/tags"
        )
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                tags_data = json.loads(resp.read())
                items = tags_data.get("items", tags_data) if isinstance(tags_data, dict) else tags_data
                for t in items:
                    if t.get("name") == f"project:{project}":
                        tag_ids.append(str(t["id"]))
                        break
        except Exception:
            pass

    # Build custom fields
    custom_fields = {}
    if project:
        custom_fields["project"] = project
    if agent_name:
        custom_fields["agent_name"] = agent_name

    # Create task
    task = await mc.create_task(
        board_id,
        title=title,
        description=description,
        priority=priority,
        assigned_agent_id=agent_id or None,
        custom_fields=custom_fields if custom_fields else None,
        tag_ids=tag_ids if tag_ids else None,
    )

    print(f"Created: {task.id}")
    print(f"Title:   {task.title}")
    if agent_name:
        print(f"Agent:   {agent_name}")
    if project:
        print(f"Project: {project}")

    # Notify IRC
    import json as json_mod
    oc_path = resolve_vendor_config()
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json_mod.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    from fleet.infra.irc_client import IRCClient
    irc = IRCClient(gateway_token=gateway_token)
    try:
        await irc.notify(
            "#fleet",
            format_event(agent_name or "human", "📋 TASK CREATED", title),
        )
    except Exception:
        pass

    # Dispatch if requested
    if dispatch and agent_name:
        print()
        from fleet.cli.dispatch import _run_dispatch
        result = await _run_dispatch(agent_name, task.id, project)
        await mc.close()
        return result

    await mc.close()
    return 0


def run_create(args: list[str] | None = None) -> int:
    """Entry point for fleet create."""
    argv = args if args is not None else sys.argv[2:]

    title = ""
    agent = ""
    project = ""
    description = ""
    priority = "medium"
    dispatch = False

    i = 0
    while i < len(argv):
        if argv[i] == "--agent" and i + 1 < len(argv):
            agent = argv[i + 1]; i += 2
        elif argv[i] == "--project" and i + 1 < len(argv):
            project = argv[i + 1]; i += 2
        elif argv[i] == "--desc" and i + 1 < len(argv):
            description = argv[i + 1]; i += 2
        elif argv[i] == "--priority" and i + 1 < len(argv):
            priority = argv[i + 1]; i += 2
        elif argv[i] == "--dispatch":
            dispatch = True; i += 1
        elif not title:
            title = argv[i]; i += 1
        else:
            title = f"{title} {argv[i]}"; i += 1

    if not title:
        print("Usage: fleet create \"title\" [--agent X] [--project Y] [--desc Z] [--dispatch]")
        return 1

    return asyncio.run(_run_create(title, agent, project, description, priority, dispatch))