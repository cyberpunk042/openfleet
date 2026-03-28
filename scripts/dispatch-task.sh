#!/usr/bin/env bash
set -euo pipefail

# Dispatch a task to an agent via OpenClaw gateway chat.send.
#
# Usage:
#   bash scripts/dispatch-task.sh <agent-name> <task-id> [--project <name>]
#
# If --project is specified, creates a git worktree for the agent and includes
# the working directory in the task message.
#
# Requires: MC running, gateway running, .env with LOCAL_AUTH_TOKEN

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

# Auto-refresh auth token if rotated (silent, no gateway restart)
bash "$FLEET_DIR/scripts/refresh-auth.sh" 2>/dev/null || true

# Parse args
AGENT_NAME=""
TASK_ID=""
PROJECT_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project) PROJECT_NAME="$2"; shift 2 ;;
        *)
            if [[ -z "$AGENT_NAME" ]]; then
                AGENT_NAME="$1"
            elif [[ -z "$TASK_ID" ]]; then
                TASK_ID="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$AGENT_NAME" || -z "$TASK_ID" ]]; then
    echo "Usage: dispatch-task.sh <agent-name> <task-id> [--project <name>]" >&2
    exit 1
fi

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"

# Resolve agent info from MC
AGENT_INFO=$(curl -s -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" "$MC_URL/api/v1/agents" | python3 -c "
import json, sys
for a in json.load(sys.stdin).get('items', []):
    if a.get('name') == '$AGENT_NAME':
        print(json.dumps({'id': str(a['id']), 'board_id': str(a.get('board_id','')), 'session': a.get('openclaw_session_id','')}))
        break
" 2>/dev/null)

if [[ -z "$AGENT_INFO" ]]; then
    echo "ERROR: Agent '$AGENT_NAME' not found in MC" >&2
    exit 1
fi

BOARD_ID=$(echo "$AGENT_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['board_id'])")
SESSION_KEY=$(echo "$AGENT_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['session'])")

# Fetch task details
TASK_INFO=$(curl -s -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" "$MC_URL/api/v1/boards/${BOARD_ID}/tasks" | python3 -c "
import json, sys
for t in json.load(sys.stdin).get('items', []):
    if str(t.get('id', '')) == '$TASK_ID':
        print(json.dumps(t, default=str))
        break
" 2>/dev/null)

if [[ -z "$TASK_INFO" ]]; then
    echo "ERROR: Task '$TASK_ID' not found on board $BOARD_ID" >&2
    exit 1
fi

TASK_TITLE=$(echo "$TASK_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('title',''))")
TASK_DESC=$(echo "$TASK_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('description','No description.'))")
TASK_PRIORITY=$(echo "$TASK_INFO" | python3 -c "import json,sys; print(json.load(sys.stdin).get('priority','normal'))")

echo "Agent:    $AGENT_NAME"
echo "Session:  $SESSION_KEY"
echo "Task:     $TASK_TITLE"
echo "Priority: $TASK_PRIORITY"

# Setup worktree if project specified
WORK_DIR=""
if [[ -n "$PROJECT_NAME" ]]; then
    echo "Project:  $PROJECT_NAME"
    bash "$FLEET_DIR/scripts/setup-project.sh" "$PROJECT_NAME" >/dev/null 2>&1 || {
        echo "ERROR: Could not setup project '$PROJECT_NAME'" >&2
        exit 1
    }
    WORK_DIR=$(bash "$FLEET_DIR/scripts/setup-worktree.sh" "$PROJECT_NAME" "$AGENT_NAME" "$TASK_ID" 2>/dev/null | tail -1)
    echo "Worktree: $WORK_DIR"
fi

# Write message to temp file for clean passing to Python
MSG_FILE=$(mktemp)
trap "rm -f $MSG_FILE" EXIT

{
echo "NEW TASK ASSIGNMENT"
echo ""
echo "Task ID: $TASK_ID"
echo "Board ID: $BOARD_ID"
echo "Title: $TASK_TITLE"
echo "Priority: $TASK_PRIORITY"

if [[ -n "$WORK_DIR" ]]; then
echo "Project: $PROJECT_NAME"
echo "Working Directory: $WORK_DIR"
echo ""
echo "IMPORTANT: Do your work in $WORK_DIR (git worktree with project code)."
echo "Use absolute paths for file operations. Branch: fleet/$AGENT_NAME/${TASK_ID:0:8}"
echo "Commit your changes to this branch when done."
fi

echo ""
echo "Description:"
echo "$TASK_DESC"
echo ""
echo "Follow the Mission Control Workflow in your SOUL.md."
echo "Read TOOLS.md for your credentials (AUTH_TOKEN, BASE_URL, BOARD_ID)."
} > "$MSG_FILE"

# Dispatch via gateway
echo ""
echo "Dispatching..."
python3 << PYEOF
import asyncio, json, uuid
import websockets

async def send():
    with open('$HOME/.openclaw/openclaw.json') as f:
        cfg = json.load(f)
    oc_token = cfg.get('gateway', {}).get('auth', {}).get('token', '')

    with open('$MSG_FILE') as f:
        message = f.read()

    async with websockets.connect('ws://localhost:18789', origin='http://localhost:18789') as ws:
        await asyncio.wait_for(ws.recv(), timeout=5)
        await ws.send(json.dumps({
            'type': 'req', 'id': str(uuid.uuid4()), 'method': 'connect',
            'params': {
                'minProtocol': 3, 'maxProtocol': 3, 'role': 'operator',
                'scopes': ['operator.read', 'operator.admin', 'operator.approvals', 'operator.pairing'],
                'client': {'id': 'openclaw-control-ui', 'version': '1.0.0', 'platform': 'python', 'mode': 'ui'},
                'auth': {'token': oc_token},
            },
        }))
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        if not json.loads(raw).get('ok'):
            print('ERROR: Gateway connect failed')
            return

        rid = str(uuid.uuid4())
        await ws.send(json.dumps({
            'type': 'req', 'id': rid, 'method': 'chat.send',
            'params': {
                'sessionKey': '$SESSION_KEY',
                'message': message,
                'deliver': False,
                'idempotencyKey': str(uuid.uuid4()),
            },
        }))
        while True:
            data = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
            if data.get('id') == rid:
                if data.get('ok'):
                    run_id = data.get('payload', {}).get('runId', '')
                    print(f'Dispatched: runId={run_id}')
                else:
                    err = data.get('error', {}).get('message', 'unknown')
                    print(f'ERROR: {err}')
                break

asyncio.run(send())
PYEOF

# Notify IRC
bash "$FLEET_DIR/scripts/notify-irc.sh" \
    --agent "$AGENT_NAME" --event "DISPATCHED" \
    --title "$TASK_TITLE" \
    --url "http://localhost:3000" 2>/dev/null || true