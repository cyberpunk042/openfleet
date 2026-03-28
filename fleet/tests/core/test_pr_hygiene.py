"""Tests for PR hygiene — stale, conflicting, orphaned PRs."""

from datetime import datetime, timedelta

from fleet.core.models import Task, TaskCustomFields, TaskStatus
from fleet.core.pr_hygiene import assess_pr_hygiene


def _task(id: str = "t1", status: str = "review", pr_url: str = "https://github.com/test/pr/1", agent: str = "devops") -> Task:
    return Task(
        id=id, board_id="b1", title="Test", status=TaskStatus(status),
        custom_fields=TaskCustomFields(pr_url=pr_url, agent_name=agent),
    )


def _pr(url: str = "https://github.com/test/pr/1", number: int = 1, title: str = "Test PR",
        mergeable: str = "MERGEABLE", created_at: str = "") -> dict:
    return {"url": url, "number": number, "title": title, "mergeable": mergeable, "created_at": created_at}


def test_conflicting_pr_detected():
    tasks = [_task(pr_url="https://github.com/test/pr/1")]
    prs = [_pr(mergeable="CONFLICTING")]
    report = assess_pr_hygiene(tasks, prs)
    assert report.conflicting == 1
    assert report.issues[0].issue_type == "conflicting"
    assert report.issues[0].severity == "high"


def test_stale_pr_detected():
    tasks = [_task(status="done", pr_url="https://github.com/test/pr/1")]
    prs = [_pr()]
    report = assess_pr_hygiene(tasks, prs)
    assert report.stale == 1
    assert any(i.issue_type == "stale" for i in report.issues)


def test_conflicting_and_stale():
    tasks = [_task(status="done", pr_url="https://github.com/test/pr/1")]
    prs = [_pr(mergeable="CONFLICTING")]
    report = assess_pr_hygiene(tasks, prs)
    assert report.conflicting == 1
    assert report.stale == 1
    assert len(report.issues) == 2


def test_clean_pr_no_issues():
    tasks = [_task(status="review", pr_url="https://github.com/test/pr/1")]
    prs = [_pr(mergeable="MERGEABLE", created_at=datetime.now().isoformat())]
    report = assess_pr_hygiene(tasks, prs)
    conflicting = [i for i in report.issues if i.issue_type in ("conflicting", "stale")]
    assert len(conflicting) == 0


def test_long_open_pr():
    old = (datetime.now() - timedelta(hours=72)).isoformat()
    tasks = [_task(pr_url="https://github.com/test/pr/1")]
    prs = [_pr(created_at=old)]
    report = assess_pr_hygiene(tasks, prs)
    assert any(i.issue_type == "long_open" for i in report.issues)


def test_conflict_recommends_rebase_for_review():
    tasks = [_task(status="review")]
    prs = [_pr(mergeable="CONFLICTING")]
    report = assess_pr_hygiene(tasks, prs)
    issue = report.issues[0]
    assert "rebase" in issue.recommended_action.lower()


def test_conflict_recommends_close_for_done():
    tasks = [_task(status="done")]
    prs = [_pr(mergeable="CONFLICTING")]
    report = assess_pr_hygiene(tasks, prs)
    conflict_issue = next(i for i in report.issues if i.issue_type == "conflicting")
    assert "close" in conflict_issue.recommended_action.lower()


def test_no_prs_no_issues():
    report = assess_pr_hygiene([], [])
    assert not report.has_issues
    assert report.total_open_prs == 0