#!/usr/bin/env bash
set -euo pipefail

# Start the OpenClaw gateway.
# Must run before Mission Control connects.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Starting OpenClaw Gateway ==="

# Check if already running
if pgrep -f "openclaw-gateway" >/dev/null 2>&1; then
    echo "  Gateway already running"
    exit 0
fi

# Start gateway in background
openclaw gateway run --port 18789 &
GATEWAY_PID=$!

# Wait for it to be ready
echo "  Waiting for gateway..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:18789/ >/dev/null 2>&1; then
        echo "  Gateway ready (PID: $GATEWAY_PID)"
        exit 0
    fi
    sleep 2
done

echo "  WARNING: Gateway may not be ready yet. Check: curl http://localhost:18789/"