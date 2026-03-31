"""Tests for automated challenge generator (M-IV02)."""

from fleet.core.challenge_automated import (
    AutomatedChallenge,
    generate_automated_challenges,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus


def _task(sp: int = 3, task_type: str = "task") -> Task:
    return Task(
        id="t1", board_id="b1", title="Test", status=TaskStatus.INBOX,
        custom_fields=TaskCustomFields(story_points=sp, task_type=task_type),
    )


# Sample diffs for testing
DIFF_CONDITIONAL = """\
--- a/fleet/core/router.py
+++ b/fleet/core/router.py
@@ -10,6 +10,9 @@
+    if complexity >= 8:
+        return "opus"
+    elif complexity is None:
+        return "sonnet"
"""

DIFF_LOOP = """\
--- a/fleet/core/processor.py
+++ b/fleet/core/processor.py
@@ -5,3 +5,6 @@
+    for task in tasks:
+        process(task)
"""

DIFF_ASYNC = """\
--- a/fleet/core/health.py
+++ b/fleet/core/health.py
@@ -1,3 +1,6 @@
+    async def check_all(self):
+        results = await asyncio.gather(*checks)
"""

DIFF_NETWORK = """\
--- a/fleet/core/client.py
+++ b/fleet/core/client.py
@@ -1,3 +1,5 @@
+    resp = requests.get(url, timeout=10)
+    return resp.json()
"""

DIFF_ERROR = """\
--- a/fleet/core/safe.py
+++ b/fleet/core/safe.py
@@ -1,3 +1,6 @@
+    try:
+        result = do_thing()
+    except:
+        pass
"""

DIFF_MULTI_FILE = """\
--- a/fleet/core/alpha.py
+++ b/fleet/core/alpha.py
@@ -1,3 +1,5 @@
+from fleet.core.beta import helper
--- a/fleet/core/beta.py
+++ b/fleet/core/beta.py
@@ -1,3 +1,5 @@
+from fleet.core.gamma import util
--- a/fleet/core/gamma.py
+++ b/fleet/core/gamma.py
@@ -1,3 +1,5 @@
+import json
--- a/fleet/core/delta.py
+++ b/fleet/core/delta.py
@@ -1,3 +1,5 @@
+import os
"""

DIFF_DOCS_ONLY = """\
--- a/docs/README.md
+++ b/docs/README.md
@@ -1,3 +1,5 @@
+# New section
+Some documentation
"""


# ─── Regression Check ──────────────────────────────────────────────


def test_code_changes_get_regression_check():
    challenges = generate_automated_challenges(_task(), DIFF_CONDITIONAL)
    categories = [c.category for c in challenges]
    assert "regression" in categories


def test_docs_only_no_regression():
    challenges = generate_automated_challenges(_task(), DIFF_DOCS_ONLY)
    categories = [c.category for c in challenges]
    assert "regression" not in categories


# ─── Conditional Edge Cases ────────────────────────────────────────


def test_conditional_generates_boundary_check():
    challenges = generate_automated_challenges(_task(), DIFF_CONDITIONAL)
    edge_cases = [c for c in challenges if c.category == "edge_case"]
    assert len(edge_cases) >= 1
    descriptions = " ".join(c.description for c in edge_cases)
    assert "boundary" in descriptions.lower() or "None" in descriptions


def test_none_check_generates_challenge():
    challenges = generate_automated_challenges(_task(), DIFF_CONDITIONAL)
    edge_cases = [c for c in challenges if c.category == "edge_case"]
    assert any("None" in c.description or "empty" in c.description for c in edge_cases)


# ─── Loop Handling ─────────────────────────────────────────────────


def test_loop_generates_empty_input_check():
    challenges = generate_automated_challenges(_task(), DIFF_LOOP)
    loop_challenges = [c for c in challenges if c.category == "loop"]
    assert len(loop_challenges) == 3  # empty, single, large
    descriptions = [c.description for c in loop_challenges]
    assert any("empty" in d for d in descriptions)
    assert any("single" in d for d in descriptions)
    assert any("large" in d or "100" in d for d in descriptions)


# ─── Async/Concurrency ────────────────────────────────────────────


def test_async_generates_race_condition_check():
    challenges = generate_automated_challenges(_task(), DIFF_ASYNC)
    async_challenges = [c for c in challenges if c.category == "concurrency"]
    assert len(async_challenges) >= 1
    assert any("race" in c.description.lower() for c in async_challenges)


def test_gather_generates_failure_check():
    challenges = generate_automated_challenges(_task(), DIFF_ASYNC)
    async_challenges = [c for c in challenges if c.category == "concurrency"]
    assert any("gather" in c.description.lower() or "failing" in c.description.lower()
               for c in async_challenges)


# ─── Timeout/Retry ─────────────────────────────────────────────────


def test_network_generates_timeout_check():
    challenges = generate_automated_challenges(_task(), DIFF_NETWORK)
    timeout_challenges = [c for c in challenges if c.category == "timeout"]
    assert len(timeout_challenges) >= 1
    assert any("unavailable" in c.description.lower() or "latency" in c.description.lower()
               for c in timeout_challenges)


# ─── Architecture Checks ──────────────────────────────────────────


def test_multi_file_generates_import_cycle_check():
    challenges = generate_automated_challenges(_task(), DIFF_MULTI_FILE)
    arch_challenges = [c for c in challenges if c.category == "architecture"]
    assert len(arch_challenges) >= 1
    assert any("import" in c.description.lower() or "cycle" in c.description.lower()
               for c in arch_challenges)


def test_many_files_generates_consistency_check():
    challenges = generate_automated_challenges(_task(), DIFF_MULTI_FILE)
    arch_challenges = [c for c in challenges if c.category == "architecture"]
    assert any("consistency" in c.description.lower() or "caller" in c.description.lower()
               for c in arch_challenges)


# ─── Error Handling ────────────────────────────────────────────────


def test_bare_except_generates_challenge():
    challenges = generate_automated_challenges(_task(), DIFF_ERROR)
    error_challenges = [c for c in challenges if c.category == "error_handling"]
    assert len(error_challenges) >= 1
    assert any("bare" in c.description.lower() or "except" in c.description.lower()
               for c in error_challenges)


# ─── Challenge-to-Finding Conversion ──────────────────────────────


def test_challenge_to_finding():
    c = AutomatedChallenge(
        category="regression",
        description="Run test suite",
        verification="pytest",
        severity="critical",
    )
    f = c.to_finding("f1", round_number=1)
    assert f.finding_id == "f1"
    assert f.challenge_type == "automated"
    assert f.severity == "critical"


# ─── File Extraction ──────────────────────────────────────────────


def test_extract_files_from_diff():
    from fleet.core.challenge_automated import _extract_files_from_diff
    files = _extract_files_from_diff(DIFF_MULTI_FILE)
    assert "fleet/core/alpha.py" in files
    assert "fleet/core/beta.py" in files
    assert "fleet/core/gamma.py" in files


# ─── Empty Diff ────────────────────────────────────────────────────


def test_empty_diff_no_challenges():
    challenges = generate_automated_challenges(_task(), "")
    assert len(challenges) == 0


# ─── Combined Diff ─────────────────────────────────────────────────


def test_combined_diff_multiple_categories():
    """A diff with multiple patterns generates challenges from all categories."""
    combined = DIFF_CONDITIONAL + "\n" + DIFF_LOOP + "\n" + DIFF_ASYNC
    challenges = generate_automated_challenges(_task(), combined)
    categories = {c.category for c in challenges}
    assert "regression" in categories
    assert "edge_case" in categories
    assert "loop" in categories
    assert "concurrency" in categories