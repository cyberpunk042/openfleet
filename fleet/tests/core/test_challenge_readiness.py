"""Tests for challenge-aware readiness progression (M-IV06)."""

from fleet.core.challenge import ChallengeStatus
from fleet.core.challenge_readiness import (
    CHALLENGE_PASSED,
    DONE,
    PO_APPROVED,
    REVIEW_PASSED,
    WORK_COMPLETE,
    ChallengeReadinessCheck,
    check_challenge_readiness,
    compute_readiness_with_challenge,
    readiness_stage_label,
    readiness_to_emoji,
)


# ─── Constants ───────────────────────────────────────────────────


def test_checkpoint_values():
    assert WORK_COMPLETE == 70
    assert CHALLENGE_PASSED == 80
    assert REVIEW_PASSED == 90
    assert PO_APPROVED == 95
    assert DONE == 100


def test_checkpoint_ordering():
    assert WORK_COMPLETE < CHALLENGE_PASSED < REVIEW_PASSED < PO_APPROVED < DONE


# ─── ChallengeReadinessCheck ────────────────────────────────────


def test_check_dataclass():
    c = ChallengeReadinessCheck(
        can_advance=False, current_readiness=70,
        target_readiness=80, reason="blocked",
        blocking_findings=2,
    )
    assert c.is_blocked
    assert c.blocking_findings == 2


def test_check_to_dict():
    c = ChallengeReadinessCheck(
        can_advance=True, current_readiness=70,
        target_readiness=80, reason="passed",
        challenge_status="passed",
    )
    d = c.to_dict()
    assert d["can_advance"] is True
    assert d["challenge_status"] == "passed"


# ─── check_challenge_readiness ──────────────────────────────────


def test_not_ready_for_challenge():
    result = check_challenge_readiness(50, True, None)
    assert not result.can_advance
    assert "work not complete" in result.reason


def test_challenge_not_required():
    result = check_challenge_readiness(70, False, None)
    assert result.can_advance
    assert "not required" in result.reason


def test_challenge_not_started():
    result = check_challenge_readiness(70, True, None)
    assert not result.can_advance
    assert "not started" in result.reason


def test_challenge_passed():
    result = check_challenge_readiness(70, True, ChallengeStatus.PASSED)
    assert result.can_advance
    assert "passed" in result.reason


def test_challenge_waived():
    result = check_challenge_readiness(70, True, ChallengeStatus.WAIVED)
    assert result.can_advance
    assert "waived" in result.reason


def test_challenge_deferred():
    result = check_challenge_readiness(70, True, ChallengeStatus.DEFERRED)
    assert result.can_advance
    assert "deferred" in result.reason


def test_challenge_in_progress():
    result = check_challenge_readiness(70, True, ChallengeStatus.IN_PROGRESS)
    assert not result.can_advance
    assert "in progress" in result.reason


def test_challenge_failed():
    result = check_challenge_readiness(70, True, ChallengeStatus.FAILED, open_findings=3)
    assert not result.can_advance
    assert "3 open finding" in result.reason
    assert result.blocking_findings == 3


def test_challenge_pending():
    result = check_challenge_readiness(70, True, ChallengeStatus.PENDING)
    assert not result.can_advance
    assert "pending" in result.reason


def test_unknown_status_blocks():
    result = check_challenge_readiness(70, True, "weird_status")
    assert not result.can_advance
    assert "unknown" in result.reason


# ─── compute_readiness_with_challenge ────────────────────────────


def test_compute_work_in_progress():
    r = compute_readiness_with_challenge(
        work_complete=False, challenge_required=True, challenge_status=None,
    )
    assert r == 50


def test_compute_work_complete_challenge_required():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True, challenge_status=None,
    )
    assert r == WORK_COMPLETE


def test_compute_work_complete_no_challenge():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=False, challenge_status=None,
    )
    assert r == CHALLENGE_PASSED


def test_compute_challenge_passed():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.PASSED,
    )
    assert r == CHALLENGE_PASSED


def test_compute_challenge_waived():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.WAIVED,
    )
    assert r == CHALLENGE_PASSED


def test_compute_challenge_deferred():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.DEFERRED,
    )
    assert r == CHALLENGE_PASSED


def test_compute_challenge_failed():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.FAILED,
    )
    assert r == WORK_COMPLETE


def test_compute_review_passed():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.PASSED,
        review_passed=True,
    )
    assert r == PO_APPROVED


def test_compute_po_approved():
    r = compute_readiness_with_challenge(
        work_complete=True, challenge_required=True,
        challenge_status=ChallengeStatus.PASSED,
        review_passed=True, po_approved=True,
    )
    assert r == DONE


# ─── readiness_stage_label ───────────────────────────────────────


def test_label_in_progress():
    assert readiness_stage_label(50) == "in-progress"


def test_label_challenge_pending():
    assert readiness_stage_label(70) == "challenge-pending"


def test_label_challenge_passed():
    assert readiness_stage_label(80) == "challenge-passed"


def test_label_review_passed():
    assert readiness_stage_label(90) == "review-passed"


def test_label_po_review():
    assert readiness_stage_label(95) == "po-review"


def test_label_done():
    assert readiness_stage_label(100) == "done"


# ─── readiness_to_emoji ─────────────────────────────────────────


def test_emoji_working():
    assert readiness_to_emoji(50) == "[WORKING]"


def test_emoji_challenging():
    assert readiness_to_emoji(70) == "[CHALLENGING]"


def test_emoji_challenged():
    assert readiness_to_emoji(80) == "[CHALLENGED]"


def test_emoji_reviewed():
    assert readiness_to_emoji(90) == "[REVIEWED]"


def test_emoji_po():
    assert readiness_to_emoji(95) == "[PO]"


def test_emoji_done():
    assert readiness_to_emoji(100) == "[DONE]"