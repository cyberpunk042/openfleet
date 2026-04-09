"""Fleet task comment formatters.

Produces structured markdown for MC task comments:
accept, progress, complete, blocker.

Labor attribution: completion comments include a provenance table
showing what backend, model, effort level, and confidence tier
produced the work. This is infrastructure-populated — agents
don't decide their own labels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fleet.core.urls import ResolvedUrls

if TYPE_CHECKING:
    from fleet.core.labor_stamp import LaborStamp


def format_accept(plan: str, agent_name: str) -> str:
    """Format task acceptance comment."""
    return (
        f"## \u25b6\ufe0f Accepted\n\n"
        f"**Plan:** {plan}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


def format_progress(
    done: str, next_step: str, blockers: str = "none", agent_name: str = ""
) -> str:
    """Format progress update comment."""
    return (
        f"## \U0001f504 Progress Update\n\n"
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
    labor_stamp: Optional["LaborStamp"] = None,
) -> str:
    """Format task completion comment with references and labor attribution."""
    lines = ["\u2705 Completed\n"]

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

    # Trainee warning — visible BEFORE labor table if non-expert model produced this
    if labor_stamp and labor_stamp.trainee_warning:
        lines.append(f"\n{labor_stamp.trainee_warning}\n")

    # Labor attribution — provenance of the work
    if labor_stamp:
        lines.append(_format_labor_table(labor_stamp))

    stamp_label = labor_stamp.provenance_line if labor_stamp else "unknown"
    lines.append(f"\n---\n<sub>{stamp_label}</sub>")

    return "\n".join(lines)


def format_complete_no_changes(summary: str, agent_name: str = "") -> str:
    """Format completion when no code changes were needed."""
    return (
        f"## \u2705 Completed (no code changes)\n\n"
        f"### Summary\n{summary}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


def format_blocker(
    reason: str, needed: str, agent_name: str = ""
) -> str:
    """Format blocker comment."""
    return (
        f"## \U0001f6ab Blocked\n\n"
        f"**Reason:** {reason}\n"
        f"**Needed:** {needed}\n\n"
        f"---\n<sub>{agent_name}</sub>"
    )


# ─── Labor Attribution Table ──────────────────────────────────────────


def _format_labor_table(stamp: "LaborStamp") -> str:
    """Format a labor attribution table for completion comments.

    Shows what produced this work: backend, model, effort, confidence
    tier, cost, and duration. Infrastructure-populated, not self-reported.
    """
    tier_emoji = {
        "expert": "\U0001f7e2",
        "standard": "\U0001f535",
        "trainee": "\U0001f7e1",
        "community": "\U0001f7e0",
        "hybrid": "\U0001f534",
    }
    emoji = tier_emoji.get(stamp.confidence_tier, "\u26aa")

    duration_str = ""
    if stamp.duration_seconds:
        mins = stamp.duration_seconds // 60
        secs = stamp.duration_seconds % 60
        duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"

    cost_str = f"${stamp.estimated_cost_usd:.4f}" if stamp.estimated_cost_usd else "\u2014"

    lines = [
        "\n### Labor Attribution\n",
        "| | |",
        "|---|---|",
        f"| **Backend** | `{stamp.backend}` |",
        f"| **Model** | `{stamp.model}` |",
        f"| **Effort** | {stamp.effort} |",
        f"| **Confidence** | {emoji} {stamp.confidence_tier} |",
    ]
    if duration_str:
        lines.append(f"| **Duration** | {duration_str} |")
    if stamp.estimated_cost_usd:
        lines.append(f"| **Est. Cost** | {cost_str} |")
    if stamp.skills_used:
        skills = ", ".join(f"`{s}`" for s in stamp.skills_used)
        lines.append(f"| **Skills** | {skills} |")
    if stamp.iteration > 1:
        lines.append(f"| **Iteration** | {stamp.iteration} |")
    if stamp.is_trainee:
        lines.append(f"| **⚠️ Trainee** | This output requires extra review scrutiny |")

    return "\n".join(lines)