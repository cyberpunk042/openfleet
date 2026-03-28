#!/usr/bin/env bash
set -euo pipefail

# Single check pass — called by fleet-monitor-daemon.sh.
# Checks board state, posts alerts for violations.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then exit 0; fi

export MC_URL TOKEN FLEET_DIR

python3 << 'PYEOF'
import json, os, sys, subprocess
from datetime import datetime, timezone
import urllib.request, urllib.error

MC_URL = os.environ.get("MC_URL", "http://localhost:8000")
TOKEN = os.environ.get("TOKEN", "")
FLEET_DIR = os.environ.get("FLEET_DIR", ".")

def api(path):
    req = urllib.request.Request(f"{MC_URL}{path}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except:
        return None

def notify(agent, event, title, url="", channel="#fleet"):
    script = os.path.join(FLEET_DIR, "scripts", "notify-irc.sh")
    if not os.path.isfile(script):
        return
    cmd = ["bash", script, "--agent", agent, "--event", event, "--title", title, "--channel", channel]
    if url:
        cmd.extend(["--url", url])
    try:
        subprocess.run(cmd, capture_output=True, timeout=15)
    except:
        pass

def hours_ago(iso_str):
    if not iso_str:
        return 999
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() / 3600
    except:
        return 999

# Get board
agents_resp = api("/api/v1/agents")
if not agents_resp:
    sys.exit(0)
items = agents_resp.get("items", []) if isinstance(agents_resp, dict) else agents_resp
board_id = None
for a in items:
    if a.get("board_id"):
        board_id = str(a["board_id"])
        break

if not board_id:
    sys.exit(0)

# Get tasks
tasks_resp = api(f"/api/v1/boards/{board_id}/tasks?limit=100")
if not tasks_resp:
    sys.exit(0)
tasks = tasks_resp.get("items", []) if isinstance(tasks_resp, dict) else tasks_resp

alerts = 0

for task in tasks:
    title = task.get("title", "")[:60]
    status = task.get("status", "")
    created = task.get("created_at", "")
    updated = task.get("updated_at", "")
    task_id = str(task.get("id", ""))
    custom = task.get("custom_field_values") or {}
    pr_url = custom.get("pr_url", "")

    # Stale inbox (> 1 hour)
    if status == "inbox" and hours_ago(created) > 1:
        h = int(hours_ago(created))
        notify("fleet-ops", "⏰ STALE INBOX", f"{title} ({h}h)")
        alerts += 1

    # In progress > 8 hours without update
    if status == "in_progress" and hours_ago(updated) > 8:
        h = int(hours_ago(updated))
        notify("fleet-ops", "⏰ STALE PROGRESS", f"{title} (no update {h}h)")
        alerts += 1

    # In review > 24 hours
    if status == "review" and hours_ago(updated) > 24:
        h = int(hours_ago(updated))
        url = pr_url if pr_url else ""
        notify("fleet-ops", "⏰ STALE REVIEW", f"{title} ({h}h)", url=url, channel="#reviews")
        alerts += 1

    # Unmerged PR > 48 hours
    if pr_url and status == "review" and hours_ago(updated) > 48:
        notify("fleet-ops", "⚠️ PR AGING", f"{title} (48h+)", url=pr_url, channel="#reviews")
        alerts += 1

# Check agent health
for a in items:
    name = a.get("name", "")
    if "Gateway" in name:
        continue
    agent_status = a.get("status", "")
    last_seen = a.get("last_seen_at", "")
    if agent_status == "offline" and hours_ago(last_seen) > 2:
        h = int(hours_ago(last_seen))
        notify("fleet-ops", "🔴 AGENT OFFLINE", f"{name} ({h}h)", channel="#alerts")
        alerts += 1

if alerts > 0:
    print(f"  {alerts} alerts posted")
else:
    print("  Board healthy")
PYEOF