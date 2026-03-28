#!/usr/bin/env bash
set -euo pipefail

# Stop the fleet IRC daemon.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IRC_PID_FILE="$FLEET_DIR/.irc.pid"
IRC_PORT="${FLEET_IRC_PORT:-6667}"

if [[ -f "$IRC_PID_FILE" ]]; then
    PID=$(cat "$IRC_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$IRC_PID_FILE"
        echo "IRC daemon stopped (PID $PID)"
    else
        rm -f "$IRC_PID_FILE"
        echo "IRC daemon not running (stale PID file removed)"
    fi
else
    # Try to find by port
    PID=$(ss -tlnp 2>/dev/null | grep ":${IRC_PORT}" | grep -oP 'pid=\K\d+' | head -1)
    if [[ -n "$PID" ]]; then
        kill "$PID" 2>/dev/null
        echo "IRC daemon stopped (PID $PID)"
    else
        echo "IRC daemon not running"
    fi
fi