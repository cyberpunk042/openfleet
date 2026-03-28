"""Agent memory structure — persistent knowledge across sessions.

Defines the memory organization for each agent workspace:
  MEMORY.md               — Index (auto-managed by Claude Code)
  codebase_knowledge.md   — Patterns, architecture, key files learned
  project_decisions.md    — Decisions made and rationale
  task_history.md         — What I've done, lessons learned
  team_context.md         — What other agents are doing, shared knowledge

Board memory serves as the shared knowledge layer — agents post decisions
and learnings there with proper tags, and fleet_read_context surfaces
relevant entries at session start.
"""

from __future__ import annotations

import os
from pathlib import Path


# Memory file templates per agent
MEMORY_FILES = {
    "MEMORY.md": """# Agent Memory

This file is auto-managed. Your persistent knowledge is organized below.

## Recent

- Session started. Check files below for context from previous sessions.

## Files

- [codebase_knowledge.md](codebase_knowledge.md) — Patterns and architecture
- [project_decisions.md](project_decisions.md) — Decisions and rationale
- [task_history.md](task_history.md) — What I've done, lessons learned
- [team_context.md](team_context.md) — Shared knowledge from team
""",

    "codebase_knowledge.md": """---
name: Codebase Knowledge
description: Patterns, architecture, key files discovered during work
type: reference
---

# Codebase Knowledge

Record patterns, architecture insights, and key file locations here.
Focus on what helps FUTURE you — not ephemeral task details.

## Key Files

(Add files you work with frequently and their purpose)

## Patterns

(Add patterns you've discovered in the codebase)

## Architecture Notes

(Add architecture insights — how components connect)
""",

    "project_decisions.md": """---
name: Project Decisions
description: Decisions made during work and their rationale
type: project
---

# Project Decisions

Record decisions you make and WHY. Future you will thank you.

## Decisions

(Add decisions with date, context, rationale)
""",

    "task_history.md": """---
name: Task History
description: What I've done, lessons learned, mistakes to avoid
type: user
---

# Task History

Track what you've worked on and what you learned.

## Completed Work

(Add completed tasks with key learnings)

## Lessons Learned

(Add things that went wrong and how to avoid them)
""",

    "team_context.md": """---
name: Team Context
description: Knowledge shared by other agents via board memory
type: project
---

# Team Context

Knowledge from other fleet agents that affects your work.
Updated when fleet_read_context surfaces relevant board memory.

## Recent Decisions

(Decisions from board memory that affect your domain)

## Active Concerns

(Alerts and concerns from other agents)
""",
}


def initialize_agent_memory(workspace_dir: str) -> int:
    """Initialize memory directory structure in an agent workspace.

    Creates the memory files if they don't exist. Idempotent.

    Args:
        workspace_dir: Path to agent workspace (workspace-mc-{id})

    Returns:
        Number of files created.
    """
    memory_dir = os.path.join(workspace_dir, ".claude", "memory")
    os.makedirs(memory_dir, exist_ok=True)

    created = 0
    for filename, template in MEMORY_FILES.items():
        filepath = os.path.join(memory_dir, filename)
        if not os.path.isfile(filepath):
            with open(filepath, "w") as f:
                f.write(template)
            created += 1

    return created


def initialize_all_agent_memories(fleet_dir: str) -> dict[str, int]:
    """Initialize memory for all agent workspaces.

    Returns:
        Dict of agent_name → files_created.
    """
    import json

    results: dict[str, int] = {}

    for entry in os.listdir(fleet_dir):
        if not entry.startswith("workspace-mc-"):
            continue

        workspace = os.path.join(fleet_dir, entry)
        mcp_path = os.path.join(workspace, ".mcp.json")

        if not os.path.isfile(mcp_path):
            continue

        try:
            with open(mcp_path) as f:
                cfg = json.load(f)
            agent_name = cfg["mcpServers"]["fleet"]["env"]["FLEET_AGENT"]
        except Exception:
            continue

        created = initialize_agent_memory(workspace)
        results[agent_name] = created

    return results