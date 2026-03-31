"""Tests for confidence-aware review gates (M-LA06)."""

from fleet.core.review_gates import (
    ARCHITECT_REQUIRED_TIERS,
    CHALLENGE_REQUIRED_TIERS,
    ReviewGate,
    build_review_gates,
    gates_to_dicts,
    review_depth_label,
)


def _agent_names(gates: list[ReviewGate]) -> list[str]:
    return [g.agent for g in gates]


def _gate_types(gates: list[ReviewGate]) -> list[str]:
    return [g.gate_type for g in gates]


# ─── Standard Tier (minimal gates) ────────────────────────────────


def test_standard_tier_minimal():
    """Standard tier with no code = just fleet-ops."""
    gates = build_review_gates("task", has_code=False, confidence_tier="standard")
    assert _agent_names(gates) == ["fleet-ops"]


def test_standard_tier_with_code():
    """Standard tier with code = qa-engineer + fleet-ops."""
    gates = build_review_gates("task", has_code=True, confidence_tier="standard")
    assert "qa-engineer" in _agent_names(gates)
    assert gates[-1].agent == "fleet-ops"


def test_expert_tier_same_as_standard():
    """Expert tier has same review depth as standard."""
    gates = build_review_gates("task", has_code=False, confidence_tier="expert")
    assert _agent_names(gates) == ["fleet-ops"]


# ─── Trainee Tier (deep scrutiny) ─────────────────────────────────


def test_trainee_gets_challenge():
    """Trainee tier work gets adversarial challenge gate."""
    gates = build_review_gates("task", has_code=False, confidence_tier="trainee")
    types = _gate_types(gates)
    assert "challenge" in types
    assert "challenge-runner" in _agent_names(gates)


def test_trainee_gets_architect():
    """Trainee tier always requires architect review."""
    gates = build_review_gates("task", has_code=False, confidence_tier="trainee")
    assert "architect" in _agent_names(gates)


def test_trainee_full_chain():
    """Trainee tier: challenge-runner -> architect -> fleet-ops minimum."""
    gates = build_review_gates("task", has_code=False, confidence_tier="trainee")
    names = _agent_names(gates)
    assert len(gates) >= 3
    assert names[0] == "challenge-runner"
    assert "architect" in names
    assert names[-1] == "fleet-ops"


def test_trainee_with_code_adds_qa():
    """Trainee + code: challenge + architect + qa + fleet-ops."""
    gates = build_review_gates("task", has_code=True, confidence_tier="trainee")
    names = _agent_names(gates)
    assert "challenge-runner" in names
    assert "architect" in names
    assert "qa-engineer" in names
    assert names[-1] == "fleet-ops"


# ─── Community Tier (same as trainee) ─────────────────────────────


def test_community_gets_challenge():
    gates = build_review_gates("task", has_code=False, confidence_tier="community")
    assert "challenge-runner" in _agent_names(gates)


def test_community_gets_architect():
    gates = build_review_gates("task", has_code=False, confidence_tier="community")
    assert "architect" in _agent_names(gates)


# ─── Hybrid Tier (enhanced but no challenge) ──────────────────────


def test_hybrid_gets_architect_not_challenge():
    """Hybrid tier requires architect but not adversarial challenge."""
    gates = build_review_gates("task", has_code=False, confidence_tier="hybrid")
    names = _agent_names(gates)
    assert "architect" in names
    assert "challenge-runner" not in names


# ─── Budget Mode Interaction ──────────────────────────────────────


def test_frugal_skips_challenge():
    """Frugal mode disables challenges (they cost tokens)."""
    gates = build_review_gates(
        "task", has_code=False,
        confidence_tier="trainee", budget_mode="frugal",
    )
    assert "challenge-runner" not in _agent_names(gates)
    # Still requires architect
    assert "architect" in _agent_names(gates)


def test_survival_skips_challenge():
    """Survival mode also disables challenges."""
    gates = build_review_gates(
        "task", has_code=False,
        confidence_tier="trainee", budget_mode="survival",
    )
    assert "challenge-runner" not in _agent_names(gates)


def test_standard_budget_allows_challenge():
    """Standard budget mode allows challenges."""
    gates = build_review_gates(
        "task", has_code=False,
        confidence_tier="trainee", budget_mode="standard",
    )
    assert "challenge-runner" in _agent_names(gates)


# ─── Task Type Gates ──────────────────────────────────────────────


def test_epic_adds_architect():
    """Epic task type adds architect even for expert tier."""
    gates = build_review_gates("epic", has_code=False, confidence_tier="expert")
    assert "architect" in _agent_names(gates)


def test_blocker_adds_security():
    """Blocker task type adds devsecops-expert."""
    gates = build_review_gates("blocker", has_code=False, confidence_tier="standard")
    assert "devsecops-expert" in _agent_names(gates)


def test_no_duplicate_architect():
    """Trainee + epic should not duplicate architect gate."""
    gates = build_review_gates("epic", has_code=False, confidence_tier="trainee")
    architect_count = sum(1 for g in gates if g.agent == "architect")
    assert architect_count == 1


# ─── Serialization ────────────────────────────────────────────────


def test_gate_to_dict():
    gate = ReviewGate(agent="qa", gate_type="required", reason="test")
    d = gate.to_dict()
    assert d["agent"] == "qa"
    assert d["type"] == "required"
    assert d["status"] == "pending"


def test_gates_to_dicts():
    gates = build_review_gates("task", has_code=True, confidence_tier="trainee")
    dicts = gates_to_dicts(gates)
    assert len(dicts) == len(gates)
    assert all(isinstance(d, dict) for d in dicts)


# ─── Depth Labels ─────────────────────────────────────────────────


def test_depth_label_trainee():
    assert "adversarial" in review_depth_label("trainee")


def test_depth_label_hybrid():
    assert "enhanced" in review_depth_label("hybrid")


def test_depth_label_standard():
    assert "standard" in review_depth_label("standard")