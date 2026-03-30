"""Pre-embedded data — compact context injected before agent starts.

Two pre-embed builders:
- build_task_preembed: task data for dispatch (injected when agent starts working)
- build_heartbeat_preembed: fleet awareness for heartbeat (injected before heartbeat)

Pre-embeds are COMPACT — they go into the agent's system prompt or context
files. The full data is available via MCP calls. Pre-embeds give the agent
immediate awareness without needing to call anything.

Size budget: ~1000 chars for context/ files in gateway.
"""

from __future__ import annotations

from fleet.core.models import Task, TaskStatus


def build_task_preembed(task: Task, completeness_summary: str = "") -> str:
    """Build compact task pre-embed for dispatch injection.

    Includes the essential data the agent needs immediately — task ID,
    title, verbatim requirement, stage, readiness, and what to work on.

    Args:
        task: The Task being dispatched.
        completeness_summary: Optional artifact completeness one-liner.

    Returns:
        Compact text for injection into agent context.
    """
    cf = task.custom_fields
    lines = [
        "═══ TASK CONTEXT ═══",
        f"Task: {task.id[:8]} — {task.title}",
        f"Status: {task.status.value} | Priority: {task.priority}",
        f"Stage: {cf.task_stage or 'unknown'} | Readiness: {cf.task_readiness}%",
    ]

    if cf.requirement_verbatim:
        # Verbatim requirement — always included, the anchor
        verbatim = cf.requirement_verbatim
        if len(verbatim) > 300:
            verbatim = verbatim[:297] + "..."
        lines.append(f"Requirement: {verbatim}")

    if cf.project:
        lines.append(f"Project: {cf.project}")

    if completeness_summary:
        lines.append(f"Artifact: {completeness_summary}")

    # Stage-specific instruction (compact)
    stage = cf.task_stage or ""
    if stage == "conversation":
        lines.append("→ DISCUSS with PO. Do NOT produce code.")
    elif stage == "analysis":
        lines.append("→ ANALYZE codebase. Produce analysis document.")
    elif stage == "investigation":
        lines.append("→ RESEARCH options. Explore multiple approaches.")
    elif stage == "reasoning":
        lines.append("→ PLAN approach. Reference the verbatim requirement.")
    elif stage == "work":
        lines.append("→ EXECUTE the confirmed plan. Follow tool sequence.")

    if task.is_blocked:
        lines.append("⚠ BLOCKED — check dependencies before starting")

    lines.append("═══════════════════")
    return "\n".join(lines)


def build_heartbeat_preembed(
    agent_name: str,
    role: str,
    assigned_tasks: list[Task],
    messages_count: int = 0,
    events_count: int = 0,
    directives_count: int = 0,
    role_summary: str = "",
    fleet_mode: str = "",
    fleet_phase: str = "",
    agents_online: int = 0,
    agents_total: int = 0,
) -> str:
    """Build compact heartbeat pre-embed for session injection.

    Gives the agent immediate awareness of messages, events, role
    responsibilities, and assigned work without any MCP call.

    Args:
        agent_name: The agent's name.
        role: The agent's role.
        assigned_tasks: Tasks assigned to this agent.
        messages_count: Pending messages for this agent.
        events_count: Events since last heartbeat.
        directives_count: Pending PO directives.
        role_summary: One-line role-specific summary.
        fleet_mode: Current work mode.
        fleet_phase: Current cycle phase.
        agents_online: Online agent count.
        agents_total: Total agent count.

    Returns:
        Compact text for injection into agent context.
    """
    lines = [
        "═══ HEARTBEAT CONTEXT ═══",
        f"Agent: {agent_name} | Role: {role}",
        f"Fleet: {agents_online}/{agents_total} online | Mode: {fleet_mode} | Phase: {fleet_phase}",
    ]

    if messages_count:
        lines.append(f"📬 {messages_count} message(s) waiting")
    if directives_count:
        lines.append(f"📋 {directives_count} directive(s) from PO")
    if events_count:
        lines.append(f"📡 {events_count} event(s) since last heartbeat")

    if role_summary:
        lines.append(f"Role: {role_summary}")

    if assigned_tasks:
        lines.append(f"Tasks: {len(assigned_tasks)} assigned")
        for t in assigned_tasks[:3]:
            stage = t.custom_fields.task_stage or "?"
            readiness = t.custom_fields.task_readiness
            lines.append(f"  • {t.title[:40]} [{stage} {readiness}%]")
        if len(assigned_tasks) > 3:
            lines.append(f"  ... and {len(assigned_tasks) - 3} more")
    else:
        lines.append("Tasks: none assigned — idle")

    lines.append("═════════════════════════")
    return "\n".join(lines)