#!/usr/bin/env bash
set -euo pipefail

# Configure OpenClaw for headless fleet operation.
# Sets exec approval, CLI backend, and agent workspace permissions.
echo "=== Configuring OpenClaw Fleet Settings ==="

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/scripts/lib/vendor.sh"
OPENCLAW_CONFIG="$VENDOR_CONFIG_FILE"
EXEC_APPROVALS="${VENDOR_CONFIG_DIR}/exec-approvals.json"

if [[ ! -f "$OPENCLAW_CONFIG" ]]; then
    echo "ERROR: $OPENCLAW_CONFIG not found. Run '$VENDOR_CLI onboard' first."
    exit 1
fi

# 1. Patch openclaw.json: exec approval (ask=off), cliBackends
echo "1. Configuring exec tool and CLI backend..."
python3 -c "
import json, os

config_path = os.path.expanduser('$OPENCLAW_CONFIG')
with open(config_path) as f:
    cfg = json.load(f)

changed = False

# Exec tool: ask=off for headless operation, security=full
tools = cfg.setdefault('tools', {})
exec_cfg = tools.setdefault('exec', {})
if exec_cfg.get('ask') != 'off' or exec_cfg.get('security') != 'full':
    exec_cfg['host'] = exec_cfg.get('host', 'gateway')
    exec_cfg['security'] = 'full'
    exec_cfg['ask'] = 'off'
    changed = True

# CLI backend: Claude Code with bypassPermissions
agents = cfg.setdefault('agents', {})
defaults = agents.setdefault('defaults', {})
backends = defaults.setdefault('cliBackends', {})
claude_cli = backends.get('anthropic/claude-cli', {})
if claude_cli.get('command') != 'claude' or '--permission-mode' not in (claude_cli.get('args') or []):
    backends['anthropic/claude-cli'] = {
        'command': 'claude',
        'args': ['--permission-mode', 'bypassPermissions'],
    }
    changed = True

# MCP server: register fleet MCP server for all agents
mcp = cfg.setdefault('mcp', {})
servers = mcp.setdefault('servers', {})
fleet_venv = '$FLEET_DIR/.venv/bin/python'
if servers.get('fleet', {}).get('command') != fleet_venv:
    import os
    servers['fleet'] = {
        'command': fleet_venv if os.path.exists(fleet_venv) else 'python3',
        'args': ['-m', 'fleet.mcp.server'],
        'env': {
            'FLEET_DIR': '$FLEET_DIR',
            'PYTHONUNBUFFERED': '1',
        },
    }
    changed = True

if changed:
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)
    print('   Config updated: tools.exec.ask=off, cliBackends, MCP server')
else:
    print('   Config already set')
"

# 2. Set exec approvals allowlist (** wildcard for all agents)
echo "2. Configuring exec approvals allowlist..."
if [[ -n "$VENDOR_CLI" ]]; then
    # Check if ** is already in the allowlist
    if $VENDOR_CLI approvals get 2>/dev/null | grep -q '\*\*'; then
        echo "   Allowlist already has ** wildcard"
    else
        $VENDOR_CLI approvals allowlist add --agent "*" "**" >/dev/null 2>&1 || true
        echo "   Added ** wildcard to exec allowlist"
    fi
else
    echo "   WARN: $VENDOR_NAME CLI not found, skipping allowlist"
fi

# 3. Create Claude Code permissions in agent workspaces
echo "3. Configuring agent workspace permissions..."
SETTINGS='{"permissions":{"allow":["Bash(*)","Read(*)","Write(*)","Edit(*)","Glob(*)","Grep(*)"],"deny":[]}}'
configured=0
for workspace in "$FLEET_DIR"/workspace-mc-*; do
    [[ -d "$workspace" ]] || continue
    mkdir -p "$workspace/.claude"
    if [[ ! -f "$workspace/.claude/settings.json" ]] || ! grep -q "Bash" "$workspace/.claude/settings.json" 2>/dev/null; then
        echo "$SETTINGS" > "$workspace/.claude/settings.json"
        configured=$((configured + 1))
    fi
done
# Also prepare the template for future workspaces
mkdir -p "$FLEET_DIR/agents/_template/.claude"
echo "$SETTINGS" > "$FLEET_DIR/agents/_template/.claude/settings.json"
echo "   Configured $configured workspaces (+ template)"

echo "$VENDOR_NAME fleet settings configured"