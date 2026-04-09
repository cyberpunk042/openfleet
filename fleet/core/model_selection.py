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
    backend_mode: str = "claude",
    budget_mode: str = "standard",
    rate_limit_pct: float = 0.0,
    rejection_count: int = 0,
) -> ModelConfig:
    """Select model and effort based on task + agent + stage + budget + pressure.

    Priority:
    1. Backend mode override (localai/hybrid short-circuits all logic below)
    2. Explicit model override in task custom field
    3. Story points (>= 8 → opus, >= 5 → consider, < 5 → sonnet)
    4. Task type (epic/story/blocker → opus)
    5. Agent role (deep reasoning agents get opus on medium+ tasks)
    6. Default: sonnet with medium effort
    7. Stage adjustment: thinking stages raise effort floor
    8. Budget mode cap: economic/minimal modes cap model tier and effort
    9. Rate limit pressure: >85% drops effort, >95% blocks
    10. Rejection escalation: re-attempts get more resource

    Returns:
        ModelConfig with model, effort, and reason for the selection.
    """
    # Backend mode override
    if backend_mode == "localai":
        return ModelConfig(
            model="localai",
            effort="medium",
            reason="Backend mode: localai",
        )

    if backend_mode == "hybrid":
        # Use localai for low-complexity tasks, claude for everything else
        complexity = task.custom_fields.complexity or "" if task.custom_fields else ""
        story_points = task.custom_fields.story_points or 0 if task.custom_fields else 0
        try:
            story_points = int(story_points)
        except (TypeError, ValueError):
            story_points = 0
        if story_points <= 2 and complexity in ("", "low", "routine"):
            return ModelConfig(
                model="localai",
                effort="medium",
                reason=f"Hybrid mode: low complexity (sp={story_points})",
            )
        # Fall through to normal claude selection for complex tasks

    config = _select_unconstrained(task, agent_name)

    # Stage-aware adjustment — thinking stages raise the effort floor
    stage = task.custom_fields.task_stage if task.custom_fields else ""
    if stage:
        config = _apply_stage_adjustment(config, stage)

    # Budget mode cap — economic/minimal modes limit model tier + effort
    config = _apply_budget_cap(config, budget_mode)

    # Rate limit pressure — conserve when approaching limits
    config = _apply_rate_limit_pressure(config, rate_limit_pct)

    # Rejection escalation — re-attempts get more cognitive resource
    if rejection_count > 0:
        config = _apply_rejection_escalation(config, rejection_count)

    return config


# Effort level ordering for comparisons
_EFFORT_ORDER = {"low": 0, "medium": 1, "high": 2, "max": 3}

# Minimum effort per methodology stage
# Thinking stages (conversation → reasoning) require deeper cognitive work
# Work stage uses whatever complexity-based selection determined
_STAGE_EFFORT_FLOOR: dict[str, str] = {
    "conversation": "medium",   # understanding requirements
    "analysis": "medium",       # examining existing systems
    "investigation": "high",    # exploring and evaluating options
    "reasoning": "high",        # planning the approach
    "work": "low",              # executing — complexity already factored in
}


def _apply_stage_adjustment(config: ModelConfig, stage: str) -> ModelConfig:
    """Raise effort floor based on methodology stage.

    Thinking stages (conversation through reasoning) need deeper cognitive
    effort than pure execution. This ONLY raises effort — never lowers it.
    If complexity-based selection already chose high, stage won't reduce it.

    Returns:
        ModelConfig with potentially raised effort.
    """
    floor = _STAGE_EFFORT_FLOOR.get(stage)
    if not floor:
        return config

    current = _EFFORT_ORDER.get(config.effort, 1)
    minimum = _EFFORT_ORDER.get(floor, 1)

    if current < minimum:
        effort_name = floor
        return ModelConfig(
            model=config.model,
            effort=effort_name,
            reason=f"{config.reason} + stage:{stage} raises effort to {effort_name}",
        )

    return config


# ─── Budget Mode Caps ──────────────────────────────────────────────

# Model tier ordering for cap/escalation
_MODEL_ORDER = {"haiku": 0, "localai": 0, "sonnet": 1, "opus": 2}
_MODEL_NAMES = {0: "haiku", 1: "sonnet", 2: "opus"}

# Budget mode → maximum model tier + maximum effort
_BUDGET_CAPS = {
    "turbo": {"model_cap": "opus", "effort_cap": "max"},
    "standard": {"model_cap": "opus", "effort_cap": "high"},
    "economic": {"model_cap": "sonnet", "effort_cap": "medium"},
    "minimal": {"model_cap": "haiku", "effort_cap": "low"},
}


def _apply_budget_cap(config: ModelConfig, budget_mode: str) -> ModelConfig:
    """Cap model tier and effort based on fleet budget mode."""
    caps = _BUDGET_CAPS.get(budget_mode)
    if not caps:
        return config

    model_cap = caps["model_cap"]
    effort_cap = caps["effort_cap"]

    current_model = _MODEL_ORDER.get(config.model, 1)
    cap_model = _MODEL_ORDER.get(model_cap, 2)

    current_effort = _EFFORT_ORDER.get(config.effort, 1)
    cap_effort = _EFFORT_ORDER.get(effort_cap, 2)

    capped_model = config.model
    capped_effort = config.effort
    reasons = []

    if current_model > cap_model:
        capped_model = model_cap
        reasons.append(f"budget:{budget_mode} caps model to {model_cap}")

    if current_effort > cap_effort:
        capped_effort = effort_cap
        reasons.append(f"budget:{budget_mode} caps effort to {effort_cap}")

    if reasons:
        return ModelConfig(
            model=capped_model,
            effort=capped_effort,
            reason=f"{config.reason} + {' + '.join(reasons)}",
        )

    return config


def _apply_rate_limit_pressure(config: ModelConfig, rate_limit_pct: float) -> ModelConfig:
    """Reduce effort when rate limit is under pressure."""
    if rate_limit_pct <= 0:
        return config  # No data — don't adjust

    if rate_limit_pct >= 95:
        # Critical — minimum effort
        return ModelConfig(
            model=config.model,
            effort="low",
            reason=f"{config.reason} + rate_limit:{rate_limit_pct:.0f}% CRITICAL",
        )

    if rate_limit_pct >= 85:
        # Conserve — drop effort by one level
        current = _EFFORT_ORDER.get(config.effort, 1)
        reduced = max(0, current - 1)
        effort_name = {0: "low", 1: "medium", 2: "high", 3: "max"}.get(reduced, "medium")
        return ModelConfig(
            model=config.model,
            effort=effort_name,
            reason=f"{config.reason} + rate_limit:{rate_limit_pct:.0f}% conserving",
        )

    return config


def _apply_rejection_escalation(config: ModelConfig, rejection_count: int) -> ModelConfig:
    """Escalate effort for re-attempts after rejection.

    When work was rejected, the next attempt gets more cognitive resource.
    This is the opposite of budget cap — rejection RAISES effort.
    """
    if rejection_count <= 0:
        return config

    current_effort = _EFFORT_ORDER.get(config.effort, 1)
    escalated = min(3, current_effort + 1)  # Raise by 1 level
    effort_name = {0: "low", 1: "medium", 2: "high", 3: "max"}.get(escalated, "high")

    return ModelConfig(
        model=config.model,
        effort=effort_name,
        reason=f"{config.reason} + rejection #{rejection_count} → effort escalated",
    )


def _select_unconstrained(task: Task, agent_name: str) -> ModelConfig:
    """Select model without budget constraints (internal)."""
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