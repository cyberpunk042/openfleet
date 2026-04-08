#!/usr/bin/env bash
set -euo pipefail

# Configure Claude Code settings for each fleet agent workspace.
# Sets effort levels, permissions, hooks, and memory configuration per role.
# Reads hooks from config/agent-hooks.yaml and merges defaults + role-specific.
# Idempotent — safe to run multiple times.
#
# Sources:
#   config/agent-hooks.yaml — hook definitions (defaults + per-role)
#   fleet-elevation/20-ai-behavior.md — anti-corruption Line 1

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_FILE="$FLEET_DIR/config/agent-hooks.yaml"
PYTHON="${FLEET_DIR}/.venv/bin/python"

echo "=== Configuring Agent Claude Code Settings ==="

if [[ ! -f "$HOOKS_FILE" ]]; then
  echo "  WARNING: $HOOKS_FILE not found — deploying without hooks"
fi

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

declare -A SEEN_AGENTS  # Avoid processing duplicate workspaces

for mcp_file in "$FLEET_DIR"/workspace-mc-*/.mcp.json; do
  workspace_dir="$(dirname "$mcp_file")"
  agent_name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['mcpServers']['fleet']['env']['FLEET_AGENT'])" 2>/dev/null || continue)

  if [[ -n "${SEEN_AGENTS[$agent_name]:-}" ]]; then continue; fi
  SEEN_AGENTS[$agent_name]=1

  config="${AGENT_CONFIG[$agent_name]:-medium|acceptEdits}"
  effort=$(echo "$config" | cut -d'|' -f1)
  perm_mode=$(echo "$config" | cut -d'|' -f2)

  # Ensure .claude directory exists
  mkdir -p "$workspace_dir/.claude"

  # Generate settings.json via Python — handles YAML parsing + proper JSON escaping
  "$PYTHON" - "$agent_name" "$effort" "$perm_mode" "$HOOKS_FILE" \
    > "$workspace_dir/.claude/settings.json" << 'PYSCRIPT'
import sys, json, os

agent_name = sys.argv[1]
effort = sys.argv[2]
perm_mode = sys.argv[3]
hooks_file = sys.argv[4]

# Base settings
settings = {
    "effortLevel": effort,
    "permissions": {
        "defaultMode": perm_mode,
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
    "autoMemoryEnabled": True
}

# Load hooks if config exists
if os.path.isfile(hooks_file):
    import yaml
    with open(hooks_file) as f:
        hooks_config = yaml.safe_load(f) or {}

    defaults = hooks_config.get("defaults", {})
    role_hooks = hooks_config.get("roles", {}).get(agent_name, {})

    hooks_section = {}

    # Process each event type (PreToolUse, PostToolUse, SessionStart, etc.)
    all_event_types = set(
        list(defaults.keys()) + list(role_hooks.keys())
    )

    for event_type in sorted(all_event_types):
        entries = []

        # Default hooks first
        for hook_def in defaults.get(event_type, []):
            entries.append(hook_def)

        # Role-specific hooks second
        for hook_def in role_hooks.get(event_type, []):
            entries.append(hook_def)

        if entries:
            hooks_section[event_type] = []
            for entry in entries:
                hook_item = {
                    "type": entry.get("type", "command"),
                    "command": entry["command"].strip()
                }
                hooks_entry = {
                    "matcher": entry.get("matcher", ""),
                    "hooks": [hook_item]
                }
                hooks_section[event_type].append(hooks_entry)

    if hooks_section:
        settings["hooks"] = hooks_section

print(json.dumps(settings, indent=2))
PYSCRIPT

  # Count hooks for reporting
  hook_count=$("$PYTHON" -c "
import json
s = json.load(open('$workspace_dir/.claude/settings.json'))
h = s.get('hooks', {})
count = sum(len(v) for v in h.values())
print(count)
" 2>/dev/null || echo "0")

  echo "  $agent_name: effort=$effort mode=$perm_mode hooks=$hook_count memory=enabled"
done

echo ""
echo "Done. All agent workspaces configured."