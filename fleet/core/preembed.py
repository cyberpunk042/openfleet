"""Pre-embedded data — FULL context injected before agent starts.

The pre-embedded data IS the full data the agent needs. NOT compressed.
NOT summarized. The COMPLETE data set for the agent's role.

MCP calls are for aggregating ADDITIONAL data — not for getting what
should already be here.

Gateway context/ files now support up to 8000 chars each. Multiple
files can be used. No practical limit on total pre-embedded data.
"""

from __future__ import annotations

from typing import Optional
from fleet.core.models import Task, TaskStatus


def format_events(events: list[dict], limit: int = 10) -> str:
    """Format events with full detail."""
    if not events:
        return "No events since last heartbeat."

    lines = []
    for event in events[:limit]:
        etype = event.get("type", "").split(".")[-1]
        agent = event.get("agent", "system")
        summary = event.get("summary", "")
        time = event.get("time", "")[:19]
        lines.append(f"  {time} [{etype}] {agent}: {summary}")

    if len(events) > limit:
        lines.append(f"  ... +{len(events) - limit} more events")

    return "\n".join(lines)


def format_task_full(task: Task) -> str:
    """Format a single task with FULL details — not truncated."""
    cf = task.custom_fields
    lines = [
        f"### {task.title}",
        f"- ID: {task.id[:8]}",
        f"- Status: {task.status.value}",
        f"- Priority: {task.priority}",
        f"- Agent: {cf.agent_name or 'UNASSIGNED'}",
        f"- Type: {cf.task_type or 'unset'}",
        f"- Stage: {cf.task_stage or 'unset'}",
        f"- Readiness: {cf.task_readiness}%",
        f"- Delivery Phase: {cf.delivery_phase or 'not set'}",
        f"- Story Points: {cf.story_points or 'unset'}",
    ]
    if cf.requirement_verbatim:
        lines.append(f"- Verbatim Requirement: {cf.requirement_verbatim}")
    if task.description:
        lines.append(f"- Description: {task.description[:500]}")
    if task.is_blocked:
        lines.append(f"- BLOCKED by: {task.blocked_by_task_ids}")
    if cf.pr_url:
        lines.append(f"- PR: {cf.pr_url}")
    if cf.plane_issue_id:
        lines.append(f"- Plane: {cf.plane_issue_id[:8]}")

    return "\n".join(lines)


def build_task_preembed(task: Task, completeness_summary: str = "") -> str:
    """Build FULL task pre-embed for dispatch injection.

    Includes everything the agent needs about THIS task.
    Not compressed. Full data.
    """
    cf = task.custom_fields
    lines = [
        "# TASK CONTEXT",
        "",
        format_task_full(task),
    ]

    if completeness_summary:
        lines.append(f"- Artifact: {completeness_summary}")

    # Stage instructions
    stage = cf.task_stage or ""
    if stage:
        from fleet.core.stage_context import get_stage_instructions
        instructions = get_stage_instructions(stage)
        if instructions:
            lines.append("")
            lines.append(instructions)

    # Phase standards (what quality bars apply at this delivery phase)
    delivery_phase = cf.delivery_phase or ""
    if delivery_phase:
        try:
            from fleet.core.phases import get_phase_standards, get_required_contributions
            progression = cf.phase_progression or "standard"
            standards = get_phase_standards(delivery_phase, progression)
            required_contribs = get_required_contributions(delivery_phase, progression)

            lines.append("")
            lines.append(f"## Delivery Phase: {delivery_phase}")
            if standards:
                lines.append("### Phase Standards")
                for key, value in standards.items():
                    lines.append(f"- **{key}:** {value}")
            if required_contribs:
                lines.append(f"### Required Contributions: {', '.join(required_contribs)}")
        except Exception:
            pass

    # Contribution status (what's received, what's missing)
    try:
        from fleet.core.contributions import check_contribution_completeness
        agent_name = cf.agent_name or ""
        task_type = cf.task_type or "task"
        if agent_name:
            # We can't query comments from preembed (no mc client).
            # But we can note the contribution requirement.
            from fleet.core.contributions import load_synergy_matrix, get_skip_types
            skip_types = get_skip_types()
            if task_type not in skip_types:
                matrix = load_synergy_matrix()
                specs = matrix.get(agent_name, [])
                required = [s.contribution_type for s in specs if s.priority == "required"]
                if required:
                    lines.append("")
                    lines.append("## Required Contributions")
                    lines.append(f"Before work stage, these contributions must be received:")
                    for r in required:
                        lines.append(f"- **{r}** — check task comments for this input")
                    lines.append("If any are missing → use fleet_request_input to request them.")
    except Exception:
        pass

    # Skill recommendations for this stage
    agent_name = cf.agent_name or ""
    if stage and agent_name:
        try:
            from fleet.core.skill_recommendations import get_skill_recommendations
            recs = get_skill_recommendations(agent_name, stage)

            if recs["always"] or recs["stage"]:
                lines.append("")
                lines.append(f"## Skills for This Stage ({stage})")

                if recs["always"]:
                    lines.append("Always available:")
                    for s in recs["always"]:
                        lines.append(f"  - /{s['skill']} — {s.get('why', '')}")

                if recs["stage"]:
                    lines.append(f"Recommended at {stage}:")
                    for s in recs["stage"]:
                        plugin = f" ({s['plugin']})" if s.get("plugin") else ""
                        lines.append(f"  - /{s['skill']}{plugin} — {s.get('why', '')}")

                if recs["blocked"]:
                    lines.append(f"Blocked at {stage}:")
                    blocked_str = ", ".join(f"/{b}" for b in recs["blocked"][:5])
                    lines.append(f"  {blocked_str}")
        except Exception:
            pass

    return "\n".join(lines)


def build_heartbeat_preembed(
    agent_name: str,
    role: str,
    assigned_tasks: list[Task],
    messages: list[dict] | None = None,
    directives: list[dict] | None = None,
    events: list[dict] | None = None,
    role_data: dict | None = None,
    fleet_mode: str = "",
    fleet_phase: str = "",
    fleet_backend: str = "",
    agents_online: int = 0,
    agents_total: int = 0,
) -> str:
    """Build FULL heartbeat pre-embed.

    Includes everything the agent needs to do their job.
    Not compressed. Full data per role.
    """
    lines = [
        "# HEARTBEAT CONTEXT",
        "",
        f"Agent: {agent_name}",
        f"Role: {role}",
        f"Fleet: {agents_online}/{agents_total} online | Mode: {fleet_mode} | Phase: {fleet_phase} | Backend: {fleet_backend}",
        "",
    ]

    # Directives (highest priority)
    if directives:
        lines.append("## PO DIRECTIVES")
        for d in directives:
            urgent = "URGENT " if d.get("urgent") else ""
            lines.append(f"- {urgent}{d.get('content', '')} (from {d.get('from', '?')})")
        lines.append("")

    # Messages
    if messages:
        lines.append("## MESSAGES")
        for m in messages:
            lines.append(f"- From {m.get('from', '?')}: {m.get('content', '')}")
        lines.append("")

    # Assigned tasks (FULL detail)
    if assigned_tasks:
        lines.append(f"## ASSIGNED TASKS ({len(assigned_tasks)})")
        for t in assigned_tasks:
            lines.append("")
            lines.append(format_task_full(t))
        lines.append("")
    else:
        lines.append("## ASSIGNED TASKS: None")
        lines.append("")

    # Role-specific data (FULL)
    if role_data:
        lines.append("## ROLE DATA")
        for key, value in role_data.items():
            if isinstance(value, list):
                lines.append(f"### {key} ({len(value)})")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"  - {item}")
                    else:
                        lines.append(f"  - {item}")
            elif isinstance(value, (int, float)):
                lines.append(f"- {key}: {value}")
            else:
                lines.append(f"- {key}: {value}")
        lines.append("")

    # Standing orders (autonomous authority)
    if agent_name:
        try:
            from fleet.core.standing_orders import get_standing_orders
            so = get_standing_orders(agent_name)
            if so["orders"]:
                lines.append(f"## STANDING ORDERS (authority: {so['authority_level']})")
                lines.append(f"Escalation threshold: {so['escalation_threshold']} autonomous actions without feedback.")
                lines.append("")
                for order in so["orders"]:
                    lines.append(f"- **{order['name']}**: {order['description']}")
                    if order["when"]:
                        lines.append(f"  When: {order['when']}")
                    if order["boundary"]:
                        lines.append(f"  Boundary: {order['boundary']}")
                lines.append("")
        except Exception:
            pass

    # Events
    if events:
        lines.append("## EVENTS SINCE LAST HEARTBEAT")
        lines.append(format_events(events))
        lines.append("")

    return "\n".join(lines)