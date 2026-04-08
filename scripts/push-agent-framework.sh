#!/usr/bin/env bash
set -euo pipefail

# Push fleet framework files to all agent workspaces.
# Ensures every agent has the latest STANDARDS.md, MC_WORKFLOW.md, HEARTBEAT.md.
# Called by setup.sh or manually when framework files change.
# Idempotent — safe to run multiple times.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_DIR="$FLEET_DIR/agents/_template"

echo "=== Pushing Fleet Framework to Agent Workspaces ==="

pushed=0
skipped=0
declare -A SEEN_AGENTS  # Track agents already processed (avoid duplicates)

for mcp_file in "$FLEET_DIR"/workspace-mc-*/.mcp.json; do
  workspace_dir="$(dirname "$mcp_file")"
  agent_name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['mcpServers']['fleet']['env']['FLEET_AGENT'])" 2>/dev/null || continue)

  # Skip duplicate workspaces for the same agent (old vs new UUIDs)
  if [[ -n "${SEEN_AGENTS[$agent_name]:-}" ]]; then
    continue
  fi
  SEEN_AGENTS[$agent_name]=1
  agent_dir="$FLEET_DIR/agents/$agent_name"

  # Copy shared framework files from template
  for file in MC_WORKFLOW.md STANDARDS.md; do
    src="$TEMPLATE_DIR/$file"
    dst="$workspace_dir/$file"
    if [[ -f "$src" ]]; then
      cp "$src" "$dst"
      pushed=$((pushed + 1))
    fi
  done

  # Copy agent-specific CLAUDE.md
  if [[ -f "$agent_dir/CLAUDE.md" ]]; then
    cp "$agent_dir/CLAUDE.md" "$workspace_dir/CLAUDE.md"
    pushed=$((pushed + 1))
  fi

  # Copy agent-specific HEARTBEAT.md
  if [[ -f "$agent_dir/HEARTBEAT.md" ]]; then
    cp "$agent_dir/HEARTBEAT.md" "$workspace_dir/HEARTBEAT.md"
    pushed=$((pushed + 1))
  fi

  # Copy generated AGENTS.md (fleet awareness, from generate-agents-md.py)
  if [[ -f "$agent_dir/AGENTS.md" ]]; then
    cp "$agent_dir/AGENTS.md" "$workspace_dir/AGENTS.md"
    pushed=$((pushed + 1))
  fi

  # Copy generated TOOLS.md (7-layer, from generate-tools-md.py)
  # Overwrites MC-generated minimal TOOLS.md with complete version
  if [[ -f "$agent_dir/TOOLS.md" ]]; then
    cp "$agent_dir/TOOLS.md" "$workspace_dir/TOOLS.md"
    pushed=$((pushed + 1))
  fi

  echo "  $agent_name: pushed"
done

echo ""
echo "Done. $pushed files pushed to agent workspaces."