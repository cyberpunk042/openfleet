# Design: Fleet Python Library — Clean Architecture

## User Requirements

> "We have to build clean patterns. make clean design pattern usage, libs when relevant and infrastructure pieces when relevant and know when its appropriate and so on."

> "We have to build with strong OOP and SRP and remember code hygiene like rule of never more than ~500 in general. (>~700 for exceptions, and stuff like this, like consistent naming and commenting and code headers and code docs and global docs too.)"

> "We need to think onion and domain. we need to remember how to split things by folder and use prefix or even suffix when appropriate."

## Current State

25+ bash scripts with inline Python heredocs. No structure. No reuse. No testing.
Every script re-implements URL resolution, API calls, JSON construction.
The `gateway/` directory has Python modules but they're from an earlier design
and don't follow the architecture the fleet now needs.

## Target State

A proper Python package: `fleet/`

### Onion Architecture

```
┌───────────────────────────────────────────────────┐
│                    CLI / Scripts                    │  ← Presentation
│              (entry points, Makefile)               │
├───────────────────────────────────────────────────┤
│                   MCP Server                       │  ← Application
│          (tool handlers, pipeline)                  │
├────────────────────────────────────��──────────────┤
│                   Core Domain                      │  ← Domain
│      (task lifecycle, quality rules, routing)       │
├───────────────────────────────────────────────────┤
│                 Infrastructure                     │  ← Infrastructure
│        (MC client, IRC, GitHub, config)             │
└───────────────────────────────────────────────────┘
```

**Dependency rule:** Inner layers never depend on outer layers.
Core doesn't know about MC API. Core defines interfaces. Infra implements them.

### Package Structure

```
fleet/
├── __init__.py                 # Package version, public API
├── __main__.py                 # CLI entry: python -m fleet
│
├── core/                       # Domain logic — no external dependencies
│   ├── __init__.py
│   ├── task_lifecycle.py       # Task states, transitions, rules (<300 lines)
│   ├── quality_rules.py        # Quality validation rules (<300 lines)
│   ├── url_resolver.py         # URL resolution from config (<200 lines)
│   ├── routing.py              # Message routing by type/severity (<200 lines)
│   ├── models.py               # Domain models: Task, Project, Agent (<300 lines)
│   └── interfaces.py           # Abstract interfaces for infra (<100 lines)
│
├── infra/                      # External system adapters
│   ├── __init__.py
│   ├── mc_client.py            # Mission Control REST API (<400 lines)
│   ├── irc_client.py           # IRC via OpenClaw gateway RPC (<200 lines)
│   ├── gh_client.py            # GitHub CLI wrapper (<200 lines)
│   ├── gateway_client.py       # OpenClaw gateway WebSocket (<300 lines)
│   └── config_loader.py        # Load YAML configs, TOOLS.md (<200 lines)
│
├── templates/                  # Formatters — take data, produce markdown
│   ├── __init__.py
│   ├── pr_body.py              # PR body from branch diff (<300 lines)
│   ├── task_comment.py         # Acceptance, progress, completion, blocker (<300 lines)
│   ├── board_memory.py         # Alert, decision, suggestion (<200 lines)
│   ├── irc_message.py          # Event messages with emoji + URLs (<200 lines)
│   └── digest.py               # Daily/weekly digest (<300 lines)
│
├── mcp/                        # MCP server
│   ├── __init__.py
│   ├── server.py               # MCP server entry point (<200 lines)
│   ├── tools.py                # Tool definitions and handlers (<400 lines)
│   └── context.py              # Pre-task context loading (<200 lines)
│
├── cli/                        # CLI commands (replaces bash scripts)
│   ├── __init__.py
│   ├── dispatch.py             # Task dispatch (<200 lines)
│   ├── sync.py                 # Task↔PR sync (<300 lines)
│   ├── monitor.py              # Board state monitor (<300 lines)
│   ├── digest.py               # Daily digest (<200 lines)
│   ├── quality.py              # Quality check (<200 lines)
│   ├── status.py               # Fleet status (<200 lines)
│   └── irc.py                  # IRC notify (<100 lines)
│
└── tests/                      # Tests mirror source structure
    ├── core/
    │   ├── test_task_lifecycle.py
    │   ├── test_quality_rules.py
    │   └── test_url_resolver.py
    ├── infra/
    │   ├── test_mc_client.py
    │   └── test_config_loader.py
    ├── templates/
    │   ├── test_pr_body.py
    │   └── test_task_comment.py
    └── mcp/
        └── test_tools.py
```

### Code Hygiene Rules

> "never more than ~500 in general. (>~700 for exceptions)"

| Rule | Standard |
|------|----------|
| Max lines per file | 500 (hard), 700 (exception with justification) |
| Max function length | 50 lines |
| Max class methods | 10 |
| Naming | snake_case for files/functions, PascalCase for classes |
| Prefixes | `fleet_` for public API, `_` for private |
| Docstrings | Required on all public functions and classes |
| Type hints | Required on all function signatures |
| Code header | Each file starts with module docstring: purpose, author |
| Comments | Why, not what. Only for non-obvious logic |
| Imports | stdlib → third-party → fleet (sorted within each group) |

### Key Interfaces (core/interfaces.py)

```python
"""Fleet core interfaces — implemented by infra layer."""

from abc import ABC, abstractmethod
from typing import Optional
from fleet.core.models import Task, Project, Approval

class TaskClient(ABC):
    """Interface for task operations (implemented by MC client)."""

    @abstractmethod
    async def get_task(self, board_id: str, task_id: str) -> Task: ...

    @abstractmethod
    async def update_task(self, board_id: str, task_id: str,
                          status: str | None = None,
                          comment: str | None = None,
                          custom_fields: dict | None = None) -> Task: ...

    @abstractmethod
    async def create_approval(self, board_id: str, task_id: str,
                              confidence: float, rubric: dict,
                              reason: str) -> Approval: ...

class NotificationClient(ABC):
    """Interface for notifications (implemented by IRC + board memory)."""

    @abstractmethod
    async def notify(self, channel: str, message: str) -> bool: ...

    @abstractmethod
    async def post_memory(self, board_id: str, content: str,
                          tags: list[str], source: str) -> bool: ...

class GitClient(ABC):
    """Interface for git operations."""

    @abstractmethod
    async def push(self, worktree: str, branch: str) -> bool: ...

    @abstractmethod
    async def create_pr(self, repo: str, branch: str,
                        title: str, body: str) -> str: ...  # Returns PR URL
```

### Migration Path

We don't rewrite everything at once. Gradual migration:

1. **Phase 1:** Build `fleet/core/` and `fleet/infra/` — the foundation
2. **Phase 2:** Build `fleet/mcp/` — MCP server using core + infra
3. **Phase 3:** Build `fleet/templates/` — formatters using core models
4. **Phase 4:** Build `fleet/cli/` — one command at a time, replacing bash scripts
5. **Phase 5:** Deprecate bash scripts, everything through `python -m fleet`

Each bash script stays working until its Python replacement is tested.

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M131 | fleet/ package scaffold | __init__, __main__, pyproject.toml |
| M132 | fleet/core/ — models + interfaces | Domain models, abstract interfaces |
| M133 | fleet/core/ — task lifecycle + quality rules | Business logic |
| M134 | fleet/core/ — URL resolver | URL resolution from config |
| M135 | fleet/infra/ — MC client | Mission Control API wrapper |
| M136 | fleet/infra/ — IRC + GH + config | Other infrastructure |
| M137 | fleet/templates/ — all formatters | PR, comment, memory, IRC |
| M138 | fleet/mcp/ — server + tools | MCP server with all fleet tools |
| M139 | fleet/cli/ — dispatch + sync | Replace dispatch-task.sh, fleet-sync.sh |
| M140 | fleet/cli/ — monitor + digest + quality | Replace remaining scripts |
| M141 | fleet/tests/ — core + infra tests | Unit tests for domain and adapters |
| M142 | Bash script deprecation | Remove replaced scripts, update Makefile |

## Open Questions

1. **Async or sync?** MCP server needs async. CLI could be sync.
   Recommendation: async throughout (httpx async, asyncio).

2. **Config management:** Single config object loaded once? Or per-operation loading?
   Single loaded at startup, passed through dependency injection.

3. **Testing strategy:** Mock infra layer for core tests. Integration tests hit real MC.
   Test each template produces exact expected output.

4. **Package distribution:** Install as `pip install -e .` in setup.sh?
   Or just add to PYTHONPATH? pip install is cleaner.