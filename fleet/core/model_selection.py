"""Dynamic model and effort selection — task-aware intelligence allocation.

Selects the right model (opus/sonnet) and effort level (low/medium/high/max)
based on task complexity, type, story points, and agent role.

Principles:
- Complex work deserves deep reasoning (opus, high effort)
- Routine work is efficient with standard reasoning (sonnet, medium)
- The model should adapt to the TASK, not be fixed per agent
- PM can override via the model custom field
- Story points are the primary complexity signal

Used by dispatch to set ANTHROPIC_MODEL and CLAUDE_CODE_EFFORT_LEVEL
environment variables for agent sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fleet.core.models import Task


# Agents that ALWAYS benefit from opus on medium+ tasks
DEEP_REASONING_AGENTS = {
    "architect",
    "devsecops-expert",
    "project-manager",
    "accountability-generator",
}


@dataclass
class ModelConfig:
    """Selected model and effort for a task."""

    model: str       # "opus", "sonnet", "haiku"
    effort: str      # "low", "medium", "high", "max"
    reason: str      # Why this was selected


def select_model_for_task(
    task: Task,
    agent_name: str = "",
) -> ModelConfig:
    """Select model and effort based on task + agent.

    Priority:
    1. Explicit model override in task custom field
    2. Story points (>= 8 → opus, >= 5 → consider, < 5 → sonnet)
    3. Task type (epic/story/blocker → opus)
    4. Agent role (deep reasoning agents get opus on medium+ tasks)
    5. Default: sonnet with medium effort

    Returns:
        ModelConfig with model, effort, and reason for the selection.
    """
    # 1. Explicit override
    if task.custom_fields.model:
        model = task.custom_fields.model
        effort = "high" if model == "opus" else "medium"
        return ModelConfig(model=model, effort=effort, reason=f"explicit override: {model}")

    sp = task.custom_fields.story_points or 0
    task_type = task.custom_fields.task_type or "task"

    # 2. Large tasks always get opus
    if sp >= 8:
        return ModelConfig(
            model="opus", effort="high",
            reason=f"large task (sp={sp}): deep reasoning required",
        )

    # 3. Epic and blocker types get opus
    if task_type in ("epic",):
        return ModelConfig(
            model="opus", effort="max",
            reason=f"epic: strategic planning requires max effort",
        )
    if task_type in ("blocker",):
        return ModelConfig(
            model="opus", effort="high",
            reason=f"blocker: careful analysis required",
        )

    # 4. Story tasks — opus for medium+ complexity
    if task_type in ("story",) and sp >= 5:
        return ModelConfig(
            model="opus", effort="high",
            reason=f"story with sp={sp}: complex feature work",
        )

    # 5. Agent-specific: deep reasoning agents get opus on sp >= 5
    if agent_name in DEEP_REASONING_AGENTS and sp >= 5:
        return ModelConfig(
            model="opus", effort="high",
            reason=f"{agent_name} on medium+ task (sp={sp}): deep reasoning role",
        )

    # 6. Medium complexity — sonnet with appropriate effort
    if sp >= 5:
        return ModelConfig(
            model="sonnet", effort="high",
            reason=f"medium task (sp={sp}): sonnet with high effort",
        )

    if sp >= 3:
        return ModelConfig(
            model="sonnet", effort="medium",
            reason=f"standard task (sp={sp}): sonnet with medium effort",
        )

    # 7. Simple/unspecified tasks
    if task_type in ("subtask",) or sp <= 2:
        return ModelConfig(
            model="sonnet", effort="low",
            reason=f"simple task (sp={sp}, type={task_type}): efficient execution",
        )

    # 8. Default
    return ModelConfig(
        model="sonnet", effort="medium",
        reason="default: standard complexity",
    )