#!/usr/bin/env bash
# setup-lightrag.sh — Complete LightRAG setup for fleet knowledge graph
#
# Installs dependencies, starts services, syncs KB to graph.
# Idempotent — safe to run multiple times.
#
# Usage:
#   ./scripts/setup-lightrag.sh              # full setup + sync
#   ./scripts/setup-lightrag.sh --clean      # wipe graph + Redis cache, fresh sync
#   ./scripts/setup-lightrag.sh --sync       # incremental sync (changed KB only)
#   ./scripts/setup-lightrag.sh --deps-only  # install dependencies only
#   ./scripts/setup-lightrag.sh --verify     # verify health only
#
# Prerequisites:
#   - Docker + docker compose
#   - LocalAI running on port 8090
#   - Fleet venv with uv

set -u

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${FLEET_DIR}/.venv"
COMPOSE="${FLEET_DIR}/docker-compose.yaml"
LIGHTRAG_URL="${LIGHTRAG_URL:-http://localhost:9621}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Activate venv ─────────────────────────────────────────────────

activate_venv() {
    if [ -d "$VENV" ]; then
        source "$VENV/bin/activate"
    else
        echo -e "${RED}ERROR:${NC} venv not found at $VENV"
        exit 1
    fi
}

# ── Install dependencies ──────────────────────────────────────────

install_deps() {
    echo "Installing dependencies..."
    activate_venv

    if uv pip show daniel-lightrag-mcp &>/dev/null 2>&1; then
        echo -e "  ${YELLOW}[skip]${NC} daniel-lightrag-mcp"
    else
        echo -e "  ${GREEN}[install]${NC} daniel-lightrag-mcp (from GitHub)"
        uv pip install --no-deps "git+https://github.com/desimpkins/daniel-lightrag-mcp.git" 2>&1 | tail -1
    fi

    for pkg in anthropic openai pytest-mcp; do
        if uv pip show "$pkg" &>/dev/null 2>&1; then
            echo -e "  ${YELLOW}[skip]${NC} $pkg"
        else
            echo -e "  ${GREEN}[install]${NC} $pkg"
            uv pip install "$pkg" 2>&1 | tail -1
        fi
    done
}

# ── Ensure data directories ───────────────────────────────────────

ensure_dirs() {
    mkdir -p "${FLEET_DIR}/data/lightrag/inputs"
}

# ── Clean — wipe graph storage + Redis cache ──────────────────────

clean() {
    echo "Cleaning LightRAG storage..."

    echo "  Stopping LightRAG..."
    docker compose -f "$COMPOSE" stop lightrag 2>&1 || echo "  (not running)"
    echo "  Removing container..."
    docker compose -f "$COMPOSE" rm -f lightrag 2>&1 || echo "  (not found)"
    echo "  Removing volume..."
    docker volume rm openclaw-fleet_lightrag_storage 2>&1 || echo "  (not found)"
    echo -e "  ${GREEN}[ok]${NC} LightRAG storage wiped"

    echo "  Flushing Redis DB 1..."
    docker exec openclaw-fleet-redis-1 redis-cli -n 1 FLUSHDB 2>&1 || echo "  (Redis not running — starting it)"
    # If Redis wasn't running, start it and flush
    if ! docker exec openclaw-fleet-redis-1 redis-cli PING 2>&1 | grep -q PONG; then
        docker compose -f "$COMPOSE" up -d redis 2>&1
        sleep 3
        docker exec openclaw-fleet-redis-1 redis-cli -n 1 FLUSHDB 2>&1 || echo "  (flush failed)"
    fi
    echo -e "  ${GREEN}[ok]${NC} Redis DB 1 flushed"

    echo "  Clearing sync state..."
    rm -f "${FLEET_DIR}/.kb-graph-sync.json"
    echo -e "  ${GREEN}[ok]${NC} Sync state cleared"
}

# ── Start services ────────────────────────────────────────────────

start_services() {
    echo "Starting services..."

    # Ensure Redis is up (LightRAG depends on it)
    docker compose -f "$COMPOSE" up -d redis     sleep 2

    # Start LightRAG
    docker compose -f "$COMPOSE" up -d lightrag
    echo -e "  ${GREEN}[started]${NC} LightRAG"

    # Wait for health
    echo "  Waiting for LightRAG..."
    local attempts=0
    while (( attempts < 30 )); do
        if curl -s -o /dev/null "$LIGHTRAG_URL/health" 2>/dev/null; then
            echo -e "  ${GREEN}[ready]${NC} LightRAG healthy at $LIGHTRAG_URL"
            return 0
        fi
        sleep 2
        attempts=$((attempts + 1))
    done
    echo -e "  ${RED}[timeout]${NC} LightRAG not ready after 60s"
    return 1
}

# ── Sync KB to graph ──────────────────────────────────────────────

sync_full() {
    echo ""
    echo "Syncing KB + sources to knowledge graph (full)..."
    echo "  Sources: Python modules, config YAMLs, docs, agent templates, SKILL.md files"
    activate_venv
    python -u -m fleet.core.kb_sync --full --url "$LIGHTRAG_URL"
    echo ""
    echo "  Verifying graph content..."
    local labels
    labels=$(curl -s "$LIGHTRAG_URL/graph/label/list" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo -e "  ${GREEN}[ok]${NC} Graph has $labels entity labels"
}

sync_incremental() {
    echo ""
    echo "Syncing KB to knowledge graph (incremental)..."
    activate_venv
    python -m fleet.core.kb_sync --sync --url "$LIGHTRAG_URL"
}

# ── Verify ────────────────────────────────────────────────────────

verify() {
    echo ""
    echo "Verifying..."

    local pass=0 fail=0

    check() {
        if [ "$2" = "ok" ]; then
            echo -e "  ${GREEN}[✓]${NC} $1"
            pass=$((pass + 1))
        else
            echo -e "  ${RED}[✗]${NC} $1"
            fail=$((fail + 1))
        fi
    }

    activate_venv || true

    uv pip show daniel-lightrag-mcp &>/dev/null 2>&1 && check "daniel-lightrag-mcp" "ok" || check "daniel-lightrag-mcp" "fail"
    curl -s -o /dev/null "$LIGHTRAG_URL/health" 2>/dev/null && check "LightRAG API" "ok" || check "LightRAG API" "fail"
    curl -s -o /dev/null "http://localhost:8090/v1/models" 2>/dev/null && check "LocalAI API" "ok" || check "LocalAI API" "fail"
    grep -q "lightrag" "${FLEET_DIR}/config/agent-tooling.yaml" && check "LightRAG MCP in tooling" "ok" || check "LightRAG MCP in tooling" "fail"

    # Check graph has content
    local nodes
    nodes=$(curl -s "$LIGHTRAG_URL/graph/label/popular?limit=1" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")
    [ "$nodes" -gt 0 ] 2>/dev/null && check "Graph has entities ($nodes labels)" "ok" || check "Graph has entities" "fail"

    echo ""
    echo -e "  ${GREEN}$pass passed${NC}, ${RED}$fail failed${NC}"
}

# ── Main ──────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet LightRAG Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

case "${1:-}" in
    --clean)
        clean
        install_deps
        ensure_dirs
        start_services
        sync_full
        verify
        ;;
    --sync)
        sync_incremental
        ;;
    --deps-only)
        install_deps
        ensure_dirs
        ;;
    --verify)
        verify
        ;;
    ""|--all)
        install_deps
        ensure_dirs
        start_services
        sync_full
        verify
        ;;
    *)
        echo "Usage: $0 [--all|--clean|--sync|--deps-only|--verify]"
        exit 1
        ;;
esac

echo ""
echo "Done."
