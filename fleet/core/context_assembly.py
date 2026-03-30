"""Context assembly — shared data aggregation for MCP calls and pre-embed.

Single source of truth for assembling context bundles. Used by:
- MCP group calls (fleet_task_context, fleet_heartbeat_context)
- Pre-embedded data (task dispatch, heartbeat injection)

Two assembly functions:
- assemble_task_context: everything about a specific task
- assemble_heartbeat_context: role-specific fleet awareness
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from fleet.core.models import Task, TaskStatus

logger = logging.getLogger(__name__)

# Simple per-cycle cache for task context assembly.
# Cleared at the start of each orchestrator cycle.
_task_context_cache: dict[str, dict] = {}
_cache_cycle_id: str = ""


def clear_context_cache(cycle_id: str = "") -> None:
    """Clear the task context cache. Called at start of each orchestrator cycle."""
    global _task_context_cache, _cache_cycle_id
    _task_context_cache = {}
    _cache_cycle_id = cycle_id


async def assemble_task_context(
    task: Task,
    mc,
    board_id: str,
    plane=None,
    event_store=None,
) -> dict:
    """Assemble the full task context bundle.

    One call, everything about this task aggregated.

    Args:
        task: The Task object from MC.
        mc: MCClient instance.
        board_id: OCMC board ID.
        plane: Optional PlaneClient for Plane data.
        event_store: Optional EventStore for activity history.

    Returns:
        Aggregated task context dict.
    """
    # Check cache
    if task.id in _task_context_cache:
        return _task_context_cache[task.id]

    cf = task.custom_fields
    result: dict[str, Any] = {}

    # ── Task Core ───────────────────────────────────────────────
    result["task"] = {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "priority": task.priority,
        "description": task.description[:500] if task.description else "",
        "is_blocked": task.is_blocked,
        "blocked_by": task.blocked_by_task_ids,
    }

    # ── Custom Fields ───────────────────────────────────────────
    result["custom_fields"] = {
        "readiness": cf.task_readiness,
        "stage": cf.task_stage or "unknown",
        "requirement_verbatim": cf.requirement_verbatim,
        "project": cf.project,
        "branch": cf.branch,
        "pr_url": cf.pr_url,
        "agent_name": cf.agent_name,
        "story_points": cf.story_points,
        "complexity": cf.complexity,
        "task_type": cf.task_type,
        "parent_task": cf.parent_task,
    }

    # ── Methodology ─────────────────────────────────────────────
    try:
        from fleet.core.methodology import get_required_stages, get_next_stage, Stage
        from fleet.core.stage_context import get_stage_instructions, get_stage_summary

        stage = cf.task_stage or "unknown"
        task_type = cf.task_type or "task"
        required = get_required_stages(task_type)
        next_stage = get_next_stage(stage, required) if stage != "unknown" else None

        result["methodology"] = {
            "stage": stage,
            "stage_summary": get_stage_summary(stage),
            "stage_instructions": get_stage_instructions(stage),
            "readiness": cf.task_readiness,
            "required_stages": [s.value for s in required],
            "next_stage": next_stage.value if next_stage else None,
        }
    except Exception:
        result["methodology"] = {"stage": cf.task_stage or "unknown", "readiness": cf.task_readiness}

    # ── Artifact ────────────────────────────────────────────────
    result["artifact"] = {"type": None, "data": None, "completeness": None}

    if plane and cf.plane_issue_id and cf.plane_workspace and cf.plane_project_id:
        try:
            from fleet.core.transpose import from_html, get_artifact_type
            from fleet.core.artifact_tracker import check_artifact_completeness, format_completeness_summary

            issues = await plane.list_issues(cf.plane_workspace, cf.plane_project_id)
            issue = next((i for i in issues if i.id == cf.plane_issue_id), None)
            if issue and issue.description_html:
                obj = from_html(issue.description_html)
                art_type = get_artifact_type(issue.description_html)
                if obj and art_type:
                    completeness = check_artifact_completeness(art_type, obj)
                    result["artifact"] = {
                        "type": art_type,
                        "data": obj,
                        "completeness": {
                            "required_pct": completeness.required_pct,
                            "overall_pct": completeness.overall_pct,
                            "is_complete": completeness.is_complete,
                            "missing_required": completeness.missing_required,
                            "suggested_readiness": completeness.suggested_readiness,
                            "summary": format_completeness_summary(completeness),
                        },
                    }
        except Exception as e:
            logger.debug("artifact assembly error: %s", e)

    # ── Comments ────────────────────────────────────────────────
    result["comments"] = []
    try:
        comments = await mc.list_comments(board_id, task.id)
        result["comments"] = [
            {
                "author": c.agent_name if hasattr(c, 'agent_name') else c.get("agent_name", ""),
                "content": (c.message if hasattr(c, 'message') else c.get("message", ""))[:300],
                "time": str(c.created_at if hasattr(c, 'created_at') else c.get("created_at", "")),
            }
            for c in (comments or [])[:20]
        ]
    except Exception:
        pass  # Comments may not be available

    # ── Activity ────────────────────────────────────────────────
    result["activity"] = []
    if event_store:
        try:
            events = event_store.query(subject=task.id, limit=15)
            result["activity"] = [
                {
                    "type": e.type,
                    "time": e.time,
                    "agent": e.data.get("agent", ""),
                    "summary": (
                        e.data.get("summary")
                        or e.data.get("message")
                        or e.data.get("signal", "")
                    )[:100],
                }
                for e in events
            ]
        except Exception:
            pass

    # ── Related Tasks ───────────────────────────────────────────
    result["related_tasks"] = []
    try:
        all_tasks = await mc.list_tasks(board_id)
        # Children (tasks whose parent_task is this task)
        for t in all_tasks:
            if t.custom_fields.parent_task == task.id:
                result["related_tasks"].append({
                    "id": t.id[:8],
                    "title": t.title[:50],
                    "status": t.status.value,
                    "relation": "child",
                })
        # Parent
        if cf.parent_task:
            parent = next((t for t in all_tasks if t.id == cf.parent_task), None)
            if parent:
                result["related_tasks"].append({
                    "id": parent.id[:8],
                    "title": parent.title[:50],
                    "status": parent.status.value,
                    "relation": "parent",
                })
        # Dependencies
        for dep_id in task.blocked_by_task_ids:
            dep = next((t for t in all_tasks if t.id == dep_id), None)
            if dep:
                result["related_tasks"].append({
                    "id": dep.id[:8],
                    "title": dep.title[:50],
                    "status": dep.status.value,
                    "relation": "blocks_this",
                })
    except Exception:
        pass

    # ── Plane ───────────────────────────────────────────────────
    result["plane"] = None
    if cf.plane_issue_id:
        result["plane"] = {
            "issue_id": cf.plane_issue_id,
            "project_id": cf.plane_project_id,
            "workspace": cf.plane_workspace,
        }

    # Cache the result for this cycle
    _task_context_cache[task.id] = result
    return result


async def assemble_heartbeat_context(
    agent_name: str,
    role: str,
    tasks: list[Task],
    agents: list,
    mc,
    board_id: str,
    event_store=None,
    role_providers: dict | None = None,
    fleet_state: dict | None = None,
) -> dict:
    """Assemble the heartbeat context bundle — role-specific.

    Args:
        agent_name: The agent's name.
        role: The agent's role (fleet-ops, project-manager, etc.)
        tasks: All tasks from the board.
        agents: All agents.
        mc: MCClient instance.
        board_id: OCMC board ID.
        event_store: Optional EventStore for events since last heartbeat.
        role_providers: Optional dict of role → provider functions.
        fleet_state: Optional fleet control state dict.

    Returns:
        Aggregated heartbeat context dict.
    """
    result: dict[str, Any] = {"agent": agent_name, "role": role}

    # ── Assigned Tasks Summary ──────────────────────────────────
    result["assigned_tasks"] = []
    for t in tasks:
        if t.custom_fields.agent_name == agent_name and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS):
            result["assigned_tasks"].append({
                "id": t.id[:8],
                "title": t.title[:50],
                "status": t.status.value,
                "readiness": t.custom_fields.task_readiness,
                "stage": t.custom_fields.task_stage or "unknown",
            })

    # ── Messages ────────────────────────────────────────────────
    result["messages"] = []
    try:
        memory = await mc.list_memory(board_id, limit=20)
        for m in memory:
            tags = m.tags if hasattr(m, 'tags') else m.get('tags', [])
            if f"mention:{agent_name}" in tags or "mention:all" in tags:
                result["messages"].append({
                    "from": m.source if hasattr(m, 'source') else m.get('source', ''),
                    "content": (m.content if hasattr(m, 'content') else m.get('content', ''))[:200],
                    "tags": tags,
                })
        # Directives
        from fleet.core.directives import parse_directives
        directives = parse_directives(memory)
        result["directives"] = [
            {"content": d.content, "from": d.source, "urgent": d.urgent}
            for d in directives
            if d.target_agent in (agent_name, "all", None)
        ]
    except Exception:
        result["directives"] = []

    # ── Events Since Last ───────────────────────────────────────
    result["events"] = []
    if event_store:
        try:
            from fleet.core.event_router import build_agent_feed
            feed = build_agent_feed(agent_name, event_store, limit=10)
            result["events"] = [
                {
                    "type": e.type,
                    "time": e.time,
                    "agent": e.data.get("agent", ""),
                    "summary": (
                        e.data.get("summary")
                        or e.data.get("message")
                        or e.data.get("signal", "")
                    )[:80],
                }
                for e in feed
            ]
        except Exception:
            pass

    # ── Role-Specific Data ──────────────────────────────────────
    result["role_data"] = {}
    if role_providers and role in role_providers:
        try:
            provider = role_providers[role]
            result["role_data"] = await provider(
                agent_name=agent_name,
                tasks=tasks,
                agents=agents,
                mc=mc,
                board_id=board_id,
            )
        except Exception as e:
            logger.debug("role provider error for %s: %s", role, e)

    # ── Fleet State ─────────────────────────────────────────────
    result["fleet_state"] = fleet_state or {}
    result["agents_online"] = sum(1 for a in agents if a.status == "online" and "Gateway" not in a.name)
    result["agents_total"] = sum(1 for a in agents if "Gateway" not in a.name)

    return result