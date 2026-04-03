#!/usr/bin/env bash
# setup-fleet-knowledge.sh — Complete fleet knowledge infrastructure setup
#
# Runs ALL setup steps in the right order:
#   1. Install pip MCP dependencies (lightrag-mcp, pytest-mcp)
#   2. Start LightRAG container
#   3. Index knowledge base into graph
#   4. Configure claude-mem per-agent
#   5. Deploy MCP configs per-agent from agent-tooling.yaml
#   6. Install plugins per-agent
#   7. Verify everything
#
# Usage:
#   ./scripts/setup-fleet-knowledge.sh         # full setup
#   ./scripts/setup-fleet-knowledge.sh --check  # verify only
#
# Prerequisites:
#   - Docker + docker compose
#   - LocalAI running on port 8090
#   - Fleet venv exists (.venv/)
#   - claude CLI installed

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$FLEET_DIR/scripts"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

step() {
    local num="$1" desc="$2"
    echo ""
    echo -e "${BOLD}═══ Step $num: $desc ═══${NC}"
}

# ── Verify mode ────────────────────────────────────────────────────

verify_all() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Fleet Knowledge Infrastructure — Verification${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""

    local pass=0 fail=0

    check() {
        local desc="$1" result="$2"
        if [ "$result" = "ok" ]; then
            echo -e "  ${GREEN}[✓]${NC} $desc"
            pass=$((pass + 1))
        else
            echo -e "  ${RED}[✗]${NC} $desc"
            fail=$((fail + 1))
        fi
    }

    # Venv
    [ -d "$FLEET_DIR/.venv" ] && check "Fleet venv" "ok" || check "Fleet venv" "fail"

    # Pip packages
    source "$FLEET_DIR/.venv/bin/activate" 2>/dev/null || true
    uv pip show daniel-lightrag-mcp &>/dev/null && check "daniel-lightrag-mcp" "ok" || check "daniel-lightrag-mcp" "fail"

    # Docker
    command -v docker &>/dev/null && check "Docker installed" "ok" || check "Docker installed" "fail"

    # LightRAG container
    if docker compose -f "$FLEET_DIR/docker-compose.yaml" ps lightrag 2>/dev/null | grep -q "running"; then
        check "LightRAG container running" "ok"
    else
        check "LightRAG container running" "fail"
    fi

    # LightRAG API
    curl -s -o /dev/null "http://localhost:9621/health" 2>/dev/null && check "LightRAG API responding" "ok" || check "LightRAG API responding" "fail"

    # LocalAI
    curl -s -o /dev/null "http://localhost:8090/v1/models" 2>/dev/null && check "LocalAI API responding" "ok" || check "LocalAI API responding" "fail"

    # Knowledge map
    local kb_count
    kb_count=$(find "$FLEET_DIR/docs/knowledge-map/kb/" -name "*.md" 2>/dev/null | wc -l)
    [ "$kb_count" -gt 100 ] && check "Knowledge map ($kb_count entries)" "ok" || check "Knowledge map ($kb_count entries)" "fail"

    # Navigator
    python3 -c "from fleet.core.navigator import Navigator; n=Navigator(); n.load(); assert n._loaded" 2>/dev/null && check "Navigator module loads" "ok" || check "Navigator module loads" "fail"

    # Agent tooling config
    [ -f "$FLEET_DIR/config/agent-tooling.yaml" ] && check "agent-tooling.yaml exists" "ok" || check "agent-tooling.yaml" "fail"

    # LightRAG MCP in agent-tooling
    grep -q "lightrag" "$FLEET_DIR/config/agent-tooling.yaml" && check "LightRAG MCP in tooling" "ok" || check "LightRAG MCP in tooling" "fail"

    # safety-net in defaults
    grep -q "safety-net" "$FLEET_DIR/config/agent-tooling.yaml" && check "safety-net in defaults" "ok" || check "safety-net in defaults" "fail"

    # Claude CLI
    command -v claude &>/dev/null && check "Claude CLI installed" "ok" || check "Claude CLI installed" "fail"

    echo ""
    echo -e "  ${GREEN}$pass passed${NC}, ${RED}$fail failed${NC}"
    echo ""

    [ "$fail" -eq 0 ] && return 0 || return 1
}

# ── Full setup ─────────────────────────────────────────────────────

full_setup() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Fleet Knowledge Infrastructure — Full Setup${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"

    step 1 "MCP Dependencies"
    bash "$SCRIPTS/setup-mcp-deps.sh"

    step 2 "LightRAG Service"
    bash "$SCRIPTS/setup-lightrag.sh"

    step 3 "Claude-Mem Per-Agent"
    bash "$SCRIPTS/setup-claude-mem.sh"

    step 4 "Agent MCP Configs"
    bash "$SCRIPTS/setup-agent-tools.sh"

    step 5 "Agent Plugins"
    bash "$SCRIPTS/install-plugins.sh"

    step 6 "Verification"
    verify_all

    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Setup Complete${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Access:"
    echo "    LightRAG API:   http://localhost:9621"
    echo "    LightRAG WebUI: http://localhost:9621/webui/"
    echo "    Mission Control: http://localhost:3000"
    echo ""
    echo "  Next:"
    echo "    docker compose up -d     # start all services"
    echo "    ./scripts/lightrag-index.sh --health"
    echo ""
}

# ── Main ───────────────────────────────────────────────────────────

case "${1:-}" in
    --check|--verify)
        verify_all
        ;;
    ""|--all)
        full_setup
        ;;
    *)
        echo "Usage: $0 [--all|--check]"
        exit 1
        ;;
esac
