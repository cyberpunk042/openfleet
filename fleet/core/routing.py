"""Agent routing — match tasks to agents by capability, availability, workload.

Determines which agent is best suited for a task based on:
- Agent capabilities (defined in agent-identities.yaml)
- Current workload (how many active tasks)
- Agent status (active/idle/sleeping/offline)
- Task type and content analysis

Used by PM when creating subtasks and by the orchestrator when
auto-assigning unassigned inbox tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.models import Agent, Task, TaskStatus


# Agent capability definitions — what each agent is good at
AGENT_CAPABILITIES: dict[str, list[str]] = {
    "architect": [
        "architecture", "design", "system design", "component structure",
        "dependency mapping", "decision record", "review", "pattern",
    ],
    "software-engineer": [
        "implement", "code", "feature", "fix", "bug", "refactor",
        "test", "python", "module", "function", "class", "api",
    ],
    "qa-engineer": [
        "test", "qa", "quality", "coverage", "regression", "validation",
        "pytest", "benchmark", "performance",
    ],
    "devops": [
        "docker", "ci", "cd", "pipeline", "deploy", "infrastructure",
        "monitoring", "setup", "configure", "script", "automation",
    ],
    "devsecops-expert": [
        "security", "cve", "vulnerability", "secret", "audit",
        "compliance", "hardening", "credential", "supply chain",
    ],
    "technical-writer": [
        "documentation", "readme", "changelog", "api doc", "guide",
        "onboarding", "adr", "release notes",
    ],
    "ux-designer": [
        "ui", "ux", "interface", "accessibility", "wcag", "design",
        "wireframe", "layout", "user flow", "component",
    ],
    "project-manager": [
        "plan", "sprint", "evaluate", "assign", "prioritize",
        "roadmap", "velocity", "breakdown", "estimate",
    ],
    "fleet-ops": [
        "governance", "review", "quality", "digest", "monitor",
        "alert", "gap", "compliance",
    ],
    "accountability-generator": [
        "accountability", "transparency", "evidence", "mapping",
        "consequence", "narrative", "report", "intake",
    ],
}


@dataclass
class RouteMatch:
    """Result of matching a task to an agent."""

    agent_name: str
    score: float          # 0-100 match quality
    reasons: list[str] = field(default_factory=list)


def route_task(
    task: Task,
    available_agents: list[Agent],
    active_task_counts: dict[str, int] | None = None,
) -> list[RouteMatch]:
    """Find the best agent(s) for a task, ranked by match quality.

    Args:
        task: The task to route.
        available_agents: Agents that could handle the task.
        active_task_counts: How many in_progress tasks each agent has.

    Returns:
        List of matches sorted by score (highest first).
    """
    active_counts = active_task_counts or {}
    matches: list[RouteMatch] = []

    task_text = f"{task.title} {task.description or ''}".lower()
    task_type = (task.custom_fields.task_type or "").lower()

    for agent in available_agents:
        if "Gateway" in agent.name:
            continue

        capabilities = AGENT_CAPABILITIES.get(agent.name, [])
        score = 0.0
        reasons: list[str] = []

        # 1. Keyword match against capabilities
        keyword_hits = sum(1 for cap in capabilities if cap in task_text)
        if keyword_hits > 0:
            cap_score = min(keyword_hits * 15, 60)
            score += cap_score
            reasons.append(f"keyword_match={keyword_hits} (+{cap_score})")

        # 2. Task type match
        if task_type in ("blocker",) and agent.name in ("devops", "software-engineer"):
            score += 10
            reasons.append("blocker_resolver (+10)")
        if task_type in ("epic", "story") and agent.name == "architect":
            score += 15
            reasons.append("design_task (+15)")
        if "review" in task_type and agent.name in ("qa-engineer", "fleet-ops"):
            score += 20
            reasons.append("review_specialist (+20)")

        # 3. Workload penalty — prefer less busy agents
        active = active_counts.get(agent.name, 0)
        if active > 0:
            penalty = min(active * 15, 30)
            score -= penalty
            reasons.append(f"workload={active} (-{penalty})")

        # 4. Agent status bonus — prefer active/idle over sleeping
        if agent.status == "online":
            score += 5
            reasons.append("online (+5)")

        if score > 0:
            matches.append(RouteMatch(
                agent_name=agent.name,
                score=score,
                reasons=reasons,
            ))

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches


def suggest_agent(
    task: Task,
    available_agents: list[Agent],
    active_task_counts: dict[str, int] | None = None,
) -> Optional[str]:
    """Suggest the single best agent for a task. Returns agent name or None."""
    matches = route_task(task, available_agents, active_task_counts)
    return matches[0].agent_name if matches else None