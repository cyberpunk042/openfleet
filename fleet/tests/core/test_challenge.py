"""Tests for challenge loop data model (M-IV01)."""

from fleet.core.challenge import (
    ChallengeFinding,
    ChallengeRecord,
    ChallengeRound,
    ChallengeStatus,
    ChallengeType,
    FindingStatus,
    is_challenge_required,
    max_rounds_for_tier,
    select_challenge_type,
    select_challenger_agent,
)


# ─── Enums ─────────────────────────────────────────────────────────


def test_challenge_types():
    assert ChallengeType.AUTOMATED == "automated"
    assert ChallengeType.AGENT == "agent"
    assert ChallengeType.CROSS_MODEL == "cross-model"
    assert ChallengeType.SCENARIO == "scenario"


def test_challenge_statuses():
    assert ChallengeStatus.PENDING == "pending"
    assert ChallengeStatus.DEFERRED == "deferred"
    assert ChallengeStatus.WAIVED == "waived"


def test_finding_statuses():
    assert FindingStatus.OPEN == "open"
    assert FindingStatus.VERIFIED == "verified"
    assert FindingStatus.WONT_FIX == "wont_fix"


# ─── ChallengeFinding ─────────────────────────────────────────────


def test_finding_creation():
    f = ChallengeFinding(
        finding_id="f1", round_number=1,
        challenge_type="automated", category="edge_case",
        severity="major", description="Missing null check",
    )
    assert f.status == "open"
    assert f.timestamp > 0


def test_finding_to_dict():
    f = ChallengeFinding(
        finding_id="f1", round_number=1,
        challenge_type="agent", category="regression",
        severity="critical", description="Breaks existing API",
    )
    d = f.to_dict()
    assert d["finding_id"] == "f1"
    assert d["severity"] == "critical"
    assert d["status"] == "open"


# ─── ChallengeRound ───────────────────────────────────────────────


def test_round_starts_pending():
    r = ChallengeRound(round_number=1, challenge_type="automated", challenger="automated")
    assert r.status == "pending"
    assert not r.is_complete


def test_round_start():
    r = ChallengeRound(round_number=1, challenge_type="agent", challenger="qa-engineer")
    r.start()
    assert r.status == "in_progress"
    assert r.started_at > 0


def test_round_complete_passed():
    r = ChallengeRound(round_number=1, challenge_type="automated", challenger="automated")
    r.start()
    r.complete(passed=True)
    assert r.status == "passed"
    assert r.is_complete
    assert r.completed_at > 0


def test_round_complete_failed():
    r = ChallengeRound(round_number=1, challenge_type="agent", challenger="qa-engineer")
    r.start()
    r.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1,
        challenge_type="agent", category="edge_case",
        severity="major", description="Missing check",
    ))
    r.complete(passed=False)
    assert r.status == "failed"
    assert r.has_open_findings


def test_round_open_findings():
    r = ChallengeRound(round_number=1, challenge_type="automated", challenger="automated")
    f1 = ChallengeFinding(finding_id="f1", round_number=1, challenge_type="automated",
                          category="edge", severity="minor", description="x")
    f2 = ChallengeFinding(finding_id="f2", round_number=1, challenge_type="automated",
                          category="edge", severity="minor", description="y", status="verified")
    r.add_finding(f1)
    r.add_finding(f2)
    assert len(r.open_findings) == 1


def test_round_all_findings_resolved():
    r = ChallengeRound(round_number=1, challenge_type="automated", challenger="automated")
    f = ChallengeFinding(finding_id="f1", round_number=1, challenge_type="automated",
                         category="edge", severity="minor", description="x", status="verified")
    r.add_finding(f)
    assert r.all_findings_resolved


def test_round_to_dict():
    r = ChallengeRound(round_number=2, challenge_type="agent", challenger="architect")
    d = r.to_dict()
    assert d["round"] == 2
    assert d["challenger"] == "architect"


# ─── ChallengeRecord ──────────────────────────────────────────────


def test_record_starts_pending():
    rec = ChallengeRecord(task_id="t1")
    assert rec.status == "pending"
    assert rec.total_findings == 0


def test_record_start_round():
    rec = ChallengeRecord(task_id="t1")
    r = rec.start_round("automated", "automated")
    assert r.round_number == 1
    assert r.status == "in_progress"
    assert rec.current_round == 1


def test_record_multiple_rounds():
    rec = ChallengeRecord(task_id="t1", max_rounds=3)
    r1 = rec.start_round("automated", "automated")
    r1.complete(passed=False)
    r2 = rec.start_round("agent", "qa-engineer")
    r2.complete(passed=True)
    assert rec.current_round == 2
    assert rec.rounds_survived == 1


def test_record_can_add_round():
    rec = ChallengeRecord(task_id="t1", max_rounds=2)
    rec.start_round("automated", "automated")
    assert rec.can_add_round  # Round 1 of 2
    rec.start_round("agent", "qa")
    assert not rec.can_add_round  # Round 2 of 2


def test_record_challenge_types_faced():
    rec = ChallengeRecord(task_id="t1")
    rec.start_round("automated", "automated")
    rec.start_round("agent", "qa-engineer")
    rec.start_round("automated", "automated")
    assert rec.challenge_types_faced == ["automated", "agent"]


def test_record_to_stamp_fields():
    rec = ChallengeRecord(task_id="t1")
    r1 = rec.start_round("automated", "automated")
    r1.complete(passed=True)
    r2 = rec.start_round("agent", "qa")
    r2.complete(passed=True)
    fields = rec.to_stamp_fields()
    assert fields["challenge_rounds_survived"] == 2
    assert "automated" in fields["challenge_types_faced"]
    assert "agent" in fields["challenge_types_faced"]


def test_record_to_task_fields():
    rec = ChallengeRecord(task_id="t1")
    r = rec.start_round("automated", "automated")
    r.add_finding(ChallengeFinding(
        finding_id="f1", round_number=1,
        challenge_type="automated", category="edge",
        severity="minor", description="test",
    ))
    r.complete(passed=False)
    fields = rec.to_task_fields()
    assert fields["challenge_round"] == 1
    assert fields["challenge_status"] == "failed"
    assert len(fields["challenge_findings"]) == 1
    assert fields["challenge_type"] == "automated"


def test_record_status_passed():
    rec = ChallengeRecord(task_id="t1")
    r = rec.start_round("automated", "automated")
    r.complete(passed=True)
    assert rec.status == "passed"


def test_record_total_findings():
    rec = ChallengeRecord(task_id="t1")
    r1 = rec.start_round("automated", "automated")
    r1.add_finding(ChallengeFinding(finding_id="f1", round_number=1,
                                    challenge_type="automated", category="x",
                                    severity="minor", description="a"))
    r2 = rec.start_round("agent", "qa")
    r2.add_finding(ChallengeFinding(finding_id="f2", round_number=2,
                                    challenge_type="agent", category="y",
                                    severity="major", description="b"))
    r2.add_finding(ChallengeFinding(finding_id="f3", round_number=2,
                                    challenge_type="agent", category="z",
                                    severity="minor", description="c"))
    assert rec.total_findings == 3


# ─── Challenge Requirements ───────────────────────────────────────


def test_heartbeat_never_challenged():
    req, reason = is_challenge_required("heartbeat", 0, "standard", "standard")
    assert not req
    assert "heartbeat" in reason


def test_survival_disables_challenges():
    req, reason = is_challenge_required("story", 5, "trainee", "survival")
    assert not req


def test_blackout_disables_challenges():
    req, reason = is_challenge_required("story", 5, "trainee", "blackout")
    assert not req


def test_blocker_always_required():
    req, reason = is_challenge_required("blocker", 1, "expert", "standard")
    assert req


def test_trainee_always_required():
    req, reason = is_challenge_required("task", 1, "trainee", "standard")
    assert req


def test_community_always_required():
    req, reason = is_challenge_required("task", 1, "community", "standard")
    assert req


def test_trainee_frugal_deferred():
    req, reason = is_challenge_required("task", 1, "trainee", "frugal")
    assert not req
    assert "deferred" in reason


def test_bug_sp3_required():
    req, reason = is_challenge_required("bug", 3, "standard", "standard")
    assert req


def test_complex_story_required():
    req, reason = is_challenge_required("story", 5, "standard", "standard")
    assert req


def test_epic_always_required():
    req, reason = is_challenge_required("epic", 1, "standard", "standard")
    assert req


def test_simple_task_optional():
    req, reason = is_challenge_required("task", 1, "standard", "standard")
    assert not req


def test_docs_optional():
    req, reason = is_challenge_required("docs", 2, "standard", "standard")
    assert not req


# ─── Challenge Type Selection ─────────────────────────────────────


def test_bug_fix_gets_scenario():
    t = select_challenge_type("bug", 3, "standard", "standard", is_bug_fix=True)
    assert t == "scenario"


def test_economic_gets_automated():
    t = select_challenge_type("story", 5, "standard", "economic")
    assert t == "automated"


def test_trainee_blitz_gets_cross_model():
    t = select_challenge_type("task", 1, "trainee", "blitz")
    assert t == "cross-model"


def test_trainee_standard_gets_agent():
    t = select_challenge_type("task", 1, "trainee", "standard")
    assert t == "agent"


def test_complex_gets_agent():
    t = select_challenge_type("epic", 8, "standard", "standard")
    assert t == "agent"


def test_simple_gets_automated():
    t = select_challenge_type("task", 1, "standard", "standard")
    assert t == "automated"


# ─── Challenger Selection ─────────────────────────────────────────


def test_blocker_gets_devsecops():
    assert select_challenger_agent("blocker", "worker") == "devsecops-expert"


def test_epic_gets_architect():
    assert select_challenger_agent("epic", "worker") == "architect"


def test_default_gets_qa():
    assert select_challenger_agent("task", "worker") == "qa-engineer"


def test_qa_author_gets_software_engineer():
    assert select_challenger_agent("task", "qa-engineer") == "software-engineer"


# ─── Max Rounds by Tier ───────────────────────────────────────────


def test_expert_gets_1_round():
    assert max_rounds_for_tier("expert") == 1


def test_trainee_gets_3_rounds():
    assert max_rounds_for_tier("trainee") == 3


def test_standard_gets_2_rounds():
    assert max_rounds_for_tier("standard") == 2


def test_unknown_gets_2_rounds():
    assert max_rounds_for_tier("unknown") == 2