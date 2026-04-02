"""Fleet task dispatch — send tasks to agents via OpenClaw gateway.

Replaces: scripts/dispatch-task.sh
Usage: python -m fleet dispatch <agent> <task-id> [--project <name>]
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import websockets

from fleet.infra.config_loader import ConfigLoader
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient
from fleet.templates.irc import format_event


async def _run_dispatch(
    agent_name: str,
    task_id: str,
    project_name: str = "",
    backend_mode: str = "claude",
) -> int:
    """Dispatch a task to an agent."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")
    fleet_dir = str(loader.fleet_dir)

    if not token:
        print("ERROR: No LOCAL_AUTH_TOKEN")
        return 1

    mc = MCClient(token=token)

    # Refresh auth token if rotated
    _refresh_auth(loader)

    # Resolve agent info
    agents = await mc.list_agents()
    agent = next((a for a in agents if a.name == agent_name), None)
    if not agent:
        print(f"ERROR: Agent '{agent_name}' not found")
        await mc.close()
        return 1

    board_id = agent.board_id or await mc.get_board_id()
    session_key = agent.session_key or ""

    if not session_key:
        print(f"ERROR: Agent '{agent_name}' has no session key")
        await mc.close()
        return 1

    # Fetch task
    try:
        task = await mc.get_task(board_id, task_id)
    except Exception:
        print(f"ERROR: Task '{task_id}' not found")
        await mc.close()
        return 1

    print(f"Agent:    {agent_name}")
    print(f"Task:     {task.title}")
    print(f"Priority: {task.priority}")

    # Setup project worktree if requested
    work_dir = ""
    if project_name:
        print(f"Project:  {project_name}")
        work_dir = await _setup_worktree(fleet_dir, project_name, agent_name, task_id)
        if work_dir:
            print(f"Worktree: {work_dir}")

    # Update task custom fields with agent context
    custom_fields = {"agent_name": agent_name}
    if work_dir:
        custom_fields["worktree"] = work_dir
    try:
        await mc.update_task(board_id, task_id, custom_fields=custom_fields)
    except Exception:
        pass

    # Route to backend based on backend_mode setting from OCMC
    from fleet.core.backend_router import route_task
    from fleet.core.model_selection import select_model_for_task
    from fleet.core.labor_stamp import DispatchRecord

    routing = route_task(task, agent_name, backend_mode=backend_mode)
    print(f"Backend:  {routing.backend} (tier={routing.confidence_tier})")
    print(f"Model:    {routing.model} (effort={routing.effort})")
    print(f"          {routing.reason}")

    # Record dispatch intent — the provenance chain starts here
    dispatch_record = DispatchRecord(
        task_id=task_id,
        agent_name=agent_name,
        backend=routing.backend,
        model=routing.model,
        effort=routing.effort,
        selection_reason=routing.reason,
        skills=[],  # Populated when skill system is integrated
    )

    # Persist dispatch record for fleet_task_complete to read later
    _save_dispatch_record(fleet_dir, task_id, dispatch_record)

    # Update .mcp.json with task context
    _update_mcp_json(fleet_dir, agent, task_id, project_name, work_dir)

    # Update agent workspace settings with model and effort for this task
    _update_agent_settings(fleet_dir, agent, model_config)

    # Build dispatch message
    message = _build_message(task, task_id, board_id, project_name, work_dir, agent_name)

    # Send via gateway
    print("\nDispatching...")
    ok, run_id = await _send_chat(session_key, message)

    if ok:
        print(f"Dispatched: runId={run_id}")
    else:
        print(f"ERROR: Dispatch failed")
        await mc.close()
        return 1

    # Notify IRC
    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    irc = IRCClient(gateway_token=gateway_token)
    try:
        await irc.notify(
            "#fleet",
            format_event(agent_name, "🚀 DISPATCHED", task.title),
        )
    except Exception:
        pass

    await mc.close()
    return 0


def _refresh_auth(loader: ConfigLoader) -> None:
    """Refresh auth token if Claude Code rotated it."""
    creds_path = Path.home() / ".claude" / ".credentials.json"
    oc_env_path = Path.home() / ".openclaw" / ".env"

    if not creds_path.exists():
        return

    try:
        with open(creds_path) as f:
            creds = json.load(f)
        new_token = creds.get("claudeAiOauth", {}).get("accessToken", "")
        if not new_token:
            return

        current_token = ""
        if oc_env_path.exists():
            for line in oc_env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    current_token = line.split("=", 1)[1]

        if new_token != current_token:
            lines = []
            if oc_env_path.exists():
                lines = [
                    l for l in oc_env_path.read_text().splitlines()
                    if not l.startswith("ANTHROPIC_API_KEY")
                ]
            lines.append(f"ANTHROPIC_API_KEY={new_token}")
            oc_env_path.write_text("\n".join(lines) + "\n")
    except Exception:
        pass


def _save_dispatch_record(
    fleet_dir: str, task_id: str, record: "DispatchRecord",
) -> None:
    """Persist dispatch record so fleet_task_complete can read it later.

    Saved as JSON in fleet_dir/state/dispatch_records/<task_short>.json.
    The stamp assembly step reads this at completion time.
    """
    state_dir = os.path.join(fleet_dir, "state", "dispatch_records")
    os.makedirs(state_dir, exist_ok=True)
    record_path = os.path.join(state_dir, f"{task_id[:8]}.json")
    try:
        with open(record_path, "w") as f:
            json.dump(record.to_dict(), f, indent=2)
    except Exception as e:
        print(f"WARNING: Could not save dispatch record: {e}")


def _load_dispatch_record(fleet_dir: str, task_id: str) -> dict | None:
    """Load a previously saved dispatch record."""
    record_path = os.path.join(
        fleet_dir, "state", "dispatch_records", f"{task_id[:8]}.json",
    )
    try:
        with open(record_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


async def _setup_worktree(
    fleet_dir: str, project: str, agent: str, task_id: str
) -> str:
    """Create a git worktree for the task."""
    from fleet.infra.gh_client import GHClient
    gh = GHClient()

    projects_dir = os.path.join(fleet_dir, "projects")
    project_path = os.path.join(projects_dir, project)
    short = task_id[:8]

    if not os.path.isdir(project_path):
        # Clone project
        loader = ConfigLoader(fleet_dir)
        projects = loader.load_projects()
        proj = projects.get(project)
        if not proj or proj.local:
            return ""

        os.makedirs(projects_dir, exist_ok=True)
        repo_url = f"https://github.com/{proj.owner}/{proj.repo}"
        ok, _ = await gh._run(["git", "clone", repo_url, project_path])
        if not ok:
            return ""

    wt_path = os.path.join(project_path, "worktrees", f"{agent}-{short}")
    if os.path.isdir(wt_path):
        return wt_path

    # Get default branch
    ok, default_branch = await gh._run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=project_path,
    )
    default_branch = default_branch.strip().replace("refs/remotes/origin/", "") if ok else "main"

    # Fetch and create worktree
    await gh._run(["git", "fetch", "origin", default_branch], cwd=project_path)
    branch = f"fleet/{agent}/{short}"
    ok, output = await gh._run(
        ["git", "worktree", "add", "-b", branch, wt_path, f"origin/{default_branch}"],
        cwd=project_path,
    )

    return wt_path if ok else ""


def _update_mcp_json(
    fleet_dir: str, agent, task_id: str, project: str, worktree: str
) -> None:
    """Update .mcp.json in agent workspace with task context."""
    if not agent.id:
        return
    workspace = os.path.join(fleet_dir, f"workspace-mc-{agent.id}")
    mcp_path = os.path.join(workspace, ".mcp.json")
    if not os.path.isfile(mcp_path):
        return

    try:
        with open(mcp_path) as f:
            cfg = json.load(f)
        env = cfg.get("mcpServers", {}).get("fleet", {}).get("env", {})
        env["FLEET_TASK_ID"] = task_id
        env["FLEET_PROJECT"] = project
        if worktree:
            env["FLEET_WORKTREE"] = worktree
        with open(mcp_path, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def _update_agent_settings(fleet_dir: str, agent, model_config) -> None:
    """Update agent workspace .claude/settings.json with task-specific model and effort."""
    if not agent.id:
        return
    workspace = os.path.join(fleet_dir, f"workspace-mc-{agent.id}")
    settings_path = os.path.join(workspace, ".claude", "settings.json")

    try:
        if os.path.isfile(settings_path):
            with open(settings_path) as f:
                settings = json.load(f)
        else:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            settings = {}

        settings["effortLevel"] = model_config.effort
        # Note: model is set via ANTHROPIC_MODEL env var in gateway, not settings.json
        # But we record it for reference
        settings["_taskModel"] = model_config.model
        settings["_taskModelReason"] = model_config.reason

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def _build_message(task, task_id, board_id, project, work_dir, agent_name) -> str:
    """Build the dispatch message."""
    lines = [
        "NEW TASK ASSIGNMENT",
        "",
        f"Task ID: {task_id}",
        f"Board ID: {board_id}",
        f"Title: {task.title}",
        f"Priority: {task.priority}",
    ]

    if work_dir:
        lines.extend([
            f"Project: {project}",
            f"Working Directory: {work_dir}",
            "",
            f"IMPORTANT: Do your work in {work_dir} (git worktree with project code).",
            f"Branch: fleet/{agent_name}/{task_id[:8]}",
        ])

    lines.extend([
        "",
        "Description:",
        task.description or "(no description)",
        "",
        f'FIRST: Call fleet_read_context(task_id="{task_id}", project="{project}") to load your context.',
        "Then follow the fleet tool workflow in your SOUL.md.",
    ])

    return "\n".join(lines)


async def _send_chat(session_key: str, message: str) -> tuple[bool, str]:
    """Send message via gateway chat.send."""
    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    with open(oc_path) as f:
        cfg = json.load(f)
    oc_token = cfg.get("gateway", {}).get("auth", {}).get("token", "")

    try:
        async with websockets.connect(
            "ws://localhost:18789",
            origin="http://localhost:18789",
        ) as ws:
            await asyncio.wait_for(ws.recv(), timeout=5)
            await ws.send(json.dumps({
                "type": "req",
                "id": str(uuid.uuid4()),
                "method": "connect",
                "params": {
                    "minProtocol": 3,
                    "maxProtocol": 3,
                    "role": "operator",
                    "scopes": ["operator.read", "operator.admin",
                               "operator.approvals", "operator.pairing"],
                    "client": {
                        "id": "openclaw-control-ui",
                        "version": "1.0.0",
                        "platform": "python",
                        "mode": "ui",
                    },
                    "auth": {"token": oc_token},
                },
            }))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            if not json.loads(raw).get("ok"):
                return False, ""

            req_id = str(uuid.uuid4())
            await ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": "chat.send",
                "params": {
                    "sessionKey": session_key,
                    "message": message,
                    "deliver": False,
                    "idempotencyKey": str(uuid.uuid4()),
                },
            }))

            while True:
                data = json.loads(
                    await asyncio.wait_for(ws.recv(), timeout=30)
                )
                if data.get("id") == req_id:
                    if data.get("ok"):
                        run_id = data.get("payload", {}).get("runId", "")
                        return True, run_id
                    return False, ""

    except Exception:
        return False, ""


def run_dispatch(args: list[str] | None = None) -> int:
    """Entry point for fleet dispatch."""
    argv = args if args is not None else sys.argv[2:]

    agent_name = ""
    task_id = ""
    project = ""

    i = 0
    while i < len(argv):
        if argv[i] == "--project" and i + 1 < len(argv):
            project = argv[i + 1]
            i += 2
        elif not agent_name:
            agent_name = argv[i]
            i += 1
        elif not task_id:
            task_id = argv[i]
            i += 1
        else:
            i += 1

    if not agent_name or not task_id:
        print("Usage: fleet dispatch <agent> <task-id> [--project <name>]")
        return 1

    return asyncio.run(_run_dispatch(agent_name, task_id, project))