#!/usr/bin/env bash
set -euo pipefail

# Send a message to the fleet IRC channel via OpenClaw gateway.
#
# Usage:
#   bash scripts/notify-irc.sh "message text"
#   bash scripts/notify-irc.sh --agent software-engineer --event "PR READY" --url "https://..." --title "Fix tests"
#
# Formats:
#   Plain:     bash scripts/notify-irc.sh "Hello from fleet"
#   Structured: bash scripts/notify-irc.sh --agent <name> --event <EVENT> [--title <text>] [--url <url>]
#     → [<agent>] EVENT: <title> — <url>

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse args
AGENT=""
EVENT=""
TITLE=""
URL=""
PLAIN_MSG=""

if [[ $# -eq 1 && "$1" != --* ]]; then
    PLAIN_MSG="$1"
else
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --agent) AGENT="$2"; shift 2 ;;
            --event) EVENT="$2"; shift 2 ;;
            --title) TITLE="$2"; shift 2 ;;
            --url) URL="$2"; shift 2 ;;
            *) PLAIN_MSG="${PLAIN_MSG:+$PLAIN_MSG }$1"; shift ;;
        esac
    done
fi

# Build message
if [[ -n "$EVENT" ]]; then
    MSG="[$AGENT] $EVENT"
    [[ -n "$TITLE" ]] && MSG="$MSG: $TITLE"
    [[ -n "$URL" ]] && MSG="$MSG — $URL"
elif [[ -n "$PLAIN_MSG" ]]; then
    MSG="$PLAIN_MSG"
else
    echo "Usage: notify-irc.sh \"message\" or --agent <name> --event <EVENT> ..." >&2
    exit 1
fi

# Send via OpenClaw gateway send RPC
python3 << PYEOF
import asyncio, json, uuid
import websockets

async def send_irc():
    with open('$HOME/.openclaw/openclaw.json') as f:
        cfg = json.load(f)
    oc_token = cfg.get('gateway', {}).get('auth', {}).get('token', '')

    try:
        async with websockets.connect('ws://localhost:18789', origin='http://localhost:18789') as ws:
            await asyncio.wait_for(ws.recv(), timeout=5)
            await ws.send(json.dumps({
                'type': 'req', 'id': str(uuid.uuid4()), 'method': 'connect',
                'params': {
                    'minProtocol': 3, 'maxProtocol': 3, 'role': 'operator',
                    'scopes': ['operator.read', 'operator.admin'],
                    'client': {'id': 'openclaw-control-ui', 'version': '1.0.0', 'platform': 'python', 'mode': 'ui'},
                    'auth': {'token': oc_token},
                },
            }))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            if not json.loads(raw).get('ok'):
                print('Gateway connect failed')
                return False

            # Send message to IRC channel via send RPC
            rid = str(uuid.uuid4())
            await ws.send(json.dumps({
                'type': 'req', 'id': rid, 'method': 'send',
                'params': {
                    'channel': 'irc',
                    'to': '#fleet',
                    'message': $(python3 -c "import json; print(json.dumps('''$MSG'''))"),
                    'accountId': 'fleet',
                    'idempotencyKey': str(uuid.uuid4()),
                },
            }))

            while True:
                data = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if data.get('id') == rid:
                    if data.get('ok'):
                        return True
                    else:
                        err = data.get('error', {}).get('message', 'unknown')
                        print(f'Send failed: {err}')
                        return False
    except Exception as e:
        print(f'Error: {e}')
        return False

ok = asyncio.run(send_irc())
if ok:
    print('Sent to #fleet')
PYEOF