"""Tests for shadow routing (M-MU03)."""

from fleet.core.shadow_routing import (
    ShadowResult,
    ShadowRouter,
    compare_responses,
)


# ─── ShadowResult ─────────────────────────────────────────────


def test_result_candidate_faster():
    r = ShadowResult(
        task_id="t1", task_type="heartbeat",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=2.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=1.0, candidate_passed=True,
    )
    assert r.candidate_faster
    assert r.latency_diff_seconds == -1.0


def test_result_candidate_slower():
    r = ShadowResult(
        task_id="t1", task_type="heartbeat",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=2.0, candidate_passed=True,
    )
    assert not r.candidate_faster
    assert r.latency_diff_seconds == 1.0


def test_result_upgrade_worthy():
    r = ShadowResult(
        task_id="t1", task_type="heartbeat",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=1.5, candidate_passed=True,
        responses_agree=True,
    )
    assert r.candidate_upgrade_worthy


def test_result_not_upgrade_worthy_failed():
    r = ShadowResult(
        task_id="t1", task_type="heartbeat",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="bad",
        candidate_latency_seconds=1.5, candidate_passed=False,
        responses_agree=False,
    )
    assert not r.candidate_upgrade_worthy


def test_result_to_dict():
    r = ShadowResult(
        task_id="t1", task_type="review",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=0.8, candidate_passed=True,
        responses_agree=True,
    )
    d = r.to_dict()
    assert d["task_id"] == "t1"
    assert d["candidate_faster"] is True
    assert d["candidate_upgrade_worthy"] is True
    assert d["production_latency"] == 1.0


def test_result_to_stamp_metadata():
    r = ShadowResult(
        task_id="t1", task_type="review",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=0.8, candidate_passed=True,
        responses_agree=True,
    )
    meta = r.to_stamp_metadata()
    assert meta["shadow_routing"] is True
    assert meta["shadow_candidate_model"] == "qwen3-8b"
    assert meta["shadow_candidate_passed"] is True
    assert meta["shadow_responses_agree"] is True
    assert meta["shadow_candidate_faster"] is True


# ─── compare_responses ─────────────────────────────────────────


def test_compare_expected_strings_both_pass():
    prod_ok, cand_ok, notes = compare_responses(
        "HEARTBEAT_OK", "HEARTBEAT_OK",
        expected_contains=["HEARTBEAT_OK"],
    )
    assert prod_ok
    assert cand_ok


def test_compare_expected_strings_candidate_fails():
    prod_ok, cand_ok, notes = compare_responses(
        "HEARTBEAT_OK", "I'm not sure what to do",
        expected_contains=["HEARTBEAT_OK"],
    )
    assert prod_ok
    assert not cand_ok
    assert "candidate missing" in notes


def test_compare_json_keys_both_pass():
    prod = '{"steps": ["a"], "risk_level": "low"}'
    cand = '{"steps": ["b"], "risk_level": "high"}'
    prod_ok, cand_ok, notes = compare_responses(
        prod, cand, expected_json_keys=["steps", "risk_level"],
    )
    assert prod_ok
    assert cand_ok


def test_compare_json_keys_candidate_missing():
    prod = '{"steps": ["a"], "risk_level": "low"}'
    cand = '{"steps": ["b"]}'
    prod_ok, cand_ok, notes = compare_responses(
        prod, cand, expected_json_keys=["steps", "risk_level"],
    )
    assert prod_ok
    assert not cand_ok
    assert "candidate missing JSON keys" in notes


def test_compare_json_candidate_invalid():
    prod = '{"steps": ["a"]}'
    cand = "not json at all"
    prod_ok, cand_ok, notes = compare_responses(
        prod, cand, expected_json_keys=["steps"],
    )
    assert prod_ok
    assert not cand_ok
    assert "candidate invalid JSON" in notes


def test_compare_no_expectations():
    prod_ok, cand_ok, notes = compare_responses("hello", "world")
    assert prod_ok
    assert cand_ok
    assert "both pass by default" in notes


def test_compare_json_in_code_block():
    prod = '```json\n{"key": "val"}\n```'
    cand = '{"key": "val"}'
    prod_ok, cand_ok, _ = compare_responses(
        prod, cand, expected_json_keys=["key"],
    )
    assert prod_ok
    assert cand_ok


# ─── ShadowRouter ──────────────────────────────────────────────


def test_router_init():
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    assert router.production_model == "hermes-3b"
    assert router.candidate_model == "qwen3-8b"
    assert router.total_comparisons == 0


def test_router_record():
    router = ShadowRouter()
    result = ShadowResult(
        task_id="t1", task_type="heartbeat",
        production_model="hermes-3b", production_response="OK",
        production_latency_seconds=1.0, production_passed=True,
        candidate_model="qwen3-8b", candidate_response="OK",
        candidate_latency_seconds=0.9, candidate_passed=True,
        responses_agree=True,
    )
    router.record(result)
    assert router.total_comparisons == 1


def test_router_record_comparison():
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    result = router.record_comparison(
        task_id="t1", task_type="heartbeat",
        production_response="HEARTBEAT_OK",
        production_latency=1.2,
        candidate_response="HEARTBEAT_OK",
        candidate_latency=0.9,
        expected_contains=["HEARTBEAT_OK"],
    )
    assert result.production_passed
    assert result.candidate_passed
    assert result.responses_agree
    assert router.total_comparisons == 1


def test_router_record_comparison_candidate_fails():
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    result = router.record_comparison(
        task_id="t1", task_type="heartbeat",
        production_response="HEARTBEAT_OK",
        production_latency=1.2,
        candidate_response="I don't understand",
        candidate_latency=0.8,
        expected_contains=["HEARTBEAT_OK"],
    )
    assert result.production_passed
    assert not result.candidate_passed
    assert not result.responses_agree


def test_router_max_results():
    router = ShadowRouter(max_results=3)
    for i in range(5):
        router.record(ShadowResult(
            task_id=f"t{i}", task_type="heartbeat",
            production_model="hermes-3b", production_response="OK",
            production_latency_seconds=1.0, production_passed=True,
            candidate_model="qwen3-8b", candidate_response="OK",
            candidate_latency_seconds=1.0, candidate_passed=True,
        ))
    assert router.total_comparisons == 3


# ─── Metrics ───────────────────────────────────────────────────


def _populated_router() -> ShadowRouter:
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    # 3 heartbeats: 2 agree, 1 candidate fails
    router.record_comparison(
        task_id="t1", task_type="heartbeat",
        production_response="HEARTBEAT_OK", production_latency=1.0,
        candidate_response="HEARTBEAT_OK", candidate_latency=0.8,
        expected_contains=["HEARTBEAT_OK"],
    )
    router.record_comparison(
        task_id="t2", task_type="heartbeat",
        production_response="HEARTBEAT_OK", production_latency=1.2,
        candidate_response="HEARTBEAT_OK", candidate_latency=0.9,
        expected_contains=["HEARTBEAT_OK"],
    )
    router.record_comparison(
        task_id="t3", task_type="heartbeat",
        production_response="HEARTBEAT_OK", production_latency=1.1,
        candidate_response="dunno", candidate_latency=0.7,
        expected_contains=["HEARTBEAT_OK"],
    )
    # 2 reviews: both agree
    router.record_comparison(
        task_id="t4", task_type="review",
        production_response='{"passed": true}', production_latency=2.0,
        candidate_response='{"passed": true}', candidate_latency=1.5,
        expected_json_keys=["passed"],
    )
    router.record_comparison(
        task_id="t5", task_type="review",
        production_response='{"passed": false}', production_latency=1.8,
        candidate_response='{"passed": false}', candidate_latency=1.6,
        expected_json_keys=["passed"],
    )
    return router


def test_agreement_rate():
    router = _populated_router()
    # 4 agree out of 5
    assert abs(router.agreement_rate - 0.8) < 0.01


def test_candidate_pass_rate():
    router = _populated_router()
    # 4 pass out of 5
    assert abs(router.candidate_pass_rate - 0.8) < 0.01


def test_production_pass_rate():
    router = _populated_router()
    assert router.production_pass_rate == 1.0


def test_candidate_faster_rate():
    router = _populated_router()
    # All 5 candidates are faster
    assert router.candidate_faster_rate == 1.0


def test_upgrade_worthy_rate():
    router = _populated_router()
    # 4 out of 5 are upgrade-worthy (passed + agree)
    assert abs(router.upgrade_worthy_rate - 0.8) < 0.01


def test_avg_latencies():
    router = _populated_router()
    assert router.avg_production_latency() > 0
    assert router.avg_candidate_latency() > 0
    assert router.avg_candidate_latency() < router.avg_production_latency()


def test_empty_router_metrics():
    router = ShadowRouter()
    assert router.agreement_rate == 0.0
    assert router.candidate_pass_rate == 0.0
    assert router.candidate_faster_rate == 0.0
    assert router.avg_production_latency() == 0.0
    assert router.avg_candidate_latency() == 0.0


# ─── By Task Type ──────────────────────────────────────────────


def test_by_task_type():
    router = _populated_router()
    breakdown = router.by_task_type()
    assert "heartbeat" in breakdown
    assert "review" in breakdown
    assert breakdown["heartbeat"]["total"] == 3
    assert breakdown["review"]["total"] == 2
    assert breakdown["review"]["agreement_rate"] == 1.0


# ─── Summary & Report ──────────────────────────────────────────


def test_summary():
    router = _populated_router()
    s = router.summary()
    assert s["total_comparisons"] == 5
    assert s["production_model"] == "hermes-3b"
    assert s["candidate_model"] == "qwen3-8b"
    assert "by_task_type" in s


def test_summary_empty():
    router = ShadowRouter()
    s = router.summary()
    assert s["total_comparisons"] == 0


def test_format_report():
    router = _populated_router()
    report = router.format_report()
    assert "Shadow Routing Report" in report
    assert "hermes-3b" in report
    assert "qwen3-8b" in report
    assert "heartbeat" in report
    assert "Promotion verdict" in report


def test_format_report_ready():
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    # All pass and agree
    for i in range(5):
        router.record_comparison(
            task_id=f"t{i}", task_type="heartbeat",
            production_response="HEARTBEAT_OK", production_latency=1.0,
            candidate_response="HEARTBEAT_OK", candidate_latency=0.8,
            expected_contains=["HEARTBEAT_OK"],
        )
    report = router.format_report()
    assert "READY" in report


def test_format_report_not_ready():
    router = ShadowRouter("hermes-3b", "qwen3-8b")
    # All fail
    for i in range(5):
        router.record_comparison(
            task_id=f"t{i}", task_type="heartbeat",
            production_response="HEARTBEAT_OK", production_latency=1.0,
            candidate_response="nope", candidate_latency=0.8,
            expected_contains=["HEARTBEAT_OK"],
        )
    report = router.format_report()
    assert "NOT READY" in report