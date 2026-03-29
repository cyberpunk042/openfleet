"""Event display — render events differently per channel.

Same event → different format for each surface:
  IRC: compact, one-line, with emoji
  Plane: rich HTML with links and tables
  ntfy: title + body with action URL
  Heartbeat: structured data for agent processing
  Board memory: tagged, searchable, archived

> "making sure everything is properly used and in chain to do the
> proper display adapted to the channel and always cross reference,
> like when updating a task on Plane you can say it in the internal
> chat naturally."
"""

from __future__ import annotations

from fleet.core.events import FleetEvent


def render_irc(event: FleetEvent) -> str:
    """Render event as IRC message — compact, one-line."""
    data = event.data
    agent = data.get("agent", "system")
    event_type = event.type.split(".")[-1]

    templates = {
        "completed": f"[{agent}] ✅ Task completed: {data.get('summary', '?')[:50]}",
        "accepted": f"[{agent}] 📋 Task accepted — plan shared",
        "created": f"[{agent}] ➕ Subtask created: {data.get('title', '?')[:50]}",
        "approved": f"[fleet-ops] ✅ Approved: {data.get('comment', '')[:40]}",
        "rejected": f"[fleet-ops] ❌ Rejected: {data.get('comment', '')[:40]}",
        "blocked": f"[{agent}] 🚫 Blocked: {data.get('reason', '?')[:50]}",
        "message": f"[{data.get('channel', '#fleet')}] {agent}: {data.get('message', '')[:60]}",
        "mention": f"[{agent}] 💬 @{', '.join(data.get('mentions', []))}: {data.get('message', '')[:50]}",
        "posted": f"[{agent}] {'🔴' if data.get('severity') in ('critical', 'high') else '⚠️'} {data.get('severity', '?').upper()}: {data.get('title', '?')[:50]}",
        "issue_created": f"[{agent}] 📋 Plane: {data.get('title', '?')[:50]} ({data.get('project', '?')})",
        "issue_commented": f"[{agent}] 💬 Plane comment: {data.get('comment', '')[:40]}",
        "issue_updated": f"[system] 📝 Plane updated: {data.get('title', '?')[:50]}",
        "cycle_started": f"[system] 🏃 Sprint started: {data.get('cycle_name', '?')}",
        "cycle_completed": f"[system] 🏆 Sprint completed: {data.get('cycle_name', '?')}",
        "pr_merged": f"[system] 🚀 PR merged: {data.get('task_title', '?')[:40]} {data.get('pr_url', '')}",
        "online": f"[system] 🟢 {data.get('agent', '?')} online",
        "offline": f"[system] 🔴 {data.get('agent', '?')} offline",
        "stuck": f"[system] ⚠️ Agent stuck: {data.get('agent', '?')}",
    }

    return templates.get(event_type, f"[{agent}] {event.type}: {str(data)[:60]}")


def render_plane_comment(event: FleetEvent) -> str:
    """Render event as Plane issue comment HTML."""
    data = event.data
    agent = data.get("agent", "system")
    event_type = event.type.split(".")[-1]

    if event_type == "completed":
        pr_url = data.get("pr_url", "")
        pr_line = f'<p>PR: <a href="{pr_url}">{pr_url}</a></p>' if pr_url else ""
        return (
            f"<p><strong>Task completed by {agent}</strong></p>"
            f"<p>{data.get('summary', '')}</p>"
            f"{pr_line}"
        )
    elif event_type == "approved":
        return f"<p>✅ <strong>Approved</strong> by fleet-ops: {data.get('comment', '')}</p>"
    elif event_type == "rejected":
        return f"<p>❌ <strong>Rejected</strong> by fleet-ops: {data.get('comment', '')}</p>"
    elif event_type == "blocked":
        return (
            f"<p>🚫 <strong>Blocked</strong> by {agent}</p>"
            f"<p>Reason: {data.get('reason', '?')}</p>"
            f"<p>Needed: {data.get('needed', '?')}</p>"
        )
    elif event_type == "pr_merged":
        return f"<p>🚀 PR merged: <a href=\"{data.get('pr_url', '')}\">{data.get('task_title', '?')}</a></p>"

    return f"<p>[{agent}] {event.type}: {str(data)[:200]}</p>"


def render_ntfy(event: FleetEvent) -> dict:
    """Render event as ntfy notification payload."""
    data = event.data
    agent = data.get("agent", "system")
    event_type = event.type.split(".")[-1]

    severity_map = {
        "critical": "max",
        "high": "urgent",
        "medium": "high",
        "low": "default",
    }

    title_templates = {
        "completed": f"Task completed: {data.get('summary', '?')[:40]}",
        "approved": f"Approved: task by {agent}",
        "rejected": f"Rejected: task by {agent}",
        "posted": f"{data.get('severity', '?').upper()}: {data.get('title', '?')[:40]}",
        "blocked": f"Blocked: {data.get('reason', '?')[:40]}",
        "pr_merged": f"PR merged: {data.get('task_title', '?')[:40]}",
        "stuck": f"Agent stuck: {data.get('agent', '?')}",
        "offline": f"Agent offline: {data.get('agent', '?')}",
        "cycle_started": f"Sprint started: {data.get('cycle_name', '?')}",
        "cycle_completed": f"Sprint completed: {data.get('cycle_name', '?')}",
    }

    title = title_templates.get(event_type, f"{event.type}")
    priority = severity_map.get(data.get("severity", ""), "default")
    if event.priority == "urgent":
        priority = "urgent"
    elif event.priority == "important":
        priority = "high"

    return {
        "title": title,
        "message": data.get("summary", data.get("message", data.get("details", str(data)[:200]))),
        "priority": priority,
        "tags": data.get("tags", [event_type]),
        "click_url": data.get("pr_url", data.get("click_url", "")),
    }


def render_heartbeat(event: FleetEvent) -> dict:
    """Render event as structured data for agent heartbeat context."""
    data = event.data
    return {
        "type": event.type,
        "priority": event.priority,
        "time": event.time,
        "from": data.get("agent", "system"),
        "summary": (
            data.get("summary")
            or data.get("title")
            or data.get("message")
            or data.get("comment", "")
        )[:100],
        "mentions": data.get("mentions", []),
        "actions": data.get("actions", []),
        "refs": {
            k: v for k, v in {
                "pr_url": data.get("pr_url"),
                "task_id": data.get("task_id") or event.subject,
                "issue_id": data.get("issue_id"),
                "project": data.get("project"),
            }.items() if v
        },
    }


def render_board_memory(event: FleetEvent) -> dict:
    """Render event as board memory entry (content + tags)."""
    data = event.data
    agent = data.get("agent", "system")
    event_type = event.type.split(".")[-1]

    content_templates = {
        "completed": f"Task completed by {agent}: {data.get('summary', '')}. PR: {data.get('pr_url', 'n/a')}",
        "approved": f"Approved by fleet-ops: {data.get('comment', '')}",
        "rejected": f"Rejected by fleet-ops: {data.get('comment', '')}",
        "posted": f"ALERT [{data.get('severity', '?')}]: {data.get('title', '')}: {data.get('details', '')}",
        "pr_merged": f"PR merged: {data.get('task_title', '')} — {data.get('pr_url', '')}",
        "issue_created": f"Plane issue created: {data.get('title', '')} ({data.get('project', '')})",
    }

    content = content_templates.get(event_type, f"[{event.type}] {str(data)[:200]}")

    tags = list(data.get("tags", []))
    tags.append(event_type)
    if data.get("project"):
        tags.append(f"project:{data['project']}")

    return {
        "content": content[:500],
        "tags": tags,
        "source": agent,
    }