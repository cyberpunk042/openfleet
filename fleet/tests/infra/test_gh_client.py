"""Tests for fleet GH client — commit parsing."""

from fleet.core.models import CommitType
from fleet.infra.gh_client import GHClient


def test_parse_conventional_commit():
    gh = GHClient()
    c = gh.parse_commit("abc1234567", "feat(core): add type hints [task:3402f526]")
    assert c.commit_type == CommitType.FEAT
    assert c.scope == "core"
    assert c.description == "add type hints"
    assert c.task_ref == "3402f526"
    assert c.short_sha == "abc1234"


def test_parse_commit_no_scope():
    gh = GHClient()
    c = gh.parse_commit("def5678", "fix: handle token rotation")
    assert c.commit_type == CommitType.FIX
    assert c.scope is None
    assert c.description == "handle token rotation"


def test_parse_commit_no_task_ref():
    gh = GHClient()
    c = gh.parse_commit("ghi9012", "docs(readme): update setup instructions")
    assert c.commit_type == CommitType.DOCS
    assert c.scope == "readme"
    assert c.task_ref is None


def test_parse_non_conventional_commit():
    gh = GHClient()
    c = gh.parse_commit("jkl3456", "random message without format")
    assert c.commit_type is None
    assert c.scope is None
    assert c.description == ""


def test_parse_all_commit_types():
    gh = GHClient()
    for type_str in ["feat", "fix", "docs", "refactor", "test", "chore", "ci", "style", "perf"]:
        c = gh.parse_commit("abc", f"{type_str}: test message")
        assert c.commit_type == CommitType(type_str), f"Failed for {type_str}"