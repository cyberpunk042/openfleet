#!/usr/bin/env bash
set -euo pipefail

# Fleet operations monitor — checks board state and posts alerts.
# Runs periodically alongside fleet-sync-daemon.
#
# Checks:
#   - Stale tasks (inbox > 1h, in_progress > 8h no comment, review > 24h)
#   - Offline agents
#   - Unmerged PRs > 48h
#   - Unresolved blockers in board memory
#
# Usage:
#   bash scripts/fleet-monitor-daemon.sh           # foreground, 300s interval
#   bash scripts/fleet-monitor-daemon.sh &          # background

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

INTERVAL="${FLEET_MONITOR_INTERVAL:-300}"
PID_FILE="$FLEET_DIR/.monitor.pid"

[[ "${1:-}" == "--interval" ]] && INTERVAL="${2:-300}"

if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Monitor already running (PID $OLD_PID)"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

echo "$$" > "$PID_FILE"
trap "rm -f $PID_FILE; exit" INT TERM EXIT

echo "Fleet monitor started (PID $$, interval ${INTERVAL}s)"

while true; do
    bash "$FLEET_DIR/scripts/fleet-monitor-check.sh" 2>&1 | while read -r line; do
        [[ -n "$line" ]] && echo "[$(date +%H:%M:%S)] $line"
    done
    sleep "$INTERVAL"
done