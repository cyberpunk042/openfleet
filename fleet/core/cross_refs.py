"""Cross-reference automation — link related items across surfaces.

When an event happens on one surface, automatically create references
on other surfaces so everything is connected and navigable.

Examples:
  - Task completed with PR → Plane issue gets PR link as comment
  - Plane issue created → OCMC board memory notes the Plane item
  - PR merged → OCMC task comment links to merged PR
  - Agent @mentioned in Plane → IRC cross-post with link
  - Sprint started in Plane → IRC #sprint announcement with link

> "always cross reference, like when updating a task on Plane you can
> say it in the internal chat naturally"

Cross-references are generated from events, not hardcoded in tools.
The cross_ref engine reads events and produces reference actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.events import FleetEvent


@dataclass
class CrossReference:
    """A reference to create on a target surface."""

    target_surface: str       # "plane", "ocmc", "irc", "github"
    action: str               # "comment", "link", "memory", "notify"
    content: str              # What to post/link
    target_id: str = ""       # Issue ID, task ID, PR URL, channel
    source_event_id: str = "" # Which event triggered this


def generate_cross_refs(event: FleetEvent) -> list[CrossReference]:
    """Generate cross-references from an event.

    Each event can produce 0-N cross-references on other surfaces.
    The caller executes these via the appropriate clients.
    """
    refs: list[CrossReference] = []
    data = event.data
    event_type = event.type

    # ── Task completed with PR → cross-ref on Plane + IRC ──
    if event_type == "fleet.task.completed":
        pr_url = data.get("pr_url", "")
        summary = data.get("summary", "")
        agent = data.get("agent", "")
        project = data.get("project", "")

        if pr_url:
            # Plane: comment on related issue (if mapped)
            refs.append(CrossReference(
                target_surface="plane",
                action="comment",
                content=f"OCMC task completed by {agent}. PR: {pr_url}\n{summary}",
                source_event_id=event.id,
            ))

            # IRC: cross-post to #reviews with task + PR link
            refs.append(CrossReference(
                target_surface="irc",
                action="notify",
                content=f"[{agent}] PR ready for review: {summary[:40]} — {pr_url}",
                target_id="#reviews",
                source_event_id=event.id,
            ))

        # Board memory: record completion
        refs.append(CrossReference(
            target_surface="ocmc",
            action="memory",
            content=f"Completed: {summary[:100]} by {agent}" + (f" PR: {pr_url}" if pr_url else ""),
            source_event_id=event.id,
        ))

    # ── Plane issue created → cross-ref on OCMC + IRC ──
    elif event_type == "fleet.plane.issue_created":
        title = data.get("title", "")
        project = data.get("project", "")
        issue_id = data.get("issue_id", "")

        # OCMC: board memory note
        refs.append(CrossReference(
            target_surface="ocmc",
            action="memory",
            content=f"New Plane issue: {title} ({project})",
            source_event_id=event.id,
        ))

        # IRC: announce in #fleet
        refs.append(CrossReference(
            target_surface="irc",
            action="notify",
            content=f"[plane] New issue: {title} ({project})",
            target_id="#fleet",
            source_event_id=event.id,
        ))

    # ── PR merged → cross-ref on OCMC + Plane + IRC ──
    elif event_type == "fleet.github.pr_merged":
        pr_url = data.get("pr_url", "")
        task_title = data.get("task_title", "")
        human_merged = data.get("human_merged", False)

        if human_merged:
            # Extra cross-ref: human acted directly
            refs.append(CrossReference(
                target_surface="irc",
                action="notify",
                content=f"[github] Human merged PR: {task_title[:40]} — {pr_url}",
                target_id="#fleet",
                source_event_id=event.id,
            ))

        # Plane: update issue state
        refs.append(CrossReference(
            target_surface="plane",
            action="comment",
            content=f"PR merged: {pr_url}",
            source_event_id=event.id,
        ))

    # ── Agent @mentioned → cross-post to IRC ──
    elif event_type in ("fleet.chat.mention", "fleet.plane.issue_commented"):
        mentions = data.get("mentions", [])
        message = data.get("message", data.get("comment", ""))
        agent = data.get("agent", "system")

        for mentioned in mentions:
            refs.append(CrossReference(
                target_surface="irc",
                action="notify",
                content=f"[{agent}] @{mentioned}: {message[:60]}",
                target_id="#fleet",
                source_event_id=event.id,
            ))

    # ── Sprint started → cross-ref on IRC + OCMC ──
    elif event_type == "fleet.plane.cycle_started":
        cycle_name = data.get("cycle_name", "")
        project = data.get("project", "")

        refs.append(CrossReference(
            target_surface="irc",
            action="notify",
            content=f"[plane] 🏃 Sprint started: {cycle_name} ({project})",
            target_id="#sprint",
            source_event_id=event.id,
        ))

        refs.append(CrossReference(
            target_surface="ocmc",
            action="memory",
            content=f"Sprint started: {cycle_name} ({project})",
            source_event_id=event.id,
        ))

    # ── Sprint completed → cross-ref everywhere ──
    elif event_type == "fleet.plane.cycle_completed":
        cycle_name = data.get("cycle_name", "")
        project = data.get("project", "")

        refs.append(CrossReference(
            target_surface="irc",
            action="notify",
            content=f"[plane] 🏆 Sprint completed: {cycle_name} ({project})",
            target_id="#fleet",
            source_event_id=event.id,
        ))

        refs.append(CrossReference(
            target_surface="ocmc",
            action="memory",
            content=f"Sprint completed: {cycle_name} ({project}). Check Plane for velocity report.",
            source_event_id=event.id,
        ))

    # ── Alert posted → cross-ref IRC + ntfy ──
    elif event_type == "fleet.alert.posted":
        severity = data.get("severity", "")
        title = data.get("title", "")

        if severity in ("critical", "high"):
            refs.append(CrossReference(
                target_surface="irc",
                action="notify",
                content=f"🔴 ALERT [{severity}]: {title}",
                target_id="#alerts",
                source_event_id=event.id,
            ))

    # ── Task blocked → cross-ref IRC + Plane ──
    elif event_type == "fleet.task.blocked":
        reason = data.get("reason", "")
        agent = data.get("agent", "")

        refs.append(CrossReference(
            target_surface="irc",
            action="notify",
            content=f"[{agent}] 🚫 Blocked: {reason[:60]}",
            target_id="#fleet",
            source_event_id=event.id,
        ))

    # ── Escalation → cross-ref everywhere ──
    elif event_type == "fleet.escalation":
        title = data.get("title", "")
        severity = data.get("severity", "")

        refs.append(CrossReference(
            target_surface="irc",
            action="notify",
            content=f"🚨 ESCALATION [{severity}]: {title}",
            target_id="#alerts",
            source_event_id=event.id,
        ))

        refs.append(CrossReference(
            target_surface="ocmc",
            action="memory",
            content=f"ESCALATION [{severity}]: {title}. Human attention required.",
            source_event_id=event.id,
        ))

    return refs


def format_cross_ref_summary(refs: list[CrossReference]) -> str:
    """Format cross-references as a summary for logging."""
    if not refs:
        return "no cross-refs"
    surfaces = set(r.target_surface for r in refs)
    return f"{len(refs)} cross-refs → {', '.join(sorted(surfaces))}"