"""Deferred challenge queue (M-IV07).

Manages challenges that were skipped due to budget constraints.
When budget mode improves, deferred challenges are processed FIFO.

Flow:
  1. Challenge required but budget too tight → defer (tag task)
  2. Budget mode improves (e.g., frugal → standard) → drain queue
  3. Process oldest deferred challenges first (FIFO)
  4. Alert if deferred queue grows too large

Deferred challenges are tracked in-memory with persistence to
state/deferred_challenges.json for durability across restarts.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fleet.core.budget_modes import MODE_ORDER

logger = logging.getLogger(__name__)


# ─── Budget Mode Ordering ────────────────────────────────────────
# Derived from budget_modes.MODE_ORDER — single source of truth.

# Budget modes that defer challenges (too tight to afford)
DEFERRAL_MODES = {"frugal", "survival", "blackout"}

# Budget modes that can process deferred challenges
PROCESSING_MODES = {"blitz", "standard", "economic"}

# Budget mode strictness (higher = tighter budget)
MODE_STRICTNESS: dict[str, int] = {
    mode: idx for idx, mode in enumerate(MODE_ORDER)
}


def should_defer_challenge(budget_mode: str) -> bool:
    """Whether the current budget mode requires deferring challenges."""
    return budget_mode in DEFERRAL_MODES


def can_process_deferred(budget_mode: str) -> bool:
    """Whether the current budget mode allows processing deferred challenges."""
    return budget_mode in PROCESSING_MODES


def budget_improved(old_mode: str, new_mode: str) -> bool:
    """Whether the budget mode has improved (less strict)."""
    old = MODE_STRICTNESS.get(old_mode, 1)
    new = MODE_STRICTNESS.get(new_mode, 1)
    return new < old


# ─── Deferred Challenge Entry ────────────────────────────────────


@dataclass
class DeferredChallenge:
    """A challenge that was deferred due to budget constraints."""

    task_id: str
    task_type: str
    story_points: int
    confidence_tier: str
    deferred_at: float = 0.0        # Unix timestamp
    reason: str = ""                 # Why it was deferred
    original_budget_mode: str = ""   # Budget mode when deferred
    challenge_type: str = ""         # What type of challenge was planned
    priority: int = 0               # Higher = more important (SP-based)

    def __post_init__(self) -> None:
        if not self.deferred_at:
            self.deferred_at = time.time()
        if not self.priority:
            self.priority = self._compute_priority()

    def _compute_priority(self) -> int:
        """Compute priority based on task attributes.

        Higher priority for:
        - Higher story points
        - Trainee/community tier
        - Security-related task types
        """
        p = self.story_points

        if self.confidence_tier in ("trainee", "community"):
            p += 5  # Trainee work needs more scrutiny

        if self.task_type in ("blocker", "concern"):
            p += 10  # Security is always important

        if self.task_type == "epic":
            p += 3  # Architecture decisions matter

        return p

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "story_points": self.story_points,
            "confidence_tier": self.confidence_tier,
            "deferred_at": self.deferred_at,
            "reason": self.reason,
            "original_budget_mode": self.original_budget_mode,
            "challenge_type": self.challenge_type,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeferredChallenge:
        return cls(
            task_id=data["task_id"],
            task_type=data.get("task_type", "task"),
            story_points=data.get("story_points", 0),
            confidence_tier=data.get("confidence_tier", "standard"),
            deferred_at=data.get("deferred_at", 0.0),
            reason=data.get("reason", ""),
            original_budget_mode=data.get("original_budget_mode", ""),
            challenge_type=data.get("challenge_type", ""),
            priority=data.get("priority", 0),
        )


# ─── Deferred Challenge Queue ────────────────────────────────────


@dataclass
class QueueStatus:
    """Status of the deferred challenge queue."""

    total: int
    by_tier: dict[str, int]
    by_type: dict[str, int]
    oldest_age_seconds: float
    alert_level: str                 # "ok", "warning", "critical"
    alert_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "by_tier": self.by_tier,
            "by_type": self.by_type,
            "oldest_age_seconds": self.oldest_age_seconds,
            "alert_level": self.alert_level,
            "alert_reason": self.alert_reason,
        }


class DeferredChallengeQueue:
    """FIFO queue for deferred challenges with priority override.

    Challenges are processed in FIFO order by default, but
    high-priority items (security, trainee tier) can be bumped up.
    """

    # Thresholds for alerts
    WARNING_SIZE = 10
    CRITICAL_SIZE = 25
    WARNING_AGE_HOURS = 24
    CRITICAL_AGE_HOURS = 72

    def __init__(self, max_size: int = 100) -> None:
        self._queue: list[DeferredChallenge] = []
        self._max_size = max_size

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def enqueue(self, entry: DeferredChallenge) -> bool:
        """Add a deferred challenge to the queue.

        Returns False if queue is full.
        """
        if len(self._queue) >= self._max_size:
            return False

        # Check for duplicate task_id
        if any(e.task_id == entry.task_id for e in self._queue):
            return False

        self._queue.append(entry)
        return True

    def dequeue(self, count: int = 1) -> list[DeferredChallenge]:
        """Remove and return the next challenges to process.

        Returns up to `count` challenges, ordered by priority (highest
        first), then by age (oldest first, FIFO).

        Args:
            count: Maximum number of challenges to dequeue.

        Returns:
            List of DeferredChallenge objects to process.
        """
        if not self._queue:
            return []

        # Sort by priority desc, then by deferred_at asc (FIFO within same priority)
        sorted_queue = sorted(
            self._queue,
            key=lambda e: (-e.priority, e.deferred_at),
        )

        to_process = sorted_queue[:count]
        for entry in to_process:
            self._queue.remove(entry)

        return to_process

    def peek(self, count: int = 1) -> list[DeferredChallenge]:
        """Preview the next challenges without removing them."""
        sorted_queue = sorted(
            self._queue,
            key=lambda e: (-e.priority, e.deferred_at),
        )
        return sorted_queue[:count]

    def remove(self, task_id: str) -> bool:
        """Remove a specific task from the queue.

        Used when a task is cancelled or manually challenged.
        """
        before = len(self._queue)
        self._queue = [e for e in self._queue if e.task_id != task_id]
        return len(self._queue) < before

    def status(self) -> QueueStatus:
        """Get current queue status with alert evaluation."""
        now = time.time()

        by_tier: dict[str, int] = {}
        by_type: dict[str, int] = {}
        oldest_age = 0.0

        for entry in self._queue:
            by_tier[entry.confidence_tier] = by_tier.get(entry.confidence_tier, 0) + 1
            by_type[entry.task_type] = by_type.get(entry.task_type, 0) + 1
            age = now - entry.deferred_at
            oldest_age = max(oldest_age, age)

        alert_level, alert_reason = self._evaluate_alert(oldest_age)

        return QueueStatus(
            total=len(self._queue),
            by_tier=by_tier,
            by_type=by_type,
            oldest_age_seconds=oldest_age,
            alert_level=alert_level,
            alert_reason=alert_reason,
        )

    def _evaluate_alert(self, oldest_age_seconds: float) -> tuple[str, str]:
        """Evaluate alert level based on queue size and age."""
        oldest_hours = oldest_age_seconds / 3600

        if len(self._queue) >= self.CRITICAL_SIZE:
            return "critical", f"deferred queue has {len(self._queue)} items (>= {self.CRITICAL_SIZE})"

        if oldest_hours >= self.CRITICAL_AGE_HOURS:
            return "critical", f"oldest deferred challenge is {oldest_hours:.0f}h old (>= {self.CRITICAL_AGE_HOURS}h)"

        if len(self._queue) >= self.WARNING_SIZE:
            return "warning", f"deferred queue has {len(self._queue)} items (>= {self.WARNING_SIZE})"

        if oldest_hours >= self.WARNING_AGE_HOURS:
            return "warning", f"oldest deferred challenge is {oldest_hours:.0f}h old (>= {self.WARNING_AGE_HOURS}h)"

        return "ok", ""

    def to_list(self) -> list[dict]:
        """Serialize the entire queue."""
        return [e.to_dict() for e in self._queue]

    def load_from_list(self, data: list[dict]) -> None:
        """Load the queue from serialized data."""
        self._queue = [DeferredChallenge.from_dict(d) for d in data]

    def save(self, path: Path) -> None:
        """Persist the queue to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_list(), indent=2))

    def load(self, path: Path) -> None:
        """Load the queue from a JSON file."""
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
            self.load_from_list(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("failed to load deferred queue from %s: %s", path, e)


# ─── Drain Logic ─────────────────────────────────────────────────


def compute_drain_batch_size(
    budget_mode: str,
    queue_size: int,
) -> int:
    """Compute how many deferred challenges to process per cycle.

    More aggressive draining when budget is generous.

    Args:
        budget_mode: Current budget mode.
        queue_size: Current queue size.

    Returns:
        Number of challenges to process this cycle.
    """
    if not can_process_deferred(budget_mode) or queue_size == 0:
        return 0

    if budget_mode == "blitz":
        return min(5, queue_size)  # Aggressive: 5 per cycle
    if budget_mode == "standard":
        return min(3, queue_size)  # Moderate: 3 per cycle
    if budget_mode == "economic":
        return min(1, queue_size)  # Conservative: 1 per cycle

    return 0