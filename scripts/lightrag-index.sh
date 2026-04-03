#!/usr/bin/env bash
# lightrag-index.sh — Index fleet knowledge base into LightRAG
#
# Syncs KB entries, manuals, and metadata into the LightRAG knowledge graph.
# Idempotent — LightRAG deduplicates by content hash (MD5).
#
# Usage:
#   ./scripts/lightrag-index.sh                    # index all KB content
#   ./scripts/lightrag-index.sh --branch systems   # index one branch only
#   ./scripts/lightrag-index.sh --scan             # scan input dir for new files
#   ./scripts/lightrag-index.sh --health           # check LightRAG health
#
# Prerequisites:
#   - LightRAG running (docker compose up lightrag)
#   - curl available
#
# Environment:
#   LIGHTRAG_URL   — LightRAG API base URL (default: http://localhost:9621)
#   LIGHTRAG_API_KEY — API key if auth is enabled (default: empty)

set -euo pipefail

LIGHTRAG_URL="${LIGHTRAG_URL:-http://localhost:9621}"
LIGHTRAG_API_KEY="${LIGHTRAG_API_KEY:-}"
FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KB_DIR="${FLEET_DIR}/docs/knowledge-map/kb"
MANUALS_DIR="${FLEET_DIR}/docs/knowledge-map"
INPUT_DIR="${FLEET_DIR}/data/lightrag/inputs"

# Auth header (empty if no key)
AUTH_HEADER=""
if [ -n "$LIGHTRAG_API_KEY" ]; then
    AUTH_HEADER="-H X-API-Key: ${LIGHTRAG_API_KEY}"
fi

# ── Functions ──────────────────────────────────────────────────────

health_check() {
    echo "Checking LightRAG health..."
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" "${LIGHTRAG_URL}/health" 2>/dev/null) || true
    if [ "$response" = "200" ]; then
        echo "  LightRAG is healthy (${LIGHTRAG_URL})"
        return 0
    else
        echo "  ERROR: LightRAG not reachable at ${LIGHTRAG_URL} (HTTP ${response:-timeout})"
        echo "  Run: docker compose up lightrag"
        return 1
    fi
}

upload_file() {
    local file_path="$1"
    local file_name
    file_name=$(basename "$file_path")

    # Upload via documents/upload endpoint
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${LIGHTRAG_URL}/documents/upload" \
        ${AUTH_HEADER} \
        -F "file=@${file_path}" \
        2>/dev/null) || true

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✓ ${file_name}"
        return 0
    else
        echo "  ✗ ${file_name} (HTTP ${http_code:-error})"
        return 1
    fi
}

insert_text() {
    local file_path="$1"
    local file_name
    file_name=$(basename "$file_path")
    local content
    content=$(cat "$file_path")

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${LIGHTRAG_URL}/documents/text" \
        ${AUTH_HEADER} \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg text "$content" --arg desc "$file_name" \
            '{text: $text, description: $desc}')" \
        2>/dev/null) || true

    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✓ ${file_name}"
        return 0
    else
        # Fallback: copy to input dir for scan-based ingestion
        cp "$file_path" "${INPUT_DIR}/${file_name}" 2>/dev/null || true
        echo "  → ${file_name} (copied to inputs for scan)"
        return 0
    fi
}

index_branch() {
    local branch="$1"
    local branch_dir="${KB_DIR}/${branch}"

    if [ ! -d "$branch_dir" ]; then
        echo "  Branch not found: ${branch}"
        return 1
    fi

    local count=0
    local total
    total=$(find "$branch_dir" -name "*.md" | wc -l)
    echo "Indexing branch: ${branch} (${total} files)"

    for file in "${branch_dir}"/*.md; do
        [ -f "$file" ] || continue
        insert_text "$file"
        count=$((count + 1))
    done

    echo "  ${count}/${total} files indexed from ${branch}/"
}

index_manuals() {
    echo "Indexing manuals..."
    local manuals=(
        "agent-manuals.md"
        "methodology-manual.md"
        "standards-manual.md"
        "module-manuals.md"
        "system-manuals-condensed.md"
        "system-manuals-minimal.md"
    )

    for manual in "${manuals[@]}"; do
        local path="${MANUALS_DIR}/${manual}"
        if [ -f "$path" ]; then
            insert_text "$path"
        else
            echo "  - ${manual} (not found)"
        fi
    done
}

index_all() {
    echo "═══════════════════════════════════════════════"
    echo "  LightRAG Fleet Knowledge Indexing"
    echo "═══════════════════════════════════════════════"
    echo ""

    # Ensure input dir exists
    mkdir -p "$INPUT_DIR"

    # Health check first
    health_check || exit 1
    echo ""

    # Index each KB branch
    local branches
    branches=$(find "$KB_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

    for branch in $branches; do
        index_branch "$branch"
        echo ""
    done

    # Index manuals
    index_manuals
    echo ""

    # Trigger scan for any files in input dir
    echo "Triggering document scan..."
    curl -s -X POST "${LIGHTRAG_URL}/documents/scan" \
        ${AUTH_HEADER} \
        -H "Content-Type: application/json" \
        -d '{}' > /dev/null 2>&1 || true
    echo "  Scan triggered"

    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  Indexing complete"
    echo "═══════════════════════════════════════════════"
}

scan_only() {
    echo "Scanning input directory for new documents..."
    health_check || exit 1

    curl -s -X POST "${LIGHTRAG_URL}/documents/scan" \
        ${AUTH_HEADER} \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null || true
    echo "  Scan complete"
}

# ── Main ───────────────────────────────────────────────────────────

case "${1:-}" in
    --health)
        health_check
        ;;
    --scan)
        scan_only
        ;;
    --branch)
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 --branch <branch_name>"
            echo "Available branches:"
            find "$KB_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort | sed 's/^/  /'
            exit 1
        fi
        health_check || exit 1
        index_branch "$2"
        ;;
    --manuals)
        health_check || exit 1
        index_manuals
        ;;
    ""|--all)
        index_all
        ;;
    *)
        echo "Usage: $0 [--all|--branch <name>|--manuals|--scan|--health]"
        exit 1
        ;;
esac
