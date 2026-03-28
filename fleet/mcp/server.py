"""Fleet MCP Server — exposes fleet operations as native agent tools.

Agents call these tools naturally, like they call exec or read.
The server handles all infrastructure: MC API, IRC, GitHub, URL resolution.

Run: python -m fleet mcp-server
Or via .mcp.json in agent workspace (stdio transport).
"""

from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from fleet.mcp.tools import register_tools


def create_server() -> FastMCP:
    """Create and configure the Fleet MCP server."""
    server = FastMCP(
        name="fleet",
        instructions=(
            "Fleet operations tools for OpenClaw agents. "
            "Use these to interact with Mission Control, create PRs, "
            "post to IRC, and manage your task lifecycle. "
            "Call fleet_read_context first to understand your task."
        ),
    )

    register_tools(server)

    return server


def run_server() -> int:
    """Run the Fleet MCP server (stdio transport)."""
    # Debug: log startup to confirm server was spawned by OpenClaw
    debug_log = os.path.join(
        os.environ.get("FLEET_DIR", "."), ".fleet-mcp-debug.log"
    )
    try:
        with open(debug_log, "a") as f:
            from datetime import datetime
            f.write(f"[{datetime.now().isoformat()}] Fleet MCP server starting\n")
            f.write(f"  FLEET_DIR={os.environ.get('FLEET_DIR', '')}\n")
            f.write(f"  FLEET_TASK_ID={os.environ.get('FLEET_TASK_ID', '')}\n")
            f.write(f"  FLEET_AGENT={os.environ.get('FLEET_AGENT', '')}\n")
            f.write(f"  Python={sys.executable}\n")
    except Exception:
        pass

    server = create_server()

    # Log registered tools
    try:
        with open(debug_log, "a") as f:
            tools = server._tool_manager._tools
            f.write(f"  Tools registered: {len(tools)}\n")
            for name in sorted(tools.keys()):
                f.write(f"    - {name}\n")
    except Exception as e:
        try:
            with open(debug_log, "a") as f:
                f.write(f"  Tools logging error: {e}\n")
        except Exception:
            pass

    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(run_server())