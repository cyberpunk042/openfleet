#!/usr/bin/env bash
# provision-agent-files.sh — Provision agent workspace files from templates + config
#
# Usage: bash scripts/provision-agent-files.sh [agent-name]
#   No args: provision all agents
#   With arg: provision specific agent
#
# Reads: agents/_template/, config/agent-identities.yaml, config/agent-tooling.yaml
# Produces: agents/{name}/ with all required files per standards
# Idempotent: only writes files that differ from source, preserves custom content

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
TEMPLATE_DIR="$AGENTS_DIR/_template"
IDENTITIES="$FLEET_DIR/config/agent-identities.yaml"
SCRIPTS_DIR="$FLEET_DIR/scripts"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Dependencies ────────────────────────────────────────────────────

if ! command -v yq &>/dev/null; then
    echo -e "${YELLOW}[dep]${NC} yq not found, installing..."
    mkdir -p "$HOME/.local/bin"
    wget -qO "$HOME/.local/bin/yq" \
        "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64" \
        && chmod +x "$HOME/.local/bin/yq"
    export PATH="$HOME/.local/bin:$PATH"
    command -v yq &>/dev/null || { echo -e "${RED}ERROR:${NC} yq install failed"; exit 1; }
    echo -e "${GREEN}[dep]${NC} yq installed"
fi

if [[ ! -f "$IDENTITIES" ]]; then
    echo -e "${RED}ERROR:${NC} $IDENTITIES not found"
    exit 1
fi

# ─── Counters ────────────────────────────────────────────────────────

CREATED=0
UPDATED=0
SKIPPED=0

# ─── Helpers ─────────────────────────────────────────────────────────

# Copy template with placeholder substitution, only if content differs
copy_template() {
    local src="$1" dst="$2" label="$3"

    if [[ ! -f "$src" ]]; then
        echo -e "    ${YELLOW}[skip]${NC} $label: template not found ($src)"
        return 1
    fi

    local content
    content=$(sed \
        -e "s|{{AGENT_NAME}}|$agent_name|g" \
        -e "s|{{DISPLAY_NAME}}|$display_name|g" \
        -e "s|{{USERNAME}}|$username|g" \
        -e "s|{{FLEET_ID}}|$fleet_id|g" \
        -e "s|{{FLEET_NAME}}|$fleet_name|g" \
        -e "s|{{FLEET_NUMBER}}|$fleet_number|g" \
        "$src")

    write_if_changed "$content" "$dst" "$label"
}

# Copy file only if content differs
copy_if_changed() {
    local src="$1" dst="$2" label="$3"

    if [[ ! -f "$src" ]]; then
        echo -e "    ${YELLOW}[skip]${NC} $label: source not found"
        return
    fi

    if [[ -f "$dst" ]]; then
        if diff -q "$src" "$dst" &>/dev/null; then
            SKIPPED=$((SKIPPED + 1))
            return
        fi
        echo -e "    ${GREEN}[updated]${NC} $label"
        UPDATED=$((UPDATED + 1))
    else
        echo -e "    ${GREEN}[created]${NC} $label"
        CREATED=$((CREATED + 1))
    fi

    cp "$src" "$dst"
}

# Write string content only if differs
write_if_changed() {
    local content="$1" dst="$2" label="$3"

    if [[ -f "$dst" ]]; then
        local existing
        existing=$(cat "$dst")
        if [[ "$existing" == "$content" ]]; then
            SKIPPED=$((SKIPPED + 1))
            return
        fi
        echo -e "    ${GREEN}[updated]${NC} $label"
        UPDATED=$((UPDATED + 1))
    else
        echo -e "    ${GREEN}[created]${NC} $label"
        CREATED=$((CREATED + 1))
    fi

    echo "$content" > "$dst"
}

# ─── Provision one agent ─────────────────────────────────────────────

provision_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    local display_name username fleet_id fleet_name fleet_number
    display_name=$(yq -r ".agents.\"$agent_name\".display_name // \"$agent_name\"" "$IDENTITIES")
    username=$(yq -r ".agents.\"$agent_name\".username // \"$agent_name\"" "$IDENTITIES")
    fleet_id=$(yq -r '.fleet.id // "alpha"' "$IDENTITIES")
    fleet_name=$(yq -r '.fleet.name // "Fleet Alpha"' "$IDENTITIES")
    fleet_number=$(yq -r '.fleet.number // 1' "$IDENTITIES")

    echo ""
    echo "Provisioning agents/$agent_name ($display_name)..."

    # Create directory structure
    mkdir -p "$agent_dir/context"

    # 1. agent.yaml — preserve if it has custom content, template otherwise
    if [[ -f "$agent_dir/agent.yaml" ]]; then
        local existing_mission
        existing_mission=$(yq -r '.mission // ""' "$agent_dir/agent.yaml" 2>/dev/null) || existing_mission=""
        if [[ -n "$existing_mission" && "$existing_mission" != "Define the agent's mission here" ]]; then
            echo -e "    ${YELLOW}[keep]${NC} agent.yaml (has custom mission)"
        else
            local yaml_content
            yaml_content=$(sed "s/^name: template$/name: $agent_name/" "$TEMPLATE_DIR/agent.yaml")
            write_if_changed "$yaml_content" "$agent_dir/agent.yaml" "agent.yaml"
        fi
    else
        local yaml_content
        yaml_content=$(sed "s/^name: template$/name: $agent_name/" "$TEMPLATE_DIR/agent.yaml")
        write_if_changed "$yaml_content" "$agent_dir/agent.yaml" "agent.yaml"
    fi

    # 2. CLAUDE.md — role-specific template with placeholder substitution
    copy_template "$TEMPLATE_DIR/CLAUDE.md/${agent_name}.md" "$agent_dir/CLAUDE.md" "CLAUDE.md"

    # 3. HEARTBEAT.md — role-specific, fallback to worker template
    local heartbeat_src="$TEMPLATE_DIR/heartbeats/${agent_name}.md"
    if [[ ! -f "$heartbeat_src" ]]; then
        heartbeat_src="$TEMPLATE_DIR/heartbeats/worker.md"
    fi
    copy_if_changed "$heartbeat_src" "$agent_dir/HEARTBEAT.md" "HEARTBEAT.md"

    # 4. IDENTITY.md — role-specific template with placeholder substitution
    copy_template "$TEMPLATE_DIR/IDENTITY.md/${agent_name}.md" "$agent_dir/IDENTITY.md" "IDENTITY.md"

    # 5. SOUL.md — role-specific template with placeholder substitution
    copy_template "$TEMPLATE_DIR/SOUL.md/${agent_name}.md" "$agent_dir/SOUL.md" "SOUL.md"

    # 6. TOOLS.md — placeholder if missing or stub (generate-tools-md.sh fills real content)
    if [[ ! -f "$agent_dir/TOOLS.md" ]] || [[ $(wc -c < "$agent_dir/TOOLS.md") -lt 50 ]]; then
        write_if_changed "# Tools — $display_name

Generated by scripts/generate-tools-md.sh. Run: make generate-tools" \
            "$agent_dir/TOOLS.md" "TOOLS.md (placeholder)"
    else
        SKIPPED=$((SKIPPED + 1))
    fi

    # 7. AGENTS.md — placeholder if missing or stub (generate-agents-md.sh fills real content)
    if [[ ! -f "$agent_dir/AGENTS.md" ]] || [[ $(wc -c < "$agent_dir/AGENTS.md") -lt 50 ]]; then
        write_if_changed "# Colleagues — $display_name

Generated by scripts/generate-agents-md.sh. Run: make generate-agents" \
            "$agent_dir/AGENTS.md" "AGENTS.md (placeholder)"
    else
        SKIPPED=$((SKIPPED + 1))
    fi

    # 8. context/ files — initial stubs if not present
    if [[ ! -f "$agent_dir/context/fleet-context.md" ]]; then
        write_if_changed "# Fleet context — generated by orchestrator each cycle" \
            "$agent_dir/context/fleet-context.md" "context/fleet-context.md"
    fi
    if [[ ! -f "$agent_dir/context/task-context.md" ]]; then
        write_if_changed "# Task context — generated by orchestrator at dispatch" \
            "$agent_dir/context/task-context.md" "context/task-context.md"
    fi
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet Agent File Provisioning"
echo "  Templates: agents/_template/"
echo "  Config: config/agent-identities.yaml"
echo "═══════════════════════════════════════════════════════"

if [[ $# -gt 0 ]]; then
    provision_agent "$1"
else
    for agent_name in $(yq -r '.agents | keys | .[]' "$IDENTITIES"); do
        provision_agent "$agent_name"
    done
fi

# Deploy MCP configs
echo ""
echo "─── MCP Deployment ────────────────────────────────────"
if [[ $# -gt 0 ]]; then
    bash "$SCRIPTS_DIR/setup-agent-tools.sh" "$1"
else
    bash "$SCRIPTS_DIR/setup-agent-tools.sh"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Provisioning complete"
echo -e "  ${GREEN}Created: ${CREATED}${NC}  ${GREEN}Updated: ${UPDATED}${NC}  ${YELLOW}Kept/Skipped: ${SKIPPED}${NC}"
echo ""
echo "  Next: make validate-agents"
echo "═══════════════════════════════════════════════════════"
