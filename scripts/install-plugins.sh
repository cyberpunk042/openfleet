#!/usr/bin/env bash
# install-plugins.sh — Install Claude plugins per agent from config/agent-tooling.yaml
#
# Usage: bash scripts/install-plugins.sh [agent-name]
#   No args: install for all agents
#   With arg: install for specific agent
#
# Requires: claude CLI, yq

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
CONFIG="$FLEET_DIR/config/agent-tooling.yaml"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Dependencies ────────────────────────────────────────────────────

if ! command -v yq &>/dev/null; then
    echo -e "${RED}ERROR:${NC} yq required. Run: bash scripts/setup-agent-tools.sh first"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo -e "${RED}ERROR:${NC} claude CLI required for plugin installation"
    exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
    echo -e "${RED}ERROR:${NC} $CONFIG not found"
    exit 1
fi

# ─── Ensure plugin marketplaces are registered ─────────────────────────

# Plugin marketplaces — GitHub repos that publish plugin manifests
# Claude Code and OpenClaw both use `plugin marketplace add <source>`
MARKETPLACES=(
    "thedotmack/claude-mem"
    "kenryu42/claude-code-safety-net"
    "zscole/adversarial-spec"
    "b17z/sage"
    "backnotprop/plannotator"
    "agenticnotetaking/arscontexta"
)

echo ""
echo "Registering plugin marketplaces..."
for mp in "${MARKETPLACES[@]}"; do
    # Register in Claude Code
    if claude plugin marketplace list 2>/dev/null | grep -q "$mp"; then
        echo -e "  ${YELLOW}[skip]${NC} $mp (claude)"
    else
        claude plugin marketplace add "$mp" 2>/dev/null && \
            echo -e "  ${GREEN}[added]${NC} $mp (claude)" || \
            echo -e "  ${RED}[error]${NC} $mp (claude): failed to add"
    fi
    # Register in OpenClaw
    if command -v openclaw &>/dev/null; then
        openclaw plugins marketplace list "$mp" --json >/dev/null 2>&1 && \
            echo -e "  ${YELLOW}[skip]${NC} $mp (openclaw)" || {
            openclaw plugins install "marketplace:$mp" 2>/dev/null && \
                echo -e "  ${GREEN}[added]${NC} $mp (openclaw)" || true
        }
    fi
done

# ─── Install plugins for one agent ───────────────────────────────────

install_for_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    if [[ ! -d "$agent_dir" ]]; then
        echo -e "  ${YELLOW}[skip]${NC} $agent_name: directory not found"
        return
    fi

    echo ""
    echo "Plugins for $agent_name:"

    # Default plugins (all agents)
    local default_count
    default_count=$(yq -r '.defaults.plugins | length' "$CONFIG") || default_count=0

    local i=0
    while (( i < default_count )); do
        local plugin
        plugin=$(yq -r ".defaults.plugins[$i]" "$CONFIG")
        _install_plugin "$agent_name" "$agent_dir" "$plugin"
        i=$((i + 1))
    done

    # Role-specific plugins
    local role_count
    role_count=$(yq -r ".agents.\"$agent_name\".plugins | length" "$CONFIG" 2>/dev/null) || role_count=0

    i=0
    while (( i < role_count )); do
        local plugin
        plugin=$(yq -r ".agents.\"$agent_name\".plugins[$i]" "$CONFIG")
        _install_plugin "$agent_name" "$agent_dir" "$plugin"
        i=$((i + 1))
    done

    if (( default_count + role_count == 0 )); then
        echo -e "  ${YELLOW}[none]${NC} no plugins configured"
    fi
}

_install_plugin() {
    local agent_name="$1" agent_dir="$2" plugin="$3"

    # Check if already installed (look for plugin in .claude/ config)
    if [[ -d "$agent_dir/.claude" ]] && grep -rq "$plugin" "$agent_dir/.claude/" 2>/dev/null; then
        echo -e "  ${YELLOW}[skip]${NC} $plugin (already installed)"
        return
    fi

    echo -e "  ${GREEN}[install]${NC} $plugin"
    (cd "$agent_dir" && claude plugin install "$plugin" 2>&1) || \
        echo -e "  ${RED}[error]${NC} $plugin: installation failed"
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet Plugin Installation"
echo "  Config: config/agent-tooling.yaml"
echo "═══════════════════════════════════════════════════════"

if [[ $# -gt 0 ]]; then
    install_for_agent "$1"
else
    for agent_name in $(yq -r '.agents | keys | .[]' "$CONFIG"); do
        install_for_agent "$agent_name"
    done
fi

echo ""
echo "Done."
