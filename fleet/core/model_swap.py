"""LocalAI model swap management (M-BR05).

Router-initiated model swaps for LocalAI's single-active-backend
constraint. The router decides when to swap, not agents.

Design doc requirement:
> Router-initiated model swaps (not agent-initiated).
> Swap protocol: check queue → initiate → wait → verify → route.
> Swap metrics (duration, frequency, which models).
> Skip-swap logic when next task needs current model.

Hot-swap protocol:
  1. Router decides task needs a different model
  2. Check if queued tasks need the current model (skip-swap logic)
  3. If swap needed: record start, initiate, wait for health, record end
  4. Route task to newly loaded model
  5. Labor stamp records model_swap_time_s in metadata
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# ─── Swap Record ───────────────────────────────────────────────


@dataclass
class SwapRecord:
    """Record of a single model swap event."""

    from_model: str
    to_model: str
    initiated_at: float = 0.0
    completed_at: float = 0.0
    success: bool = False
    reason: str = ""            # Why the swap was needed
    skipped: bool = False       # Was swap skipped (skip-swap logic)?
    skip_reason: str = ""
    error: str = ""

    def __post_init__(self) -> None:
        if not self.initiated_at:
            self.initiated_at = time.time()

    @property
    def duration_seconds(self) -> float:
        if not self.completed_at or not self.initiated_at:
            return 0.0
        return self.completed_at - self.initiated_at

    def to_dict(self) -> dict:
        return {
            "from_model": self.from_model,
            "to_model": self.to_model,
            "duration_seconds": round(self.duration_seconds, 1),
            "success": self.success,
            "skipped": self.skipped,
            "reason": self.reason,
            "skip_reason": self.skip_reason,
            "error": self.error,
        }


# ─── Swap Decision ─────────────────────────────────────────────


@dataclass
class SwapDecision:
    """Result of evaluating whether a swap is needed."""

    needed: bool
    current_model: str
    requested_model: str
    should_skip: bool = False
    skip_reason: str = ""

    @property
    def should_swap(self) -> bool:
        return self.needed and not self.should_skip


# ─── Queue Item ────────────────────────────────────────────────


@dataclass
class QueuedTask:
    """A task waiting in the queue, used for skip-swap logic."""

    task_id: str
    required_model: str
    priority: int = 0           # Higher = more important
    queued_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.queued_at:
            self.queued_at = time.time()


# ─── Model Swap Manager ───────────────────────────────────────


class ModelSwapManager:
    """Manages LocalAI model swaps with skip-swap intelligence.

    The swap manager does NOT call LocalAI directly — it makes swap
    decisions and records metrics. The caller executes the actual swap.
    """

    def __init__(
        self,
        current_model: str = "hermes-3b",
        max_records: int = 100,
    ) -> None:
        self.current_model = current_model
        self._records: list[SwapRecord] = []
        self._queue: list[QueuedTask] = []
        self._max_records = max_records

    # ─── Queue Management ───────────────────────────────────────

    def enqueue(self, task: QueuedTask) -> None:
        """Add a task to the pending queue."""
        self._queue.append(task)

    def dequeue(self, task_id: str) -> Optional[QueuedTask]:
        """Remove a task from the queue."""
        for i, t in enumerate(self._queue):
            if t.task_id == task_id:
                return self._queue.pop(i)
        return None

    def clear_queue(self) -> None:
        self._queue.clear()

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    def queued_models(self) -> list[str]:
        """Models needed by queued tasks."""
        return list({t.required_model for t in self._queue})

    # ─── Swap Decision ──────────────────────────────────────────

    def evaluate_swap(self, requested_model: str) -> SwapDecision:
        """Evaluate whether a model swap is needed and worthwhile.

        Skip-swap logic: if the next queued task needs the current model,
        don't swap away from it — use a different backend instead.
        """
        if requested_model == self.current_model:
            return SwapDecision(
                needed=False,
                current_model=self.current_model,
                requested_model=requested_model,
            )

        # Check if queued tasks need the current model
        current_model_queued = sum(
            1 for t in self._queue if t.required_model == self.current_model
        )
        requested_model_queued = sum(
            1 for t in self._queue if t.required_model == requested_model
        )

        # If more queued tasks need the current model, skip the swap
        if current_model_queued > requested_model_queued:
            return SwapDecision(
                needed=True,
                current_model=self.current_model,
                requested_model=requested_model,
                should_skip=True,
                skip_reason=(
                    f"{current_model_queued} queued tasks need {self.current_model}, "
                    f"only {requested_model_queued} need {requested_model}"
                ),
            )

        return SwapDecision(
            needed=True,
            current_model=self.current_model,
            requested_model=requested_model,
        )

    # ─── Swap Recording ─────────────────────────────────────────

    def record_swap(self, record: SwapRecord) -> None:
        """Record a completed swap."""
        if record.success and not record.skipped:
            self.current_model = record.to_model
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

    def record_successful_swap(
        self,
        from_model: str,
        to_model: str,
        duration_seconds: float,
        reason: str = "",
    ) -> SwapRecord:
        """Record a successful swap with timing."""
        now = time.time()
        record = SwapRecord(
            from_model=from_model,
            to_model=to_model,
            initiated_at=now - duration_seconds,
            completed_at=now,
            success=True,
            reason=reason,
        )
        self.record_swap(record)
        return record

    def record_skipped_swap(
        self,
        from_model: str,
        to_model: str,
        skip_reason: str,
    ) -> SwapRecord:
        """Record a skipped swap."""
        record = SwapRecord(
            from_model=from_model,
            to_model=to_model,
            skipped=True,
            skip_reason=skip_reason,
        )
        self.record_swap(record)
        return record

    def record_failed_swap(
        self,
        from_model: str,
        to_model: str,
        error: str,
        duration_seconds: float = 0.0,
    ) -> SwapRecord:
        """Record a failed swap."""
        now = time.time()
        record = SwapRecord(
            from_model=from_model,
            to_model=to_model,
            initiated_at=now - duration_seconds,
            completed_at=now,
            success=False,
            error=error,
        )
        self.record_swap(record)
        return record

    # ─── Stamp Metadata ─────────────────────────────────────────

    def swap_metadata(self, swap: SwapRecord) -> dict:
        """Metadata to attach to a labor stamp for swapped tasks."""
        return {
            "model_swap": True,
            "swap_from": swap.from_model,
            "swap_to": swap.to_model,
            "model_swap_time_s": round(swap.duration_seconds, 1),
            "swap_skipped": swap.skipped,
        }

    # ─── Metrics ────────────────────────────────────────────────

    @property
    def total_swaps(self) -> int:
        return sum(1 for r in self._records if r.success and not r.skipped)

    @property
    def total_skipped(self) -> int:
        return sum(1 for r in self._records if r.skipped)

    @property
    def total_failed(self) -> int:
        return sum(1 for r in self._records if not r.success and not r.skipped)

    def avg_swap_duration(self) -> float:
        """Average duration of successful swaps."""
        successful = [r for r in self._records if r.success and not r.skipped]
        if not successful:
            return 0.0
        return sum(r.duration_seconds for r in successful) / len(successful)

    def swap_frequency(self) -> dict[str, int]:
        """How often each model pair is swapped."""
        freq: dict[str, int] = {}
        for r in self._records:
            if r.success and not r.skipped:
                key = f"{r.from_model} → {r.to_model}"
                freq[key] = freq.get(key, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    def model_load_count(self) -> dict[str, int]:
        """How often each model was loaded."""
        counts: dict[str, int] = {}
        for r in self._records:
            if r.success and not r.skipped:
                counts[r.to_model] = counts.get(r.to_model, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    # ─── Summary ────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "current_model": self.current_model,
            "queue_size": self.queue_size,
            "total_swaps": self.total_swaps,
            "total_skipped": self.total_skipped,
            "total_failed": self.total_failed,
            "avg_swap_duration_seconds": round(self.avg_swap_duration(), 1),
            "swap_frequency": self.swap_frequency(),
            "model_load_count": self.model_load_count(),
        }

    def format_report(self) -> str:
        """Format swap metrics as markdown."""
        s = self.summary()
        lines = [
            "## LocalAI Model Swap Report",
            "",
            f"**Current model:** {s['current_model']}",
            f"**Queue size:** {s['queue_size']}",
            f"**Total swaps:** {s['total_swaps']}",
            f"**Skipped swaps:** {s['total_skipped']}",
            f"**Failed swaps:** {s['total_failed']}",
            f"**Avg swap duration:** {s['avg_swap_duration_seconds']:.1f}s",
            "",
        ]

        if s["swap_frequency"]:
            lines.append("### Swap Frequency")
            for pair, count in s["swap_frequency"].items():
                lines.append(f"- {pair}: {count}")
            lines.append("")

        if s["model_load_count"]:
            lines.append("### Model Load Count")
            for model, count in s["model_load_count"].items():
                lines.append(f"- {model}: {count}")

        return "\n".join(lines)