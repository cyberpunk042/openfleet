#!/usr/bin/env bash
set -euo pipefail

# Reprovision all fleet agents:
# 1. Push framework files (CLAUDE.md, MC_WORKFLOW.md, STANDARDS.md, HEARTBEAT.md)
# 2. Update .claude/settings.json (effort, memory, permissions)
# 3. Kill MCP server processes (gateway will restart them with new tools)
# 4. Verify MCP servers restart with updated tool count
#
# Run this after ANY change to:
# - fleet/mcp/tools.py (new/modified tools)
# - agents/*/CLAUDE.md or HEARTBEAT.md (agent instructions)
# - agents/_template/* (shared framework)
# - .claude/skills/* (new skills)
# - .claude/agents/* (sub-agents)
# - config/agent-hooks.yaml (hook configurations)
# - config/agent-tooling.yaml (sub-agent assignments)
# - scripts/configure-agent-settings.sh (settings changes)

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Reprovisioning Fleet Agents ==="
echo ""

# Step 1: Push framework files (STANDARDS.md, MC_WORKFLOW.md, CLAUDE.md, HEARTBEAT.md)
echo "Step 1: Pushing framework files..."
bash "$FLEET_DIR/scripts/push-agent-framework.sh"
echo ""

# Step 1b: Push SOUL.md, mcp.json, skills, sub-agents
echo "Step 1b: Pushing SOUL + skills + sub-agents..."
bash "$FLEET_DIR/scripts/push-soul.sh"
echo ""

# Step 2: Update Claude Code settings (effort, permissions, hooks from agent-hooks.yaml)
echo "Step 2: Updating agent settings..."
bash "$FLEET_DIR/scripts/configure-agent-settings.sh"
echo ""

# Step 3: Kill MCP server processes (gateway auto-restarts them)
echo "Step 3: Restarting MCP server processes..."
MCP_PIDS=$(pgrep -f "fleet.mcp.server" 2>/dev/null || true)
if [[ -n "$MCP_PIDS" ]]; then
  KILL_COUNT=0
  for pid in $MCP_PIDS; do
    kill "$pid" 2>/dev/null && KILL_COUNT=$((KILL_COUNT + 1))
  done
  echo "  Killed $KILL_COUNT MCP server process(es)"
  sleep 3
else
  echo "  No MCP server processes found"
fi

# Step 4: Verify MCP servers restart
echo ""
echo "Step 4: Verifying MCP server restart..."
sleep 5
NEW_PIDS=$(pgrep -f "fleet.mcp.server" 2>/dev/null || true)
if [[ -n "$NEW_PIDS" ]]; then
  NEW_COUNT=$(echo "$NEW_PIDS" | wc -l)
  echo "  $NEW_COUNT MCP server process(es) running"
else
  echo "  WARNING: No MCP server processes detected"
  echo "  Gateway may need to restart: make gateway-restart"
fi

# Step 5: Check tool count in debug log
echo ""
echo "Step 5: Checking tool registration..."
sleep 3
if [[ -f "$FLEET_DIR/.fleet-mcp-debug.log" ]]; then
  LATEST=$(tail -20 "$FLEET_DIR/.fleet-mcp-debug.log" | grep "Tools registered" | tail -1)
  if [[ -n "$LATEST" ]]; then
    echo "  $LATEST"
  else
    echo "  Waiting for MCP server to log tools..."
  fi
fi

echo ""
echo "Done. Agents will pick up new tools on their next session."
echo "Current tools in tools.py:"
grep -c "async def fleet_" "$FLEET_DIR/fleet/mcp/tools.py" 2>/dev/null | xargs -I{} echo "  {} MCP tools defined"