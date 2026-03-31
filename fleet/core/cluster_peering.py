"""Cluster peering — Machine 1 ↔ Machine 2 (M-MU08).

Configuration for LocalAI cluster peering between two machines.
Load balancing and failover across clusters.

Design doc requirement:
> LocalAI cluster configuration for two machines.
> Load balancing between clusters.
> Failover: if Machine 1's GPU is busy, route to Machine 2.
> Shared model registry across clusters.

Status: FUTURE — depends on second machine.
This module defines the peering configuration schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClusterNode:
    """A machine in the LocalAI cluster."""

    node_id: str
    hostname: str
    localai_url: str              # e.g., "http://192.168.1.10:8090/v1"
    vram_mb: int = 8192
    models_available: list[str] = field(default_factory=list)
    model_loaded: str = ""
    healthy: bool = False
    last_seen: float = 0.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "localai_url": self.localai_url,
            "vram_mb": self.vram_mb,
            "models_available": self.models_available,
            "model_loaded": self.model_loaded,
            "healthy": self.healthy,
        }


@dataclass
class ClusterPeeringConfig:
    """Peering configuration for two LocalAI clusters."""

    nodes: list[ClusterNode] = field(default_factory=list)
    load_balance_strategy: str = "round-robin"  # round-robin, least-loaded, model-affinity

    def healthy_nodes(self) -> list[ClusterNode]:
        return [n for n in self.nodes if n.healthy]

    def node_with_model(self, model: str) -> Optional[ClusterNode]:
        """Find a healthy node that has the model loaded."""
        for n in self.nodes:
            if n.healthy and n.model_loaded == model:
                return n
        return None

    def node_that_can_load(self, model: str) -> Optional[ClusterNode]:
        """Find a healthy node that has the model available (but not loaded)."""
        for n in self.nodes:
            if n.healthy and model in n.models_available:
                return n
        return None

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "load_balance_strategy": self.load_balance_strategy,
            "healthy_count": len(self.healthy_nodes()),
        }