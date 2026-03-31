"""Model benchmark framework (M-MU01).

Benchmarks LocalAI models against each other on fleet-representative
prompts. Used to evaluate Qwen3-8B (and future models) against
hermes-3b before promotion.

Design doc requirement:
> Benchmark: latency, quality, structured output.
> Compare against hermes-3b on fleet prompts.
> Document results.

Fleet-representative prompts:
  1. Heartbeat response (HEARTBEAT_OK)
  2. Task acceptance (structured plan)
  3. Simple review (pass/fail detection)
  4. Structured JSON output
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


# ─── Benchmark Prompt ───────────────────────────────────────────


@dataclass
class BenchmarkPrompt:
    """A prompt used to evaluate a model's capabilities."""

    name: str
    category: str                      # heartbeat, acceptance, review, structured
    system_message: str
    user_message: str
    expected_contains: list[str] = field(default_factory=list)
    expected_json_keys: list[str] = field(default_factory=list)
    max_tokens: int = 500


# Fleet-representative prompts from the design doc
FLEET_PROMPTS: list[BenchmarkPrompt] = [
    BenchmarkPrompt(
        name="heartbeat_ok",
        category="heartbeat",
        system_message="You are a fleet agent. Respond with HEARTBEAT_OK if you have no pending work.",
        user_message="Check for pending work. Your queue is empty.",
        expected_contains=["HEARTBEAT_OK"],
        max_tokens=50,
    ),
    BenchmarkPrompt(
        name="task_acceptance",
        category="acceptance",
        system_message=(
            "You are a software engineer agent. When given a task, respond with "
            "a structured plan as a JSON object with keys: steps (array of strings), "
            "estimated_sp (integer), risk_level (low/medium/high)."
        ),
        user_message=(
            "Task: Implement JWT validation middleware for the auth module. "
            "Story points: 5. Priority: high."
        ),
        expected_json_keys=["steps", "estimated_sp", "risk_level"],
        max_tokens=300,
    ),
    BenchmarkPrompt(
        name="simple_review",
        category="review",
        system_message=(
            "You are a QA agent. Review the following test output and respond "
            "with a JSON object: {\"passed\": true/false, \"reason\": \"...\"}"
        ),
        user_message=(
            "Test output:\n"
            "PASSED test_auth_login\n"
            "PASSED test_auth_logout\n"
            "FAILED test_auth_token_refresh (AssertionError: expected 200, got 401)\n"
            "3 passed, 1 failed"
        ),
        expected_json_keys=["passed", "reason"],
        expected_contains=["false", "fail"],
        max_tokens=200,
    ),
    BenchmarkPrompt(
        name="structured_json",
        category="structured",
        system_message="Respond ONLY with a valid JSON object. No other text.",
        user_message=(
            "Generate a JSON object describing a software task with keys: "
            "title (string), priority (low/medium/high/critical), "
            "story_points (integer 1-13), tags (array of strings)."
        ),
        expected_json_keys=["title", "priority", "story_points", "tags"],
        max_tokens=200,
    ),
    BenchmarkPrompt(
        name="error_analysis",
        category="review",
        system_message=(
            "You are a DevOps agent. Analyze the error and respond with "
            "a JSON object: {\"root_cause\": \"...\", \"severity\": \"low/medium/high/critical\", "
            "\"action\": \"...\"}"
        ),
        user_message=(
            "Error: ConnectionRefusedError at localhost:8090/v1/models\n"
            "Context: LocalAI health check failed during model swap.\n"
            "Last successful check: 30 seconds ago."
        ),
        expected_json_keys=["root_cause", "severity", "action"],
        max_tokens=200,
    ),
]


# ─── Benchmark Result ───────────────────────────────────────────


@dataclass
class BenchmarkResult:
    """Result of running one prompt against one model."""

    prompt_name: str
    model: str
    latency_seconds: float
    response_text: str
    contains_expected: bool = False
    has_expected_keys: bool = False
    is_valid_json: bool = False
    error: str = ""

    @property
    def passed(self) -> bool:
        """Whether the model produced an acceptable response."""
        if self.error:
            return False
        return self.contains_expected or self.has_expected_keys

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt_name,
            "model": self.model,
            "latency_seconds": round(self.latency_seconds, 3),
            "passed": self.passed,
            "contains_expected": self.contains_expected,
            "has_expected_keys": self.has_expected_keys,
            "is_valid_json": self.is_valid_json,
            "error": self.error,
        }


def evaluate_response(
    prompt: BenchmarkPrompt,
    model: str,
    response_text: str,
    latency_seconds: float,
) -> BenchmarkResult:
    """Evaluate a model's response against a benchmark prompt."""
    import json

    result = BenchmarkResult(
        prompt_name=prompt.name,
        model=model,
        latency_seconds=latency_seconds,
        response_text=response_text,
    )

    # Check expected substrings
    if prompt.expected_contains:
        lower_response = response_text.lower()
        result.contains_expected = all(
            exp.lower() in lower_response for exp in prompt.expected_contains
        )
    else:
        result.contains_expected = True  # No expected strings = pass

    # Check JSON structure
    if prompt.expected_json_keys:
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text)
            result.is_valid_json = True
            result.has_expected_keys = all(
                k in parsed for k in prompt.expected_json_keys
            )
        except (json.JSONDecodeError, IndexError):
            result.is_valid_json = False
            result.has_expected_keys = False
    else:
        result.has_expected_keys = True  # No expected keys = pass

    return result


# ─── Model Benchmark Suite ──────────────────────────────────────


@dataclass
class ModelBenchmarkSummary:
    """Summary of benchmarking a model against all prompts."""

    model: str
    total_prompts: int = 0
    passed: int = 0
    failed: int = 0
    avg_latency_seconds: float = 0.0
    json_compliance_rate: float = 0.0
    results: list[BenchmarkResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_prompts if self.total_prompts else 0.0

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "total_prompts": self.total_prompts,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 3),
            "avg_latency_seconds": round(self.avg_latency_seconds, 3),
            "json_compliance_rate": round(self.json_compliance_rate, 3),
            "results": [r.to_dict() for r in self.results],
        }


def summarize_results(model: str, results: list[BenchmarkResult]) -> ModelBenchmarkSummary:
    """Summarize benchmark results for one model."""
    summary = ModelBenchmarkSummary(model=model)
    summary.total_prompts = len(results)
    summary.results = results

    for r in results:
        if r.passed:
            summary.passed += 1
        else:
            summary.failed += 1

    if results:
        summary.avg_latency_seconds = sum(r.latency_seconds for r in results) / len(results)
        json_prompts = [r for r in results if r.is_valid_json or any(
            p.expected_json_keys for p in FLEET_PROMPTS if p.name == r.prompt_name
        )]
        if json_prompts:
            json_valid = sum(1 for r in json_prompts if r.is_valid_json)
            summary.json_compliance_rate = json_valid / len(json_prompts)

    return summary


# ─── Comparison ─────────────────────────────────────────────────


@dataclass
class ModelComparison:
    """Side-by-side comparison of two models."""

    model_a: str
    model_b: str
    summary_a: ModelBenchmarkSummary
    summary_b: ModelBenchmarkSummary

    @property
    def winner(self) -> str:
        """Which model performed better overall."""
        score_a = self.summary_a.pass_rate * 0.7 + (1 - min(self.summary_a.avg_latency_seconds, 5) / 5) * 0.3
        score_b = self.summary_b.pass_rate * 0.7 + (1 - min(self.summary_b.avg_latency_seconds, 5) / 5) * 0.3
        if score_a > score_b:
            return self.model_a
        elif score_b > score_a:
            return self.model_b
        return "tie"

    def to_dict(self) -> dict:
        return {
            "model_a": self.summary_a.to_dict(),
            "model_b": self.summary_b.to_dict(),
            "winner": self.winner,
        }

    def format_markdown(self) -> str:
        """Format comparison as markdown."""
        a = self.summary_a
        b = self.summary_b
        lines = [
            f"## Model Comparison: {self.model_a} vs {self.model_b}",
            "",
            "| Metric | {} | {} |".format(self.model_a, self.model_b),
            "|--------|{}|{}|".format("-" * (len(self.model_a) + 2), "-" * (len(self.model_b) + 2)),
            f"| Pass rate | {a.pass_rate:.1%} | {b.pass_rate:.1%} |",
            f"| Avg latency | {a.avg_latency_seconds:.3f}s | {b.avg_latency_seconds:.3f}s |",
            f"| JSON compliance | {a.json_compliance_rate:.1%} | {b.json_compliance_rate:.1%} |",
            f"| Passed | {a.passed}/{a.total_prompts} | {b.passed}/{b.total_prompts} |",
            "",
            f"**Winner:** {self.winner}",
        ]
        return "\n".join(lines)