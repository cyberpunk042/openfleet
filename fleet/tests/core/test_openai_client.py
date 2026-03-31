"""Tests for OpenAI-compatible client (M-BR04).

Tests the client logic without making real HTTP calls —
uses mock responses to verify parsing, error handling, and config.
"""

import json
from unittest.mock import MagicMock, patch

from fleet.core.openai_client import (
    ChatMessage,
    CompletionResult,
    OpenAIClientConfig,
    OpenAICompatibleClient,
    create_localai_client,
    create_openrouter_client,
)


# ─── Config and Construction ──────────────────────────────────────


def test_config_defaults():
    cfg = OpenAIClientConfig(base_url="http://localhost:8090/v1")
    assert cfg.timeout_seconds == 30
    assert cfg.max_retries == 2
    assert cfg.api_key == ""


def test_client_endpoint():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://localhost:8090/v1"),
    )
    assert client.endpoint == "http://localhost:8090/v1/chat/completions"
    assert client.models_endpoint == "http://localhost:8090/v1/models"


def test_client_strips_trailing_slash():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://localhost:8090/v1/"),
    )
    assert client.endpoint == "http://localhost:8090/v1/chat/completions"


# ─── Response Parsing ─────────────────────────────────────────────


def test_parse_valid_response():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://test/v1"),
    )
    body = {
        "model": "hermes-3b",
        "choices": [{
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 10,
            "total_tokens": 60,
        },
    }
    result = client._parse_response(body, "hermes-3b", latency_ms=150)
    assert result.ok
    assert result.content == "Hello!"
    assert result.model == "hermes-3b"
    assert result.finish_reason == "stop"
    assert result.input_tokens == 50
    assert result.output_tokens == 10
    assert result.total_tokens == 60
    assert result.latency_ms == 150


def test_parse_empty_choices():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://test/v1"),
    )
    body = {"choices": []}
    result = client._parse_response(body, "test", latency_ms=100)
    assert not result.ok
    assert "no choices" in result.error


def test_parse_missing_usage():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://test/v1"),
    )
    body = {
        "choices": [{
            "message": {"content": "OK"},
            "finish_reason": "stop",
        }],
    }
    result = client._parse_response(body, "test", latency_ms=50)
    assert result.ok
    assert result.total_tokens == 0  # No usage data


# ─── CompletionResult ─────────────────────────────────────────────


def test_result_ok():
    r = CompletionResult(content="hello", model="test")
    assert r.ok


def test_result_not_ok_error():
    r = CompletionResult(content="", error="timeout")
    assert not r.ok


def test_result_not_ok_empty():
    r = CompletionResult(content="")
    assert not r.ok


# ─── Chat Message ─────────────────────────────────────────────────


def test_chat_message():
    m = ChatMessage(role="user", content="Hello")
    assert m.role == "user"
    assert m.content == "Hello"


# ─── No Model Error ───────────────────────────────────────────────


def test_chat_no_model_returns_error():
    client = OpenAICompatibleClient(
        OpenAIClientConfig(base_url="http://test/v1"),
    )
    result = client.chat([ChatMessage(role="user", content="hi")])
    assert not result.ok
    assert "no model" in result.error


# ─── Factory Functions ─────────────────────────────────────────────


def test_create_localai_client():
    client = create_localai_client()
    assert "localhost:8090" in client.endpoint
    assert client._config.default_model == "hermes-3b"
    assert client._config.timeout_seconds == 60


def test_create_localai_client_custom():
    client = create_localai_client(
        base_url="http://custom:9090/v1",
        model="codellama",
    )
    assert "custom:9090" in client.endpoint
    assert client._config.default_model == "codellama"


def test_create_openrouter_client():
    client = create_openrouter_client(api_key="test-key")
    assert "openrouter.ai" in client.endpoint
    assert client._config.api_key == "test-key"
    assert "HTTP-Referer" in client._config.extra_headers
    assert "X-Title" in client._config.extra_headers


def test_create_openrouter_client_default_model():
    client = create_openrouter_client()
    assert client._config.default_model == "openrouter/auto"


# ─── Mock HTTP Chat ───────────────────────────────────────────────


def test_chat_success_mock():
    """Test full chat flow with mocked HTTP."""
    response_body = json.dumps({
        "model": "hermes-3b",
        "choices": [{
            "message": {"role": "assistant", "content": "Test response"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        client = create_localai_client()
        result = client.chat([ChatMessage(role="user", content="hello")])

    assert result.ok
    assert result.content == "Test response"
    assert result.total_tokens == 25


def test_chat_connection_error_mock():
    """Test error handling with mocked connection failure."""
    with patch("urllib.request.urlopen", side_effect=ConnectionError("refused")):
        client = OpenAICompatibleClient(
            OpenAIClientConfig(
                base_url="http://test/v1",
                default_model="test",
                max_retries=0,
            ),
        )
        result = client.chat([ChatMessage(role="user", content="hello")])

    assert not result.ok
    assert "ConnectionError" in result.error