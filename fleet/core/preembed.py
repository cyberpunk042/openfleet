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
    """Build task pre-embed in autocomplete chain order.

    The 10-section order IS the autocomplete chain — the data arrangement
    drives correct agent behavior. Identity grounding → task focus →
    stage awareness → verbatim anchoring → protocol → contributions →
    phase → action → consequences.

    Standard: docs/milestones/active/standards/context-files-standard.md
    """
    cf = task.custom_fields
    agent_name = cf.agent_name or ""
    stage = cf.task_stage or ""
    readiness = cf.task_readiness or 0
    verbatim = cf.requirement_verbatim or ""
    delivery_phase = cf.delivery_phase or ""
    lines = []

    # § 1. Identity grounding
    lines.append(f"# YOU ARE: {agent_name}")
    lines.append("")

    # § 2. Task focus
    lines.append(f"# YOUR TASK: {task.title}")
    lines.append(f"- ID: {task.id[:8]}")
    lines.append(f"- Priority: {task.priority}")
    lines.append(f"- Type: {cf.task_type or 'unset'}")
    if task.description:
        lines.append(f"- Description: {task.description[:300]}")
    if task.is_blocked:
        lines.append(f"- BLOCKED by: {task.blocked_by_task_ids}")
    if cf.pr_url:
        lines.append(f"- PR: {cf.pr_url}")
    if completeness_summary:
        lines.append(f"- Artifact: {completeness_summary}")
    lines.append("")

    # § 3. Stage awareness
    lines.append(f"# YOUR STAGE: {stage or 'unset'}")
    lines.append("")

    # § 4. Readiness (PO-set, gates dispatch) + Progress (agent-driven, tracks work)
    progress = cf.task_progress or 0
    lines.append(f"# READINESS: {readiness}% (PO-set — gates dispatch)")
    if progress > 0:
        lines.append(f"# PROGRESS: {progress}% (your work — 0=started, 50=halfway, 70=implementation done, 80=challenged, 90=reviewed)")
    lines.append("")

    # § 5. Verbatim requirement (THE ANCHOR)
    lines.append("## VERBATIM REQUIREMENT")
    if verbatim:
        lines.append(f"> {verbatim}")
    else:
        lines.append("*(No verbatim requirement set — ask PO for clarification.)*")
    lines.append("")

    # § 6. Stage protocol (MUST/MUST NOT/CAN)
    if stage:
        try:
            from fleet.core.stage_context import get_stage_instructions
            instructions = get_stage_instructions(stage)
            if instructions:
                lines.append(instructions)
                lines.append("")
        except Exception:
            pass

    # § 7. Inputs from colleagues (contributions received)
    lines.append("## INPUTS FROM COLLEAGUES")
    try:
        from fleet.core.contributions import load_synergy_matrix, get_skip_types
        task_type = cf.task_type or "task"
        skip_types = get_skip_types()
        if agent_name and task_type not in skip_types:
            matrix = load_synergy_matrix()
            specs = matrix.get(agent_name, [])
            required = [s for s in specs if s.priority == "required"]
            if required:
                for s in required:
                    lines.append(f"- **{s.contribution_type}** from {s.role}: check task comments for this input")
                lines.append("")
                lines.append("Missing inputs → `fleet_request_input()`. Do NOT proceed without required contributions.")
            else:
                lines.append("*(No contributions required for this task type.)*")
        else:
            lines.append("*(No contributions required.)*")
    except Exception:
        lines.append("*(Contribution check unavailable.)*")
    lines.append("")

    # § 8. Delivery phase
    if delivery_phase:
        lines.append(f"## DELIVERY PHASE: {delivery_phase}")
        try:
            from fleet.core.phases import get_phase_standards, get_required_contributions
            progression = cf.phase_progression or "standard"
            standards = get_phase_standards(delivery_phase, progression)
            if standards:
                for key, value in standards.items():
                    lines.append(f"- **{key}:** {value}")
        except Exception:
            pass
        lines.append("")

    # § 9. What to do now (action directive)
    lines.append("## WHAT TO DO NOW")
    if stage == "conversation":
        lines.append("Read the verbatim requirement above. Ask specific clarifying questions. Do NOT produce code or solutions.")
    elif stage == "analysis":
        lines.append("Examine the codebase for areas related to the requirement. Produce an analysis_document with specific file references.")
    elif stage == "investigation":
        lines.append("Research multiple approaches (minimum 2). Document options with tradeoffs. Do NOT decide yet.")
    elif stage == "reasoning":
        lines.append("Produce a plan that REFERENCES the verbatim requirement above. Specify target files and acceptance criteria mapping.")
    elif stage == "work":
        lines.append("Execute the confirmed plan. Check contributions above. Call `fleet_read_context()` first, then `fleet_task_accept()`, then implement.")
    else:
        lines.append("Follow the stage protocol above.")
    lines.append("")

    # § 10. What happens when you act (chain awareness)
    lines.append("## WHAT HAPPENS WHEN YOU ACT")
    if stage == "work":
        lines.append("- `fleet_commit()` → git + event + trail (one logical change per commit)")
        lines.append("- `fleet_task_complete()` → push → PR → approval → IRC → Plane → trail → parent eval")
    else:
        lines.append("- `fleet_artifact_create/update()` → Plane HTML + completeness check")
        lines.append("- `fleet_chat()` → board memory + IRC + agent mentions")
    lines.append("- Every tool call fires automatic chains — you don't update multiple places manually.")
    lines.append("")

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