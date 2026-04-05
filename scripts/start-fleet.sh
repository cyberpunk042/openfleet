#!/usr/bin/env bash
set -euo pipefail

# Start the gateway.
# Kills any existing gateway first (clean restart).
# Must run before Mission Control connects.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

# Load config
source "$FLEET_DIR/.env" 2>/dev/null || true
GW_PORT="18789"

# SAFETY: Check if fleet is paused. If paused, refuse to start.
# Use "fleet resume" first, then start.
if [ -f "$FLEET_DIR/.fleet-paused" ]; then
    echo "ERROR: Fleet is PAUSED. Cannot start gateway."
    echo "  Reason: $(cat "$FLEET_DIR/.fleet-paused")"
    echo "  Run 'python -m fleet resume' first."
    exit 1
fi

# SAFETY: Check if MC is reachable. If MC is down, refuse to start.
# Starting the gateway without MC causes cron jobs to fire Claude
# calls with no MC to serve — burning tokens for nothing.
MC_PORT="${BACKEND_PORT:-8000}"
if ! curl -sf "http://localhost:${MC_PORT}/health" >/dev/null 2>&1; then
    echo "ERROR: MC backend is not reachable (localhost:${MC_PORT})."
    echo "  Start MC first: docker compose up -d"
    echo "  Then: make gateway"
    exit 1
fi

echo "=== Starting $VENDOR_NAME Gateway ==="

# Stop legacy vendor if switching from openclaw to openarms
_vendor_stop_legacy

# Unmask in case teardown left it masked
systemctl --user unmask fleet-gateway.service 2>/dev/null || true

# Disable legacy service (Restart=always causes storms)
systemctl --user stop openclaw-fleet-gateway.service 2>/dev/null || true
systemctl --user disable openclaw-fleet-gateway.service 2>/dev/null || true

# Stop systemd-managed gateway if running (it would respawn after kill)
if systemctl --user is-active fleet-gateway.service >/dev/null 2>&1; then
    echo "  Stopping systemd gateway service..."
    systemctl --user stop fleet-gateway.service 2>/dev/null || true
    sleep 2
fi

# Kill existing gateway processes (avoid duplicates — check both vendors)
for proc_pattern in "openarms gateway" "openclaw gateway" "openarms$" "openclaw$"; do
    if pgrep -f "$proc_pattern" >/dev/null 2>&1; then
        echo "  Killing $proc_pattern..."
        pkill -f "$proc_pattern" 2>/dev/null || true
    fi
done
sleep 2

# Kill anything else occupying the gateway port
PORT_PID=$(lsof -ti :"$GW_PORT" 2>/dev/null || true)
if [[ -n "$PORT_PID" ]]; then
    echo "  Killing process on port $GW_PORT (PID: $PORT_PID)..."
    kill $PORT_PID 2>/dev/null || true
    sleep 2
    # Force kill if still alive
    if lsof -ti :"$GW_PORT" >/dev/null 2>&1; then
        kill -9 $PORT_PID 2>/dev/null || true
        sleep 1
    fi
fi

# Install/update systemd service if template exists, then start via systemd
if [[ -f "$FLEET_DIR/systemd/fleet-gateway.service.template" ]]; then
    bash "$FLEET_DIR/scripts/install-service.sh" 2>&1 | sed 's/^/  /'
    echo "  Starting via systemd..."
    systemctl --user start fleet-gateway.service
else
    # Fallback: start directly if no systemd template
    export NODE_OPTIONS="--max-old-space-size=4096"
    nohup $VENDOR_CLI gateway run --port "$GW_PORT" > "$FLEET_DIR/.gateway.log" 2>&1 &
    disown
fi

# Wait for it to be ready
echo "  Waiting for gateway..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${GW_PORT}/health" >/dev/null 2>&1; then
        echo "  Gateway ready on port $GW_PORT"
        exit 0
    fi
    sleep 2
done

echo "  ERROR: Gateway failed to start within 60 seconds."
if systemctl --user is-active fleet-gateway.service >/dev/null 2>&1; then
    echo "  Check logs: journalctl --user -u fleet-gateway -n 50"
else
    echo "  Check logs: tail -50 $FLEET_DIR/.gateway.log"
fi
exit 1