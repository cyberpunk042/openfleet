#!/usr/bin/env bash
set -euo pipefail

# Teardown — stop everything cleanly for a fresh setup.
# Stops all processes, disables cron jobs, kills agent sessions.
# Usage: bash scripts/teardown.sh

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

echo "=== Fleet Teardown ==="

# 1. Fleet daemons
echo "1. Stopping fleet daemons..."
pkill -f "fleet daemon" 2>/dev/null && echo "   Killed" || echo "   None running"

# 2. MCP servers
echo "2. Stopping MCP servers..."
pkill -f "fleet.mcp.server" 2>/dev/null && echo "   Killed" || echo "   None running"

# 3. Disable CRON jobs (prevent heartbeats from firing)
echo "3. Disabling gateway CRON jobs..."
if [[ -n "$VENDOR_CONFIG_DIR" ]]; then
    CRON_FILE="$VENDOR_CONFIG_DIR/cron/jobs.json"
    if [[ -f "$CRON_FILE" ]]; then
        python3 -c "
import json
with open('$CRON_FILE') as f:
    data = json.load(f)
disabled = 0
for j in data.get('jobs', []):
    if j.get('enabled'):
        j['enabled'] = False
        disabled += 1
if disabled:
    with open('$CRON_FILE', 'w') as f:
        json.dump(data, f, indent=2)
print(f'   Disabled {disabled} cron jobs')
" 2>/dev/null || echo "   WARN: Could not disable cron jobs"
    else
        echo "   No cron jobs file"
    fi
fi

# 4. Mask + stop gateway systemd services
#    mask is the ONLY way to prevent Restart=always from respawning after pkill.
#    disable only prevents auto-start at login — it does NOT stop restart loops.
echo "4. Stopping gateway services..."
for svc in fleet-gateway openclaw-fleet-gateway; do
    systemctl --user mask "$svc" 2>/dev/null || true
    systemctl --user stop "$svc" 2>/dev/null && echo "   Stopped $svc" || true
    systemctl --user reset-failed "$svc" 2>/dev/null || true
done
systemctl --user daemon-reload 2>/dev/null || true

# 5. Kill ALL gateway processes (both vendors)
echo "5. Killing gateway processes..."
for pattern in "openarms-gateway" "openclaw-gateway" "openarms gateway" "openclaw gateway"; do
    pkill -f "$pattern" 2>/dev/null && echo "   Killed $pattern" || true
done
sleep 2
# SIGKILL stragglers — mask prevents systemd from restarting them
for pattern in "openarms-gateway" "openclaw-gateway" "openarms gateway" "openclaw gateway"; do
    pkill -9 -f "$pattern" 2>/dev/null || true
done

# 5b. Kill anything on vendor gateway port (18789) and OCF gateway port (9400)
for GW_PORT in 18789 9400; do
    PORT_PID=$(lsof -ti :"$GW_PORT" 2>/dev/null || true)
    if [[ -n "$PORT_PID" ]]; then
        echo "   Killing PID $PORT_PID on port $GW_PORT"
        kill -9 $PORT_PID 2>/dev/null || true
    fi
done

# 6. Stop Docker containers
echo "6. Stopping Docker containers..."
cd "$FLEET_DIR"
docker compose down 2>/dev/null && echo "   Down" || echo "   None running"

# 7. Stop IRC
echo "7. Stopping IRC..."
pkill -f "miniircd" 2>/dev/null && echo "   Killed" || echo "   None running"

# 8. Stop stale syncs
echo "8. Stopping stale LightRAG syncs..."
pkill -f "setup-lightrag" 2>/dev/null && echo "   Killed" || echo "   None running"

# 9. Remove pause marker (fresh start)
echo "9. Cleaning state..."
rm -f "$FLEET_DIR/.fleet-paused" && echo "   Removed pause marker" || true
rm -f "$FLEET_DIR/.gateway-starting" && echo "   Removed gateway lock" || true

# 10. Unmask services so setup.sh can re-enable them
echo "10. Unmasking services for next setup..."
for svc in fleet-gateway openclaw-fleet-gateway; do
    systemctl --user unmask "$svc" 2>/dev/null || true
done
systemctl --user daemon-reload 2>/dev/null || true

# 11. Remove stale legacy service file (install-service.sh only creates fleet-gateway)
LEGACY_SVC="$HOME/.config/systemd/user/openclaw-fleet-gateway.service"
if [[ -f "$LEGACY_SVC" ]]; then
    rm -f "$LEGACY_SVC"
    echo "   Removed stale legacy service file"
    systemctl --user daemon-reload 2>/dev/null || true
fi

# 12. Verify nothing left
echo ""
echo "=== Verification ==="
REMAINING=$(pgrep -af 'openarms|openclaw|fleet daemon|fleet.mcp|miniircd' 2>/dev/null | grep -v grep | grep -v teardown | grep -v pgrep || true)
if [[ -n "$REMAINING" ]]; then
    echo "WARNING: Some processes still running:"
    echo "$REMAINING"
else
    echo "All fleet processes stopped."
fi

CONTAINERS=$(docker ps --format '{{.Names}}' 2>/dev/null | grep 'openclaw-fleet\|mission-control' || true)
if [[ -n "$CONTAINERS" ]]; then
    echo "WARNING: Some containers still running:"
    echo "$CONTAINERS"
else
    echo "All fleet containers stopped."
fi

echo ""
echo "=== Teardown Complete ==="
echo "CRON jobs disabled. Gateway masked+stopped. Containers down. Legacy service removed."
echo "Run ./setup.sh for a fresh start."
