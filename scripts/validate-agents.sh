#!/usr/bin/env bash
# validate-agents.sh — Validate all agent files against per-type standards
#
# Usage: bash scripts/validate-agents.sh [agent-name]
#   No args: validate all agents
#   With arg: validate specific agent
#
# Standards: docs/milestones/active/standards/

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_DIR="$FLEET_DIR/agents"
TEMPLATE_DIR="$AGENTS_DIR/_template"

# Counters
TOTAL_PASS=0
TOTAL_WARN=0
TOTAL_FAIL=0
AGENTS_CHECKED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; TOTAL_PASS=$((TOTAL_PASS + 1)); }
warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; TOTAL_WARN=$((TOTAL_WARN + 1)); }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; TOTAL_FAIL=$((TOTAL_FAIL + 1)); }

# ─── File existence checks ──────────────────────────────────────────

check_file_exists() {
    local agent_dir="$1" file="$2"
    if [[ -f "$agent_dir/$file" ]]; then
        pass "$file exists"
    else
        fail "$file MISSING"
    fi
}

# ─── CLAUDE.md checks ───────────────────────────────────────────────

check_claude_md() {
    local agent_dir="$1" agent_name="$2"
    local file="$agent_dir/CLAUDE.md"
    [[ -f "$file" ]] || return

    # Char count (max 4000)
    local chars
    chars=$(wc -c < "$file")
    if (( chars <= 4000 )); then
        pass "CLAUDE.md: ${chars} chars (under 4000 limit)"
    else
        fail "CLAUDE.md: ${chars} chars EXCEEDS 4000 limit"
    fi

    # Required sections
    for section in "Core Responsibility" "Stage Protocol" "Anti-Corruption"; do
        if grep -qi "$section" "$file" 2>/dev/null; then
            pass "CLAUDE.md: '$section' section present"
        else
            warn "CLAUDE.md: '$section' section missing"
        fi
    done

    # Check for generic/template content
    if grep -q "{{" "$file" 2>/dev/null; then
        fail "CLAUDE.md: contains unresolved {{placeholders}}"
    fi
}

# ─── SOUL.md checks ─────────────────────────────────────────────────

check_soul_md() {
    local agent_dir="$1"
    local file="$agent_dir/SOUL.md"
    [[ -f "$file" ]] || return

    # Anti-corruption rules (should have 10)
    local rule_count=0
    rule_count=$(grep -cE '^\s*[0-9]+\.' "$file" 2>/dev/null) || rule_count=0
    if (( rule_count >= 10 )); then
        pass "SOUL.md: ${rule_count} numbered rules (>= 10 required)"
    elif (( rule_count >= 5 )); then
        warn "SOUL.md: only ${rule_count} numbered rules (10 required)"
    else
        fail "SOUL.md: only ${rule_count} numbered rules (10 required)"
    fi
}

# ─── IDENTITY.md checks ─────────────────────────────────────────────

check_identity_md() {
    local agent_dir="$1"
    local file="$agent_dir/IDENTITY.md"
    [[ -f "$file" ]] || return

    # Fleet identity fields
    for field in "fleet" "role" "expert"; do
        if grep -qi "$field" "$file" 2>/dev/null; then
            pass "IDENTITY.md: '$field' reference present"
        else
            warn "IDENTITY.md: '$field' reference missing"
        fi
    done
}

# ─── agent.yaml checks ──────────────────────────────────────────────

check_agent_yaml() {
    local agent_dir="$1" agent_name="$2"
    local file="$agent_dir/agent.yaml"
    [[ -f "$file" ]] || return

    # Required fields
    for field in "name" "mission" "capabilities" "mode" "backend"; do
        if grep -q "^${field}:" "$file" 2>/dev/null; then
            pass "agent.yaml: '$field' field present"
        else
            fail "agent.yaml: '$field' field MISSING"
        fi
    done

    # Name consistency
    local yaml_name
    yaml_name=$(grep "^name:" "$file" | head -1 | awk '{print $2}')
    if [[ "$yaml_name" == "$agent_name" ]]; then
        pass "agent.yaml: name matches directory ($agent_name)"
    else
        fail "agent.yaml: name '$yaml_name' doesn't match directory '$agent_name'"
    fi
}

# ─── HEARTBEAT.md checks ────────────────────────────────────────────

check_heartbeat_md() {
    local agent_dir="$1"
    local file="$agent_dir/HEARTBEAT.md"
    [[ -f "$file" ]] || return

    local lines
    lines=$(wc -l < "$file")
    if (( lines >= 5 )); then
        pass "HEARTBEAT.md: ${lines} lines (substantive)"
    else
        warn "HEARTBEAT.md: only ${lines} lines (may be too thin)"
    fi

    # Check for HEARTBEAT_OK mention
    if grep -q "HEARTBEAT_OK" "$file" 2>/dev/null; then
        pass "HEARTBEAT.md: HEARTBEAT_OK protocol referenced"
    else
        warn "HEARTBEAT.md: HEARTBEAT_OK not mentioned"
    fi
}

# ─── mcp.json checks ────────────────────────────────────────────────

check_mcp_json() {
    local agent_dir="$1"
    local file="$agent_dir/mcp.json"
    if [[ ! -f "$file" ]]; then
        warn "mcp.json: not deployed yet (B3 pending)"
        return
    fi

    # Valid JSON
    if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
        pass "mcp.json: valid JSON"
    else
        fail "mcp.json: INVALID JSON"
        return
    fi

    # Fleet MCP server present
    if grep -q '"fleet"' "$file" 2>/dev/null; then
        pass "mcp.json: fleet MCP server configured"
    else
        fail "mcp.json: fleet MCP server MISSING"
    fi
}

# ─── Validate one agent ─────────────────────────────────────────────

validate_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    if [[ ! -d "$agent_dir" ]]; then
        echo "ERROR: Agent directory not found: $agent_dir"
        return 1
    fi

    echo ""
    echo "Validating agents/$agent_name..."
    AGENTS_CHECKED=$((AGENTS_CHECKED + 1))

    # File existence
    check_file_exists "$agent_dir" "agent.yaml"
    check_file_exists "$agent_dir" "CLAUDE.md"
    check_file_exists "$agent_dir" "HEARTBEAT.md"
    check_file_exists "$agent_dir" "IDENTITY.md"
    check_file_exists "$agent_dir" "SOUL.md"
    check_file_exists "$agent_dir" "TOOLS.md"
    check_file_exists "$agent_dir" "AGENTS.md"

    # Per-type checks
    check_claude_md "$agent_dir" "$agent_name"
    check_soul_md "$agent_dir"
    check_identity_md "$agent_dir"
    check_agent_yaml "$agent_dir" "$agent_name"
    check_heartbeat_md "$agent_dir"
    check_mcp_json "$agent_dir"

    # Context directory
    if [[ -d "$agent_dir/context" ]]; then
        pass "context/ directory exists"
    else
        warn "context/ directory missing (created at runtime)"
    fi
}

# ─── Main ────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet Agent Validation"
echo "  Standards: docs/milestones/active/standards/"
echo "═══════════════════════════════════════════════════════"

if [[ $# -gt 0 ]]; then
    # Validate specific agent
    validate_agent "$1"
else
    # Validate all agents (skip _template)
    for agent_dir in "$AGENTS_DIR"/*/; do
        agent_name=$(basename "$agent_dir")
        [[ "$agent_name" == "_template" ]] && continue
        validate_agent "$agent_name"
    done
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results: ${AGENTS_CHECKED} agents checked"
echo -e "  ${GREEN}PASS: ${TOTAL_PASS}${NC}  ${YELLOW}WARN: ${TOTAL_WARN}${NC}  ${RED}FAIL: ${TOTAL_FAIL}${NC}"
echo "═══════════════════════════════════════════════════════"

if (( TOTAL_FAIL > 0 )); then
    exit 1
fi
exit 0
