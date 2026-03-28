"""Tests for fleet plane CLI — argument parsing, routing, output formatting."""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fleet.cli.plane import (
    _list_projects,
    _list_issues,
    _create_issue,
    _list_cycles,
    _list_states,
    _sync,
    _load_plane_client,
    _load_workspace,
    run_plane,
)
from fleet.infra.plane_client import (
    PlaneCycle,
    PlaneIssue,
    PlaneProject,
    PlaneState,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────


def _project(id: str = "p1", name: str = "Alpha", identifier: str = "ALP") -> PlaneProject:
    return PlaneProject({"id": id, "name": name, "identifier": identifier, "is_member": True})


def _issue(
    id: str = "i1",
    title: str = "Fix bug",
    priority: str = "medium",
    seq: int = 1,
) -> PlaneIssue:
    return PlaneIssue({
        "id": id, "name": title, "priority": priority, "sequence_id": seq,
        "state": "s1", "project": "p1", "assignees": [], "label_ids": [],
        "cycle": None, "description_html": "",
    })


def _cycle(id: str = "c1", name: str = "Sprint 1", status: str = "current") -> PlaneCycle:
    return PlaneCycle({"id": id, "name": name, "status": status, "project": "p1"})


def _state(id: str = "s1", name: str = "In Progress", group: str = "started") -> PlaneState:
    return PlaneState({"id": id, "name": name, "group": group, "color": "#0f0", "project": "p1"})


def _make_plane_mock(**kwargs) -> MagicMock:
    plane = MagicMock()
    plane.close = AsyncMock()
    for k, v in kwargs.items():
        setattr(plane, k, AsyncMock(return_value=v))
    return plane


# ─── _load_plane_client ───────────────────────────────────────────────────────


def test_load_plane_client_exits_without_url(monkeypatch):
    monkeypatch.delenv("PLANE_URL", raising=False)
    with pytest.raises(SystemExit):
        _load_plane_client({"PLANE_API_KEY": "k"})


def test_load_plane_client_exits_without_key(monkeypatch):
    monkeypatch.delenv("PLANE_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        _load_plane_client({"PLANE_URL": "http://plane.local"})


def test_load_plane_client_constructs(monkeypatch):
    monkeypatch.delenv("PLANE_URL", raising=False)
    monkeypatch.delenv("PLANE_API_KEY", raising=False)
    client = _load_plane_client({"PLANE_URL": "http://plane.local", "PLANE_API_KEY": "secret"})
    assert client._base_url == "http://plane.local"
    assert client._api_key == "secret"


# ─── _load_workspace ─────────────────────────────────────────────────────────


def test_load_workspace_from_arg():
    args = MagicMock()
    args.workspace = "my-ws"
    assert _load_workspace({}, args) == "my-ws"


def test_load_workspace_from_env():
    args = MagicMock()
    args.workspace = None
    assert _load_workspace({"PLANE_WORKSPACE": "env-ws"}, args) == "env-ws"


def test_load_workspace_exits_when_missing(monkeypatch):
    monkeypatch.delenv("PLANE_WORKSPACE", raising=False)
    args = MagicMock()
    args.workspace = None
    with pytest.raises(SystemExit):
        _load_workspace({}, args)


# ─── _list_projects ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_projects_output(capsys):
    plane = _make_plane_mock(list_projects=[_project("p1", "NNRT", "NNRT")])
    rc = await _list_projects(plane, "ws")
    assert rc == 0
    out = capsys.readouterr().out
    assert "NNRT" in out
    assert "p1" in out


@pytest.mark.asyncio
async def test_list_projects_empty(capsys):
    plane = _make_plane_mock(list_projects=[])
    rc = await _list_projects(plane, "ws")
    assert rc == 0
    out = capsys.readouterr().out
    assert "No projects" in out


# ─── _list_issues ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_issues_output(capsys):
    plane = _make_plane_mock(list_issues=[_issue("i1", "Fix the login bug", "high", 42)])
    rc = await _list_issues(plane, "ws", "proj-1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Fix the login bug" in out
    assert "42" in out


@pytest.mark.asyncio
async def test_list_issues_passes_filters():
    plane = _make_plane_mock(list_issues=[])
    await _list_issues(plane, "ws", "proj-1", state_id="s1", priority="high")
    plane.list_issues.assert_called_once_with(
        "ws", "proj-1", state_id="s1", priority="high"
    )


@pytest.mark.asyncio
async def test_list_issues_empty(capsys):
    plane = _make_plane_mock(list_issues=[])
    rc = await _list_issues(plane, "ws", "proj-1")
    assert rc == 0
    assert "No issues" in capsys.readouterr().out


# ─── _create_issue ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_issue_success(capsys):
    created = _issue("i-new", "My new issue", "high", 7)
    plane = _make_plane_mock(create_issue=created)
    rc = await _create_issue(plane, "ws", "proj-1", title="My new issue", priority="high")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Created" in out
    assert "My new issue" in out
    assert "#7" in out


@pytest.mark.asyncio
async def test_create_issue_passes_all_fields():
    created = _issue()
    plane = _make_plane_mock(create_issue=created)
    await _create_issue(
        plane, "ws", "proj-1",
        title="T",
        description="desc",
        priority="urgent",
        state_id="s1",
        assignees=["u1"],
        cycle_id="c1",
    )
    call = plane.create_issue.call_args
    assert call[1]["title"] == "T"
    assert "desc" in call[1]["description_html"]
    assert call[1]["priority"] == "urgent"
    assert call[1]["state_id"] == "s1"
    assert call[1]["assignees"] == ["u1"]
    assert call[1]["cycle_id"] == "c1"


@pytest.mark.asyncio
async def test_create_issue_no_description_no_html():
    created = _issue()
    plane = _make_plane_mock(create_issue=created)
    await _create_issue(plane, "ws", "proj-1", title="T")
    call = plane.create_issue.call_args
    assert call[1]["description_html"] == ""


# ─── _list_cycles ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_cycles_output(capsys):
    plane = _make_plane_mock(list_cycles=[_cycle("c1", "Sprint 1", "current")])
    rc = await _list_cycles(plane, "ws", "proj-1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Sprint 1" in out
    assert "current" in out


@pytest.mark.asyncio
async def test_list_cycles_empty(capsys):
    plane = _make_plane_mock(list_cycles=[])
    rc = await _list_cycles(plane, "ws", "proj-1")
    assert rc == 0
    assert "No cycles" in capsys.readouterr().out


# ─── _list_states ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_states_output(capsys):
    plane = _make_plane_mock(list_states=[_state("s1", "In Progress", "started")])
    rc = await _list_states(plane, "ws", "proj-1")
    assert rc == 0
    out = capsys.readouterr().out
    assert "In Progress" in out
    assert "started" in out


@pytest.mark.asyncio
async def test_list_states_empty(capsys):
    plane = _make_plane_mock(list_states=[])
    rc = await _list_states(plane, "ws", "proj-1")
    assert rc == 0
    assert "No states" in capsys.readouterr().out


# ─── _sync ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_both_directions(capsys):
    from fleet.core.models import Task, TaskCustomFields, TaskStatus
    from fleet.core.plane_sync import IngestResult, PushResult

    plane = _make_plane_mock()
    mc = MagicMock()

    created_task = Task(
        id="ocmc-1", board_id="b1", title="New issue",
        status=TaskStatus.INBOX,
        custom_fields=TaskCustomFields(plane_issue_id="i1"),
    )
    ingest_result = IngestResult(created=[created_task], skipped=["i0"])
    push_result = PushResult(updated=["i1"], skipped=["ocmc-2"])

    with patch("fleet.cli.plane.PlaneSyncer") as MockSyncer:
        syncer_inst = MagicMock()
        syncer_inst.ingest_from_plane = AsyncMock(return_value=ingest_result)
        syncer_inst.push_completions_to_plane = AsyncMock(return_value=push_result)
        MockSyncer.return_value = syncer_inst

        rc = await _sync(
            plane, mc, "ws", "board-1",
            project_ids=["proj-1"],
            done_state_id="state-done",
            direction="both",
        )

    assert rc == 0
    out = capsys.readouterr().out
    assert "Created" in out
    assert "New issue" in out
    assert "Updated" in out
    assert "i1" in out


@pytest.mark.asyncio
async def test_sync_in_only(capsys):
    from fleet.core.plane_sync import IngestResult, PushResult

    plane = _make_plane_mock()
    mc = MagicMock()

    with patch("fleet.cli.plane.PlaneSyncer") as MockSyncer:
        inst = MagicMock()
        inst.ingest_from_plane = AsyncMock(return_value=IngestResult())
        inst.push_completions_to_plane = AsyncMock(return_value=PushResult())
        MockSyncer.return_value = inst

        await _sync(plane, mc, "ws", "b1", project_ids=[], done_state_id="s", direction="in")

    inst.ingest_from_plane.assert_called_once()
    inst.push_completions_to_plane.assert_not_called()


@pytest.mark.asyncio
async def test_sync_out_only(capsys):
    from fleet.core.plane_sync import IngestResult, PushResult

    plane = _make_plane_mock()
    mc = MagicMock()

    with patch("fleet.cli.plane.PlaneSyncer") as MockSyncer:
        inst = MagicMock()
        inst.ingest_from_plane = AsyncMock(return_value=IngestResult())
        inst.push_completions_to_plane = AsyncMock(return_value=PushResult())
        MockSyncer.return_value = inst

        await _sync(plane, mc, "ws", "b1", project_ids=[], done_state_id="s", direction="out")

    inst.ingest_from_plane.assert_not_called()
    inst.push_completions_to_plane.assert_called_once()


@pytest.mark.asyncio
async def test_sync_warns_when_no_done_state(capsys):
    from fleet.core.plane_sync import IngestResult, PushResult

    plane = _make_plane_mock()
    mc = MagicMock()

    with patch("fleet.cli.plane.PlaneSyncer") as MockSyncer:
        inst = MagicMock()
        inst.ingest_from_plane = AsyncMock(return_value=IngestResult())
        MockSyncer.return_value = inst

        await _sync(plane, mc, "ws", "b1", project_ids=[], done_state_id=None, direction="both")

    out = capsys.readouterr().out
    assert "--done-state" in out


@pytest.mark.asyncio
async def test_sync_returns_1_on_errors(capsys):
    from fleet.core.plane_sync import IngestResult

    plane = _make_plane_mock()
    mc = MagicMock()

    with patch("fleet.cli.plane.PlaneSyncer") as MockSyncer:
        inst = MagicMock()
        inst.ingest_from_plane = AsyncMock(
            return_value=IngestResult(errors=["Plane API 500"])
        )
        MockSyncer.return_value = inst

        rc = await _sync(
            plane, mc, "ws", "b1",
            project_ids=[], done_state_id=None, direction="in",
        )

    assert rc == 1


# ─── run_plane (CLI entry point) ─────────────────────────────────────────────


def test_run_plane_no_args_returns_1():
    rc = run_plane([])
    assert rc == 1


def test_run_plane_help_exits(capsys):
    with pytest.raises(SystemExit):
        run_plane(["--help"])
    out = capsys.readouterr().out
    assert "list-projects" in out


def test_run_plane_unknown_action_exits():
    with pytest.raises(SystemExit):
        run_plane(["not-a-command"])


def test_main_module_registers_plane_command():
    """fleet __main__.py should include 'plane' in COMMANDS."""
    import fleet.__main__ as main_mod
    assert "plane" in main_mod.COMMANDS
    _, module, func = main_mod.COMMANDS["plane"]
    assert module == "fleet.cli.plane"
    assert func == "run_plane"
