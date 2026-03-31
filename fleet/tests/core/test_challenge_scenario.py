"""Tests for scenario challenge for bug fixes (M-IV05)."""

from fleet.core.challenge import ChallengeType
from fleet.core.challenge_scenario import (
    Scenario,
    ScenarioResult,
    ScenarioType,
    evaluate_scenario_results,
    generate_bug_fix_scenarios,
    scenario_summary,
    _has_boundary_conditions,
    _has_concurrency_patterns,
    _extract_changed_files,
    _truncate,
)
from fleet.core.models import Task, TaskCustomFields, TaskStatus


# ─── Helpers ──────────────────────────────────────────────────────


def _task(
    title: str = "Fix heartbeat loop",
    description: str = "Heartbeat enters infinite loop when max_iterations=0",
    sp: int = 3,
) -> Task:
    return Task(
        id="t1", board_id="b1", title=title, status=TaskStatus.INBOX,
        description=description,
        custom_fields=TaskCustomFields(story_points=sp, task_type="bug"),
    )


DIFF_SIMPLE = """\
--- a/fleet/core/heartbeat.py
+++ b/fleet/core/heartbeat.py
@@ -10,6 +10,9 @@
-    while iterations < max_iterations:
+    while iterations < max_iterations and max_iterations > 0:
         process()
         iterations += 1
"""

DIFF_BOUNDARY = """\
--- a/fleet/core/router.py
+++ b/fleet/core/router.py
@@ -5,3 +5,5 @@
+    if count >= 10:
+        return "overflow"
"""

DIFF_CONCURRENT = """\
--- a/fleet/core/handler.py
+++ b/fleet/core/handler.py
@@ -1,3 +1,6 @@
+    async def handle(self):
+        results = await asyncio.gather(*tasks)
"""

DIFF_MULTI_FILE = """\
--- a/fleet/core/alpha.py
+++ b/fleet/core/alpha.py
@@ -1,3 +1,5 @@
+from fleet.core.beta import fix
--- a/fleet/core/beta.py
+++ b/fleet/core/beta.py
@@ -1,3 +1,5 @@
+def fix(): pass
"""


# ─── Scenario Generation ─────────────────────────────────────────


def test_always_includes_reproduction():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_SIMPLE)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.REPRODUCTION in types


def test_always_includes_removal():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_SIMPLE)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.REMOVAL in types


def test_always_includes_regression():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_SIMPLE)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.REGRESSION in types


def test_boundary_included_when_conditions_present():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_BOUNDARY)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.BOUNDARY in types


def test_no_boundary_for_simple_diff():
    diff = """\
--- a/fleet/core/fix.py
+++ b/fleet/core/fix.py
@@ -1,3 +1,3 @@
-    return old_value
+    return new_value
"""
    scenarios = generate_bug_fix_scenarios(_task(), diff)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.BOUNDARY not in types


def test_concurrency_included_when_async():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_CONCURRENT)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.CONCURRENCY in types


def test_interaction_included_for_multi_file():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_MULTI_FILE)
    types = [s.scenario_type for s in scenarios]
    assert ScenarioType.INTERACTION in types


def test_reproduction_uses_bug_description():
    task = _task(description="Widget crashes on null input")
    scenarios = generate_bug_fix_scenarios(task, DIFF_SIMPLE)
    repro = [s for s in scenarios if s.scenario_type == ScenarioType.REPRODUCTION][0]
    assert "Widget crashes on null input" in repro.description


def test_custom_bug_description_overrides():
    scenarios = generate_bug_fix_scenarios(
        _task(), DIFF_SIMPLE, bug_description="Custom bug desc",
    )
    repro = [s for s in scenarios if s.scenario_type == ScenarioType.REPRODUCTION][0]
    assert "Custom bug desc" in repro.description


def test_reproduction_severity_critical():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_SIMPLE)
    repro = [s for s in scenarios if s.scenario_type == ScenarioType.REPRODUCTION][0]
    assert repro.severity_if_failed == "critical"


def test_removal_severity_critical():
    scenarios = generate_bug_fix_scenarios(_task(), DIFF_SIMPLE)
    removal = [s for s in scenarios if s.scenario_type == ScenarioType.REMOVAL][0]
    assert removal.severity_if_failed == "critical"


# ─── Scenario Dataclass ──────────────────────────────────────────


def test_scenario_to_finding():
    s = Scenario(
        scenario_type=ScenarioType.REPRODUCTION,
        description="Reproduce the bug",
        steps=["Step 1", "Step 2"],
        expected_outcome="Bug should not occur",
        severity_if_failed="critical",
    )
    f = s.to_finding("sc1-1", round_number=1, evidence="Bug reproduced")
    assert f.finding_id == "sc1-1"
    assert f.challenge_type == ChallengeType.SCENARIO
    assert f.severity == "critical"
    assert "Reproduce" in f.description
    assert f.evidence == "Bug reproduced"


def test_scenario_to_dict():
    s = Scenario(
        scenario_type=ScenarioType.BOUNDARY,
        description="Test boundaries",
        steps=["Step 1"],
        expected_outcome="All pass",
    )
    d = s.to_dict()
    assert d["type"] == "boundary"
    assert d["steps"] == ["Step 1"]
    assert d["expected"] == "All pass"


# ─── Scenario Results ────────────────────────────────────────────


def test_scenario_result_passed():
    s = Scenario(ScenarioType.REGRESSION, "Tests", [], "All pass")
    r = ScenarioResult(scenario=s, passed=True, evidence="All 150 tests passed")
    assert r.passed
    assert not r.failed


def test_scenario_result_failed():
    s = Scenario(ScenarioType.REPRODUCTION, "Repro", [], "Bug gone")
    r = ScenarioResult(
        scenario=s, passed=False,
        actual_outcome="Bug still occurs",
        evidence="Error on line 42",
    )
    assert r.failed


# ─── evaluate_scenario_results ───────────────────────────────────


def test_evaluate_all_passed():
    s1 = Scenario(ScenarioType.REPRODUCTION, "Repro", [], "OK")
    s2 = Scenario(ScenarioType.REMOVAL, "Removal", [], "Bug returns")
    results = [
        ScenarioResult(scenario=s1, passed=True),
        ScenarioResult(scenario=s2, passed=True),
    ]
    findings = evaluate_scenario_results([s1, s2], results)
    assert findings == []


def test_evaluate_some_failed():
    s1 = Scenario(ScenarioType.REPRODUCTION, "Repro", [], "OK", "critical")
    s2 = Scenario(ScenarioType.BOUNDARY, "Boundary", [], "OK", "major")
    results = [
        ScenarioResult(scenario=s1, passed=True),
        ScenarioResult(scenario=s2, passed=False, actual_outcome="Crashed on zero"),
    ]
    findings = evaluate_scenario_results([s1, s2], results, round_number=1)
    assert len(findings) == 1
    assert findings[0].finding_id == "sc1-2"
    assert findings[0].severity == "major"
    assert "Scenario failed" in findings[0].description


def test_evaluate_finding_ids_sequential():
    s1 = Scenario(ScenarioType.REPRODUCTION, "A", [], "OK", "critical")
    s2 = Scenario(ScenarioType.BOUNDARY, "B", [], "OK", "major")
    s3 = Scenario(ScenarioType.REGRESSION, "C", [], "OK", "critical")
    results = [
        ScenarioResult(scenario=s1, passed=False, evidence="e1"),
        ScenarioResult(scenario=s2, passed=False, evidence="e2"),
        ScenarioResult(scenario=s3, passed=True),
    ]
    findings = evaluate_scenario_results([s1, s2, s3], results, round_number=2)
    assert len(findings) == 2
    assert findings[0].finding_id == "sc2-1"
    assert findings[1].finding_id == "sc2-2"


# ─── scenario_summary ───────────────────────────────────────────


def test_summary_all_passed():
    s = Scenario(ScenarioType.REGRESSION, "Tests", [], "OK")
    results = [ScenarioResult(scenario=s, passed=True)]
    summary = scenario_summary(results)
    assert summary["all_passed"]
    assert summary["total"] == 1
    assert summary["passed"] == 1
    assert summary["failed"] == 0


def test_summary_with_failures():
    s1 = Scenario(ScenarioType.REPRODUCTION, "A", [], "OK")
    s2 = Scenario(ScenarioType.BOUNDARY, "B", [], "OK")
    results = [
        ScenarioResult(scenario=s1, passed=True),
        ScenarioResult(scenario=s2, passed=False, actual_outcome="Crashed"),
    ]
    summary = scenario_summary(results)
    assert not summary["all_passed"]
    assert summary["failed"] == 1
    assert len(summary["failed_scenarios"]) == 1
    assert summary["failed_scenarios"][0]["type"] == "boundary"
    assert summary["failed_scenarios"][0]["actual"] == "Crashed"


# ─── Pattern Detection ───────────────────────────────────────────


def test_has_boundary_with_comparison():
    assert _has_boundary_conditions(DIFF_BOUNDARY)


def test_has_boundary_with_range():
    diff = "+    for i in range(len(items)):"
    assert _has_boundary_conditions(diff)


def test_no_boundary_in_simple_diff():
    assert not _has_boundary_conditions("+    return value")


def test_has_concurrency_async():
    assert _has_concurrency_patterns(DIFF_CONCURRENT)


def test_has_concurrency_threading():
    diff = "+    lock = threading.Lock()"
    assert _has_concurrency_patterns(diff)


def test_no_concurrency_simple():
    assert not _has_concurrency_patterns("+    return value")


def test_extract_changed_files():
    files = _extract_changed_files(DIFF_MULTI_FILE)
    assert "fleet/core/alpha.py" in files
    assert "fleet/core/beta.py" in files


def test_extract_files_empty_diff():
    assert _extract_changed_files("") == []


# ─── Utility ─────────────────────────────────────────────────────


def test_truncate_short():
    assert _truncate("short", 10) == "short"


def test_truncate_long():
    result = _truncate("a" * 100, 20)
    assert len(result) == 20
    assert result.endswith("...")


def test_truncate_exact():
    assert _truncate("exact", 5) == "exact"