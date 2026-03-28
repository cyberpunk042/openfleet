"""Fleet sync — keeps MC tasks and GitHub PRs in sync.

Replaces: scripts/fleet-sync.sh
Usage: python -m fleet sync
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys

from fleet.infra.config_loader import ConfigLoader
from fleet.infra.gh_client import GHClient
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient
from fleet.templates.irc import format_merged, format_task_done


async def _run_sync() -> int:
    """Execute one sync pass."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")

    if not token:
        print("ERROR: No LOCAL_AUTH_TOKEN")
        return 1

    mc = MCClient(token=token)
    gh = GHClient()

    # Load IRC client
    import json
    gateway_token = ""
    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")
    irc = IRCClient(gateway_token=gateway_token)

    board_id = await mc.get_board_id()
    if not board_id:
        print("ERROR: No board found")
        await mc.close()
        return 1

    tasks = await mc.list_tasks(board_id)
    actions = 0

    for task in tasks:
        pr_url = task.custom_fields.pr_url
        if not pr_url:
            continue

        pr_state = await gh.get_pr_state(pr_url)

        # Task done + PR open → merge
        if task.status.value == "done" and pr_state == "OPEN":
            print(f"  MERGE: {task.title[:50]} — {pr_url}")
            ok = await gh.merge_pr(pr_url)
            if ok:
                await mc.post_comment(
                    board_id, task.id, f"**Auto-merged** PR: {pr_url}"
                )
                await mc.post_memory(
                    board_id,
                    content=f"**Merged**: {task.title}\nPR: {pr_url}",
                    tags=["merged", f"project:{task.custom_fields.project or 'fleet'}"],
                    source="fleet-sync",
                )
                try:
                    await irc.notify("#fleet", format_merged(task.title, pr_url))
                except Exception:
                    pass
                actions += 1
            else:
                print(f"    FAIL: merge failed")

        # Task review + PR merged → close task
        elif task.status.value == "review" and pr_state == "MERGED":
            print(f"  DONE: {task.title[:50]} — PR merged")
            await mc.update_task(
                board_id, task.id,
                status="done",
                comment=f"**Auto-closed** — PR was merged: {pr_url}",
            )
            await mc.post_memory(
                board_id,
                content=f"**Completed**: {task.title}\nPR: {pr_url} (merged)",
                tags=["completed", f"project:{task.custom_fields.project or 'fleet'}"],
                source="fleet-sync",
            )
            try:
                await irc.notify("#fleet", format_task_done(task.title))
            except Exception:
                pass
            actions += 1

        # Task done → cleanup worktree
        if task.status.value == "done":
            wt = _find_worktree(task.id)
            if wt and os.path.isdir(wt):
                print(f"  CLEANUP: {os.path.basename(wt)}")
                project_dir = os.path.dirname(os.path.dirname(wt))
                ok, _ = await gh._run(
                    ["git", "worktree", "remove", wt, "--force"],
                    cwd=project_dir,
                )
                if ok:
                    actions += 1

    if actions == 0:
        print("  Nothing to sync")
    else:
        print(f"\n  {actions} actions taken")

    await mc.close()
    return 0


def _find_worktree(task_id: str) -> str | None:
    """Find worktree for a task by ID prefix."""
    fleet_dir = os.environ.get("FLEET_DIR", ".")
    short = task_id[:8]
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


def run_sync() -> int:
    """Entry point for fleet sync."""
    return asyncio.run(_run_sync())


if __name__ == "__main__":
    sys.exit(run_sync())