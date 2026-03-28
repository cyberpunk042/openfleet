"""Fleet CLI entry point.

Usage: python -m fleet <command> [options]
"""

import sys


COMMANDS = {
    "mcp-server": ("Start the Fleet MCP server (stdio)", "fleet.mcp.server", "run_server"),
    "status": ("Fleet overview (agents, tasks, activity)", "fleet.cli.status", "run_status"),
    "trace": ("Full task trace (MC + git + worktree + PR)", "fleet.cli.trace", "run_trace"),
    "sync": ("Sync tasks ↔ PRs (merge, close, cleanup)", "fleet.cli.sync", "run_sync"),
    "notify": ("Send IRC notification", "fleet.cli.notify", "run_notify"),
    "create": ("Create task (and optionally dispatch)", "fleet.cli.create", "run_create"),
    "dispatch": ("Dispatch task to agent", "fleet.cli.dispatch", "run_dispatch"),
    "digest": ("Generate daily fleet digest", "fleet.cli.digest", "run_digest"),
    "project": ("Manage projects (add/list/check)", "fleet.cli.project", "run_project"),
    "quality": ("Run quality compliance checks", "fleet.cli.quality", "run_quality"),
    "auth": ("Check and refresh auth tokens", "fleet.cli.auth", "run_auth"),
    "board": ("Board management (info/tasks/cleanup/tags/fields)", "fleet.cli.board", "run_board"),
    "cache": ("Manage cache (stats/cleanup/export/import)", "fleet.cli.cache_cmd", "run_cache"),
    "daemon": ("Run background daemons (sync/monitor/all)", "fleet.cli.daemon", "run_daemon"),
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

    # Commands that accept args
    if command in ("notify", "digest", "dispatch", "create", "daemon", "cache", "board", "auth", "trace", "project"):
        return func(sys.argv[2:])
    else:
        return func()


if __name__ == "__main__":
    sys.exit(main())