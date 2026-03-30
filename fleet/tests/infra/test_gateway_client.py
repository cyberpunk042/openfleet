"""Tests for fleet.infra.gateway_client — gateway wrapper functions."""

import json
import pytest
from unittest.mock import AsyncMock, patch, mock_open

from fleet.infra.gateway_client import (
    _gateway_rpc,
    prune_agent,
    force_compact,
    inject_content,
    create_fresh_session,
)


# Mock WebSocket that simulates gateway protocol
class MockWebSocket:
    def __init__(self, responses=None):
        self.sent = []
        self._responses = list(responses or [])
        self._idx = 0

    async def recv(self):
        if self._idx < len(self._responses):
            resp = self._responses[self._idx]
            self._idx += 1
            return json.dumps(resp)
        return json.dumps({"type": "event"})

    async def send(self, data):
        self.sent.append(json.loads(data))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_oc_config():
    config = json.dumps({"gateway": {"auth": {"token": "test-token"}}})
    with patch("builtins.open", mock_open(read_data=config)):
        yield


class TestGatewayRpc:
    @pytest.mark.asyncio
    async def test_missing_config_returns_false(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            ok, resp = await _gateway_rpc("sessions.delete", {"key": "s1"})
            assert ok is False
            assert "error" in resp


class TestPruneAgent:
    @pytest.mark.asyncio
    async def test_prune_calls_sessions_delete(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (True, {})
            result = await prune_agent("session-key-123")
            assert result is True
            mock_rpc.assert_called_once_with(
                "sessions.delete", {"key": "session-key-123"}
            )

    @pytest.mark.asyncio
    async def test_prune_failure(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (False, {"error": "not found"})
            result = await prune_agent("bad-key")
            assert result is False


class TestForceCompact:
    @pytest.mark.asyncio
    async def test_compact_calls_sessions_compact(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (True, {})
            result = await force_compact("session-key-123")
            assert result is True
            mock_rpc.assert_called_once_with(
                "sessions.compact", {"key": "session-key-123"}
            )


class TestInjectContent:
    @pytest.mark.asyncio
    async def test_inject_calls_chat_send(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (True, {})
            result = await inject_content("session-key-123", "LESSON CONTENT HERE")
            assert result is True
            call_args = mock_rpc.call_args
            assert call_args[0][0] == "chat.send"
            assert call_args[0][1]["sessionKey"] == "session-key-123"
            assert call_args[0][1]["message"] == "LESSON CONTENT HERE"


class TestCreateFreshSession:
    @pytest.mark.asyncio
    async def test_create_calls_sessions_patch(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (True, {})
            result = await create_fresh_session("session-key-123", label="architect")
            assert result is True
            mock_rpc.assert_called_once_with(
                "sessions.patch", {"key": "session-key-123", "label": "architect"}
            )

    @pytest.mark.asyncio
    async def test_create_without_label(self, mock_oc_config):
        with patch("fleet.infra.gateway_client._gateway_rpc", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = (True, {})
            result = await create_fresh_session("session-key-123")
            assert result is True
            mock_rpc.assert_called_once_with(
                "sessions.patch", {"key": "session-key-123"}
            )