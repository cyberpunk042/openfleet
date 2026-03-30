"""Artifact tracker — progressive work tracking across fleet operation cycles.

One PM task = many fleet operation cycles. Each cycle the agent does a piece
of work on the artifact. The tracker monitors completeness against the
standard and suggests readiness increases.

The agent reads the artifact object (via transpose layer), works on it,
updates it. The tracker checks: how complete is this artifact against
its standard? What fields are done? What's missing? What readiness
level does the current completeness warrant?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from fleet.core.standards import get_standard, check_standard, Standard
from fleet.core.methodology import VALID_READINESS


@dataclass
class ArtifactCompleteness:
    """How complete an artifact is against its standard."""
    artifact_type: str
    total_required: int = 0
    filled_required: int = 0
    total_optional: int = 0
    filled_optional: int = 0
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)

    @property
    def required_pct(self) -> int:
        if self.total_required == 0:
            return 100
        return int(self.filled_required / self.total_required * 100)

    @property
    def overall_pct(self) -> int:
        total = self.total_required + self.total_optional
        filled = self.filled_required + self.filled_optional
        if total == 0:
            return 100
        return int(filled / total * 100)

    @property
    def is_complete(self) -> bool:
        return len(self.missing_required) == 0

    @property
    def suggested_readiness(self) -> int:
        """Suggest a readiness value based on artifact completeness.

        Maps completeness to the valid readiness values.
        Strategic checkpoints at 0, 50, 90.
        """
        pct = self.required_pct
        if pct == 0:
            return 0
        if pct < 25:
            return 10
        if pct < 40:
            return 20
        if pct < 60:
            return 50  # checkpoint
        if pct < 75:
            return 70
        if pct < 90:
            return 80
        if pct < 100:
            return 90  # checkpoint
        # 100% required fields — check optional
        if self.overall_pct >= 90:
            return 95
        return 90


def check_artifact_completeness(
    artifact_type: str,
    obj: dict,
) -> ArtifactCompleteness:
    """Check how complete an artifact object is against its standard.

    Args:
        artifact_type: The artifact type (analysis_document, plan, etc.)
        obj: The structured artifact object.

    Returns:
        ArtifactCompleteness with field-level detail.
    """
    standard = get_standard(artifact_type)
    if not standard:
        return ArtifactCompleteness(artifact_type=artifact_type)

    result = ArtifactCompleteness(artifact_type=artifact_type)

    for rf in standard.required_fields:
        if rf.required:
            result.total_required += 1
            val = obj.get(rf.name)
            if _has_value(val):
                result.filled_required += 1
            else:
                result.missing_required.append(rf.name)
        else:
            result.total_optional += 1
            val = obj.get(rf.name)
            if _has_value(val):
                result.filled_optional += 1
            else:
                result.missing_optional.append(rf.name)

    return result


def _has_value(val) -> bool:
    """Check if a field has a meaningful value."""
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    if isinstance(val, list) and len(val) == 0:
        return False
    if isinstance(val, dict) and len(val) == 0:
        return False
    return True


def format_completeness_summary(completeness: ArtifactCompleteness) -> str:
    """Format completeness as a short summary for task comments."""
    status = "COMPLETE" if completeness.is_complete else "IN PROGRESS"
    parts = [
        f"Artifact: {completeness.artifact_type} — {status}",
        f"Required: {completeness.filled_required}/{completeness.total_required} "
        f"({completeness.required_pct}%)",
    ]
    if completeness.missing_required:
        parts.append(f"Missing: {', '.join(completeness.missing_required)}")
    if completeness.total_optional > 0:
        parts.append(
            f"Optional: {completeness.filled_optional}/{completeness.total_optional}"
        )
    parts.append(f"Suggested readiness: {completeness.suggested_readiness}%")
    return " | ".join(parts)