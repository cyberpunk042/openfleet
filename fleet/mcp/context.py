"""Fleet MCP context — shared state for tool handlers.

Loads configuration, credentials, and creates infra clients.
Initialized once per MCP server instance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.models import Project
from fleet.core.urls import UrlResolver
from fleet.infra.config_loader import ConfigLoader, resolve_vendor_config
from fleet.infra.gh_client import GHClient
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient
from fleet.infra.plane_client import PlaneClient


@dataclass
class FleetMCPContext:
    """Shared context for all fleet MCP tool handlers."""

    fleet_dir: str = ""
    task_id: str = ""
    project_name: str = ""
    agent_name: str = ""
    board_id: str = ""
    worktree: str = ""
    _fleet_id: str = ""
    _fleet_prefix: str = ""

    @property
    def namespaced_agent(self) -> str:
        """Agent name with fleet prefix for cross-fleet ops (Plane, etc.)."""
        if self._fleet_prefix and self.agent_name:
            return f"{self._fleet_prefix}-{self.agent_name}"
        return self.agent_name or ""

    @property
    def fleet_id(self) -> str:
        """Unique fleet instance ID."""
        return self._fleet_id

    # Clients (lazy-initialized)
    _mc: Optional[MCClient] = field(default=None, repr=False)
    _irc: Optional[IRCClient] = field(default=None, repr=False)
    _gh: Optional[GHClient] = field(default=None, repr=False)
    _plane: Optional[PlaneClient] = field(default=None, repr=False)
    _urls: Optional[UrlResolver] = field(default=None, repr=False)
    _config: Optional[ConfigLoader] = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> FleetMCPContext:
        """Create context from environment variables.

        Env vars set by dispatch-task.sh or .mcp.json:
          FLEET_DIR, FLEET_TASK_ID, FLEET_PROJECT, FLEET_AGENT
        Credentials from TOOLS.md or .env.
        """
        fleet_dir = os.environ.get("FLEET_DIR", ".")
        agent_name = os.environ.get("FLEET_AGENT", "")

        # Load fleet identity for namespaced operations (Plane, cross-fleet)
        fleet_id = ""
        fleet_prefix = ""
        try:
            from fleet.core.federation import load_fleet_identity
            identity = load_fleet_identity(fleet_dir)
            if identity:
                fleet_id = identity.fleet_id
                fleet_prefix = identity.agent_prefix
        except Exception:
            pass

        ctx = cls(
            fleet_dir=fleet_dir,
            task_id=os.environ.get("FLEET_TASK_ID", ""),
            project_name=os.environ.get("FLEET_PROJECT", ""),
            agent_name=agent_name,
        )
        ctx._fleet_id = fleet_id
        ctx._fleet_prefix = fleet_prefix
        return ctx

    @property
    def config(self) -> ConfigLoader:
        if self._config is None:
            self._config = ConfigLoader(self.fleet_dir)
        return self._config

    @property
    def mc(self) -> MCClient:
        if self._mc is None:
            env = self.config.load_env()
            # Try agent token first (from TOOLS.md), then admin token
            agent_workspace = os.environ.get("FLEET_WORKSPACE", "")
            if agent_workspace:
                tools = self.config.load_tools_md(agent_workspace)
                token = tools.get("AUTH_TOKEN", "")
                base_url = tools.get("BASE_URL", "http://localhost:8000")
                self.board_id = tools.get("BOARD_ID", "")
            else:
                token = env.get("LOCAL_AUTH_TOKEN", "")
                base_url = env.get("OCF_MISSION_CONTROL_URL", "http://localhost:8000")
            # Use SQLite cache for API response caching
            from fleet.infra.cache_sqlite import SQLiteCache
            cache = SQLiteCache()
            self._mc = MCClient(base_url=base_url, token=token, cache=cache)
        return self._mc

    @property
    def irc(self) -> IRCClient:
        if self._irc is None:
            url_templates = self.config.load_url_templates()
            # Read gateway token from openclaw.json
            import json
            oc_config_path = resolve_vendor_config()
            gateway_token = ""
            if os.path.exists(oc_config_path):
                with open(oc_config_path) as f:
                    oc_cfg = json.load(f)
                gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")
            self._irc = IRCClient(gateway_token=gateway_token)
        return self._irc

    @property
    def gh(self) -> GHClient:
        if self._gh is None:
            self._gh = GHClient()
        return self._gh

    @property
    def plane(self) -> Optional[PlaneClient]:
        """Plane client — returns None if Plane not configured (optional surface)."""
        if self._plane is None:
            env = self.config.load_env()
            plane_url = env.get("PLANE_URL", "")
            plane_key = env.get("PLANE_API_KEY", "")
            if plane_url and plane_key:
                self._plane = PlaneClient(base_url=plane_url, api_key=plane_key)
        return self._plane

    @property
    def plane_workspace(self) -> str:
        """Plane workspace slug — from env or default 'fleet'."""
        env = self.config.load_env()
        return env.get("PLANE_WORKSPACE", "fleet")

    @property
    def urls(self) -> UrlResolver:
        if self._urls is None:
            projects = self.config.load_projects()
            templates = self.config.load_url_templates()
            self._urls = UrlResolver(projects, templates, board_id=self.board_id)
        return self._urls

    async def resolve_board_id(self) -> str:
        """Resolve board ID if not already known."""
        if not self.board_id:
            self.board_id = await self.mc.get_board_id() or ""
        return self.board_id