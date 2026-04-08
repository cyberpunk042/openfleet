#!/usr/bin/env bash
# generate-tools-md.sh — Generate complete TOOLS.md per agent (all 7 layers)
#
# Usage: bash scripts/generate-tools-md.sh [agent-name]
#
# Reads:
#   fleet/mcp/tools.py             (generic tool names + docstrings)
#   fleet/mcp/roles/*.py           (role-specific group calls)
#   config/tool-chains.yaml        (chain docs for generic tools)
#   config/agent-tooling.yaml      (MCP servers, plugins, skills, sub-agents)
#   config/skill-stage-mapping.yaml (stage-aware recommendations)
#   config/agent-crons.yaml        (scheduled CRON jobs)
#   config/standing-orders.yaml    (autonomous authority)
#   config/agent-hooks.yaml        (structural enforcement)
#   config/agent-identities.yaml   (display names)
#   .claude/agents/*.md            (sub-agent descriptions)
#
# Produces: agents/{name}/TOOLS.md (complete, 7-layer tool reference)
#
# Previous version used yq (Go) for YAML. Rewritten in Python for
# consistency and to handle multi-config merging across all 7 layers.

set -euo pipefail

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"

exec "$FLEET_DIR/.venv/bin/python" "$FLEET_DIR/scripts/generate-tools-md.py" "$@"
