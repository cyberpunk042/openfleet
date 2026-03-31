"""Fleet orchestrator — the autonomous brain.

Runs in a loop, driving the fleet through the task lifecycle:
1. Process pending approvals (auto-approve high-confidence)
2. Transition approved review tasks to done
3. Dispatch unblocked inbox tasks to assigned agents
4. Evaluate parent tasks when all children complete
5. Wake driver agents (PM, fleet-ops) on heartbeat

Usage:
  python -m fleet daemon orchestrator [--interval 30]
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from fleet.core.agent_lifecycle import AgentStatus, FleetLifecycle
from fleet.core.change_detector import ChangeDetector
from fleet.core.models import Approval, Task, TaskStatus
from fleet.core.notification_router import NotificationRouter
from fleet.infra.config_loader import ConfigLoader
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient

# Global state (persists across cycles)
_fleet_lifecycle = FleetLifecycle()
_notification_router = NotificationRouter(cooldown_seconds=300)
_change_detector = ChangeDetector()

from fleet.core.budget_monitor import BudgetMonitor
from fleet.core.doctor import DoctorReport, AgentHealth, ResponseAction, run_doctor_cycle
from fleet.core.directives import parse_directives, format_directive_for_agent
from fleet.core.fleet_mode import FleetControlState, read_fleet_control, should_dispatch as fleet_should_dispatch, get_active_agents_for_phase
from fleet.core.teaching import adapt_lesson, format_lesson_for_injection, DiseaseCategory
_budget_monitor = BudgetMonitor()


# ─── Cycle State ─────────────────────────────────────────────────────────


@dataclass
class OrchestratorState:
    """Track what happened each cycle for logging."""

    approvals_processed: int = 0
    tasks_transitioned: int = 0
    tasks_dispatched: int = 0
    parents_evaluated: int = 0
    drivers_woken: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def total_actions(self) -> int:
        return (
            self.approvals_processed
            + self.tasks_transitioned
            + self.tasks_dispatched
            + self.parents_evaluated
            + self.drivers_woken
        )


# ─── Main Cycle ──────────────────────────────────────────────────────────


async def run_orchestrator_cycle(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    config: dict,
    dry_run: bool = False,
) -> OrchestratorState:
    """Execute one orchestrator cycle."""
    from fleet.core.effort_profiles import get_active_profile_name, get_profile

    state = OrchestratorState()

    # Clear context assembly cache for this cycle
    try:
        from fleet.core.context_assembly import clear_context_cache
        clear_context_cache(cycle_id=str(datetime.now().timestamp()))
    except Exception:
        pass

    # Check effort profile — fleet may be paused or in minimal mode
    profile_name = config.get("effort_profile", "full")
    profile = get_profile(profile_name)
    if profile and not profile.allow_dispatch:
        return state  # Profile says don't dispatch — skip cycle

    # Override max dispatch from profile
    if profile:
        config["max_dispatch_per_cycle"] = min(
            config.get("max_dispatch_per_cycle", 2),
            profile.max_dispatch_per_cycle,
        )

    tasks = await mc.list_tasks(board_id)
    agents = await mc.list_agents()
    agent_map = {a.id: a for a in agents if "Gateway" not in a.name}
    agent_name_map = {a.name: a for a in agents if "Gateway" not in a.name}
    now = datetime.now()

    # Read fleet control state (Work Mode, Cycle Phase, Backend Mode)
    try:
        board_data = await mc.get_board(board_id)
        fleet_state = read_fleet_control(board_data if isinstance(board_data, dict) else {})
    except Exception:
        fleet_state = FleetControlState()  # defaults if board read fails

    # Detect mode changes and emit events
    global _previous_fleet_state
    if _previous_fleet_state is not None:
        changes_detected = []
        if fleet_state.work_mode != _previous_fleet_state.work_mode:
            changes_detected.append(f"work_mode: {_previous_fleet_state.work_mode} → {fleet_state.work_mode}")
        if fleet_state.cycle_phase != _previous_fleet_state.cycle_phase:
            changes_detected.append(f"cycle_phase: {_previous_fleet_state.cycle_phase} → {fleet_state.cycle_phase}")
        if fleet_state.backend_mode != _previous_fleet_state.backend_mode:
            changes_detected.append(f"backend_mode: {_previous_fleet_state.backend_mode} → {fleet_state.backend_mode}")
        if changes_detected:
            state.notes.append(f"Fleet mode CHANGED: {'; '.join(changes_detected)}")
            try:
                from fleet.core.events import create_event, EventStore
                store = EventStore()
                store.append(create_event(
                    event_type="fleet.system.mode_changed",
                    source="fleet/cli/orchestrator",
                    old_work_mode=_previous_fleet_state.work_mode,
                    new_work_mode=fleet_state.work_mode,
                    old_cycle_phase=_previous_fleet_state.cycle_phase,
                    new_cycle_phase=fleet_state.cycle_phase,
                    old_backend_mode=_previous_fleet_state.backend_mode,
                    new_backend_mode=fleet_state.backend_mode,
                    set_by=fleet_state.updated_by or "unknown",
                ))
            except Exception:
                pass  # Event emission must not break orchestrator
    _previous_fleet_state = fleet_state

    # Fleet mode gate — check if dispatch is allowed
    if not fleet_should_dispatch(fleet_state):
        state.notes.append(f"Fleet mode: {fleet_state.work_mode} — dispatch paused")
        return state

    # Detect changes since last cycle
    changes = _change_detector.detect(tasks, now)

    # Update fleet lifecycle tracker with current activity
    active_agents: dict[str, str] = {}
    for t in tasks:
        if t.status == TaskStatus.IN_PROGRESS and t.custom_fields.agent_name:
            active_agents[t.custom_fields.agent_name] = t.id
    for a in agents:
        if "Gateway" not in a.name:
            _fleet_lifecycle.get_or_create(a.name)
    _fleet_lifecycle.update_all(now, active_agents)

    # Step 0: Refresh agent context files — pre-embed full data for heartbeats
    await _refresh_agent_contexts(tasks, agents, board_id, mc, fleet_state)

    # Step 1: Security scan — check new/changed tasks for suspicious content
    await _security_scan(mc, irc, board_id, tasks, changes, state, dry_run)

    # Step 2: Doctor — immune system observation, detection, response
    doctor_report = await _run_doctor(tasks, agents, state, config, dry_run)

    # Step 3: Ensure review tasks have approvals (so fleet-ops can review them)
    await _ensure_review_approvals(mc, board_id, tasks, state, dry_run)

    # Step 4: Wake drivers — PM for unassigned tasks, fleet-ops for approvals
    await _wake_drivers(mc, irc, board_id, tasks, agents, agent_name_map, state, dry_run)

    # Step 5: Dispatch unblocked inbox tasks to assigned agents
    # (respects doctor report — skips agents flagged by immune system)
    # (respects fleet control state — filters by cycle phase active agents)
    await _dispatch_ready_tasks(mc, irc, board_id, tasks, agent_map, state, dry_run, config,
                                doctor_report=doctor_report, fleet_state=fleet_state)

    # Step 6: Process directives from board memory
    await _process_directives(mc, irc, board_id, state, dry_run)

    # Step 7: Evaluate parent task completion (all children done → parent to review)
    await _evaluate_parents(mc, irc, board_id, tasks, state, dry_run)

    # Step 8: Health check — detect stuck tasks, offline agents, stale deps
    await _health_check(mc, irc, board_id, tasks, agents, state, dry_run)

    # NOTE: Heartbeats are managed by the GATEWAY, not the orchestrator.
    # The orchestrator NEVER creates Claude Code sessions directly.
    # The gateway's heartbeat system (HEARTBEAT.md, heartbeat_config.every)
    # handles agent cycling at controlled intervals.
    # The orchestrator only: dispatch tasks, evaluate parents, check health.

    return state


# ─── Step 0: Refresh Agent Contexts ─────────────────────────────────────


async def _refresh_agent_contexts(
    tasks: list[Task],
    agents: list,
    board_id: str,
    mc,
    fleet_state,
) -> None:
    """Refresh every agent's context/ files with full pre-embedded data.

    Runs every orchestrator cycle. The gateway reads these files when
    the agent heartbeats. FULL data, not compressed.
    """
    try:
        from fleet.core.preembed import build_heartbeat_preembed, build_task_preembed
        from fleet.core.context_writer import write_heartbeat_context, write_task_context
        from fleet.core.role_providers import get_role_provider
        from fleet.core.directives import parse_directives

        # Get messages and directives
        try:
            memory = await mc.list_memory(board_id, limit=30)
        except Exception:
            memory = []

        directives = []
        try:
            directives = [
                {"content": d.content, "from": d.source, "urgent": d.urgent}
                for d in parse_directives(memory)
            ]
        except Exception:
            pass

        fleet_state_dict = {
            "work_mode": fleet_state.work_mode if fleet_state else "",
            "cycle_phase": fleet_state.cycle_phase if fleet_state else "",
            "backend_mode": fleet_state.backend_mode if fleet_state else "",
        }

        online_count = sum(1 for a in agents if a.status == "online" and "Gateway" not in a.name)
        total_count = sum(1 for a in agents if "Gateway" not in a.name)

        for agent in agents:
            if "Gateway" in agent.name:
                continue

            agent_name = agent.name

            # Agent's assigned tasks
            my_tasks = [
                t for t in tasks
                if t.custom_fields.agent_name == agent_name
                and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS)
            ]

            # Messages for this agent
            agent_messages = []
            for m in memory:
                tags = m.tags if hasattr(m, 'tags') else m.get('tags', [])
                if f"mention:{agent_name}" in tags or "mention:all" in tags:
                    content = m.content if hasattr(m, 'content') else m.get('content', '')
                    source = m.source if hasattr(m, 'source') else m.get('source', '')
                    agent_messages.append({"from": source, "content": content})

            # Agent directives
            agent_directives = [
                d for d in directives
                if d.get("from") == "human"  # all directives are from human
            ]

            # Role-specific data
            role_data = {}
            try:
                role = agent_name  # role = agent name for provider lookup
                provider = get_role_provider(role)
                role_data = await provider(
                    agent_name=agent_name,
                    tasks=tasks,
                    agents=agents,
                    mc=mc,
                    board_id=board_id,
                )
            except Exception:
                pass

            # Build FULL heartbeat pre-embed
            heartbeat_text = build_heartbeat_preembed(
                agent_name=agent_name,
                role=agent_name,
                assigned_tasks=my_tasks,
                messages=agent_messages if agent_messages else None,
                directives=agent_directives if agent_directives else None,
                role_data=role_data if role_data else None,
                fleet_mode=fleet_state_dict.get("work_mode", ""),
                fleet_phase=fleet_state_dict.get("cycle_phase", ""),
                fleet_backend=fleet_state_dict.get("backend_mode", ""),
                agents_online=online_count,
                agents_total=total_count,
            )

            write_heartbeat_context(agent_name, heartbeat_text)

            # Also write task context for in-progress tasks
            in_progress = [t for t in my_tasks if t.status == TaskStatus.IN_PROGRESS]
            if in_progress:
                task_text = build_task_preembed(in_progress[0])
                write_task_context(agent_name, task_text)

    except Exception:
        pass  # Context refresh must not break orchestrator cycle


# ─── Step 2: Doctor — Immune System ─────────────────────────────────────

# Persistent health profiles — survive across orchestrator cycles
_doctor_health_profiles: dict[str, AgentHealth] = {}
_doctor_tool_calls: dict[str, list[str]] = {}  # agent_name → recent tool calls

# Previous fleet control state — for detecting mode changes
_previous_fleet_state: FleetControlState | None = None


async def _run_doctor(
    tasks: list[Task],
    agents: list,
    state: OrchestratorState,
    config: dict,
    dry_run: bool,
) -> DoctorReport:
    """Run the doctor's observation cycle.

    Hidden from agents. Produces a report the orchestrator uses to
    adjust dispatch and trigger responses.
    """
    try:
        report = await run_doctor_cycle(
            tasks=tasks,
            agents=agents,
            tool_call_history=_doctor_tool_calls,
            health_profiles=_doctor_health_profiles,
            config=config.get("doctor", {}),
        )

        if report.has_findings:
            for detection in report.detections:
                state.notes.append(
                    f"Doctor: {detection.disease.value} detected on "
                    f"{detection.agent_name} ({detection.signal})"
                )

        if report.has_interventions:
            for intervention in report.interventions:
                if dry_run:
                    state.notes.append(
                        f"Doctor [dry_run]: WOULD {intervention.action.value} "
                        f"{intervention.agent_name} ({intervention.reason})"
                    )
                    continue

                state.notes.append(
                    f"Doctor: {intervention.action.value} "
                    f"{intervention.agent_name} ({intervention.reason})"
                )

                # Execute the response
                await _execute_doctor_intervention(intervention, agents, state)

        return report

    except Exception as exc:
        state.errors.append(f"Doctor error: {exc}")
        return DoctorReport()


async def _execute_doctor_intervention(
    intervention,
    agents: list,
    state: OrchestratorState,
) -> None:
    """Execute a doctor intervention — prune, compact, or teach.

    This is where the immune system's decisions become real actions
    through the gateway.
    """
    from fleet.infra.gateway_client import (
        prune_agent,
        force_compact,
        inject_content,
    )

    # Find the agent's session key
    agent = next(
        (a for a in agents if a.name == intervention.agent_name and a.session_key),
        None,
    )
    if not agent:
        state.errors.append(
            f"Doctor: can't find session for {intervention.agent_name}"
        )
        return

    try:
        if intervention.action == ResponseAction.PRUNE:
            ok = await prune_agent(agent.session_key)
            if ok:
                state.notes.append(
                    f"Doctor: PRUNED {intervention.agent_name} — "
                    f"session killed, will regrow fresh"
                )

        elif intervention.action == ResponseAction.FORCE_COMPACT:
            ok = await force_compact(agent.session_key)
            if ok:
                state.notes.append(
                    f"Doctor: COMPACTED {intervention.agent_name} — "
                    f"context reduced"
                )

        elif intervention.action == ResponseAction.TRIGGER_TEACHING:
            # Create adapted lesson from the intervention context
            disease = intervention.disease or DiseaseCategory.DEVIATION
            context = intervention.lesson_context or {}
            lesson = adapt_lesson(
                disease=disease,
                agent_name=intervention.agent_name,
                task_id=intervention.task_id,
                context=context,
            )
            # Format and inject into agent session
            lesson_text = format_lesson_for_injection(lesson)
            ok = await inject_content(agent.session_key, lesson_text)
            if ok:
                state.notes.append(
                    f"Doctor: TEACHING {intervention.agent_name} — "
                    f"lesson injected ({disease.value})"
                )

    except Exception as exc:
        state.errors.append(
            f"Doctor intervention failed for {intervention.agent_name}: {exc}"
        )


# ─── Step 6: Directives ─────────────────────────────────────────────────


async def _process_directives(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Process PO directives from board memory."""
    try:
        memory = await mc.list_memory(board_id, limit=20)
        directives = parse_directives(memory)

        for directive in directives:
            target = directive.target_agent or "all"
            if dry_run:
                state.notes.append(
                    f"Directive [dry_run]: WOULD route to {target}: "
                    f"{directive.content[:50]}"
                )
                continue

            state.notes.append(
                f"Directive: → {target}: {directive.content[:50]}"
            )

            # Notify via IRC
            urgency = "🚨 " if directive.urgent else ""
            await _notify(
                irc, "#fleet",
                f"[directive] {urgency}{directive.source} → {target}: "
                f"{directive.content[:80]}",
            )

    except Exception as exc:
        state.errors.append(f"Directive processing error: {exc}")


# ─── Step 1: Security Scan ──────────────────────────────────────────────


async def _security_scan(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    changes,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Scan newly created or changed tasks for suspicious content."""
    from fleet.core.behavioral_security import scan_task
    from fleet.core.change_detector import ChangeSet

    if not isinstance(changes, ChangeSet) or not changes.has_changes:
        return

    for change in changes.changes:
        if change.change_type not in ("task_created", "task_status_changed"):
            continue

        task = next((t for t in tasks if t.id == change.task_id), None)
        if not task:
            continue

        scan = scan_task(task.title, task.description or "")
        if not scan.has_findings:
            continue

        for finding in scan.findings:
            if dry_run:
                print(f"  [dry_run] SECURITY: {finding.severity} — {finding.title} "
                      f"on task {task.id[:8]}")
                continue

            # Alert via IRC
            await _notify(irc, "#alerts",
                f"[security] {finding.severity.upper()}: {finding.title} "
                f"— task {task.id[:8]} {task.title[:30]}")

            # Notify human via ntfy for critical findings
            if finding.severity in ("critical", "high"):
                await _notify_human(
                    title=f"Security: {finding.title}",
                    message=f"Task: {task.title[:50]}\n{finding.evidence}\n{finding.recommendation}",
                    event_type="security_alert",
                    severity=finding.severity,
                )

            # Set security_hold if needed
            if finding.should_hold:
                try:
                    await mc.update_task(
                        board_id, task.id,
                        custom_fields={"security_hold": "true"},
                        comment=f"**Security Hold** by orchestrator: {finding.title}\n{finding.recommendation}",
                    )
                except Exception:
                    pass


# ─── Step 6: Health Check ───────────────────────────────────────────────


async def _health_check(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    agents: list,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Run fleet health assessment and auto-resolve issues."""
    from fleet.core.health import assess_fleet_health
    from fleet.core.self_healing import plan_healing_actions

    report = assess_fleet_health(tasks, agents)

    if report.healthy:
        return

    actions = plan_healing_actions(report, agents)

    for action in actions:
        if action.escalate:
            await _notify_human(
                title=f"Fleet health: {action.issue_title}",
                message=action.escalate_reason,
                event_type="escalation",
            )
            continue

        if not action.task_title:
            continue

        if dry_run:
            print(f"  [dry_run] HEALTH: would create task for {action.target_agent}: "
                  f"{action.task_title[:40]}")
            continue

        # Create remediation task
        try:
            target_agents = await mc.list_agents()
            target_id = next(
                (a.id for a in target_agents if a.name == action.target_agent), None
            )
            await mc.create_task(
                board_id,
                title=action.task_title,
                description=action.task_description,
                priority=action.priority,
                assigned_agent_id=target_id,
                custom_fields={"agent_name": action.target_agent, "task_type": "subtask"},
            )
        except Exception as e:
            state.errors.append(f"health action: {e}")


# ─── Step 2: Ensure Review Tasks Have Approvals ─────────────────────────
#
# The orchestrator does NOT approve tasks. That is fleet-ops' job as board lead.
# MC auto-assigns review tasks to the board lead (fleet-ops).
# fleet-ops reviews the work, runs quality checks, and approves or rejects.
#
# The orchestrator only ensures review tasks have pending approvals created,
# so that fleet-ops has something to evaluate during their heartbeat.
#


async def _ensure_review_approvals(
    mc: MCClient,
    board_id: str,
    tasks: list[Task],
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Create approvals for review tasks that don't have any.

    Agents sometimes move tasks to review without calling fleet_task_complete
    (e.g., due to MCP env var issues). This ensures those tasks aren't stuck.
    """
    review_tasks = [t for t in tasks if t.status == TaskStatus.REVIEW]
    if not review_tasks:
        return

    try:
        all_approvals = await mc.list_approvals(board_id)
    except Exception:
        return

    tasks_with_approvals = {a.task_id for a in all_approvals}

    for task in review_tasks:
        if task.id in tasks_with_approvals:
            continue

        if dry_run:
            print(f"  [dry_run] WOULD create approval for orphaned review: "
                  f"{task.id[:8]} {task.title[:40]}")
            continue

        try:
            await mc.create_approval(
                board_id,
                task_ids=[task.id],
                action_type="task_completion",
                confidence=85.0,
                rubric_scores={"completeness": 80, "quality": 80},
                reason=f"Auto-created by orchestrator — task in review without approval",
            )
        except Exception:
            pass  # Non-critical, will retry next cycle


# ─── Step 2: Transition Approved Reviews ─────────────────────────────────


async def _transition_approved_reviews(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Move review tasks to done if they have approved approvals."""
    review_tasks = [t for t in tasks if t.status == TaskStatus.REVIEW]

    for task in review_tasks:
        try:
            has_approval = await mc.task_has_approved_approval(board_id, task.id)
            if has_approval:
                if dry_run:
                    print(f"  [dry_run] WOULD transition {task.id[:8]} → done: "
                          f"{task.title[:40]}")
                else:
                    await mc.update_task(
                        board_id, task.id,
                        status="done",
                        comment="**Auto-transitioned** to done — approval granted.",
                    )
                    await _notify(irc, "#fleet",
                        f"[orchestrator] \u2705 DONE: {task.title[:50]}")
                state.tasks_transitioned += 1
        except Exception as e:
            state.errors.append(f"transition {task.id[:8]}: {e}")


# ─── Step 2: Wake Fleet-Ops for Pending Reviews ─────────────────────────

_last_review_wake: Optional[datetime] = None


# Cooldown tracking for driver waking
_last_pm_wake: datetime | None = None
_last_ops_wake: datetime | None = None


async def _wake_drivers(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    agents: list,
    agent_name_map: dict,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Wake PM and fleet-ops when there's work that needs their attention.

    PM wakes when: unassigned inbox tasks exist
    Fleet-ops wakes when: pending approvals exist

    Waking = inject pre-embedded data into agent's session via gateway.
    The agent then heartbeats with full awareness.
    """
    global _last_pm_wake, _last_ops_wake
    now = datetime.now()

    # ── Wake PM for unassigned tasks ────────────────────────────
    unassigned = [t for t in tasks if t.status == TaskStatus.INBOX and not t.custom_fields.agent_name]
    if unassigned and (not _last_pm_wake or (now - _last_pm_wake).total_seconds() > 120):
        pm = agent_name_map.get("project-manager")
        if pm and pm.session_key:
            if dry_run:
                state.notes.append(f"[dry_run] WOULD wake PM for {len(unassigned)} unassigned tasks")
            else:
                try:
                    from fleet.core.preembed import build_heartbeat_preembed, format_task_full
                    from fleet.infra.gateway_client import inject_content

                    # Build PM-specific wake data with unassigned task details
                    task_details = "\n\n".join(format_task_full(t) for t in unassigned[:10])
                    wake_msg = (
                        f"# PM WAKE — {len(unassigned)} UNASSIGNED TASKS\n\n"
                        f"You have {len(unassigned)} unassigned inbox tasks.\n"
                        f"ASSIGN agents to these tasks NOW.\n\n"
                        f"{task_details}"
                    )
                    await inject_content(pm.session_key, wake_msg)
                    state.notes.append(f"Woke PM for {len(unassigned)} unassigned tasks")
                    await _notify(irc, "#fleet", f"[orchestrator] Woke PM — {len(unassigned)} unassigned tasks")
                except Exception as e:
                    state.errors.append(f"Failed to wake PM: {e}")
            _last_pm_wake = now

    # ── Wake fleet-ops for pending approvals ────────────────────
    review_tasks = [t for t in tasks if t.status == TaskStatus.REVIEW]
    if review_tasks and (not _last_ops_wake or (now - _last_ops_wake).total_seconds() > 120):
        ops = agent_name_map.get("fleet-ops")
        if ops and ops.session_key:
            if dry_run:
                state.notes.append(f"[dry_run] WOULD wake fleet-ops for {len(review_tasks)} reviews")
            else:
                try:
                    from fleet.infra.gateway_client import inject_content

                    wake_msg = (
                        f"# FLEET-OPS WAKE — {len(review_tasks)} PENDING REVIEWS\n\n"
                        f"You have {len(review_tasks)} tasks awaiting review.\n"
                        f"PROCESS approvals NOW.\n"
                    )
                    await inject_content(ops.session_key, wake_msg)
                    state.notes.append(f"Woke fleet-ops for {len(review_tasks)} reviews")
                    await _notify(irc, "#reviews", f"[orchestrator] Woke fleet-ops — {len(review_tasks)} pending reviews")
                except Exception as e:
                    state.errors.append(f"Failed to wake fleet-ops: {e}")
            _last_ops_wake = now


async def _wake_lead_for_reviews(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    agent_name_map: dict,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Wake fleet-ops when there are pending approvals to process.

    More urgent than the 30-min heartbeat — checks every 5 minutes.
    If fleet-ops already has an active review task, skips.
    """
    global _last_review_wake

    review_count = sum(1 for t in tasks if t.status == TaskStatus.REVIEW)
    if review_count == 0:
        return

    now = datetime.now()
    if _last_review_wake and (now - _last_review_wake).total_seconds() < 300:
        return

    fleet_ops = agent_name_map.get("fleet-ops")
    if not fleet_ops or not fleet_ops.session_key:
        return

    # Check if fleet-ops already has an active task
    has_active = any(
        t.custom_fields.agent_name == "fleet-ops"
        and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS)
        for t in tasks
    )
    if has_active:
        _last_review_wake = now
        return

    if dry_run:
        print(f"  [dry_run] WOULD wake fleet-ops for {review_count} pending reviews")
        _last_review_wake = now
        return

    # NOTE: Do NOT call _send_chat here. MC auto-assigns review tasks to
    # fleet-ops (board lead). The gateway wakes fleet-ops on its heartbeat.
    # We just log that reviews are pending — no session creation.
    try:
        pending = await mc.list_approvals(board_id, status="pending")
        if pending:
            _last_review_wake = now
            await _notify(irc, "#reviews",
                f"[orchestrator] {len(pending)} pending approvals for fleet-ops")
    except Exception:
        pass


# ─── Step 3: Dispatch Ready Tasks ───────────────────────────────────────


async def _dispatch_ready_tasks(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    agent_map: dict,
    state: OrchestratorState,
    dry_run: bool,
    config: dict | None = None,
    doctor_report: DoctorReport | None = None,
    fleet_state: FleetControlState | None = None,
) -> None:
    """Find unblocked inbox tasks with assigned agents and dispatch them."""
    from fleet.cli.dispatch import _run_dispatch
    from fleet.core.task_scoring import rank_tasks

    # ERROR CHECK — detect agent errors (rate limits, API outages)
    from fleet.core.error_reporter import detect_rate_limit, detect_api_outage
    if detect_rate_limit():
        state.errors.append("RATE LIMIT detected — backing off dispatch")
        await _notify(irc, "#alerts", "[orchestrator] Rate limit detected — reducing dispatch")
        return  # Skip this cycle
    if detect_api_outage():
        state.errors.append("API OUTAGE detected — multiple agents reporting errors")
        await _notify(irc, "#alerts", "[orchestrator] API outage — pausing dispatch")
        await _notify_human(
            title="Fleet: API outage detected",
            message="Multiple agents reporting errors. Fleet pausing dispatch.",
            event_type="escalation",
        )
        return

    # BUDGET CHECK — read real quota from Claude OAuth API (rate-limited, cached 5 min)
    safe, reason = _budget_monitor.check_quota()
    if not safe:
        state.errors.append(f"BUDGET PAUSE: {reason}")
        await _notify(irc, "#alerts", f"[orchestrator] BUDGET: {reason}")
        await _notify_human(
            title="Fleet budget critical",
            message=reason,
            event_type="escalation",
        )
        return  # Do NOT dispatch

    # Check for threshold alerts (50%, 70%, 80%, 90%)
    for alert in _budget_monitor.get_alerts():
        await _notify(irc, "#alerts", f"[budget] {alert.severity}: {alert.title}")
        if alert.severity == "critical":
            await _notify_human(
                title=alert.title,
                message=alert.message,
                event_type="escalation",
            )

    # Methodology gate: separate work-ready tasks from earlier-stage tasks
    all_inbox = [
        t for t in tasks
        if t.status == TaskStatus.INBOX
        and t.assigned_agent_id
        and not t.is_blocked
    ]

    # Work-ready tasks (readiness >= 99) — dispatched for execution
    inbox_tasks = [t for t in all_inbox if t.custom_fields.task_readiness >= 99]

    # Earlier-stage tasks — not dispatched for work, but tracked
    methodology_pending = [t for t in all_inbox if t.custom_fields.task_readiness < 99]
    if methodology_pending:
        stages = {}
        for t in methodology_pending:
            stage = t.custom_fields.task_stage or "no-stage"
            stages.setdefault(stage, 0)
            stages[stage] += 1
        stage_summary = ", ".join(f"{s}:{n}" for s, n in sorted(stages.items()))
        state.notes.append(
            f"Methodology: {len(methodology_pending)} tasks below readiness 99% "
            f"({stage_summary})"
        )

    # Smart scoring — considers priority, dependency chain, wait time, task type
    scored = rank_tasks(inbox_tasks, tasks)
    inbox_tasks = [s.task for s in scored]

    # Track busy agents (those with in_progress tasks)
    busy_agent_ids = {
        t.assigned_agent_id
        for t in tasks
        if t.status == TaskStatus.IN_PROGRESS and t.assigned_agent_id
    }

    # Doctor's skip list — agents flagged by immune system
    if doctor_report:
        doctor_skip_agents = set()
        for skip_name in doctor_report.agents_to_skip:
            for aid, agent in agent_map.items():
                if agent.name == skip_name:
                    doctor_skip_agents.add(aid)
        busy_agent_ids |= doctor_skip_agents

    # Fleet control — cycle phase agent filter
    if fleet_state:
        phase_agents = get_active_agents_for_phase(fleet_state)
        if phase_agents is not None:
            # Only allow agents in the phase's active list
            phase_skip = set()
            for aid, agent in agent_map.items():
                if agent.name not in phase_agents:
                    phase_skip.add(aid)
            busy_agent_ids |= phase_skip
            if phase_skip:
                skipped_names = [agent_map[aid].name for aid in phase_skip if aid in agent_map]
                state.notes.append(
                    f"Fleet phase '{fleet_state.cycle_phase}': "
                    f"{len(skipped_names)} agents inactive"
                )

    # SAFETY: Max 2 dispatches per cycle to prevent session storms
    max_dispatch = (config or {}).get("max_dispatch_per_cycle", 2)

    for task in inbox_tasks:
        if state.tasks_dispatched >= max_dispatch:
            break  # Remaining tasks wait for next cycle

        if task.assigned_agent_id in busy_agent_ids:
            continue

        agent = agent_map.get(task.assigned_agent_id)
        if not agent or not agent.session_key:
            continue

        project = task.custom_fields.project or ""

        if dry_run:
            print(f"  [dry_run] WOULD dispatch {task.id[:8]} → {agent.name}: "
                  f"{task.title[:40]}")
            state.tasks_dispatched += 1
            busy_agent_ids.add(task.assigned_agent_id)
            continue

        try:
            result = await _run_dispatch(agent.name, task.id, project)
            if result == 0:
                state.tasks_dispatched += 1
                busy_agent_ids.add(task.assigned_agent_id)

                # Inject task pre-embed into agent session + context file
                try:
                    from fleet.core.preembed import build_task_preembed
                    from fleet.core.context_writer import write_task_context
                    from fleet.infra.gateway_client import inject_content
                    preembed = build_task_preembed(task)
                    await inject_content(agent.session_key, preembed)
                    write_task_context(agent.name, preembed)
                except Exception:
                    pass  # Pre-embed injection must not break dispatch

                await _notify(irc, "#fleet",
                    f"[orchestrator] \U0001f680 DISPATCHED: "
                    f"{task.title[:50]} \u2192 {agent.name}")
                await _notify_human(
                    title=f"Dispatched: {task.title[:40]} → {agent.name}",
                    message=f"Task dispatched to {agent.name}. Priority: {task.priority}.",
                    event_type="task_done",
                )
        except Exception as e:
            state.errors.append(f"dispatch {task.id[:8]}: {e}")


# ─── Step 4: Evaluate Parent Completion ──────────────────────────────────


async def _evaluate_parents(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Check if parent tasks can move to review when all children complete."""
    # Build parent → children mapping
    parent_children: dict[str, list[Task]] = {}
    for task in tasks:
        parent_id = task.custom_fields.parent_task
        if parent_id:
            parent_children.setdefault(parent_id, []).append(task)

    task_map = {t.id: t for t in tasks}

    for parent_id, children in parent_children.items():
        parent = task_map.get(parent_id)
        if not parent:
            continue

        # Skip if parent is already done or in review
        if parent.status in (TaskStatus.DONE, TaskStatus.REVIEW):
            continue

        # Check if ALL children are done
        all_done = all(c.status == TaskStatus.DONE for c in children)

        if all_done and len(children) > 0:
            child_summary = ", ".join(f"{c.title[:30]}" for c in children[:5])
            if len(children) > 5:
                child_summary += f" (+{len(children) - 5} more)"

            if dry_run:
                print(f"  [dry_run] WOULD move parent {parent_id[:8]} → review: "
                      f"{parent.title[:40]} ({len(children)} children done)")
            else:
                try:
                    await mc.update_task(
                        board_id, parent.id,
                        status="review",
                        comment=(
                            f"**All {len(children)} subtasks completed.** "
                            f"Moving to review.\n\n"
                            f"Subtasks: {child_summary}"
                        ),
                    )
                    await _notify(irc, "#fleet",
                        f"[orchestrator] \U0001f4e6 PARENT READY: "
                        f"{parent.title[:50]} ({len(children)} children done)")
                    # Notify human via ntfy — sprint milestone
                    await _notify_human(
                        title=f"Sprint milestone: {parent.title[:50]}",
                        message=f"All {len(children)} subtasks completed. Parent task ready for review.",
                        event_type="sprint_milestone",
                    )
                except Exception as e:
                    state.errors.append(f"parent {parent_id[:8]}: {e}")
            state.parents_evaluated += 1


# NOTE: _lifecycle_heartbeats REMOVED.
# Heartbeats are managed by the GATEWAY's own heartbeat system.
# The orchestrator MUST NEVER call _send_chat or create sessions directly.
# See docs/milestones/catastrophic-usage-drain-investigation.md for why.


# ─── Helper ──────────────────────────────────────────────────────────────


async def _notify(irc: IRCClient, channel: str, message: str) -> None:
    """Best-effort IRC notification."""
    try:
        await irc.notify(channel, message)
    except Exception:
        pass


async def _notify_human(
    title: str,
    message: str,
    event_type: str = "info",
    source_agent: str = "orchestrator",
    url: str = "",
    severity: str = "",
) -> None:
    """Smart notification to human via ntfy with routing and deduplication."""
    notification = _notification_router.classify(
        event_type=event_type,
        title=title,
        message=message,
        source_agent=source_agent,
        url=url,
        severity=severity,
    )

    if not _notification_router.should_send(notification):
        return  # Dedup — already sent recently

    try:
        from fleet.infra.ntfy_client import NtfyClient
        ntfy = NtfyClient()
        await ntfy.publish(
            title=f"[{source_agent}] {title}",
            message=message,
            priority=notification.level.value,
            click_url=url,
            tags=notification.tags,
        )
        await ntfy.close()
        _notification_router.mark_sent(notification)
    except Exception:
        pass


# ─── Daemon Loop ─────────────────────────────────────────────────────────


def _load_orchestrator_config(loader: ConfigLoader) -> dict:
    """Load orchestrator config from fleet.yaml."""
    import yaml

    config_path = loader.fleet_dir / "config" / "fleet.yaml"
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("orchestrator", {})
    return {}


async def run_orchestrator_daemon(interval: int = 30) -> None:
    """Run the orchestrator in a loop."""
    loader = ConfigLoader()
    env = loader.load_env()
    token = env.get("LOCAL_AUTH_TOKEN", "")

    if not token:
        print("[orchestrator] ERROR: No LOCAL_AUTH_TOKEN")
        return

    config = _load_orchestrator_config(loader)
    dry_run = config.get("dry_run", False)

    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    gateway_token = ""
    if os.path.exists(oc_path):
        with open(oc_path) as f:
            oc_cfg = json.load(f)
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")

    mode = " [DRY RUN]" if dry_run else ""
    print(f"[orchestrator] Daemon started{mode} (interval={interval}s)")
    print(f"[orchestrator] Auto-approve threshold: "
          f"{config.get('auto_approve_threshold', 80)}%")
    print(f"[orchestrator] Driver agents: "
          f"{config.get('driver_agents', ['project-manager', 'fleet-ops'])}")

    from fleet.core.outage_detector import OutageDetector
    _outage = OutageDetector()

    while True:
        # Check if we should run this cycle (outage/backoff)
        should_run, skip_reason = _outage.should_run_cycle()
        if not should_run:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [orchestrator] Skipping: {skip_reason}")
            await asyncio.sleep(interval)
            continue

        # Circuit breaker: disable cron jobs with too many consecutive errors.
        # Runs every cycle to catch runaway jobs quickly.
        try:
            from fleet.infra.gateway_client import check_cron_circuit_breaker
            tripped = check_cron_circuit_breaker(max_consecutive_errors=3)
            if tripped:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] [orchestrator] Circuit breaker: disabled {tripped} failing cron job(s)")
        except Exception:
            pass

        try:
            mc = MCClient(token=token)
            irc = IRCClient(gateway_token=gateway_token)
            board_id = await mc.get_board_id()
            _outage.record_success("mc_api")

            # MC is reachable — ensure gateway cron jobs are enabled.
            # They may have been disabled by a previous MC-down event.
            try:
                from fleet.infra.gateway_client import enable_gateway_cron_jobs
                enable_gateway_cron_jobs()
            except Exception:
                pass

            if board_id:
                state = await run_orchestrator_cycle(
                    mc, irc, board_id, config, dry_run=dry_run,
                )

                ts = datetime.now().strftime("%H:%M:%S")
                if state.total_actions > 0 or state.errors:
                    print(
                        f"[{ts}] [orchestrator] "
                        f"approved={state.approvals_processed} "
                        f"transitioned={state.tasks_transitioned} "
                        f"dispatched={state.tasks_dispatched} "
                        f"parents={state.parents_evaluated} "
                        f"drivers={state.drivers_woken} "
                        f"errors={len(state.errors)}"
                    )
                    for err in state.errors:
                        print(f"  ERROR: {err}")

            await mc.close()
        except Exception as e:
            _outage.record_failure("mc_api", str(e))
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [orchestrator] MC UNREACHABLE: {e}")

            # MC is DOWN. Fleet is OFF. Kill EVERYTHING.
            # No gateway = no sessions = no heartbeats = no Claude calls = ZERO.
            import subprocess as _sp

            # Kill gateway process
            try:
                _sp.run(["pkill", "-f", "openclaw-gateway"], capture_output=True, timeout=5)
                _sp.run(["pkill", "-f", "openclaw$"], capture_output=True, timeout=5)
                print(f"[{ts}] [orchestrator] KILLED gateway — MC is DOWN")
            except Exception:
                pass

            # Disable cron jobs (safety: if gateway somehow restarts)
            try:
                from fleet.infra.gateway_client import disable_gateway_cron_jobs
                disable_gateway_cron_jobs()
            except Exception:
                pass

            # Stop orchestrator. Nothing to orchestrate. ZERO consumption.
            print(f"[{ts}] [orchestrator] STOPPING — MC is DOWN. Fleet is OFF.")
            print(f"[{ts}] [orchestrator] Start Docker, then: make daemons-start")
            return  # EXIT the daemon loop — orchestrator is DEAD