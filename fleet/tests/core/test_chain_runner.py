"""Tests for the chain runner — executes event chains across surfaces."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from fleet.core.event_chain import (
    EventChain,
    EventSurface,
    build_task_complete_chain,
    build_alert_chain,
)
from fleet.core.chain_runner import ChainRunner


@pytest.fixture
def mock_mc():
    mc = AsyncMock()
    mc.update_task = AsyncMock()
    mc.create_approval = AsyncMock()
    mc.post_memory = AsyncMock()
    mc.post_comment = AsyncMock()
    return mc


@pytest.fixture
def mock_irc():
    irc = AsyncMock()
    irc.notify = AsyncMock(return_value=True)
    return irc


@pytest.fixture
def mock_ntfy():
    ntfy = AsyncMock()
    ntfy.publish = AsyncMock(return_value=True)
    return ntfy


@pytest.fixture
def mock_gh():
    gh = AsyncMock()
    gh._run = AsyncMock()
    return gh


@pytest.fixture
def runner(mock_mc, mock_irc, mock_ntfy, mock_gh):
    return ChainRunner(
        mc=mock_mc,
        irc=mock_irc,
        gh=mock_gh,
        ntfy=mock_ntfy,
        board_id="test-board-id",
    )


@pytest.mark.asyncio
async def test_run_empty_chain(runner):
    chain = EventChain(operation="test")
    result = await runner.run(chain)
    assert result.ok
    assert result.total_events == 0
    assert result.executed == 0


@pytest.mark.asyncio
async def test_run_internal_update_task(runner, mock_mc):
    chain = EventChain(operation="test")
    chain.add(EventSurface.INTERNAL, "update_task_status", {
        "task_id": "abc123", "status": "review",
    })
    result = await runner.run(chain)
    assert result.ok
    assert result.executed == 1
    mock_mc.update_task.assert_called_once()


@pytest.mark.asyncio
async def test_run_channel_irc(runner, mock_irc):
    chain = EventChain(operation="test")
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet", "message": "test message",
    })
    result = await runner.run(chain)
    assert result.ok
    mock_irc.notify.assert_called_once_with("#fleet", "test message")


@pytest.mark.asyncio
async def test_run_notify_ntfy(runner, mock_ntfy):
    chain = EventChain(operation="test")
    chain.add(EventSurface.NOTIFY, "ntfy_publish", {
        "title": "Test", "priority": "info", "event_type": "task_done",
    })
    result = await runner.run(chain)
    assert result.ok
    mock_ntfy.publish.assert_called_once()


@pytest.mark.asyncio
async def test_partial_failure_non_required(runner, mock_irc):
    """Non-required event failure doesn't fail the chain."""
    mock_irc.notify.side_effect = Exception("IRC down")
    chain = EventChain(operation="test")
    chain.add(EventSurface.CHANNEL, "notify_irc", {
        "channel": "#fleet", "message": "test",
    }, required=False)
    result = await runner.run(chain)
    assert result.ok  # Non-required failure = still ok
    assert result.failed == 0  # Not counted as failure


@pytest.mark.asyncio
async def test_partial_failure_required(runner, mock_mc):
    """Required event failure fails the chain."""
    mock_mc.update_task.side_effect = Exception("MC down")
    chain = EventChain(operation="test")
    chain.add(EventSurface.INTERNAL, "update_task_status", {
        "task_id": "abc", "status": "review",
    }, required=True)
    result = await runner.run(chain)
    assert not result.ok
    assert result.failed == 1
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_plane_graceful_skip(runner):
    """PLANE events skip gracefully when Plane not configured."""
    chain = EventChain(operation="test")
    chain.add(EventSurface.PLANE, "update_issue_state", {
        "issue_id": "xyz", "project_id": "abc", "state": "Done",
    }, required=False)
    result = await runner.run(chain)
    assert result.ok  # Plane skip is not a failure
    assert result.executed == 1


@pytest.mark.asyncio
async def test_task_complete_chain(runner, mock_mc, mock_irc, mock_ntfy):
    """Full task_complete chain executes all surfaces."""
    chain = build_task_complete_chain(
        task_id="task-123",
        agent_name="software-engineer",
        summary="Added type hints to engine",
        pr_url="https://github.com/org/repo/pull/42",
        branch="feat/type-hints",
        project="fleet",
    )
    result = await runner.run(chain)
    # Should execute all events (some may fail gracefully)
    assert result.total_events > 5
    assert result.executed == result.total_events


@pytest.mark.asyncio
async def test_alert_chain(runner, mock_mc, mock_irc, mock_ntfy):
    """Alert chain publishes to internal + channel + notify."""
    chain = build_alert_chain(
        agent_name="devsecops",
        severity="critical",
        title="CVE in pydantic",
        details="Version 2.7.0 affected",
        category="security",
    )
    result = await runner.run(chain)
    assert result.executed > 0
    mock_irc.notify.assert_called()  # Should post to #alerts
    mock_ntfy.publish.assert_called()  # Should notify human