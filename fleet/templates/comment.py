"""Fleet task comment formatters.

Produces structured markdown for MC task comments:
accept, progress, complete, blocker.
"""

from __future__ import annotations

from typing import Optional

from fleet.core.urls import ResolvedUrls


def format_accept(plan: str, agent_name: str) -> str:
    """Format task acceptance comment."""
    return (
        f"## ▶️ Accepted\n\n"
        f"**Plan:** {plan}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


def format_progress(
    done: str, next_step: str, blockers: str = "none", agent_name: str = ""
) -> str:
    """Format progress update comment."""
    return (
        f"## 🔄 Progress Update\n\n"
        f"**Done:** {done}\n"
        f"**Next:** {next_step}\n"
        f"**Blockers:** {blockers}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


def format_complete(
    *,
    summary: str,
    pr_url: str = "",
    branch: str = "",
    compare_url: str = "",
    commit_count: int = 0,
    files: list[str] = None,
    agent_name: str = "",
) -> str:
    """Format task completion comment with references."""
    lines = ["## ✅ Completed\n"]

    if pr_url:
        lines.append(f"**PR:** [{pr_url}]({pr_url})")
    if branch:
        branch_link = f"[`{branch}`]({compare_url})" if compare_url else f"`{branch}`"
        lines.append(f"**Branch:** {branch_link}")
    if commit_count:
        lines.append(f"**Commits:** {commit_count}")
    if files:
        file_list = ", ".join(f"`{f}`" for f in files[:5])
        more = f" (+{len(files) - 5} more)" if len(files) > 5 else ""
        lines.append(f"**Files:** {file_list}{more}")

    lines.append(f"\n### Summary\n{summary}")
    lines.append(f"\n---\n<sub>{agent_name}</sub>")

    return "\n".join(lines)


def format_complete_no_changes(summary: str, agent_name: str = "") -> str:
    """Format completion when no code changes were needed."""
    return (
        f"## ✅ Completed (no code changes)\n\n"
        f"### Summary\n{summary}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


def format_blocker(
    reason: str, needed: str, agent_name: str = ""
) -> str:
    """Format blocker comment."""
    return (
        f"## 🚫 Blocked\n\n"
        f"**Reason:** {reason}\n"
        f"**Needed:** {needed}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )