#!/usr/bin/env bash
set -euo pipefail

# Clean stale agent artifacts from previous setup runs.
#
# Removes:
#   - workspace-mc-* directories not matching current MC agents
#   - ~/.openclaw/agents/mc-* directories not matching current MC agents
#   - Gateway config entries (agents.list) not matching current MC agents
#
# Idempotent — safe to run multiple times.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"

set -a
source "$FLEET_DIR/.env" 2>/dev/null || true
set +a

echo "=== Cleaning Stale Agents ==="

if [[ -z "${LOCAL_AUTH_TOKEN:-}" ]]; then
    echo "  ERROR: LOCAL_AUTH_TOKEN not set"
    exit 1
fi

MC_URL="http://localhost:${BACKEND_PORT:-8000}"

# Get current MC agent IDs
CURRENT_IDS=$(curl -sf -m 10 -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
    "$MC_URL/api/v1/agents" 2>/dev/null \
    | python3 -c "
import json, sys
data = json.load(sys.stdin)
items = data.get('items', data) if isinstance(data, dict) else data
for a in items:
    print(a['id'])
" 2>/dev/null || true)

if [[ -z "$CURRENT_IDS" ]]; then
    echo "  ERROR: Could not fetch agents from MC"
    exit 1
fi

CURRENT_COUNT=$(echo "$CURRENT_IDS" | wc -l)
echo "  Current MC agents: $CURRENT_COUNT"

# 1. Clean stale workspaces
cleaned_ws=0
for workspace in "$FLEET_DIR"/workspace-mc-*; do
    [[ -d "$workspace" ]] || continue
    ws_id=$(basename "$workspace" | sed 's/workspace-mc-//')
    if ! echo "$CURRENT_IDS" | grep -q "$ws_id"; then
        rm -rf "$workspace"
        cleaned_ws=$((cleaned_ws + 1))
    fi
done
echo "  Stale workspaces removed: $cleaned_ws"

# 2. Clean stale agent dirs in ~/.openclaw/agents/
cleaned_dirs=0
OPENCLAW_AGENTS="$VENDOR_CONFIG_DIR/agents"
if [[ -d "$OPENCLAW_AGENTS" ]]; then
    for agent_dir in "$OPENCLAW_AGENTS"/mc-*; do
        [[ -d "$agent_dir" ]] || continue
        # Extract UUID from mc-{UUID}
        dir_id=$(basename "$agent_dir" | sed 's/mc-//')
        if ! echo "$CURRENT_IDS" | grep -q "$dir_id"; then
            rm -rf "$agent_dir"
            cleaned_dirs=$((cleaned_dirs + 1))
        fi
    done
fi
echo "  Stale agent dirs removed: $cleaned_dirs"

# 3. Clean stale entries from gateway config (agents.list)
if [[ -n "$VENDOR_CONFIG_FILE" && -f "$VENDOR_CONFIG_FILE" ]]; then
    python3 << PYEOF
import json, os

current_ids = set('''$CURRENT_IDS'''.strip().split('\n'))
# Gateway uses mc-{UUID} format
current_gw_ids = {f"mc-{uid}" for uid in current_ids if uid}

config_path = "$VENDOR_CONFIG_FILE"
with open(config_path) as f:
    cfg = json.load(f)

agents = cfg.get("agents", {}).get("list", [])
before = len(agents)

# Keep: current MC agents + gateway agents + non-mc agents
kept = [a for a in agents if a.get("id", "") in current_gw_ids
        or "gateway" in a.get("id", "").lower()
        or not a.get("id", "").startswith("mc-")]
removed = before - len(kept)

if removed > 0:
    cfg["agents"]["list"] = kept
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)
    # Reset config health checkpoint
    health_path = os.path.join("$VENDOR_CONFIG_DIR", "logs", "config-health.json")
    if os.path.exists(health_path):
        os.remove(health_path)

print(f"  Stale gateway entries removed: {removed}")
PYEOF
else
    echo "  Stale gateway entries removed: 0 (no vendor config)"
fi

echo "  Done"
