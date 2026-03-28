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
from fleet.core.models import Approval, Task, TaskStatus
from fleet.core.notification_router import NotificationRouter
from fleet.infra.config_loader import ConfigLoader
from fleet.infra.irc_client import IRCClient
from fleet.infra.mc_client import MCClient

# Global state (persists across cycles)
_fleet_lifecycle = FleetLifecycle()
_notification_router = NotificationRouter(cooldown_seconds=300)


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
    state = OrchestratorState()

    tasks = await mc.list_tasks(board_id)
    agents = await mc.list_agents()
    agent_map = {a.id: a for a in agents if "Gateway" not in a.name}
    agent_name_map = {a.name: a for a in agents if "Gateway" not in a.name}
    now = datetime.now()

    # Update fleet lifecycle tracker with current activity
    active_agents: dict[str, str] = {}
    for t in tasks:
        if t.status == TaskStatus.IN_PROGRESS and t.custom_fields.agent_name:
            active_agents[t.custom_fields.agent_name] = t.id
    for a in agents:
        if "Gateway" not in a.name:
            _fleet_lifecycle.get_or_create(a.name)
    _fleet_lifecycle.update_all(now, active_agents)

    # Step 1: Ensure review tasks have approvals (so fleet-ops can review them)
    await _ensure_review_approvals(mc, board_id, tasks, state, dry_run)

    # Step 2: Wake fleet-ops urgently if there are pending approvals to process
    await _wake_lead_for_reviews(mc, irc, board_id, tasks, agent_name_map, state, dry_run)

    # Step 3: Dispatch unblocked inbox tasks to assigned agents
    await _dispatch_ready_tasks(mc, irc, board_id, tasks, agent_map, state, dry_run)

    # Step 4: Evaluate parent task completion (all children done → parent to review)
    await _evaluate_parents(mc, irc, board_id, tasks, state, dry_run)

    # Step 5: Smart heartbeats — only wake agents that need it based on lifecycle status
    await _lifecycle_heartbeats(mc, irc, board_id, tasks, agent_name_map, config, state, dry_run)

    return state


# ─── Step 1: Ensure Review Tasks Have Approvals ─────────────────────────
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

    try:
        pending = await mc.list_approvals(board_id, status="pending")
        if not pending:
            return

        approval_list = "\n".join(
            f"- task {a.task_id[:8]} (confidence={a.confidence:.0f}%)"
            for a in pending[:5]
        )

        await mc.create_task(
            board_id,
            title=f"[review] Process {len(pending)} pending approvals",
            description=(
                f"You have {len(pending)} pending approvals and "
                f"{review_count} tasks in review.\n\n"
                f"Pending approvals:\n{approval_list}\n\n"
                f"Use fleet_agent_status() for the full picture.\n"
                f"For each: review the work, then fleet_approve() or reject.\n"
                f"See your HEARTBEAT.md for the full review chain process."
            ),
            priority="high",
            assigned_agent_id=fleet_ops.id,
            custom_fields={
                "agent_name": "fleet-ops",
                "task_type": "subtask",
            },
        )
        _last_review_wake = now
        state.drivers_woken += 1
    except Exception as e:
        state.errors.append(f"wake fleet-ops for reviews: {e}")


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

    for task in inbox_tasks:
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


# ─── Step 5: Lifecycle-Aware Heartbeats ──────────────────────────────────

DRIVER_AGENTS = ["project-manager", "fleet-ops"]


async def _lifecycle_heartbeats(
    mc: MCClient,
    irc: IRCClient,
    board_id: str,
    tasks: list[Task],
    agent_name_map: dict,
    config: dict,
    state: OrchestratorState,
    dry_run: bool,
) -> None:
    """Send heartbeats based on agent lifecycle status.

    Active agents → no heartbeat (they're working)
    Idle agents → heartbeat every 5 minutes
    Sleeping agents → heartbeat every 30 minutes
    Offline agents → heartbeat every 2 hours

    This replaces the fixed-interval driver wake with smart status management.
    """
    now = datetime.now()
    drivers = set(config.get("driver_agents", DRIVER_AGENTS))

    agents_needing_heartbeat = _fleet_lifecycle.agents_needing_heartbeat(now)

    for agent_state in agents_needing_heartbeat:
        agent = agent_name_map.get(agent_state.name)
        if not agent or not agent.session_key:
            continue

        # Check if agent already has a pending heartbeat/review task
        has_pending = any(
            t.custom_fields.agent_name == agent_state.name
            and t.status in (TaskStatus.INBOX, TaskStatus.IN_PROGRESS)
            and ("[heartbeat]" in t.title or "[review]" in t.title)
            for t in tasks
        )
        if has_pending:
            agent_state.mark_heartbeat_sent(now)
            continue

        # Only create heartbeat tasks for drivers and agents with specific work
        # Worker agents in sleeping/offline don't need heartbeats unless they have work
        if agent_state.name not in drivers and agent_state.status in (AgentStatus.SLEEPING, AgentStatus.OFFLINE):
            # Check if this agent has any assigned inbox tasks
            has_work = any(
                t.custom_fields.agent_name == agent_state.name
                and t.status == TaskStatus.INBOX
                and not t.is_blocked
                for t in tasks
            )
            if not has_work:
                agent_state.mark_heartbeat_sent(now)
                continue

        if dry_run:
            print(f"  [dry_run] WOULD heartbeat {agent_state.name} "
                  f"(status={agent_state.status.value})")
            agent_state.mark_heartbeat_sent(now)
            state.drivers_woken += 1
            continue

        try:
            status_label = agent_state.status.value
            task = await mc.create_task(
                board_id,
                title=f"[heartbeat] {agent_state.name} periodic check",
                description=(
                    f"Heartbeat task for {agent_state.name} "
                    f"(status: {status_label}). "
                    "Check your HEARTBEAT.md for instructions. "
                    "Use fleet_agent_status to assess fleet health. "
                    "If everything is fine, complete with 'HEARTBEAT_OK'."
                ),
                priority="low",
                assigned_agent_id=agent.id,
                custom_fields={
                    "agent_name": agent_state.name,
                    "task_type": "subtask",
                },
            )
            agent_state.mark_heartbeat_sent(now)
            state.drivers_woken += 1
        except Exception as e:
            state.errors.append(f"heartbeat {agent_state.name}: {e}")


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

    while True:
        try:
            mc = MCClient(token=token)
            irc = IRCClient(gateway_token=gateway_token)
            board_id = await mc.get_board_id()

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
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [orchestrator] Error: {e}")

        await asyncio.sleep(interval)