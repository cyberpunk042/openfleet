"""OCF Gateway WebSocket server — speaks the OpenClaw gateway protocol.

Mission Control connects to gateways via WebSocket using JSON-RPC style messages.

Protocol:
1. Client connects
2. Gateway sends connect.challenge event
3. Client sends connect request
4. Gateway responds with server metadata (including version)
5. Client calls methods via JSON-RPC

Key methods for task execution:
- sessions.patch: create/update a session for an agent
- chat.send: send a message to a session → execute via Claude Code → return result
- chat.history: retrieve session history
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import yaml

AGENTS_DIR = Path(__file__).parent.parent / "agents"
CONFIG_DIR = Path(__file__).parent.parent / "config"
GATEWAY_VERSION = "2026.3.26"


def _load_projects() -> Dict[str, Dict[str, Any]]:
    """Load project registry from config/projects.yaml."""
    projects_path = CONFIG_DIR / "projects.yaml"
    if not projects_path.exists():
        return {}
    with open(projects_path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("projects", {})


class Session:
    """Tracks a chat session with an agent."""

    def __init__(self, key: str, label: str = "") -> None:
        self.key = key
        self.label = label
        self.created = datetime.utcnow().isoformat() + "Z"
        self.messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "label": self.label,
            "created": self.created,
            "messageCount": len(self.messages),
        }


class GatewayProtocol:
    """Handles the OpenClaw gateway WebSocket protocol."""

    def __init__(self) -> None:
        self.agents = self._load_agents()
        self.agent_configs: Dict[str, Dict] = {}
        self.sessions: Dict[str, Session] = {}
        self._load_agent_configs()
        self.projects = _load_projects()

    async def handle_connection(self, websocket) -> None:
        """Handle a single WebSocket connection."""
        print(f"[gateway] Connection from {websocket.remote_address}", flush=True)

        challenge = {
            "type": "event",
            "event": "connect.challenge",
            "payload": {"nonce": str(uuid4())},
        }
        await websocket.send(json.dumps(challenge))

        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                msg_id = data.get("id")
                method = data.get("method", "")
                params = data.get("params", {})

                print(f"[gateway] {method} (id={msg_id})", flush=True)

                if msg_type == "req":
                    try:
                        result = await self._handle_request(method, params)
                        response = {"type": "res", "id": msg_id, "payload": result}
                    except Exception as e:
                        response = {
                            "type": "res", "id": msg_id,
                            "ok": False, "error": {"message": str(e)},
                        }
                    await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"[gateway] Connection closed: {e}", flush=True)

    async def _handle_request(self, method: str, params: Dict[str, Any]) -> Any:
        handlers = {
            "connect": self._handle_connect,
            "health": self._handle_health,
            "status": self._handle_status,
            "agents.list": self._handle_agents_list,
            "config.get": self._handle_config_get,
            "models.list": self._handle_models_list,
            "skills.status": self._handle_skills_status,
            "sessions.patch": self._handle_sessions_patch,
            "sessions.list": self._handle_sessions_list,
            "sessions.delete": self._handle_sessions_delete,
            "chat.send": self._handle_chat_send,
            "chat.history": self._handle_chat_history,
        }

        handler = handlers.get(method)
        if handler:
            return await handler(params)

        print(f"[gateway] Unhandled: {method}", flush=True)
        return {"ok": True}

    # --- Protocol handshake ---

    async def _handle_connect(self, params: Dict) -> Dict:
        return {
            "server": {
                "version": GATEWAY_VERSION,
                "name": "OCF Gateway",
                "capabilities": ["agents", "health", "chat"],
            },
            "session": {"id": str(uuid4())},
        }

    async def _handle_health(self, params: Dict) -> Dict:
        return {"ok": True, "gateway": "ocf", "version": GATEWAY_VERSION}

    async def _handle_status(self, params: Dict) -> Dict:
        return {
            "gateway": "ocf", "version": GATEWAY_VERSION,
            "agents": len(self.agents), "sessions": len(self.sessions), "ok": True,
        }

    async def _handle_agents_list(self, params: Dict) -> Dict:
        return {"agents": self.agents}

    async def _handle_config_get(self, params: Dict) -> Dict:
        return {"config": {"meta": {"lastTouchedVersion": GATEWAY_VERSION}}}

    async def _handle_models_list(self, params: Dict) -> Dict:
        return {"models": []}

    async def _handle_skills_status(self, params: Dict) -> Dict:
        return {"skills": [], "installed": []}

    # --- Session management ---

    async def _handle_sessions_patch(self, params: Dict) -> Dict:
        key = params.get("key", str(uuid4()))
        label = params.get("label", "")

        if key not in self.sessions:
            self.sessions[key] = Session(key, label)
            print(f"[gateway] Session created: {key} ({label})", flush=True)
        elif label:
            self.sessions[key].label = label

        return self.sessions[key].to_dict()

    async def _handle_sessions_list(self, params: Dict) -> Dict:
        return {"sessions": [s.to_dict() for s in self.sessions.values()]}

    async def _handle_sessions_delete(self, params: Dict) -> Dict:
        key = params.get("key", "")
        if key in self.sessions:
            del self.sessions[key]
        return {"ok": True}

    # --- Chat execution (the core loop) ---

    async def _handle_chat_send(self, params: Dict) -> Dict:
        """Execute a chat message via Claude Code.

        This is the operational loop:
        1. Find the session and its agent
        2. Build Claude Code command with agent context
        3. Execute
        4. Store result in session history
        5. Return result
        """
        session_key = params.get("sessionKey", "")
        message = params.get("message", "")
        deliver = params.get("deliver", False)

        if not message:
            return {"ok": False, "error": "empty message"}

        session = self.sessions.get(session_key)
        if not session:
            # Auto-create session
            session = Session(session_key, "auto")
            self.sessions[session_key] = session

        # Determine which agent this session belongs to (from label)
        agent_name = session.label
        agent_config = self.agent_configs.get(agent_name, {})
        agent_dir = AGENTS_DIR / agent_name if agent_name else None

        # Resolve target project
        project_name = params.get("project", "")
        work_dir = None
        if project_name and project_name in self.projects:
            work_dir = Path(self.projects[project_name]["path"])
        else:
            for pn, pc in self.projects.items():
                if pc.get("default"):
                    work_dir = Path(pc["path"])
                    project_name = pn
                    break

        proj = f" project={project_name}" if project_name else ""
        print(f"[gateway] Executing: agent={agent_name}{proj} msg={message[:80]}...", flush=True)

        # Record user message
        session.add_message("user", message)

        # Execute via Claude Code (in executor to avoid blocking the event loop)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._execute_claude, message, agent_config, agent_dir,
            work_dir,
        )

        # Record assistant response
        response_text = result.get("text", "")
        session.add_message("assistant", response_text)

        print(f"[gateway] Result: {len(response_text)} chars", flush=True)

        return {
            "ok": True,
            "message": response_text,
            "usage": result.get("usage", {}),
        }

    async def _handle_chat_history(self, params: Dict) -> Dict:
        session_key = params.get("sessionKey", "")
        session = self.sessions.get(session_key)
        if not session:
            return {"messages": []}
        limit = params.get("limit")
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        return {"messages": messages}

    # --- Claude Code execution ---

    def _execute_claude(
        self, prompt: str, agent_config: Dict, agent_dir: Path = None,
        work_dir: Path = None,
    ) -> Dict:
        """Execute a prompt via Claude Code CLI. Runs in a thread."""
        if not shutil.which("claude"):
            return {"text": "Error: Claude Code CLI not found on PATH", "usage": {}}

        mode = agent_config.get("mode", "think")
        model = "opus"

        cmd = ["claude", "-p", "--output-format", "json", "--model", model]
        cmd.extend(["--max-turns", "15"])

        # Mode enforcement
        # Note: --permission-mode plan returns empty result in JSON for opus.
        # Instead, enforce think mode via tool restrictions + system prompt.
        if mode == "think":
            cmd.extend(["--allowedTools", "Read", "Glob", "Grep"])
            cmd.extend(["--disallowedTools", "Edit", "Write", "Bash"])
        elif mode == "edit":
            cmd.extend(["--allowedTools", "Read", "Edit", "Write", "Glob", "Grep"])
            cmd.extend(["--disallowedTools", "Bash"])

        # Agent context
        context = self._build_agent_context(agent_config, agent_dir)
        if context:
            cmd.extend(["--append-system-prompt", context])

        cmd.append(prompt)

        # Execute — work_dir (project) takes precedence over agent_dir
        if work_dir and work_dir.exists():
            cwd = str(work_dir)
        elif agent_dir and agent_dir.exists():
            cwd = str(agent_dir)
        else:
            cwd = "."
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return {"text": "Error: Claude Code timed out after 300s", "usage": {}}

        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            return {"text": f"Error: {detail}", "usage": {}}

        # Parse JSON response
        try:
            data = json.loads(result.stdout)
            return {
                "text": data.get("result", result.stdout),
                "usage": data.get("usage", {}),
                "cost_usd": data.get("cost_usd"),
                "model": data.get("model", model),
            }
        except json.JSONDecodeError:
            return {"text": result.stdout, "usage": {}}

    def _build_agent_context(self, config: Dict, agent_dir: Path = None) -> str:
        parts = []
        name = config.get("name", "")
        mission = config.get("mission", "")
        if name and mission:
            parts.append(f"You are the {name} agent. Mission: {mission}")

        if agent_dir:
            # 8-file onion injection order (fleet-elevation/02):
            # IDENTITY → SOUL → CLAUDE → TOOLS → AGENTS → context → HEARTBEAT
            for identity_file in ("IDENTITY.md", "SOUL.md"):
                path = agent_dir / identity_file
                if path.exists():
                    parts.append(path.read_text(errors="replace")[:4000])

            claude_md = agent_dir / "CLAUDE.md"
            if claude_md.exists():
                parts.append(claude_md.read_text(errors="replace")[:4000])

            for knowledge_file in ("TOOLS.md", "AGENTS.md"):
                path = agent_dir / knowledge_file
                if path.exists():
                    parts.append(path.read_text(errors="replace")[:4000])

            context_dir = agent_dir / "context"
            if context_dir.exists():
                for f in sorted(context_dir.iterdir()):
                    if f.is_file() and f.suffix in (".md", ".txt", ".yaml", ".json"):
                        parts.append(f"Context ({f.name}):\n{f.read_text(errors='replace')[:8000]}")

            heartbeat_md = agent_dir / "HEARTBEAT.md"
            if heartbeat_md.exists():
                parts.append(heartbeat_md.read_text(errors="replace")[:4000])

        return "\n\n".join(parts) if parts else ""

    # --- Agent loading ---

    def _load_agents(self) -> list:
        agents = []
        if not AGENTS_DIR.exists():
            return agents
        for d in sorted(AGENTS_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                config_path = d / "agent.yaml"
                if config_path.exists():
                    with open(config_path) as f:
                        cfg = yaml.safe_load(f) or {}
                    agents.append({
                        "name": cfg.get("name", d.name),
                        "type": cfg.get("type", "definition"),
                        "description": cfg.get("description", ""),
                        "status": "active",
                    })
        return agents

    def _load_agent_configs(self) -> None:
        if not AGENTS_DIR.exists():
            return
        for d in sorted(AGENTS_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                config_path = d / "agent.yaml"
                if config_path.exists():
                    with open(config_path) as f:
                        self.agent_configs[d.name] = yaml.safe_load(f) or {}


async def run_ws_gateway(host: str = "0.0.0.0", port: int = 9400) -> None:
    """Start the WebSocket gateway server."""
    try:
        import websockets
    except ImportError:
        print("Error: 'websockets' package required. pip install websockets")
        return

    protocol = GatewayProtocol()
    print(f"OCF Gateway (WebSocket) listening on ws://{host}:{port}", flush=True)
    print(f"Version: {GATEWAY_VERSION}", flush=True)
    print(f"Agents: {len(protocol.agents)}", flush=True)

    async with websockets.serve(protocol.handle_connection, host, port):
        await asyncio.Future()