"""Automated challenge generator (M-IV02).

Generates deterministic, zero-LLM-cost challenges from task metadata
and code diffs. Pattern-based rules catch common issues:

  1. Regression check       \u2014 run full test suite
  2. Conditional edge cases \u2014 boundary values for if/else
  3. Loop handling          \u2014 empty, single, max items
  4. Async/concurrency      \u2014 race conditions
  5. Timeout/retry          \u2014 network unavailable, extreme latency
  6. Architecture checks    \u2014 import cycles, multi-file changes

All challenges are verifiable without human intervention.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.challenge import ChallengeFinding, ChallengeType
from fleet.core.models import Task


@dataclass
class AutomatedChallenge:
    """A single automated challenge to execute."""

    category: str               # regression, edge_case, loop, async, timeout, architecture
    description: str             # What to check
    verification: str            # How to verify (command, assertion, etc.)
    severity: str = "minor"      # Severity if finding confirmed

    def to_finding(self, finding_id: str, round_number: int) -> ChallengeFinding:
        """Convert to a ChallengeFinding if the challenge reveals an issue."""
        return ChallengeFinding(
            finding_id=finding_id,
            round_number=round_number,
            challenge_type=ChallengeType.AUTOMATED,
            category=self.category,
            severity=self.severity,
            description=self.description,
            evidence=self.verification,
        )


def generate_automated_challenges(
    task: Task,
    diff: str,
    file_list: list[str] | None = None,
) -> list[AutomatedChallenge]:
    """Generate automated challenges from task metadata and code diff.

    Args:
        task: The task being challenged.
        diff: The unified diff of changes.
        file_list: List of changed file paths.

    Returns:
        List of AutomatedChallenge objects to execute.
    """
    challenges: list[AutomatedChallenge] = []
    file_list = file_list or _extract_files_from_diff(diff)

    # 1. Regression check (always)
    if _has_code_changes(file_list):
        challenges.append(AutomatedChallenge(
            category="regression",
            description="Run full test suite including previously passing tests",
            verification="pytest --tb=short -q",
            severity="critical",
        ))

    # 2. Conditional edge cases
    if _has_conditionals(diff):
        challenges.extend(_generate_conditional_challenges(diff))

    # 3. Loop handling
    if _has_loops(diff):
        challenges.extend(_generate_loop_challenges(diff))

    # 4. Async/concurrency
    if _has_async_patterns(diff):
        challenges.extend(_generate_async_challenges(diff))

    # 5. Timeout/retry patterns
    if _has_network_patterns(diff):
        challenges.extend(_generate_timeout_challenges(diff))

    # 6. Architecture checks (multi-file)
    if len(file_list) > 1:
        challenges.extend(_generate_architecture_challenges(file_list, diff))

    # 7. Error handling patterns
    if _has_error_handling(diff):
        challenges.extend(_generate_error_handling_challenges(diff))

    return challenges


# \u2500\u2500\u2500 Pattern Detection \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _has_code_changes(file_list: list[str]) -> bool:
    code_extensions = {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".sh"}
    return any(
        any(f.endswith(ext) for ext in code_extensions)
        for f in file_list
    )


def _has_conditionals(diff: str) -> bool:
    return bool(re.search(r'^\+.*\b(if|elif|else|match|case)\b', diff, re.MULTILINE))


def _has_loops(diff: str) -> bool:
    return bool(re.search(r'^\+.*\b(for|while|loop)\b', diff, re.MULTILINE))


def _has_async_patterns(diff: str) -> bool:
    return bool(re.search(r'^\+.*\b(async|await|asyncio|aiohttp|gather)\b', diff, re.MULTILINE))


def _has_network_patterns(diff: str) -> bool:
    return bool(re.search(
        r'^\+.*\b(requests\.|urllib|aiohttp|httpx|fetch|curl|timeout|retry)\b',
        diff, re.MULTILINE,
    ))


def _has_error_handling(diff: str) -> bool:
    return bool(re.search(r'^\+.*\b(try|except|raise|Error|Exception)\b', diff, re.MULTILINE))


def _extract_files_from_diff(diff: str) -> list[str]:
    """Extract file paths from unified diff headers."""
    files = []
    for match in re.finditer(r'^(?:\+\+\+|---) [ab]/(.+)$', diff, re.MULTILINE):
        path = match.group(1)
        if path not in files and path != "/dev/null":
            files.append(path)
    return files


# \u2500\u2500\u2500 Challenge Generators \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500


def _generate_conditional_challenges(diff: str) -> list[AutomatedChallenge]:
    challenges = []
    # Check for boundary values
    if re.search(r'^\+.*[<>=!]=?\s*\d+', diff, re.MULTILINE):
        challenges.append(AutomatedChallenge(
            category="edge_case",
            description="Test boundary values: 0, 1, -1, max_int at numeric comparisons",
            verification="Unit test with boundary values for all new comparisons",
            severity="major",
        ))

    # Check for None/null checks
    if re.search(r'^\+.*\bis\s+None\b|^\+.*\bis\s+not\s+None\b|^\+.*\bnot\s+\w+\b', diff, re.MULTILINE):
        challenges.append(AutomatedChallenge(
            category="edge_case",
            description="Verify None/empty handling: pass None, empty string, empty list to new code paths",
            verification="Unit test with None and empty inputs",
            severity="major",
        ))

    return challenges


def _generate_loop_challenges(diff: str) -> list[AutomatedChallenge]:
    return [
        AutomatedChallenge(
            category="loop",
            description="Test loop with empty input (zero iterations)",
            verification="Unit test with empty collection input",
            severity="major",
        ),
        AutomatedChallenge(
            category="loop",
            description="Test loop with single item input",
            verification="Unit test with single-element collection",
            severity="minor",
        ),
        AutomatedChallenge(
            category="loop",
            description="Test loop with large input (100+ items) to detect performance issues",
            verification="Unit test with large collection, check no O(n^2) behavior",
            severity="minor",
        ),
    ]


def _generate_async_challenges(diff: str) -> list[AutomatedChallenge]:
    challenges = [
        AutomatedChallenge(
            category="concurrency",
            description="Check for race conditions: what if two tasks complete simultaneously?",
            verification="Concurrent test with asyncio.gather of same operation",
            severity="critical",
        ),
    ]
    if re.search(r'^\+.*\bgather\b', diff, re.MULTILINE):
        challenges.append(AutomatedChallenge(
            category="concurrency",
            description="Test gather with one task failing: does the rest complete or cascade?",
            verification="Test with one failing coroutine in gather",
            severity="major",
        ))
    return challenges


def _generate_timeout_challenges(diff: str) -> list[AutomatedChallenge]:
    return [
        AutomatedChallenge(
            category="timeout",
            description="Test with network unavailable: connection refused, DNS failure",
            verification="Mock network calls to raise ConnectionError",
            severity="critical",
        ),
        AutomatedChallenge(
            category="timeout",
            description="Test with extreme latency: response takes 30+ seconds",
            verification="Mock with delayed response, verify timeout handling",
            severity="major",
        ),
    ]


def _generate_architecture_challenges(
    file_list: list[str], diff: str,
) -> list[AutomatedChallenge]:
    challenges = []

    # Import cycle detection
    py_files = [f for f in file_list if f.endswith(".py")]
    if len(py_files) > 1:
        challenges.append(AutomatedChallenge(
            category="architecture",
            description="Check for import cycles between modified modules",
            verification="python -c 'import <module>' for each changed module",
            severity="critical",
        ))

    # Cross-module consistency
    if len(file_list) > 3:
        challenges.append(AutomatedChallenge(
            category="architecture",
            description="Verify cross-module consistency: all callers updated for changed signatures",
            verification="grep for old function signatures in non-modified files",
            severity="major",
        ))

    return challenges


def _generate_error_handling_challenges(diff: str) -> list[AutomatedChallenge]:
    challenges = []

    # Bare except
    if re.search(r'^\+\s*except\s*:', diff, re.MULTILINE):
        challenges.append(AutomatedChallenge(
            category="error_handling",
            description="Bare 'except:' catches all exceptions including KeyboardInterrupt \u2014 use specific exception types",
            verification="Review diff for bare except clauses",
            severity="major",
        ))

    # Exception swallowing (except + pass)
    if re.search(r'^\+\s*except.*:\s*$', diff, re.MULTILINE):
        challenges.append(AutomatedChallenge(
            category="error_handling",
            description="Check for exception swallowing: except blocks that silently pass without logging",
            verification="Review except blocks for pass-without-log pattern",
            severity="minor",
        ))

    return challenges