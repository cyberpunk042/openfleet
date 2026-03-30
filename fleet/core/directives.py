"""Directives — PO commands routed to agents via board memory.

The PO posts a directive to board memory with specific tags. The
orchestrator reads new directives each cycle and routes them to
the target agent or the entire fleet.

Directive format in board memory:
  content: "PM: start working on AICP Stage 1"
  tags: ["directive", "to:project-manager", "from:human"]
  source: "human"

The orchestrator reads directives tagged with "directive" that haven't
been processed yet. It creates tasks or updates heartbeat context so
the target agent sees the directive on its next heartbeat.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Directive:
    """A parsed directive from board memory."""
    id: str
    content: str
    target_agent: Optional[str]  # None = all agents
    source: str  # who posted it (usually "human")
    urgent: bool = False
    created_at: Optional[str] = None


def parse_directives(memory_entries: list) -> list[Directive]:
    """Parse directives from board memory entries.

    Looks for entries tagged with "directive" that haven't been
    processed (no "processed" tag).

    Args:
        memory_entries: Board memory entries (from mc.list_memory).

    Returns:
        List of parsed Directive objects.
    """
    directives = []

    for entry in memory_entries:
        tags = entry.tags if hasattr(entry, 'tags') else entry.get('tags', [])
        if "directive" not in tags:
            continue
        if "processed" in tags:
            continue

        # Extract target agent from tags
        target = None
        for tag in tags:
            if tag.startswith("to:"):
                target = tag[3:]
                break

        urgent = "urgent" in tags

        content = entry.content if hasattr(entry, 'content') else entry.get('content', '')
        source = entry.source if hasattr(entry, 'source') else entry.get('source', '')
        entry_id = entry.id if hasattr(entry, 'id') else entry.get('id', '')
        created_at = entry.created_at if hasattr(entry, 'created_at') else entry.get('created_at')

        directives.append(Directive(
            id=str(entry_id),
            content=content,
            target_agent=target,
            source=source,
            urgent=urgent,
            created_at=str(created_at) if created_at else None,
        ))

    return directives


def format_directive_for_agent(directive: Directive) -> str:
    """Format a directive as text for an agent's heartbeat context."""
    urgency = "🚨 URGENT " if directive.urgent else ""
    return (
        f"{urgency}DIRECTIVE from {directive.source}:\n"
        f"{directive.content}"
    )