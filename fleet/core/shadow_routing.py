"""Shadow routing — dual-route tasks for model comparison (M-MU03).

Sends the same task to both the current (production) model and a
candidate model, compares outputs, and records the comparison.
This validates new models in production-like conditions without
affecting the live pipeline.

Design doc requirement:
> Router sends tasks to both old and new model.
> Compare outputs.
> Record comparison in labor stamp metadata.
> Dashboard: shadow comparison results.

Shadow routing is non-blocking: the production model's response is
always used. The candidate's response is recorded for analysis only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# ─── Shadow Result ─────────────────────────────────────────────


@dataclass
class ShadowResult:
    """Result of a single shadow comparison between two models."""

    task_id: str
    task_type: str

    # Production model
    production_model: str
    production_response: str
    production_latency_seconds: float
    production_passed: bool

    # Candidate model
    candidate_model: str
    candidate_response: str
    candidate_latency_seconds: float
    candidate_passed: bool

    # Comparison
    responses_agree: bool = False
    quality_notes: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    @property
    def candidate_faster(self) -> bool:
        return self.candidate_latency_seconds < self.production_latency_seconds

    @property
    def latency_diff_seconds(self) -> float:
        return self.candidate_latency_seconds - self.production_latency_seconds

    @property
    def candidate_upgrade_worthy(self) -> bool:
        """Whether the candidate performed at least as well as production."""
        return self.candidate_passed and self.responses_agree

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "production_model": self.production_model,
            "production_latency": round(self.production_latency_seconds, 3),
            "production_passed": self.production_passed,
            "candidate_model": self.candidate_model,
            "candidate_latency": round(self.candidate_latency_seconds, 3),
            "candidate_passed": self.candidate_passed,
            "responses_agree": self.responses_agree,
            "candidate_faster": self.candidate_faster,
            "candidate_upgrade_worthy": self.candidate_upgrade_worthy,
            "quality_notes": self.quality_notes,
            "timestamp": self.timestamp,
        }

    def to_stamp_metadata(self) -> dict:
        """Metadata to attach to a labor stamp for shadow-routed tasks."""
        return {
            "shadow_routing": True,
            "shadow_candidate_model": self.candidate_model,
            "shadow_candidate_passed": self.candidate_passed,
            "shadow_responses_agree": self.responses_agree,
            "shadow_candidate_latency": round(self.candidate_latency_seconds, 3),
            "shadow_candidate_faster": self.candidate_faster,
        }


# ─── Shadow Comparison ─────────────────────────────────────────


def compare_responses(
    production_response: str,
    candidate_response: str,
    expected_contains: Optional[list[str]] = None,
    expected_json_keys: Optional[list[str]] = None,
) -> tuple[bool, bool, str]:
    """Compare two model responses.

    Returns (production_passed, candidate_passed, agreement_notes).
    """
    import json

    prod_passed = True
    cand_passed = True
    notes_parts: list[str] = []

    # Check expected substrings
    if expected_contains:
        prod_lower = production_response.lower()
        cand_lower = candidate_response.lower()
        prod_has = all(s.lower() in prod_lower for s in expected_contains)
        cand_has = all(s.lower() in cand_lower for s in expected_contains)
        if not prod_has:
            prod_passed = False
            notes_parts.append("production missing expected strings")
        if not cand_has:
            cand_passed = False
            notes_parts.append("candidate missing expected strings")

    # Check JSON structure
    if expected_json_keys:
        for label, text, passed_ref in [
            ("production", production_response, "prod"),
            ("candidate", candidate_response, "cand"),
        ]:
            try:
                clean = text.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                parsed = json.loads(clean)
                if not all(k in parsed for k in expected_json_keys):
                    if label == "production":
                        prod_passed = False
                    else:
                        cand_passed = False
                    notes_parts.append(f"{label} missing JSON keys")
            except (json.JSONDecodeError, IndexError):
                if label == "production":
                    prod_passed = False
                else:
                    cand_passed = False
                notes_parts.append(f"{label} invalid JSON")

    # No expectations = both pass
    if not expected_contains and not expected_json_keys:
        notes_parts.append("no expectations defined, both pass by default")

    notes = "; ".join(notes_parts) if notes_parts else "both responses acceptable"
    return prod_passed, cand_passed, notes


# ─── Shadow Router ─────────────────────────────────────────────


class ShadowRouter:
    """Tracks shadow routing comparisons between production and candidate models.

    The shadow router does NOT execute requests itself — the caller
    runs both models and feeds results here for recording and analysis.
    """

    def __init__(
        self,
        production_model: str = "hermes-3b",
        candidate_model: str = "qwen3-8b",
        max_results: int = 200,
    ) -> None:
        self.production_model = production_model
        self.candidate_model = candidate_model
        self._results: list[ShadowResult] = []
        self._max_results = max_results

    def record(self, result: ShadowResult) -> None:
        """Record a shadow comparison result."""
        self._results.append(result)
        if len(self._results) > self._max_results:
            self._results = self._results[-self._max_results:]

    def record_comparison(
        self,
        task_id: str,
        task_type: str,
        production_response: str,
        production_latency: float,
        candidate_response: str,
        candidate_latency: float,
        expected_contains: Optional[list[str]] = None,
        expected_json_keys: Optional[list[str]] = None,
    ) -> ShadowResult:
        """Record a shadow comparison from raw responses.

        Evaluates both responses and records the result.
        """
        prod_passed, cand_passed, notes = compare_responses(
            production_response, candidate_response,
            expected_contains, expected_json_keys,
        )

        result = ShadowResult(
            task_id=task_id,
            task_type=task_type,
            production_model=self.production_model,
            production_response=production_response,
            production_latency_seconds=production_latency,
            production_passed=prod_passed,
            candidate_model=self.candidate_model,
            candidate_response=candidate_response,
            candidate_latency_seconds=candidate_latency,
            candidate_passed=cand_passed,
            responses_agree=(prod_passed == cand_passed),
            quality_notes=notes,
        )
        self.record(result)
        return result

    @property
    def total_comparisons(self) -> int:
        return len(self._results)

    # ─── Agreement Metrics ──────────────────────────────────────

    @property
    def agreement_rate(self) -> float:
        """How often candidate agrees with production outcome."""
        if not self._results:
            return 0.0
        agreed = sum(1 for r in self._results if r.responses_agree)
        return agreed / len(self._results)

    @property
    def candidate_pass_rate(self) -> float:
        """How often candidate passes on its own."""
        if not self._results:
            return 0.0
        passed = sum(1 for r in self._results if r.candidate_passed)
        return passed / len(self._results)

    @property
    def production_pass_rate(self) -> float:
        """How often production passes."""
        if not self._results:
            return 0.0
        passed = sum(1 for r in self._results if r.production_passed)
        return passed / len(self._results)

    @property
    def candidate_faster_rate(self) -> float:
        """How often candidate is faster than production."""
        if not self._results:
            return 0.0
        faster = sum(1 for r in self._results if r.candidate_faster)
        return faster / len(self._results)

    @property
    def upgrade_worthy_rate(self) -> float:
        """How often candidate is at least as good as production."""
        if not self._results:
            return 0.0
        worthy = sum(1 for r in self._results if r.candidate_upgrade_worthy)
        return worthy / len(self._results)

    # ─── Latency Stats ──────────────────────────────────────────

    def avg_production_latency(self) -> float:
        if not self._results:
            return 0.0
        return sum(r.production_latency_seconds for r in self._results) / len(self._results)

    def avg_candidate_latency(self) -> float:
        if not self._results:
            return 0.0
        return sum(r.candidate_latency_seconds for r in self._results) / len(self._results)

    # ─── Per-Task-Type Breakdown ────────────────────────────────

    def by_task_type(self) -> dict[str, dict]:
        """Breakdown of shadow results by task type."""
        groups: dict[str, list[ShadowResult]] = {}
        for r in self._results:
            groups.setdefault(r.task_type, []).append(r)

        breakdown: dict[str, dict] = {}
        for task_type, results in groups.items():
            total = len(results)
            agreed = sum(1 for r in results if r.responses_agree)
            cand_passed = sum(1 for r in results if r.candidate_passed)
            breakdown[task_type] = {
                "total": total,
                "agreement_rate": round(agreed / total, 3),
                "candidate_pass_rate": round(cand_passed / total, 3),
            }
        return breakdown

    # ─── Summary ────────────────────────────────────────────────

    def summary(self) -> dict:
        """Full shadow routing summary."""
        return {
            "production_model": self.production_model,
            "candidate_model": self.candidate_model,
            "total_comparisons": self.total_comparisons,
            "agreement_rate": round(self.agreement_rate, 3),
            "candidate_pass_rate": round(self.candidate_pass_rate, 3),
            "production_pass_rate": round(self.production_pass_rate, 3),
            "candidate_faster_rate": round(self.candidate_faster_rate, 3),
            "upgrade_worthy_rate": round(self.upgrade_worthy_rate, 3),
            "avg_production_latency": round(self.avg_production_latency(), 3),
            "avg_candidate_latency": round(self.avg_candidate_latency(), 3),
            "by_task_type": self.by_task_type(),
        }

    def format_report(self) -> str:
        """Format shadow routing results as markdown."""
        s = self.summary()
        lines = [
            f"## Shadow Routing Report: {self.production_model} vs {self.candidate_model}",
            "",
            f"**Total comparisons:** {s['total_comparisons']}",
            f"**Agreement rate:** {s['agreement_rate']:.1%}",
            f"**Candidate pass rate:** {s['candidate_pass_rate']:.1%}",
            f"**Production pass rate:** {s['production_pass_rate']:.1%}",
            f"**Candidate faster:** {s['candidate_faster_rate']:.1%}",
            f"**Upgrade-worthy rate:** {s['upgrade_worthy_rate']:.1%}",
            "",
            f"**Avg production latency:** {s['avg_production_latency']:.3f}s",
            f"**Avg candidate latency:** {s['avg_candidate_latency']:.3f}s",
            "",
        ]

        if s["by_task_type"]:
            lines.append("### By Task Type")
            lines.append("")
            lines.append("| Task Type | Total | Agreement | Candidate Pass |")
            lines.append("|-----------|-------|-----------|----------------|")
            for tt, data in s["by_task_type"].items():
                lines.append(
                    f"| {tt} | {data['total']} "
                    f"| {data['agreement_rate']:.1%} "
                    f"| {data['candidate_pass_rate']:.1%} |"
                )

        verdict = "READY" if s["upgrade_worthy_rate"] >= 0.8 else "NOT READY"
        lines.append("")
        lines.append(f"**Promotion verdict:** {verdict} (threshold: 80% upgrade-worthy)")

        return "\n".join(lines)