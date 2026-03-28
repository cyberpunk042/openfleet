"""Fleet CLI entry point.

Usage: python -m fleet <command> [options]
"""

import sys


COMMANDS = {
    "mcp-server": ("Start the Fleet MCP server (stdio)", "fleet.mcp.server", "run_server"),
    "status": ("Fleet overview (agents, tasks, activity)", "fleet.cli.status", "run_status"),
    "sync": ("Sync tasks ↔ PRs (merge, close, cleanup)", "fleet.cli.sync", "run_sync"),
    "notify": ("Send IRC notification", "fleet.cli.notify", "run_notify"),
}


def main() -> int:
    """Fleet CLI dispatcher."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m fleet <command> [options]")
        print()
        print("Commands:")
        for name, (desc, _, _) in sorted(COMMANDS.items()):
            print(f"  {name:16s} {desc}")
        return 0 if sys.argv[1:] == ["--help"] else 1

    command = sys.argv[1]

    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(sorted(COMMANDS))}")
        return 1

    _, module_path, func_name = COMMANDS[command]
    module = __import__(module_path, fromlist=[func_name])
    func = getattr(module, func_name)

    if command == "notify":
        return func(sys.argv[2:])
    else:
        return func()


if __name__ == "__main__":
    sys.exit(main())