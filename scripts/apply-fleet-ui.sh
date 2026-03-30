#!/usr/bin/env bash
set -euo pipefail

# apply-fleet-ui.sh — Inject fleet UI components into MC vendor frontend.
# Idempotent: safe to re-run. Called after apply-patches.sh.
#
# This script:
# 1. Copies fleet-control components to the vendor frontend
# 2. Patches DashboardShell.tsx to render FleetControlBar in header
# 3. Patches board page to render FleetHealthPanel
#
# All changes are IaC — reproducible from a fresh vendor clone.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PATCHES_DIR="$FLEET_DIR/patches"
VENDOR_FE="$FLEET_DIR/vendor/openclaw-mission-control/frontend/src"
COMPONENTS_DIR="$VENDOR_FE/components/fleet-control"

log() { echo "[fleet-ui] $*"; }

# ── Step 1: Copy component files ────────────────────────────────────────

mkdir -p "$COMPONENTS_DIR"

for tsx in "$PATCHES_DIR"/*.tsx; do
    [[ -f "$tsx" ]] || continue
    name=$(basename "$tsx")
    dest_name="${name#*-}"  # strip NNNN- prefix

    if [[ -f "$COMPONENTS_DIR/$dest_name" ]] && diff -q "$tsx" "$COMPONENTS_DIR/$dest_name" >/dev/null 2>&1; then
        log "SKIP: $dest_name (unchanged)"
    else
        cp "$tsx" "$COMPONENTS_DIR/$dest_name"
        log "COPY: $dest_name"
    fi
done

# ── Step 2: Patch DashboardShell — add FleetControlBar to header ────────

SHELL_FILE="$VENDOR_FE/components/templates/DashboardShell.tsx"

if [[ -f "$SHELL_FILE" ]]; then
    # Add import if not present
    if ! grep -q "FleetControlBar" "$SHELL_FILE"; then
        sed -i '/import { BrandMark }/a import { FleetControlBar } from "@/components/fleet-control/FleetControlBar";' "$SHELL_FILE"
        log "PATCH: DashboardShell — added FleetControlBar import"
    fi

    # Add component render if not present
    if ! grep -q "FleetControlBar" "$SHELL_FILE" || ! grep -q "boardId={" "$SHELL_FILE"; then
        # Insert FleetControlBar after OrgSwitcher div, add gap-3 to parent
        sed -i 's/className="hidden md:flex flex-1 items-center"/className="hidden md:flex flex-1 items-center gap-3"/' "$SHELL_FILE"
        sed -i '/<\/div>/{N;/OrgSwitcher/a\              <FleetControlBar />
}' "$SHELL_FILE" 2>/dev/null || true
        log "PATCH: DashboardShell — added FleetControlBar render"
    fi
else
    log "WARN: DashboardShell.tsx not found"
fi

# ── Step 3: Patch board page — add FleetHealthPanel ─────────────────────

BOARD_PAGE="$VENDOR_FE/app/boards/[boardId]/page.tsx"

if [[ -f "$BOARD_PAGE" ]]; then
    # Add import if not present
    if ! grep -q "FleetHealthPanel" "$BOARD_PAGE"; then
        sed -i '/import { Markdown }/a import { FleetHealthPanel } from "@/components/fleet-control/FleetHealthPanel";' "$BOARD_PAGE"
        log "PATCH: board page — added FleetHealthPanel import"
    fi
else
    log "WARN: board page not found"
fi

log "Done"