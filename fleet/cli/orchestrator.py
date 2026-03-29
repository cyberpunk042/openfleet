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

    # Step 1: Security scan — check new/changed tasks for suspicious content
    await _security_scan(mc, irc, board_id, tasks, changes, state, dry_run)

    # Step 2: Ensure review tasks have approvals (so fleet-ops can review them)
    await _ensure_review_approvals(mc, board_id, tasks, state, dry_run)

    # Step 3: Wake fleet-ops urgently if there are pending approvals to process
    await _wake_lead_for_reviews(mc, irc, board_id, tasks, agent_name_map, state, dry_run)

    # Step 4: Dispatch unblocked inbox tasks to assigned agents
    await _dispatch_ready_tasks(mc, irc, board_id, tasks, agent_map, state, dry_run)

    # Step 5: Evaluate parent task completion (all children done → parent to review)
    await _evaluate_parents(mc, irc, board_id, tasks, state, dry_run)

    # Step 6: Health check — detect stuck tasks, offline agents, stale deps
    await _health_check(mc, irc, board_id, tasks, agents, state, dry_run)

    # NOTE: Heartbeats are managed by the GATEWAY, not the orchestrator.
    # The orchestrator NEVER creates Claude Code sessions directly.
    # The gateway's heartbeat system (HEARTBEAT.md, heartbeat_config.every)
    # handles agent cycling at controlled intervals.
    # The orchestrator only: dispatch tasks, evaluate parents, check health.

    return state


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
) -> None:
    """Find unblocked inbox tasks with assigned agents and dispatch them."""
    from fleet.cli.dispatch import _run_dispatch
    from fleet.core.task_scoring import rank_tasks

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

    inbox_tasks = [
        t for t in tasks
        if t.status == TaskStatus.INBOX
        and t.assigned_agent_id
        and not t.is_blocked
    ]

    # Smart scoring — considers priority, dependency chain, wait time, task type
    scored = rank_tasks(inbox_tasks, tasks)
    inbox_tasks = [s.task for s in scored]

    # Track busy agents (those with in_progress tasks)
    busy_agent_ids = {
        t.assigned_agent_id
        for t in tasks
        if t.status == TaskStatus.IN_PROGRESS and t.assigned_agent_id
    }

    # SAFETY: Max 2 dispatches per cycle to prevent session storms
    max_dispatch = config.get("max_dispatch_per_cycle", 2)

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
          f"{config.get('driver_agents', DRIVER_AGENTS)}")

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

        try:
            mc = MCClient(token=token)
            irc = IRCClient(gateway_token=gateway_token)
            board_id = await mc.get_board_id()
            _outage.record_success("mc_api")

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
            print(f"[{ts}] [orchestrator] Error: {e}")
            # Alert on repeated failures
            alerts = _outage.get_alerts()
            if alerts:
                for alert in alerts:
                    print(f"  OUTAGE: {alert}")

        await asyncio.sleep(interval)