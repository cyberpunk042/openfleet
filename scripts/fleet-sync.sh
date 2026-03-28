#!/usr/bin/env bash
set -euo pipefail

# Fleet sync — keeps MC tasks and GitHub PRs in sync.
#
# Runs once and exits (designed for cron or periodic execution).
# Use: bash scripts/fleet-sync.sh
#      Or: make sync
#
# What it does:
#   1. Tasks in "done" with unmerged PR → merge the PR
#   2. Tasks in "review" with merged PR → move to "done"
#   3. Tasks in "done" → cleanup worktrees
#   4. Posts notifications to board memory

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then echo "ERROR: No LOCAL_AUTH_TOKEN" >&2; exit 1; fi

export FLEET_DIR MC_URL TOKEN LOCAL_AUTH_TOKEN
MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"

python3 << 'PYEOF'
import json, sys, os, subprocess, shutil
import urllib.request, urllib.error

MC_URL = os.environ.get("MC_URL", os.environ.get("OCF_MISSION_CONTROL_URL", "http://localhost:8000"))
TOKEN = os.environ.get("LOCAL_AUTH_TOKEN", "")
FLEET_DIR = os.environ.get("FLEET_DIR", ".")

def api(method, path, data=None):
    url = f"{MC_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except: return {"detail": str(e)}
    except Exception as e:
        return {"detail": str(e)}

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd)
        return r.returncode == 0, r.stdout.strip()
    except:
        return False, ""

def get_board_id():
    resp = api("GET", "/api/v1/agents")
    items = resp.get("items", []) if isinstance(resp, dict) else resp if isinstance(resp, list) else []
    for a in items:
        if a.get("board_id"):
            return str(a["board_id"])
    return None

def get_tasks(board_id):
    resp = api("GET", f"/api/v1/boards/{board_id}/tasks?limit=100")
    return resp.get("items", []) if isinstance(resp, dict) else resp if isinstance(resp, list) else []

def get_pr_state(pr_url):
    """Check if a GitHub PR is merged using gh CLI."""
    if not pr_url:
        return None
    ok, output = run(["gh", "pr", "view", pr_url, "--json", "state,mergedAt"])
    if not ok:
        return None
    try:
        data = json.loads(output)
        return data.get("state", "").upper()  # OPEN, CLOSED, MERGED
    except:
        return None

def find_worktree(task_id):
    """Find worktree for a task by ID prefix."""
    short = task_id[:8]
    fleet_dir = os.environ.get("FLEET_DIR", ".")
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

def post_comment(board_id, task_id, message):
    api("POST", f"/api/v1/boards/{board_id}/tasks/{task_id}/comments",
        {"message": message})

def post_memory(board_id, content, tags):
    api("POST", f"/api/v1/boards/{board_id}/memory",
        {"content": content, "tags": tags, "source": "fleet-sync"})

def notify_irc(agent, event, title="", url=""):
    """Send notification to IRC via notify-irc.sh."""
    fleet_dir = os.environ.get("FLEET_DIR", ".")
    script = os.path.join(fleet_dir, "scripts", "notify-irc.sh")
    if not os.path.isfile(script):
        return
    cmd = ["bash", script, "--agent", agent, "--event", event]
    if title:
        cmd.extend(["--title", title])
    if url:
        cmd.extend(["--url", url])
    try:
        subprocess.run(cmd, capture_output=True, timeout=15)
    except:
        pass

def update_task_status(board_id, task_id, status, comment=None):
    data = {"status": status}
    if comment:
        data["comment"] = comment
    api("PATCH", f"/api/v1/boards/{board_id}/tasks/{task_id}", data)

# ─── Main ────────────────────────────────────────────────────────────────

board_id = get_board_id()
if not board_id:
    print("ERROR: No board found")
    sys.exit(1)

tasks = get_tasks(board_id)
actions = 0

for task in tasks:
    task_id = str(task.get("id", ""))
    status = task.get("status", "")
    title = task.get("title", "")
    custom = task.get("custom_field_values") or {}
    pr_url = custom.get("pr_url", "")

    # Skip tasks without PRs
    if not pr_url:
        # Check task comments for PR URL (fallback)
        continue

    pr_state = get_pr_state(pr_url)

    # ── Task in "done" with unmerged PR → merge it ──
    if status == "done" and pr_state == "OPEN":
        print(f"  MERGE: {title[:50]} — {pr_url}")
        ok, output = run(["gh", "pr", "merge", pr_url, "--squash", "--delete-branch"])
        if ok:
            post_comment(board_id, task_id, f"**Auto-merged** PR: {pr_url}")
            post_memory(board_id,
                f"**Merged**: {title}\nPR: {pr_url}",
                ["merged", custom.get("project", "fleet")])
            notify_irc("fleet", "MERGED", title, pr_url)
            actions += 1
        else:
            print(f"    FAIL: merge failed — {output}")

    # ── Task in "review" with merged PR → move to done ──
    elif status == "review" and pr_state == "MERGED":
        print(f"  DONE: {title[:50]} — PR already merged")
        update_task_status(board_id, task_id, "done",
            f"**Auto-closed** — PR was merged: {pr_url}")
        post_memory(board_id,
            f"**Completed**: {title}\nPR: {pr_url} (merged)",
            ["completed", custom.get("project", "fleet")])
        notify_irc("fleet", "TASK DONE", title, pr_url)
        actions += 1

    # ── Task in "done" → cleanup worktree ──
    if status == "done":
        wt = find_worktree(task_id)
        if wt and os.path.isdir(wt):
            print(f"  CLEANUP: {wt}")
            # Remove git worktree properly
            project_dir = os.path.dirname(os.path.dirname(wt))
            ok, _ = run(["git", "worktree", "remove", wt, "--force"], cwd=project_dir)
            if ok:
                # Also delete the branch
                branch = f"fleet/{os.path.basename(wt).rsplit('-', 1)[0]}/{task_id[:8]}"
                run(["git", "branch", "-D", branch], cwd=project_dir)
                actions += 1
            else:
                print(f"    FAIL: worktree removal failed")

if actions == 0:
    print("  Nothing to sync")
else:
    print(f"\n  {actions} actions taken")
PYEOF