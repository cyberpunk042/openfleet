"""Fleet task trace — full context for any task.

Replaces: scripts/trace-task.sh
Usage: python -m fleet trace <task-id>
"""

from __future__ import annotations

import asyncio
import os
import sys

from fleet.infra.config_loader import ConfigLoader
from fleet.infra.gh_client import GHClient
from fleet.infra.mc_client import MCClient

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"
NC = "\033[0m"


async def _run_trace(task_id: str) -> int:
    """Trace a task — show everything about it."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")
    fleet_dir = str(loader.fleet_dir)

    if not token:
        print("ERROR: No LOCAL_AUTH_TOKEN")
        return 1

    mc = MCClient(token=token)
    gh = GHClient()
    short = task_id[:8]

    print(f"{BOLD}=== Task Trace: {short} ==={NC}\n")

    # Task details
    board_id = await mc.get_board_id()
    if not board_id:
        print("ERROR: No board found")
        await mc.close()
        return 1

    print(f"{BOLD}Task{NC}")
    try:
        task = await mc.get_task(board_id, task_id)
        print(f"  Title:    {task.title}")
        print(f"  Status:   {task.status.value}")
        print(f"  Priority: {task.priority}")
        print(f"  Project:  {task.custom_fields.project or '(none)'}")
        print(f"  Branch:   {task.custom_fields.branch or '(none)'}")
        if task.custom_fields.pr_url:
            print(f"  PR:       {task.custom_fields.pr_url}")
        if task.description:
            print(f"  Desc:     {task.description[:200]}")
    except Exception as e:
        print(f"  {RED}Not found: {e}{NC}")
        await mc.close()
        return 1

    # Activity
    print(f"\n{BOLD}Activity{NC}")
    import urllib.request
    import json
    try:
        req = urllib.request.Request(
            f"http://localhost:8000/api/v1/activity?limit=50"
        )
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            events = json.loads(resp.read()).get("items", [])

        task_events = [
            e for e in events
            if short in str(e.get("message", ""))
            or task_id in str(e.get("task_id", ""))
        ]
        for e in task_events:
            ts = e.get("created_at", "")[:19].replace("T", " ")
            evt = e.get("event_type", "")
            msg = str(e.get("message", ""))
            print(f"  {DIM}{ts}{NC}  {evt}")
            for line in msg.split("\n")[:3]:
                print(f"    {line[:120]}")
        if not task_events:
            print(f"  {DIM}(no activity){NC}")
    except Exception:
        print(f"  {DIM}(could not fetch activity){NC}")

    # Approvals
    print(f"\n{BOLD}Approvals{NC}")
    try:
        approvals = await mc.list_approvals(board_id)
        task_approvals = [a for a in approvals if a.task_id == task_id]
        if task_approvals:
            for a in task_approvals:
                color = GREEN if a.status == "approved" else YELLOW if a.status == "pending" else RED
                print(f"  {color}{a.status}{NC}  confidence={a.confidence:.0f}%  {a.action_type}")
                if a.reason:
                    print(f"    {DIM}{a.reason[:120]}{NC}")
        else:
            print(f"  {DIM}(none){NC}")
    except Exception:
        print(f"  {DIM}(could not fetch){NC}")

    # Worktree
    print(f"\n{BOLD}Worktree{NC}")
    wt_path = _find_worktree(fleet_dir, short)
    if wt_path:
        _, branch = await gh._run(["git", "branch", "--show-current"], cwd=wt_path)
        print(f"  Path:   {wt_path}")
        print(f"  Branch: {branch.strip()}")

        commits = await gh.get_branch_commits(wt_path)
        if commits:
            print(f"\n  {BOLD}Commits ({len(commits)}){NC}")
            for c in commits:
                parsed = gh.parse_commit(c["sha"], c["message"])
                print(f"    {CYAN}{parsed.short_sha}{NC} {c['message'][:80]}")

        diff = await gh.get_diff_stat(wt_path)
        if diff:
            print(f"\n  {BOLD}Files Changed ({len(diff)}){NC}")
            for f in diff:
                print(f"    {f['path']} +{f['added']}/-{f['removed']}")

        # Check if pushed
        _, remote = await gh._run(
            ["git", "branch", "-r"], cwd=wt_path
        )
        if short in remote:
            print(f"\n  {GREEN}Pushed to remote{NC}")
        else:
            print(f"\n  {YELLOW}Not pushed{NC}")
    else:
        print(f"  {DIM}(no worktree for {short}){NC}")

    # PR state
    if task.custom_fields.pr_url:
        print(f"\n{BOLD}Pull Request{NC}")
        pr_state = await gh.get_pr_state(task.custom_fields.pr_url)
        color = GREEN if pr_state == "MERGED" else YELLOW if pr_state == "OPEN" else RED
        print(f"  URL:   {task.custom_fields.pr_url}")
        print(f"  State: {color}{pr_state}{NC}")

    # Board memory
    print(f"\n{BOLD}Board Memory{NC}")
    try:
        memory = await mc.list_memory(board_id, limit=20)
        matches = [m for m in memory if short in m.content or task_id in m.content]
        if matches:
            for m in matches:
                print(f"  {DIM}{m.source}{NC} tags={m.tags}")
                print(f"    {m.content[:200]}")
        else:
            print(f"  {DIM}(no entries reference this task){NC}")
    except Exception:
        pass

    await mc.close()
    return 0


def _find_worktree(fleet_dir: str, short: str) -> str | None:
    """Find worktree by task short ID."""
    projects_dir = os.path.join(fleet_dir, "projects")
    if not os.path.isdir(projects_dir):
        return None
    for project in os.listdir(projects_dir):
        wt_dir = os.path.join(projects_dir, project, "worktrees")
        if not os.path.isdir(wt_dir):
            continue
        for wt in os.listdir(wt_dir):
            if wt.endswith(f"-{short}"):
                return os.path.join(wt_dir, wt)
    return None


def run_trace(args: list[str] | None = None) -> int:
    """Entry point for fleet trace."""
    argv = args if args is not None else sys.argv[2:]
    if not argv:
        print("Usage: fleet trace <task-id>")
        return 1
    return asyncio.run(_run_trace(argv[0]))