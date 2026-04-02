#!/usr/bin/env bash
# setup-agent-tools.sh — Deploy per-agent mcp.json from config/agent-tooling.yaml
#
# Usage: bash scripts/setup-agent-tools.sh [agent-name]
# Requires: yq, jq

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
CONFIG="$FLEET_DIR/config/agent-tooling.yaml"
VENV="$FLEET_DIR/.venv"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Dependencies (auto-install if missing) ─────────────────────────

install_if_missing() {
    local cmd="$1"
    if command -v "$cmd" &>/dev/null; then
        return 0
    fi
    echo -e "  ${YELLOW}[dep]${NC} $cmd not found, installing..."
    case "$cmd" in
        jq)
            if sudo -n true 2>/dev/null; then
                sudo apt-get install -y jq >/dev/null 2>&1
            else
                mkdir -p "$HOME/.local/bin"
                local jq_url="https://github.com/jqlang/jq/releases/latest/download/jq-linux-amd64"
                wget -qO "$HOME/.local/bin/jq" "$jq_url" && chmod +x "$HOME/.local/bin/jq"
                export PATH="$HOME/.local/bin:$PATH"
            fi
            command -v jq &>/dev/null || { echo -e "${RED}ERROR:${NC} Failed to install jq"; exit 1; }
            ;;
        yq)
            # yq v4 — Go binary from GitHub (try system-wide, fallback to ~/.local/bin)
            local yq_url="https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64"
            if sudo -n true 2>/dev/null; then
                sudo wget -qO /usr/local/bin/yq "$yq_url" && sudo chmod +x /usr/local/bin/yq
            else
                mkdir -p "$HOME/.local/bin"
                wget -qO "$HOME/.local/bin/yq" "$yq_url" && chmod +x "$HOME/.local/bin/yq"
                export PATH="$HOME/.local/bin:$PATH"
            fi
            command -v yq &>/dev/null || { echo -e "${RED}ERROR:${NC} Failed to install yq"; exit 1; }
            ;;
    esac
    echo -e "  ${GREEN}[dep]${NC} $cmd installed"
}

install_if_missing jq
install_if_missing yq

if [[ ! -f "$CONFIG" ]]; then
    echo -e "${RED}ERROR:${NC} $CONFIG not found"
    exit 1
fi

# ─── Resolve placeholders ───────────────────────────────────────────

resolve() {
    local val="$1" agent_name="$2"
    echo "$val" \
        | sed "s|{{FLEET_DIR}}|$FLEET_DIR|g" \
        | sed "s|{{FLEET_VENV}}|$VENV|g" \
        | sed "s|{{AGENT_NAME}}|$agent_name|g" \
        | sed "s|{{WORKSPACE}}|$AGENTS_DIR/$agent_name|g"
}

# ─── Build mcp.json for one agent ───────────────────────────────────

build_mcp_json() {
    local agent_name="$1"
    local result='{"mcpServers":{}}'

    # Default fleet MCP server
    local fleet_cmd fleet_args fleet_env
    fleet_cmd=$(resolve "$(yq -r '.defaults.mcp_servers[0].command // ""' "$CONFIG")" "$agent_name")
    fleet_args=$(yq -r '.defaults.mcp_servers[0].args // [] | @json' "$CONFIG" | sed "s|{{FLEET_DIR}}|$FLEET_DIR|g;s|{{FLEET_VENV}}|$VENV|g;s|{{AGENT_NAME}}|$agent_name|g")
    fleet_env=$(yq -r '.defaults.mcp_servers[0].env // {} | @json' "$CONFIG" | sed "s|{{FLEET_DIR}}|$FLEET_DIR|g;s|{{FLEET_VENV}}|$VENV|g;s|{{AGENT_NAME}}|$agent_name|g")

    result=$(echo "$result" | jq --arg cmd "$fleet_cmd" --argjson args "$fleet_args" --argjson env "$fleet_env" \
        '.mcpServers.fleet = {command: $cmd, args: $args, env: $env}')

    # Role-specific MCP servers
    local server_count
    server_count=$(yq -r ".agents.$agent_name.mcp_servers | length" "$CONFIG" 2>/dev/null) || server_count=0

    local i=0
    while (( i < server_count )); do
        local name package srv_args
        name=$(yq -r ".agents.$agent_name.mcp_servers[$i].name" "$CONFIG")
        package=$(yq -r ".agents.$agent_name.mcp_servers[$i].package // \"\"" "$CONFIG")

        if [[ -n "$package" ]]; then
            # npx-based server
            srv_args=$(yq -r ".agents.$agent_name.mcp_servers[$i].args // [] | @json" "$CONFIG")
            srv_args=$(resolve "$srv_args" "$agent_name")
            # Build: ["npx", "-y", "package", ...extra_args]
            local full_args
            full_args=$(echo "$srv_args" | jq --arg pkg "$package" '[ "-y", $pkg ] + .')
            result=$(echo "$result" | jq --arg n "$name" --argjson a "$full_args" \
                '.mcpServers[$n] = {command: "npx", args: $a}')
        fi

        i=$((i + 1))
    done

    echo "$result" | jq '.'
}

# ─── Deploy for one agent ────────────────────────────────────────────

deploy_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    if [[ ! -d "$agent_dir" ]]; then
        echo -e "  ${YELLOW}[skip]${NC} $agent_name: directory not found"
        return
    fi

    local mcp_path="$agent_dir/mcp.json"
    local new_content
    new_content=$(build_mcp_json "$agent_name")
    local server_count
    server_count=$(echo "$new_content" | jq '.mcpServers | length')

    if [[ -f "$mcp_path" ]]; then
        local existing
        existing=$(cat "$mcp_path")
        if [[ "$existing" == "$new_content" ]]; then
            echo -e "  ${YELLOW}[skip]${NC} $agent_name: mcp.json unchanged ($server_count servers)"
            return
        fi
        echo -e "  ${GREEN}[updated]${NC} $agent_name: mcp.json ($server_count servers)"
    else
        echo -e "  ${GREEN}[created]${NC} $agent_name: mcp.json ($server_count servers)"
    fi

    echo "$new_content" > "$mcp_path"
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet Agent MCP Deployment"
echo "  Config: config/agent-tooling.yaml"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ $# -gt 0 ]]; then
    deploy_agent "$1"
else
    for agent_name in $(yq -r '.agents | keys | .[]' "$CONFIG"); do
        deploy_agent "$agent_name"
    done
fi

echo ""
echo "Done."
