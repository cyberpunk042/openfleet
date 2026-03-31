"""Cross-model challenge system (M-IV04).

Uses a different LLM to challenge work produced by the original model.
This provides independent verification — a second opinion from a model
with different training, biases, and failure modes.

Model selection strategy:
  - LocalAI (hermes-3b) as free challenger for simple tasks
  - OpenRouter free tier for cross-vendor verification
  - Stronger model (opus) for critical/security tasks

The cross-model challenge sends the same adversarial prompt as agent
challenges, but to an LLM endpoint rather than dispatching to a fleet
agent. Results are parsed and converted to ChallengeFinding objects.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from fleet.core.challenge import (
    ChallengeFinding,
    ChallengeRound,
    ChallengeType,
)
from fleet.core.challenge_protocol import ChallengeContext
from fleet.core.openai_client import (
    ChatMessage,
    CompletionResult,
    OpenAICompatibleClient,
)

logger = logging.getLogger(__name__)


# ─── Cross-Model Challenger Configuration ─────────────────────────


@dataclass
class CrossModelConfig:
    """Configuration for cross-model challenge."""

    challenger_model: str            # Model ID (e.g., "hermes-3b", "openrouter/auto")
    challenger_backend: str          # "localai" or "openrouter"
    temperature: float = 0.3        # Low temp for consistent analysis
    max_tokens: int = 2048
    system_prompt: str = ""

    @property
    def label(self) -> str:
        """Label for provenance tracking (e.g., 'cross-model:hermes-3b')."""
        return f"cross-model:{self.challenger_model}"


def select_cross_model_config(
    task_type: str,
    story_points: int,
    budget_mode: str,
    localai_available: bool = True,
) -> CrossModelConfig:
    """Select the cross-model challenger based on task context.

    Strategy:
      - Simple tasks (SP <= 3): LocalAI if available, else OpenRouter free
      - Complex tasks (SP >= 5): OpenRouter free (different vendor)
      - Security/blocker: OpenRouter free (independent verification)
      - Frugal/survival: LocalAI only (zero external cost)

    Args:
        task_type: Type of task being challenged.
        story_points: Task complexity.
        budget_mode: Current budget mode.
        localai_available: Whether LocalAI is reachable.

    Returns:
        CrossModelConfig for the challenger.
    """
    # Budget-constrained: LocalAI only
    if budget_mode in ("frugal", "survival"):
        if localai_available:
            return CrossModelConfig(
                challenger_model="hermes-3b",
                challenger_backend="localai",
            )
        # Can't do cross-model without a free backend
        return CrossModelConfig(
            challenger_model="hermes-3b",
            challenger_backend="localai",
        )

    # Security/critical: different vendor for independence
    if task_type in ("blocker", "concern"):
        return CrossModelConfig(
            challenger_model="openrouter/auto",
            challenger_backend="openrouter",
        )

    # Complex: different vendor
    if story_points >= 5 or task_type in ("epic",):
        return CrossModelConfig(
            challenger_model="openrouter/auto",
            challenger_backend="openrouter",
        )

    # Simple: LocalAI if available
    if localai_available:
        return CrossModelConfig(
            challenger_model="hermes-3b",
            challenger_backend="localai",
        )

    return CrossModelConfig(
        challenger_model="openrouter/auto",
        challenger_backend="openrouter",
    )


# ─── Cross-Model Challenge Execution ─────────────────────────────


CROSS_MODEL_SYSTEM_PROMPT = """\
You are a code reviewer performing an adversarial challenge. Your job is to find \
flaws in the work presented to you. Be thorough and critical.

Respond with a JSON array of findings. Each finding must have:
- "category": one of regression, edge_case, logic_error, requirement_gap, \
security, performance, test_gap
- "severity": one of critical, major, minor, info
- "description": clear explanation of the issue
- "evidence": how to verify or reproduce

If the work is correct and you find no issues, respond with an empty array: []

IMPORTANT: Respond ONLY with the JSON array. No other text."""


def build_cross_model_messages(
    context: ChallengeContext,
) -> list[ChatMessage]:
    """Build the message list for cross-model challenge.

    Args:
        context: The challenge context with diff, requirement, etc.

    Returns:
        List of ChatMessage objects for the API call.
    """
    prompt = context.to_prompt()
    return [ChatMessage(role="user", content=prompt)]


def execute_cross_model_challenge(
    client: OpenAICompatibleClient,
    context: ChallengeContext,
    config: CrossModelConfig,
) -> CrossModelResult:
    """Execute a cross-model challenge via API call.

    Sends the challenge context to a different LLM and parses
    the response into findings.

    Args:
        client: The OpenAI-compatible client to use.
        context: Challenge context built from the task.
        config: Cross-model configuration.

    Returns:
        CrossModelResult with parsed findings and metadata.
    """
    messages = build_cross_model_messages(context)

    result = client.chat(
        messages=messages,
        model=config.challenger_model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        system_prompt=config.system_prompt or CROSS_MODEL_SYSTEM_PROMPT,
    )

    if not result.ok:
        return CrossModelResult(
            success=False,
            error=result.error or "unknown error",
            model=config.challenger_model,
            backend=config.challenger_backend,
            tokens_used=result.total_tokens,
            latency_ms=result.latency_ms,
        )

    findings = parse_cross_model_response(
        result.content,
        round_number=context.round_number,
    )

    return CrossModelResult(
        success=True,
        findings=findings,
        raw_response=result.content,
        model=config.challenger_model,
        backend=config.challenger_backend,
        tokens_used=result.total_tokens,
        latency_ms=result.latency_ms,
    )


# ─── Response Parsing ────────────────────────────────────────────


VALID_CATEGORIES = {
    "regression", "edge_case", "logic_error", "requirement_gap",
    "security", "performance", "test_gap", "general",
}

VALID_SEVERITIES = {"critical", "major", "minor", "info"}


def parse_cross_model_response(
    response: str,
    round_number: int = 1,
) -> list[ChallengeFinding]:
    """Parse the cross-model LLM response into ChallengeFinding objects.

    Handles common LLM response quirks:
    - JSON wrapped in markdown code fences
    - Extra text before/after the JSON
    - Invalid categories or severities

    Args:
        response: Raw LLM response text.
        round_number: Current challenge round number.

    Returns:
        List of validated ChallengeFinding objects.
    """
    cleaned = _extract_json_array(response)
    if cleaned is None:
        return []

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        logger.warning("cross-model response was not valid JSON: %s", response[:200])
        return []

    if not isinstance(data, list):
        return []

    findings: list[ChallengeFinding] = []
    for i, item in enumerate(data, 1):
        if not isinstance(item, dict):
            continue

        description = item.get("description", "")
        if not description:
            continue

        category = item.get("category", "general")
        if category not in VALID_CATEGORIES:
            category = "general"

        severity = item.get("severity", "minor")
        if severity not in VALID_SEVERITIES:
            severity = "minor"

        findings.append(ChallengeFinding(
            finding_id=f"cm{round_number}-{i}",
            round_number=round_number,
            challenge_type=ChallengeType.CROSS_MODEL,
            category=category,
            severity=severity,
            description=description,
            evidence=item.get("evidence", ""),
        ))

    return findings


def _extract_json_array(text: str) -> str | None:
    """Extract a JSON array from potentially messy LLM output.

    Handles:
    - Clean JSON arrays
    - Markdown code fences (```json ... ```)
    - Text before/after the array
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # Try direct parse first
    if text.startswith("["):
        return text

    # Try extracting from code fence
    fence_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    # Try finding any JSON array in the text
    bracket_match = re.search(r'\[.*\]', text, re.DOTALL)
    if bracket_match:
        return bracket_match.group(0)

    return None


# ─── Result Container ────────────────────────────────────────────


@dataclass
class CrossModelResult:
    """Result of a cross-model challenge execution."""

    success: bool
    findings: list[ChallengeFinding] = field(default_factory=list)
    raw_response: str = ""
    error: str = ""
    model: str = ""
    backend: str = ""
    tokens_used: int = 0
    latency_ms: int = 0

    @property
    def passed(self) -> bool:
        """True if challenge succeeded and found no issues."""
        return self.success and len(self.findings) == 0

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "passed": self.passed,
            "findings_count": self.finding_count,
            "model": self.model,
            "backend": self.backend,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }