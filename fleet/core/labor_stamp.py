"""Labor attribution — provenance tracking for fleet-produced artifacts.

Every artifact carries a LaborStamp recording what produced it, how, and
at what confidence level. Stamps are populated by infrastructure (dispatch
+ session metrics), not by agents.

Confidence tiers:
  expert    — Claude opus (deep reasoning)
  standard  — Claude sonnet/haiku or deterministic output
  trainee   — LocalAI (any model) — learning, needs extra review
  community — OpenRouter free tier — best-effort, must verify
  hybrid    — Multiple backends in one task — highest scrutiny
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─── Confidence Tier Derivation ─────────────────────────────────────────


def derive_confidence_tier(backend: str, model: str) -> tuple[str, str]:
    """Derive confidence tier from backend and model.

    Returns (tier, reason).
    """
    if backend == "direct":
        return "standard", "deterministic/no-LLM — rule-based output"
    if backend == "claude-code":
        if "opus" in model:
            return "expert", f"cloud/{model}"
        return "standard", f"cloud/{model}"
    if backend == "localai":
        return "trainee", f"local/{model} — quality unvalidated at scale"
    if backend == "openrouter":
        return "community", f"free-tier/{model} — best-effort, must verify"
    return "community", f"unknown/{backend}/{model}"


# ─── LaborStamp ─────────────────────────────────────────────────────────


@dataclass
class LaborStamp:
    """Complete provenance record for any fleet-produced artifact."""

    # WHO
    agent_name: str = ""
    agent_role: str = ""                   # worker, driver

    # WHAT PRODUCED IT
    backend: str = ""                      # claude-code, localai, openrouter, direct
    model: str = ""                        # opus-4-6, sonnet-4-6, hermes-3b, qwen3-8b
    model_version: str = ""                # Full model ID for reproducibility
    effort: str = "medium"                 # low, medium, high, max

    # HOW
    skills_used: list[str] = field(default_factory=list)
    tools_called: list[str] = field(default_factory=list)
    session_type: str = ""                 # fresh, compact, continue

    # CONFIDENCE
    confidence_tier: str = ""              # expert, standard, trainee, community, hybrid
    confidence_reason: str = ""

    # COST
    duration_seconds: int = 0
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0

    # EFFORT (from session telemetry)
    lines_added: int = 0
    lines_removed: int = 0
    cache_read_tokens: int = 0

    # ITERATION
    iteration: int = 1
    challenge_rounds_survived: int = 0
    challenge_types_faced: list[str] = field(default_factory=list)
    challenge_skipped: bool = False
    challenge_skip_reason: str = ""    # e.g. "frugal mode", "blackout"
    previous_attempt_id: Optional[str] = None

    # CONTEXT
    budget_mode: str = "standard"
    fallback_from: Optional[str] = None    # If this was a fallback routing
    fallback_reason: Optional[str] = None

    # TIMESTAMP
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.confidence_tier and self.backend:
            self.confidence_tier, self.confidence_reason = derive_confidence_tier(
                self.backend, self.model
            )

    @property
    def requires_challenge(self) -> bool:
        """Whether this tier requires adversarial challenge before approval."""
        return self.confidence_tier in ("trainee", "community", "hybrid")

    @property
    def short_label(self) -> str:
        """Short label for footers: 'opus-4-6 · expert'."""
        return f"{self.model} · {self.confidence_tier}"

    def to_dict(self) -> dict:
        """Serialize for storage in custom fields or events."""
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "backend": self.backend,
            "model": self.model,
            "model_version": self.model_version,
            "effort": self.effort,
            "skills_used": self.skills_used,
            "tools_called": self.tools_called,
            "session_type": self.session_type,
            "confidence_tier": self.confidence_tier,
            "confidence_reason": self.confidence_reason,
            "duration_seconds": self.duration_seconds,
            "estimated_tokens": self.estimated_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "iteration": self.iteration,
            "challenge_rounds_survived": self.challenge_rounds_survived,
            "challenge_types_faced": self.challenge_types_faced,
            "budget_mode": self.budget_mode,
            "fallback_from": self.fallback_from,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LaborStamp:
        """Deserialize from stored dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ─── Dispatch Record ────────────────────────────────────────────────────


@dataclass
class DispatchRecord:
    """Recorded by the brain when dispatching a task.

    Captures the intent — what model/effort/backend was selected and why.
    Made available to fleet_task_complete via session context so the stamp
    can be assembled at completion time.
    """

    task_id: str
    agent_name: str
    backend: str                           # claude-code, localai, openrouter
    model: str                             # Selected model
    effort: str                            # Selected effort
    selection_reason: str                   # Why this model was selected
    budget_mode: str                       # Active budget mode at dispatch time
    skills: list[str] = field(default_factory=list)
    dispatched_at: str = ""

    def __post_init__(self) -> None:
        if not self.dispatched_at:
            self.dispatched_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "backend": self.backend,
            "model": self.model,
            "effort": self.effort,
            "selection_reason": self.selection_reason,
            "budget_mode": self.budget_mode,
            "skills": self.skills,
            "dispatched_at": self.dispatched_at,
        }


# ─── Stamp Assembly ─────────────────────────────────────────────────────


def assemble_stamp(
    dispatch: DispatchRecord,
    duration_seconds: int = 0,
    estimated_tokens: int = 0,
    tools_called: list[str] | None = None,
    session_type: str = "",
    iteration: int = 1,
    agent_role: str = "worker",
) -> LaborStamp:
    """Assemble a LaborStamp from dispatch record + session metrics.

    Called by fleet_task_complete when a task finishes.
    """
    tier, reason = derive_confidence_tier(dispatch.backend, dispatch.model)

    # Estimate cost based on backend
    cost = 0.0
    if dispatch.backend == "claude-code":
        if "opus" in dispatch.model:
            cost = estimated_tokens * 0.000045  # rough opus avg
        else:
            cost = estimated_tokens * 0.000009  # rough sonnet avg
    # localai and openrouter-free = $0

    return LaborStamp(
        agent_name=dispatch.agent_name,
        agent_role=agent_role,
        backend=dispatch.backend,
        model=dispatch.model,
        model_version=dispatch.model,
        effort=dispatch.effort,
        skills_used=dispatch.skills,
        tools_called=tools_called or [],
        session_type=session_type,
        confidence_tier=tier,
        confidence_reason=reason,
        duration_seconds=duration_seconds,
        estimated_tokens=estimated_tokens,
        estimated_cost_usd=round(cost, 4),
        iteration=iteration,
        budget_mode=dispatch.budget_mode,
    )


def mark_challenge_skipped(
    stamp: LaborStamp,
    reason: str = "",
) -> None:
    """Mark a stamp as having its challenge skipped.

    Called when ChallengeDecision.deferred is True (budget too tight)
    or when challenge is waived for other reasons.
    """
    stamp.challenge_skipped = True
    stamp.challenge_skip_reason = reason