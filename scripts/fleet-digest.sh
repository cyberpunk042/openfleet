#!/usr/bin/env bash
set -euo pipefail

# Generate and post fleet daily digest to IRC #fleet and board memory.
#
# Usage:
#   bash scripts/fleet-digest.sh           # generate and post
#   bash scripts/fleet-digest.sh --dry-run  # print without posting

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if [[ -z "$TOKEN" ]]; then echo "ERROR: No LOCAL_AUTH_TOKEN" >&2; exit 1; fi

export MC_URL TOKEN FLEET_DIR DRY_RUN

python3 << 'PYEOF'
import json, os, sys
from datetime import datetime, timezone, timedelta
import urllib.request, urllib.error, subprocess

MC_URL = os.environ.get("MC_URL", "http://localhost:8000")
TOKEN = os.environ.get("TOKEN", "")
FLEET_DIR = os.environ.get("FLEET_DIR", ".")
DRY_RUN = os.environ.get("DRY_RUN", "false") == "true"

def api(method, path, data=None):
    url = f"{MC_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except:
        return None

def get_items(path):
    resp = api("GET", path)
    if isinstance(resp, list): return resp
    if isinstance(resp, dict): return resp.get("items", [])
    return []

# Gather data
agents = get_items("/api/v1/agents")
board_id = None
for a in agents:
    if a.get("board_id"):
        board_id = str(a["board_id"])
        break

if not board_id:
    print("No board found")
    sys.exit(1)

tasks = get_items(f"/api/v1/boards/{board_id}/tasks?limit=100")
activity = get_items("/api/v1/activity?limit=100")

# Count by status
status_counts = {}
for t in tasks:
    s = t.get("status", "?")
    status_counts[s] = status_counts.get(s, 0) + 1

# Recent activity (last 24h)
now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=24)
recent = []
for e in activity:
    ts = e.get("created_at", "")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt > cutoff:
            recent.append(e)
    except:
        pass

# Count activity types
activity_counts = {}
for e in recent:
    et = e.get("event_type", "?")
    activity_counts[et] = activity_counts.get(et, 0) + 1

tasks_created = activity_counts.get("task.created", 0)
tasks_done = sum(1 for e in recent if e.get("event_type") == "task.status_changed" and "done" in str(e.get("message", "")))
prs_merged = sum(1 for e in recent if "merged" in str(e.get("message", "")).lower() or "auto-merged" in str(e.get("message", "")).lower())

# Active work
active = [t for t in tasks if t.get("status") == "in_progress"]
review = [t for t in tasks if t.get("status") == "review"]
blocked = [t for t in tasks if "block" in str(t.get("description", "")).lower()]

# Agent health
online = sum(1 for a in agents if a.get("status") == "online" and "Gateway" not in a.get("name", ""))
total = sum(1 for a in agents if "Gateway" not in a.get("name", ""))

# Build digest
date_str = now.strftime("%Y-%m-%d")
digest = f"""## 📊 Fleet Daily Digest — {date_str}

### Activity (last 24h)
| Metric | Count |
|--------|-------|
| Tasks created | {tasks_created} |
| Tasks completed | {tasks_done} |
| PRs merged | {prs_merged} |
| Events total | {len(recent)} |

### Board Status
| Status | Count |
|--------|-------|
"""

for status in ["inbox", "in_progress", "review", "done"]:
    count = status_counts.get(status, 0)
    if count > 0:
        digest += f"| {status} | {count} |\n"

if active:
    digest += "\n### Active Work\n| Agent | Task | Hours |\n|-------|------|-------|\n"
    for t in active:
        title = t.get("title", "?")[:40]
        updated = t.get("updated_at", "")
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            hours = int((now - dt).total_seconds() / 3600)
        except:
            hours = "?"
        digest += f"| — | {title} | {hours}h |\n"

if review:
    digest += f"\n### Pending Review ({len(review)})\n"
    for t in review:
        title = t.get("title", "?")[:50]
        custom = t.get("custom_field_values") or {}
        pr = custom.get("pr_url", "")
        if pr:
            digest += f"- [{title}]({pr})\n"
        else:
            digest += f"- {title}\n"

digest += f"\n### Health\n- Agents online: {online}/{total}\n"

digest += f"\n---\n<sub>fleet-ops · {now.strftime('%Y-%m-%d %H:%M UTC')}</sub>"

if DRY_RUN:
    print(digest)
    sys.exit(0)

# Post to board memory
api("POST", f"/api/v1/boards/{board_id}/memory", {
    "content": digest,
    "tags": ["report", "digest", "daily"],
    "source": "fleet-ops",
})

# Post summary to IRC #fleet
summary = f"[fleet-ops] 📊 DAILY DIGEST: {tasks_created} created, {tasks_done} done, {prs_merged} merged, {len(review)} in review, {online}/{total} agents online"
script = os.path.join(FLEET_DIR, "scripts", "notify-irc.sh")
if os.path.isfile(script):
    try:
        subprocess.run(["bash", script, summary], capture_output=True, timeout=15)
    except:
        pass

print(f"Digest posted for {date_str}")
PYEOF