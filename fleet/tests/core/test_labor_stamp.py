"""Tests for labor attribution — LaborStamp, DispatchRecord, confidence tiers."""

from fleet.core.labor_stamp import (
    LaborStamp,
    DispatchRecord,
    assemble_stamp,
    derive_confidence_tier,
)


# ─── Confidence Tier Derivation ───────────────────────────────────────


def test_claude_opus_is_expert():
    tier, reason = derive_confidence_tier("claude-code", "opus-4-6")
    assert tier == "expert"
    assert "cloud" in reason


def test_claude_sonnet_is_standard():
    tier, reason = derive_confidence_tier("claude-code", "sonnet-4-6")
    assert tier == "standard"
    assert "cloud" in reason


def test_localai_is_trainee():
    tier, reason = derive_confidence_tier("localai", "hermes-3b")
    assert tier == "trainee"
    assert "local" in reason
    assert "unvalidated" in reason


def test_openrouter_is_community():
    tier, reason = derive_confidence_tier("openrouter", "qwen3-8b")
    assert tier == "community"
    assert "free-tier" in reason


def test_direct_is_standard():
    tier, reason = derive_confidence_tier("direct", "")
    assert tier == "standard"
    assert "deterministic" in reason


def test_unknown_backend_is_community():
    tier, _ = derive_confidence_tier("unknown-backend", "unknown-model")
    assert tier == "community"


# ─── LaborStamp ──────────────────────────────────────────────────────


def test_stamp_auto_derives_tier():
    stamp = LaborStamp(backend="claude-code", model="opus-4-6")
    assert stamp.confidence_tier == "expert"
    assert stamp.confidence_reason != ""


def test_stamp_auto_sets_timestamp():
    stamp = LaborStamp()
    assert stamp.timestamp != ""


def test_stamp_short_label():
    stamp = LaborStamp(model="sonnet-4-6", confidence_tier="standard")
    assert stamp.short_label == "sonnet-4-6 \u00b7 standard"


def test_stamp_requires_challenge_for_trainee():
    stamp = LaborStamp(confidence_tier="trainee")
    assert stamp.requires_challenge is True


def test_stamp_no_challenge_for_expert():
    stamp = LaborStamp(confidence_tier="expert")
    assert stamp.requires_challenge is False


def test_stamp_to_dict_roundtrip():
    stamp = LaborStamp(
        agent_name="qa-engineer",
        backend="claude-code",
        model="sonnet-4-6",
        effort="medium",
        confidence_tier="standard",
    )
    d = stamp.to_dict()
    assert d["agent_name"] == "qa-engineer"
    assert d["backend"] == "claude-code"
    assert d["confidence_tier"] == "standard"

    restored = LaborStamp.from_dict(d)
    assert restored.agent_name == "qa-engineer"
    assert restored.backend == "claude-code"


# ─── DispatchRecord ──────────────────────────────────────────────────


def test_dispatch_record_auto_timestamp():
    record = DispatchRecord(
        task_id="abc12345", agent_name="software-engineer",
        backend="claude-code", model="sonnet",
        effort="medium", selection_reason="default",
        budget_mode="standard",
    )
    assert record.dispatched_at != ""


def test_dispatch_record_to_dict():
    record = DispatchRecord(
        task_id="abc12345", agent_name="architect",
        backend="claude-code", model="opus",
        effort="high", selection_reason="epic task",
        budget_mode="blitz", skills=["code-review"],
    )
    d = record.to_dict()
    assert d["model"] == "opus"
    assert d["budget_mode"] == "blitz"
    assert "code-review" in d["skills"]


# ─── Stamp Assembly ─────────────────────────────────────────────────


def test_assemble_stamp_from_dispatch():
    dispatch = DispatchRecord(
        task_id="abc12345", agent_name="software-engineer",
        backend="claude-code", model="sonnet-4-6",
        effort="medium", selection_reason="default",
        budget_mode="standard", skills=["git-ops"],
    )
    stamp = assemble_stamp(
        dispatch=dispatch,
        duration_seconds=120,
        estimated_tokens=5000,
        tools_called=["fleet_read_context", "fleet_commit"],
        session_type="fresh",
        iteration=1,
    )
    assert stamp.agent_name == "software-engineer"
    assert stamp.backend == "claude-code"
    assert stamp.model == "sonnet-4-6"
    assert stamp.confidence_tier == "standard"
    assert stamp.duration_seconds == 120
    assert stamp.estimated_tokens == 5000
    assert stamp.estimated_cost_usd > 0  # sonnet cost estimated
    assert "git-ops" in stamp.skills_used
    assert "fleet_commit" in stamp.tools_called
    assert stamp.budget_mode == "standard"


def test_assemble_stamp_localai_zero_cost():
    dispatch = DispatchRecord(
        task_id="abc12345", agent_name="software-engineer",
        backend="localai", model="hermes-3b",
        effort="low", selection_reason="heartbeat",
        budget_mode="survival",
    )
    stamp = assemble_stamp(dispatch=dispatch, estimated_tokens=1000)
    assert stamp.confidence_tier == "trainee"
    assert stamp.estimated_cost_usd == 0.0
    assert stamp.requires_challenge is True


def test_assemble_stamp_opus_cost_higher():
    dispatch_opus = DispatchRecord(
        task_id="abc12345", agent_name="architect",
        backend="claude-code", model="opus-4-6",
        effort="high", selection_reason="epic",
        budget_mode="blitz",
    )
    dispatch_sonnet = DispatchRecord(
        task_id="abc12345", agent_name="architect",
        backend="claude-code", model="sonnet-4-6",
        effort="high", selection_reason="epic",
        budget_mode="blitz",
    )
    stamp_opus = assemble_stamp(dispatch=dispatch_opus, estimated_tokens=10000)
    stamp_sonnet = assemble_stamp(dispatch=dispatch_sonnet, estimated_tokens=10000)
    assert stamp_opus.estimated_cost_usd > stamp_sonnet.estimated_cost_usd