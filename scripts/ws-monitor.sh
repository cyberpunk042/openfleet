#!/usr/bin/env bash
set -euo pipefail

# Monitor OpenClaw gateway events in real-time.
#
# Usage:
#   bash scripts/ws-monitor.sh                    # all sessions
#   bash scripts/ws-monitor.sh --agent architect   # filter by agent
#   bash scripts/ws-monitor.sh --sessions          # just list sessions and exit
#
# Shows: session changes, agent messages, tool calls, errors.
# Ctrl+C to stop.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

AGENT_FILTER=""
LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent) AGENT_FILTER="$2"; shift 2 ;;
        --sessions) LIST_ONLY=true; shift ;;
        *) shift ;;
    esac
done

python3 << PYEOF
import asyncio, json, uuid, sys, signal
from datetime import datetime
import websockets

AGENT_FILTER = "$AGENT_FILTER"
LIST_ONLY = $( [[ "$LIST_ONLY" == "true" ]] && echo "True" || echo "False" )

COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'red': '\033[31m',
}

def c(color, text):
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def now():
    return datetime.now().strftime('%H:%M:%S')

async def monitor():
    with open('$VENDOR_CONFIG_FILE') as f:
        cfg = json.load(f)
    oc_token = cfg.get('gateway', {}).get('auth', {}).get('token', '')

    async with websockets.connect('ws://localhost:18789', origin='http://localhost:18789') as ws:
        # Connect
        await asyncio.wait_for(ws.recv(), timeout=5)
        await ws.send(json.dumps({
            'type': 'req', 'id': str(uuid.uuid4()), 'method': 'connect',
            'params': {
                'minProtocol': 3, 'maxProtocol': 3, 'role': 'operator',
                'scopes': ['operator.read', 'operator.admin'],
                'client': {'id': '${VENDOR_CLI}-control-ui', 'version': '1.0.0', 'platform': 'python', 'mode': 'ui'},
                'auth': {'token': oc_token},
            },
        }))
        raw = await asyncio.wait_for(ws.recv(), timeout=5)
        if not json.loads(raw).get('ok'):
            print('Connect failed')
            return

        # List sessions
        rid = str(uuid.uuid4())
        await ws.send(json.dumps({'type': 'req', 'id': rid, 'method': 'sessions.list', 'params': {}}))
        sessions = []
        while True:
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if resp.get('id') == rid:
                sessions = resp.get('payload', {}).get('sessions', [])
                break

        if LIST_ONLY:
            print(f"{c('bold', 'Sessions')} ({len(sessions)})")
            for s in sessions:
                key = s.get('key', '?')
                label = s.get('label', '') or '(no label)'
                print(f"  {key:55s} {c('cyan', label)}")
            return

        # Subscribe to all sessions
        rid = str(uuid.uuid4())
        await ws.send(json.dumps({'type': 'req', 'id': rid, 'method': 'sessions.subscribe', 'params': {}}))
        await asyncio.wait_for(ws.recv(), timeout=5)

        # Also subscribe to individual session messages
        for s in sessions:
            key = s.get('key', '')
            if AGENT_FILTER and AGENT_FILTER not in key and AGENT_FILTER not in (s.get('label') or ''):
                continue
            rid = str(uuid.uuid4())
            await ws.send(json.dumps({
                'type': 'req', 'id': rid,
                'method': 'sessions.messages.subscribe',
                'params': {'key': key},
            }))
            try:
                await asyncio.wait_for(ws.recv(), timeout=3)
            except asyncio.TimeoutError:
                pass

        filter_label = f" (filter: {AGENT_FILTER})" if AGENT_FILTER else ""
        print(f"{c('bold', '=== Fleet Monitor ===' )}{filter_label}")
        print(f"Watching {len(sessions)} sessions. Ctrl+C to stop.")
        print()

        # Listen for events
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(raw)

                event_type = data.get('event', data.get('type', ''))
                payload = data.get('payload', {})

                if event_type == 'sessions.changed':
                    key = payload.get('sessionKey', '?')
                    reason = payload.get('reason', '')
                    if AGENT_FILTER and AGENT_FILTER not in key:
                        continue
                    agent = key.split(':')[1] if ':' in key else key
                    print(f"[{c('dim', now())}] {c('yellow', 'session')} {agent} → {reason}")

                elif event_type == 'sessions.message':
                    key = payload.get('sessionKey', '?')
                    if AGENT_FILTER and AGENT_FILTER not in key:
                        continue
                    agent = key.split(':')[1] if ':' in key else key
                    msg = payload.get('message', {})
                    role = msg.get('role', '?')
                    content = msg.get('content', [])

                    if role == 'assistant':
                        for block in (content if isinstance(content, list) else []):
                            if block.get('type') == 'text':
                                text = block['text'][:200]
                                print(f"[{c('dim', now())}] {c('green', agent)} {text}")
                            elif block.get('type') in ('toolCall', 'toolUse'):
                                tool = block.get('toolName', block.get('name', '?'))
                                print(f"[{c('dim', now())}] {c('cyan', agent)} → {c('magenta', tool)}")
                    elif role == 'toolResult':
                        for block in (content if isinstance(content, list) else []):
                            if block.get('type') == 'text':
                                text = block['text'][:100]
                                is_err = block.get('isError', False)
                                color = 'red' if is_err else 'dim'
                                print(f"[{c('dim', now())}] {c(color, '  result')} {text}")

                elif event_type == 'agent.event':
                    evt = payload.get('event', '')
                    agent_id = payload.get('agentId', '')
                    if evt in ('start', 'end', 'error'):
                        color = 'green' if evt == 'start' else 'red' if evt == 'error' else 'yellow'
                        print(f"[{c('dim', now())}] {c('bold', 'agent')} {c(color, evt)} {agent_id}")

                elif event_type == 'health':
                    pass  # ignore health pings

                elif data.get('type') == 'res':
                    pass  # ignore RPC responses

                else:
                    if event_type:
                        print(f"[{c('dim', now())}] {c('dim', event_type)}")

            except asyncio.TimeoutError:
                print(f"[{c('dim', now())}] {c('dim', '... waiting')}")

try:
    asyncio.run(monitor())
except KeyboardInterrupt:
    print("\nMonitor stopped.")
PYEOF