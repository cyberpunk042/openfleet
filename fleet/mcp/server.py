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
    server = create_server()
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(run_server())