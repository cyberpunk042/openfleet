"""OpenAI-compatible HTTP client for LocalAI and OpenRouter free tier (M-BR04).

Provides a unified client for any OpenAI-compatible API endpoint.
Used by the router when dispatching to non-Claude backends:
  - LocalAI (http://localhost:8090/v1)
  - OpenRouter free (https://openrouter.ai/api/v1)

Both use the standard OpenAI chat completions format.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""

    role: str       # "system", "user", "assistant"
    content: str


@dataclass
class CompletionResult:
    """Result from a chat completion request."""

    content: str
    model: str = ""
    finish_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    backend: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.content != ""


@dataclass
class OpenAIClientConfig:
    """Configuration for an OpenAI-compatible endpoint."""

    base_url: str                    # e.g., "http://localhost:8090/v1"
    api_key: str = ""                # Optional — LocalAI doesn't need one
    default_model: str = ""          # e.g., "hermes-3b" or "openrouter/free"
    timeout_seconds: int = 30
    max_retries: int = 2
    extra_headers: dict = field(default_factory=dict)


class OpenAICompatibleClient:
    """HTTP client for OpenAI-compatible chat completion APIs.

    Works with LocalAI, OpenRouter, and any compatible endpoint.
    """

    def __init__(self, config: OpenAIClientConfig) -> None:
        self._config = config
        self._base_url = config.base_url.rstrip("/")

    @property
    def endpoint(self) -> str:
        return f"{self._base_url}/chat/completions"

    @property
    def models_endpoint(self) -> str:
        return f"{self._base_url}/models"

    def chat(
        self,
        messages: list[ChatMessage],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "",
    ) -> CompletionResult:
        """Send a synchronous chat completion request.

        Args:
            messages: Conversation history.
            model: Model to use (falls back to config default).
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.
            system_prompt: Prepended as system message if provided.

        Returns:
            CompletionResult with the response or error.
        """
        import urllib.request
        import urllib.error

        model = model or self._config.default_model
        if not model:
            return CompletionResult(
                content="", error="no model specified",
                backend=self._base_url,
            )

        # Build messages list
        msg_dicts = []
        if system_prompt:
            msg_dicts.append({"role": "system", "content": system_prompt})
        for m in messages:
            msg_dicts.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "messages": msg_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
            **self._config.extra_headers,
        }
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        data = json.dumps(payload).encode()
        start = time.time()

        for attempt in range(self._config.max_retries + 1):
            try:
                req = urllib.request.Request(
                    self.endpoint,
                    data=data,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(
                    req, timeout=self._config.timeout_seconds,
                ) as resp:
                    body = json.loads(resp.read().decode())
                    latency = int((time.time() - start) * 1000)
                    return self._parse_response(body, model, latency)

            except urllib.error.HTTPError as e:
                error_body = e.read().decode() if e.fp else str(e)
                if attempt < self._config.max_retries and e.code in (429, 502, 503):
                    time.sleep(1 * (attempt + 1))  # Simple backoff
                    continue
                return CompletionResult(
                    content="",
                    error=f"HTTP {e.code}: {error_body[:200]}",
                    backend=self._base_url,
                    latency_ms=int((time.time() - start) * 1000),
                )
            except Exception as e:
                if attempt < self._config.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                return CompletionResult(
                    content="",
                    error=f"{type(e).__name__}: {str(e)[:200]}",
                    backend=self._base_url,
                    latency_ms=int((time.time() - start) * 1000),
                )

        return CompletionResult(
            content="", error="max retries exceeded",
            backend=self._base_url,
        )

    def list_models(self) -> list[str]:
        """List available models on the endpoint."""
        import urllib.request

        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        try:
            req = urllib.request.Request(
                self.models_endpoint, headers=headers,
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode())
                return [m["id"] for m in body.get("data", [])]
        except Exception:
            return []

    def health_check(self) -> bool:
        """Check if the endpoint is reachable."""
        models = self.list_models()
        return len(models) > 0

    def _parse_response(
        self, body: dict, model: str, latency_ms: int,
    ) -> CompletionResult:
        """Parse the OpenAI-format response body."""
        choices = body.get("choices", [])
        if not choices:
            return CompletionResult(
                content="", error="no choices in response",
                model=model, backend=self._base_url,
                latency_ms=latency_ms,
            )

        choice = choices[0]
        message = choice.get("message", {})
        usage = body.get("usage", {})

        return CompletionResult(
            content=message.get("content", ""),
            model=body.get("model", model),
            finish_reason=choice.get("finish_reason", ""),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency_ms,
            backend=self._base_url,
        )


# ─── Pre-configured Clients ────────────────────────────────────────


def create_localai_client(
    base_url: str = "http://localhost:8090/v1",
    model: str = "hermes-3b",
) -> OpenAICompatibleClient:
    """Create a client configured for LocalAI."""
    return OpenAICompatibleClient(OpenAIClientConfig(
        base_url=base_url,
        default_model=model,
        timeout_seconds=60,  # LocalAI cold starts can be slow
        max_retries=1,
    ))


def create_openrouter_client(
    api_key: str = "",
    model: str = "openrouter/auto",
) -> OpenAICompatibleClient:
    """Create a client configured for OpenRouter free tier.

    OpenRouter free tier auto-selects from 29 free models
    when model is "openrouter/auto" or a free model ID.

    API key is optional for free models but recommended
    for rate limit tracking.
    """
    import os
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")

    return OpenAICompatibleClient(OpenAIClientConfig(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_model=model,
        timeout_seconds=30,
        max_retries=2,
        extra_headers={
            "HTTP-Referer": "https://github.com/openclaw-fleet",
            "X-Title": "OpenClaw Fleet",
        },
    ))