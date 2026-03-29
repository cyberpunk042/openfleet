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

# Event emission for the event bus
def _sync_emit_event(event_type, **kwargs):
    try:
        from fleet.core.events import create_event, EventStore
        store = EventStore()
        event = create_event(event_type, source="fleet/cli/sync", **kwargs)
        store.append(event)
    except Exception:
        pass


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
                # NOTE: No board memory post — merge notifications go to IRC/ntfy only.
                # Board memory is reserved for decisions, alerts, knowledge, chat.
                try:
                    await irc.notify("#fleet", format_merged(task.title, pr_url))
                except Exception:
                    pass
                # ntfy notification on PR merge
                try:
                    from fleet.infra.ntfy_client import NtfyClient
                    ntfy = NtfyClient()
                    await ntfy.publish(
                        title=f"PR merged: {task.title[:40]}",
                        message=f"PR: {pr_url}",
                        priority="info",
                        tags=["rocket", "merged"],
                        click_url=pr_url,
                    )
                    await ntfy.close()
                except Exception:
                    pass
                _sync_emit_event(
                    "fleet.github.pr_merged",
                    subject=task.id,
                    recipient=task.custom_fields.agent_name or "all",
                    priority="info",
                    tags=["merged", f"project:{task.custom_fields.project or 'unknown'}"],
                    surfaces=["internal", "channel", "notify"],
                    pr_url=pr_url,
                    task_title=task.title[:60],
                )
                actions += 1
            else:
                print(f"    FAIL: merge failed")

        # Task review + PR merged by human → create approval + close task
        elif task.status.value == "review" and pr_state == "MERGED":
            # Human merged on GitHub — create approval so MC allows done transition
            try:
                await mc.create_approval(
                    board_id,
                    task_ids=[task.id],
                    action_type="task_completion",
                    confidence=100.0,
                    rubric_scores={"human_merged": 100},
                    reason="PR merged by human on GitHub.",
                )
            except Exception:
                pass  # Approval may already exist

            try:
                await mc.update_task(
                    board_id, task.id,
                    status="done",
                    comment=f"**Human merged** PR on GitHub: {pr_url}",
                )
                print(f"  DONE: {task.title[:50]} — human merged PR")
                _sync_emit_event(
                    "fleet.github.pr_merged",
                    subject=task.id,
                    recipient=task.custom_fields.agent_name or "all",
                    priority="important",
                    mentions=[task.custom_fields.agent_name] if task.custom_fields.agent_name else [],
                    tags=["merged", "human_action"],
                    surfaces=["internal", "channel"],
                    pr_url=pr_url,
                    human_merged=True,
                )
                # No board memory — IRC/ntfy only for operational events
                try:
                    await irc.notify("#fleet", format_task_done(task.title))
                except Exception:
                    pass
                actions += 1
            except Exception:
                print(f"  PENDING: {task.title[:50]} — PR merged, awaiting approval")

        # Task in review/in_progress + PR closed without merging → human rejected
        elif pr_state == "CLOSED" and task.status.value in ("review", "in_progress"):
            print(f"  CLOSED: {task.title[:50]} — human closed PR")
            try:
                await mc.update_task(
                    board_id, task.id,
                    status="inbox",
                    comment=(
                        f"**PR closed by human** without merging: {pr_url}\n\n"
                        f"The human may want this reworked or abandoned. "
                        f"Check board memory or IRC for direction."
                    ),
                )
                # No board memory — PR close goes to IRC/ntfy only
                try:
                    await irc.notify("#fleet",
                        f"[fleet] \u274c PR CLOSED: {task.title[:40]} — human closed {pr_url}")
                except Exception:
                    pass

                # Notify human via ntfy
                try:
                    from fleet.infra.ntfy_client import NtfyClient
                    ntfy = NtfyClient()
                    await ntfy.publish(
                        title=f"PR closed: {task.title[:40]}",
                        message=f"You closed PR {pr_url}. Task moved to inbox.",
                        priority="info",
                        tags=["x", "pr-closed"],
                    )
                    await ntfy.close()
                except Exception:
                    pass

                actions += 1
            except Exception as e:
                print(f"  ERROR closing task: {e}")

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

    # PR comment detection — check active PRs for new human comments
    await _check_pr_comments(mc, gh, irc, board_id, tasks)

    # PR hygiene check — detect conflicts, stale PRs, orphaned PRs
    await _check_pr_hygiene(mc, gh, irc, board_id, tasks, actions)

    # Budget status log (from real OAuth API)
    try:
        from fleet.core.budget_monitor import BudgetMonitor
        bm = BudgetMonitor()
        bm.check_quota()
        status = bm.format_status()
        if "PAUSE" in status:
            print(f"  {status}")
    except Exception:
        pass

    if actions == 0:
        print("  Nothing to sync")
    else:
        print(f"\n  {actions} actions taken")

    await mc.close()
    return 0


_pr_comment_counts: dict[str, int] = {}  # PR URL → last known comment count


async def _check_pr_comments(mc, gh, irc, board_id, tasks) -> None:
    """Check active task PRs for new human comments."""
    from fleet.core.remote_watcher import classify_human_comment

    active_prs = [
        t for t in tasks
        if t.status.value in ("in_progress", "review")
        and t.custom_fields.pr_url
    ]

    for task in active_prs[:5]:  # Max 5 per cycle (rate limit)
        pr_url = task.custom_fields.pr_url
        try:
            import json as _json
            ok, output = await gh._run([
                "gh", "pr", "view", pr_url, "--json", "comments",
            ])
            if not ok:
                continue

            data = _json.loads(output)
            comments = data.get("comments", [])
            current_count = len(comments)
            prev_count = _pr_comment_counts.get(pr_url, current_count)

            if current_count > prev_count:
                new_comments = comments[prev_count:]
                for c in new_comments:
                    body = c.get("body", "")
                    author = c.get("author", {}).get("login", "human")
                    if author in ("github-actions", "dependabot"):
                        continue

                    change = classify_human_comment(task, body, author)
                    print(f"  PR COMMENT: {pr_url} by {author}: {change.action_needed[:50]}")

                    try:
                        await mc.post_comment(
                            board_id, task.id,
                            f"**GitHub comment by {author}**: {body[:200]}\n\n"
                            f"Action: {change.action_needed}",
                        )
                    except Exception:
                        pass

                    try:
                        await irc.notify("#reviews",
                            f"[sync] PR comment by {author} on {task.title[:30]}: {body[:60]}")
                    except Exception:
                        pass

                    # Emit event for agent's feed
                    _sync_emit_event(
                        "fleet.github.pr_commented",
                        subject=task.id,
                        recipient=task.custom_fields.agent_name or "all",
                        priority="important",
                        mentions=[task.custom_fields.agent_name] if task.custom_fields.agent_name else [],
                        tags=["github", "pr_comment", f"project:{task.custom_fields.project or 'unknown'}"],
                        surfaces=["internal", "channel"],
                        pr_url=pr_url,
                        author=author,
                        comment_preview=body[:100],
                        action_needed=change.action_needed,
                    )

            _pr_comment_counts[pr_url] = current_count
        except Exception:
            continue


async def _check_pr_hygiene(mc, gh, irc, board_id, tasks, actions_count) -> None:
    """Check all open PRs across fleet projects for hygiene issues."""
    from fleet.core.pr_hygiene import assess_pr_hygiene

    loader = ConfigLoader()
    projects = loader.load_projects()

    all_open_prs: list[dict] = []
    for name, proj in projects.items():
        if proj.local or not proj.owner:
            continue
        try:
            ok, output = await gh._run([
                "gh", "pr", "list", "--repo", f"{proj.owner}/{proj.repo}",
                "--state", "open", "--json", "number,title,url,createdAt",
            ])
            if ok and output.strip():
                import json
                prs = json.loads(output)
                for pr in prs:
                    pr["mergeable"] = "UNKNOWN"
                    # Check mergeable state per PR
                    try:
                        ok2, merge_info = await gh._run([
                            "gh", "pr", "view", str(pr["number"]),
                            "--repo", f"{proj.owner}/{proj.repo}",
                            "--json", "mergeable",
                        ])
                        if ok2:
                            merge_data = json.loads(merge_info)
                            pr["mergeable"] = merge_data.get("mergeable", "UNKNOWN")
                    except Exception:
                        pass
                    pr["created_at"] = pr.get("createdAt", "")
                    all_open_prs.append(pr)
        except Exception:
            continue

    if not all_open_prs:
        return

    report = assess_pr_hygiene(tasks, all_open_prs)

    if not report.has_issues:
        return

    for issue in report.issues:
        if issue.issue_type == "conflicting":
            print(f"  CONFLICT: PR #{issue.pr_number} — {issue.pr_title[:40]}")
            # Create resolve-conflict task if task exists
            if issue.task_id:
                try:
                    agents = await mc.list_agents()
                    agent_id = next(
                        (a.id for a in agents if a.name == issue.target_agent), None
                    )
                    await mc.create_task(
                        board_id,
                        title=f"Resolve conflict: PR #{issue.pr_number} — {issue.pr_title[:30]}",
                        description=(
                            f"PR #{issue.pr_number} has merge conflicts.\n"
                            f"URL: {issue.pr_url}\n\n"
                            f"{issue.recommended_action}\n\n"
                            f"Rebase branch against main, resolve conflicts, force-push."
                        ),
                        priority="high",
                        assigned_agent_id=agent_id,
                        custom_fields={
                            "agent_name": issue.target_agent,
                            "parent_task": issue.task_id,
                            "task_type": "blocker",
                            "pr_url": issue.pr_url,
                        },
                    )
                    print(f"    Created resolve-conflict task → {issue.target_agent}")
                except Exception as e:
                    print(f"    ERROR creating conflict task: {e}")

        elif issue.issue_type == "stale":
            print(f"  STALE: PR #{issue.pr_number} — task done, PR still open")
            # Close stale PRs whose tasks are done
            try:
                repo = issue.pr_url.split("/pull/")[0].replace("https://github.com/", "")
                ok, _ = await gh._run([
                    "gh", "pr", "close", str(issue.pr_number),
                    "--repo", repo,
                    "--comment", "Closing — task completed via different path.",
                ])
                if ok:
                    print(f"    Closed PR #{issue.pr_number}")
            except Exception:
                pass

        elif issue.issue_type == "orphaned":
            print(f"  ORPHANED: PR #{issue.pr_number} — no linked task")
            # Close orphaned conflicting PRs (work done elsewhere)
            if any(i.issue_type == "conflicting" and i.pr_number == issue.pr_number for i in report.issues):
                try:
                    repo = issue.pr_url.split("/pull/")[0].replace("https://github.com/", "")
                    ok, _ = await gh._run([
                        "gh", "pr", "close", str(issue.pr_number),
                        "--repo", repo,
                        "--comment", "Closing — orphaned PR with conflicts. No linked task. Work likely completed via different PR.",
                    ])
                    if ok:
                        print(f"    Closed orphaned conflicting PR #{issue.pr_number}")
                except Exception:
                    pass

        elif issue.issue_type == "long_open":
            print(f"  STALE: PR #{issue.pr_number} open too long — {issue.description[:50]}")


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