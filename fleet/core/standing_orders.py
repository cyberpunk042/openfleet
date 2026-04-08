"""Standing orders — autonomous authority per role.

Reads config/standing-orders.yaml and returns standing orders
for a given agent role, respecting fleet state.

Used by preembed to include standing orders in heartbeat context.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_config: dict | None = None


def _load_config() -> dict:
    global _config
    if _config is not None:
        return _config

    fleet_dir = Path(__file__).resolve().parent.parent.parent
    config_path = fleet_dir / "config" / "standing-orders.yaml"

    if not config_path.exists():
        _config = {}
        return _config

    try:
        import yaml
        with open(config_path) as f:
            _config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Failed to load standing-orders.yaml: %s", e)
        _config = {}

    return _config


def get_standing_orders(agent_name: str) -> dict[str, Any]:
    """Get standing orders for an agent role.

    Returns:
        authority_level: conservative | standard | autonomous
        orders: list of standing order dicts with name, description, when, boundary
        escalation_threshold: number of autonomous actions before escalation
    """
    config = _load_config()
    if not config:
        return {"authority_level": "conservative", "orders": [], "escalation_threshold": 2}

    defaults = config.get("defaults", {})
    role_config = config.get(agent_name, {})

    authority = role_config.get("authority_level",
                                defaults.get("authority_level", "conservative"))
    threshold = defaults.get("escalation_threshold", 2)

    orders = []
    for order in role_config.get("standing_orders", []):
        orders.append({
            "name": order.get("name", ""),
            "description": order.get("description", ""),
            "when": order.get("when", ""),
            "boundary": order.get("boundary", ""),
        })

    return {
        "authority_level": authority,
        "orders": orders,
        "escalation_threshold": threshold,
    }
