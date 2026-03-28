"""Tests for task lifecycle validation."""

from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.task_lifecycle import (
    LifecycleStage,
    assess_task_lifecycle,
    validate_post_stage,
    validate_pre_stage,
    validate_progress_stage,
)


def _task(status: str = "inbox", agent: str = "", project: str = "", task_type: str = "task", pr_url: str = "") -> Task:
    return Task(
        id="t1", board_id="b1", title="Test", status=TaskStatus(status),
        custom_fields=TaskCustomFields(agent_name=agent, project=project, task_type=task_type, pr_url=pr_url),
    )


def test_pre_stage_all_pass():
    t = _task(agent="devops", project="dspd")
    checks = validate_pre_stage(t, has_context=True, has_plan=True)
    assert all(c.passed for c in checks)


def test_pre_stage_missing_context():
    t = _task(agent="devops", project="dspd")
    checks = validate_pre_stage(t, has_context=False, has_plan=True)
    assert not checks[0].passed
    assert "fleet_read_context" in checks[0].message


def test_pre_stage_missing_plan():
    t = _task(agent="devops", project="dspd")
    checks = validate_pre_stage(t, has_context=True, has_plan=False)
    assert not checks[1].passed
    assert "fleet_task_accept" in checks[1].message


def test_progress_stage_with_commits():
    t = _task()
    checks = validate_progress_stage(t, commit_count=3, has_progress_update=True)
    assert all(c.passed for c in checks)


def test_progress_stage_no_commits():
    t = _task()
    checks = validate_progress_stage(t, commit_count=0, has_progress_update=False)
    assert not checks[0].passed


def test_post_stage_all_pass():
    t = _task(pr_url="https://github.com/test/pr/1")
    checks = validate_post_stage(t, has_pr=True, tests_passed=True, has_review_gates=True, has_approval=True)
    assert all(c.passed for c in checks)


def test_post_stage_tests_failed():
    t = _task()
    checks = validate_post_stage(t, has_pr=True, tests_passed=False, has_review_gates=True, has_approval=True)
    failed = [c for c in checks if not c.passed]
    assert len(failed) == 1
    assert "tests" in failed[0].check_name.lower()


def test_assess_full_lifecycle_compliant():
    t = _task(status="review", agent="devops", project="dspd", pr_url="https://pr")
    report = assess_task_lifecycle(
        t, has_context=True, has_plan=True, commit_count=3,
        has_progress_update=True, has_pr=True, tests_passed=True,
        has_review_gates=True, has_approval=True,
    )
    assert report.compliant
    assert report.score == 100.0
    assert report.stage == LifecycleStage.IN_REVIEW


def test_assess_lifecycle_non_compliant():
    t = _task(status="review")
    report = assess_task_lifecycle(
        t, has_context=False, has_plan=False, commit_count=0,
        has_pr=False, tests_passed=False, has_review_gates=False, has_approval=False,
    )
    assert not report.compliant
    assert report.score < 50.0
    assert len(report.issues) > 0


def test_assess_stage_detection():
    inbox = _task(status="inbox")
    report = assess_task_lifecycle(inbox)
    assert report.stage == LifecycleStage.NOT_STARTED

    in_progress = _task(status="in_progress")
    report = assess_task_lifecycle(in_progress, has_context=True, has_plan=True)
    assert report.stage == LifecycleStage.IN_PROGRESS

    done = _task(status="done")
    report = assess_task_lifecycle(done)
    assert report.stage == LifecycleStage.DONE