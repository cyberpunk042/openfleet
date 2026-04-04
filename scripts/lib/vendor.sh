#!/usr/bin/env bash
# vendor.sh — Resolve which gateway vendor is installed (openarms preferred over openclaw).
# Source this file from any fleet script: source "$FLEET_DIR/scripts/lib/vendor.sh"
#
# After sourcing, these variables are set:
#   VENDOR_CLI          — "openarms" or "openclaw"
#   VENDOR_NAME         — "OpenArms" or "OpenClaw"
#   VENDOR_CONFIG_DIR   — ~/.openarms or ~/.openclaw
#   VENDOR_CONFIG_FILE  — ~/.openarms/openarms.json or ~/.openclaw/openclaw.json
#   VENDOR_ENV_FILE     — ~/.openarms/.env or ~/.openclaw/.env

if command -v openarms >/dev/null 2>&1; then
    VENDOR_CLI="openarms"
    VENDOR_NAME="OpenArms"
    VENDOR_CONFIG_DIR="${HOME}/.openarms"
    VENDOR_CONFIG_FILE="${VENDOR_CONFIG_DIR}/openarms.json"
    VENDOR_ENV_FILE="${VENDOR_CONFIG_DIR}/.env"
    VENDOR_LEGACY_CLI="openclaw"
    VENDOR_LEGACY_CONFIG_DIR="${HOME}/.openclaw"
    VENDOR_LEGACY_CONFIG_FILE="${VENDOR_LEGACY_CONFIG_DIR}/openclaw.json"
    VENDOR_LEGACY_ENV_FILE="${VENDOR_LEGACY_CONFIG_DIR}/.env"
elif command -v openclaw >/dev/null 2>&1; then
    VENDOR_CLI="openclaw"
    VENDOR_NAME="OpenClaw"
    VENDOR_CONFIG_DIR="${HOME}/.openclaw"
    VENDOR_CONFIG_FILE="${VENDOR_CONFIG_DIR}/openclaw.json"
    VENDOR_ENV_FILE="${VENDOR_CONFIG_DIR}/.env"
    VENDOR_LEGACY_CLI=""
    VENDOR_LEGACY_CONFIG_DIR=""
    VENDOR_LEGACY_CONFIG_FILE=""
    VENDOR_LEGACY_ENV_FILE=""
else
    echo "ERROR: Neither openarms nor openclaw found in PATH" >&2
    VENDOR_CLI=""
    VENDOR_NAME=""
    VENDOR_CONFIG_DIR=""
    VENDOR_CONFIG_FILE=""
    VENDOR_ENV_FILE=""
    VENDOR_LEGACY_CLI=""
    VENDOR_LEGACY_CONFIG_DIR=""
    VENDOR_LEGACY_CONFIG_FILE=""
    VENDOR_LEGACY_ENV_FILE=""
fi

# --- Cutover: migrate from legacy vendor if switching ---
# If openarms is active and legacy openclaw config exists but openarms config doesn't,
# migrate the config so we don't have to re-onboard.
_vendor_cutover() {
    [[ "$VENDOR_CLI" == "openarms" ]] || return 0
    [[ -f "${VENDOR_LEGACY_CONFIG_FILE}" ]] || return 0
    [[ -f "${VENDOR_CONFIG_FILE}" ]] && return 0  # already migrated

    echo "  Migrating config from ${VENDOR_LEGACY_CONFIG_DIR} to ${VENDOR_CONFIG_DIR}..."
    mkdir -p "$VENDOR_CONFIG_DIR"

    # Copy config, replacing "openclaw" paths/names
    sed 's/\.openclaw/\.openarms/g; s/openclaw\.json/openarms.json/g' \
        "$VENDOR_LEGACY_CONFIG_FILE" > "$VENDOR_CONFIG_FILE"

    # Copy env file if it exists
    if [[ -f "$VENDOR_LEGACY_ENV_FILE" ]]; then
        cp "$VENDOR_LEGACY_ENV_FILE" "$VENDOR_ENV_FILE"
    fi

    # Copy identity if it exists (device keypair — same machine, reuse it)
    if [[ -d "${VENDOR_LEGACY_CONFIG_DIR}/identity" ]]; then
        cp -r "${VENDOR_LEGACY_CONFIG_DIR}/identity" "${VENDOR_CONFIG_DIR}/identity"
    fi

    echo "  Config migrated. Legacy config preserved at ${VENDOR_LEGACY_CONFIG_DIR}"
}

# --- Cutover: stop legacy gateway if switching ---
_vendor_stop_legacy() {
    [[ "$VENDOR_CLI" == "openarms" ]] || return 0
    [[ -n "$VENDOR_LEGACY_CLI" ]] || return 0

    # Stop legacy systemd service
    if systemctl --user is-active openclaw-fleet-gateway.service >/dev/null 2>&1; then
        echo "  Stopping legacy openclaw systemd service..."
        systemctl --user stop openclaw-fleet-gateway.service 2>/dev/null || true
    fi

    # Kill legacy gateway processes
    if pgrep -f "openclaw gateway" >/dev/null 2>&1; then
        echo "  Killing legacy openclaw gateway..."
        pkill -f "openclaw gateway" 2>/dev/null || true
    fi
    if pgrep -f "openclaw$" >/dev/null 2>&1; then
        pkill -f "openclaw$" 2>/dev/null || true
    fi
}
