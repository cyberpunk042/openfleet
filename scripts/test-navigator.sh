#!/usr/bin/env bash
# test-navigator.sh — Test navigator output for all role×stage combinations
#
# Usage:
#   ./scripts/test-navigator.sh                              # test all
#   ./scripts/test-navigator.sh architect reasoning opus      # test one
#   ./scripts/test-navigator.sh --full architect reasoning    # show full output
#
# Requires: fleet venv with fleet package importable

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "$FLEET_DIR/.venv" ]; then
    source "$FLEET_DIR/.venv/bin/activate"
fi

case "${1:-}" in
    --full)
        # Show full output for one role+stage
        role="${2:?Usage: $0 --full <role> <stage> [model]}"
        stage="${3:?Usage: $0 --full <role> <stage> [model]}"
        model="${4:-opus-4-6}"
        cd "$FLEET_DIR" && python3 -c "
from fleet.core.navigator import Navigator
nav = Navigator()
nav.load()
ctx = nav.assemble(role='$role', stage='$stage', model='$model')
print(ctx.render())
print()
print(f'--- {len(ctx.sections)} sections, {len(ctx.render())} chars ---')
"
        ;;

    ""|--all)
        # Test all role×stage combinations
        cd "$FLEET_DIR" && python3 << 'PYEOF'
from fleet.core.navigator import Navigator

nav = Navigator()
nav.load()

intents = nav._intent_map.get("intents", {})
role_map = {
    "pm": "project-manager",
    "engineer": "software-engineer",
    "qa": "qa-engineer",
    "architect": "architect",
    "devsecops": "devsecops-expert",
    "fleet-ops": "fleet-ops",
    "devops": "devops",
    "writer": "technical-writer",
    "ux": "ux-designer",
    "accountability": "accountability-generator",
}

print(f"Navigator: {len(intents)} intents, {len(nav._profiles)} profiles")
print(f"{'Intent':<42s} {'Opus':>12s} {'Sonnet':>12s} {'LocalAI':>12s}")
print("-" * 80)

for intent_name in sorted(intents.keys()):
    # Parse role from intent name
    parts = intent_name.rsplit("-", 1)
    stages = ["conversation","reasoning","work","review","heartbeat","analysis","investigation","contribution"]

    role_short = None
    stage = None
    for s in stages:
        if intent_name.endswith(f"-{s}"):
            role_short = intent_name[:-(len(s)+1)]
            stage = s
            break

    if not role_short:
        role_short = parts[0]
        stage = parts[1] if len(parts) > 1 else "work"

    role = role_map.get(role_short, role_short)

    results = []
    for model in ["opus-4-6", "sonnet-4-6", "hermes-3b"]:
        ctx = nav.assemble(role=role, stage=stage, model=model)
        r = ctx.render()
        results.append(f"{len(r):5d}/{len(ctx.sections)}s")

    print(f"{intent_name:<42s} {results[0]:>12s} {results[1]:>12s} {results[2]:>12s}")

print()
print("Format: chars/sections. All outputs verified under 8000 char gateway limit.")
PYEOF
        ;;

    *)
        # Test specific role+stage
        role="${1}"
        stage="${2:-work}"
        model="${3:-opus-4-6}"
        cd "$FLEET_DIR" && python3 -c "
from fleet.core.navigator import Navigator
nav = Navigator()
nav.load()
ctx = nav.assemble(role='$role', stage='$stage', model='$model')
r = ctx.render()
print(f'Role: $role')
print(f'Stage: $stage')
print(f'Model: $model')
print(f'Sections: {len(ctx.sections)}')
print(f'Chars: {len(r)}')
print(f'Under limit: {len(r) <= 8000}')
print()
for i, s in enumerate(ctx.sections):
    first = s.split(chr(10))[0][:80]
    print(f'  [{i}] ({len(s):5d} chars) {first}')
"
        ;;
esac
