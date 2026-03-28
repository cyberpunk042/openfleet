"""Fleet IRC message formatters.

Produces structured one-line messages for IRC channels.
Each message includes emoji, agent name, event type, and URL.
"""

from __future__ import annotations


def format_event(
    agent: str, event: str, title: str = "", url: str = ""
) -> str:
    """Format a general fleet event message.

    Output: [agent] EVENT: title — url
    """
    msg = f"[{agent}] {event}"
    if title:
        msg = f"{msg}: {title}"
    if url:
        msg = f"{msg} — {url}"
    return msg


def format_task_started(agent: str, title: str, task_url: str = "") -> str:
    """Task accepted and started."""
    return format_event(agent, "▶️ STARTED", title, task_url)


def format_task_blocked(
    agent: str, title: str, reason: str = "", task_url: str = ""
) -> str:
    """Task blocked."""
    display = f"{title} — {reason}" if reason else title
    return format_event(agent, "🚫 BLOCKED", display, task_url)


def format_pr_ready(agent: str, title: str, pr_url: str) -> str:
    """PR ready for review."""
    return format_event(agent, "✅ PR READY", title, pr_url)


def format_pr_review(agent: str, title: str, pr_url: str) -> str:
    """PR posted to #reviews."""
    return format_event(agent, "🔀 PR", title, pr_url)


def format_merged(title: str, pr_url: str) -> str:
    """PR merged."""
    return format_event("fleet", "🔀 MERGED", title, pr_url)


def format_task_done(title: str, task_url: str = "") -> str:
    """Task completed and closed."""
    return format_event("fleet", "✅ TASK DONE", title, task_url)


def format_alert(
    agent: str, severity: str, title: str, url: str = ""
) -> str:
    """Alert message routed by severity."""
    emoji = {
        "critical": "🔴", "high": "🟠",
        "medium": "🟡", "low": "🟢",
    }.get(severity, "⚠️")
    return f"{emoji} [{agent}] {severity.upper()}: {title}" + (f" — {url}" if url else "")


def format_digest_summary(
    tasks_done: int, prs_merged: int, review_count: int,
    agents_online: int, agents_total: int,
) -> str:
    """Daily digest one-liner for IRC."""
    return (
        f"[fleet-ops] 📊 DAILY DIGEST: "
        f"{tasks_done} done, {prs_merged} merged, "
        f"{review_count} in review, "
        f"{agents_online}/{agents_total} agents online"
    )


def route_channel(severity: str = "", event_type: str = "") -> str:
    """Determine which IRC channel to use.

    Args:
        severity: Alert severity (routes critical/high to #alerts).
        event_type: Event type (routes PR events to #reviews).

    Returns:
        Channel name: #fleet, #alerts, or #reviews.
    """
    if severity in ("critical", "high"):
        return "#alerts"
    if event_type in ("pr_ready", "pr_review", "pr_merged", "stale_review"):
        return "#reviews"
    return "#fleet"