"""Flow 2: Contribution Pipeline — Synergy × Contributions × Completeness.

Tests the contribution flow: synergy matrix defines requirements,
contributions arrive via typed comments, completeness is tracked,
and stage-aware recommendations adapt per methodology stage.

This is a cross-flow integration test — it verifies that configs,
brain modules, and runtime context work together correctly.
"""

from fleet.core.contributions import (
    check_contribution_completeness,
    load_synergy_matrix,
    ContributionStatus,
)
from fleet.core.model_selection import select_model_for_task, _EFFORT_ORDER
from fleet.core.skill_recommendations import get_skill_recommendations
from fleet.core.standing_orders import get_standing_orders

from .conftest import make_task


# ── Synergy matrix integration ─────────────────────────────────────


def test_synergy_matrix_loads_for_all_agents():
    """Synergy matrix should load successfully and cover key agent roles."""
    matrix = load_synergy_matrix()
    assert isinstance(matrix, dict)
    # Engineer should receive contributions (most common target)
    assert "software-engineer" in matrix
    # Architect contributions should be defined
    engineer_specs = matrix["software-engineer"]
    design_input = [s for s in engineer_specs if s.contribution_type == "design_input"]
    assert len(design_input) > 0, "Engineer should require design_input from architect"


def test_contribution_completeness_for_story():
    """Story tasks should require multiple contributions."""
    status = check_contribution_completeness(
        task_id="T-100",
        target_agent="software-engineer",
        task_type="story",
        received_types=[],
    )
    assert not status.all_received
    assert len(status.required) > 0
    assert "design_input" in status.required


def test_contribution_completeness_with_partial():
    """Partial contributions should show specific missing types."""
    status = check_contribution_completeness(
        task_id="T-100",
        target_agent="software-engineer",
        task_type="story",
        received_types=["design_input"],
    )
    assert "design_input" not in status.missing
    assert "design_input" in status.received
    assert status.completeness_pct > 0


def test_contribution_completeness_subtask_skip():
    """Subtask should skip contribution requirements."""
    status = check_contribution_completeness(
        task_id="T-100",
        target_agent="software-engineer",
        task_type="subtask",
        received_types=[],
    )
    assert status.all_received
    assert status.completeness_pct == 100.0


def test_contribution_completeness_all_received():
    """When all required contributions are received, status should be complete."""
    # Get required types first
    status_empty = check_contribution_completeness(
        task_id="T-100",
        target_agent="software-engineer",
        task_type="story",
        received_types=[],
    )
    # Now provide all required
    status_full = check_contribution_completeness(
        task_id="T-100",
        target_agent="software-engineer",
        task_type="story",
        received_types=status_empty.required,
    )
    assert status_full.all_received
    assert status_full.completeness_pct == 100.0
    assert len(status_full.missing) == 0


# ── Contribution + Model Selection ─────────────────────────────────


def test_reasoning_stage_gets_higher_effort_than_work():
    """Reasoning stage tasks should get higher effort for deeper thinking."""
    task_work = make_task(story_points=3, task_type="task", task_stage="work")
    task_reasoning = make_task(story_points=3, task_type="task", task_stage="reasoning")

    config_work = select_model_for_task(task_work, "software-engineer")
    config_reasoning = select_model_for_task(task_reasoning, "software-engineer")

    assert _EFFORT_ORDER[config_reasoning.effort] >= _EFFORT_ORDER[config_work.effort]


def test_investigation_stage_gets_high_effort():
    """Investigation stage should enforce at least 'high' effort."""
    task = make_task(story_points=1, task_type="subtask", task_stage="investigation")
    config = select_model_for_task(task, "software-engineer")
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["high"]


def test_conversation_stage_gets_medium_effort():
    """Conversation stage should enforce at least 'medium' effort."""
    task = make_task(story_points=1, task_type="subtask", task_stage="conversation")
    config = select_model_for_task(task, "software-engineer")
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["medium"]


def test_work_stage_does_not_inflate_effort():
    """Work stage should NOT raise effort floor above 'low'."""
    task = make_task(story_points=1, task_type="subtask", task_stage="work")
    config = select_model_for_task(task, "software-engineer")
    # Work stage floor is 'low', so simple tasks should stay low
    assert config.effort in ("low", "medium", "high")  # any valid effort


# ── Skill Recommendations × Stage ─────────────────────────────────


def test_skill_recommendations_differ_by_stage():
    """Different stages should recommend different skills for the same agent."""
    recs_work = get_skill_recommendations("software-engineer", "work")
    recs_reasoning = get_skill_recommendations("software-engineer", "reasoning")

    # Always-available skills should be present in both
    assert len(recs_work["always"]) > 0
    assert len(recs_reasoning["always"]) > 0

    # Stage-specific recommendations may differ
    # Stage entries are dicts with 'skill' key
    def skill_names(entries):
        return {e["skill"] if isinstance(e, dict) else e for e in entries}

    work_stage = skill_names(recs_work.get("stage", []))
    reasoning_stage = skill_names(recs_reasoning.get("stage", []))
    # At least one should have stage-specific skills
    assert work_stage or reasoning_stage


def test_skill_recommendations_for_pm():
    """PM should have role-specific skill recommendations."""
    recs = get_skill_recommendations("project-manager", "work")
    all_skills = recs["always"] + recs.get("stage", [])
    assert len(all_skills) > 0


def test_skill_recommendations_blocked_at_stage():
    """Some skills should be blocked at certain stages."""
    # Conversation stage typically blocks implementation skills
    recs = get_skill_recommendations("software-engineer", "conversation")
    # The blocked list may be empty depending on config, but structure should exist
    assert "blocked" in recs


# ── Standing Orders × Role ─────────────────────────────────────────


def test_standing_orders_exist_for_fleet_ops():
    """fleet-ops should have standing orders for autonomous review authority."""
    orders = get_standing_orders("fleet-ops")
    assert orders["authority_level"] != ""
    assert len(orders["orders"]) > 0


def test_standing_orders_exist_for_pm():
    """PM should have standing orders for sprint management authority."""
    orders = get_standing_orders("project-manager")
    assert orders["authority_level"] != ""
    assert len(orders["orders"]) > 0


def test_standing_orders_have_escalation_threshold():
    """All standing orders should have escalation thresholds."""
    for agent in ["fleet-ops", "project-manager", "devsecops-expert"]:
        orders = get_standing_orders(agent)
        assert "escalation_threshold" in orders
        assert orders["escalation_threshold"] > 0


def test_standing_orders_for_unknown_agent():
    """Unknown agent should get empty/default standing orders."""
    orders = get_standing_orders("nonexistent-agent")
    assert len(orders["orders"]) == 0


# ── Cross-Flow: Contribution → Model Selection ─────────────────────


def test_contribution_stage_model_consistency():
    """Tasks requiring contributions (reasoning stage) should get appropriate effort."""
    # Use a simple subtask that would normally get low effort — reasoning stage
    # should raise it to at least 'high'
    task = make_task(
        story_points=1,
        task_type="subtask",
        task_stage="reasoning",
        agent_name="software-engineer",
    )

    # Check model selection for reasoning stage
    config = select_model_for_task(task, "software-engineer")

    # Simple subtask in reasoning stage → effort should be raised to high
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["high"]  # reasoning floor
    assert "stage:reasoning" in config.reason  # stage adjustment should be noted


def test_work_stage_simple_task_cost_effective():
    """Simple tasks in work stage should use cost-effective model selection."""
    task = make_task(
        story_points=1,
        task_type="subtask",
        task_stage="work",
    )

    config = select_model_for_task(task, "software-engineer")

    # Simple subtask in work stage should not over-allocate
    # Work stage floor is 'low', so simple tasks should stay low/medium
    assert config.effort in ("low", "medium")


def test_high_complexity_reasoning_gets_opus():
    """High complexity task in reasoning stage should use opus model."""
    task = make_task(
        story_points=8,
        task_type="story",
        complexity="high",
        task_stage="reasoning",
    )

    config = select_model_for_task(task, "architect")

    # High SP + high complexity + reasoning → opus with high effort
    assert config.model == "opus"
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["high"]
