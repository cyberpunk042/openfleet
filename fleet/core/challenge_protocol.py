"""Agent challenge protocol (M-IV03).

Orchestrates the challenge lifecycle:

  1. Evaluate whether a task needs challenge
  2. Assign the right challenger (different from author)
  3. Build challenge context (diff + requirement + summary)
  4. Start a challenge round and collect findings
  5. Determine outcome: pass, fail, re-challenge, escalate

This module coordinates between the data model (challenge.py),
automated generator (challenge_automated.py), and review gates
(review_gates.py). The orchestrator calls into this module
when tasks reach REVIEW status.

Challenge flow:
  Task completes → evaluate → assign challenger → build context →
  run challenge → findings? → author re-works → re-challenge or pass →
  advance to human review
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.challenge import (
    ChallengeRecord,
    ChallengeRound,
    ChallengeStatus,
    ChallengeType,
    ChallengeFinding,
    is_challenge_required,
    max_rounds_for_tier,
    select_challenge_type,
    select_challenger_agent,
)
from fleet.core.challenge_automated import (
    AutomatedChallenge,
    generate_automated_challenges,
)
from fleet.core.models import Task


# ─── Challenge Context ────────────────────────────────────────────


@dataclass
class ChallengeContext:
    """Everything a challenger needs to review work adversarially."""

    task_id: str
    task_type: str
    task_title: str
    requirement_verbatim: str        # PO's exact words — the anchor
    author_agent: str                # Who produced the work
    diff: str                        # Unified diff of changes
    author_summary: str = ""         # Author's description of changes
    pr_url: str = ""                 # Link to the PR
    files_changed: list[str] = field(default_factory=list)
    story_points: int = 0
    confidence_tier: str = "standard"
    round_number: int = 1
    previous_findings: list[dict] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Build the adversarial challenge prompt for a challenger agent."""
        lines = [
            "# Challenge Assignment",
            "",
            f"You are challenging work on task **{self.task_id}**: {self.task_title}",
            f"Author: {self.author_agent} | Confidence tier: {self.confidence_tier}",
            f"Round: {self.round_number} | Story points: {self.story_points}",
            "",
            "## Requirement (PO verbatim)",
            "",
            self.requirement_verbatim or "(no verbatim requirement recorded)",
            "",
            "## Author Summary",
            "",
            self.author_summary or "(no summary provided)",
            "",
        ]

        if self.pr_url:
            lines.extend(["## Pull Request", "", self.pr_url, ""])

        if self.files_changed:
            lines.extend([
                "## Files Changed",
                "",
                *[f"- {f}" for f in self.files_changed],
                "",
            ])

        lines.extend([
            "## Diff",
            "",
            "```diff",
            self.diff or "(no diff available)",
            "```",
            "",
        ])

        if self.previous_findings:
            lines.extend([
                "## Previous Findings (address status)",
                "",
                *[
                    f"- [{f.get('status', 'open')}] {f.get('description', '')}"
                    for f in self.previous_findings
                ],
                "",
            ])

        lines.extend([
            "## Instructions",
            "",
            "Find flaws. Be adversarial. Try to break this.",
            "",
            "Focus on:",
            "- Does the implementation match the requirement?",
            "- Are there edge cases, race conditions, or error paths not handled?",
            "- Could this break existing functionality?",
            "- Are tests adequate for the complexity?",
            "",
            "For each finding, report:",
            "- **Category**: regression, edge_case, logic_error, requirement_gap, "
            "security, performance, test_gap",
            "- **Severity**: critical, major, minor, info",
            "- **Description**: What is wrong and why it matters",
            "- **Evidence**: How to reproduce or verify",
        ])

        return "\n".join(lines)


# ─── Challenge Evaluation ─────────────────────────────────────────


@dataclass
class ChallengeDecision:
    """Result of evaluating whether a task needs challenge."""

    required: bool
    reason: str
    challenge_type: str = ""         # ChallengeType value
    challenger: str = ""             # Agent name or "automated"
    max_rounds: int = 2
    deferred: bool = False           # True if challenge deferred (budget)

    @property
    def is_automated(self) -> bool:
        return self.challenge_type == ChallengeType.AUTOMATED

    @property
    def is_agent(self) -> bool:
        return self.challenge_type == ChallengeType.AGENT

    def to_dict(self) -> dict:
        return {
            "required": self.required,
            "reason": self.reason,
            "challenge_type": self.challenge_type,
            "challenger": self.challenger,
            "max_rounds": self.max_rounds,
            "deferred": self.deferred,
        }


def evaluate_challenge(
    task: Task,
    confidence_tier: str = "standard",
    budget_mode: str = "standard",
    author_agent: str = "worker",
    is_bug_fix: bool = False,
) -> ChallengeDecision:
    """Evaluate whether a task needs challenge and determine parameters.

    Combines is_challenge_required(), select_challenge_type(), and
    select_challenger_agent() into a single decision.

    Args:
        task: The completed task.
        confidence_tier: Confidence tier of the work.
        budget_mode: Current budget mode.
        author_agent: Agent that produced the work.
        is_bug_fix: Whether this is a bug fix.

    Returns:
        ChallengeDecision with all parameters set.
    """
    task_type = task.custom_fields.task_type or "task"
    story_points = task.custom_fields.story_points or 0

    required, reason = is_challenge_required(
        task_type, story_points, confidence_tier, budget_mode,
    )

    if not required:
        deferred = "deferred" in reason.lower()
        return ChallengeDecision(
            required=False,
            reason=reason,
            deferred=deferred,
        )

    challenge_type = select_challenge_type(
        task_type, story_points, confidence_tier, budget_mode,
        is_bug_fix=is_bug_fix,
    )

    if challenge_type == ChallengeType.AUTOMATED:
        challenger = "automated"
    else:
        challenger = select_challenger_agent(task_type, author_agent)

    max_rounds = max_rounds_for_tier(confidence_tier)

    return ChallengeDecision(
        required=True,
        reason=reason,
        challenge_type=challenge_type,
        challenger=challenger,
        max_rounds=max_rounds,
    )


# ─── Challenge Context Builder ────────────────────────────────────


def build_challenge_context(
    task: Task,
    diff: str,
    author_summary: str = "",
    pr_url: str = "",
    round_number: int = 1,
    previous_findings: list[dict] | None = None,
) -> ChallengeContext:
    """Build the challenge context from task metadata and diff.

    Args:
        task: The task being challenged.
        diff: Unified diff of changes.
        author_summary: Author's description of the changes.
        pr_url: URL of the pull request.
        round_number: Current challenge round number.
        previous_findings: Findings from previous rounds (for re-challenge).

    Returns:
        ChallengeContext ready for challenger consumption.
    """
    from fleet.core.challenge_automated import _extract_files_from_diff

    cf = task.custom_fields
    return ChallengeContext(
        task_id=task.id,
        task_type=cf.task_type or "task",
        task_title=task.title,
        requirement_verbatim=cf.requirement_verbatim or "",
        author_agent=cf.agent_name or "unknown",
        diff=diff,
        author_summary=author_summary,
        pr_url=pr_url or cf.pr_url or "",
        files_changed=_extract_files_from_diff(diff),
        story_points=cf.story_points or 0,
        confidence_tier=cf.labor_confidence or "standard",
        round_number=round_number,
        previous_findings=previous_findings or [],
    )


# ─── Challenge Round Management ───────────────────────────────────


def start_challenge(
    task: Task,
    decision: ChallengeDecision,
    diff: str = "",
    author_summary: str = "",
) -> tuple[ChallengeRecord, list[AutomatedChallenge] | ChallengeContext]:
    """Start a challenge for a task.

    For automated challenges: runs the generator immediately and returns
    the list of challenges to execute.

    For agent challenges: builds the context and returns it for dispatch
    to the challenger agent.

    Args:
        task: The task to challenge.
        decision: The challenge decision (from evaluate_challenge).
        diff: Unified diff of changes.
        author_summary: Author's description of the changes.

    Returns:
        Tuple of (ChallengeRecord, challenges_or_context).
        - For automated: (record, list[AutomatedChallenge])
        - For agent/cross-model/scenario: (record, ChallengeContext)
    """
    record = ChallengeRecord(
        task_id=task.id,
        max_rounds=decision.max_rounds,
    )

    current_round = record.start_round(
        challenge_type=decision.challenge_type,
        challenger=decision.challenger,
    )

    if decision.is_automated:
        challenges = generate_automated_challenges(task, diff)
        return record, challenges

    # Agent, cross-model, or scenario — build context for dispatch
    context = build_challenge_context(
        task=task,
        diff=diff,
        author_summary=author_summary,
        round_number=current_round.round_number,
    )
    return record, context


def continue_challenge(
    record: ChallengeRecord,
    task: Task,
    diff: str = "",
    author_summary: str = "",
) -> ChallengeRound | ChallengeContext | None:
    """Continue a challenge with the next round.

    Called after the author has addressed findings from the previous round.
    Returns None if max rounds reached or challenge already passed.

    Args:
        record: The existing challenge record.
        task: The task being challenged.
        diff: Updated diff after author's re-work.
        author_summary: Author's description of fixes.

    Returns:
        - For automated: ChallengeRound (already started)
        - For agent: ChallengeContext (for dispatch)
        - None if no more rounds available
    """
    if not record.can_add_round:
        return None

    last_round = record.rounds[-1] if record.rounds else None
    if last_round and last_round.status == ChallengeStatus.PASSED:
        return None

    # Determine challenge type for next round — same as previous
    challenge_type = last_round.challenge_type if last_round else ChallengeType.AUTOMATED
    challenger = last_round.challenger if last_round else "automated"

    new_round = record.start_round(
        challenge_type=challenge_type,
        challenger=challenger,
    )

    if challenge_type == ChallengeType.AUTOMATED:
        return new_round

    # Agent challenge — build context with previous findings
    previous_findings = []
    for r in record.rounds[:-1]:  # Exclude current round
        for f in r.findings:
            previous_findings.append(f.to_dict())

    context = build_challenge_context(
        task=task,
        diff=diff,
        author_summary=author_summary,
        round_number=new_round.round_number,
        previous_findings=previous_findings,
    )
    return context


# ─── Finding Processing ──────────────────────────────────────────


def process_automated_findings(
    record: ChallengeRecord,
    challenges: list[AutomatedChallenge],
    results: list[bool],
) -> ChallengeRound:
    """Process results from automated challenge execution.

    Each challenge has a corresponding boolean result: True = passed,
    False = finding confirmed.

    Args:
        record: The challenge record.
        challenges: List of automated challenges.
        results: Boolean results for each challenge (True = pass).

    Returns:
        The completed challenge round.
    """
    current_round = record.rounds[-1]
    finding_count = 0

    for challenge, passed in zip(challenges, results):
        if not passed:
            finding_count += 1
            finding = challenge.to_finding(
                finding_id=f"f{record.current_round}-{finding_count}",
                round_number=record.current_round,
            )
            current_round.add_finding(finding)

    all_passed = finding_count == 0
    current_round.complete(passed=all_passed)
    return current_round


def process_agent_findings(
    record: ChallengeRecord,
    findings: list[dict],
) -> ChallengeRound:
    """Process findings from an agent challenger.

    Args:
        record: The challenge record.
        findings: List of finding dicts from the challenger agent.
            Each dict should have: category, severity, description, evidence.

    Returns:
        The completed challenge round.
    """
    current_round = record.rounds[-1]

    for i, finding_data in enumerate(findings, 1):
        finding = ChallengeFinding(
            finding_id=f"f{record.current_round}-{i}",
            round_number=record.current_round,
            challenge_type=current_round.challenge_type,
            category=finding_data.get("category", "general"),
            severity=finding_data.get("severity", "minor"),
            description=finding_data.get("description", ""),
            evidence=finding_data.get("evidence", ""),
        )
        current_round.add_finding(finding)

    all_passed = len(findings) == 0
    current_round.complete(passed=all_passed)
    return current_round


# ─── Round Outcome Evaluation ────────────────────────────────────


@dataclass
class RoundOutcome:
    """Result of evaluating a challenge round."""

    action: str             # "passed", "rechallenge", "escalate", "failed"
    reason: str
    findings_count: int = 0
    open_findings: int = 0
    rounds_completed: int = 0
    max_rounds: int = 0

    @property
    def needs_rework(self) -> bool:
        return self.action in ("rechallenge", "failed")

    @property
    def can_advance(self) -> bool:
        return self.action == "passed"

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "findings_count": self.findings_count,
            "open_findings": self.open_findings,
            "rounds_completed": self.rounds_completed,
            "max_rounds": self.max_rounds,
        }


def evaluate_round_outcome(record: ChallengeRecord) -> RoundOutcome:
    """Evaluate the outcome of the most recent challenge round.

    Determines the next action:
    - "passed": Work survived, advance to human review
    - "rechallenge": Findings found, author must rework, then re-challenge
    - "escalate": Max rounds reached with open findings, escalate to human
    - "failed": Challenge failed definitively (e.g., critical finding)

    Args:
        record: The challenge record with completed round(s).

    Returns:
        RoundOutcome describing what to do next.
    """
    if not record.rounds:
        return RoundOutcome(
            action="passed",
            reason="no challenge rounds executed",
        )

    last_round = record.rounds[-1]
    total_findings = record.total_findings
    open_findings = record.open_findings

    if last_round.status == ChallengeStatus.PASSED:
        return RoundOutcome(
            action="passed",
            reason=f"challenge round {record.current_round} passed — "
                   f"work survived {record.rounds_survived} round(s)",
            findings_count=total_findings,
            open_findings=0,
            rounds_completed=record.current_round,
            max_rounds=record.max_rounds,
        )

    # Check for critical findings — immediate escalation
    critical_findings = [
        f for r in record.rounds for f in r.findings
        if f.severity == "critical" and f.status == "open"
    ]
    if critical_findings:
        if not record.can_add_round:
            return RoundOutcome(
                action="escalate",
                reason=f"{len(critical_findings)} critical finding(s) after "
                       f"{record.current_round}/{record.max_rounds} rounds — "
                       f"escalating to human review",
                findings_count=total_findings,
                open_findings=open_findings,
                rounds_completed=record.current_round,
                max_rounds=record.max_rounds,
            )

    # More rounds available — rechallenge after rework
    if record.can_add_round:
        return RoundOutcome(
            action="rechallenge",
            reason=f"round {record.current_round} failed with "
                   f"{open_findings} open finding(s) — "
                   f"rework and re-challenge "
                   f"(round {record.current_round + 1}/{record.max_rounds})",
            findings_count=total_findings,
            open_findings=open_findings,
            rounds_completed=record.current_round,
            max_rounds=record.max_rounds,
        )

    # Max rounds reached — escalate
    return RoundOutcome(
        action="escalate",
        reason=f"max rounds ({record.max_rounds}) reached with "
               f"{open_findings} open finding(s) — "
               f"escalating to human review",
        findings_count=total_findings,
        open_findings=open_findings,
        rounds_completed=record.current_round,
        max_rounds=record.max_rounds,
    )


# ─── Task Field Updates ──────────────────────────────────────────


def apply_challenge_to_task(
    record: ChallengeRecord,
    outcome: RoundOutcome,
) -> dict:
    """Build task custom field updates from challenge results.

    Returns a dict of field name → value for TaskCustomFields update.

    Args:
        record: The challenge record.
        outcome: The round outcome.

    Returns:
        Dict of custom field updates.
    """
    fields = record.to_task_fields()
    fields["challenge_status"] = _outcome_to_status(outcome)
    return fields


def _outcome_to_status(outcome: RoundOutcome) -> str:
    """Map RoundOutcome action to ChallengeStatus value."""
    return {
        "passed": ChallengeStatus.PASSED,
        "rechallenge": ChallengeStatus.FAILED,
        "escalate": ChallengeStatus.FAILED,
        "failed": ChallengeStatus.FAILED,
    }.get(outcome.action, ChallengeStatus.PENDING)