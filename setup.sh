#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Fleet — Full Setup
#
# Takes you from a fresh clone to a running fleet.
# Run: ./setup.sh
#
# BUDGET PROTECTION — READ THIS BEFORE MODIFYING
# ================================================
# The fleet's #1 safety invariant: OCMC down = ZERO Claude API calls.
#
# How it works:
#   1. Systemd service (fleet-gateway.service) has ExecStartPre that checks
#      OCMC health. Gateway refuses to start if OCMC is down.
#   2. Orchestrator daemon watches MC every 30s. MC unreachable →
#      disable_gateway_cron_jobs() → heartbeats stop → zero Claude calls.
#   3. When OCMC comes back up, orchestrator re-enables cron jobs.
#
# DO NOT:
#   - Change Restart=on-failure to Restart=always (causes restart storm)
#   - Remove ExecStartPre MC health check
#   - Start the gateway without MC being up
#   - Hardcode vendor paths (use vendor.sh / resolve_vendor_dir)
#
# Violation = thousands of dollars burned on heartbeats to dead MC.
# ================================================
#
# What it does:
# 1. Installs gateway vendor (OpenArms or OpenClaw)
# 2. Configures gateway (bind, controlUi)
# 3. Configures auth (Claude Code subscription bridge)
# 4. Configures exec approval, CLI backend, workspace permissions
# 5. Sets up IRC channel
# 6. Starts MC containers (docker compose up)
# 7. Starts gateway (needs MC health check)
# 8. Registers gateway/board/agents in MC (needs gateway running)
#    MC provisions agents on gateway via template sync (agents.create)
# 9. Pushes SOUL.md + Claude Code settings to agent workspaces

FLEET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$FLEET_DIR"
source "$FLEET_DIR/scripts/lib/vendor.sh"

echo "╔══════════════════════════════════════╗"
echo "║     Fleet Setup                      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Step 0: Kill existing fleet processes (clean slate for idempotent setup)
echo "=== Cleaning Existing Processes ==="
pkill -f "fleet daemon" 2>/dev/null && echo "  Killed fleet daemons" || true
pkill -f "fleet.mcp.server" 2>/dev/null && echo "  Killed MCP servers" || true
pkill -f "setup-lightrag" 2>/dev/null && echo "  Killed stale LightRAG sync" || true
pkill -f "miniircd" 2>/dev/null && echo "  Killed IRC daemon" || true
pkill -f "python3 -m gateway start" 2>/dev/null && echo "  Killed stale AICP gateway" || true
echo "  Clean"
echo ""

# Step 0b: Pre-flight checks
echo "=== Pre-flight Checks ==="
PREFLIGHT_OK=true

# Python 3.11+
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
        echo "  Python $PY_VER: OK"
    else
        echo "  Python $PY_VER: NEED 3.11+ (some features may not work)"
    fi
else
    echo "  Python: NOT FOUND — install Python 3.11+"
    PREFLIGHT_OK=false
fi

# Docker
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "  Docker: OK"
else
    echo "  Docker: NOT AVAILABLE — install Docker and start the daemon"
    PREFLIGHT_OK=false
fi

# Docker Compose
if docker compose version >/dev/null 2>&1; then
    echo "  Docker Compose: OK"
else
    echo "  Docker Compose: NOT FOUND — install docker-compose-plugin"
    PREFLIGHT_OK=false
fi

# Claude Code
if command -v claude >/dev/null 2>&1; then
    echo "  Claude Code: OK"
else
    echo "  Claude Code: NOT FOUND — agents won't execute (install: npm install -g @anthropic-ai/claude-code)"
fi

# GitHub CLI (for PR creation)
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "  GitHub CLI: OK (authenticated)"
else
    echo "  GitHub CLI: NOT AUTHED — agents can't create PRs (run: gh auth login)"
fi

# Git
if command -v git >/dev/null 2>&1; then
    echo "  Git: OK"
else
    echo "  Git: NOT FOUND"
    PREFLIGHT_OK=false
fi

if [[ "$PREFLIGHT_OK" != "true" ]]; then
    echo ""
    echo "Pre-flight checks failed. Fix the issues above and re-run."
    exit 1
fi

# uv (Python version + venv manager)
if command -v uv >/dev/null 2>&1; then
    echo "  uv: OK"
else
    echo "  uv: NOT FOUND — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
    export PATH="$HOME/.local/bin:$PATH"
fi

# Set up Python venv with 3.11+
echo "  Setting up Python venv..."
if [[ ! -d "$FLEET_DIR/.venv" ]]; then
    uv venv --python 3.11 "$FLEET_DIR/.venv" 2>/dev/null || {
        echo "  WARN: Could not create Python 3.11 venv"
    }
fi

# Install fleet package in venv
if [[ -d "$FLEET_DIR/.venv" ]]; then
    uv pip install --python "$FLEET_DIR/.venv/bin/python" -q -e "$FLEET_DIR[dev]" 2>/dev/null || {
        echo "  WARN: Fleet package install failed"
    }
    echo "  Python venv: OK (.venv with Python 3.11+)"
fi
echo ""

# Step 0c: Generate fleet identity (unique per machine)
echo "=== Fleet Identity ==="
if [[ -f "$FLEET_DIR/.venv/bin/python" ]]; then
    "$FLEET_DIR/.venv/bin/python" -c "
from fleet.core.federation import generate_fleet_identity, load_fleet_identity
identity = generate_fleet_identity('$FLEET_DIR')
print(f'  Fleet ID:   {identity.fleet_id}')
print(f'  Fleet Name: {identity.fleet_name}')
print(f'  Machine:    {identity.machine_id}')
print(f'  Prefix:     {identity.agent_prefix}')
" 2>/dev/null || echo "  SKIP: Fleet identity (venv not ready)"
fi
echo ""

# Step 1: Install gateway vendor
bash scripts/install-openclaw.sh
source "$FLEET_DIR/scripts/lib/vendor.sh"  # re-source after install
_vendor_cutover  # migrate config from openclaw if switching to openarms
# Set GATEWAY_CLIENT_ID in .env for MC backend
if grep -q "GATEWAY_CLIENT_ID" "$FLEET_DIR/.env" 2>/dev/null; then
    sed -i "s/GATEWAY_CLIENT_ID=.*/GATEWAY_CLIENT_ID=${VENDOR_CLI}-control-ui/" "$FLEET_DIR/.env"
else
    echo "GATEWAY_CLIENT_ID=${VENDOR_CLI}-control-ui" >> "$FLEET_DIR/.env"
fi
echo ""

# Step 2: Configure gateway vendor (if not already set up)
if [[ -n "$VENDOR_CLI" ]] && [[ ! -f "$VENDOR_CONFIG_FILE" ]]; then
    echo "=== Configuring $VENDOR_NAME ==="
    $VENDOR_CLI onboard --non-interactive --accept-risk --workspace "$FLEET_DIR" --skip-health
fi

# Step 3: Configure OpenClaw gateway settings
echo "=== Configuring Gateway ==="
python3 -c "
import json, os
config_path = os.path.expanduser('$VENDOR_CONFIG_FILE')
with open(config_path) as f:
    cfg = json.load(f)

changed = False

# Ensure LAN bind
if cfg.get('gateway', {}).get('bind') != 'lan':
    cfg.setdefault('gateway', {})['bind'] = 'lan'
    changed = True

# Ensure control UI allows MC connections
cu = cfg.get('gateway', {}).get('controlUi', {})
if not cu.get('allowInsecureAuth') or not cu.get('dangerouslyDisableDeviceAuth'):
    cfg['gateway']['controlUi'] = {
        'allowedOrigins': ['*'],
        'allowInsecureAuth': True,
        'dangerouslyDisableDeviceAuth': True,
    }
    changed = True

# Ensure workspace is set
if cfg.get('agents', {}).get('defaults', {}).get('workspace') != '$FLEET_DIR':
    cfg.setdefault('agents', {}).setdefault('defaults', {})['workspace'] = '$FLEET_DIR'
    changed = True

if changed:
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    print('Gateway config updated')
else:
    print('Gateway config OK')
"
echo ""

# Step 4: Configure auth
bash scripts/configure-auth.sh || {
    echo ""
    echo "⚠️  Auth not configured. Fleet will start but agents won't execute."
    echo "   Fix it later with: bash scripts/configure-auth.sh"
    echo ""
}
echo ""

# Step 5: Configure exec tool, CLI backend, and workspace permissions
bash scripts/configure-openclaw.sh
echo ""

# Step 6: Set up IRC channel for fleet observation
bash scripts/setup-irc.sh
echo ""

# Step 7: Start MC containers (gateway needs MC health check, but MC setup needs gateway)
# Solve chicken-and-egg: start containers → start gateway → register in MC → seed → restart
echo "=== Starting Mission Control Containers ==="
bash scripts/setup-mc.sh --containers-only
echo ""

# Step 7a: Start LightRAG KB sync in background (if LocalAI is available)
# LightRAG needs LocalAI for embeddings (nomic-embed). Every entity/relationship
# create calls the embedding model. Without LocalAI, all creates fail with HTTP 500.
echo "=== LightRAG KB Sync ==="
LIGHTRAG_LOG="$FLEET_DIR/.lightrag-sync.log"
LIGHTRAG_PID=""
LIGHTRAG_SKIPPED=""
if curl -sf http://localhost:8090/v1/models >/dev/null 2>&1; then
    bash scripts/setup-lightrag.sh --all > "$LIGHTRAG_LOG" 2>&1 &
    LIGHTRAG_PID=$!
    echo "  Started in background (PID: $LIGHTRAG_PID)"
else
    LIGHTRAG_SKIPPED=true
    echo "  Skipped — LocalAI not running (localhost:8090)"
fi
echo ""

# Step 7b: Install fleet extensions to gateway vendor
if [[ -d "$FLEET_DIR/extensions/fleet-heartbeat-gate" ]]; then
    VENDOR_EXT_DIR="$VENDOR_CONFIG_DIR/extensions/fleet-heartbeat-gate"
    mkdir -p "$VENDOR_EXT_DIR"
    cp -r "$FLEET_DIR/extensions/fleet-heartbeat-gate/"* "$VENDOR_EXT_DIR/"
    echo "Fleet heartbeat gate plugin installed"
fi

# Step 7c: Start the fleet gateway (MC containers are up, health check passes)
bash scripts/start-fleet.sh
echo ""

# Step 7c: Register gateway, board, agents in MC (both MC and gateway are now up)
echo "=== Registering Fleet in Mission Control ==="
bash scripts/setup-mc.sh --register
echo ""

# Step 7d: Clean stale agents from previous setup runs
bash scripts/clean-stale-agents.sh
echo ""

# Step 7e: Pre-seed gateway config with MC agent entries.
# This avoids the SIGUSR1 restart storm during template sync: agents already
# exist in gateway config on boot → template sync just pushes files (no agents.create).
bash scripts/seed-gateway-agents.sh
echo ""

# Step 7f: Clean gateway config (dedup + stagger heartbeats) then restart once.
echo "=== Cleaning Gateway Config ==="
bash scripts/clean-gateway-config.sh
echo ""
echo "=== Restarting Gateway (seeded + clean config) ==="
bash scripts/start-fleet.sh
echo ""

# Step 8: Start The Lounge (web IRC client)
bash scripts/setup-lounge.sh
echo ""

# Step 12: Configure agent Claude Code settings (effort, memory, permissions)
echo "=== Configuring Agent Settings ==="
bash scripts/configure-agent-settings.sh
echo ""

# Step 13: Push fleet framework to all agent workspaces
echo "=== Pushing Agent Framework ==="
bash scripts/push-agent-framework.sh
echo ""

# Step 13b: Install Codex plugin config (adversarial reviews)
echo "=== Codex Plugin Setup ==="
bash scripts/install-codex-plugin.sh || {
    echo "  WARN: Codex plugin setup failed (non-critical, can retry with: make codex-setup)"
}
echo ""

# Step 13c: Install Claude Code statusline (context awareness)
echo "=== Statusline Setup ==="
bash scripts/install-statusline.sh || {
    echo "  WARN: Statusline setup failed (non-critical, can retry with: make install-statusline)"
}
echo ""

# Step 14: Configure board custom fields and tags
echo "=== Configuring Board ==="
bash scripts/configure-board.sh
echo ""

# Step 15: Start fleet daemons (sync + monitor + orchestrator in conservative mode)
echo "=== Starting Fleet Daemons ==="
echo "NOTE: Fleet starts paused. Use 'fleet resume' when ready."
if [[ -f "$FLEET_DIR/.venv/bin/python" ]]; then
    # Source .env for latest Plane credentials + fleet config
    PYTHONUNBUFFERED=1 FLEET_DIR="$FLEET_DIR" nohup "$FLEET_DIR/.venv/bin/python" -m fleet daemon all > "$FLEET_DIR/.fleet-daemons.log" 2>&1 &
    disown
    echo "Fleet daemons started (PID: $!, log: .fleet-daemons.log)"
else
    echo "ERROR: Python venv not found. Run: uv venv --python 3.11 && uv pip install -e ."
fi
echo ""

# Step 16: Final template sync (refreshes last_seen_at so agents show "online")
# Must be the LAST thing before the completion message — any delay >10min
# causes MC to compute status as "offline".
echo "=== Final Agent Sync ==="
set -a
source "$FLEET_DIR/.env" 2>/dev/null || true
set +a
if [[ -n "${LOCAL_AUTH_TOKEN:-}" ]]; then
    # Touch last_seen_at on all agents so they show online after gateway restart.
    # The gateway HeartbeatRunner fires on its own schedule (30-90 min), but MC's
    # OFFLINE_AFTER is only 10 min. Without this, agents go offline before the
    # first heartbeat fires.
    ONLINE=0
    AGENTS_JSON=$(curl -sf -m 10 -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
        http://localhost:8000/api/v1/agents 2>/dev/null || echo '{"items":[]}')
    for AGENT_ID in $(echo "$AGENTS_JSON" | python3 -c "
import json,sys
data=json.load(sys.stdin)
items=data.get('items',data) if isinstance(data,dict) else data
for a in items:
    if 'Gateway' not in a.get('name',''):
        print(a['id'])
" 2>/dev/null); do
        RESP=$(curl -sf -m 10 -X POST \
            -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            "http://localhost:8000/api/v1/agents/${AGENT_ID}/heartbeat" \
            -d '{}' 2>/dev/null || echo "")
        if [[ -n "$RESP" ]]; then
            ONLINE=$((ONLINE + 1))
        fi
    done
    echo "  $ONLINE agents online"

    # Wait for gateway to fully initialize before template sync
    echo "  Waiting for gateway to stabilize..."
    sleep 15

    # Trigger template sync to recreate CRON jobs for all agents
    GW_ID=$(curl -sf -m 5 -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
        http://localhost:8000/api/v1/gateways \
        | python3 -c "
import json,sys; data=json.load(sys.stdin)
items=data.get('items',data) if isinstance(data,dict) else data
for g in items:
    if 'Gateway' not in g.get('name',''):
        continue
    print(g['id'])
    break
" 2>/dev/null || true)

    if [[ -n "${GW_ID:-}" ]]; then
        SYNC_RESULT=$(curl -sf -m 180 -X POST \
            -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
            -H "Content-Type: application/json" \
            "http://localhost:8000/api/v1/gateways/${GW_ID}/templates/sync" \
            -d '{}' 2>&1 || echo '{}')
        echo "  Template sync: $(echo "$SYNC_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'updated={d.get(\"agents_updated\",0)}')" 2>/dev/null || echo "done")"
    fi
fi
echo ""

# Step 17: Wait for background LightRAG sync with progress
if [[ -n "${LIGHTRAG_PID:-}" ]] && kill -0 "$LIGHTRAG_PID" 2>/dev/null; then
    echo "=== LightRAG KB Sync ==="
    echo ""
    echo "  Press ENTER to detach (sync continues in background)"
    echo "  Type 'w' + ENTER to detach and get notified when done"
    echo "  Press Ctrl+C to cancel the sync"
    echo ""

    # Ctrl+C cancels the LightRAG sync
    trap 'echo ""; echo "  Cancelling LightRAG sync..."; kill "$LIGHTRAG_PID" 2>/dev/null; kill "$INPUT_PID" 2>/dev/null; rm -f "$INPUT_FLAG"; trap - INT; echo "  Cancelled."; echo ""' INT

    # Progress loop: show sync progress, check for user input
    # Background: watch for user input, write to a temp file when received
    DETACHED=false
    NOTIFY=false
    LAST_DISPLAY=""
    INPUT_FLAG=$(mktemp)
    rm -f "$INPUT_FLAG"
    ( read -r line < /dev/tty 2>/dev/null; echo "$line" > "$INPUT_FLAG" ) &
    INPUT_PID=$!

    while kill -0 "$LIGHTRAG_PID" 2>/dev/null; do
        # Check for user input (non-blocking — just check if file appeared)
        if [[ -f "$INPUT_FLAG" ]]; then
            USER_INPUT=$(cat "$INPUT_FLAG" 2>/dev/null || true)
            if [[ "$USER_INPUT" == "w" || "$USER_INPUT" == "W" ]]; then
                NOTIFY=true
            fi
            DETACHED=true
            break
        fi

        if [[ -f "$LIGHTRAG_LOG" ]]; then
            # Find the last progress line "    N/M (X ok, Y fail)"
            PROGRESS=$(grep -aoP '\s+\d+/\d+ \(\d+ ok, \d+ fail\)' "$LIGHTRAG_LOG" 2>/dev/null | tail -1 || true)
            # Find the current phase
            PHASE=$(grep -aoP '(Installing|Waiting|Syncing|Inserting|Verifying|Source entities|Source relationships|Entities done|Relationships done|Result:).*' "$LIGHTRAG_LOG" 2>/dev/null | tail -1 || true)

            DISPLAY=""
            if [[ "$PROGRESS" =~ ([0-9]+)/([0-9]+)\ \(([0-9]+)\ ok,\ ([0-9]+)\ fail ]]; then
                CURRENT="${BASH_REMATCH[1]}"
                TOTAL="${BASH_REMATCH[2]}"
                OK="${BASH_REMATCH[3]}"
                FAIL="${BASH_REMATCH[4]}"
                if [[ "$TOTAL" -gt 0 ]]; then
                    PCT=$(( CURRENT * 100 / TOTAL ))
                    BAR_LEN=20
                    FILLED=$(( PCT * BAR_LEN / 100 ))
                    BAR=$(printf '%*s' "$FILLED" '' | tr ' ' '#')
                    EMPTY=$(printf '%*s' $((BAR_LEN - FILLED)) '' | tr ' ' '-')
                    DISPLAY=$(printf "[%s%s] %3d%% (%d/%d, %d ok, %d fail)" "$BAR" "$EMPTY" "$PCT" "$CURRENT" "$TOTAL" "$OK" "$FAIL")
                fi
            elif [[ -n "$PHASE" ]]; then
                DISPLAY=$(echo "$PHASE" | sed 's/\x1b\[[0-9;]*m//g')
                DISPLAY="${DISPLAY:0:60}"
            fi

            if [[ -n "$DISPLAY" && "$DISPLAY" != "$LAST_DISPLAY" ]]; then
                LAST_DISPLAY="$DISPLAY"
                printf "\r  %-72s" "$DISPLAY"
            fi
        fi

        sleep 1
    done

    # Cleanup
    kill "$INPUT_PID" 2>/dev/null || true
    wait "$INPUT_PID" 2>/dev/null || true
    rm -f "$INPUT_FLAG"
    printf "\n"

    if [[ "$DETACHED" == true ]]; then
        echo "  Detached — sync continues in background (PID: $LIGHTRAG_PID)"
        echo "  Log: tail -f $LIGHTRAG_LOG"
        if [[ "$NOTIFY" == true ]]; then
            # Spawn a notifier that waits for the sync and pings the user
            (
                wait "$LIGHTRAG_PID" 2>/dev/null
                EXIT_CODE=$?
                RESULT=$(grep 'Result:' "$LIGHTRAG_LOG" 2>/dev/null | tail -1 || echo "check .lightrag-sync.log")
                if [[ "$EXIT_CODE" -eq 0 ]]; then
                    MSG="LightRAG sync complete: $RESULT"
                else
                    MSG="LightRAG sync FAILED (exit $EXIT_CODE). Check .lightrag-sync.log"
                fi
                # Bell + message to terminal
                printf '\a\n\033[1;32m>>> %s\033[0m\n' "$MSG" > /dev/tty 2>/dev/null || true
                # ntfy notification if available
                curl -sf -d "$MSG" "http://localhost:8091/fleet" >/dev/null 2>&1 || true
            ) &
            disown
            echo "  You'll be notified when it's done"
        fi
    else
        # Sync finished while we were watching
        wait "$LIGHTRAG_PID" 2>/dev/null
        EXIT_CODE=$?
        if [[ "$EXIT_CODE" -eq 0 ]]; then
            echo "  LightRAG sync complete"
        else
            echo "  WARN: LightRAG sync failed (exit $EXIT_CODE, check .lightrag-sync.log)"
        fi
        tail -3 "$LIGHTRAG_LOG" 2>/dev/null | sed 's/^/  /'
    fi
    echo ""
elif [[ -n "${LIGHTRAG_PID:-}" ]]; then
    # Already finished before we got here
    wait "$LIGHTRAG_PID" 2>/dev/null
    EXIT_CODE=$?
    echo "=== LightRAG KB Sync ==="
    if [[ "$EXIT_CODE" -eq 0 ]]; then
        echo "  Complete"
    else
        echo "  WARN: Failed (exit $EXIT_CODE)"
    fi
    tail -3 "$LIGHTRAG_LOG" 2>/dev/null | sed 's/^/  /'
    echo ""
fi

# Reset trap
trap - INT

echo "╔══════════════════════════════════════╗"
echo "║     Fleet Setup Complete             ║"
echo "╚══════════════════════════════════════╝"
echo ""
source "$FLEET_DIR/.env" 2>/dev/null || true
GW_PORT="${OCF_GATEWAY_PORT:-9400}"
echo "Everything is running:"
echo "  Mission Control UI:  http://localhost:${FRONTEND_PORT:-3000}"
echo "  Mission Control API: http://localhost:${BACKEND_PORT:-8000}"
echo "  $VENDOR_NAME Gateway:    ws://localhost:${GW_PORT}"
echo "  $VENDOR_NAME Control UI: http://localhost:${GW_PORT}"
echo "  LightRAG:            http://localhost:${LIGHTRAG_PORT:-9621}"
echo "  IRC Server:          localhost:6667"
echo "  The Lounge (IRC UI): http://localhost:${LOUNGE_PORT:-9000}  (fleet/fleet)"
echo ""
echo "IRC Channels: #fleet #alerts #reviews #sprint #agents #security #human #builds #memory #plane"
echo ""
echo "Safety:"
echo "  Work mode:        starts paused (use 'fleet resume' to dispatch)"
echo "  Heartbeats:       staggered 30-90m per agent"
echo "  Budget monitor:   reads CLAUDE_QUOTA_* — auto-pause at 90%"
echo "  Kill switch:      fleet pause / fleet resume"
echo ""
echo "Manage:"
echo "  make status    — fleet overview"
echo "  make watch     — real-time agent events"
echo "  make sync      — sync tasks ↔ PRs"
echo "  make mc-up     — start Mission Control"
echo "  make gateway   — start gateway"
echo "  make logs      — view gateway logs"

if [[ -n "${LIGHTRAG_SKIPPED:-}" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  LightRAG KB sync was SKIPPED — LocalAI was not running.   ║"
    echo "║                                                            ║"
    echo "║  LightRAG needs LocalAI for embeddings (nomic-embed).      ║"
    echo "║  Start LocalAI, then run:                                  ║"
    echo "║                                                            ║"
    echo "║    bash scripts/setup-lightrag.sh --all                    ║"
    echo "║                                                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
fi