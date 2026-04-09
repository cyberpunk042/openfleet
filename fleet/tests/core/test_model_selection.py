"""Tests for dynamic model and effort selection.

Includes stage-aware effort adjustment tests.
"""

from fleet.core.model_selection import (
    select_model_for_task,
    _apply_stage_adjustment,
    _EFFORT_ORDER,
    _STAGE_EFFORT_FLOOR,
    ModelConfig,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _task(
    sp: int = 0, task_type: str = "task", model: str = "",
    stage: str = "", complexity: str = "",
) -> Task:
    return Task(
        id="t1", board_id="b1", title="Test", status=TaskStatus.INBOX,
        custom_fields=TaskCustomFields(
            story_points=sp, task_type=task_type, model=model,
            task_stage=stage, complexity=complexity,
        ),
    )


def test_explicit_override():
    config = select_model_for_task(_task(model="opus"), "devops")
    assert config.model == "opus"
    assert "explicit" in config.reason


def test_large_task_gets_opus():
    config = select_model_for_task(_task(sp=13), "software-engineer")
    assert config.model == "opus"
    assert config.effort == "high"


def test_epic_gets_opus_max_in_turbo():
    config = select_model_for_task(_task(task_type="epic"), "project-manager", budget_mode="turbo")
    assert config.model == "opus"
    assert config.effort == "max"


def test_epic_capped_to_high_in_standard():
    config = select_model_for_task(_task(task_type="epic"), "project-manager", budget_mode="standard")
    assert config.model == "opus"
    assert config.effort == "high"  # standard mode caps effort at high


def test_blocker_gets_opus():
    config = select_model_for_task(_task(task_type="blocker"), "devops")
    assert config.model == "opus"
    assert config.effort == "high"


def test_economic_mode_caps_model():
    config = select_model_for_task(_task(sp=8, task_type="story"), "software-engineer", budget_mode="economic")
    assert config.model == "sonnet"  # economic caps at sonnet
    assert config.effort == "medium"  # economic caps at medium


def test_rate_limit_pressure_reduces_effort():
    config = select_model_for_task(_task(sp=5), "architect", rate_limit_pct=87.0)
    # 85%+ rate limit drops effort by one level
    assert _EFFORT_ORDER[config.effort] < _EFFORT_ORDER["high"]


def test_rejection_escalates_effort():
    config = select_model_for_task(_task(sp=3), "software-engineer", rejection_count=1)
    # Rejection raises effort by one level from the base selection
    assert config.effort in ("medium", "high")  # base would be medium or low, escalated


def test_medium_story_gets_opus():
    config = select_model_for_task(_task(sp=5, task_type="story"), "software-engineer")
    assert config.model == "opus"


def test_simple_subtask_gets_sonnet_low():
    config = select_model_for_task(_task(sp=1, task_type="subtask"), "software-engineer")
    assert config.model == "sonnet"
    assert config.effort == "low"


def test_deep_reasoning_agent_medium_task():
    # architect with sp=5 should get opus
    config = select_model_for_task(_task(sp=5), "architect")
    assert config.model == "opus"
    assert "deep reasoning" in config.reason


def test_worker_agent_medium_task_stays_sonnet():
    # software-engineer with sp=5 but not a story -> sonnet high
    config = select_model_for_task(_task(sp=5), "software-engineer")
    assert config.model == "sonnet"
    assert config.effort == "high"


def test_standard_task():
    config = select_model_for_task(_task(sp=3), "devops")
    assert config.model == "sonnet"
    assert config.effort == "medium"


def test_default_no_sp():
    config = select_model_for_task(_task(), "software-engineer")
    assert config.model == "sonnet"


# Budget mode constraint tests removed — select_model_for_task
# no longer takes budget_mode parameter.


# ── Stage-aware effort adjustment ───────────────────────────────────

def test_reasoning_stage_raises_low_to_high():
    """Subtask at reasoning stage: low → high."""
    config = select_model_for_task(_task(sp=1, task_type="subtask", stage="reasoning"), "software-engineer")
    assert config.effort == "high"
    assert "stage:reasoning" in config.reason


def test_investigation_stage_raises_low_to_high():
    """Subtask at investigation stage: low → high."""
    config = select_model_for_task(_task(sp=1, task_type="subtask", stage="investigation"), "software-engineer")
    assert config.effort == "high"


def test_conversation_stage_raises_low_to_medium():
    """Subtask at conversation stage: low → medium."""
    config = select_model_for_task(_task(sp=1, task_type="subtask", stage="conversation"), "software-engineer")
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["medium"]


def test_analysis_stage_raises_low_to_medium():
    """Subtask at analysis stage: low → medium."""
    config = select_model_for_task(_task(sp=1, task_type="subtask", stage="analysis"), "software-engineer")
    assert _EFFORT_ORDER[config.effort] >= _EFFORT_ORDER["medium"]


def test_work_stage_no_raise():
    """Subtask at work stage: stays low."""
    config = select_model_for_task(_task(sp=1, task_type="subtask", stage="work"), "software-engineer")
    assert config.effort == "low"


def test_stage_never_lowers_high():
    """Large task already at high: work stage doesn't lower it."""
    config = select_model_for_task(_task(sp=8, stage="work"), "software-engineer")
    assert config.effort == "high"


def test_epic_max_survives_reasoning_in_turbo():
    """Epic already at max in turbo: reasoning doesn't change it."""
    config = select_model_for_task(_task(task_type="epic", sp=5, stage="reasoning"), "project-manager", budget_mode="turbo")
    assert config.effort == "max"


def test_standard_task_at_reasoning():
    """Standard 3-point task at reasoning: medium → high."""
    config = select_model_for_task(_task(sp=3, stage="reasoning"), "devops")
    assert config.effort == "high"
    assert "stage:reasoning" in config.reason


def test_all_stages_have_floor():
    """Every methodology stage should have a defined effort floor."""
    for stage in ["conversation", "analysis", "investigation", "reasoning", "work"]:
        assert stage in _STAGE_EFFORT_FLOOR


def test_thinking_floors_higher_than_work():
    """Investigation and reasoning floors should exceed work floor."""
    work_floor = _EFFORT_ORDER[_STAGE_EFFORT_FLOOR["work"]]
    for stage in ["investigation", "reasoning"]:
        assert _EFFORT_ORDER[_STAGE_EFFORT_FLOOR[stage]] > work_floor
