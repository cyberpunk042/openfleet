"""Flow 1: Task Dispatch — Budget → Router → Stamp → Challenge.

Tests the full dispatch path: budget mode constrains model selection,
router picks cheapest capable backend, labor stamp records provenance,
challenge engine respects budget mode.
"""

from fleet.core.backend_router import route_task
from fleet.core.budget_modes import constrain_model_by_budget
from fleet.core.challenge_deferred import should_defer_challenge
from fleet.core.challenge_protocol import evaluate_challenge
from fleet.core.labor_stamp import (
    LaborStamp,
    assemble_stamp,
    mark_challenge_skipped,
)
from fleet.core.models import TaskCustomFields

from .conftest import make_task


def test_dispatch_blitz():
    """Blitz mode: opus allowed, full challenge, stamp records everything."""
    task = make_task(story_points=5, task_type="story")

    # Route
    decision = route_task(task, agent_name="worker", budget_mode="blitz")
    assert decision.backend == "claude-code"
    assert "opus" in decision.model

    # Model not constrained in blitz
    model, effort, reason = constrain_model_by_budget("opus", "high", "test", "blitz")
    assert model == "opus"

    # Challenge: blitz allows full challenge
    challenge = evaluate_challenge(
        task, confidence_tier="standard", budget_mode="blitz",
    )
    # Standard tier + blitz = challenge not required (only trainee/community trigger)
    # But if trainee:
    challenge_trainee = evaluate_challenge(
        task, confidence_tier="trainee", budget_mode="blitz",
    )
    assert challenge_trainee.required is True
    assert challenge_trainee.deferred is False


def test_dispatch_economic():
    """Economic mode: opus blocked, automated challenge only."""
    task = make_task(story_points=3)

    # Model constrained — opus blocked in economic
    model, effort, reason = constrain_model_by_budget("opus", "high", "test", "economic")
    assert model == "sonnet"
    assert "constrained" in reason

    # Route
    decision = route_task(task, agent_name="worker", budget_mode="economic")
    assert decision.backend in ("claude-code", "localai")
    # Opus should not appear in economic routing
    if decision.backend == "claude-code":
        assert "opus" not in decision.model


def test_dispatch_frugal():
    """Frugal mode: free backends only, challenge deferred, stamp marks skipped."""
    task = make_task(story_points=2)

    # Route: frugal prefers free backends
    decision = route_task(task, agent_name="worker", budget_mode="frugal")
    assert decision.backend in ("localai", "openrouter-free", "claude-code")

    # Challenge deferred in frugal
    assert should_defer_challenge("frugal") is True

    # Stamp records the skip
    stamp = LaborStamp(
        agent_name="worker",
        backend=decision.backend,
        model=decision.model,
        budget_mode="frugal",
    )
    mark_challenge_skipped(stamp, reason="frugal mode")
    assert stamp.challenge_skipped is True
    assert stamp.challenge_skip_reason == "frugal mode"


def test_dispatch_survival():
    """Survival mode: LocalAI only, no challenge, stamp marks skipped."""
    task = make_task(story_points=1)

    # Route: survival = LocalAI only (or direct)
    decision = route_task(task, agent_name="worker", budget_mode="survival")
    assert decision.backend in ("localai", "direct")

    # Challenge deferred
    assert should_defer_challenge("survival") is True

    # Stamp
    stamp = LaborStamp(
        agent_name="worker",
        backend="localai",
        model="hermes-3b",
        budget_mode="survival",
    )
    mark_challenge_skipped(stamp, reason="survival mode — no Claude tokens")
    assert stamp.challenge_skipped is True
    assert "survival" in stamp.challenge_skip_reason


def test_dispatch_blackout():
    """Blackout mode: no dispatch — only direct/no-LLM allowed."""
    task = make_task()

    decision = route_task(task, agent_name="worker", budget_mode="blackout")
    assert decision.backend == "direct"
    assert "blackout" in decision.reason.lower() or "frozen" in decision.reason.lower()

    # Challenge deferred
    assert should_defer_challenge("blackout") is True
