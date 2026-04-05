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
    # If openarms config exists, it's the legacy vendor (switched back)
    if [[ -f "${HOME}/.openarms/openarms.json" ]]; then
        VENDOR_LEGACY_CLI="openarms"
        VENDOR_LEGACY_CONFIG_DIR="${HOME}/.openarms"
        VENDOR_LEGACY_CONFIG_FILE="${VENDOR_LEGACY_CONFIG_DIR}/openarms.json"
        VENDOR_LEGACY_ENV_FILE="${VENDOR_LEGACY_CONFIG_DIR}/.env"
    else
        VENDOR_LEGACY_CLI=""
        VENDOR_LEGACY_CONFIG_DIR=""
        VENDOR_LEGACY_CONFIG_FILE=""
        VENDOR_LEGACY_ENV_FILE=""
    fi
else
    # No vendor installed yet — this is normal during first setup.
    # Callers check $VENDOR_CLI being empty to decide whether to install.
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
    [[ -n "$VENDOR_LEGACY_CONFIG_DIR" ]] || return 0
    [[ -f "${VENDOR_LEGACY_CONFIG_FILE}" ]] || return 0
    [[ -f "${VENDOR_CONFIG_FILE}" ]] && return 0  # already migrated

    echo "  Migrating config from ${VENDOR_LEGACY_CONFIG_DIR} to ${VENDOR_CONFIG_DIR}..."
    mkdir -p "$VENDOR_CONFIG_DIR"

    # Determine sed replacement based on direction
    local from_name to_name
    if [[ "$VENDOR_CLI" == "openarms" ]]; then
        from_name="openclaw"; to_name="openarms"
    else
        from_name="openarms"; to_name="openclaw"
    fi

    # Copy config, replacing vendor paths/names
    sed "s/\.${from_name}/\.${to_name}/g; s/${from_name}\.json/${to_name}.json/g" \
        "$VENDOR_LEGACY_CONFIG_FILE" > "$VENDOR_CONFIG_FILE"

    # Copy env file if it exists
    if [[ -f "$VENDOR_LEGACY_ENV_FILE" ]]; then
        cp "$VENDOR_LEGACY_ENV_FILE" "$VENDOR_ENV_FILE"
    fi

    # Copy identity if it exists (device keypair — same machine, reuse it)
    if [[ -d "${VENDOR_LEGACY_CONFIG_DIR}/identity" ]]; then
        cp -r "${VENDOR_LEGACY_CONFIG_DIR}/identity" "${VENDOR_CONFIG_DIR}/identity"
    fi

    # BUDGET PROTECTION: Do NOT copy legacy cron jobs — they have stale agent IDs
    # from previous installs. The gateway template sync creates fresh cron jobs
    # with current agent IDs. Only disable legacy cron to prevent budget leak.
    if [[ -d "${VENDOR_LEGACY_CONFIG_DIR}/cron" ]]; then
        # Disable ALL legacy cron jobs (do NOT copy them to new vendor)
        if [[ -f "${VENDOR_LEGACY_CONFIG_DIR}/cron/jobs.json" ]]; then
            python3 -c "
import json
p = '${VENDOR_LEGACY_CONFIG_DIR}/cron/jobs.json'
with open(p) as f: data = json.load(f)
for j in data.get('jobs', []): j['enabled'] = False
with open(p, 'w') as f: json.dump(data, f, indent=2)
" 2>/dev/null || true
        fi
    fi

    echo "  Config migrated. Legacy cron disabled. Legacy config preserved at ${VENDOR_LEGACY_CONFIG_DIR}"
}

# --- Cutover: stop and disable legacy gateway if switching ---
# BUDGET PROTECTION: Must disable legacy cron jobs AND kill processes.
# Leaving legacy cron enabled = heartbeats fire = Claude API calls = budget burn.
_vendor_stop_legacy() {
    [[ -n "$VENDOR_LEGACY_CLI" ]] || return 0

    # Disable and stop the OLD openclaw-fleet-gateway systemd service
    if systemctl --user is-active openclaw-fleet-gateway.service >/dev/null 2>&1 || \
       systemctl --user is-enabled openclaw-fleet-gateway.service >/dev/null 2>&1; then
        echo "  Disabling legacy openclaw-fleet-gateway systemd service..."
        systemctl --user stop openclaw-fleet-gateway.service 2>/dev/null || true
        systemctl --user disable openclaw-fleet-gateway.service 2>/dev/null || true
        systemctl --user reset-failed openclaw-fleet-gateway.service 2>/dev/null || true
    fi

    # Kill ALL legacy vendor processes
    if [[ -n "$VENDOR_LEGACY_CLI" ]] && pgrep -f "$VENDOR_LEGACY_CLI" >/dev/null 2>&1; then
        echo "  Killing all $VENDOR_LEGACY_CLI processes..."
        pkill -f "$VENDOR_LEGACY_CLI" 2>/dev/null || true
        sleep 2
    fi

    # BUDGET PROTECTION: Disable legacy cron jobs
    if [[ -n "$VENDOR_LEGACY_CONFIG_DIR" && -f "${VENDOR_LEGACY_CONFIG_DIR}/cron/jobs.json" ]]; then
        python3 -c "
import json
p = '${VENDOR_LEGACY_CONFIG_DIR}/cron/jobs.json'
with open(p) as f: data = json.load(f)
changed = 0
for j in data.get('jobs', []):
    if j.get('enabled'):
        j['enabled'] = False
        changed += 1
if changed:
    with open(p, 'w') as f: json.dump(data, f, indent=2)
    print(f'  Disabled {changed} legacy cron jobs')
" 2>/dev/null || true
    fi
}
