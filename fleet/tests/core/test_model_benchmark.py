"""Tests for model benchmark framework (M-MU01)."""

from fleet.core.model_benchmark import (
    FLEET_PROMPTS,
    BenchmarkPrompt,
    BenchmarkResult,
    ModelBenchmarkSummary,
    ModelComparison,
    evaluate_response,
    summarize_results,
)


# ─── Fleet Prompts ──────────────────────────────────────────────


def test_fleet_prompts_exist():
    assert len(FLEET_PROMPTS) >= 5


def test_fleet_prompts_categories():
    categories = {p.category for p in FLEET_PROMPTS}
    assert "heartbeat" in categories
    assert "acceptance" in categories
    assert "review" in categories
    assert "structured" in categories


def test_fleet_prompts_have_names():
    for p in FLEET_PROMPTS:
        assert p.name
        assert p.system_message
        assert p.user_message


# ─── evaluate_response ──────────────────────────────────────────


def test_evaluate_heartbeat_pass():
    prompt = FLEET_PROMPTS[0]  # heartbeat_ok
    result = evaluate_response(prompt, "hermes-3b", "HEARTBEAT_OK", 1.2)
    assert result.passed
    assert result.contains_expected
    assert result.latency_seconds == 1.2


def test_evaluate_heartbeat_fail():
    prompt = FLEET_PROMPTS[0]
    result = evaluate_response(prompt, "hermes-3b", "I don't know what to do", 1.5)
    assert not result.contains_expected


def test_evaluate_json_pass():
    prompt = FLEET_PROMPTS[1]  # task_acceptance
    response = '{"steps": ["step1", "step2"], "estimated_sp": 5, "risk_level": "high"}'
    result = evaluate_response(prompt, "hermes-3b", response, 2.0)
    assert result.passed
    assert result.is_valid_json
    assert result.has_expected_keys


def test_evaluate_json_wrapped_in_code_block():
    prompt = FLEET_PROMPTS[1]
    response = '```json\n{"steps": ["s1"], "estimated_sp": 3, "risk_level": "low"}\n```'
    result = evaluate_response(prompt, "hermes-3b", response, 1.8)
    assert result.is_valid_json
    assert result.has_expected_keys


def test_evaluate_json_fail_invalid():
    prompt = FLEET_PROMPTS[1]
    result = evaluate_response(prompt, "hermes-3b", "not json at all", 1.0)
    assert not result.is_valid_json
    assert not result.has_expected_keys


def test_evaluate_json_fail_missing_keys():
    prompt = FLEET_PROMPTS[1]
    response = '{"steps": ["s1"]}'  # Missing estimated_sp and risk_level
    result = evaluate_response(prompt, "hermes-3b", response, 1.0)
    assert result.is_valid_json
    assert not result.has_expected_keys


def test_evaluate_review_pass():
    prompt = FLEET_PROMPTS[2]  # simple_review
    response = '{"passed": false, "reason": "test_auth_token_refresh failed"}'
    result = evaluate_response(prompt, "hermes-3b", response, 1.5)
    assert result.passed
    assert result.is_valid_json


def test_evaluate_no_expected_strings():
    prompt = BenchmarkPrompt(
        name="test", category="test",
        system_message="test", user_message="test",
        expected_json_keys=["key1"],
    )
    response = '{"key1": "value"}'
    result = evaluate_response(prompt, "test-model", response, 0.5)
    assert result.contains_expected  # No expected_contains = auto-pass
    assert result.has_expected_keys


def test_evaluate_no_expectations():
    prompt = BenchmarkPrompt(
        name="test", category="test",
        system_message="test", user_message="test",
    )
    result = evaluate_response(prompt, "test-model", "anything", 0.5)
    assert result.passed  # No expectations = pass


def test_evaluate_error():
    result = BenchmarkResult(
        prompt_name="test", model="test",
        latency_seconds=0.0, response_text="",
        error="Connection refused",
    )
    assert not result.passed


# ─── BenchmarkResult ────────────────────────────────────────────


def test_result_to_dict():
    r = BenchmarkResult(
        prompt_name="heartbeat_ok", model="hermes-3b",
        latency_seconds=1.2, response_text="HEARTBEAT_OK",
        contains_expected=True, has_expected_keys=True,
    )
    d = r.to_dict()
    assert d["prompt"] == "heartbeat_ok"
    assert d["passed"] is True
    assert d["latency_seconds"] == 1.2


# ─── summarize_results ──────────────────────────────────────────


def test_summarize_all_passed():
    results = [
        BenchmarkResult(
            prompt_name="p1", model="test",
            latency_seconds=1.0, response_text="ok",
            contains_expected=True, has_expected_keys=True,
        ),
        BenchmarkResult(
            prompt_name="p2", model="test",
            latency_seconds=2.0, response_text="ok",
            contains_expected=True, has_expected_keys=True,
        ),
    ]
    summary = summarize_results("test", results)
    assert summary.pass_rate == 1.0
    assert summary.passed == 2
    assert summary.failed == 0
    assert summary.avg_latency_seconds == 1.5


def test_summarize_mixed():
    results = [
        BenchmarkResult(
            prompt_name="p1", model="test",
            latency_seconds=1.0, response_text="ok",
            contains_expected=True, has_expected_keys=True,
        ),
        BenchmarkResult(
            prompt_name="p2", model="test",
            latency_seconds=2.0, response_text="bad",
            contains_expected=False, has_expected_keys=False,
        ),
    ]
    summary = summarize_results("test", results)
    assert summary.pass_rate == 0.5
    assert summary.passed == 1
    assert summary.failed == 1


def test_summarize_empty():
    summary = summarize_results("test", [])
    assert summary.pass_rate == 0.0
    assert summary.total_prompts == 0


def test_summary_to_dict():
    summary = ModelBenchmarkSummary(
        model="hermes-3b", total_prompts=5, passed=4, failed=1,
        avg_latency_seconds=1.5, json_compliance_rate=0.8,
    )
    d = summary.to_dict()
    assert d["model"] == "hermes-3b"
    assert d["pass_rate"] == 0.8


# ─── ModelComparison ────────────────────────────────────────────


def test_comparison_winner():
    a = ModelBenchmarkSummary(
        model="hermes-3b", total_prompts=5, passed=3, failed=2,
        avg_latency_seconds=1.2,
    )
    b = ModelBenchmarkSummary(
        model="qwen3-8b", total_prompts=5, passed=5, failed=0,
        avg_latency_seconds=1.5,
    )
    comp = ModelComparison(model_a="hermes-3b", model_b="qwen3-8b", summary_a=a, summary_b=b)
    assert comp.winner == "qwen3-8b"


def test_comparison_tie():
    a = ModelBenchmarkSummary(
        model="model-a", total_prompts=5, passed=4, failed=1,
        avg_latency_seconds=1.0,
    )
    b = ModelBenchmarkSummary(
        model="model-b", total_prompts=5, passed=4, failed=1,
        avg_latency_seconds=1.0,
    )
    comp = ModelComparison(model_a="model-a", model_b="model-b", summary_a=a, summary_b=b)
    assert comp.winner == "tie"


def test_comparison_to_dict():
    a = ModelBenchmarkSummary(model="a", total_prompts=1, passed=1)
    b = ModelBenchmarkSummary(model="b", total_prompts=1, passed=0)
    comp = ModelComparison(model_a="a", model_b="b", summary_a=a, summary_b=b)
    d = comp.to_dict()
    assert "model_a" in d
    assert "model_b" in d
    assert "winner" in d


def test_comparison_markdown():
    a = ModelBenchmarkSummary(
        model="hermes-3b", total_prompts=5, passed=3, failed=2,
        avg_latency_seconds=1.2, json_compliance_rate=0.6,
    )
    b = ModelBenchmarkSummary(
        model="qwen3-8b", total_prompts=5, passed=5, failed=0,
        avg_latency_seconds=1.5, json_compliance_rate=1.0,
    )
    comp = ModelComparison(model_a="hermes-3b", model_b="qwen3-8b", summary_a=a, summary_b=b)
    md = comp.format_markdown()
    assert "hermes-3b" in md
    assert "qwen3-8b" in md
    assert "Winner" in md