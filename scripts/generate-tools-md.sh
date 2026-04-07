#!/usr/bin/env bash
# generate-tools-md.sh — Generate chain-aware TOOLS.md per agent
#
# Usage: bash scripts/generate-tools-md.sh [agent-name]
#
# Reads:
#   fleet/mcp/tools.py           (tool names from code — source of truth)
#   config/tool-chains.yaml      (chain documentation per tool)
#   config/agent-tooling.yaml    (per-role MCP servers + skills)
#   config/agent-identities.yaml (display names)
# Produces: agents/{name}/TOOLS.md (chain-aware, per standards)

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
TOOLING_CONFIG="$FLEET_DIR/config/agent-tooling.yaml"
CHAINS_CONFIG="$FLEET_DIR/config/tool-chains.yaml"
IDENTITIES="$FLEET_DIR/config/agent-identities.yaml"
TOOLS_PY="$FLEET_DIR/fleet/mcp/tools.py"
VENV="$FLEET_DIR/.venv"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if ! command -v yq &>/dev/null; then
    echo -e "${YELLOW}[dep]${NC} yq required. Run: bash scripts/setup-agent-tools.sh first"
    exit 1
fi

# Extract tool names from tools.py (source of truth for what tools exist)
extract_tool_names() {
    "$VENV/bin/python" -c "
import ast
with open('$TOOLS_PY') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
        if node.name.startswith('fleet_'):
            print(node.name)
" 2>/dev/null || true
}

TOOL_NAMES=$(extract_tool_names)

generate_for_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    [[ -d "$agent_dir" ]] || return

    local display_name
    display_name=$(yq -r ".agents.\"$agent_name\".display_name // \"$agent_name\"" \
        "$IDENTITIES" 2>/dev/null) || display_name="$agent_name"

    # ── Build tool section from chain docs ──────────────────────

    local tool_section=""
    while IFS= read -r tool_name; do
        [[ -z "$tool_name" ]] && continue

        local what when chain input auto blocked
        what=$(yq -r ".tools.\"$tool_name\".what // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || what=""
        when=$(yq -r ".tools.\"$tool_name\".when // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || when=""
        chain=$(yq -r ".tools.\"$tool_name\".chain // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || chain=""
        input=$(yq -r ".tools.\"$tool_name\".input // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || input=""
        auto=$(yq -r ".tools.\"$tool_name\".auto // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || auto=""
        blocked=$(yq -r ".tools.\"$tool_name\".blocked // \"\"" "$CHAINS_CONFIG" 2>/dev/null) || blocked=""

        if [[ -n "$what" ]]; then
            tool_section="$tool_section
### $tool_name
**What:** $what
**When:** $when
**Chain:** $chain
**Input:** $input"
            [[ -n "$auto" ]] && tool_section="$tool_section
**You do NOT need to:** $auto"
            [[ -n "$blocked" ]] && tool_section="$tool_section
**$blocked**"
            tool_section="$tool_section
"
        else
            # Tool exists in code but no chain doc yet
            tool_section="$tool_section
### $tool_name
(chain documentation pending)
"
        fi
    done <<< "$TOOL_NAMES"

    # ── Build MCP servers section ───────────────────────────────

    local mcp_section="- fleet (all fleet tools)"
    local mcp_count
    mcp_count=$(yq -r ".agents.\"$agent_name\".mcp_servers | length" "$TOOLING_CONFIG" 2>/dev/null) || mcp_count=0
    local i=0
    while (( i < mcp_count )); do
        local srv_name
        srv_name=$(yq -r ".agents.\"$agent_name\".mcp_servers[$i].name" "$TOOLING_CONFIG")
        mcp_section="$mcp_section
- $srv_name"
        i=$((i + 1))
    done

    # ── Build skills section ────────────────────────────────────

    local skills_section=""
    local skill_count
    skill_count=$(yq -r ".agents.\"$agent_name\".skills | length" "$TOOLING_CONFIG" 2>/dev/null) || skill_count=0
    i=0
    while (( i < skill_count )); do
        local skill
        skill=$(yq -r ".agents.\"$agent_name\".skills[$i]" "$TOOLING_CONFIG")
        skills_section="$skills_section
- /$skill"
        i=$((i + 1))
    done

    # ── Assemble TOOLS.md ───────────────────────────────────────

    local content="# Tools — $display_name

## Fleet MCP Tools
$tool_section
## MCP Servers

$mcp_section"

    if [[ -n "$skills_section" ]]; then
        content="$content

## Skills (slash commands)
$skills_section"
    fi

    # ── Write if changed ────────────────────────────────────────

    local tools_path="$agent_dir/TOOLS.md"
    if [[ -f "$tools_path" ]]; then
        local existing
        existing=$(cat "$tools_path")
        if [[ "$existing" == "$content" ]]; then
            echo -e "  ${YELLOW}[skip]${NC} $agent_name: unchanged"
            return
        fi
        echo -e "  ${GREEN}[updated]${NC} $agent_name"
    else
        echo -e "  ${GREEN}[created]${NC} $agent_name"
    fi

    echo "$content" > "$tools_path"
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Generate chain-aware TOOLS.md per agent"
echo "  Chain docs: config/tool-chains.yaml"
echo "  Tool names: fleet/mcp/tools.py"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ $# -gt 0 ]]; then
    generate_for_agent "$1"
else
    for agent_name in $(yq -r '.agents | keys | .[]' "$TOOLING_CONFIG"); do
        generate_for_agent "$agent_name"
    done
fi

echo ""
echo "Done."
