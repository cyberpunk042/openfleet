#!/usr/bin/env bash
set -euo pipefail

# Teardown — stop everything cleanly for a fresh setup.
#
# Usage:
#   bash scripts/teardown.sh          # Stop all processes, disable cron, clean state
#   bash scripts/teardown.sh --full   # + remove vendor configs, systemd units, npm globals, docker images

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

FULL=false
[[ "${1:-}" == "--full" ]] && FULL=true

if $FULL; then
    echo "=== Fleet FULL Teardown (processes + vendor + systemd + docker images) ==="
else
    echo "=== Fleet Teardown ==="
fi

# ── 1. Mask systemd services FIRST ─────────────────────────────────────────
#    mask is the ONLY way to prevent Restart=always from respawning after pkill.
#    disable only prevents auto-start at login — it does NOT stop restart loops.
#    We do this BEFORE killing anything so kills don't trigger restarts.
echo "1. Masking gateway services..."
for svc in fleet-gateway openclaw-fleet-gateway; do
    systemctl --user mask "$svc" 2>/dev/null && echo "   Masked $svc" || true
done

# ── 2. Stop systemd services ───────────────────────────────────────────────
echo "2. Stopping gateway services..."
for svc in fleet-gateway openclaw-fleet-gateway; do
    systemctl --user stop "$svc" 2>/dev/null && echo "   Stopped $svc" || true
    systemctl --user reset-failed "$svc" 2>/dev/null || true
done
systemctl --user daemon-reload 2>/dev/null || true

# ── 3. Disable CRON jobs (prevent heartbeats from firing) ──────────────────
echo "3. Disabling gateway CRON jobs..."
for vendor_dir in "$HOME/.openarms" "$HOME/.openclaw"; do
    CRON_FILE="$vendor_dir/cron/jobs.json"
    if [[ -f "$CRON_FILE" ]]; then
        python3 -c "
import json, sys
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
print(f'   Disabled {disabled} cron jobs in $CRON_FILE')
" 2>/dev/null || true
    fi
done

# ── 4. Kill fleet daemons and MCP servers ──────────────────────────────────
echo "4. Stopping fleet daemons and MCP servers..."
pkill -f "fleet daemon" 2>/dev/null && echo "   Killed fleet daemons" || true
pkill -f "fleet.mcp.server" 2>/dev/null && echo "   Killed MCP servers" || true

# ── 5. Kill ALL gateway processes (both vendors) ──────────────────────────
echo "5. Killing gateway processes..."
for pattern in "openarms-gateway" "openclaw-gateway" "openarms gateway" "openclaw gateway"; do
    pkill -f "$pattern" 2>/dev/null && echo "   Killed: $pattern" || true
done
sleep 2
# SIGKILL stragglers — mask prevents systemd from restarting them
for pattern in "openarms-gateway" "openclaw-gateway" "openarms gateway" "openclaw gateway"; do
    pkill -9 -f "$pattern" 2>/dev/null || true
done

# ── 6. Kill anything on gateway ports ──────────────────────────────────────
#    Vendor gateway = 18789, OCF Python gateway = 9400. Kill both.
echo "6. Clearing gateway ports..."
for port in 18789 9400; do
    PORT_PID=$(lsof -ti :"$port" 2>/dev/null || true)
    if [[ -n "$PORT_PID" ]]; then
        echo "   Killing PID $PORT_PID on port $port"
        kill -9 $PORT_PID 2>/dev/null || true
    fi
done

# ── 7. Stop Docker containers ─────────────────────────────────────────────
echo "7. Stopping Docker containers..."
cd "$FLEET_DIR"
if $FULL; then
    docker compose down --volumes --rmi local 2>/dev/null && echo "   Down + volumes + images removed" || echo "   None running"
else
    docker compose down 2>/dev/null && echo "   Down" || echo "   None running"
fi

# ── 8. Stop IRC ───────────────────────────────────────────────────────────
echo "8. Stopping IRC..."
pkill -f "miniircd" 2>/dev/null && echo "   Killed" || echo "   None running"

# ── 9. Stop stale syncs ───────────────────────────────────────────────────
echo "9. Stopping stale LightRAG syncs..."
pkill -f "setup-lightrag" 2>/dev/null && echo "   Killed" || echo "   None running"

# ── 10. Clean state markers ───────────────────────────────────────────────
echo "10. Cleaning state..."
rm -f "$FLEET_DIR/.fleet-paused" && echo "   Removed pause marker" || true
rm -f "$FLEET_DIR/.gateway-starting" && echo "   Removed gateway lock" || true

# ── 11. Unmask / remove systemd services ──────────────────────────────────
if $FULL; then
    echo "11. Removing ALL systemd service files..."
    for svc in fleet-gateway openclaw-fleet-gateway; do
        systemctl --user unmask "$svc" 2>/dev/null || true
        systemctl --user disable "$svc" 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/$svc.service" && echo "   Removed $svc.service" || true
    done
    systemctl --user daemon-reload 2>/dev/null || true
else
    echo "11. Unmasking services for next setup..."
    for svc in fleet-gateway openclaw-fleet-gateway; do
        systemctl --user unmask "$svc" 2>/dev/null || true
    done
    # Always remove the stale legacy service (install-service.sh only creates fleet-gateway)
    if [[ -f "$HOME/.config/systemd/user/openclaw-fleet-gateway.service" ]]; then
        rm -f "$HOME/.config/systemd/user/openclaw-fleet-gateway.service"
        echo "   Removed stale legacy service file"
    fi
    systemctl --user daemon-reload 2>/dev/null || true
fi

# ── 12. Full: remove vendor config directories ───────────────────────────
if $FULL; then
    echo "12. Removing vendor config directories..."
    for vendor_dir in "$HOME/.openarms" "$HOME/.openclaw"; do
        if [[ -d "$vendor_dir" ]]; then
            rm -rf "$vendor_dir"
            echo "   Removed $vendor_dir"
        fi
    done

    echo "13. Uninstalling vendor npm packages..."
    npm uninstall -g openarms 2>/dev/null && echo "   Uninstalled openarms" || echo "   openarms not installed"
    npm uninstall -g openclaw 2>/dev/null && echo "   Uninstalled openclaw" || echo "   openclaw not installed"

    echo "14. Cleaning vendor temp files..."
    rm -rf /tmp/openarms /tmp/openclaw 2>/dev/null && echo "   Cleaned /tmp" || true
fi

# ── Verify ────────────────────────────────────────────────────────────────
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

if $FULL; then
    echo ""
    # Verify vendor is gone
    for vendor_dir in "$HOME/.openarms" "$HOME/.openclaw"; do
        if [[ -d "$vendor_dir" ]]; then
            echo "WARNING: $vendor_dir still exists"
        fi
    done
    for cmd in openarms openclaw; do
        if command -v "$cmd" >/dev/null 2>&1; then
            echo "WARNING: $cmd still in PATH: $(command -v "$cmd")"
        fi
    done
fi

echo ""
if $FULL; then
    echo "=== FULL Teardown Complete ==="
    echo "Processes killed. CRON disabled. Services removed. Vendor wiped. Docker images removed."
    echo "Run ./setup.sh for a clean install from scratch."
else
    echo "=== Teardown Complete ==="
    echo "Processes killed. CRON disabled. Services stopped. State cleaned."
    echo "Run ./setup.sh for a fresh start."
fi
