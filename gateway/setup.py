"""OCF Fleet setup — first-time configuration and agent registration.

Handles:
- Creating the organization in Mission Control
- Creating a board for the fleet
- Registering all agents from agents/ directory
- Verifying the setup is complete

Run: python -m gateway.setup
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml


AGENTS_DIR = Path(__file__).parent.parent / "agents"


class FleetSetup:
    """Manages first-time setup of the OCF fleet in Mission Control."""

    def __init__(self, mc_url: str, auth_token: str) -> None:
        self.mc_url = mc_url.rstrip("/")
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    def check_connection(self) -> bool:
        """Verify Mission Control is reachable."""
        try:
            r = httpx.get(f"{self.mc_url}/health", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def get_current_user(self) -> Optional[Dict]:
        """Get the authenticated user."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/users/me",
                headers=self.headers, timeout=5.0,
            )
            if r.status_code == 200:
                return r.json()
            return None
        except Exception:
            return None

    def update_user(self, name: str, preferred_name: str = "", timezone: str = "") -> Optional[Dict]:
        """Update the current user's profile."""
        data = {"name": name}
        if preferred_name:
            data["preferred_name"] = preferred_name
        if timezone:
            data["timezone"] = timezone
        try:
            r = httpx.patch(
                f"{self.mc_url}/api/v1/users/me",
                headers=self.headers, json=data, timeout=5.0,
            )
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def list_organizations(self) -> List[Dict]:
        """List existing organizations."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/organizations",
                headers=self.headers, timeout=5.0,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("items", data) if isinstance(data, dict) else data
            return []
        except Exception:
            return []

    def create_organization(self, name: str, slug: str = "") -> Optional[Dict]:
        """Create an organization."""
        data = {"name": name}
        if slug:
            data["slug"] = slug
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/organizations",
                headers=self.headers, json=data, timeout=5.0,
            )
            return r.json() if r.status_code in (200, 201) else None
        except Exception:
            return None

    def get_active_org(self) -> Optional[Dict]:
        """Get the active organization."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/organizations/me",
                headers=self.headers, timeout=5.0,
            )
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def set_active_org(self, org_id: str) -> bool:
        """Set the active organization."""
        try:
            r = httpx.patch(
                f"{self.mc_url}/api/v1/organizations/me/active",
                headers=self.headers, json={"organization_id": org_id}, timeout=5.0,
            )
            return r.status_code in (200, 204)
        except Exception:
            return False

    def list_gateways(self) -> List[Dict]:
        """List registered gateways."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/gateways",
                headers=self.headers, timeout=5.0,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("items", data) if isinstance(data, dict) else data
            return []
        except Exception:
            return []

    def register_gateway(self, name: str, url: str, workspace_root: str = "/app") -> Optional[Dict]:
        """Register a gateway in Mission Control."""
        # Read gateway auth token from openclaw.json for MC verification
        import json as _json
        gw_token = ""
        oc_config = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.exists(oc_config):
            with open(oc_config) as f:
                oc_cfg = _json.load(f)
            gw_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

        data = {
            "name": name,
            "url": url,
            "workspace_root": workspace_root,
            "disable_device_pairing": True,
        }
        if gw_token:
            data["token"] = gw_token
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/gateways",
                headers=self.headers, json=data, timeout=10.0,
            )
            if r.status_code in (200, 201):
                return r.json()
            print(f"   DEBUG: Gateway register returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"   DEBUG: Gateway register exception: {e}", file=sys.stderr)
            return None

    def list_boards(self) -> List[Dict]:
        """List boards in the active organization."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/boards",
                headers=self.headers, timeout=5.0,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("items", data) if isinstance(data, dict) else data
            return []
        except Exception:
            return []

    def create_board(self, name: str, gateway_id: str, description: str = "") -> Optional[Dict]:
        """Create a board in the active organization."""
        slug = name.lower().replace(" ", "-")
        data = {"name": name, "slug": slug, "gateway_id": gateway_id}
        if description:
            data["description"] = description
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/boards",
                headers=self.headers, json=data, timeout=5.0,
            )
            if r.status_code in (200, 201):
                return r.json()
            print(f"   DEBUG: Board create returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"   DEBUG: Board create exception: {e}", file=sys.stderr)
            return None

    def list_agents(self, board_id: str = None) -> List[Dict]:
        """List registered agents."""
        params = {}
        if board_id:
            params["board_id"] = board_id
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/agents",
                headers=self.headers, params=params, timeout=5.0,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("items", data) if isinstance(data, dict) else data
            return []
        except Exception:
            return []

    def register_agent(self, board_id: str, agent_config: Dict) -> Optional[Dict]:
        """Register an agent in Mission Control from its agent.yaml config."""
        data = {
            "board_id": board_id,
            "name": agent_config.get("name", "unnamed"),
            "status": "provisioning",
            "identity_profile": {
                "role": agent_config.get("description", ""),
                "type": agent_config.get("type", "definition"),
                "capabilities": ", ".join(agent_config.get("capabilities", [])),
                "mode": agent_config.get("mode", "think"),
            },
            "identity_template": agent_config.get("mission", ""),
            "soul_template": f"You are the {agent_config.get('name', '')} agent. "
                           f"Mission: {agent_config.get('mission', '')}",
        }
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/agents",
                headers=self.headers, json=data, timeout=10.0,
            )
            if r.status_code in (200, 201):
                return r.json()
            print(f"   DEBUG: Agent register {agent_config.get('name')} returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"   DEBUG: Agent register exception: {e}", file=sys.stderr)
            return None

    def load_local_agents(self) -> List[Dict]:
        """Load agent configs from agents/ directory."""
        agents = []
        for d in sorted(AGENTS_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                config_path = d / "agent.yaml"
                if config_path.exists():
                    with open(config_path) as f:
                        cfg = yaml.safe_load(f)
                    if cfg:
                        agents.append(cfg)
        return agents


def _detect_timezone() -> str:
    """Detect system timezone."""
    try:
        tz_file = Path("/etc/timezone")
        if tz_file.exists():
            return tz_file.read_text().strip()
    except Exception:
        pass
    return "America/Toronto"


def run_setup() -> int:
    """Interactive fleet setup."""
    mc_url = os.environ.get("OCF_MISSION_CONTROL_URL", "http://localhost:8000")
    auth_token = os.environ.get("LOCAL_AUTH_TOKEN", "")

    if not auth_token:
        # Try reading from .env
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("LOCAL_AUTH_TOKEN="):
                    auth_token = line.split("=", 1)[1].strip()

    if not auth_token:
        print("Error: LOCAL_AUTH_TOKEN not set. Check .env file.", file=sys.stderr)
        return 1

    setup = FleetSetup(mc_url, auth_token)

    print("=== OpenClaw Fleet Setup ===\n")

    # Step 1: Check connection
    print("1. Checking Mission Control connection...")
    if not setup.check_connection():
        print(f"   FAIL: Cannot reach {mc_url}", file=sys.stderr)
        print("   Is Mission Control running? docker compose up -d", file=sys.stderr)
        return 1
    print(f"   OK: {mc_url}")

    # Step 2: Verify user
    print("\n2. Checking user...")
    user = setup.get_current_user()
    if not user:
        print("   FAIL: Cannot authenticate. Check LOCAL_AUTH_TOKEN.", file=sys.stderr)
        return 1
    print(f"   OK: {user.get('name', '?')} ({user.get('email', '?')})")

    if user.get("name") == "Local User" or not user.get("timezone"):
        tz = _detect_timezone()
        print("   Updating user profile...")
        setup.update_user("Jean Fortin", "Jean", timezone=tz)
        print(f"   Updated: Jean Fortin (timezone: {tz})")

    # Step 3: Organization
    print("\n3. Checking organization...")
    org = setup.get_active_org()
    if org:
        print(f"   OK: {org.get('name', '?')} (id: {org.get('id', '?')})")
    else:
        print("   No active org, creating...")
        org = setup.create_organization("OpenClaw Fleet", "openclaw-fleet")
        if org:
            setup.set_active_org(org.get("id", ""))
            print(f"   OK: Created and activated")
        else:
            print("   WARN: Could not create organization")

    # Step 4: Gateway
    print("\n4. Registering gateway...")
    gateways = setup.list_gateways()
    gw = next((g for g in gateways if g.get("name") == "OCF Gateway"), None)
    if not gw:
        # Gateway runs on host, MC backend in Docker reaches it via host IP
        import socket
        host_ip = socket.gethostbyname(socket.gethostname())
        # Gateway URL: Docker containers reach the host via host.docker.internal
        gw_port = os.environ.get("OCF_GATEWAY_PORT", "18789")
        gw_host = os.environ.get("OCF_GATEWAY_HOST", "host.docker.internal")
        fleet_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gw = setup.register_gateway("OCF Gateway", f"ws://{gw_host}:{gw_port}", workspace_root=fleet_dir)
        if gw:
            print(f"   OK: Registered (id: {gw.get('id', '?')})")
        else:
            print("   WARN: Could not register gateway")
    else:
        # Update workspace_root if it's wrong (e.g., /app from old registration)
        fleet_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if gw.get("workspace_root") != fleet_dir:
            try:
                r = httpx.patch(
                    f"{setup.mc_url}/api/v1/gateways/{gw['id']}",
                    headers=setup.headers,
                    json={"workspace_root": fleet_dir},
                    timeout=10.0,
                )
                if r.status_code == 200:
                    print(f"   OK: Updated workspace_root → {fleet_dir}")
                else:
                    print(f"   WARN: Could not update workspace_root: {r.status_code}")
            except Exception as e:
                print(f"   WARN: Could not update workspace_root: {e}")
        print(f"   OK: Already registered (id: {gw.get('id', '?')})")

    # Step 5: Board
    gateway_id = gw.get("id", "") if gw else ""
    print("\n5. Setting up fleet board...")
    boards = setup.list_boards()
    board = next((b for b in boards if b.get("name") == "Fleet Operations"), None)

    if not board and gateway_id:
        board = setup.create_board("Fleet Operations", gateway_id, "Main board for OCF agent workforce")
        if board:
            print(f"   OK: Created (id: {board.get('id', '?')})")
        else:
            print("   WARN: Could not create board")
    elif board:
        print(f"   OK: Already exists (id: {board.get('id', '?')})")
    else:
        print("   WARN: No gateway, cannot create board")

    # Step 6: Register agents
    if board:
        board_id = board.get("id", "")
        print("\n5. Registering agents...")
        local_agents = setup.load_local_agents()
        existing = setup.list_agents(board_id)
        existing_names = {a.get("name", "") for a in existing}

        registered = 0
        for agent_cfg in local_agents:
            name = agent_cfg.get("name", "?")
            if name in existing_names:
                print(f"   SKIP: {name} (already registered)")
            else:
                result = setup.register_agent(board_id, agent_cfg)
                if result:
                    print(f"   OK: {name}")
                    registered += 1
                else:
                    print(f"   WARN: {name} failed")
        print(f"   Registered {registered}/{len(local_agents)} agents")
    else:
        print("\n   Skipping agents (no board)")

    # Step 7: Sync templates (push TOOLS.md + SOUL.md to agents)
    if gw:
        gw_id = gw.get("id", "")
        print("\n7. Syncing agent templates...")
        try:
            r = httpx.post(
                f"{mc_url}/api/v1/gateways/{gw_id}/templates/sync?rotate_tokens=true&force_bootstrap=true",
                headers=setup.headers, json={}, timeout=30.0,
            )
            if r.status_code in (200, 201):
                result = r.json()
                updated = result.get("agents_updated", 0)
                errors = result.get("errors", [])
                print(f"   OK: {updated} agents provisioned")
                for err in errors[:3]:
                    print(f"   WARN: {err.get('agent_name', '?')}: {err.get('message', '?')[:100]}")
            else:
                print(f"   WARN: Template sync returned {r.status_code}")
        except Exception as e:
            print(f"   WARN: Template sync failed: {e}")

    # Step 8: Push SOUL.md to agent workspaces
    print("\n8. Pushing SOUL.md to agent workspaces...")
    push_script = Path(__file__).parent.parent / "scripts" / "push-soul.sh"
    if push_script.exists():
        import subprocess
        result = subprocess.run(["bash", str(push_script)], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[-3:]:
                print(f"   {line}")
        else:
            print(f"   WARN: push-soul.sh failed: {result.stderr[:200]}")
    else:
        print("   SKIP: scripts/push-soul.sh not found")

    # Step 9: Save setup state
    print("\n9. Saving setup state...")
    state_path = Path(__file__).parent.parent / ".aicp" / "state.yaml"
    if state_path.exists():
        with open(state_path) as f:
            state = yaml.safe_load(f) or {}
        state["phase"] = "setup-complete"
        state["setup"] = {
            "mission_control_url": mc_url,
            "user": user.get("name", "?"),
            "organization": org.get("name", "?") if org else None,
            "board": board.get("name", "?") if org and board else None,
        }
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        print("   OK: State saved to .aicp/state.yaml")

    print("\n=== Setup complete ===")
    print(f"Mission Control UI: http://localhost:3000")
    print(f"Mission Control API: {mc_url}")
    print(f"OCF Gateway: http://localhost:9400")
    return 0


if __name__ == "__main__":
    sys.exit(run_setup())