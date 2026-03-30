#!/usr/bin/env bash
set -euo pipefail

# Start Mission Control and configure it
echo "=== Setting Up Mission Control ==="

FLEET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FLEET_DIR"

# Check .env
if [[ ! -f .env ]]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    # Generate auth token
    TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    sed -i "s/LOCAL_AUTH_TOKEN=.*/LOCAL_AUTH_TOKEN=${TOKEN}/" .env
    echo "Generated LOCAL_AUTH_TOKEN"
    # Ensure Postgres port doesn't conflict with Plane (5432)
    if ! grep -q "POSTGRES_PORT" .env; then
        echo "POSTGRES_PORT=5433" >> .env
    fi
fi

# Ensure Postgres port is 5433 (Plane uses 5432)
if grep -q "POSTGRES_PORT=5432" .env 2>/dev/null; then
    sed -i 's/POSTGRES_PORT=5432/POSTGRES_PORT=5433/' .env
    echo "Fixed POSTGRES_PORT: 5432 → 5433 (avoid Plane conflict)"
fi

# Clone vendor if needed
if [[ ! -d vendor/openclaw-mission-control ]]; then
    echo "Cloning Mission Control..."
    mkdir -p vendor
    git clone https://github.com/abhi1693/openclaw-mission-control.git vendor/openclaw-mission-control
fi

# Apply fleet patches to vendor
bash scripts/apply-patches.sh
bash scripts/apply-fleet-ui.sh

# Start Docker services
echo "Starting Mission Control services..."
docker compose up -d --build 2>&1 | tail -5

# Wait for backend
echo "Waiting for backend..."
for i in $(seq 1 20); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "Mission Control backend ready"
        break
    fi
    echo "  waiting... ($i/20)"
    sleep 3
done

# Run fleet setup (registers gateway, board, agents in MC)
echo ""
echo "Running fleet setup..."
source .env 2>/dev/null || true
python3 -m gateway.setup

# Configure board custom fields and tags
echo ""
bash scripts/configure-board.sh

# Template sync already handled by gateway.setup (step 7 above).
# If it timed out there, retry once with a 180s timeout.
echo ""
source .env 2>/dev/null || true
if [[ -n "${LOCAL_AUTH_TOKEN:-}" ]]; then
    ONLINE=$(curl -sf -m 5 -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
        http://localhost:8000/api/v1/agents \
        | python3 -c "
import json,sys
data = json.load(sys.stdin)
items = data.get('items',data) if isinstance(data,dict) else data
online = sum(1 for a in items if a.get('status')=='online' and 'Gateway' not in a.get('name',''))
total = sum(1 for a in items if 'Gateway' not in a.get('name',''))
print(f'{online}/{total}')
" 2>/dev/null || echo "?/?")
    echo "Agent status: $ONLINE online"

    if [[ "$ONLINE" == "0/"* ]]; then
        echo "Retrying template sync (180s timeout)..."
        GW_ID=$(curl -sf -m 5 -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
            http://localhost:8000/api/v1/gateways \
            | python3 -c "
import json,sys; data=json.load(sys.stdin)
items=data.get('items',data) if isinstance(data,dict) else data
print(next(g['id'] for g in items if 'OCF' in g.get('name','') or 'OpenClaw' in g.get('name','')))
" 2>/dev/null || true)
        if [[ -n "${GW_ID:-}" ]]; then
            RESULT=$(curl -sf -m 180 -X POST \
                -H "Authorization: Bearer $LOCAL_AUTH_TOKEN" \
                -H "Content-Type: application/json" \
                "http://localhost:8000/api/v1/gateways/${GW_ID}/templates/sync?rotate_tokens=true&force_bootstrap=true" \
                -d '{}' 2>&1 || echo '{"agents_updated":"?","errors":[]}')
            UPDATED=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('agents_updated',0))" 2>/dev/null || echo "?")
            echo "Retry result: $UPDATED agents updated"
        fi
    fi
else
    echo "WARN: No LOCAL_AUTH_TOKEN, skipping agent check"
fi

# Push SOUL.md and Claude Code settings to agent workspaces
echo ""
echo "Pushing SOUL.md and workspace settings..."
bash scripts/push-soul.sh

# Register skill packs in marketplace and install skills
echo ""
bash scripts/register-skill-packs.sh
echo ""
echo "Installing fleet skills..."
bash scripts/install-skills.sh