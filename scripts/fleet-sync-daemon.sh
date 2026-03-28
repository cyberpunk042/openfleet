#!/usr/bin/env bash
set -euo pipefail

# Fleet sync daemon — runs fleet-sync.sh periodically.
#
# Usage:
#   bash scripts/fleet-sync-daemon.sh              # foreground, 60s interval
#   bash scripts/fleet-sync-daemon.sh --interval 30 # custom interval
#   bash scripts/fleet-sync-daemon.sh &             # background
#
# Stop: kill $(cat .sync.pid) or make sync-stop

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INTERVAL="${1:-60}"
PID_FILE="$FLEET_DIR/.sync.pid"

[[ "$1" == "--interval" ]] && INTERVAL="${2:-60}"

# Check not already running
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Sync daemon already running (PID $OLD_PID)"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

echo "$$" > "$PID_FILE"
trap "rm -f $PID_FILE; exit" INT TERM EXIT

echo "Fleet sync daemon started (PID $$, interval ${INTERVAL}s)"
echo "Watching: task↔PR sync, worktree cleanup, IRC notifications"

while true; do
    bash "$FLEET_DIR/scripts/fleet-sync.sh" 2>&1 | while read -r line; do
        [[ -n "$line" ]] && echo "[$(date +%H:%M:%S)] $line"
    done
    sleep "$INTERVAL"
done