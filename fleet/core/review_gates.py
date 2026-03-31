"""Confidence-aware review gates (M-LA06).

Determines review depth based on the confidence tier of the work.
Trainee and community tier artifacts require deeper scrutiny than
expert or standard tier work.

Confidence tiers:
  expert    (Claude opus)       — standard review
  standard  (Claude sonnet)     — standard review
  trainee   (LocalAI)           — extra scrutiny: adversarial challenge + architect
  community (OpenRouter free)   — extra scrutiny: adversarial challenge + architect
  hybrid    (mixed backends)    — enhanced review: architect required
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReviewGate:
    """A single review gate requirement."""

    agent: str
    gate_type: str       # "required", "advisory", "challenge"
    status: str = "pending"
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "type": self.gate_type,
            "status": self.status,
            "reason": self.reason,
        }


# ─── Review Depth by Confidence Tier ──────────────────────────────


# Which tiers require adversarial challenge before approval
CHALLENGE_REQUIRED_TIERS = {"trainee", "community"}

# Which tiers require architect review regardless of task type
ARCHITECT_REQUIRED_TIERS = {"trainee", "community", "hybrid"}

# Minimum number of review gates per tier
MIN_GATES_BY_TIER: dict[str, int] = {
    "expert": 1,      # fleet-ops only
    "standard": 1,    # fleet-ops only
    "trainee": 3,     # challenge + architect + fleet-ops
    "community": 3,   # challenge + architect + fleet-ops
    "hybrid": 2,      # architect + fleet-ops
}


def build_review_gates(
    task_type: str,
    has_code: bool,
    confidence_tier: str = "standard",
    budget_mode: str = "standard",
) -> list[ReviewGate]:
    """Build review gates based on task type, code, and confidence tier.

    Args:
        task_type: The task type (epic, story, subtask, etc.)
        has_code: Whether the task produced code changes
        confidence_tier: The confidence tier of the work
        budget_mode: Current budget mode (challenges disabled in frugal+)

    Returns:
        Ordered list of ReviewGate objects.
    """
    gates: list[ReviewGate] = []

    # ─── Confidence-tier gates (run first) ──────────────────────
    needs_challenge = (
        confidence_tier in CHALLENGE_REQUIRED_TIERS
        and budget_mode not in ("frugal", "survival", "blackout")
    )

    if needs_challenge:
        gates.append(ReviewGate(
            agent="challenge-runner",
            gate_type="challenge",
            reason=f"{confidence_tier} tier work requires adversarial validation",
        ))

    if confidence_tier in ARCHITECT_REQUIRED_TIERS:
        gates.append(ReviewGate(
            agent="architect",
            gate_type="required",
            reason=f"{confidence_tier} tier work requires architecture review",
        ))

    # ─── Standard task-type gates ───────────────────────────────
    if has_code and not _has_agent_gate(gates, "qa-engineer"):
        gates.append(ReviewGate(
            agent="qa-engineer",
            gate_type="required",
            reason="code changes require QA review",
        ))

    if task_type in ("epic", "story") and not _has_agent_gate(gates, "architect"):
        gates.append(ReviewGate(
            agent="architect",
            gate_type="required",
            reason=f"{task_type} requires architecture review",
        ))

    if task_type in ("blocker", "concern") and not _has_agent_gate(gates, "devsecops-expert"):
        gates.append(ReviewGate(
            agent="devsecops-expert",
            gate_type="required",
            reason=f"{task_type} requires security review",
        ))

    # ─── fleet-ops is always the final gate ─────────────────────
    gates.append(ReviewGate(
        agent="fleet-ops",
        gate_type="required",
        reason="board lead final review",
    ))

    return gates


def review_depth_label(confidence_tier: str) -> str:
    """Human-readable label for the review depth applied to a tier."""
    if confidence_tier in CHALLENGE_REQUIRED_TIERS:
        return "deep (adversarial challenge + architect + fleet-ops)"
    if confidence_tier in ARCHITECT_REQUIRED_TIERS:
        return "enhanced (architect + fleet-ops)"
    return "standard (fleet-ops)"


def gates_to_dicts(gates: list[ReviewGate]) -> list[dict]:
    """Convert gates to dict format for MC custom fields."""
    return [g.to_dict() for g in gates]


def _has_agent_gate(gates: list[ReviewGate], agent: str) -> bool:
    """Check if an agent already has a gate."""
    return any(g.agent == agent for g in gates)