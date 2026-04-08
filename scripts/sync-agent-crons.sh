#!/usr/bin/env bash
# sync-agent-crons.sh — Deploy CRONs from config/agent-crons.yaml to gateway
#
# Reads CRON definitions per agent, creates/updates gateway CRON jobs.
# Idempotent — existing jobs with matching names are updated, not duplicated.
#
# Usage:
#   bash scripts/sync-agent-crons.sh           # sync all agents
#   bash scripts/sync-agent-crons.sh fleet-ops # sync one agent
#   bash scripts/sync-agent-crons.sh --list    # list current gateway CRONs
#   bash scripts/sync-agent-crons.sh --dry-run # show commands without executing
#
# Requires: yq, gateway CLI (openarms/openclaw)

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$FLEET_DIR/config/agent-crons.yaml"

source "$FLEET_DIR/scripts/lib/vendor.sh"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DRY_RUN=false
LIST_ONLY=false

# ─── Argument parsing ─────────────────────────────────────────────────

AGENT_FILTER=""
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --list) LIST_ONLY=true ;;
        *) AGENT_FILTER="$arg" ;;
    esac
done

# ─── Dependencies ─────────────────────────────────────────────────────

if ! command -v yq &>/dev/null; then
    echo -e "${RED}ERROR:${NC} yq required. Run: bash scripts/setup-agent-tools.sh first"
    exit 1
fi

if [[ -z "$VENDOR_CLI" ]]; then
    if $DRY_RUN; then
        VENDOR_CLI="openclaw"  # placeholder for dry-run preview
        echo -e "  ${YELLOW}[warn]${NC} No gateway CLI found — using '$VENDOR_CLI' for preview"
    else
        echo -e "${RED}ERROR:${NC} No gateway CLI found (openarms or openclaw)"
        exit 1
    fi
fi

if [[ ! -f "$CONFIG" ]]; then
    echo -e "${RED}ERROR:${NC} $CONFIG not found"
    exit 1
fi

# ─── List mode ────────────────────────────────────────────────────────

if $LIST_ONLY; then
    echo "Current gateway CRON jobs:"
    $VENDOR_CLI cron list 2>&1 || echo "(no jobs or gateway not running)"
    exit 0
fi

# ─── Fleet state guard prefix ─────────────────────────────────────────

GUARD_PREFIX=$(yq -r '.fleet_state_guard // ""' "$CONFIG")

# ─── Get existing CRON jobs ───────────────────────────────────────────
# We need to know what already exists to avoid duplicates

get_existing_job_id() {
    local name="$1"
    # Try to find an existing job by name
    $VENDOR_CLI cron list --json 2>/dev/null \
        | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    jobs = data if isinstance(data, list) else data.get('jobs', [])
    for j in jobs:
        if j.get('name') == '$name':
            print(j.get('id', ''))
            sys.exit(0)
except: pass
" 2>/dev/null || true
}

# ─── Deploy CRONs for one agent ──────────────────────────────────────

deploy_agent_crons() {
    local agent_name="$1"

    # Check if agent has CRON config
    local cron_count
    cron_count=$(yq -r ".\"$agent_name\" | length" "$CONFIG" 2>/dev/null) || cron_count=0

    if [[ "$cron_count" == "0" ]] || [[ "$cron_count" == "null" ]]; then
        echo -e "  ${YELLOW}[skip]${NC} $agent_name: no CRONs configured"
        return
    fi

    echo ""
    echo "  $agent_name ($cron_count CRONs):"

    local i=0
    while (( i < cron_count )); do
        local name schedule timezone session model thinking message delivery timeout
        name=$(yq -r ".\"$agent_name\"[$i].name" "$CONFIG")
        schedule=$(yq -r ".\"$agent_name\"[$i].schedule" "$CONFIG")
        timezone=$(yq -r ".\"$agent_name\"[$i].timezone // \"UTC\"" "$CONFIG")
        session=$(yq -r ".\"$agent_name\"[$i].session // \"isolated\"" "$CONFIG")
        model=$(yq -r ".\"$agent_name\"[$i].model // \"sonnet\"" "$CONFIG")
        thinking=$(yq -r ".\"$agent_name\"[$i].thinking // \"medium\"" "$CONFIG")
        message=$(yq -r ".\"$agent_name\"[$i].message" "$CONFIG")
        delivery=$(yq -r ".\"$agent_name\"[$i].delivery // \"none\"" "$CONFIG")
        timeout=$(yq -r ".\"$agent_name\"[$i].timeout_seconds // 300" "$CONFIG")

        # Prepend fleet state guard to message
        local full_message="$message"
        if [[ -n "$GUARD_PREFIX" ]]; then
            full_message="${GUARD_PREFIX}

${message}"
        fi

        # Check if job already exists
        local existing_id
        existing_id=$(get_existing_job_id "$name")

        # Build the CLI command
        local cmd=""
        if [[ -n "$existing_id" ]]; then
            # Update existing job
            cmd="$VENDOR_CLI cron edit $existing_id"
            cmd+=" --message \"$(echo "$full_message" | head -c 2000)\""
            cmd+=" --model \"$model\""
            cmd+=" --thinking \"$thinking\""

            if $DRY_RUN; then
                echo -e "    ${YELLOW}[dry-run]${NC} UPDATE $name ($existing_id)"
            else
                eval "$cmd" 2>/dev/null \
                    && echo -e "    ${GREEN}[updated]${NC} $name ($existing_id)" \
                    || echo -e "    ${RED}[error]${NC} $name: update failed"
            fi
        else
            # Create new job
            cmd="$VENDOR_CLI cron add --name \"$name\""
            cmd+=" --cron \"$schedule\""
            cmd+=" --tz \"$timezone\""
            cmd+=" --session $session"
            cmd+=" --message \"$(echo "$full_message" | head -c 2000)\""
            cmd+=" --model \"$model\""
            cmd+=" --thinking \"$thinking\""
            cmd+=" --agent \"$agent_name\""
            cmd+=" --timeout-seconds $timeout"

            if [[ "$delivery" == "announce" ]]; then
                cmd+=" --announce"
            fi

            if $DRY_RUN; then
                echo -e "    ${YELLOW}[dry-run]${NC} CREATE $name"
                echo "      schedule: $schedule ($timezone)"
                echo "      model: $model, thinking: $thinking, timeout: ${timeout}s"
            else
                eval "$cmd" 2>/dev/null \
                    && echo -e "    ${GREEN}[created]${NC} $name (${schedule} ${timezone})" \
                    || echo -e "    ${RED}[error]${NC} $name: creation failed (gateway running?)"
            fi
        fi

        i=$((i + 1))
    done
}

# ─── Main ─────────────────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════"
echo "  Fleet CRON Sync"
echo "  Config: config/agent-crons.yaml"
echo "  Gateway: $VENDOR_CLI"
if $DRY_RUN; then
    echo "  Mode: DRY RUN (no changes)"
fi
echo "═══════════════════════════════════════════════════════"

if [[ -n "$AGENT_FILTER" ]]; then
    deploy_agent_crons "$AGENT_FILTER"
else
    # Get all agent keys (skip non-agent keys like fleet_state_guard)
    for agent_name in $(yq -r 'keys | .[]' "$CONFIG" | grep -v fleet_state_guard); do
        # Skip if value is not a list (it's a scalar like fleet_state_guard)
        val_type=$(yq -r ".\"$agent_name\" | type" "$CONFIG" 2>/dev/null) || val_type=""
        if [[ "$val_type" == "!!seq" ]] || [[ "$val_type" == "array" ]]; then
            deploy_agent_crons "$agent_name"
        fi
    done
fi

echo ""
if $DRY_RUN; then
    echo "Dry run complete. No changes made."
else
    echo "Done. Run '$VENDOR_CLI cron list' to verify."
fi
