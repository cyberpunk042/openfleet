"""Task executor — runs agent work through Claude Code CLI or LocalAI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def execute_task(
    agent_dir: Path,
    task: Dict[str, Any],
    claude_model: str = "opus",
    timeout: int = 300,
) -> Dict[str, Any]:
    """Execute a task for an agent via Claude Code CLI.

    Args:
        agent_dir: Path to the agent's directory (contains agent.yaml, CLAUDE.md, context/)
        task: Task definition with 'prompt', 'mode', optional 'effort'
        claude_model: Claude model to use
        timeout: Max seconds for execution

    Returns: dict with 'result', 'usage', 'error'
    """
    if not shutil.which("claude"):
        return {"result": None, "error": "Claude Code CLI not found", "usage": {}}

    agent_config = _load_agent_config(agent_dir)
    prompt = task.get("prompt", "")
    mode = task.get("mode", agent_config.get("mode", "think"))
    effort = task.get("effort", "high")

    # Build command
    cmd = ["claude", "-p", "--output-format", "json", "--model", claude_model]
    cmd.extend(["--effort", effort])

    # Mode enforcement
    if mode == "think":
        cmd.extend(["--permission-mode", "plan"])
    elif mode == "edit":
        cmd.extend(["--allowedTools", "Read", "Edit", "Write", "Glob", "Grep"])
        cmd.extend(["--disallowedTools", "Bash"])

    max_turns = task.get("max_turns", 10)
    cmd.extend(["--max-turns", str(max_turns)])

    # Agent context via system prompt
    context = _build_agent_context(agent_dir, agent_config)
    if context:
        cmd.extend(["--append-system-prompt", context])

    cmd.append(prompt)

    # Execute
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(agent_dir),
        )
    except subprocess.TimeoutExpired:
        return {"result": None, "error": f"Timed out after {timeout}s", "usage": {}}

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        return {"result": None, "error": detail, "usage": {}}

    # Parse JSON response
    try:
        data = json.loads(result.stdout)
        return {
            "result": data.get("result", result.stdout),
            "usage": data.get("usage", {}),
            "cost_usd": data.get("cost_usd", 0),
            "model": data.get("model", claude_model),
            "error": None,
        }
    except json.JSONDecodeError:
        return {"result": result.stdout, "usage": {}, "error": None}


def _load_agent_config(agent_dir: Path) -> Dict[str, Any]:
    config_path = agent_dir / "agent.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _build_agent_context(agent_dir: Path, config: Dict[str, Any]) -> str:
    """Build context string from agent's CLAUDE.md and context/ files."""
    parts = []

    # Agent identity
    name = config.get("name", agent_dir.name)
    mission = config.get("mission", "")
    if mission:
        parts.append(f"You are the {name} agent. Mission: {mission}")

    # CLAUDE.md
    claude_md = agent_dir / "CLAUDE.md"
    if claude_md.exists():
        parts.append(claude_md.read_text(errors="replace")[:4000])

    # Context files — FULL data, not compressed.
    # Each file can be up to 8000 chars. No limit on number of files.
    # The pre-embedded data is the agent's FULL working context.
    context_dir = agent_dir / "context"
    if context_dir.exists():
        for f in sorted(context_dir.iterdir()):
            if f.is_file() and f.suffix in (".md", ".txt", ".yaml", ".json"):
                content = f.read_text(errors="replace")[:8000]
                parts.append(f"Context ({f.name}):\n{content}")

    return "\n\n".join(parts) if parts else ""