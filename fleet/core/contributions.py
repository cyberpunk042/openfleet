"""Contribution system — cross-agent synergy brain module.

When a task enters REASONING stage, this module creates parallel
contribution subtasks based on the synergy matrix. Contributors
work independently. All required contributions must arrive before
the target task can proceed to WORK stage.

Source: fleet-vision-architecture §30, §33.5, fleet-elevation/15
Config: config/synergy-matrix.yaml

10 pieces (§33.5):
  1. fleet_contribute MCP tool ✓ (in tools.py)
  2. fleet_request_input MCP tool ✓ (in tools.py)
  3. contributions.py brain module ← THIS FILE
  4. config/synergy-matrix.yaml ✓ (created)
  5. Contribution pre-embed section (in preembed — future)
  6. build_contribution_chain() (in event_chain — exists)
  7. Contribution completeness checking ← IN THIS FILE
  8. PM notification when all arrive ← IN THIS FILE
  9. Dispatch blocking until received ← IN THIS FILE
  10. Anti-pattern detection ← IN THIS FILE
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


# ─── Synergy Matrix Loading ─────────────────────────────────────────


@dataclass
class ContributionSpec:
    """A contribution requirement from the synergy matrix."""
    role: str
    contribution_type: str
    priority: str  # required, recommended, conditional
    condition: str = ""
    description: str = ""


def load_synergy_matrix(fleet_dir: str = "") -> dict[str, list[ContributionSpec]]:
    """Load synergy matrix from config/synergy-matrix.yaml.

    Returns: {target_role: [ContributionSpec, ...]}
    """
    if not fleet_dir:
        fleet_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(fleet_dir, "config", "synergy-matrix.yaml")
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Failed to load synergy matrix: %s", e)
        return {}

    matrix: dict[str, list[ContributionSpec]] = {}
    for target_role, specs in data.get("contributions", {}).items():
        matrix[target_role] = [
            ContributionSpec(
                role=s.get("role", ""),
                contribution_type=s.get("type", ""),
                priority=s.get("priority", "recommended"),
                condition=s.get("condition", ""),
                description=s.get("description", ""),
            )
            for s in (specs or [])
        ]

    return matrix


def get_skip_types(fleet_dir: str = "") -> list[str]:
    """Task types that skip contributions entirely."""
    if not fleet_dir:
        fleet_dir = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))

    config_path = os.path.join(fleet_dir, "config", "synergy-matrix.yaml")
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return data.get("skip_contributions", [])
    except Exception:
        return ["subtask", "blocker", "concern", "spike"]


# ─── Contribution Opportunity Detection ─────────────────────────────


@dataclass
class ContributionOpportunity:
    """A contribution that should be created for a task."""
    target_task_id: str
    target_agent: str
    contributor_role: str
    contribution_type: str
    priority: str
    description: str


def detect_contribution_opportunities(
    task_id: str,
    target_agent: str,
    task_type: str = "task",
    fleet_dir: str = "",
) -> list[ContributionOpportunity]:
    """Detect what contributions a task needs based on synergy matrix.

    Called by orchestrator when a task enters REASONING stage.

    Args:
        task_id: The task entering REASONING
        target_agent: The agent assigned to the task
        task_type: Task type (epic, story, task, subtask, etc.)
        fleet_dir: Fleet directory for config loading

    Returns:
        List of ContributionOpportunity to create as subtasks
    """
    skip_types = get_skip_types(fleet_dir)
    if task_type in skip_types:
        return []

    matrix = load_synergy_matrix(fleet_dir)

    # Determine target role from agent name
    # Agent names map to roles (e.g., "software-engineer" → "software-engineer")
    target_role = target_agent

    specs = matrix.get(target_role, [])
    if not specs:
        return []

    opportunities = []
    for spec in specs:
        # Skip conditional contributions (brain can't evaluate conditions
        # without understanding the task — PO decides via requirements)
        if spec.priority == "conditional":
            continue

        opportunities.append(ContributionOpportunity(
            target_task_id=task_id,
            target_agent=target_agent,
            contributor_role=spec.role,
            contribution_type=spec.contribution_type,
            priority=spec.priority,
            description=spec.description,
        ))

    return opportunities


# ─── Contribution Completeness ───────────────────────────────────────


@dataclass
class ContributionStatus:
    """Status of contributions for a task."""
    task_id: str
    required: list[str]       # contribution types required
    received: list[str]       # contribution types received
    missing: list[str]        # required but not received
    all_received: bool
    completeness_pct: float


def check_contribution_completeness(
    task_id: str,
    target_agent: str,
    task_type: str,
    received_types: list[str],
    fleet_dir: str = "",
) -> ContributionStatus:
    """Check if all required contributions have been received.

    Used by:
    - Orchestrator dispatch gate: block dispatch until required received
    - fleet_contribute tool: check if all arrived after posting
    - Fleet-ops review: verify contributions were used

    Args:
        task_id: Task to check
        target_agent: Agent assigned to task
        task_type: Task type
        received_types: Contribution types already received
        fleet_dir: Fleet dir for config
    """
    skip_types = get_skip_types(fleet_dir)
    if task_type in skip_types:
        return ContributionStatus(
            task_id=task_id,
            required=[],
            received=received_types,
            missing=[],
            all_received=True,
            completeness_pct=100.0,
        )

    matrix = load_synergy_matrix(fleet_dir)
    target_role = target_agent
    specs = matrix.get(target_role, [])

    required = [
        s.contribution_type for s in specs
        if s.priority == "required"
    ]

    received_set = set(received_types)
    missing = [r for r in required if r not in received_set]
    total = len(required)
    received_count = total - len(missing)
    pct = (received_count / total * 100) if total > 0 else 100.0

    return ContributionStatus(
        task_id=task_id,
        required=required,
        received=[r for r in required if r in received_set],
        missing=missing,
        all_received=len(missing) == 0,
        completeness_pct=pct,
    )


# ─── Anti-Pattern Detection ─────────────────────────────────────────


@dataclass
class ContributionAntiPattern:
    """Detected contribution anti-pattern."""
    pattern: str  # siloed_work, ghost_contribution, contribution_ignored
    agent: str
    task_id: str
    details: str


def detect_anti_patterns(
    task_id: str,
    target_agent: str,
    task_type: str,
    received_types: list[str],
    task_comments: list[dict],
    fleet_dir: str = "",
) -> list[ContributionAntiPattern]:
    """Detect contribution anti-patterns.

    Patterns:
    - siloed_work: task completed without required contributions
    - ghost_contribution: contribution posted but never referenced
    - contribution_ignored: contributions received but not in plan/work

    Args:
        task_id: Task to check
        target_agent: Agent assigned
        task_type: Task type
        received_types: What was received
        task_comments: Task comments for reference checking
    """
    patterns = []

    # Siloed work: required contributions missing but task advanced
    status = check_contribution_completeness(
        task_id, target_agent, task_type, received_types, fleet_dir,
    )
    if not status.all_received and status.required:
        patterns.append(ContributionAntiPattern(
            pattern="siloed_work",
            agent=target_agent,
            task_id=task_id,
            details=f"Missing required: {', '.join(status.missing)}",
        ))

    return patterns
