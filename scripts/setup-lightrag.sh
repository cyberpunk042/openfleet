#!/usr/bin/env bash
# setup-lightrag.sh — Complete LightRAG setup for fleet knowledge graph
#
# Installs dependencies, starts the service, indexes knowledge base.
# Idempotent — safe to run multiple times.
#
# Usage:
#   ./scripts/setup-lightrag.sh              # full setup
#   ./scripts/setup-lightrag.sh --deps-only  # install dependencies only
#   ./scripts/setup-lightrag.sh --index-only # index KB only (assumes running)
#
# Prerequisites:
#   - Docker + docker compose
#   - LocalAI running on port 8090 (for LLM + embeddings)
#   - Python 3.11+ with pip

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${FLEET_DIR}/.venv"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Install daniel-lightrag-mcp (MCP server for agent access) ──────

install_mcp_dependency() {
    echo "Installing LightRAG MCP server dependency..."

    if [ -d "$VENV" ]; then
        source "$VENV/bin/activate"
    fi

    # Install daniel-lightrag-mcp in fleet venv
    if uv pip show daniel-lightrag-mcp &>/dev/null; then
        echo -e "  ${YELLOW}[skip]${NC} daniel-lightrag-mcp already installed"
    else
        echo -e "  ${GREEN}[install]${NC} daniel-lightrag-mcp (from GitHub)"
        uv pip install --no-deps "git+https://github.com/desimpkins/daniel-lightrag-mcp.git" 2>&1 | tail -1
    fi
}

# ── Ensure data directories ────────────────────────────────────────

ensure_directories() {
    echo "Ensuring data directories..."
    mkdir -p "${FLEET_DIR}/data/lightrag/inputs"
    echo -e "  ${GREEN}[ok]${NC} data/lightrag/inputs/"
}

# ── Start LightRAG container ──────────────────────────────────────

start_service() {
    echo "Starting LightRAG service..."

    # Check if already running
    if docker compose -f "${FLEET_DIR}/docker-compose.yaml" ps lightrag 2>/dev/null | grep -q "running"; then
        echo -e "  ${YELLOW}[skip]${NC} LightRAG already running"
        return
    fi

    docker compose -f "${FLEET_DIR}/docker-compose.yaml" up -d lightrag
    echo -e "  ${GREEN}[started]${NC} LightRAG on port 9621"

    # Wait for health
    echo "  Waiting for LightRAG to be ready..."
    local attempts=0
    while (( attempts < 30 )); do
        if curl -s -o /dev/null "${LIGHTRAG_URL:-http://localhost:9621}/health" 2>/dev/null; then
            echo -e "  ${GREEN}[ready]${NC} LightRAG is healthy"
            return
        fi
        sleep 2
        attempts=$((attempts + 1))
    done
    echo -e "  ${RED}[timeout]${NC} LightRAG not ready after 60s"
}

# ── Index knowledge base ───────────────────────────────────────────

index_kb() {
    echo ""
    echo "Indexing fleet knowledge base..."
    bash "${FLEET_DIR}/scripts/lightrag-index.sh" --all
}

# ── Verify setup ──────────────────────────────────────────────────

verify() {
    echo ""
    echo "Verifying setup..."

    # Check MCP package
    if uv pip show daniel-lightrag-mcp &>/dev/null; then
        echo -e "  ${GREEN}[✓]${NC} daniel-lightrag-mcp installed"
    else
        echo -e "  ${RED}[✗]${NC} daniel-lightrag-mcp NOT installed"
    fi

    # Check container
    if docker compose -f "${FLEET_DIR}/docker-compose.yaml" ps lightrag 2>/dev/null | grep -q "running"; then
        echo -e "  ${GREEN}[✓]${NC} LightRAG container running"
    else
        echo -e "  ${RED}[✗]${NC} LightRAG container NOT running"
    fi

    # Check health
    if curl -s -o /dev/null "${LIGHTRAG_URL:-http://localhost:9621}/health" 2>/dev/null; then
        echo -e "  ${GREEN}[✓]${NC} LightRAG API responding"
    else
        echo -e "  ${RED}[✗]${NC} LightRAG API NOT responding"
    fi

    # Check agent-tooling has lightrag MCP
    if grep -q "lightrag" "${FLEET_DIR}/config/agent-tooling.yaml"; then
        echo -e "  ${GREEN}[✓]${NC} LightRAG MCP in agent-tooling.yaml"
    else
        echo -e "  ${RED}[✗]${NC} LightRAG MCP NOT in agent-tooling.yaml"
    fi
}

# ── Main ───────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet LightRAG Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

case "${1:-}" in
    --deps-only)
        install_mcp_dependency
        ensure_directories
        verify
        ;;
    --index-only)
        index_kb
        ;;
    ""|--all)
        install_mcp_dependency
        ensure_directories
        start_service
        index_kb
        verify
        ;;
    *)
        echo "Usage: $0 [--all|--deps-only|--index-only]"
        exit 1
        ;;
esac

echo ""
echo "Done."
