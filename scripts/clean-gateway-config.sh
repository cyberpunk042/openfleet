#!/usr/bin/env bash
set -euo pipefail

# Clean gateway config — deduplicate agents, set safe heartbeat intervals.
# Agents get duplicated because register-agents.sh creates one entry and
# MC provisioning creates another. Keep the MC-provisioned one (has workspace-mc-* path).
# Remove unnamed/main entries. Set staggered heartbeat intervals.

OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

if [[ ! -f "$OPENCLAW_CONFIG" ]]; then
  echo "ERROR: $OPENCLAW_CONFIG not found"
  exit 1
fi

echo "=== Cleaning Gateway Configuration ==="
echo ""

python3 - "$OPENCLAW_CONFIG" << 'PYEOF'
import json, sys

config_path = sys.argv[1]

with open(config_path) as f:
    cfg = json.load(f)

agents = cfg.get("agents", {}).get("list", [])
print(f"Before: {len(agents)} agents")

# Deduplicate by name — keep the one with workspace-mc-* path (MC provisioned)
seen_names = {}
gateway_agent = None
cleaned = []
removed = []

for a in agents:
    name = a.get("name", "")
    agent_id = a.get("id", "")
    workspace = a.get("workspace", "")

    # Skip unnamed/main entries
    if not name or agent_id == "main":
        removed.append(f"(unnamed, id={agent_id})")
        continue

    # Keep gateway agent (only one)
    if "Gateway" in name:
        if not gateway_agent:
            gateway_agent = a
            continue
        else:
            removed.append(f"{name} (duplicate gateway)")
            continue

    # For fleet agents: keep the one with workspace-mc-* path
    if name in seen_names:
        existing = seen_names[name]
        existing_ws = existing.get("workspace", "")
        # Prefer workspace-mc- path (MC provisioned, has TOOLS.md with tokens)
        if "workspace-mc-" in workspace and "workspace-mc-" not in existing_ws:
            removed.append(f"{name} (id={existing.get('id','?')}, non-MC duplicate)")
            seen_names[name] = a
        else:
            removed.append(f"{name} (id={agent_id}, duplicate)")
    else:
        seen_names[name] = a

# Build final list
if gateway_agent:
    cleaned.append(gateway_agent)
cleaned.extend(seen_names.values())

print(f"Removed {len(removed)} entries:")
for r in removed:
    print(f"  - {r}")

# Set staggered heartbeat intervals
intervals = {
    "fleet-ops": "30m",
    "project-manager": "35m",
    "devsecops-expert": "55m",
    "architect": "60m",
    "software-engineer": "65m",
    "qa-engineer": "70m",
    "devops": "75m",
    "technical-writer": "80m",
    "ux-designer": "85m",
    "accountability-generator": "90m",
}

for a in cleaned:
    name = a.get("name", "")
    if "Gateway" in name:
        a["heartbeat"] = {"every": "30m", "target": "last", "includeReasoning": False}
    elif name in intervals:
        a["heartbeat"] = {"every": intervals[name], "target": "last", "includeReasoning": False}
    else:
        a["heartbeat"] = {"every": "60m", "target": "last", "includeReasoning": False}

cfg["agents"]["list"] = cleaned

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)

print(f"\nAfter: {len(cleaned)} agents")
print("\nHeartbeat intervals:")
for a in cleaned:
    name = a.get("name", "(none)")
    every = a.get("heartbeat", {}).get("every", "?")
    print(f"  {name:40s} {every}")
PYEOF

echo ""
echo "Done."