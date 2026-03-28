"""Fleet cache management — stats, cleanup, export, import.

Usage:
  python -m fleet cache stats
  python -m fleet cache cleanup
  python -m fleet cache export <path>
  python -m fleet cache import <path>
"""

from __future__ import annotations

import sys

from fleet.infra.cache_sqlite import SQLiteCache


def run_cache(args: list[str] | None = None) -> int:
    """Entry point for fleet cache."""
    argv = args if args is not None else sys.argv[2:]

    if not argv:
        print("Usage: fleet cache <stats|cleanup|export|import> [path]")
        return 1

    action = argv[0]
    cache = SQLiteCache()

    if action == "stats":
        stats = cache.stats()
        print(f"Cache: {stats['db_path']}")
        print(f"  Entries:  {stats['active_entries']} active, {stats['expired_entries']} expired")
        print(f"  Total:    {stats['total_entries']}")
        print(f"  Size:     {stats['db_size_bytes'] / 1024:.1f} KB")

    elif action == "cleanup":
        removed = cache.cleanup_expired()
        print(f"Removed {removed} expired entries")

    elif action == "export":
        if len(argv) < 2:
            print("Usage: fleet cache export <output.json>")
            return 1
        count = cache.export_json(argv[1])
        print(f"Exported {count} entries to {argv[1]}")

    elif action == "import":
        if len(argv) < 2:
            print("Usage: fleet cache import <input.json>")
            return 1
        count = cache.import_json(argv[1])
        print(f"Imported {count} entries from {argv[1]}")

    else:
        print(f"Unknown action: {action}")
        return 1

    cache.close()
    return 0