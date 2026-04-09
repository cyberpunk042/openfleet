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
    challenge_skip_reason: str = ""
    previous_attempt_id: Optional[str] = None

    # CONTEXT
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
    def is_trainee(self) -> bool:
        """Whether this artifact was produced by a trainee-tier model.

        Trainee work needs extra review scrutiny. Fleet-ops should know
        this during the 7-step review — it affects confidence in the output.
        PO directive: "flagged as trainee's work like any other variant
        in what was used to generate the artifacts."
        """
        return self.confidence_tier in ("trainee", "community")

    @property
    def requires_challenge(self) -> bool:
        """Whether this tier requires adversarial challenge before approval."""
        return self.confidence_tier in ("trainee", "community", "hybrid")

    @property
    def trainee_warning(self) -> str:
        """Warning text for trainee-produced artifacts. Empty for expert/standard."""
        if not self.is_trainee:
            return ""
        if self.confidence_tier == "trainee":
            return f"⚠️ TRAINEE OUTPUT — produced by {self.model} (LocalAI). Requires extra review scrutiny."
        if self.confidence_tier == "community":
            return f"⚠️ COMMUNITY OUTPUT — produced by {self.model} (free tier). Must verify correctness."
        return ""

    @property
    def short_label(self) -> str:
        """Short label for footers: 'opus-4-6 · expert'."""
        return f"{self.model} · {self.confidence_tier}"

    @property
    def provenance_line(self) -> str:
        """One-line provenance for PR bodies, comments, and IRC.

        Shows: agent · model · tier · effort. Trainee gets warning prefix.
        """
        prefix = "⚠️ " if self.is_trainee else ""
        return f"{prefix}{self.agent_name} · {self.model} · {self.confidence_tier} · effort:{self.effort}"

    @property
    def full_signature(self) -> str:
        """Full signature with all metrics for detailed transparency.

        PO directive: "all the detail about the effort, context size,
        consumed and etc.... this way we use the agent identity and all
        his metrics and settings to actually generate transparency."
        """
        parts = [
            f"Agent: {self.agent_name}",
            f"Model: {self.model} ({self.confidence_tier})",
            f"Backend: {self.backend}",
            f"Effort: {self.effort}",
        ]
        if self.duration_seconds:
            mins = self.duration_seconds // 60
            secs = self.duration_seconds % 60
            parts.append(f"Duration: {mins}m{secs}s")
        if self.estimated_tokens:
            parts.append(f"Tokens: ~{self.estimated_tokens:,}")
        if self.estimated_cost_usd:
            parts.append(f"Cost: ${self.estimated_cost_usd:.4f}")
        if self.lines_added or self.lines_removed:
            parts.append(f"Lines: +{self.lines_added}/-{self.lines_removed}")
        if self.cache_read_tokens:
            parts.append(f"Cache: {self.cache_read_tokens:,} tokens read")
        if self.iteration > 1:
            parts.append(f"Iteration: {self.iteration}")
        if self.challenge_rounds_survived:
            parts.append(f"Challenge: {self.challenge_rounds_survived} rounds passed")
        if self.session_type:
            parts.append(f"Session: {self.session_type}")
        if self.fallback_from:
            parts.append(f"Fallback from: {self.fallback_from}")
        return " | ".join(parts)

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
