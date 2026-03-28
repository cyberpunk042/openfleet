"""Fleet federation — multi-machine identity and collaboration.

Each fleet instance has a unique identity:
- Fleet ID: unique identifier (e.g., "fleet-alpha")
- Fleet Name: human-readable (e.g., "Alpha Team")
- Machine ID: hostname
- Agent prefix: namespace for agents (e.g., "alpha-architect")

Two fleets on different machines can work on the same project (DSPD/Plane)
with their own agents, tasks, and boards, while sharing GitHub repos and
Plane workspaces.

The fleet identity is generated on first setup and persists in
config/fleet-identity.yaml.
"""

from __future__ import annotations

import os
import platform
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class FleetIdentity:
    """Unique identity for a fleet instance."""

    fleet_id: str          # e.g., "fleet-alpha"
    fleet_name: str        # e.g., "Alpha Team"
    machine_id: str        # hostname
    instance_uuid: str     # globally unique UUID
    agent_prefix: str      # namespace prefix for agents
    created_at: str


def load_fleet_identity(fleet_dir: str) -> Optional[FleetIdentity]:
    """Load fleet identity from config/fleet-identity.yaml."""
    path = os.path.join(fleet_dir, "config", "fleet-identity.yaml")
    if not os.path.isfile(path):
        return None

    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        fleet = data.get("fleet", {})
        return FleetIdentity(
            fleet_id=fleet.get("id", ""),
            fleet_name=fleet.get("name", ""),
            machine_id=fleet.get("machine", ""),
            instance_uuid=fleet.get("uuid", ""),
            agent_prefix=fleet.get("agent_prefix", ""),
            created_at=fleet.get("created_at", ""),
        )
    except Exception:
        return None


def generate_fleet_identity(
    fleet_dir: str,
    fleet_name: str = "",
    agent_prefix: str = "",
) -> FleetIdentity:
    """Generate a new fleet identity and save to config/fleet-identity.yaml.

    If the file already exists, returns the existing identity.
    Only generates on first run.
    """
    existing = load_fleet_identity(fleet_dir)
    if existing:
        return existing

    hostname = platform.node() or "unknown"
    instance_uuid = str(uuid.uuid4())
    short_uuid = instance_uuid[:8]

    # Auto-generate names if not provided
    if not fleet_name:
        fleet_name = f"Fleet {hostname}"
    if not agent_prefix:
        agent_prefix = short_uuid[:4]

    fleet_id = f"fleet-{short_uuid}"
    now = datetime.now().isoformat()

    identity = FleetIdentity(
        fleet_id=fleet_id,
        fleet_name=fleet_name,
        machine_id=hostname,
        instance_uuid=instance_uuid,
        agent_prefix=agent_prefix,
        created_at=now,
    )

    # Save to config
    config_dir = os.path.join(fleet_dir, "config")
    os.makedirs(config_dir, exist_ok=True)

    path = os.path.join(config_dir, "fleet-identity.yaml")
    data = {
        "fleet": {
            "id": identity.fleet_id,
            "name": identity.fleet_name,
            "machine": identity.machine_id,
            "uuid": identity.instance_uuid,
            "agent_prefix": identity.agent_prefix,
            "created_at": identity.created_at,
        },
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return identity


def get_namespaced_agent_name(agent_name: str, identity: FleetIdentity) -> str:
    """Get the fleet-namespaced agent name.

    e.g., "architect" → "alpha-architect" for fleet with prefix "alpha"
    """
    if not identity.agent_prefix:
        return agent_name
    return f"{identity.agent_prefix}-{agent_name}"