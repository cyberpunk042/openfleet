#!/usr/bin/env bash
set -euo pipefail

# Configure Anthropic auth for gateway vendor.
# Automatically bridges Claude Code subscription — no manual steps.
echo "=== Configuring Auth ==="

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

if [[ -z "$VENDOR_CLI" ]]; then
    echo "ERROR: No gateway vendor installed"
    exit 1
fi

# Always check for fresh Claude Code token (tokens rotate)
CLAUDE_CREDS="${HOME}/.claude/.credentials.json"
if [[ -f "$CLAUDE_CREDS" ]]; then
    TOKEN=$(python3 -c "
import json, sys
with open('$CLAUDE_CREDS') as f:
    creds = json.load(f)
token = creds.get('claudeAiOauth', {}).get('accessToken', '')
if token:
    print(token)
else:
    sys.exit(1)
" 2>/dev/null) || TOKEN=""

    if [[ -n "$TOKEN" ]]; then
        echo "Found Claude Code OAuth token"

        # Write to vendor env
        mkdir -p "$VENDOR_CONFIG_DIR"
        if [[ -f "$VENDOR_ENV_FILE" ]]; then
            grep -v "ANTHROPIC_API_KEY" "$VENDOR_ENV_FILE" > "${VENDOR_ENV_FILE}.tmp" || true
            mv "${VENDOR_ENV_FILE}.tmp" "$VENDOR_ENV_FILE"
        fi
        echo "ANTHROPIC_API_KEY=${TOKEN}" >> "$VENDOR_ENV_FILE"
        echo "Token written to $VENDOR_ENV_FILE"
        echo "Auth configured for all agents via environment"
        exit 0
    fi
fi

# Fallback: check existing env var
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ANTHROPIC_API_KEY found in environment"
    mkdir -p "$VENDOR_CONFIG_DIR"
    if ! grep -q "ANTHROPIC_API_KEY" "$VENDOR_ENV_FILE" 2>/dev/null; then
        echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" >> "$VENDOR_ENV_FILE"
        echo "Written to $VENDOR_ENV_FILE"
    fi
    exit 0
fi

echo ""
echo "ERROR: No auth source found."
echo "  - No Claude Code credentials at ~/.claude/.credentials.json"
echo "  - No ANTHROPIC_API_KEY in environment"
echo ""
echo "Fix: run 'claude auth login' first, then re-run setup."
exit 1
