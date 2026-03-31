"""Tests for cross-model challenge system (M-IV04)."""

import json

from fleet.core.challenge import ChallengeType
from fleet.core.challenge_cross_model import (
    CROSS_MODEL_SYSTEM_PROMPT,
    CrossModelConfig,
    CrossModelResult,
    _extract_json_array,
    build_cross_model_messages,
    parse_cross_model_response,
    select_cross_model_config,
)
from fleet.core.challenge_protocol import ChallengeContext


# ─── CrossModelConfig ────────────────────────────────────────────


def test_config_label():
    cfg = CrossModelConfig(
        challenger_model="hermes-3b", challenger_backend="localai",
    )
    assert cfg.label == "cross-model:hermes-3b"


def test_config_defaults():
    cfg = CrossModelConfig(
        challenger_model="test", challenger_backend="localai",
    )
    assert cfg.temperature == 0.3
    assert cfg.max_tokens == 2048


# ─── select_cross_model_config ───────────────────────────────────


def test_select_simple_localai_available():
    cfg = select_cross_model_config("task", 2, "standard", localai_available=True)
    assert cfg.challenger_backend == "localai"
    assert cfg.challenger_model == "hermes-3b"


def test_select_simple_localai_unavailable():
    cfg = select_cross_model_config("task", 2, "standard", localai_available=False)
    assert cfg.challenger_backend == "openrouter"


def test_select_complex_task():
    cfg = select_cross_model_config("story", 5, "standard")
    assert cfg.challenger_backend == "openrouter"


def test_select_epic():
    cfg = select_cross_model_config("epic", 3, "standard")
    assert cfg.challenger_backend == "openrouter"


def test_select_blocker():
    cfg = select_cross_model_config("blocker", 1, "standard")
    assert cfg.challenger_backend == "openrouter"


def test_select_frugal_uses_localai():
    cfg = select_cross_model_config("story", 5, "frugal", localai_available=True)
    assert cfg.challenger_backend == "localai"
    assert cfg.challenger_model == "hermes-3b"


def test_select_survival_uses_localai():
    cfg = select_cross_model_config("blocker", 8, "survival", localai_available=True)
    assert cfg.challenger_backend == "localai"


# ─── build_cross_model_messages ──────────────────────────────────


def test_build_messages():
    ctx = ChallengeContext(
        task_id="t1", task_type="task", task_title="Test",
        requirement_verbatim="Must work", author_agent="dev",
        diff="+ some code",
    )
    messages = build_cross_model_messages(ctx)
    assert len(messages) == 1
    assert messages[0].role == "user"
    assert "Challenge Assignment" in messages[0].content


# ─── _extract_json_array ─────────────────────────────────────────


def test_extract_clean_array():
    result = _extract_json_array('[{"a": 1}]')
    assert result == '[{"a": 1}]'


def test_extract_from_code_fence():
    text = 'Here are the findings:\n```json\n[{"a": 1}]\n```\nDone.'
    result = _extract_json_array(text)
    assert result == '[{"a": 1}]'


def test_extract_from_surrounding_text():
    text = 'The findings are: [{"a": 1}] as you can see.'
    result = _extract_json_array(text)
    assert result == '[{"a": 1}]'


def test_extract_empty_string():
    assert _extract_json_array("") is None


def test_extract_no_array():
    assert _extract_json_array("No findings here.") is None


def test_extract_empty_array():
    result = _extract_json_array("[]")
    assert result == "[]"


# ─── parse_cross_model_response ──────────────────────────────────


def test_parse_valid_findings():
    response = json.dumps([
        {"category": "edge_case", "severity": "major",
         "description": "Missing null check", "evidence": "line 42"},
        {"category": "security", "severity": "critical",
         "description": "SQL injection risk", "evidence": "user input unescaped"},
    ])
    findings = parse_cross_model_response(response, round_number=1)
    assert len(findings) == 2
    assert findings[0].finding_id == "cm1-1"
    assert findings[0].category == "edge_case"
    assert findings[0].challenge_type == ChallengeType.CROSS_MODEL
    assert findings[1].severity == "critical"


def test_parse_empty_array():
    findings = parse_cross_model_response("[]")
    assert findings == []


def test_parse_invalid_json():
    findings = parse_cross_model_response("This is not JSON at all")
    assert findings == []


def test_parse_with_code_fence():
    response = '```json\n[{"category": "regression", "severity": "minor", "description": "Test gap"}]\n```'
    findings = parse_cross_model_response(response)
    assert len(findings) == 1
    assert findings[0].category == "regression"


def test_parse_invalid_category_defaults_general():
    response = json.dumps([
        {"category": "made_up", "severity": "major", "description": "Something"},
    ])
    findings = parse_cross_model_response(response)
    assert findings[0].category == "general"


def test_parse_invalid_severity_defaults_minor():
    response = json.dumps([
        {"category": "edge_case", "severity": "extreme", "description": "Something"},
    ])
    findings = parse_cross_model_response(response)
    assert findings[0].severity == "minor"


def test_parse_skips_entries_without_description():
    response = json.dumps([
        {"category": "edge_case", "severity": "major"},
        {"category": "regression", "severity": "minor", "description": "Valid one"},
    ])
    findings = parse_cross_model_response(response)
    assert len(findings) == 1
    assert findings[0].description == "Valid one"


def test_parse_skips_non_dict_entries():
    response = json.dumps([
        "not a dict",
        {"category": "edge_case", "severity": "major", "description": "Valid"},
    ])
    findings = parse_cross_model_response(response)
    assert len(findings) == 1


def test_parse_round_number_in_finding_id():
    response = json.dumps([
        {"category": "edge_case", "severity": "minor", "description": "Test"},
    ])
    findings = parse_cross_model_response(response, round_number=3)
    assert findings[0].finding_id == "cm3-1"
    assert findings[0].round_number == 3


# ─── CrossModelResult ────────────────────────────────────────────


def test_result_passed():
    r = CrossModelResult(success=True, findings=[])
    assert r.passed
    assert r.finding_count == 0


def test_result_failed_with_findings():
    from fleet.core.challenge import ChallengeFinding
    f = ChallengeFinding(
        finding_id="cm1-1", round_number=1,
        challenge_type="cross-model", category="edge_case",
        severity="major", description="Issue",
    )
    r = CrossModelResult(success=True, findings=[f])
    assert not r.passed
    assert r.finding_count == 1


def test_result_error():
    r = CrossModelResult(success=False, error="connection refused")
    assert not r.passed
    assert r.error == "connection refused"


def test_result_to_dict():
    r = CrossModelResult(
        success=True, findings=[], model="hermes-3b",
        backend="localai", tokens_used=150, latency_ms=1200,
    )
    d = r.to_dict()
    assert d["success"] is True
    assert d["passed"] is True
    assert d["model"] == "hermes-3b"
    assert d["tokens_used"] == 150


# ─── System Prompt ───────────────────────────────────────────────


def test_system_prompt_is_set():
    assert "adversarial" in CROSS_MODEL_SYSTEM_PROMPT
    assert "JSON array" in CROSS_MODEL_SYSTEM_PROMPT