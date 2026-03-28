#!/usr/bin/env bash
set -euo pipefail

# Create a task in Mission Control and optionally dispatch it to an agent.
#
# Usage:
#   bash scripts/create-task.sh <title> [--agent <name>] [--desc <description>] [--dispatch]
#
# Options:
#   --agent <name>   Assign to this agent
#   --desc <text>    Task description
#   --priority <p>   Priority: low, medium, high, urgent (default: medium)
#   --dispatch       Immediately dispatch to the agent via chat.send

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: No LOCAL_AUTH_TOKEN in .env" >&2
    exit 1
fi

# Parse args
TITLE=""
AGENT_NAME=""
DESCRIPTION=""
PRIORITY="medium"
DISPATCH=false
PROJECT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent) AGENT_NAME="$2"; shift 2 ;;
        --desc) DESCRIPTION="$2"; shift 2 ;;
        --priority) PRIORITY="$2"; shift 2 ;;
        --project) PROJECT="$2"; shift 2 ;;
        --dispatch) DISPATCH=true; shift ;;
        *)
            if [[ -z "$TITLE" ]]; then
                TITLE="$1"
            else
                TITLE="$TITLE $1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$TITLE" ]]; then
    echo "Usage: bash scripts/create-task.sh <title> [--agent <name>] [--desc <text>] [--project <name>] [--dispatch]"
    exit 1
fi

# Resolve board ID and agent ID
BOARD_ID=""
AGENT_ID=""

AGENTS_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "$MC_URL/api/v1/agents")
BOARD_ID=$(echo "$AGENTS_JSON" | python3 -c "
import json, sys
for a in json.load(sys.stdin).get('items', []):
    if a.get('board_id'):
        print(a['board_id'])
        break
" 2>/dev/null)

if [[ -n "$AGENT_NAME" ]]; then
    AGENT_ID=$(echo "$AGENTS_JSON" | python3 -c "
import json, sys
for a in json.load(sys.stdin).get('items', []):
    if a.get('name') == '$AGENT_NAME':
        print(a['id'])
        break
" 2>/dev/null)
    if [[ -z "$AGENT_ID" ]]; then
        echo "ERROR: Agent '$AGENT_NAME' not found" >&2
        exit 1
    fi
fi

# Create task
# Resolve tag IDs for project and type
TAG_IDS=$(python3 -c "
import json, sys
import urllib.request

def get(path):
    req = urllib.request.Request('$MC_URL' + path)
    req.add_header('Authorization', 'Bearer $TOKEN')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except: return []

tags_resp = get('/api/v1/tags')
tags = tags_resp.get('items', []) if isinstance(tags_resp, dict) else tags_resp if isinstance(tags_resp, list) else []

ids = []
project = '$PROJECT'
if project:
    for t in tags:
        if t.get('name') == f'project:{project}':
            ids.append(str(t['id']))
            break

print(','.join(ids))
" 2>/dev/null)

TASK_DATA=$(python3 -c "
import json
data = {
    'title': '''$TITLE''',
    'status': 'inbox',
    'priority': '$PRIORITY',
}
desc = '''$DESCRIPTION'''
if desc:
    data['description'] = desc
agent_id = '$AGENT_ID'
if agent_id:
    data['assigned_agent_id'] = agent_id

# Custom fields
custom = {}
project = '$PROJECT'
if project:
    custom['project'] = project
if custom:
    data['custom_field_values'] = custom

# Tags
tag_ids = '$TAG_IDS'.split(',')
tag_ids = [t for t in tag_ids if t]
if tag_ids:
    data['tag_ids'] = tag_ids

print(json.dumps(data))
")

RESULT=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "$MC_URL/api/v1/boards/${BOARD_ID}/tasks" \
    -d "$TASK_DATA")

TASK_ID=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)

if [[ -z "$TASK_ID" ]]; then
    echo "ERROR: Failed to create task"
    echo "$RESULT" | head -3
    exit 1
fi

echo "Created task: $TASK_ID"
echo "Title: $TITLE"
[[ -n "$AGENT_NAME" ]] && echo "Assigned: $AGENT_NAME"
echo "Priority: $PRIORITY"

# Notify IRC
NOTIFY_AGENT="${AGENT_NAME:-human}"
bash "$FLEET_DIR/scripts/notify-irc.sh" \
    --agent "$NOTIFY_AGENT" --event "TASK CREATED" \
    --title "$TITLE" 2>/dev/null || true

# Dispatch if requested
if [[ "$DISPATCH" == "true" && -n "$AGENT_NAME" ]]; then
    echo ""
    DISPATCH_ARGS=("$AGENT_NAME" "$TASK_ID")
    [[ -n "$PROJECT" ]] && DISPATCH_ARGS+=(--project "$PROJECT")
    bash "$FLEET_DIR/scripts/dispatch-task.sh" "${DISPATCH_ARGS[@]}"
fi