#!/usr/bin/env bash
# generate-agents-md.sh — Generate synergy-aware AGENTS.md per agent
#
# Usage: bash scripts/generate-agents-md.sh [agent-name]
#
# Reads: config/agent-identities.yaml (names, display names)
# Produces: agents/{name}/AGENTS.md (per tools-agents-standard.md)
#
# Format per colleague:
#   ### {Display Name} — {role}
#   **Contributes to me:** {what they provide + when}
#   **I contribute to them:** {what I provide + when}
#   **When to @mention:** {conditions}

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
IDENTITIES="$FLEET_DIR/config/agent-identities.yaml"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if ! command -v yq &>/dev/null; then
    echo -e "${YELLOW}[dep]${NC} yq required. Run: bash scripts/setup-agent-tools.sh first"
    exit 1
fi

# Synergy matrix from fleet-elevation/15 + config/synergy-matrix.yaml
# Format: target_role|contributor_role|contribution_type|description
SYNERGY_MATRIX=(
    "software-engineer|architect|design_input|approach, files, patterns, constraints"
    "software-engineer|devsecops-expert|security_requirement|what to do and not do security-wise"
    "software-engineer|qa-engineer|qa_test_definition|test criteria the implementation must satisfy"
    "software-engineer|ux-designer|ux_spec|component patterns for user-facing work"
    "architect|software-engineer|feasibility_assessment|validates design against implementation reality"
    "architect|devsecops-expert|security_review|security implications of designs"
    "devops|architect|infrastructure_design|infrastructure architecture and patterns"
    "devops|devsecops-expert|security_requirement|infrastructure security requirements"
    "devops|software-engineer|application_requirements|what the application needs from infrastructure"
    "qa-engineer|software-engineer|implementation_context|what was implemented for test validation"
    "qa-engineer|architect|design_context|architecture context for test strategy"
    "technical-writer|software-engineer|technical_accuracy|verifies docs match implementation"
    "technical-writer|architect|architecture_context|design decisions to formalize as ADRs"
    "devsecops-expert|architect|architecture_context|architecture for security assessment"
    "devsecops-expert|software-engineer|implementation_context|code for security review"
)

# When to @mention per role (from fleet-elevation/15 per-agent operational surface)
declare -A MENTION_GUIDANCE=(
    ["project-manager"]="When blocked, scope unclear, done early, need assignment"
    ["fleet-ops"]="(rarely — finds you through review queue)"
    ["architect"]="Design input unclear, architectural implications discovered, need complexity assessment"
    ["devsecops-expert"]="Security-sensitive decisions, vulnerability discovered"
    ["software-engineer"]="Implementation questions, need feasibility assessment"
    ["qa-engineer"]="Test criteria ambiguous or untestable"
    ["devops"]="Need infrastructure changes, CI/CD issues"
    ["technical-writer"]="Feature needs user documentation"
    ["ux-designer"]="UX spec unclear, need interaction guidance"
    ["accountability-generator"]="(rarely — reads trails automatically)"
)

generate_for_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    [[ -d "$agent_dir" ]] || return

    local display_name
    display_name=$(yq -r ".agents.\"$agent_name\".display_name // \"$agent_name\"" "$IDENTITIES")

    local content="# Fleet Awareness — $display_name
"
    # For each colleague
    for colleague in $(yq -r '.agents | keys | .[]' "$IDENTITIES"); do
        [[ "$colleague" == "$agent_name" ]] && continue

        local col_display
        col_display=$(yq -r ".agents.\"$colleague\".display_name // \"$colleague\"" "$IDENTITIES")

        # Find what they contribute to me
        local contributes_to_me=""
        for entry in "${SYNERGY_MATRIX[@]}"; do
            IFS='|' read -r target contrib_role contrib_type desc <<< "$entry"
            if [[ "$target" == "$agent_name" && "$contrib_role" == "$colleague" ]]; then
                contributes_to_me="$contrib_type ($desc)"
            fi
        done

        # Find what I contribute to them
        local i_contribute=""
        for entry in "${SYNERGY_MATRIX[@]}"; do
            IFS='|' read -r target contrib_role contrib_type desc <<< "$entry"
            if [[ "$target" == "$colleague" && "$contrib_role" == "$agent_name" ]]; then
                i_contribute="$contrib_type ($desc)"
            fi
        done

        # Get mention guidance
        local mention="${MENTION_GUIDANCE[$colleague]:-"When their expertise is needed"}"

        content="$content
### $col_display — $colleague
**Contributes to me:** ${contributes_to_me:-"(no direct contribution — fleet colleague)"}
**I contribute to them:** ${i_contribute:-"(no direct contribution)"}
**When to @mention:** $mention
"
    done

    # Write if changed
    local agents_path="$agent_dir/AGENTS.md"
    if [[ -f "$agents_path" ]]; then
        local existing
        existing=$(cat "$agents_path")
        if [[ "$existing" == "$content" ]]; then
            echo -e "  ${YELLOW}[skip]${NC} $agent_name: unchanged"
            return
        fi
        echo -e "  ${GREEN}[updated]${NC} $agent_name"
    else
        echo -e "  ${GREEN}[created]${NC} $agent_name"
    fi

    echo "$content" > "$agents_path"
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Generate synergy-aware AGENTS.md per agent"
echo "═══════════════════════════════════════════════════════"
echo ""

if [[ $# -gt 0 ]]; then
    generate_for_agent "$1"
else
    for agent_name in $(yq -r '.agents | keys | .[]' "$IDENTITIES"); do
        generate_for_agent "$agent_name"
    done
fi

echo ""
echo "Done."
