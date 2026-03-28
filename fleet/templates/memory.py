"""Fleet board memory formatters.

Produces structured markdown for MC board memory entries:
alert, decision, suggestion, PR notification.
"""

from __future__ import annotations


def format_alert(
    *,
    severity: str,
    title: str,
    details: str,
    category: str,
    agent_name: str,
) -> str:
    """Format a board memory alert entry."""
    return (
        f"## ⚠️ {severity.upper()}: {title}\n\n"
        f"**Found by:** {agent_name}\n"
        f"**Severity:** {severity}\n"
        f"**Category:** {category}\n\n"
        f"### Details\n{details}\n"
    )


def format_pr_notice(
    *,
    task_title: str,
    pr_url: str,
    agent_name: str,
    branch: str = "",
    compare_url: str = "",
) -> str:
    """Format a PR notification for board memory."""
    lines = [
        f"## 🔀 PR Ready: {task_title}\n",
        f"**PR:** [{pr_url}]({pr_url})",
        f"**Agent:** {agent_name}",
    ]
    if branch:
        branch_link = f"[`{branch}`]({compare_url})" if compare_url else f"`{branch}`"
        lines.append(f"**Branch:** {branch_link}")
    return "\n".join(lines)


def format_decision(
    *,
    title: str,
    context: str,
    decision: str,
    rationale: str,
    agent_name: str,
) -> str:
    """Format a decision record for board memory."""
    return (
        f"## 📌 Decision: {title}\n\n"
        f"**Made by:** {agent_name}\n\n"
        f"### Context\n{context}\n\n"
        f"### Decision\n{decision}\n\n"
        f"### Rationale\n{rationale}\n"
    )


def format_suggestion(
    *,
    title: str,
    observation: str,
    suggestion: str,
    benefit: str,
    agent_name: str,
    area: str = "fleet",
) -> str:
    """Format an improvement suggestion for board memory."""
    return (
        f"## 💡 Suggestion: {title}\n\n"
        f"**From:** {agent_name}\n"
        f"**Area:** {area}\n\n"
        f"### Observation\n{observation}\n\n"
        f"### Suggestion\n{suggestion}\n\n"
        f"### Expected Benefit\n{benefit}\n"
    )


def alert_tags(severity: str, category: str, project: str = "") -> list[str]:
    """Build tags for an alert entry."""
    tags = ["alert", severity, category]
    if project:
        tags.append(f"project:{project}")
    return tags


def pr_tags(project: str = "") -> list[str]:
    """Build tags for a PR notification entry."""
    tags = ["pr", "review"]
    if project:
        tags.append(f"project:{project}")
    return tags