"""Scenario challenge for bug fixes (M-IV05).

Reproduce-and-break testing that verifies bug fixes address root causes:

  1. Reproduction   — Does the original bug still occur without the fix?
  2. Boundary       — Do edge cases around the fix trigger regressions?
  3. Concurrency    — Does the fix hold under concurrent access?
  4. Removal        — Remove the fix: does the original bug return?
  5. Interaction    — Does the fix interact poorly with recent changes?

Each scenario produces a pass/fail with evidence trail.
Used for bug fixes with SP >= 3 (from challenge type selection).

PO requirement (verbatim):
> "remove fix, does the original bug return?"
> "challenged and challenged in order to really fix the bugs"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.challenge import ChallengeFinding, ChallengeType
from fleet.core.models import Task


# ─── Scenario Types ──────────────────────────────────────────────


class ScenarioType:
    """Types of scenarios for bug fix validation."""

    REPRODUCTION = "reproduction"       # Reproduce original bug conditions
    BOUNDARY = "boundary"               # Edge cases around the fix
    CONCURRENCY = "concurrency"         # Concurrent access patterns
    REMOVAL = "removal"                 # Remove fix, verify bug returns
    INTERACTION = "interaction"         # Interaction with other changes
    REGRESSION = "regression"           # Ensure fix doesn't break existing


# ─── Scenario Definition ─────────────────────────────────────────


@dataclass
class Scenario:
    """A single test scenario for bug fix validation."""

    scenario_type: str              # ScenarioType value
    description: str                # What to test
    steps: list[str]                # Ordered steps to execute
    expected_outcome: str           # What should happen if fix is correct
    severity_if_failed: str = "major"  # Severity if this scenario fails

    def to_finding(
        self,
        finding_id: str,
        round_number: int,
        evidence: str = "",
    ) -> ChallengeFinding:
        """Convert a failed scenario to a ChallengeFinding."""
        return ChallengeFinding(
            finding_id=finding_id,
            round_number=round_number,
            challenge_type=ChallengeType.SCENARIO,
            category=self.scenario_type,
            severity=self.severity_if_failed,
            description=f"Scenario failed: {self.description}",
            evidence=evidence or f"Expected: {self.expected_outcome}",
        )

    def to_dict(self) -> dict:
        return {
            "type": self.scenario_type,
            "description": self.description,
            "steps": self.steps,
            "expected": self.expected_outcome,
            "severity_if_failed": self.severity_if_failed,
        }


# ─── Scenario Result ─────────────────────────────────────────────


@dataclass
class ScenarioResult:
    """Result of executing a single scenario."""

    scenario: Scenario
    passed: bool
    evidence: str = ""              # Test output, logs, etc.
    actual_outcome: str = ""        # What actually happened

    @property
    def failed(self) -> bool:
        return not self.passed


# ─── Scenario Generation ─────────────────────────────────────────


def generate_bug_fix_scenarios(
    task: Task,
    diff: str,
    bug_description: str = "",
) -> list[Scenario]:
    """Generate test scenarios for a bug fix.

    Analyzes the diff and bug description to produce targeted
    scenarios that verify the fix addresses the root cause.

    Args:
        task: The bug fix task.
        diff: Unified diff of the fix.
        bug_description: Description of the original bug.

    Returns:
        List of Scenario objects to execute.
    """
    scenarios: list[Scenario] = []
    files = _extract_changed_files(diff)
    bug_desc = bug_description or task.description or task.title

    # 1. Reproduction — always included for bug fixes
    scenarios.append(Scenario(
        scenario_type=ScenarioType.REPRODUCTION,
        description=f"Reproduce original bug conditions: {_truncate(bug_desc, 80)}",
        steps=[
            "Set up the conditions that triggered the original bug",
            "Verify the bug no longer occurs with the fix applied",
            "Confirm the fix addresses the root cause, not just the symptom",
        ],
        expected_outcome="Original bug should not reproduce with fix applied",
        severity_if_failed="critical",
    ))

    # 2. Removal — always included (PO requirement)
    scenarios.append(Scenario(
        scenario_type=ScenarioType.REMOVAL,
        description="Remove the fix and verify the original bug returns",
        steps=[
            "Revert the changes in the diff",
            "Reproduce the original bug conditions",
            "Verify the bug reappears (confirms fix targets root cause)",
        ],
        expected_outcome="Bug should reappear when fix is removed",
        severity_if_failed="critical",
    ))

    # 3. Regression — always included
    scenarios.append(Scenario(
        scenario_type=ScenarioType.REGRESSION,
        description="Run full test suite to verify fix introduces no regressions",
        steps=[
            "Run pytest with full test suite",
            "Verify no previously passing tests now fail",
            f"Pay special attention to tests in: {', '.join(files[:3]) or 'affected modules'}",
        ],
        expected_outcome="All previously passing tests still pass",
        severity_if_failed="critical",
    ))

    # 4. Boundary — if the diff contains numeric comparisons or conditionals
    if _has_boundary_conditions(diff):
        scenarios.append(Scenario(
            scenario_type=ScenarioType.BOUNDARY,
            description="Test boundary values around the fix",
            steps=[
                "Identify numeric thresholds or conditional boundaries in the fix",
                "Test with values at, just below, and just above each boundary",
                "Test with zero, negative, and maximum values",
            ],
            expected_outcome="Fix handles all boundary conditions correctly",
            severity_if_failed="major",
        ))

    # 5. Concurrency — if the diff touches async/threading/shared state
    if _has_concurrency_patterns(diff):
        scenarios.append(Scenario(
            scenario_type=ScenarioType.CONCURRENCY,
            description="Test fix under concurrent access",
            steps=[
                "Execute the fixed code path from multiple threads/coroutines",
                "Check for race conditions, deadlocks, or data corruption",
                "Verify shared state is properly protected",
            ],
            expected_outcome="Fix is thread-safe and handles concurrent access",
            severity_if_failed="critical",
        ))

    # 6. Interaction — if the diff touches multiple files
    if len(files) > 1:
        scenarios.append(Scenario(
            scenario_type=ScenarioType.INTERACTION,
            description="Verify fix doesn't conflict with other recent changes",
            steps=[
                f"Check {len(files)} modified files for cross-module consistency",
                "Verify imports and function signatures are consistent",
                "Check that callers of modified functions still work correctly",
            ],
            expected_outcome="Fix integrates cleanly with surrounding code",
            severity_if_failed="major",
        ))

    return scenarios


# ─── Scenario Evaluation ─────────────────────────────────────────


def evaluate_scenario_results(
    scenarios: list[Scenario],
    results: list[ScenarioResult],
    round_number: int = 1,
) -> list[ChallengeFinding]:
    """Convert failed scenario results to ChallengeFinding objects.

    Args:
        scenarios: The scenarios that were executed (unused, kept for API symmetry).
        results: Results from executing each scenario.
        round_number: Current challenge round number.

    Returns:
        List of findings for failed scenarios only.
    """
    findings: list[ChallengeFinding] = []
    for i, result in enumerate(results, 1):
        if result.failed:
            finding = result.scenario.to_finding(
                finding_id=f"sc{round_number}-{i}",
                round_number=round_number,
                evidence=result.evidence or result.actual_outcome,
            )
            findings.append(finding)
    return findings


def scenario_summary(results: list[ScenarioResult]) -> dict:
    """Summarize scenario results.

    Args:
        results: List of scenario results.

    Returns:
        Summary dict with counts and details.
    """
    passed = [r for r in results if r.passed]
    failed = [r for r in results if r.failed]

    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "all_passed": len(failed) == 0,
        "failed_scenarios": [
            {
                "type": r.scenario.scenario_type,
                "description": r.scenario.description,
                "actual": r.actual_outcome,
            }
            for r in failed
        ],
    }


# ─── Pattern Detection (for scenario selection) ──────────────────


def _has_boundary_conditions(diff: str) -> bool:
    """Check if the diff contains numeric comparisons or conditionals."""
    return bool(re.search(
        r'^\+.*([<>=!]=?\s*\d+|\brange\b|\blen\b.*[<>=])',
        diff, re.MULTILINE,
    ))


def _has_concurrency_patterns(diff: str) -> bool:
    """Check if the diff touches async, threading, or shared state patterns."""
    return bool(re.search(
        r'^\+.*\b(async|await|threading|Lock|Semaphore|Queue|atomic|gather|concurrent)\b',
        diff, re.MULTILINE,
    ))


def _extract_changed_files(diff: str) -> list[str]:
    """Extract file paths from unified diff headers."""
    files = []
    for match in re.finditer(r'^(?:\+\+\+|---) [ab]/(.+)$', diff, re.MULTILINE):
        path = match.group(1)
        if path not in files and path != "/dev/null":
            files.append(path)
    return files


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."