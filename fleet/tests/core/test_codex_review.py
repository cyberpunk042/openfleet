"""Tests for Codex adversarial review integration (M-BR06)."""

from fleet.core.codex_review import (
    CODEX_ADVERSARIAL_CMD,
    CODEX_REVIEW_CMD,
    CodexReviewRequest,
    CodexReviewResult,
    CodexReviewTracker,
    review_backend,
    review_command,
    should_trigger_review,
)


# ─── should_trigger_review ─────────────────────────────────────


def test_trigger_trainee_standard():
    yes, reason = should_trigger_review("trainee", "standard")
    assert yes
    assert "Codex plugin" in reason


def test_trigger_trainee_economic():
    yes, reason = should_trigger_review("trainee", "economic")
    assert yes
    assert "Codex plugin" in reason


def test_trigger_trainee_frugal():
    yes, reason = should_trigger_review("trainee", "frugal")
    assert yes
    assert "LocalAI" in reason
    assert "free" in reason


def test_trigger_trainee_survival():
    yes, reason = should_trigger_review("trainee", "survival")
    assert yes
    assert "LocalAI" in reason


def test_no_trigger_expert():
    yes, reason = should_trigger_review("expert", "standard")
    assert not yes
    assert "does not require" in reason


def test_no_trigger_standard_tier():
    yes, reason = should_trigger_review("standard", "standard")
    assert not yes


def test_no_trigger_blackout():
    yes, reason = should_trigger_review("trainee", "blackout")
    assert not yes
    assert "blackout" in reason


def test_trigger_force():
    yes, reason = should_trigger_review("expert", "blackout", force=True)
    assert yes
    assert "forced" in reason


def test_trigger_community():
    yes, _ = should_trigger_review("community", "standard")
    assert yes


def test_trigger_hybrid():
    yes, _ = should_trigger_review("hybrid", "blitz")
    assert yes


# ─── review_backend ───────────────────────────────────────────


def test_backend_standard():
    assert review_backend("standard") == "codex-plugin"


def test_backend_blitz():
    assert review_backend("blitz") == "codex-plugin"


def test_backend_frugal():
    assert review_backend("frugal") == "localai"


def test_backend_survival():
    assert review_backend("survival") == "localai"


# ─── review_command ────────────────────────────────────────────


def test_command_adversarial():
    assert review_command("standard", adversarial=True) == CODEX_ADVERSARIAL_CMD


def test_command_standard_review():
    assert review_command("standard", adversarial=False) == CODEX_REVIEW_CMD


def test_command_frugal_returns_empty():
    assert review_command("frugal") == ""


# ─── CodexReviewRequest ───────────────────────────────────────


def test_request_codex_backend():
    req = CodexReviewRequest(
        pr_number=42, repo="user/repo",
        confidence_tier="trainee", budget_mode="standard",
    )
    assert req.backend == "codex-plugin"
    assert req.uses_codex
    assert req.command == CODEX_ADVERSARIAL_CMD


def test_request_localai_backend():
    req = CodexReviewRequest(
        pr_number=42, repo="user/repo",
        confidence_tier="trainee", budget_mode="frugal",
    )
    assert req.backend == "localai"
    assert not req.uses_codex
    assert req.command == ""


def test_request_to_agent_instruction_codex():
    req = CodexReviewRequest(
        pr_number=42, repo="user/repo",
        confidence_tier="trainee", budget_mode="standard",
        files_changed=["fleet/core/router.py"],
    )
    instruction = req.to_agent_instruction()
    assert "/codex:adversarial-review" in instruction
    assert "#42" in instruction
    assert "router.py" in instruction


def test_request_to_agent_instruction_localai():
    req = CodexReviewRequest(
        pr_number=42, repo="user/repo",
        confidence_tier="trainee", budget_mode="frugal",
    )
    instruction = req.to_agent_instruction()
    assert "local challenge system" in instruction
    assert "/codex:" not in instruction


def test_request_standard_review():
    req = CodexReviewRequest(
        pr_number=10, repo="user/repo",
        confidence_tier="trainee", budget_mode="standard",
        adversarial=False,
    )
    assert req.command == CODEX_REVIEW_CMD


def test_request_to_dict():
    req = CodexReviewRequest(
        pr_number=42, repo="user/repo",
        confidence_tier="trainee", budget_mode="standard",
        files_changed=["a.py"],
    )
    d = req.to_dict()
    assert d["pr_number"] == 42
    assert d["backend"] == "codex-plugin"
    assert d["command"] == CODEX_ADVERSARIAL_CMD


# ─── CodexReviewResult ─────────────────────────────────────────


def test_result_passed():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin", raw_output="LGTM",
        approved=True,
    )
    assert r.passed


def test_result_failed():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin", raw_output="Issues found",
        approved=False,
    )
    assert not r.passed


def test_result_error():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin", raw_output="",
        error="Codex not authenticated",
    )
    assert not r.passed


def test_result_to_pr_comment():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin",
        raw_output="Found SQL injection in query.py:45",
        issues_found=1,
        severity_counts={"high": 1},
        approved=False,
    )
    comment = r.to_pr_comment()
    assert "Adversarial Review" in comment
    assert "codex-plugin" in comment
    assert "CHANGES REQUESTED" in comment
    assert "SQL injection" in comment
    assert "high: 1" in comment


def test_result_to_pr_comment_approved():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin",
        raw_output="No issues found",
        approved=True,
    )
    comment = r.to_pr_comment()
    assert "APPROVED" in comment


def test_result_to_dict():
    r = CodexReviewResult(
        pr_number=42, repo="user/repo",
        review_backend="codex-plugin", raw_output="ok",
        issues_found=2, approved=False, duration_seconds=5.5,
    )
    d = r.to_dict()
    assert d["pr_number"] == 42
    assert d["issues_found"] == 2
    assert d["passed"] is False
    assert d["duration_seconds"] == 5.5


# ─── CodexReviewTracker ───────────────────────────────────────


def test_tracker_record():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin",
        raw_output="ok", approved=True,
    ))
    assert t.total_reviews == 1


def test_tracker_approval_rate():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin",
        raw_output="ok", approved=True,
    ))
    t.record(CodexReviewResult(
        pr_number=2, repo="r", review_backend="codex-plugin",
        raw_output="bad", approved=False,
    ))
    assert t.approval_rate == 0.5


def test_tracker_avg_issues():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin",
        raw_output="ok", issues_found=2,
    ))
    t.record(CodexReviewResult(
        pr_number=2, repo="r", review_backend="codex-plugin",
        raw_output="ok", issues_found=4,
    ))
    assert t.avg_issues == 3.0


def test_tracker_by_backend():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin", raw_output="",
    ))
    t.record(CodexReviewResult(
        pr_number=2, repo="r", review_backend="localai", raw_output="",
    ))
    t.record(CodexReviewResult(
        pr_number=3, repo="r", review_backend="codex-plugin", raw_output="",
    ))
    by = t.by_backend()
    assert by["codex-plugin"] == 2
    assert by["localai"] == 1


def test_tracker_empty():
    t = CodexReviewTracker()
    assert t.approval_rate == 0.0
    assert t.avg_issues == 0.0
    assert t.by_backend() == {}


def test_tracker_max_results():
    t = CodexReviewTracker(max_results=3)
    for i in range(5):
        t.record(CodexReviewResult(
            pr_number=i, repo="r", review_backend="codex-plugin", raw_output="",
        ))
    assert t.total_reviews == 3


def test_tracker_summary():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin",
        raw_output="ok", approved=True, issues_found=1,
    ))
    s = t.summary()
    assert s["total_reviews"] == 1
    assert s["approval_rate"] == 1.0
    assert s["avg_issues_found"] == 1.0


def test_tracker_format_report():
    t = CodexReviewTracker()
    t.record(CodexReviewResult(
        pr_number=1, repo="r", review_backend="codex-plugin",
        raw_output="ok", approved=True,
    ))
    report = t.format_report()
    assert "Codex Adversarial Review Report" in report
    assert "codex-plugin" in report