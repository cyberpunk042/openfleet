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
TEMPLATE="$FLEET_DIR/systemd/fleet-gateway.service.template"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "ERROR: Template not found: $TEMPLATE" >&2
    exit 1
fi

# Resolve paths for this machine — find stable bin directory.
# fnm creates ephemeral shell directories (/run/user/.../fnm_multishells/NNN_*)
# that disappear when the terminal closes. The service needs a stable path.
VENDOR_BIN=$(command -v "$VENDOR_CLI" 2>/dev/null || echo "")
if [[ -z "$VENDOR_BIN" ]]; then
    echo "ERROR: $VENDOR_NAME not found in PATH" >&2
    exit 1
fi
# If the binary is in an fnm_multishells ephemeral dir, resolve to the
# stable fnm installation dir (e.g. ~/.local/share/fnm/node-versions/.../bin/).
VENDOR_BIN_DIR=$(dirname "$VENDOR_BIN")
if [[ "$VENDOR_BIN_DIR" == *fnm_multishells* ]]; then
    NODE_VER=$(node --version 2>/dev/null || true)
    FNM_STABLE="$HOME/.local/share/fnm/node-versions/$NODE_VER/installation/bin"
    if [[ -n "$NODE_VER" && -x "$FNM_STABLE/$VENDOR_CLI" ]]; then
        VENDOR_BIN="$FNM_STABLE/$VENDOR_CLI"
        VENDOR_BIN_DIR="$FNM_STABLE"
    fi
fi

echo "=== Installing $VENDOR_NAME Fleet Service ==="
echo "  Fleet dir:    $FLEET_DIR"
echo "  $VENDOR_NAME bin: $VENDOR_BIN"
echo "  User:         $USER"
echo "  Home:         $HOME"

# Render template
SERVICE_DIR="${HOME}/.config/systemd/user"
mkdir -p "$SERVICE_DIR"
SERVICE_FILE="$SERVICE_DIR/fleet-gateway.service"

sed \
    -e "s|{{FLEET_DIR}}|$FLEET_DIR|g" \
    -e "s|{{VENDOR_BIN_DIR}}|$VENDOR_BIN_DIR|g" \
    -e "s|{{VENDOR_BIN}}|$VENDOR_BIN|g" \
    -e "s|{{HOME}}|$HOME|g" \
    "$TEMPLATE" > "$SERVICE_FILE"

echo "  Service file: $SERVICE_FILE"

# Enable and start
systemctl --user daemon-reload
systemctl --user enable fleet-gateway.service
echo ""
echo "Service installed and enabled."
echo ""
echo "Commands:"
echo "  systemctl --user start fleet-gateway    # start now"
echo "  systemctl --user stop fleet-gateway     # stop"
echo "  systemctl --user status fleet-gateway   # check status"
echo "  journalctl --user -u fleet-gateway -f   # view logs"
echo ""
echo "To auto-start on login: loginctl enable-linger $USER"