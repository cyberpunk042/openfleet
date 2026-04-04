#!/usr/bin/env bash
set -euo pipefail

# Install the OpenClaw Fleet gateway as a systemd user service.
# Renders the template with paths from the current machine.
#
# Usage: bash scripts/install-service.sh
#
# Installs as a user service (no sudo needed for --user).
# To use as a system service, run with sudo and adjust paths.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"
TEMPLATE="$FLEET_DIR/systemd/openclaw-fleet-gateway.service.template"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "ERROR: Template not found: $TEMPLATE" >&2
    exit 1
fi

# Resolve paths for this machine
VENDOR_BIN=$(command -v "$VENDOR_CLI" 2>/dev/null || echo "")
if [[ -z "$VENDOR_BIN" ]]; then
    echo "ERROR: $VENDOR_NAME not found in PATH" >&2
    exit 1
fi
VENDOR_BIN_DIR=$(dirname "$VENDOR_BIN")

echo "=== Installing OpenClaw Fleet Service ==="
echo "  Fleet dir:    $FLEET_DIR"
echo "  $VENDOR_NAME bin: $VENDOR_BIN"
echo "  User:         $USER"
echo "  Home:         $HOME"

# Render template
SERVICE_DIR="${HOME}/.config/systemd/user"
mkdir -p "$SERVICE_DIR"
SERVICE_FILE="$SERVICE_DIR/openclaw-fleet-gateway.service"

sed \
    -e "s|{{FLEET_DIR}}|$FLEET_DIR|g" \
    -e "s|{{VENDOR_BIN_DIR}}|$VENDOR_BIN_DIR|g" \
    -e "s|{{VENDOR_BIN}}|$VENDOR_BIN|g" \
    -e "s|{{HOME}}|$HOME|g" \
    "$TEMPLATE" > "$SERVICE_FILE"

echo "  Service file: $SERVICE_FILE"

# Enable and start
systemctl --user daemon-reload
systemctl --user enable openclaw-fleet-gateway.service
echo ""
echo "Service installed and enabled."
echo ""
echo "Commands:"
echo "  systemctl --user start openclaw-fleet-gateway    # start now"
echo "  systemctl --user stop openclaw-fleet-gateway     # stop"
echo "  systemctl --user status openclaw-fleet-gateway   # check status"
echo "  journalctl --user -u openclaw-fleet-gateway -f   # view logs"
echo ""
echo "To auto-start on login: loginctl enable-linger $USER"