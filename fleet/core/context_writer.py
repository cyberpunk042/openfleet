"""Context writer — writes pre-embed data to agent context files.

The gateway reads files from agents/{name}/context/ and includes them
in the agent's system prompt. This module writes pre-embed data to
those files so agents have context before making any MCP call.

Three context files:
- fleet-context.md: heartbeat pre-embed (fleet state, messages, role data)
- task-context.md: task pre-embed (task details, stage, requirement)
- knowledge-context.md: navigator output (knowledge map, graph, memory)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Agents directory — relative to fleet repo root
AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"


def write_heartbeat_context(agent_name: str, content: str) -> bool:
    """Write heartbeat pre-embed to agent's context directory.

    Creates the context/ directory if it doesn't exist.
    The gateway reads this on next heartbeat execution.

    Args:
        agent_name: The agent's directory name.
        content: Pre-embed text to write.

    Returns:
        True if written successfully.
    """
    return _write_context_file(agent_name, "fleet-context.md", content)


def write_task_context(agent_name: str, content: str) -> bool:
    """Write task pre-embed to agent's context directory.

    Created at dispatch time. The gateway reads this when the agent
    starts working on the task.

    Args:
        agent_name: The agent's directory name.
        content: Pre-embed text to write.

    Returns:
        True if written successfully.
    """
    return _write_context_file(agent_name, "task-context.md", content)


def write_knowledge_context(agent_name: str, content: str) -> bool:
    """Write navigator knowledge context to agent's context directory.

    The navigator assembles this from the knowledge map, LightRAG graph,
    and injection profiles. Contains role-specific, stage-specific,
    model-appropriate knowledge for the agent's current work.

    Args:
        agent_name: The agent's directory name.
        content: Navigator-assembled context.

    Returns:
        True if written successfully.
    """
    return _write_context_file(agent_name, "knowledge-context.md", content)


def clear_task_context(agent_name: str) -> bool:
    """Remove task context file when task is complete or agent is pruned."""
    agent_dir = AGENTS_DIR / agent_name / "context"
    path = agent_dir / "task-context.md"
    try:
        if path.exists():
            path.unlink()
            logger.debug("Cleared task context for %s", agent_name)
        return True
    except Exception as e:
        logger.error("Failed to clear task context for %s: %s", agent_name, e)
        return False


def _write_context_file(agent_name: str, filename: str, content: str) -> bool:
    """Write a context file for an agent."""
    agent_dir = AGENTS_DIR / agent_name
    if not agent_dir.exists():
        logger.warning("Agent directory not found: %s", agent_name)
        return False

    context_dir = agent_dir / "context"
    context_dir.mkdir(exist_ok=True)

    path = context_dir / filename
    try:
        path.write_text(content)
        logger.debug("Wrote %s for %s (%d chars)", filename, agent_name, len(content))
        return True
    except Exception as e:
        logger.error("Failed to write %s for %s: %s", filename, agent_name, e)
        return False