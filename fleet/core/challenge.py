"""Challenge loop system (M-IV01) \u2014 iterative validation data model.

Four challenge types, each with different cost and depth:
  automated   \u2014 Deterministic pattern checks (free, fast)
  agent       \u2014 Domain expert reviews work adversarially
  cross-model \u2014 Different LLM challenges original work
  scenario    \u2014 Reproduce-and-break testing for bug fixes

Challenge flow:
  Work produced \u2192 challenge assigned \u2192 findings posted \u2192
  author addresses \u2192 re-challenge or pass \u2192 advance to review

PO requirement (verbatim):
> "challenged and challenged in order to really fix the bugs"
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# \u2500\u2500\u2500 Challenge Types \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


class ChallengeType(str, Enum):
    """Types of challenge, ordered by cost."""

    AUTOMATED = "automated"       # Free, deterministic pattern checks
    AGENT = "agent"               # Domain expert adversarial review
    CROSS_MODEL = "cross-model"   # Different LLM reviews work
    SCENARIO = "scenario"         # Reproduce-and-break for bug fixes


class ChallengeStatus(str, Enum):
    """Status of a challenge round."""

    PENDING = "pending"           # Challenge assigned, not started
    IN_PROGRESS = "in_progress"   # Challenger is actively reviewing
    PASSED = "passed"             # Work survived the challenge
    FAILED = "failed"             # Findings require author to address
    WAIVED = "waived"             # Challenge skipped (low risk / PO decision)
    DEFERRED = "deferred"         # Skipped due to budget, queued for later


class FindingStatus(str, Enum):
    """Status of a single challenge finding."""

    OPEN = "open"                 # Not yet addressed
    ADDRESSED = "addressed"       # Author claims fixed
    VERIFIED = "verified"         # Challenger confirmed fix
    WONT_FIX = "wont_fix"         # Accepted risk (requires PO approval)
    INVALID = "invalid"           # Finding was incorrect


# \u2500\u2500\u2500 Challenge Finding \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


@dataclass
class ChallengeFinding:
    """A single finding from a challenge round."""

    finding_id: str                # Unique ID within the challenge
    round_number: int              # Which challenge round
    challenge_type: str            # ChallengeType value
    category: str                  # edge_case, regression, race_condition, etc.
    severity: str                  # critical, major, minor, info
    description: str               # What was found
    evidence: str = ""             # Test output, logs, etc.
    status: str = "open"           # FindingStatus value
    addressed_by: str = ""         # Commit SHA or explanation
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "round": self.round_number,
            "type": self.challenge_type,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status,
            "addressed_by": self.addressed_by,
        }


# \u2500\u2500\u2500 Challenge Round \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


@dataclass
class ChallengeRound:
    """One round of challenge on a task."""

    round_number: int
    challenge_type: str            # ChallengeType value
    challenger: str                # Agent name, model ID, or "automated"
    status: str = "pending"        # ChallengeStatus value
    findings: list[ChallengeFinding] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0

    @property
    def is_complete(self) -> bool:
        return self.status in ("passed", "failed", "waived")

    @property
    def open_findings(self) -> list[ChallengeFinding]:
        return [f for f in self.findings if f.status == "open"]

    @property
    def has_open_findings(self) -> bool:
        return len(self.open_findings) > 0

    @property
    def all_findings_resolved(self) -> bool:
        return all(
            f.status in ("verified", "wont_fix", "invalid")
            for f in self.findings
        ) if self.findings else True

    def add_finding(self, finding: ChallengeFinding) -> None:
        self.findings.append(finding)

    def start(self) -> None:
        self.status = ChallengeStatus.IN_PROGRESS
        self.started_at = time.time()

    def complete(self, passed: bool) -> None:
        self.status = ChallengeStatus.PASSED if passed else ChallengeStatus.FAILED
        self.completed_at = time.time()

    def to_dict(self) -> dict:
        return {
            "round": self.round_number,
            "type": self.challenge_type,
            "challenger": self.challenger,
            "status": self.status,
            "findings_count": len(self.findings),
            "open_findings": len(self.open_findings),
        }


# \u2500\u2500\u2500 Challenge Record \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


@dataclass
class ChallengeRecord:
    """Full challenge history for a task."""

    task_id: str
    rounds: list[ChallengeRound] = field(default_factory=list)
    max_rounds: int = 3
    current_round: int = 0

    @property
    def status(self) -> str:
        """Overall challenge status."""
        if not self.rounds:
            return ChallengeStatus.PENDING
        last = self.rounds[-1]
        if last.status == ChallengeStatus.PASSED:
            if self.current_round >= len(self.rounds):
                return ChallengeStatus.PASSED
        return last.status

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.rounds)

    @property
    def open_findings(self) -> int:
        return sum(len(r.open_findings) for r in self.rounds)

    @property
    def challenge_types_faced(self) -> list[str]:
        """Unique challenge types faced, for labor stamp."""
        return list(dict.fromkeys(r.challenge_type for r in self.rounds))

    @property
    def rounds_survived(self) -> int:
        """Count of passed rounds, for labor stamp."""
        return sum(1 for r in self.rounds if r.status == ChallengeStatus.PASSED)

    @property
    def can_add_round(self) -> bool:
        """Whether more rounds are allowed."""
        return self.current_round < self.max_rounds

    def start_round(
        self,
        challenge_type: str,
        challenger: str,
    ) -> ChallengeRound:
        """Start a new challenge round."""
        self.current_round += 1
        new_round = ChallengeRound(
            round_number=self.current_round,
            challenge_type=challenge_type,
            challenger=challenger,
        )
        new_round.start()
        self.rounds.append(new_round)
        return new_round

    def to_stamp_fields(self) -> dict:
        """Extract fields for LaborStamp update."""
        return {
            "challenge_rounds_survived": self.rounds_survived,
            "challenge_types_faced": self.challenge_types_faced,
        }

    def to_task_fields(self) -> dict:
        """Extract fields for TaskCustomFields update."""
        findings_dicts = []
        for r in self.rounds:
            for f in r.findings:
                findings_dicts.append(f.to_dict())

        return {
            "challenge_round": self.current_round,
            "challenge_max_rounds": self.max_rounds,
            "challenge_status": self.status,
            "challenge_findings": findings_dicts if findings_dicts else None,
            "challenge_challenger": (
                self.rounds[-1].challenger if self.rounds else None
            ),
            "challenge_type": (
                self.rounds[-1].challenge_type if self.rounds else None
            ),
        }


# \u2500\u2500\u2500 Challenge Requirements \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def is_challenge_required(
    task_type: str,
    story_points: int,
    confidence_tier: str,
    budget_mode: str,
) -> tuple[bool, str]:
    """Determine if a challenge is required for this task.

    Returns (required, reason).
    """
    # Never challenge heartbeats
    if task_type == "heartbeat":
        return False, "heartbeats never challenged"

    # Budget mode overrides
    if budget_mode in ("survival", "blackout"):
        return False, f"{budget_mode} mode: challenges disabled"

    # Security and architecture: always mandatory
    if task_type in ("blocker", "concern"):
        return True, "security/blocker tasks always require challenge"

    # Trainee/community tier: always mandatory (if budget allows)
    if confidence_tier in ("trainee", "community"):
        if budget_mode in ("frugal",):
            return False, "frugal mode: challenge deferred for trainee work"
        return True, f"{confidence_tier} tier work requires adversarial validation"

    # Bug fixes with significant complexity
    if task_type == "bug" and story_points >= 3:
        return True, f"bug fix with SP={story_points} requires scenario challenge"

    # Complex features
    if story_points >= 5 and task_type in ("story", "epic"):
        return True, f"complex {task_type} (SP={story_points}) benefits from challenge"

    # Architecture decisions
    if task_type == "epic":
        return True, "epics always require challenge"

    # Simple/documentation: optional
    if story_points <= 2 or task_type in ("docs", "chore"):
        return False, f"low-risk {task_type} (SP={story_points}): challenge optional"

    return False, "standard task: challenge optional"


def select_challenge_type(
    task_type: str,
    story_points: int,
    confidence_tier: str,
    budget_mode: str,
    is_bug_fix: bool = False,
) -> str:
    """Select the appropriate challenge type based on context.

    Returns ChallengeType value.
    """
    # Scenario challenge for bug fixes
    if is_bug_fix and story_points >= 3:
        return ChallengeType.SCENARIO

    # Budget-constrained: automated only
    if budget_mode in ("economic", "frugal"):
        return ChallengeType.AUTOMATED

    # Trainee/community: cross-model (verify with stronger model)
    if confidence_tier in ("trainee", "community"):
        if budget_mode == "blitz":
            return ChallengeType.CROSS_MODEL
        return ChallengeType.AGENT  # Standard mode: agent challenge

    # Complex work: agent challenge
    if story_points >= 5 or task_type in ("epic", "blocker"):
        return ChallengeType.AGENT

    # Default: automated (free)
    return ChallengeType.AUTOMATED


def select_challenger_agent(
    task_type: str,
    author_agent: str,
) -> str:
    """Select which agent should challenge the work.

    The challenger must be different from the author.
    """
    if task_type in ("blocker", "concern") or "security" in (task_type or ""):
        return "devsecops-expert"

    if task_type in ("epic",) or "architect" in (task_type or ""):
        return "architect"

    if "test" in (task_type or ""):
        return "qa-engineer"

    # Default: qa-engineer if author isn't qa, otherwise software-engineer
    if author_agent == "qa-engineer":
        return "software-engineer"
    return "qa-engineer"


def max_rounds_for_tier(confidence_tier: str) -> int:
    """Maximum challenge rounds based on confidence tier."""
    return {
        "expert": 1,
        "standard": 2,
        "trainee": 3,
        "community": 3,
        "hybrid": 3,
    }.get(confidence_tier, 2)