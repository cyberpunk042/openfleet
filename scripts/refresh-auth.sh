#!/usr/bin/env bash
set -euo pipefail

# Refresh Anthropic auth token if it has rotated.
# Safe to run repeatedly — only updates if the token changed.
# Call this before dispatching tasks or on 401 errors.
#
# Usage: bash scripts/refresh-auth.sh [--restart-gateway]

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLAW_ENV="${HOME}/.openclaw/.env"
CLAUDE_CREDS="${HOME}/.claude/.credentials.json"
RESTART_GATEWAY=false

[[ "${1:-}" == "--restart-gateway" ]] && RESTART_GATEWAY=true

if [[ ! -f "$CLAUDE_CREDS" ]]; then
    echo "No Claude Code credentials found" >&2
    exit 1
fi

# Get current token from Claude Code
NEW_TOKEN=$(python3 -c "
import json, sys
with open('$CLAUDE_CREDS') as f:
    creds = json.load(f)
token = creds.get('claudeAiOauth', {}).get('accessToken', '')
if token:
    print(token)
else:
    sys.exit(1)
" 2>/dev/null) || { echo "Could not extract Claude Code token" >&2; exit 1; }

# Get stored token
STORED_TOKEN=""
if [[ -f "$OPENCLAW_ENV" ]]; then
    STORED_TOKEN=$(grep "^ANTHROPIC_API_KEY=" "$OPENCLAW_ENV" 2>/dev/null | cut -d= -f2 || true)
fi

# Compare
if [[ "$NEW_TOKEN" == "$STORED_TOKEN" ]]; then
    echo "Token current (no rotation detected)"
    exit 0
fi

# Update
mkdir -p "${HOME}/.openclaw"
if [[ -f "$OPENCLAW_ENV" ]]; then
    grep -v "ANTHROPIC_API_KEY" "$OPENCLAW_ENV" > "${OPENCLAW_ENV}.tmp" 2>/dev/null || true
    mv "${OPENCLAW_ENV}.tmp" "$OPENCLAW_ENV"
fi
echo "ANTHROPIC_API_KEY=${NEW_TOKEN}" >> "$OPENCLAW_ENV"
echo "Token refreshed (rotation detected)"

# Restart gateway if requested (picks up new token)
# SAFETY: only restart if fleet is not paused AND MC is reachable.
if [[ "$RESTART_GATEWAY" == "true" ]]; then
    if [ -f "$FLEET_DIR/.fleet-paused" ]; then
        echo "Fleet is PAUSED — NOT restarting gateway"
    elif ! curl -sf http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "MC is DOWN — NOT restarting gateway"
    else
        echo "Restarting gateway..."
        pkill -f "openclaw-gateway" 2>/dev/null || true
        sleep 3
        cd "$FLEET_DIR" && openclaw gateway run --port 18789 &
        sleep 5
        if curl -sf http://localhost:18789 > /dev/null 2>&1; then
            echo "Gateway restarted with new token"
        else
            echo "WARN: Gateway may not have started" >&2
        fi
    fi
fi