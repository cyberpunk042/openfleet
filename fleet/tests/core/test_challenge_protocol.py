"""Tests for agent challenge protocol (M-IV03)."""

from fleet.core.challenge import (
    ChallengeRecord,
    ChallengeRound,
    ChallengeStatus,
    ChallengeType,
    ChallengeFinding,
)
from fleet.core.challenge_automated import AutomatedChallenge
from fleet.core.challenge_protocol import (
    ChallengeContext,
    ChallengeDecision,
    RoundOutcome,
    apply_challenge_to_task,
    build_challenge_context,
    continue_challenge,
    evaluate_challenge,
    evaluate_round_outcome,
    process_agent_findings,
    process_automated_findings,
    start_challenge,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus


# ─── Helpers ──────────────────────────────────────────────────────


def _task(
    sp: int = 3,
    task_type: str = "task",
    agent_name: str = "worker",
    requirement: str = "",
    confidence: str = "standard",
) -> Task:
    return Task(
        id="t1", board_id="b1", title="Test Task", status=TaskStatus.INBOX,
        custom_fields=TaskCustomFields(
            story_points=sp,
            task_type=task_type,
            agent_name=agent_name,
            requirement_verbatim=requirement,
            labor_confidence=confidence,
        ),
    )


SAMPLE_DIFF = """\
--- a/fleet/core/router.py
+++ b/fleet/core/router.py
@@ -10,6 +10,9 @@
+    if complexity >= 8:
+        return "opus"
+    elif complexity is None:
+        return "sonnet"
"""


# ─── ChallengeDecision ───────────────────────────────────────────


def test_decision_automated_type():
    d = ChallengeDecision(
        required=True, reason="test",
        challenge_type="automated", challenger="automated",
    )
    assert d.is_automated
    assert not d.is_agent


def test_decision_agent_type():
    d = ChallengeDecision(
        required=True, reason="test",
        challenge_type="agent", challenger="qa-engineer",
    )
    assert d.is_agent
    assert not d.is_automated


def test_decision_to_dict():
    d = ChallengeDecision(
        required=True, reason="test", challenge_type="agent",
        challenger="qa-engineer", max_rounds=3, deferred=False,
    )
    result = d.to_dict()
    assert result["required"] is True
    assert result["challenger"] == "qa-engineer"
    assert result["deferred"] is False


# ─── evaluate_challenge ──────────────────────────────────────────


def test_evaluate_heartbeat_not_required():
    task = _task(task_type="heartbeat")
    decision = evaluate_challenge(task)
    assert not decision.required
    assert "heartbeat" in decision.reason


def test_evaluate_blocker_always_required():
    task = _task(task_type="blocker", sp=1)
    decision = evaluate_challenge(task)
    assert decision.required
    assert decision.challenger == "devsecops-expert"


def test_evaluate_trainee_gets_agent_challenge():
    task = _task(task_type="task", sp=1)
    decision = evaluate_challenge(task, confidence_tier="trainee")
    assert decision.required
    assert decision.challenge_type == ChallengeType.AGENT
    assert decision.max_rounds == 3


def test_evaluate_bug_fix_gets_scenario():
    task = _task(task_type="bug", sp=3)
    decision = evaluate_challenge(task, is_bug_fix=True)
    assert decision.required
    assert decision.challenge_type == ChallengeType.SCENARIO


def test_evaluate_economic_gets_automated():
    task = _task(task_type="story", sp=5)
    decision = evaluate_challenge(task, budget_mode="economic")
    assert decision.required
    assert decision.challenge_type == ChallengeType.AUTOMATED
    assert decision.challenger == "automated"


def test_evaluate_simple_task_not_required():
    task = _task(task_type="task", sp=1)
    decision = evaluate_challenge(task)
    assert not decision.required


def test_evaluate_frugal_trainee_deferred():
    task = _task(task_type="task", sp=1)
    decision = evaluate_challenge(task, confidence_tier="trainee", budget_mode="frugal")
    assert not decision.required
    assert decision.deferred


def test_evaluate_epic_gets_agent():
    task = _task(task_type="epic", sp=8)
    decision = evaluate_challenge(task)
    assert decision.required
    assert decision.challenge_type == ChallengeType.AGENT
    assert decision.challenger == "architect"


def test_evaluate_qa_author_gets_different_challenger():
    task = _task(task_type="task", sp=1)
    decision = evaluate_challenge(
        task, confidence_tier="trainee", author_agent="qa-engineer",
    )
    assert decision.challenger == "software-engineer"


# ─── ChallengeContext ────────────────────────────────────────────


def test_build_context_from_task():
    task = _task(
        task_type="story", sp=5, agent_name="dev-agent",
        requirement="Must handle null values gracefully",
    )
    ctx = build_challenge_context(task, SAMPLE_DIFF, author_summary="Added null check")
    assert ctx.task_id == "t1"
    assert ctx.requirement_verbatim == "Must handle null values gracefully"
    assert ctx.author_agent == "dev-agent"
    assert "router.py" in ctx.files_changed[0]


def test_context_prompt_contains_sections():
    ctx = ChallengeContext(
        task_id="t1", task_type="story", task_title="Test",
        requirement_verbatim="Must work", author_agent="dev",
        diff=SAMPLE_DIFF, author_summary="Did the thing",
        pr_url="https://github.com/org/repo/pull/1",
        files_changed=["fleet/core/router.py"],
    )
    prompt = ctx.to_prompt()
    assert "# Challenge Assignment" in prompt
    assert "Must work" in prompt
    assert "Did the thing" in prompt
    assert "Find flaws" in prompt
    assert "fleet/core/router.py" in prompt
    assert "https://github.com/org/repo/pull/1" in prompt


def test_context_prompt_with_previous_findings():
    ctx = ChallengeContext(
        task_id="t1", task_type="task", task_title="Fix",
        requirement_verbatim="Fix the bug", author_agent="dev",
        diff="", previous_findings=[
            {"status": "addressed", "description": "Missing null check"},
        ],
    )
    prompt = ctx.to_prompt()
    assert "Previous Findings" in prompt
    assert "Missing null check" in prompt


def test_context_prompt_no_requirement():
    ctx = ChallengeContext(
        task_id="t1", task_type="task", task_title="Test",
        requirement_verbatim="", author_agent="dev", diff="",
    )
    prompt = ctx.to_prompt()
    assert "no verbatim requirement recorded" in prompt


# ─── start_challenge ─────────────────────────────────────────────


def test_start_automated_challenge():
    task = _task(task_type="story", sp=5)
    decision = ChallengeDecision(
        required=True, reason="test",
        challenge_type="automated", challenger="automated", max_rounds=2,
    )
    record, challenges = start_challenge(task, decision, diff=SAMPLE_DIFF)
    assert isinstance(record, ChallengeRecord)
    assert record.current_round == 1
    assert isinstance(challenges, list)
    assert all(isinstance(c, AutomatedChallenge) for c in challenges)


def test_start_agent_challenge():
    task = _task(task_type="epic", sp=8, requirement="Build the thing")
    decision = ChallengeDecision(
        required=True, reason="test",
        challenge_type="agent", challenger="architect", max_rounds=2,
    )
    record, context = start_challenge(
        task, decision, diff=SAMPLE_DIFF, author_summary="Built it",
    )
    assert isinstance(context, ChallengeContext)
    assert context.round_number == 1
    assert record.rounds[0].challenger == "architect"


# ─── continue_challenge ──────────────────────────────────────────


def test_continue_after_failed_round():
    task = _task()
    record = ChallengeRecord(task_id="t1", max_rounds=3)
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1-1", round_number=1,
        challenge_type="agent", category="edge_case",
        severity="major", description="Missing check",
    ))
    r1.complete(passed=False)

    result = continue_challenge(record, task, diff=SAMPLE_DIFF)
    assert isinstance(result, ChallengeContext)
    assert record.current_round == 2
    assert len(result.previous_findings) == 1


def test_continue_returns_none_at_max_rounds():
    task = _task()
    record = ChallengeRecord(task_id="t1", max_rounds=1)
    r1 = record.start_round("automated", "automated")
    r1.complete(passed=False)

    result = continue_challenge(record, task)
    assert result is None


def test_continue_returns_none_after_pass():
    task = _task()
    record = ChallengeRecord(task_id="t1", max_rounds=3)
    r1 = record.start_round("automated", "automated")
    r1.complete(passed=True)

    result = continue_challenge(record, task)
    assert result is None


# ─── process_automated_findings ──────────────────────────────────


def test_process_all_passed():
    record = ChallengeRecord(task_id="t1")
    record.start_round("automated", "automated")
    challenges = [
        AutomatedChallenge("regression", "Run tests", "pytest", "critical"),
        AutomatedChallenge("edge_case", "Boundary", "unit test", "major"),
    ]
    completed = process_automated_findings(record, challenges, [True, True])
    assert completed.status == ChallengeStatus.PASSED
    assert len(completed.findings) == 0


def test_process_some_failed():
    record = ChallengeRecord(task_id="t1")
    record.start_round("automated", "automated")
    challenges = [
        AutomatedChallenge("regression", "Run tests", "pytest", "critical"),
        AutomatedChallenge("edge_case", "Boundary", "unit test", "major"),
    ]
    completed = process_automated_findings(record, challenges, [True, False])
    assert completed.status == ChallengeStatus.FAILED
    assert len(completed.findings) == 1
    assert completed.findings[0].finding_id == "f1-1"
    assert completed.findings[0].severity == "major"


def test_process_all_failed():
    record = ChallengeRecord(task_id="t1")
    record.start_round("automated", "automated")
    challenges = [
        AutomatedChallenge("regression", "Run tests", "pytest", "critical"),
        AutomatedChallenge("edge_case", "Boundary", "unit test", "major"),
    ]
    completed = process_automated_findings(record, challenges, [False, False])
    assert completed.status == ChallengeStatus.FAILED
    assert len(completed.findings) == 2


# ─── process_agent_findings ──────────────────────────────────────


def test_process_agent_no_findings():
    record = ChallengeRecord(task_id="t1")
    record.start_round("agent", "qa-engineer")
    completed = process_agent_findings(record, [])
    assert completed.status == ChallengeStatus.PASSED
    assert len(completed.findings) == 0


def test_process_agent_with_findings():
    record = ChallengeRecord(task_id="t1")
    record.start_round("agent", "architect")
    findings = [
        {"category": "logic_error", "severity": "critical",
         "description": "Race condition in handler", "evidence": "See line 42"},
        {"category": "test_gap", "severity": "minor",
         "description": "No test for error path"},
    ]
    completed = process_agent_findings(record, findings)
    assert completed.status == ChallengeStatus.FAILED
    assert len(completed.findings) == 2
    assert completed.findings[0].finding_id == "f1-1"
    assert completed.findings[0].severity == "critical"
    assert completed.findings[1].finding_id == "f1-2"


# ─── evaluate_round_outcome ─────────────────────────────────────


def test_outcome_passed():
    record = ChallengeRecord(task_id="t1", max_rounds=2)
    r1 = record.start_round("automated", "automated")
    r1.complete(passed=True)
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "passed"
    assert outcome.can_advance
    assert not outcome.needs_rework


def test_outcome_rechallenge():
    record = ChallengeRecord(task_id="t1", max_rounds=3)
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1, challenge_type="agent",
        category="edge", severity="major", description="Issue",
    ))
    r1.complete(passed=False)
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "rechallenge"
    assert outcome.needs_rework
    assert not outcome.can_advance
    assert outcome.open_findings == 1


def test_outcome_escalate_max_rounds():
    record = ChallengeRecord(task_id="t1", max_rounds=1)
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1, challenge_type="agent",
        category="edge", severity="major", description="Issue",
    ))
    r1.complete(passed=False)
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "escalate"
    assert "max rounds" in outcome.reason


def test_outcome_escalate_critical_at_max():
    record = ChallengeRecord(task_id="t1", max_rounds=1)
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1, challenge_type="agent",
        category="security", severity="critical", description="SQL injection",
    ))
    r1.complete(passed=False)
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "escalate"
    assert "critical" in outcome.reason


def test_outcome_rechallenge_critical_with_rounds_left():
    record = ChallengeRecord(task_id="t1", max_rounds=3)
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1, challenge_type="agent",
        category="security", severity="critical", description="SQL injection",
    ))
    r1.complete(passed=False)
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "rechallenge"


def test_outcome_no_rounds():
    record = ChallengeRecord(task_id="t1")
    outcome = evaluate_round_outcome(record)
    assert outcome.action == "passed"


def test_outcome_to_dict():
    outcome = RoundOutcome(
        action="rechallenge", reason="test",
        findings_count=2, open_findings=1,
        rounds_completed=1, max_rounds=3,
    )
    d = outcome.to_dict()
    assert d["action"] == "rechallenge"
    assert d["open_findings"] == 1


# ─── apply_challenge_to_task ─────────────────────────────────────


def test_apply_passed_challenge():
    record = ChallengeRecord(task_id="t1")
    r1 = record.start_round("automated", "automated")
    r1.complete(passed=True)
    outcome = RoundOutcome(action="passed", reason="survived")
    fields = apply_challenge_to_task(record, outcome)
    assert fields["challenge_status"] == ChallengeStatus.PASSED
    assert fields["challenge_round"] == 1


def test_apply_failed_challenge():
    record = ChallengeRecord(task_id="t1")
    r1 = record.start_round("agent", "qa-engineer")
    r1.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1, challenge_type="agent",
        category="edge", severity="major", description="Issue",
    ))
    r1.complete(passed=False)
    outcome = RoundOutcome(action="rechallenge", reason="rework needed")
    fields = apply_challenge_to_task(record, outcome)
    assert fields["challenge_status"] == ChallengeStatus.FAILED
    assert fields["challenge_challenger"] == "qa-engineer"
    assert len(fields["challenge_findings"]) == 1


# ─── Full Protocol Flow ─────────────────────────────────────────


def test_full_automated_flow():
    """End-to-end: evaluate → start → process → outcome → apply."""
    task = _task(task_type="story", sp=5)
    decision = evaluate_challenge(task, budget_mode="economic")
    assert decision.required
    assert decision.is_automated

    record, challenges = start_challenge(task, decision, diff=SAMPLE_DIFF)
    assert len(challenges) >= 1

    # Simulate all passing
    results = [True] * len(challenges)
    completed = process_automated_findings(record, challenges, results)
    assert completed.status == ChallengeStatus.PASSED

    outcome = evaluate_round_outcome(record)
    assert outcome.can_advance

    fields = apply_challenge_to_task(record, outcome)
    assert fields["challenge_status"] == ChallengeStatus.PASSED


def test_full_agent_flow_with_rework():
    """End-to-end: evaluate → start → findings → rework → re-challenge → pass."""
    task = _task(task_type="epic", sp=8, requirement="Build it right")
    decision = evaluate_challenge(task, confidence_tier="standard")
    assert decision.required
    assert decision.is_agent

    # Round 1: start and receive findings
    record, context = start_challenge(
        task, decision, diff=SAMPLE_DIFF, author_summary="Initial impl",
    )
    assert isinstance(context, ChallengeContext)
    assert "Build it right" in context.requirement_verbatim

    findings = [
        {"category": "edge_case", "severity": "major",
         "description": "Missing null guard", "evidence": "line 12"},
    ]
    r1 = process_agent_findings(record, findings)
    assert r1.status == ChallengeStatus.FAILED

    outcome1 = evaluate_round_outcome(record)
    assert outcome1.action == "rechallenge"

    # Round 2: author re-works, re-challenge
    ctx2 = continue_challenge(record, task, diff=SAMPLE_DIFF, author_summary="Fixed null")
    assert isinstance(ctx2, ChallengeContext)
    assert ctx2.round_number == 2
    assert len(ctx2.previous_findings) == 1

    # Round 2: no findings this time
    r2 = process_agent_findings(record, [])
    assert r2.status == ChallengeStatus.PASSED

    outcome2 = evaluate_round_outcome(record)
    assert outcome2.can_advance
    assert record.rounds_survived == 1

    fields = apply_challenge_to_task(record, outcome2)
    assert fields["challenge_status"] == ChallengeStatus.PASSED
    assert fields["challenge_round"] == 2