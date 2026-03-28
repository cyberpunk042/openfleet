"""Tests for plan quality validation."""

from fleet.core.plan_quality import assess_plan, format_plan_feedback


def test_empty_plan():
    a = assess_plan("")
    assert a.score == 0
    assert not a.acceptable


def test_short_plan():
    a = assess_plan("I'll do it")
    assert a.score < 30
    assert not a.acceptable


def test_good_plan():
    plan = """
    1. First, I'll read the existing code to understand the structure
    2. Then implement the PlaneClient with async httpx
    3. Write tests for each API endpoint
    4. Run pytest to verify everything passes
    I'll be careful about the authentication handling — if the API key
    format is different than expected, I'll need to check the docs.
    """
    a = assess_plan(plan, "story")
    assert a.good
    assert a.score >= 70


def test_plan_with_steps_only():
    plan = "1. Create module 2. Add functions 3. Write tests"
    a = assess_plan(plan)
    assert a.score >= 20  # Has steps but maybe weak on verification


def test_plan_with_verification():
    plan = "I will implement the feature. Then I'll run pytest to verify and check coverage."
    a = assess_plan(plan)
    assert a.score >= 35  # Has verification


def test_plan_with_risk_awareness():
    plan = """
    Step 1: Implement the client
    Step 2: Test it
    Risk: if the Plane API rate limits us, we might need retry logic.
    """
    a = assess_plan(plan, "story")
    assert a.score >= 60  # Has steps + risk


def test_format_feedback_good():
    a = assess_plan("1. Do X 2. Do Y 3. Test Z. Verify with pytest. Risk: might fail on auth.")
    feedback = format_plan_feedback(a)
    assert "Plan quality" in feedback


def test_format_feedback_poor():
    a = assess_plan("stuff")
    feedback = format_plan_feedback(a)
    assert "needs improvement" in feedback.lower() or "Issues" in feedback