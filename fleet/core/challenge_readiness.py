"""Challenge-aware readiness progression (M-IV06).

Integrates challenge status into task readiness progression.
Adds a challenge stage between work completion and review:

  70% → Work complete, ready for challenge
  80% → Challenge passed (or waived/not required)
  90% → Fleet-ops review passed
  95% → PO gate (final approval)
  100% → Done

The brain enforces: no review until challenge passed (or waived).
This prevents work from reaching fleet-ops review without validation.

Readiness checkpoints:
  WORK_COMPLETE     = 70   # Agent finished implementation
  CHALLENGE_PASSED  = 80   # Adversarial validation survived
  REVIEW_PASSED     = 90   # Fleet-ops approved
  PO_APPROVED       = 95   # Product owner signed off
  DONE              = 100  # Task closed
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fleet.core.challenge import ChallengeStatus


# ─── Readiness Checkpoints ───────────────────────────────────────

WORK_COMPLETE = 70
CHALLENGE_PASSED = 80
REVIEW_PASSED = 90
PO_APPROVED = 95
DONE = 100


# ─── Challenge Readiness Check ───────────────────────────────────


@dataclass
class ChallengeReadinessCheck:
    """Result of checking whether a task can advance past challenge stage."""

    can_advance: bool
    current_readiness: int
    target_readiness: int
    reason: str
    challenge_status: str = ""
    blocking_findings: int = 0

    @property
    def is_blocked(self) -> bool:
        return not self.can_advance

    def to_dict(self) -> dict:
        return {
            "can_advance": self.can_advance,
            "current_readiness": self.current_readiness,
            "target_readiness": self.target_readiness,
            "reason": self.reason,
            "challenge_status": self.challenge_status,
            "blocking_findings": self.blocking_findings,
        }


def check_challenge_readiness(
    current_readiness: int,
    challenge_required: bool,
    challenge_status: str | None,
    open_findings: int = 0,
) -> ChallengeReadinessCheck:
    """Check if a task can advance past the challenge gate.

    Rules:
    - If readiness < 70: not ready for challenge yet (still in work)
    - If challenge not required: can advance to 80 immediately
    - If challenge passed: can advance to 80
    - If challenge waived: can advance to 80
    - If challenge deferred: can advance to 80 (will be challenged later)
    - If challenge failed with open findings: blocked until addressed
    - If challenge pending/in_progress: blocked until complete

    Args:
        current_readiness: Current task readiness percentage.
        challenge_required: Whether challenge is required for this task.
        challenge_status: Current challenge status (ChallengeStatus value).
        open_findings: Number of unresolved findings.

    Returns:
        ChallengeReadinessCheck with advancement decision.
    """
    # Not ready for challenge yet
    if current_readiness < WORK_COMPLETE:
        return ChallengeReadinessCheck(
            can_advance=False,
            current_readiness=current_readiness,
            target_readiness=WORK_COMPLETE,
            reason=f"work not complete (readiness {current_readiness}% < {WORK_COMPLETE}%)",
        )

    # Challenge not required — skip to 80
    if not challenge_required:
        return ChallengeReadinessCheck(
            can_advance=True,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge not required — advancing to review",
        )

    # No challenge started yet
    if not challenge_status:
        return ChallengeReadinessCheck(
            can_advance=False,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge required but not started",
            challenge_status="pending",
        )

    # Challenge passed
    if challenge_status == ChallengeStatus.PASSED:
        return ChallengeReadinessCheck(
            can_advance=True,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge passed — advancing to review",
            challenge_status=challenge_status,
        )

    # Challenge waived (low risk or PO decision)
    if challenge_status == ChallengeStatus.WAIVED:
        return ChallengeReadinessCheck(
            can_advance=True,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge waived — advancing to review",
            challenge_status=challenge_status,
        )

    # Challenge deferred (budget constraint — will be challenged later)
    if challenge_status == ChallengeStatus.DEFERRED:
        return ChallengeReadinessCheck(
            can_advance=True,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge deferred (budget) — advancing to review with caveat",
            challenge_status=challenge_status,
        )

    # Challenge in progress — wait
    if challenge_status == ChallengeStatus.IN_PROGRESS:
        return ChallengeReadinessCheck(
            can_advance=False,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge in progress — waiting for completion",
            challenge_status=challenge_status,
        )

    # Challenge failed with open findings
    if challenge_status == ChallengeStatus.FAILED:
        return ChallengeReadinessCheck(
            can_advance=False,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason=f"challenge failed with {open_findings} open finding(s) — "
                   f"author must address before advancing",
            challenge_status=challenge_status,
            blocking_findings=open_findings,
        )

    # Challenge pending
    if challenge_status == ChallengeStatus.PENDING:
        return ChallengeReadinessCheck(
            can_advance=False,
            current_readiness=current_readiness,
            target_readiness=CHALLENGE_PASSED,
            reason="challenge pending — waiting for challenger assignment",
            challenge_status=challenge_status,
        )

    # Unknown status — block by default
    return ChallengeReadinessCheck(
        can_advance=False,
        current_readiness=current_readiness,
        target_readiness=CHALLENGE_PASSED,
        reason=f"unknown challenge status: {challenge_status}",
        challenge_status=challenge_status or "",
    )


# ─── Readiness Progression ───────────────────────────────────────


def compute_readiness_with_challenge(
    work_complete: bool,
    challenge_required: bool,
    challenge_status: str | None,
    review_passed: bool = False,
    po_approved: bool = False,
) -> int:
    """Compute task readiness percentage incorporating challenge stage.

    This extends the standard readiness computation to account for
    the challenge stage between work and review.

    Args:
        work_complete: Whether the agent has finished implementation.
        challenge_required: Whether challenge is required.
        challenge_status: Current challenge status.
        review_passed: Whether fleet-ops review passed.
        po_approved: Whether PO approved.

    Returns:
        Readiness percentage (0-100).
    """
    if po_approved:
        return DONE

    if review_passed:
        return PO_APPROVED

    if not work_complete:
        return 50  # Work in progress

    # Work complete — check challenge gate
    challenge_clear = (
        not challenge_required
        or challenge_status in (
            ChallengeStatus.PASSED,
            ChallengeStatus.WAIVED,
            ChallengeStatus.DEFERRED,
        )
    )

    if challenge_clear:
        return CHALLENGE_PASSED

    return WORK_COMPLETE


# ─── Stage Labels ────────────────────────────────────────────────


def readiness_stage_label(readiness: int) -> str:
    """Human-readable label for the current readiness stage.

    Args:
        readiness: Current readiness percentage.

    Returns:
        Stage label string.
    """
    if readiness >= DONE:
        return "done"
    if readiness >= PO_APPROVED:
        return "po-review"
    if readiness >= REVIEW_PASSED:
        return "review-passed"
    if readiness >= CHALLENGE_PASSED:
        return "challenge-passed"
    if readiness >= WORK_COMPLETE:
        return "challenge-pending"
    return "in-progress"


def readiness_to_emoji(readiness: int) -> str:
    """Emoji indicator for readiness stage (for IRC/dashboard)."""
    if readiness >= DONE:
        return "[DONE]"
    if readiness >= PO_APPROVED:
        return "[PO]"
    if readiness >= REVIEW_PASSED:
        return "[REVIEWED]"
    if readiness >= CHALLENGE_PASSED:
        return "[CHALLENGED]"
    if readiness >= WORK_COMPLETE:
        return "[CHALLENGING]"
    return "[WORKING]"