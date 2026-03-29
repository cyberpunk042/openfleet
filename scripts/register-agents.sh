#!/usr/bin/env bash
set -euo pipefail

# Register fleet agents in OpenClaw gateway.
# Reads agent-identities.yaml and creates agents via openclaw CLI.
# Idempotent — safe to run multiple times.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IDENTITIES="$FLEET_DIR/config/agent-identities.yaml"

echo "=== Registering Fleet Agents ==="

if [[ ! -f "$IDENTITIES" ]]; then
    echo "ERROR: $IDENTITIES not found"
    exit 1
fi

python3 << PYEOF
import yaml, subprocess, os

fleet_dir = "$FLEET_DIR"
with open("$IDENTITIES") as f:
    cfg = yaml.safe_load(f)

agents = cfg.get("agents", {})
registered = 0

for agent_name, info in agents.items():
    display = info.get("display_name", agent_name)
    workspace = os.path.join(fleet_dir, "agents", agent_name)

    if not os.path.isdir(workspace):
        print(f"  SKIP: {agent_name} — no workspace dir")
        continue

    # Check if already registered
    try:
        result = subprocess.run(
            ["openclaw", "agents", "list"],
            capture_output=True, text=True, timeout=10
        )
        if agent_name in result.stdout:
            print(f"  EXISTS: {agent_name}")
            continue
    except Exception:
        pass

    # Register
    try:
        subprocess.run(
            ["openclaw", "agents", "add", agent_name,
             "--workspace", workspace],
            capture_output=True, text=True, timeout=30
        )
        print(f"  REGISTERED: {agent_name} ({display})")
        registered += 1
    except Exception as e:
        print(f"  ERROR: {agent_name} — {e}")

print(f"\n{registered} agents registered")
PYEOF