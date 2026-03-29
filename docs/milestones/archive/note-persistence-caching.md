# Note: Persistence, Caching, Indexing, Backup

## User Requirements

> "lets not forget what needs persistence too when needed. I wanna be able to have every index and/or cache I need and even backup it if I really wanted to and possibly eventually have some kind of sharing for IRC for example."

## What This Means

The fleet system needs a **persistence layer** — not just in-memory operations:

1. **Caching** — resolved URLs, project configs, agent lists, board state shouldn't
   be fetched from MC API on every call. Cache with TTL.

2. **Indexing** — ability to search across: tasks, board memory, IRC history, commits.
   Fast lookups by task ID, project, agent, tag.

3. **Backup** — all fleet state must be exportable: board memory, task history,
   IRC logs, agent sessions, configuration.

4. **Sharing** — IRC history should be shareable (The Lounge has sqlite storage).
   Board memory decisions should be exportable. Fleet state should be transferable
   to another machine.

## Where This Lives in the Architecture

```
fleet/
├── core/
│   └── cache.py          # Cache interface (abstract)
├── infra/
│   ├── cache_sqlite.py   # SQLite-backed cache implementation
│   ├── cache_memory.py   # In-memory cache for short-lived data
│   └── backup.py         # Export/import fleet state
```

Cache is an INTERFACE in core (no dependency on storage tech).
Implementation in infra (SQLite for persistence, memory for speed).

## To Address in Build Phase

- M135+ (infra clients): add caching layer to MC client
- IRC backup: already planned in fleet-lifecycle (M166)
- Board memory export: add to backup.py
- Sharing: design export format (JSON? SQLite dump?)

This requirement applies to ALL infra clients, not just one.