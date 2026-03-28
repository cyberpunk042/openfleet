#!/usr/bin/env bash
set -euo pipefail

# Configure Claude Code settings for each fleet agent workspace.
# Sets effort levels, permissions, and memory configuration per role.
# Idempotent — safe to run multiple times.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Configuring Agent Claude Code Settings ==="

# Agent configurations: name|effort|permissionMode
declare -A AGENT_CONFIG=(
  ["architect"]="high|plan"
  ["software-engineer"]="medium|acceptEdits"
  ["qa-engineer"]="medium|acceptEdits"
  ["devops"]="medium|acceptEdits"
  ["devsecops-expert"]="high|default"
  ["project-manager"]="high|acceptEdits"
  ["fleet-ops"]="medium|acceptEdits"
  ["technical-writer"]="low|acceptEdits"
  ["ux-designer"]="medium|acceptEdits"
  ["accountability-generator"]="high|acceptEdits"
)

for mcp_file in "$FLEET_DIR"/workspace-mc-*/.mcp.json; do
  workspace_dir="$(dirname "$mcp_file")"
  agent_name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['mcpServers']['fleet']['env']['FLEET_AGENT'])" 2>/dev/null || continue)

  config="${AGENT_CONFIG[$agent_name]:-medium|acceptEdits}"
  effort=$(echo "$config" | cut -d'|' -f1)
  perm_mode=$(echo "$config" | cut -d'|' -f2)

  # Ensure .claude directory exists
  mkdir -p "$workspace_dir/.claude"

  # Write settings.json
  cat > "$workspace_dir/.claude/settings.json" << SETTINGS
{
  "effortLevel": "$effort",
  "permissions": {
    "defaultMode": "$perm_mode",
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "Glob(*)",
      "Grep(*)",
      "mcp__fleet__*"
    ],
    "deny": []
  },
  "autoMemoryEnabled": true
}
SETTINGS

  echo "  $agent_name: effort=$effort mode=$perm_mode memory=enabled"
done

echo ""
echo "Done. All agent workspaces configured."