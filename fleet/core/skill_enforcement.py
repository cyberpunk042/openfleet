"""Skill enforcement — required tool usage per task type.

Ensures agents use the right fleet tools for their task type:
- Code tasks MUST use fleet_commit (not raw git)
- Review tasks MUST use fleet_approve (not raw API)
- Planning tasks MUST use fleet_task_create (produce tasks, not text)
- All tasks MUST use fleet_read_context first

Missing required tools lower the confidence score in the approval,
which fleet-ops considers during review.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolRequirement:
    """Required or recommended tool for a task type."""

    tool_name: str
    required: bool = True     # If True, missing this lowers confidence
    reason: str = ""


# Tool requirements by task type
TASK_TYPE_REQUIREMENTS: dict[str, list[ToolRequirement]] = {
    "task": [
        ToolRequirement("fleet_read_context", True, "Must load context before starting"),
        ToolRequirement("fleet_task_accept", True, "Must share plan before working"),
        ToolRequirement("fleet_commit", True, "Must use fleet commit for code changes"),
        ToolRequirement("fleet_task_complete", True, "Must use completion flow"),
        ToolRequirement("fleet_task_progress", False, "Should post progress for long tasks"),
    ],
    "subtask": [
        ToolRequirement("fleet_read_context", True, "Must load context"),
        ToolRequirement("fleet_task_accept", True, "Must share plan"),
        ToolRequirement("fleet_task_complete", True, "Must use completion flow"),
    ],
    "story": [
        ToolRequirement("fleet_read_context", True, "Must load context"),
        ToolRequirement("fleet_task_accept", True, "Must share plan with risk assessment"),
        ToolRequirement("fleet_task_create", True, "Stories should create subtasks"),
        ToolRequirement("fleet_commit", True, "Must use fleet commit"),
        ToolRequirement("fleet_task_complete", True, "Must use completion flow"),
        ToolRequirement("fleet_task_progress", True, "Stories are long — progress required"),
    ],
    "epic": [
        ToolRequirement("fleet_read_context", True, "Must load full context"),
        ToolRequirement("fleet_agent_status", True, "Must check fleet state for planning"),
        ToolRequirement("fleet_task_create", True, "Epics MUST produce subtasks"),
        ToolRequirement("fleet_task_accept", True, "Must share breakdown plan"),
    ],
    "blocker": [
        ToolRequirement("fleet_read_context", True, "Must understand blocker context"),
        ToolRequirement("fleet_task_accept", True, "Must share resolution approach"),
        ToolRequirement("fleet_task_complete", True, "Must complete when resolved"),
        ToolRequirement("fleet_alert", False, "Consider alerting about the blocker"),
    ],
    "review": [
        ToolRequirement("fleet_read_context", True, "Must load context for review"),
        ToolRequirement("fleet_agent_status", True, "Must check fleet state"),
        ToolRequirement("fleet_approve", True, "Must use approval tool"),
    ],
    "security_audit": [
        ToolRequirement("fleet_read_context", True, "Must load context"),
        ToolRequirement("fleet_alert", True, "Must use alert for findings"),
        ToolRequirement("fleet_notify_human", False, "Should notify on critical findings"),
    ],
}


@dataclass
class ComplianceReport:
    """Report on tool usage compliance for a task."""

    task_type: str
    tools_used: list[str]
    required_met: list[str] = field(default_factory=list)
    required_missed: list[str] = field(default_factory=list)
    recommended_missed: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return len(self.required_missed) == 0

    @property
    def confidence_penalty(self) -> float:
        """Confidence reduction for missing required tools (0-30 points)."""
        if not self.required_missed:
            return 0.0
        return min(len(self.required_missed) * 10, 30)


def check_compliance(
    task_type: str,
    tools_used: list[str],
) -> ComplianceReport:
    """Check if an agent used the required tools for their task type.

    Args:
        task_type: Task type (task, story, epic, etc.)
        tools_used: List of fleet tool names the agent called.

    Returns:
        ComplianceReport with compliance status and confidence penalty.
    """
    requirements = TASK_TYPE_REQUIREMENTS.get(task_type, TASK_TYPE_REQUIREMENTS.get("task", []))
    used_set = set(tools_used)

    report = ComplianceReport(task_type=task_type, tools_used=tools_used)

    for req in requirements:
        if req.tool_name in used_set:
            report.required_met.append(req.tool_name)
        elif req.required:
            report.required_missed.append(req.tool_name)
        else:
            report.recommended_missed.append(req.tool_name)

    return report


def get_required_tools(task_type: str) -> list[str]:
    """Get list of required tool names for a task type."""
    requirements = TASK_TYPE_REQUIREMENTS.get(task_type, TASK_TYPE_REQUIREMENTS.get("task", []))
    return [r.tool_name for r in requirements if r.required]