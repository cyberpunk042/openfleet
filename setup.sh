#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Fleet — Full Setup
#
# Takes you from a fresh clone to a running fleet.
# Run: ./setup.sh
#
# What it does:
# 1. Installs OpenClaw
# 2. Configures OpenClaw gateway (bind, controlUi)
# 3. Configures auth (Claude Code subscription bridge)
# 4. Configures exec approval, CLI backend, workspace permissions
# 5. Registers agents in OpenClaw
# 6. Starts OpenClaw gateway
# 7. Starts Mission Control (Docker) + connects to gateway
# 8. Syncs templates (pushes TOOLS.md with auth tokens to agents)
# 9. Pushes SOUL.md + Claude Code settings to agent workspaces

FLEET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$FLEET_DIR"

echo "╔══════════════════════════════════════╗"
echo "║     OpenClaw Fleet Setup             ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Step 0: Kill existing fleet processes (clean slate for idempotent setup)
echo "=== Cleaning Existing Processes ==="
pkill -f "fleet daemon" 2>/dev/null && echo "  Killed fleet daemons" || true
pkill -f "fleet.mcp.server" 2>/dev/null && echo "  Killed MCP servers" || true
pkill -f "miniircd" 2>/dev/null && echo "  Killed IRC daemon" || true
pkill -f "python3 -m gateway start" 2>/dev/null && echo "  Killed stale AICP gateway" || true
echo "  Clean"
echo ""

# Step 0b: Pre-flight checks
echo "=== Pre-flight Checks ==="
PREFLIGHT_OK=true

# Python 3.11+
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
        echo "  Python $PY_VER: OK"
    else
        echo "  Python $PY_VER: NEED 3.11+ (some features may not work)"
    fi
else
    echo "  Python: NOT FOUND — install Python 3.11+"
    PREFLIGHT_OK=false
fi

# Docker
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "  Docker: OK"
else
    echo "  Docker: NOT AVAILABLE — install Docker and start the daemon"
    PREFLIGHT_OK=false
fi

# Docker Compose
if docker compose version >/dev/null 2>&1; then
    echo "  Docker Compose: OK"
else
    echo "  Docker Compose: NOT FOUND — install docker-compose-plugin"
    PREFLIGHT_OK=false
fi

# Claude Code
if command -v claude >/dev/null 2>&1; then
    echo "  Claude Code: OK"
else
    echo "  Claude Code: NOT FOUND — agents won't execute (install: npm install -g @anthropic-ai/claude-code)"
fi

# GitHub CLI (for PR creation)
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "  GitHub CLI: OK (authenticated)"
else
    echo "  GitHub CLI: NOT AUTHED — agents can't create PRs (run: gh auth login)"
fi

# Git
if command -v git >/dev/null 2>&1; then
    echo "  Git: OK"
else
    echo "  Git: NOT FOUND"
    PREFLIGHT_OK=false
fi

if [[ "$PREFLIGHT_OK" != "true" ]]; then
    echo ""
    echo "Pre-flight checks failed. Fix the issues above and re-run."
    exit 1
fi

# uv (Python version + venv manager)
if command -v uv >/dev/null 2>&1; then
    echo "  uv: OK"
else
    echo "  uv: NOT FOUND — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
    export PATH="$HOME/.local/bin:$PATH"
fi

# Set up Python venv with 3.11+
echo "  Setting up Python venv..."
if [[ ! -d "$FLEET_DIR/.venv" ]]; then
    uv venv --python 3.11 "$FLEET_DIR/.venv" 2>/dev/null || {
        echo "  WARN: Could not create Python 3.11 venv"
    }
fi

# Install fleet package in venv
if [[ -d "$FLEET_DIR/.venv" ]]; then
    uv pip install --python "$FLEET_DIR/.venv/bin/python" -q -e "$FLEET_DIR" 2>/dev/null || {
        echo "  WARN: Fleet package install failed"
    }
    echo "  Python venv: OK (.venv with Python 3.11+)"
fi
echo ""

# Step 0c: Generate fleet identity (unique per machine)
echo "=== Fleet Identity ==="
if [[ -f "$FLEET_DIR/.venv/bin/python" ]]; then
    "$FLEET_DIR/.venv/bin/python" -c "
from fleet.core.federation import generate_fleet_identity, load_fleet_identity
identity = generate_fleet_identity('$FLEET_DIR')
print(f'  Fleet ID:   {identity.fleet_id}')
print(f'  Fleet Name: {identity.fleet_name}')
print(f'  Machine:    {identity.machine_id}')
print(f'  Prefix:     {identity.agent_prefix}')
" 2>/dev/null || echo "  SKIP: Fleet identity (venv not ready)"
fi
echo ""

# Step 1: Install OpenClaw
bash scripts/install-openclaw.sh
echo ""

# Step 2: Configure OpenClaw (if not already set up)
if [[ ! -f "${HOME}/.openclaw/openclaw.json" ]]; then
    echo "=== Configuring OpenClaw ==="
    openclaw onboard --non-interactive --accept-risk --workspace "$FLEET_DIR" --skip-health
    echo ""
fi

# Step 3: Configure OpenClaw gateway settings
echo "=== Configuring Gateway ==="
python3 -c "
import json, os
config_path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(config_path) as f:
    cfg = json.load(f)

changed = False

# Ensure LAN bind
if cfg.get('gateway', {}).get('bind') != 'lan':
    cfg.setdefault('gateway', {})['bind'] = 'lan'
    changed = True

# Ensure control UI allows MC connections
cu = cfg.get('gateway', {}).get('controlUi', {})
if not cu.get('allowInsecureAuth') or not cu.get('dangerouslyDisableDeviceAuth'):
    cfg['gateway']['controlUi'] = {
        'allowedOrigins': ['*'],
        'allowInsecureAuth': True,
        'dangerouslyDisableDeviceAuth': True,
    }
    changed = True

# Ensure workspace is set
if cfg.get('agents', {}).get('defaults', {}).get('workspace') != '$FLEET_DIR':
    cfg.setdefault('agents', {}).setdefault('defaults', {})['workspace'] = '$FLEET_DIR'
    changed = True

if changed:
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    print('OpenClaw config updated')
else:
    print('OpenClaw config OK')
"
echo ""

# Step 4: Configure auth
bash scripts/configure-auth.sh || {
    echo ""
    echo "⚠️  Auth not configured. Fleet will start but agents won't execute."
    echo "   Fix it later with: bash scripts/configure-auth.sh"
    echo ""
}
echo ""

# Step 5: Configure exec tool, CLI backend, and workspace permissions
bash scripts/configure-openclaw.sh
echo ""

# Step 6: Register agents in OpenClaw
bash scripts/register-agents.sh
echo ""

# Step 7: Set up IRC channel for fleet observation
bash scripts/setup-irc.sh
echo ""

# Step 8: Clear fleet agents from gateway config (MC re-provisions them fresh)
echo "=== Preparing Gateway for Provisioning ==="
python3 -c "
import json, os
p = os.path.expanduser('~/.openclaw/openclaw.json')
with open(p) as f: cfg = json.load(f)
agents = cfg.get('agents', {}).get('list', [])
kept = [a for a in agents if 'Gateway' in a.get('name', '')]
print(f'  Cleared {len(agents) - len(kept)} agent entries for MC to re-provision')
cfg['agents']['list'] = kept
with open(p, 'w') as f: json.dump(cfg, f, indent=2)
" 2>/dev/null || echo "  SKIP"
echo ""

# Step 8b: Start the fleet (gateway must be up before MC connects)
bash scripts/start-fleet.sh
echo ""

# Step 9: Start Mission Control + connect gateway + sync templates + push SOUL.md
# MC provisions agents on the gateway (agents.create succeeds because they don't exist)
bash scripts/setup-mc.sh
echo ""

# Step 10: Start The Lounge (web IRC client)
bash scripts/setup-lounge.sh
echo ""

# Step 11: Clean gateway config (remove duplicates, set safe heartbeat intervals)
# MUST run after MC setup (which adds duplicate entries during provisioning)
echo "=== Cleaning Gateway Config ==="
bash scripts/clean-gateway-config.sh
echo ""

# Step 11b: Restart gateway with clean config
# The gateway loaded dirty config at Step 8. Now that we've cleaned it,
# restart so it uses the deduplicated, staggered config.
echo "=== Restarting Gateway (clean config) ==="
bash scripts/start-fleet.sh
echo ""

# Step 12: Configure agent Claude Code settings (effort, memory, permissions)
echo "=== Configuring Agent Settings ==="
bash scripts/configure-agent-settings.sh
echo ""

# Step 13: Push fleet framework to all agent workspaces
echo "=== Pushing Agent Framework ==="
bash scripts/push-agent-framework.sh
echo ""

# Step 14: Configure board custom fields and tags
echo "=== Configuring Board ==="
bash scripts/configure-board.sh
echo ""

# Step 15: Start fleet daemons (sync + monitor + orchestrator in conservative mode)
echo "=== Starting Fleet Daemons ==="
echo "NOTE: Effort profile is CONSERVATIVE. Use 'fleet effort full' when ready."
if [[ -f "$FLEET_DIR/.venv/bin/python" ]]; then
    nohup "$FLEET_DIR/.venv/bin/python" -m fleet daemon all > "$FLEET_DIR/.fleet-daemons.log" 2>&1 &
    disown
    echo "Fleet daemons started (PID: $!, log: .fleet-daemons.log)"
else
    echo "ERROR: Python venv not found. Run: uv venv --python 3.11 && uv pip install -e ."
fi
echo ""

echo "╔══════════════════════════════════════╗"
echo "║     Fleet Setup Complete             ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Everything is running:"
echo "  Mission Control UI:  http://localhost:3000"
echo "  Mission Control API: http://localhost:8000"
echo "  OpenClaw Gateway:    ws://localhost:18789"
echo "  OpenClaw Control UI: http://localhost:18789"
echo "  IRC Server:          localhost:6667"
echo "  The Lounge (IRC UI): http://localhost:9000  (fleet/fleet)"
echo ""
echo "IRC Channels: #fleet #alerts #reviews #sprint #agents #security #human #builds #memory #plane"
echo ""
echo "Safety:"
echo "  Effort profile:   conservative (max 1 dispatch/cycle, sonnet only)"
echo "  Heartbeats:       staggered 30-90m per agent"
echo "  Budget monitor:   reads CLAUDE_QUOTA_* — auto-pause at 90%"
echo "  Kill switch:      fleet pause / fleet resume"
echo ""
echo "Manage:"
echo "  make status    — fleet overview"
echo "  make watch     — real-time agent events"
echo "  make sync      — sync tasks ↔ PRs"
echo "  make mc-up     — start Mission Control"
echo "  make gateway   — start OpenClaw gateway"
echo "  make logs      — view gateway logs"