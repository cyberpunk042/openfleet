"""Autonomous driver model — agents that create their own work.

Driver agents have products they own and roadmaps they drive:
- project-manager → DSPD (DevOps Solution Product Development)
- accountability-generator → NNRT, Factual Engine, Factual Platform

When no human work is assigned, drivers follow this priority model:
1. Human-assigned work (highest)
2. Dependency unblocking (help other driver's prerequisite)
3. Own product roadmap (drive next milestone)
4. Fleet improvement (suggestions, gap detection)

Used by the orchestrator and PM heartbeat to determine what drivers
should work on when they have no assigned tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.models import Task, TaskStatus


@dataclass
class ProductRoadmap:
    """A product owned by a driver agent."""

    name: str                # Product name
    project: str             # Fleet project name
    owner_agent: str         # Agent responsible
    description: str = ""
    next_milestones: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # Other products this depends on


# Fleet product definitions
PRODUCTS = {
    "dspd": ProductRoadmap(
        name="DSPD",
        project="dspd",
        owner_agent="project-manager",
        description="DevOps Solution Product Development — project management surface for the fleet",
        next_milestones=[
            "Plane self-hosted and operational",
            "Fleet CLI Plane integration",
            "PM agent uses Plane for sprint management",
            "Cross-project dependency tracking in Plane",
        ],
    ),
    "nnrt": ProductRoadmap(
        name="NNRT",
        project="nnrt",
        owner_agent="accountability-generator",
        description="Narrative-to-Neutral Report Transformer — fact extraction and analysis",
        next_milestones=[
            "Contradiction detection pass",
            "Evidence chain validation",
            "Structured output pipeline",
        ],
        prerequisites=["dspd"],  # AG needs DSPD for organized development
    ),
}

# Driver agent names
DRIVER_AGENTS = {"project-manager", "fleet-ops", "accountability-generator", "devsecops-expert"}


@dataclass
class DriverDirective:
    """What a driver should work on right now."""

    priority_level: int     # 1=human, 2=unblock, 3=roadmap, 4=improvement
    action: str             # "work_on_task", "drive_product", "improve_fleet", "idle"
    task_id: str = ""       # If working on a specific task
    product: str = ""       # If driving a product
    description: str = ""   # What to do


def determine_driver_directive(
    agent_name: str,
    tasks: list[Task],
) -> DriverDirective:
    """Determine what a driver agent should focus on right now.

    Priority:
    1. Human-assigned tasks (highest)
    2. Unblocking dependencies for own product
    3. Own product roadmap
    4. Fleet improvement
    """
    # 1. Check for human-assigned tasks (not auto-created)
    human_tasks = [
        t for t in tasks
        if t.custom_fields.agent_name == agent_name
        and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS)
        and not t.auto_created
    ]
    if human_tasks:
        return DriverDirective(
            priority_level=1,
            action="work_on_task",
            task_id=human_tasks[0].id,
            description=f"Human-assigned: {human_tasks[0].title[:50]}",
        )

    # 2. Check for any assigned tasks (including auto-created)
    assigned_tasks = [
        t for t in tasks
        if t.custom_fields.agent_name == agent_name
        and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS)
    ]
    if assigned_tasks:
        return DriverDirective(
            priority_level=2,
            action="work_on_task",
            task_id=assigned_tasks[0].id,
            description=f"Assigned: {assigned_tasks[0].title[:50]}",
        )

    # 3. Check if own product has next milestone work
    product = _find_owned_product(agent_name)
    if product:
        # Check if there are existing product tasks
        product_tasks = [
            t for t in tasks
            if t.custom_fields.project == product.project
            and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW)
        ]
        if not product_tasks and product.next_milestones:
            return DriverDirective(
                priority_level=3,
                action="drive_product",
                product=product.name,
                description=f"Drive {product.name}: {product.next_milestones[0]}",
            )

    # 4. Fleet improvement
    return DriverDirective(
        priority_level=4,
        action="improve_fleet",
        description="No assigned work. Check for fleet improvements, gaps, or suggestions.",
    )


def _find_owned_product(agent_name: str) -> Optional[ProductRoadmap]:
    """Find the product owned by this agent."""
    for product in PRODUCTS.values():
        if product.owner_agent == agent_name:
            return product
    return None


def is_driver(agent_name: str) -> bool:
    """Check if an agent is a driver (creates own work) vs worker (executes assigned)."""
    return agent_name in DRIVER_AGENTS