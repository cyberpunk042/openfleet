"""Plane ↔ OCMC bidirectional sync.

Two sync directions:

1. **Plane → OCMC** (``ingest_from_plane``):
   New Plane issues are discovered and created as OCMC tasks.
   The mapping is stored in OCMC custom fields:
   - ``plane_issue_id``     — Plane issue UUID
   - ``plane_project_id``   — Plane project UUID
   - ``plane_workspace``    — Plane workspace slug

2. **OCMC → Plane** (``push_completions_to_plane``):
   OCMC tasks that reached ``done`` and carry a ``plane_issue_id``
   are reflected back to Plane by updating the issue state to the
   configured "done" state.

Usage::

    from fleet.core.plane_sync import PlaneSyncer
    from fleet.infra.mc_client import MCClient
    from fleet.infra.plane_client import PlaneClient

    mc = MCClient(token="...")
    plane = PlaneClient(base_url="...", api_key="...")

    syncer = PlaneSyncer(
        mc=mc,
        plane=plane,
        board_id="<ocmc-board-uuid>",
        workspace_slug="my-org",
        project_ids=["proj-uuid-1"],
        done_state_id="state-uuid-for-done",
        assigned_agent_id="<optional-agent-uuid>",
    )

    created, skipped = await syncer.ingest_from_plane()
    updated = await syncer.push_completions_to_plane()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.models import Task
from fleet.core.plane_methodology import (
    extract_methodology_state,
    build_label_updates,
    inject_verbatim_into_html,
)
from fleet.infra.mc_client import MCClient
from fleet.infra.plane_client import PlaneClient, PlaneIssue

logger = logging.getLogger(__name__)

# ─── Custom field keys ──────────────────────────────────────────────────────
# These keys are stored in OCMC task.custom_field_values to maintain the
# Plane ↔ OCMC mapping.  They are free-form strings (OCMC schema allows
# arbitrary custom_field_values keys).

CF_PLANE_ISSUE_ID = "plane_issue_id"
CF_PLANE_PROJECT_ID = "plane_project_id"
CF_PLANE_WORKSPACE = "plane_workspace"

# ─── Sync result dataclasses ────────────────────────────────────────────────


@dataclass
class IngestResult:
    """Result of a single Plane→OCMC ingest pass."""

    created: list[Task] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # plane issue IDs already mapped
    errors: list[str] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        return len(self.created)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)


@dataclass
class PushResult:
    """Result of a single OCMC→Plane push pass."""

    updated: list[str] = field(default_factory=list)  # plane issue IDs updated
    skipped: list[str] = field(default_factory=list)  # OCMC task IDs without plane mapping
    errors: list[str] = field(default_factory=list)

    @property
    def updated_count(self) -> int:
        return len(self.updated)


# ─── Priority mapping ────────────────────────────────────────────────────────

_PLANE_PRIORITY_TO_OCMC: dict[str, str] = {
    "urgent": "urgent",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "none": "medium",
}


def _map_priority(plane_priority: str) -> str:
    """Convert a Plane priority string to an OCMC priority string."""
    return _PLANE_PRIORITY_TO_OCMC.get(plane_priority, "medium")


# ─── PlaneSyncer ─────────────────────────────────────────────────────────────


class PlaneSyncer:
    """Bidirectional sync between Plane and OCMC.

    Args:
        mc: Authenticated :class:`~fleet.infra.mc_client.MCClient`.
        plane: Authenticated :class:`~fleet.infra.plane_client.PlaneClient`.
        board_id: OCMC board UUID to sync tasks into/from.
        workspace_slug: Plane workspace slug (e.g. ``"my-org"``).
        project_ids: List of Plane project UUIDs to watch.
            If empty, all projects visible to the API token are synced.
        done_state_id: Plane state UUID to set when an OCMC task reaches
            ``done``.  If ``None``, the push direction is a no-op.
        assigned_agent_id: OCMC agent UUID to assign created tasks to.
            If ``None``, tasks are left unassigned.
        default_priority: Fallback OCMC priority when Plane priority is
            unknown (default ``"medium"``).
    """

    def __init__(
        self,
        *,
        mc: MCClient,
        plane: PlaneClient,
        board_id: str,
        workspace_slug: str,
        project_ids: Optional[list[str]] = None,
        done_state_id: Optional[str] = None,
        assigned_agent_id: Optional[str] = None,
        default_priority: str = "medium",
    ) -> None:
        self._mc = mc
        self._plane = plane
        self._board_id = board_id
        self._workspace = workspace_slug
        self._project_ids = project_ids or []
        self._done_state_id = done_state_id
        self._assigned_agent_id = assigned_agent_id
        self._default_priority = default_priority

    # ─── Public API ──────────────────────────────────────────────────────

    async def ingest_from_plane(self) -> IngestResult:
        """Poll Plane projects and create OCMC tasks for new issues.

        Skips issues that already have an OCMC task (detected by scanning
        existing tasks for a matching ``plane_issue_id`` custom field).

        Returns:
            :class:`IngestResult` with lists of created tasks, skipped issue
            IDs, and any error messages.
        """
        result = IngestResult()

        # Resolve project list
        project_ids = await self._resolve_project_ids()
        if not project_ids:
            logger.warning("plane_sync: no Plane projects to sync")
            return result

        # Build index of already-mapped plane issue IDs from existing OCMC tasks
        mapped_ids = await self._build_mapped_issue_index()

        for project_id in project_ids:
            try:
                issues = await self._plane.list_issues(
                    self._workspace, project_id
                )
            except Exception as exc:  # noqa: BLE001
                msg = f"plane_sync: failed to list issues for project {project_id}: {exc}"
                logger.error(msg)
                result.errors.append(msg)
                continue

            for issue in issues:
                if issue.id in mapped_ids:
                    result.skipped.append(issue.id)
                    logger.debug("plane_sync: skip already-mapped issue %s", issue.id)
                    continue

                try:
                    task = await self._create_ocmc_task(issue, project_id)
                    result.created.append(task)
                    logger.info(
                        "plane_sync: created OCMC task %s for Plane issue %s",
                        task.id,
                        issue.id,
                    )
                except Exception as exc:  # noqa: BLE001
                    msg = f"plane_sync: failed to create task for issue {issue.id}: {exc}"
                    logger.error(msg)
                    result.errors.append(msg)

        return result

    async def push_completions_to_plane(self) -> PushResult:
        """Update Plane issue states for completed OCMC tasks.

        Scans OCMC ``done`` tasks that carry a ``plane_issue_id`` custom field
        and updates the corresponding Plane issue to ``done_state_id``.

        Returns:
            :class:`PushResult` with updated/skipped/error counts.
        """
        result = PushResult()

        if not self._done_state_id:
            logger.debug("plane_sync: done_state_id not configured; skipping push")
            return result

        done_tasks = await self._mc.list_tasks(self._board_id, status="done")

        for task in done_tasks:
            plane_issue_id = self._get_cf(task, CF_PLANE_ISSUE_ID)
            plane_project_id = self._get_cf(task, CF_PLANE_PROJECT_ID)

            if not plane_issue_id or not plane_project_id:
                result.skipped.append(task.id)
                continue

            try:
                await self._plane.update_issue(
                    self._workspace,
                    plane_project_id,
                    plane_issue_id,
                    state_id=self._done_state_id,
                )
                result.updated.append(plane_issue_id)
                logger.info(
                    "plane_sync: updated Plane issue %s to done state",
                    plane_issue_id,
                )
            except Exception as exc:  # noqa: BLE001
                msg = (
                    f"plane_sync: failed to update Plane issue {plane_issue_id} "
                    f"(OCMC task {task.id}): {exc}"
                )
                logger.error(msg)
                result.errors.append(msg)

        return result

    async def sync_methodology_fields(self) -> dict:
        """Bidirectional sync of methodology fields (readiness, stage, verbatim).

        For each OCMC task that has a plane_issue_id mapping:
        - Reads methodology state from both platforms
        - Syncs whichever is more recent / authoritative

        Direction rules:
        - requirement_verbatim: Plane → OCMC (PO writes in Plane)
        - task_readiness: last-write-wins (can change on either side)
        - task_stage: last-write-wins (can change on either side)

        Returns:
            Dict with counts: ocmc_updated, plane_updated, errors.
        """
        result = {"ocmc_updated": 0, "plane_updated": 0, "errors": []}

        try:
            tasks = await self._mc.list_tasks(self._board_id, limit=500)
        except Exception as exc:
            result["errors"].append(f"Failed to list OCMC tasks: {exc}")
            return result

        # Build label caches per project (ID → name, name → ID)
        label_caches: dict[str, dict[str, str]] = {}  # project_id → {id: name}

        for task in tasks:
            plane_issue_id = self._get_cf(task, CF_PLANE_ISSUE_ID)
            plane_project_id = self._get_cf(task, CF_PLANE_PROJECT_ID)
            if not plane_issue_id or not plane_project_id:
                continue

            try:
                # Get Plane issue
                issues = await self._plane.list_issues(
                    self._workspace, plane_project_id
                )
                issue = next((i for i in issues if i.id == plane_issue_id), None)
                if not issue:
                    continue

                # Build label cache for this project
                if plane_project_id not in label_caches:
                    label_caches[plane_project_id] = await self._plane.list_labels(
                        self._workspace, plane_project_id
                    )
                label_id_to_name = label_caches[plane_project_id]
                label_names = [label_id_to_name.get(lid, "") for lid in issue.labels]

                # Extract Plane methodology state
                plane_state = extract_methodology_state(
                    label_names, issue.description_html
                )

                # OCMC methodology state
                ocmc_readiness = task.custom_fields.task_readiness
                ocmc_stage = task.custom_fields.task_stage
                ocmc_verbatim = task.custom_fields.requirement_verbatim

                # ── Plane → OCMC: verbatim requirement (Plane is source) ──
                ocmc_updates = {}
                if plane_state.requirement_verbatim and plane_state.requirement_verbatim != ocmc_verbatim:
                    ocmc_updates["requirement_verbatim"] = plane_state.requirement_verbatim

                # ── Bidirectional: readiness (Plane wins if different and non-zero) ──
                if plane_state.task_readiness != ocmc_readiness:
                    if plane_state.task_readiness > 0:
                        ocmc_updates["task_readiness"] = plane_state.task_readiness
                    elif ocmc_readiness > 0:
                        # OCMC has readiness, Plane doesn't — push to Plane
                        pass  # handled below in Plane updates

                # ── Bidirectional: stage (Plane wins if set) ──
                if plane_state.task_stage and plane_state.task_stage != ocmc_stage:
                    ocmc_updates["task_stage"] = plane_state.task_stage

                # Apply OCMC updates
                if ocmc_updates:
                    await self._mc.update_task(
                        self._board_id, task.id,
                        custom_fields=ocmc_updates,
                    )
                    result["ocmc_updated"] += 1
                    logger.info(
                        "methodology_sync: updated OCMC task %s: %s",
                        task.id[:8], list(ocmc_updates.keys()),
                    )

                # ── OCMC → Plane: push readiness/stage/verbatim if OCMC has more ──
                plane_needs_update = False
                new_label_names = list(label_names)
                new_description = issue.description_html

                # Push stage to Plane if OCMC has it and Plane doesn't
                if ocmc_stage and not plane_state.task_stage:
                    new_label_names = build_label_updates(
                        label_names, stage=ocmc_stage,
                        readiness=ocmc_readiness if ocmc_readiness > 0 else None,
                    )
                    plane_needs_update = True
                # Push readiness to Plane if OCMC has it and Plane doesn't
                elif ocmc_readiness > 0 and plane_state.task_readiness == 0:
                    new_label_names = build_label_updates(
                        label_names, readiness=ocmc_readiness,
                    )
                    plane_needs_update = True

                # Push verbatim to Plane if OCMC has it and Plane doesn't
                if ocmc_verbatim and not plane_state.requirement_verbatim:
                    new_description = inject_verbatim_into_html(
                        issue.description_html, ocmc_verbatim
                    )
                    plane_needs_update = True

                if plane_needs_update:
                    # Resolve label names back to IDs
                    new_label_ids = await self._plane.resolve_label_ids(
                        self._workspace, plane_project_id, new_label_names,
                    )
                    update_kwargs = {}
                    if new_label_ids != issue.labels:
                        update_kwargs["label_ids"] = new_label_ids
                    if new_description != issue.description_html:
                        update_kwargs["description_html"] = new_description

                    if update_kwargs:
                        await self._plane.update_issue(
                            self._workspace, plane_project_id, plane_issue_id,
                            **update_kwargs,
                        )
                        result["plane_updated"] += 1
                        logger.info(
                            "methodology_sync: updated Plane issue %s: %s",
                            plane_issue_id[:8], list(update_kwargs.keys()),
                        )

            except Exception as exc:
                msg = f"methodology_sync: error syncing task {task.id[:8]}: {exc}"
                logger.error(msg)
                result["errors"].append(msg)

        return result

    # ─── Helpers ─────────────────────────────────────────────────────────

    async def _resolve_project_ids(self) -> list[str]:
        """Return the list of Plane project IDs to sync.

        If ``project_ids`` was provided at construction, use that.
        Otherwise, list all visible projects and return their IDs.
        """
        if self._project_ids:
            return self._project_ids

        try:
            projects = await self._plane.list_projects(self._workspace)
            return [p.id for p in projects]
        except Exception as exc:  # noqa: BLE001
            logger.error("plane_sync: failed to list Plane projects: %s", exc)
            return []

    async def _build_mapped_issue_index(self) -> set[str]:
        """Return the set of Plane issue IDs already mapped to OCMC tasks.

        Scans all tasks on the board and collects ``plane_issue_id`` values
        from their custom fields.
        """
        mapped: set[str] = set()
        try:
            tasks = await self._mc.list_tasks(self._board_id, limit=500)
            for task in tasks:
                issue_id = self._get_cf(task, CF_PLANE_ISSUE_ID)
                if issue_id:
                    mapped.add(issue_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("plane_sync: could not build mapped index: %s", exc)
        return mapped

    async def _create_ocmc_task(self, issue: PlaneIssue, project_id: str) -> Task:
        """Create an OCMC task from a Plane issue.

        Stores the Plane mapping in custom fields so future ingest passes
        can detect the issue as already synced.
        """
        priority = _map_priority(issue.priority)

        # Build a plain-text description from the Plane issue
        description = _html_to_plain(issue.description_html)
        if description:
            description = f"{description}\n\n---\n_Synced from Plane issue {issue.sequence_id}_"
        else:
            description = f"_Synced from Plane issue {issue.sequence_id}_"

        custom_fields: dict = {
            CF_PLANE_ISSUE_ID: issue.id,
            CF_PLANE_PROJECT_ID: project_id,
            CF_PLANE_WORKSPACE: self._workspace,
        }

        return await self._mc.create_task(
            self._board_id,
            title=issue.title,
            description=description,
            priority=priority,
            assigned_agent_id=self._assigned_agent_id,
            custom_fields=custom_fields,
            auto_created=True,
            auto_reason=f"Synced from Plane issue {issue.id} (#{issue.sequence_id})",
        )

    @staticmethod
    def _get_cf(task: Task, key: str) -> Optional[str]:
        """Read a Plane mapping field from a task's custom fields.

        The Plane-specific fields (``plane_issue_id``, ``plane_project_id``,
        ``plane_workspace``) are first-class attributes on
        :class:`~fleet.core.models.TaskCustomFields` and are populated by
        :meth:`~fleet.infra.mc_client.MCClient._parse_task`.
        """
        val = getattr(task.custom_fields, key, None)
        return str(val) if val is not None else None


# ─── Utility ─────────────────────────────────────────────────────────────────


def _html_to_plain(html: str) -> str:
    """Strip HTML tags to produce a plain-text description.

    Minimal implementation — no external dependency.
    Handles the common Plane HTML output patterns.
    """
    if not html:
        return ""
    import re
    # Replace block elements with newlines
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
