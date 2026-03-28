#!/usr/bin/env bash
set -euo pipefail

# Fleet quality enforcement — checks recent output against standards.
#
# Checks:
#   - Recent commits: conventional commit format?
#   - Open PRs: have changelog, references, structured body?
#   - Recent task comments: structured format?
#   - Board memory entries: properly tagged?
#
# Usage:
#   bash scripts/fleet-quality-check.sh           # check and report
#   bash scripts/fleet-quality-check.sh --fix      # suggest fixes

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then echo "ERROR: No LOCAL_AUTH_TOKEN" >&2; exit 1; fi

export MC_URL TOKEN FLEET_DIR

python3 << 'PYEOF'
import json, os, re, subprocess
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

def get_items(path):
    resp = api(path)
    if isinstance(resp, list): return resp
    if isinstance(resp, dict): return resp.get("items", [])
    return []

CONVENTIONAL_RE = re.compile(r'^(feat|fix|docs|refactor|test|chore|ci|style|perf)(\([^)]+\))?: .+')

violations = []
passes = 0

print("=== Fleet Quality Check ===")
print()

# ─── 1. Check recent commits in project worktrees ──────────────────

print("📝 Commit Messages")
for project_dir in sorted(os.listdir(os.path.join(FLEET_DIR, "projects"))) if os.path.isdir(os.path.join(FLEET_DIR, "projects")) else []:
    wt_dir = os.path.join(FLEET_DIR, "projects", project_dir, "worktrees")
    if not os.path.isdir(wt_dir):
        continue
    for wt in os.listdir(wt_dir):
        wt_path = os.path.join(wt_dir, wt)
        if not os.path.isdir(wt_path):
            continue
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "origin/main..HEAD", "--format=%s"],
                capture_output=True, text=True, timeout=5, cwd=wt_path
            )
            for msg in result.stdout.strip().split("\n"):
                if not msg:
                    continue
                if CONVENTIONAL_RE.match(msg):
                    passes += 1
                else:
                    violations.append(f"  ❌ Non-conventional commit: '{msg[:60]}' in {wt}")
                    print(f"  ❌ {wt}: '{msg[:60]}'")
        except:
            pass

if not violations:
    print("  ✅ All commits follow conventional format")
print()

# ─── 2. Check open PRs ─────────────────────────────────────────────

print("🔀 Pull Request Quality")
pr_violations = []
try:
    result = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--json", "title,body,url,number"],
        capture_output=True, text=True, timeout=15
    )
    prs = json.loads(result.stdout) if result.returncode == 0 else []
except:
    prs = []

for pr in prs:
    body = pr.get("body", "") or ""
    title = pr.get("title", "")
    url = pr.get("url", "")
    issues = []

    if "## " not in body and "# " not in body:
        issues.append("no markdown headers")
    if "changelog" not in body.lower() and "changes" not in body.lower():
        issues.append("no changelog/changes section")
    if "http" not in body:
        issues.append("no URLs/references")
    if len(body) < 100:
        issues.append(f"body too short ({len(body)} chars)")

    if issues:
        pr_violations.append(f"  ❌ PR #{pr.get('number')}: {', '.join(issues)}")
        print(f"  ❌ #{pr.get('number')} {title[:40]}: {', '.join(issues)}")
    else:
        passes += 1
        print(f"  ✅ #{pr.get('number')} {title[:40]}")

if not prs:
    print("  (no open PRs)")
print()

# ─── 3. Check board memory tags ────────────────────────────────────

print("🏷️  Board Memory Tags")
board_id = None
for a in get_items("/api/v1/agents"):
    if a.get("board_id"):
        board_id = str(a["board_id"])
        break

if board_id:
    memories = get_items(f"/api/v1/boards/{board_id}/memory?limit=20")
    untagged = 0
    tagged = 0
    for m in memories:
        tags = m.get("tags") or []
        if not tags:
            untagged += 1
        else:
            tagged += 1

    if untagged > 0:
        violations.append(f"  ❌ {untagged} board memory entries without tags")
        print(f"  ❌ {untagged} entries without tags (of {untagged + tagged} checked)")
    else:
        print(f"  ✅ All {tagged} entries properly tagged")
else:
    print("  (no board found)")
print()

# ─── 4. Check task custom fields ───────────────────────────────────

print("📋 Task Custom Fields")
if board_id:
    tasks = get_items(f"/api/v1/boards/{board_id}/tasks?limit=50")
    missing_project = 0
    has_project = 0
    for t in tasks:
        custom = t.get("custom_field_values") or {}
        if custom.get("project"):
            has_project += 1
        else:
            missing_project += 1

    if missing_project > 0:
        print(f"  ⚠️  {missing_project} tasks without project field (of {missing_project + has_project})")
    else:
        print(f"  ✅ All {has_project} tasks have project field")

    # Check review tasks have pr_url
    review_tasks = [t for t in tasks if t.get("status") == "review"]
    missing_pr = sum(1 for t in review_tasks if not (t.get("custom_field_values") or {}).get("pr_url"))
    if missing_pr > 0:
        print(f"  ⚠️  {missing_pr} review tasks without pr_url field")
    elif review_tasks:
        print(f"  ✅ All {len(review_tasks)} review tasks have pr_url")

print()

# ─── Summary ────────────────────────────────────────────────────────

total_violations = len(violations) + len(pr_violations)
print("=" * 40)
print(f"Passes: {passes}")
print(f"Violations: {total_violations}")

if total_violations > 0:
    print()
    print("Violations:")
    for v in violations + pr_violations:
        print(v)
PYEOF