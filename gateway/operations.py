"""Continuous operations loop — polls MC for tasks, executes, reports back.

This is the autonomous operation mode for the OCF gateway.
Runs as a background loop that:
1. Polls Mission Control for tasks assigned to our agents
2. Executes them through Claude Code
3. Posts results back as task comments
4. Updates task status
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml

AGENTS_DIR = Path(__file__).parent.parent / "agents"


class FleetOperator:
    """Manages continuous fleet operations against Mission Control."""

    def __init__(self, mc_url: str, auth_token: str, board_id: str) -> None:
        self.mc_url = mc_url.rstrip("/")
        self.auth_token = auth_token
        self.board_id = board_id
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self.agent_map: Dict[str, Dict] = {}  # MC agent_id → local config
        self._load_agent_map()

    def _load_agent_map(self) -> None:
        """Map MC agent IDs to local agent configs."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/agents",
                headers=self.headers,
                params={"board_id": self.board_id, "limit": 50},
                timeout=10.0,
            )
            if r.status_code == 200:
                data = r.json()
                agents = data.get("items", data) if isinstance(data, dict) else data
                for a in agents:
                    name = a.get("name", "")
                    mc_id = a.get("id", "")
                    # Load local config
                    config_path = AGENTS_DIR / name / "agent.yaml"
                    local_cfg = {}
                    if config_path.exists():
                        with open(config_path) as f:
                            local_cfg = yaml.safe_load(f) or {}
                    self.agent_map[mc_id] = {
                        "name": name,
                        "mc_id": mc_id,
                        "local_config": local_cfg,
                        "status": a.get("status", ""),
                    }
        except Exception as e:
            print(f"[ops] Failed to load agent map: {e}")

    def activate_agents(self) -> int:
        """Set all provisioning agents to active."""
        activated = 0
        for mc_id, info in self.agent_map.items():
            if info["status"] == "provisioning":
                try:
                    r = httpx.patch(
                        f"{self.mc_url}/api/v1/agents/{mc_id}",
                        headers=self.headers,
                        json={"status": "active"},
                        timeout=10.0,
                    )
                    if r.status_code == 200:
                        info["status"] = "active"
                        activated += 1
                        print(f"[ops] Activated: {info['name']}")
                except Exception as e:
                    print(f"[ops] Failed to activate {info['name']}: {e}")
        return activated

    def create_task(
        self, title: str, description: str = "",
        agent_name: str = None, tags: List[str] = None,
    ) -> Optional[Dict]:
        """Create a task on the fleet board."""
        data = {"title": title}
        if description:
            data["description"] = description
        if tags:
            data["tags"] = tags
        # Assign to agent if specified
        if agent_name:
            for mc_id, info in self.agent_map.items():
                if info["name"] == agent_name:
                    data["assignee_agent_id"] = mc_id
                    break
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/boards/{self.board_id}/tasks",
                headers=self.headers, json=data, timeout=10.0,
            )
            if r.status_code in (200, 201):
                task = r.json()
                print(f"[ops] Task created: {title} (id: {task.get('id', '?')})")
                return task
            else:
                print(f"[ops] Task create failed: {r.status_code} {r.text[:200]}")
                return None
        except Exception as e:
            print(f"[ops] Task create error: {e}")
            return None

    def get_pending_tasks(self) -> List[Dict]:
        """Get tasks that need execution."""
        try:
            r = httpx.get(
                f"{self.mc_url}/api/v1/boards/{self.board_id}/tasks",
                headers=self.headers,
                params={"limit": 20},
                timeout=10.0,
            )
            if r.status_code == 200:
                data = r.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                # Filter for actionable tasks (not done/cancelled)
                return [
                    t for t in tasks
                    if t.get("status") not in ("done", "cancelled", "completed")
                ]
            return []
        except Exception as e:
            print(f"[ops] Failed to get tasks: {e}")
            return []

    def post_task_comment(self, task_id: str, content: str) -> bool:
        """Post a comment/result on a task."""
        try:
            r = httpx.post(
                f"{self.mc_url}/api/v1/boards/{self.board_id}/tasks/{task_id}/comments",
                headers=self.headers,
                json={"content": content},
                timeout=10.0,
            )
            return r.status_code in (200, 201)
        except Exception:
            return False

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update a task's status."""
        try:
            r = httpx.patch(
                f"{self.mc_url}/api/v1/boards/{self.board_id}/tasks/{task_id}",
                headers=self.headers,
                json={"status": status},
                timeout=10.0,
            )
            return r.status_code == 200
        except Exception:
            return False


def load_operator() -> Optional[FleetOperator]:
    """Create a FleetOperator from environment/.env."""
    mc_url = os.environ.get("OCF_MISSION_CONTROL_URL", "http://localhost:8000")
    auth_token = os.environ.get("LOCAL_AUTH_TOKEN", "")

    if not auth_token:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("LOCAL_AUTH_TOKEN="):
                    auth_token = line.split("=", 1)[1].strip()

    if not auth_token:
        print("[ops] No auth token found")
        return None

    # Find board ID from state
    state_path = Path(__file__).parent.parent / ".aicp" / "state.yaml"
    board_id = ""
    if state_path.exists():
        with open(state_path) as f:
            state = yaml.safe_load(f) or {}
        board_id = state.get("setup", {}).get("board_id", "")

    if not board_id:
        # Try to find it from MC
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            r = httpx.get(f"{mc_url}/api/v1/boards", headers=headers, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                boards = data.get("items", data) if isinstance(data, dict) else data
                for b in boards:
                    if b.get("name") == "Fleet Operations":
                        board_id = b["id"]
                        break
        except Exception:
            pass

    if not board_id:
        print("[ops] No board ID found")
        return None

    return FleetOperator(mc_url, auth_token, board_id)


def run_operations_demo() -> int:
    """Demo: create tasks, activate agents, show the operational flow."""
    op = load_operator()
    if not op:
        return 1

    print("=== OpenClaw Fleet Operations ===\n")

    # Step 1: Activate agents
    print("1. Activating agents...")
    activated = op.activate_agents()
    print(f"   Activated {activated} agents\n")

    # Step 2: Create a sample task
    print("2. Creating sample tasks...")
    op.create_task(
        "Design the Structuring layer for ocf-tag",
        description="Layer 2 of the Accountability Generator. Normalize intake data into actors, institutions, decisions, dependencies, impacts, contradictions, timelines, confidence levels.",
        agent_name="architect",
        tags=["ocf-tag", "layer-2", "design"],
    )
    op.create_task(
        "Review Intake layer code quality",
        description="Review agents/accountability-generator/src/ for code quality, patterns, and potential issues.",
        agent_name="qa-engineer",
        tags=["ocf-tag", "layer-1", "review"],
    )

    # Step 3: List pending tasks
    print("\n3. Pending tasks:")
    tasks = op.get_pending_tasks()
    for t in tasks:
        print(f"   [{t.get('status','?'):12s}] {t.get('title','?')}")

    print(f"\n=== {len(tasks)} tasks pending, {len(op.agent_map)} agents active ===")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_operations_demo())