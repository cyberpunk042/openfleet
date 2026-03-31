"""AICP router unification (M-BR08).

Merges AICP router logic with fleet backend router so both
share the same routing engine, backend registry, budget
awareness, and fallback chains.

Design doc requirement:
> Merge AICP router logic with fleet backend router.
> Shared routing engine, shared backend registry.
> AICP handles user requests, fleet handles agent ops.
> Same budget awareness, same fallback chains.

Status: FUTURE — Stage 3 of LocalAI independence.
This module defines the unification interface. The actual merge
requires both AICP and fleet routers to be mature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UnifiedRoutingRequest:
    """A routing request that works for both AICP and fleet."""

    source: str                    # "aicp" or "fleet"
    task_type: str
    complexity: str = "medium"     # low, medium, high, critical
    budget_mode: str = "standard"
    required_capabilities: list[str] = field(default_factory=list)
    preferred_backend: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "budget_mode": self.budget_mode,
            "required_capabilities": self.required_capabilities,
            "preferred_backend": self.preferred_backend,
        }


@dataclass
class UnifiedRoutingResult:
    """Result of unified routing — same format for AICP and fleet."""

    backend: str
    model: str
    confidence_tier: str
    fallback_chain: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "model": self.model,
            "confidence_tier": self.confidence_tier,
            "fallback_chain": self.fallback_chain,
            "reason": self.reason,
        }