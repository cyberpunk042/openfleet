"""Task executor — runs agent work through Claude Code CLI or LocalAI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _build_clean_env() -> Dict[str, str]:
    """Build a clean environment for Claude Code execution.

    Disables telemetry and strips identifying environment variables
    so agent sessions are indistinguishable from direct CLI usage.
    """
    import os
    env = os.environ.copy()

    # Disable Claude Code telemetry
    env["DISABLE_TELEMETRY"] = "1"
    env["CLAUDE_CODE_ENABLE_TELEMETRY"] = "0"

    # Strip identifying variables
    for var in (
        "CLAUDE_CODE_ENTRYPOINT",
        "CLAUDE_AGENT_SDK_VERSION",
        "CLAUDE_AGENT_SDK_CLIENT_APP",
        "CLAUDE_CODE_CONTAINER_ID",
        "CLAUDE_CODE_REMOTE_SESSION_ID",
        "CLAUDE_CODE_REMOTE",
        "CLAUDECODE",
        "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING",
    ):
        env.pop(var, None)

    return env


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
            env=_build_clean_env(),
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


def execute_via_openai_compat(
    prompt: str,
    model: str,
    base_url: str,
    api_key: str = "",
    timeout: int = 120,
) -> Dict[str, Any]:
    """Execute via OpenAI-compatible API (LocalAI, OpenRouter).

    Args:
        prompt: The task prompt
        model: Model ID (e.g., "hermes-3b", "qwen/qwen3-235b-a22b")
        base_url: API base URL (e.g., "http://localhost:8090/v1")
        api_key: API key (empty for LocalAI)
        timeout: Max seconds

    Returns: dict with 'result', 'usage', 'error'
    """
    import httpx as _httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        r = _httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return {"result": None, "error": f"API returned {r.status_code}: {r.text[:200]}", "usage": {}}

        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return {
            "result": content,
            "usage": usage,
            "cost_usd": 0,
            "model": model,
            "error": None,
        }
    except Exception as e:
        return {"result": None, "error": str(e), "usage": {}}


def _load_agent_config(agent_dir: Path) -> Dict[str, Any]:
    config_path = agent_dir / "agent.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _build_agent_context(agent_dir: Path, config: Dict[str, Any]) -> str:
    """Build context from agent files in 8-file onion injection order.

    Order (fleet-elevation/02):
    IDENTITY → SOUL → CLAUDE → TOOLS → AGENTS → context/ → HEARTBEAT

    Limits match the real gateway (OpenArms/OpenClaw):
      - Per file: 20,000 chars (src/config/schema.help.ts)
      - Total: 150,000 chars across all bootstrap files
      - Context files: 20,000 chars each, no limit on count
    """
    import os
    MAX_PER_FILE = int(os.environ.get("FLEET_BOOTSTRAP_MAX_PER_FILE", "20000"))
    MAX_TOTAL = int(os.environ.get("FLEET_BOOTSTRAP_MAX_TOTAL", "150000"))
    WARN_PER_FILE = int(os.environ.get("FLEET_BOOTSTRAP_WARN_PER_FILE", "8000"))
    WARN_TOTAL = int(os.environ.get("FLEET_BOOTSTRAP_WARN_TOTAL", "60000"))
    parts = []

    # Agent identity from config (fallback if IDENTITY.md not present)
    name = config.get("name", agent_dir.name)
    mission = config.get("mission", "")
    if mission:
        parts.append(f"You are the {name} agent. Mission: {mission}")

    import logging
    _log = logging.getLogger("gateway.executor")

    def _read_bootstrap(path: Path, label: str) -> str:
        content = path.read_text(errors="replace")
        if len(content) > WARN_PER_FILE:
            _log.warning(
                "Agent %s %s is %d chars (warn: %d, cap: %d). "
                "Bloated files degrade focus — use skills/context for per-case detail.",
                agent_dir.name, label, len(content), WARN_PER_FILE, MAX_PER_FILE,
            )
        return content[:MAX_PER_FILE]

    # Layer 1-2: Identity and values (grounding + boundaries)
    for identity_file in ("IDENTITY.md", "SOUL.md"):
        path = agent_dir / identity_file
        if path.exists():
            parts.append(_read_bootstrap(path, identity_file))

    # Layer 3: Role-specific rules
    claude_md = agent_dir / "CLAUDE.md"
    if claude_md.exists():
        parts.append(_read_bootstrap(claude_md, "CLAUDE.md"))

    # Layer 4-5: Capabilities and team knowledge
    for knowledge_file in ("TOOLS.md", "AGENTS.md"):
        path = agent_dir / knowledge_file
        if path.exists():
            parts.append(_read_bootstrap(path, knowledge_file))

    # Layer 6-7: Dynamic context — FULL data, not compressed.
    context_dir = agent_dir / "context"
    if context_dir.exists():
        for f in sorted(context_dir.iterdir()):
            if f.is_file() and f.suffix in (".md", ".txt", ".yaml", ".json"):
                content = f.read_text(errors="replace")[:MAX_PER_FILE]
                parts.append(f"Context ({f.name}):\n{content}")

    # Layer 8: Action protocol (last — drives immediate behavior)
    heartbeat_md = agent_dir / "HEARTBEAT.md"
    if heartbeat_md.exists():
        parts.append(_read_bootstrap(heartbeat_md, "HEARTBEAT.md"))

    # Enforce total limit with warnings
    result = "\n\n".join(parts) if parts else ""
    import logging
    _log = logging.getLogger("gateway.executor")
    if len(result) > WARN_TOTAL:
        _log.warning(
            "Agent %s bootstrap total %d chars exceeds warning threshold %d. "
            "Consider reducing file sizes — focused agents perform better than bloated ones.",
            agent_dir.name, len(result), WARN_TOTAL,
        )
    return result[:MAX_TOTAL]