#!/usr/bin/env bash
set -euo pipefail

# Configure MC board with fleet custom fields and tags.
# Idempotent — safe to run multiple times.
# Called by setup-mc.sh after board creation.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"
PROJECTS_YAML="$FLEET_DIR/config/projects.yaml"

if [[ -z "$TOKEN" ]]; then echo "ERROR: No LOCAL_AUTH_TOKEN" >&2; exit 1; fi

# Resolve board ID
BOARD_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$MC_URL/api/v1/agents" | python3 -c "
import json, sys
for a in json.load(sys.stdin).get('items', []):
    if a.get('board_id'): print(a['board_id']); break
" 2>/dev/null)

if [[ -z "$BOARD_ID" ]]; then echo "ERROR: No board found" >&2; exit 1; fi

python3 << PYEOF
import json, sys, yaml
import urllib.request, urllib.error

MC_URL = "$MC_URL"
TOKEN = "$TOKEN"
BOARD_ID = "$BOARD_ID"

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

# ─── Custom Fields ──────────────────────────────────────────────────────

FIELDS = [
    {"field_key": "project", "label": "Project", "field_type": "text",
     "ui_visibility": "always", "description": "Target project name"},
    {"field_key": "branch", "label": "Branch", "field_type": "text",
     "ui_visibility": "if_set", "description": "Git branch name"},
    {"field_key": "pr_url", "label": "Pull Request", "field_type": "url",
     "ui_visibility": "if_set", "description": "GitHub PR URL"},
    {"field_key": "worktree", "label": "Worktree", "field_type": "text",
     "ui_visibility": "hidden", "description": "Local worktree path"},
    {"field_key": "agent_name", "label": "Agent", "field_type": "text",
     "ui_visibility": "if_set", "description": "Assigned agent name"},
    {"field_key": "story_points", "label": "Story Points", "field_type": "integer",
     "ui_visibility": "if_set", "description": "Effort estimate (1/2/3/5/8/13)"},
    {"field_key": "sprint", "label": "Sprint", "field_type": "text",
     "ui_visibility": "if_set", "description": "Sprint identifier"},
    {"field_key": "complexity", "label": "Complexity", "field_type": "text",
     "ui_visibility": "if_set", "description": "low/medium/high"},
    {"field_key": "model", "label": "Model", "field_type": "text",
     "ui_visibility": "hidden", "description": "AI model used (sonnet/opus)"},
    {"field_key": "parent_task", "label": "Parent Task", "field_type": "text",
     "ui_visibility": "if_set", "description": "Parent task ID for hierarchy"},
    {"field_key": "task_type", "label": "Task Type", "field_type": "text",
     "ui_visibility": "always", "description": "epic/story/task/subtask/blocker/request/concern"},
    {"field_key": "plan_id", "label": "Plan ID", "field_type": "text",
     "ui_visibility": "if_set", "description": "Sprint plan or grouping reference"},
    {"field_key": "review_gates", "label": "Review Gates", "field_type": "json",
     "ui_visibility": "if_set", "description": "Review gate status per reviewer [{agent, type, status, reason}]"},
]

print("=== Configuring Board Custom Fields ===")

# Get existing fields
existing_resp = api("GET", "/api/v1/organizations/me/custom-fields")
existing_fields = {}
if isinstance(existing_resp, dict):
    for f in existing_resp.get("items", []):
        existing_fields[f.get("field_key", "")] = f
elif isinstance(existing_resp, list):
    for f in existing_resp:
        existing_fields[f.get("field_key", "")] = f

for field_def in FIELDS:
    key = field_def["field_key"]
    if key in existing_fields:
        print(f"  EXISTS: {key}")
        continue

    field_def["board_ids"] = [BOARD_ID]
    result = api("POST", "/api/v1/organizations/me/custom-fields", field_def)
    if result.get("id"):
        print(f"  CREATED: {key} ({field_def['field_type']})")
    else:
        print(f"  FAIL: {key} — {result.get('detail', '?')}")

# ─── Tags ────────────────────────────────────────────────────────────────

print()
print("=== Configuring Board Tags ===")

# Project tags from config
project_tags = []
try:
    with open("$PROJECTS_YAML") as f:
        pcfg = yaml.safe_load(f)
    for name in pcfg.get("projects", {}).keys():
        project_tags.append({"name": f"project:{name}", "color": "2196f3",
                           "description": f"Project: {name}"})
except: pass

# Type tags
type_tags = [
    {"name": "type:feature", "color": "4caf50", "description": "New feature"},
    {"name": "type:fix", "color": "f44336", "description": "Bug fix"},
    {"name": "type:docs", "color": "9c27b0", "description": "Documentation"},
    {"name": "type:test", "color": "ff9800", "description": "Testing"},
    {"name": "type:chore", "color": "607d8b", "description": "Maintenance"},
    {"name": "type:review", "color": "00bcd4", "description": "Code review"},
]

# Hierarchy tags
hierarchy_tags = [
    {"name": "type:epic", "color": "673ab7", "description": "Epic — high-level initiative"},
    {"name": "type:story", "color": "3f51b5", "description": "Story — user-facing capability"},
    {"name": "type:subtask", "color": "03a9f4", "description": "Subtask — child of a story"},
    {"name": "type:blocker", "color": "e91e63", "description": "Blocker — requires resolution"},
    {"name": "type:request", "color": "ff9800", "description": "Request — needs input or action"},
    {"name": "type:concern", "color": "795548", "description": "Concern — needs attention"},
]

# Status tags
status_tags = [
    {"name": "needs-review", "color": "ff5722", "description": "Human review needed"},
    {"name": "auto-merge", "color": "8bc34a", "description": "Can auto-merge after checks"},
    {"name": "blocked", "color": "f44336", "description": "Blocked — needs attention"},
]

all_tags = project_tags + type_tags + hierarchy_tags + status_tags

# Get existing tags
existing_tags_resp = api("GET", "/api/v1/tags")
existing_tag_names = set()
if isinstance(existing_tags_resp, dict):
    for t in existing_tags_resp.get("items", []):
        existing_tag_names.add(t.get("name", ""))
elif isinstance(existing_tags_resp, list):
    for t in existing_tags_resp:
        existing_tag_names.add(t.get("name", ""))

created = 0
for tag in all_tags:
    if tag["name"] in existing_tag_names:
        continue
    result = api("POST", "/api/v1/tags", tag)
    if result.get("id"):
        created += 1
    else:
        print(f"  FAIL: {tag['name']} — {result.get('detail', '?')}")

print(f"  Tags: {created} created, {len(existing_tag_names)} existing")

# Print summary
print()
all_tags_resp = api("GET", "/api/v1/tags")
tag_list = all_tags_resp.get("items", []) if isinstance(all_tags_resp, dict) else all_tags_resp if isinstance(all_tags_resp, list) else []
print(f"Board: {BOARD_ID}")
print(f"Custom fields: {len(FIELDS)}")
print(f"Tags: {len(tag_list)}")
PYEOF