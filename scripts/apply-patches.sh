#!/usr/bin/env bash
set -euo pipefail

# Apply fleet patches to vendor dependencies.
# Run after cloning vendor repos (called by setup-mc.sh).
#
# Patches are stored in patches/ as git diff files.
# Each patch targets a specific vendor directory.

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PATCHES_DIR="$FLEET_DIR/patches"

if [[ ! -d "$PATCHES_DIR" ]]; then
    echo "No patches directory, skipping"
    exit 0
fi

echo "=== Applying Vendor Patches ==="

applied=0
skipped=0
failed=0

for patch in "$PATCHES_DIR"/*.patch; do
    [[ -f "$patch" ]] || continue
    name=$(basename "$patch")

    # Read target from first line comment or default to OCMC
    target="$FLEET_DIR/vendor/openclaw-mission-control"

    # Check if already applied (git apply --check with --reverse)
    if cd "$target" && git apply --check --reverse "$patch" 2>/dev/null; then
        echo "  SKIP: $name (already applied)"
        skipped=$((skipped + 1))
        continue
    fi

    # Apply
    if cd "$target" && git apply --check "$patch" 2>/dev/null; then
        git apply "$patch"
        echo "  OK: $name"
        applied=$((applied + 1))
    else
        echo "  FAIL: $name (patch doesn't apply cleanly)"
        failed=$((failed + 1))
    fi
done

echo ""
echo "Patches — Applied: $applied, Skipped: $skipped, Failed: $failed"

# ── Copy new component files ────────────────────────────────────────────
# Files named NNNN-ComponentName.tsx are copied to the vendor frontend.
# Target: vendor/openclaw-mission-control/frontend/src/components/fleet-control/

COMPONENTS_TARGET="$FLEET_DIR/vendor/openclaw-mission-control/frontend/src/components/fleet-control"
copied=0

for component in "$PATCHES_DIR"/*.tsx; do
    [[ -f "$component" ]] || continue
    name=$(basename "$component")
    # Strip the NNNN- prefix to get the actual filename
    dest_name="${name#*-}"

    mkdir -p "$COMPONENTS_TARGET"

    if [[ -f "$COMPONENTS_TARGET/$dest_name" ]]; then
        # Check if content differs
        if diff -q "$component" "$COMPONENTS_TARGET/$dest_name" >/dev/null 2>&1; then
            echo "  SKIP: $name → $dest_name (unchanged)"
            continue
        fi
    fi

    cp "$component" "$COMPONENTS_TARGET/$dest_name"
    echo "  COPY: $name → fleet-control/$dest_name"
    copied=$((copied + 1))
done

# Also copy migration files
for migration in "$PATCHES_DIR"/*-migration-*.py; do
    [[ -f "$migration" ]] || continue
    name=$(basename "$migration")
    dest_name="${name#*-migration-}"
    migrations_target="$FLEET_DIR/vendor/openclaw-mission-control/backend/migrations/versions"
    mkdir -p "$migrations_target"

    if [[ -f "$migrations_target/$dest_name" ]]; then
        echo "  SKIP: $name (migration exists)"
        continue
    fi

    cp "$migration" "$migrations_target/g1a2b3c4d5e6_add_$dest_name"
    echo "  COPY: $name → migrations/"
    copied=$((copied + 1))
done

if [[ $copied -gt 0 ]]; then
    echo "Components copied: $copied"
fi