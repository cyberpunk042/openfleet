"""Codex adversarial review integration (M-BR06).

Trigger and decision layer for adversarial reviews using the
codex-plugin-cc Claude Code plugin. The plugin provides:
  /codex:review              — standard code review
  /codex:adversarial-review  — challenges design decisions
  /codex:rescue              — delegate tasks to Codex

This module decides WHEN to trigger reviews based on confidence
tier and budget mode. Execution happens via the plugin's slash
commands inside Claude Code agent sessions.

Design doc requirement:
> Codex CLI wrapper for adversarial reviews.
> Triggered by confidence tier and budget mode.
> Output posted as PR review comment.
> Optional: point Codex at LocalAI for free adversarial review.

Integration:
  Plugin: openai/codex-plugin-cc (installed via setup IaC)
  Config: .codex/config.toml (project-level)
  Auth:   Codex CLI auth (ChatGPT subscription or OpenAI API key)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.tier_progression import VALID_TIERS


# ─── Review Trigger ────────────────────────────────────────────


# Tiers that trigger adversarial review.
# "trainee" and "trainee-validated" are from tier_progression.VALID_TIERS.
# "community" and "hybrid" are labor_stamp confidence tiers (non-validated backends).
REVIEW_TIERS = {"trainee", "trainee-validated", "community", "hybrid"}

# Validate that tier_progression tiers we reference actually exist
assert "trainee" in VALID_TIERS
assert "trainee-validated" in VALID_TIERS

# Budget modes where Codex review is allowed (costs OpenAI tokens)
REVIEW_BUDGET_MODES = {"blitz", "standard", "economic"}

# Budget modes where we use LocalAI instead of Codex (free)
FREE_REVIEW_MODES = {"frugal", "survival"}

# Plugin slash commands
CODEX_REVIEW_CMD = "/codex:review"
CODEX_ADVERSARIAL_CMD = "/codex:adversarial-review"
CODEX_RESCUE_CMD = "/codex:rescue"


def should_trigger_review(
    confidence_tier: str,
    budget_mode: str,
    task_type: str = "",
    force: bool = False,
) -> tuple[bool, str]:
    """Decide whether to trigger a Codex adversarial review.

    Returns (should_review, reason).
    """
    if force:
        return True, "forced by caller"

    if budget_mode == "blackout":
        return False, "blackout mode — no reviews allowed"

    if confidence_tier not in REVIEW_TIERS:
        return False, f"tier '{confidence_tier}' does not require adversarial review"

    if budget_mode in FREE_REVIEW_MODES:
        return True, (
            f"review needed (tier={confidence_tier}), "
            f"will use LocalAI (free, mode={budget_mode})"
        )

    if budget_mode in REVIEW_BUDGET_MODES:
        return True, (
            f"review needed (tier={confidence_tier}), "
            f"will use Codex plugin (mode={budget_mode})"
        )

    return False, f"budget mode '{budget_mode}' not configured for reviews"


def review_backend(budget_mode: str) -> str:
    """Which backend to use for adversarial review.

    In frugal/survival modes, point at LocalAI for free review.
    Otherwise, use Codex plugin (which uses OpenAI API).
    """
    if budget_mode in FREE_REVIEW_MODES:
        return "localai"
    return "codex-plugin"


def review_command(budget_mode: str, adversarial: bool = True) -> str:
    """Which plugin slash command to use.

    Returns the slash command string that an agent would invoke.
    """
    if budget_mode in FREE_REVIEW_MODES:
        # Free mode: no Codex, use LocalAI challenge system instead
        return ""
    if adversarial:
        return CODEX_ADVERSARIAL_CMD
    return CODEX_REVIEW_CMD


# ─── Review Request ────────────────────────────────────────────


@dataclass
class CodexReviewRequest:
    """A request to run a Codex adversarial review via the plugin."""

    pr_number: int
    repo: str                    # owner/repo
    confidence_tier: str
    budget_mode: str
    task_type: str = ""
    files_changed: list[str] = field(default_factory=list)
    adversarial: bool = True     # Use adversarial-review vs standard review
    instructions: str = ""       # Custom review instructions

    @property
    def backend(self) -> str:
        return review_backend(self.budget_mode)

    @property
    def command(self) -> str:
        return review_command(self.budget_mode, self.adversarial)

    @property
    def uses_codex(self) -> bool:
        return self.backend == "codex-plugin"

    def to_agent_instruction(self) -> str:
        """Build the instruction an agent would receive to trigger the review.

        This is what gets injected into an agent's task context so it
        knows to invoke the Codex plugin for adversarial review.
        """
        if not self.uses_codex:
            return (
                f"Review PR #{self.pr_number} in {self.repo} using "
                f"the local challenge system (budget mode: {self.budget_mode})."
            )

        parts = [
            f"Run `{self.command}` on PR #{self.pr_number} in {self.repo}.",
        ]
        if self.files_changed:
            parts.append(f"Focus on: {', '.join(self.files_changed)}")
        if self.instructions:
            parts.append(f"Additional focus: {self.instructions}")
        parts.append(
            "Post the review output as a PR comment with issues, "
            "severity, and recommended fixes."
        )
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "pr_number": self.pr_number,
            "repo": self.repo,
            "confidence_tier": self.confidence_tier,
            "budget_mode": self.budget_mode,
            "backend": self.backend,
            "command": self.command,
            "adversarial": self.adversarial,
            "task_type": self.task_type,
            "files_changed": self.files_changed,
        }


# ─── Review Result ─────────────────────────────────────────────


@dataclass
class CodexReviewResult:
    """Result of a Codex adversarial review."""

    pr_number: int
    repo: str
    review_backend: str
    raw_output: str
    issues_found: int = 0
    severity_counts: dict[str, int] = field(default_factory=dict)
    approved: bool = False
    duration_seconds: float = 0.0
    error: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    @property
    def passed(self) -> bool:
        return not self.error and self.approved

    def to_pr_comment(self) -> str:
        """Format review result as a PR review comment."""
        lines = [
            "## Adversarial Review",
            "",
            f"**Backend:** {self.review_backend}",
            f"**Issues found:** {self.issues_found}",
        ]

        if self.severity_counts:
            severity_parts = [
                f"{sev}: {count}" for sev, count in self.severity_counts.items()
            ]
            lines.append(f"**Severity:** {', '.join(severity_parts)}")

        verdict = "APPROVED" if self.approved else "CHANGES REQUESTED"
        lines.append(f"**Verdict:** {verdict}")
        lines.append("")

        if self.raw_output:
            lines.append("### Details")
            lines.append("")
            lines.append(self.raw_output)

        if self.error:
            lines.append("")
            lines.append(f"**Error:** {self.error}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "pr_number": self.pr_number,
            "repo": self.repo,
            "review_backend": self.review_backend,
            "issues_found": self.issues_found,
            "severity_counts": self.severity_counts,
            "approved": self.approved,
            "passed": self.passed,
            "duration_seconds": round(self.duration_seconds, 1),
            "error": self.error,
        }


# ─── Review Tracker ────────────────────────────────────────────


class CodexReviewTracker:
    """Tracks adversarial review history and metrics."""

    def __init__(self, max_results: int = 100) -> None:
        self._results: list[CodexReviewResult] = []
        self._max_results = max_results

    def record(self, result: CodexReviewResult) -> None:
        self._results.append(result)
        if len(self._results) > self._max_results:
            self._results = self._results[-self._max_results:]

    @property
    def total_reviews(self) -> int:
        return len(self._results)

    @property
    def approval_rate(self) -> float:
        if not self._results:
            return 0.0
        approved = sum(1 for r in self._results if r.approved)
        return approved / len(self._results)

    @property
    def avg_issues(self) -> float:
        if not self._results:
            return 0.0
        return sum(r.issues_found for r in self._results) / len(self._results)

    def by_backend(self) -> dict[str, int]:
        """Review count by backend."""
        counts: dict[str, int] = {}
        for r in self._results:
            counts[r.review_backend] = counts.get(r.review_backend, 0) + 1
        return counts

    def summary(self) -> dict:
        return {
            "total_reviews": self.total_reviews,
            "approval_rate": round(self.approval_rate, 3),
            "avg_issues_found": round(self.avg_issues, 1),
            "by_backend": self.by_backend(),
        }

    def format_report(self) -> str:
        s = self.summary()
        lines = [
            "## Codex Adversarial Review Report",
            "",
            f"**Total reviews:** {s['total_reviews']}",
            f"**Approval rate:** {s['approval_rate']:.1%}",
            f"**Avg issues found:** {s['avg_issues_found']:.1f}",
            "",
        ]
        if s["by_backend"]:
            lines.append("### Reviews by Backend")
            for backend, count in s["by_backend"].items():
                lines.append(f"- {backend}: {count}")
        return "\n".join(lines)