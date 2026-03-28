"""Fleet CLI entry point.

Usage: python -m fleet <command> [options]
"""

import sys


def main() -> int:
    """Fleet CLI dispatcher."""
    if len(sys.argv) < 2:
        print("Usage: python -m fleet <command>")
        print()
        print("Commands:")
        print("  mcp-server    Start the Fleet MCP server (stdio)")
        print("  dispatch      Dispatch a task to an agent")
        print("  sync          Sync tasks ↔ PRs")
        print("  monitor       Check board state and post alerts")
        print("  digest        Generate daily digest")
        print("  quality       Run quality checks")
        print("  status        Fleet overview")
        return 1

    command = sys.argv[1]

    if command == "mcp-server":
        from fleet.mcp.server import run_server
        return run_server()
    elif command == "status":
        from fleet.cli.status import run_status
        return run_status()
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())