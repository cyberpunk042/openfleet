"""Chain runner — executes event chains across all surfaces.

Takes an EventChain (built by chain builders in event_chain.py) and
executes each event on its target surface. Tolerant of partial failure —
one surface failing doesn't block others.

Surfaces:
  INTERNAL → MCClient (task updates, approvals, board memory)
  PUBLIC → GHClient (branches, PRs)
  CHANNEL → IRCClient (IRC messages)
  NOTIFY → NtfyClient (human notifications)
  PLANE → PlaneClient (Plane issue updates — optional)
  META → logging, metrics

> "smart tools, chains that will trigger multiple things for one call
> or one event and that will keep listening to all side and keep in sync"
"""

from __future__ import annotations

import logging
from typing import Optional

from fleet.core.event_chain import ChainResult, Event, EventChain, EventSurface
from fleet.core.events import EventStore, create_event

logger = logging.getLogger(__name__)


class ChainRunner:
    """Executes event chains across surfaces.

    Usage::

        runner = ChainRunner(mc=mc_client, irc=irc_client, gh=gh_client,
                             plane=plane_client, ntfy=ntfy_client)
        result = await runner.run(chain)
    """

    def __init__(
        self,
        mc=None,
        irc=None,
        gh=None,
        plane=None,
        ntfy=None,
        board_id: str = "",
        plane_workspace: str = "fleet",
    ) -> None:
        self._mc = mc
        self._irc = irc
        self._gh = gh
        self._plane = plane
        self._ntfy = ntfy
        self._board_id = board_id
        self._plane_ws = plane_workspace

    async def run(self, chain: EventChain) -> ChainResult:
        """Execute all events in the chain. Tolerant of partial failure."""
        result = ChainResult(
            operation=chain.operation,
            total_events=len(chain.events),
        )

        for event in chain.events:
            try:
                await self._execute_event(event)
                event.executed = True
                result.executed += 1
            except Exception as e:
                event.error = str(e)
                event.executed = True
                if event.required:
                    result.failed += 1
                    result.errors.append(
                        f"[{event.surface.value}] {event.action}: {e}"
                    )
                else:
                    # Non-required failures logged but don't fail the chain
                    logger.warning(
                        "Non-required event failed: [%s] %s: %s",
                        event.surface.value, event.action, e,
                    )

        # Emit chain execution as a CloudEvent for the event bus
        try:
            store = EventStore()
            store.append(create_event(
                f"fleet.chain.{chain.operation}",
                source="fleet/core/chain_runner",
                subject=chain.task_id or "",
                recipient="all",
                priority="info",
                tags=["chain", chain.operation],
                surfaces=[e.surface.value for e in chain.events if e.executed],
                total_events=result.total_events,
                executed=result.executed,
                failed=result.failed,
                agent=chain.source_agent,
            ))
        except Exception:
            pass  # Event emission must never break chain execution

        # Generate and execute cross-references
        try:
            from fleet.core.cross_refs import generate_cross_refs
            chain_event = create_event(
                f"fleet.{chain.operation}",
                source="fleet/core/chain_runner",
                subject=chain.task_id,
                agent=chain.source_agent,
                **{k: v for k, v in chain.events[0].params.items() if k in (
                    "summary", "pr_url", "branch", "project", "title",
                    "severity", "details", "cycle_name",
                )}
            ) if chain.events else None

            if chain_event:
                refs = generate_cross_refs(chain_event)
                for ref in refs:
                    try:
                        if ref.target_surface == "irc" and self._irc:
                            channel = ref.target_id or "#fleet"
                            await self._irc.notify(channel, ref.content)
                        elif ref.target_surface == "ocmc" and ref.action == "memory" and self._mc:
                            await self._mc.post_memory(
                                self._board_id,
                                content=ref.content,
                                tags=["cross-ref", chain.operation],
                            )
                    except Exception:
                        pass  # Cross-refs are best-effort
        except Exception:
            pass

        return result

    async def _execute_event(self, event: Event) -> None:
        """Dispatch an event to its surface handler."""
        handlers = {
            EventSurface.INTERNAL: self._handle_internal,
            EventSurface.PUBLIC: self._handle_public,
            EventSurface.CHANNEL: self._handle_channel,
            EventSurface.NOTIFY: self._handle_notify,
            EventSurface.META: self._handle_meta,
        }

        # PLANE surface — only if PlaneClient available
        if hasattr(EventSurface, "PLANE"):
            handlers[EventSurface.PLANE] = self._handle_plane

        handler = handlers.get(event.surface)
        if handler:
            event.result = await handler(event)
        else:
            logger.warning("No handler for surface: %s", event.surface)

    # ─── Surface Handlers ──────────────────────────────────────────────

    async def _handle_internal(self, event: Event) -> dict:
        """Handle INTERNAL events — MC task updates, approvals, board memory."""
        if not self._mc:
            raise RuntimeError("MCClient not available")

        action = event.action
        params = event.params

        if action == "update_task_status":
            task_id = params.get("task_id", "")
            status = params.get("status", "")
            if task_id and status:
                await self._mc.update_task(
                    self._board_id, task_id, status=status,
                )
                return {"updated": task_id, "status": status}

        elif action == "create_approval":
            task_id = params.get("task_id", "")
            confidence = params.get("confidence", 80)
            if task_id:
                await self._mc.create_approval(
                    self._board_id, task_id,
                    confidence=confidence,
                    summary=params.get("tests", ""),
                )
                return {"approval_created": task_id}

        elif action == "post_board_memory":
            content = params.get("content", "")
            tags = params.get("tags", [])
            if content:
                await self._mc.post_memory(
                    self._board_id,
                    content=content,
                    tags=tags,
                )
                return {"memory_posted": True}

        elif action == "post_comment":
            task_id = params.get("task_id", "")
            comment = params.get("comment", "")
            if task_id and comment:
                await self._mc.post_comment(
                    self._board_id, task_id, comment=comment,
                )
                return {"comment_posted": task_id}

        elif action == "update_custom_fields":
            task_id = params.get("task_id", "")
            custom_fields = params.get("custom_fields", {})
            if task_id and custom_fields:
                await self._mc.update_task(
                    self._board_id, task_id,
                    custom_fields=custom_fields,
                )
                return {"updated": task_id, "fields": list(custom_fields.keys())}

        return {"action": action, "status": "no_handler"}

    async def _handle_public(self, event: Event) -> dict:
        """Handle PUBLIC events — GitHub branches, PRs."""
        if not self._gh:
            raise RuntimeError("GHClient not available")

        action = event.action
        params = event.params

        if action == "push_branch":
            branch = params.get("branch", "")
            if branch:
                await self._gh._run(["git", "push", "origin", branch])
                return {"pushed": branch}

        elif action == "create_pr":
            pr_url = params.get("pr_url", "")
            return {"pr_url": pr_url}

        return {"action": action, "status": "no_handler"}

    async def _handle_channel(self, event: Event) -> dict:
        """Handle CHANNEL events — IRC messages."""
        if not self._irc:
            raise RuntimeError("IRCClient not available")

        action = event.action
        params = event.params

        if action == "notify_irc":
            channel = params.get("channel", "#fleet")
            message = params.get("message", "")
            if message:
                ok = await self._irc.notify(channel, message)
                return {"sent": ok, "channel": channel}

        return {"action": action, "status": "no_handler"}

    async def _handle_notify(self, event: Event) -> dict:
        """Handle NOTIFY events — ntfy human notifications."""
        if not self._ntfy:
            # ntfy is optional — log but don't fail
            logger.debug("ntfy not available, skipping: %s", event.action)
            return {"skipped": True, "reason": "ntfy_not_available"}

        action = event.action
        params = event.params

        if action == "ntfy_publish":
            title = params.get("title", "")
            priority = params.get("priority", "info")
            event_type = params.get("event_type", "")
            if title:
                ok = await self._ntfy.publish(
                    title=title,
                    message=params.get("message", title),
                    priority=priority,
                    tags=[event_type] if event_type else [],
                )
                return {"published": ok}

        return {"action": action, "status": "no_handler"}

    async def _handle_plane(self, event: Event) -> dict:
        """Handle PLANE events — Plane issue updates (optional surface)."""
        if not self._plane:
            # Plane is optional — graceful skip
            logger.debug("Plane not available, skipping: %s", event.action)
            return {"skipped": True, "reason": "plane_not_configured"}

        action = event.action
        params = event.params

        if action == "update_issue_state":
            issue_id = params.get("issue_id", "")
            project_id = params.get("project_id", "")
            state_name = params.get("state", "")
            if issue_id and project_id and state_name:
                # Resolve state name to ID
                states = await self._plane.list_states(
                    self._plane_ws, project_id
                )
                state = next(
                    (s for s in states if s.name.lower() == state_name.lower()),
                    None,
                )
                if state:
                    await self._plane.update_issue(
                        self._plane_ws, project_id, issue_id,
                        state_id=state.id,
                    )
                    return {"updated": issue_id, "state": state_name}

        elif action == "post_comment":
            issue_id = params.get("issue_id", "")
            project_id = params.get("project_id", "")
            comment = params.get("comment", "")
            if issue_id and project_id and comment:
                await self._plane._client.post(
                    f"/api/v1/workspaces/{self._plane_ws}/projects/{project_id}"
                    f"/issues/{issue_id}/comments/",
                    json={"comment_html": f"<p>{comment}</p>"},
                )
                return {"comment_posted": issue_id}

        elif action == "update_labels":
            issue_id = params.get("issue_id", "")
            project_id = params.get("project_id", "")
            label_ids = params.get("label_ids", [])
            if issue_id and project_id and label_ids:
                await self._plane.update_issue(
                    self._plane_ws, project_id, issue_id,
                    label_ids=label_ids,
                )
                return {"labels_updated": issue_id, "count": len(label_ids)}

        elif action == "create_issue":
            project_id = params.get("project_id", "")
            title = params.get("title", "")
            description = params.get("description", "")
            priority = params.get("priority", "medium")
            label_ids = params.get("label_ids", [])
            if project_id and title:
                issue = await self._plane.create_issue(
                    self._plane_ws, project_id,
                    title=title,
                    description_html=f"<p>{description}</p>" if description else f"<p>{title}</p>",
                    priority=priority,
                    label_ids=label_ids or None,
                )
                return {"issue_created": issue.id, "title": title}

        return {"action": action, "status": "no_handler"}

    async def _handle_meta(self, event: Event) -> dict:
        """Handle META events — logging, metrics, system tracking."""
        action = event.action
        params = event.params

        if action == "update_metrics":
            agent = params.get("agent", "")
            task_id = params.get("task_id", "")
            logger.info(
                "Chain metric: agent=%s task=%s operation=%s",
                agent, task_id, "completed",
            )
            return {"logged": True}

        return {"action": action, "status": "logged"}