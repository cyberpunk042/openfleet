"""Tests for session metrics collection (M-LA03)."""

import time

from fleet.core.session_metrics import SessionMetrics, SessionStore


# ─── SessionMetrics ────────────────────────────────────────────────


def test_session_starts_with_timestamp():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    assert s.start_time > 0
    assert s.end_time == 0.0
    assert not s.is_finished


def test_session_records_tools():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    s.record_tool_call("fleet_read_context")
    s.record_tool_call("fleet_commit")
    s.record_tool_call("fleet_read_context")  # Duplicate name
    assert s.tools_called == ["fleet_read_context", "fleet_commit"]
    assert s.tool_call_count == 3  # Total calls counted


def test_session_records_tokens():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    s.record_tokens(input_tokens=500, output_tokens=1200)
    s.record_tokens(input_tokens=300, output_tokens=800)
    assert s.input_tokens == 800
    assert s.output_tokens == 2000
    assert s.total_tokens == 2800


def test_session_records_errors():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    s.record_error("timeout")
    s.record_error("rate limit")
    assert s.error_count == 2
    assert "timeout" in s.errors


def test_session_finish():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    s.finish()
    assert s.is_finished
    assert s.end_time > 0
    assert s.duration_seconds >= 0


def test_session_duration():
    s = SessionMetrics(task_id="t1", agent_name="worker")
    s.start_time = time.time() - 10  # 10 seconds ago
    assert s.duration_seconds >= 9


def test_to_stamp_kwargs():
    s = SessionMetrics(
        task_id="t1", agent_name="worker",
        session_type="retry", iteration=2,
    )
    s.record_tool_call("fleet_commit")
    s.record_tokens(input_tokens=100, output_tokens=200)
    s.finish()

    kwargs = s.to_stamp_kwargs()
    assert kwargs["session_type"] == "retry"
    assert kwargs["iteration"] == 2
    assert kwargs["estimated_tokens"] == 300
    assert "fleet_commit" in kwargs["tools_called"]
    assert kwargs["duration_seconds"] >= 0


def test_to_dict():
    s = SessionMetrics(task_id="t1", agent_name="worker", backend="localai", model="hermes-3b")
    s.record_tokens(input_tokens=100, output_tokens=200)
    s.finish()

    d = s.to_dict()
    assert d["task_id"] == "t1"
    assert d["backend"] == "localai"
    assert d["total_tokens"] == 300
    assert d["duration_seconds"] >= 0


# ─── SessionStore ──────────────────────────────────────────────────


def test_store_start_session():
    store = SessionStore()
    s = store.start_session("t1", "worker")
    assert s.task_id == "t1"
    assert store.active_count == 1


def test_store_get_active():
    store = SessionStore()
    store.start_session("t1", "worker")
    s = store.get_active("t1")
    assert s is not None
    assert s.task_id == "t1"


def test_store_get_active_missing():
    store = SessionStore()
    assert store.get_active("nonexistent") is None


def test_store_finish_session():
    store = SessionStore()
    store.start_session("t1", "worker")
    finished = store.finish_session("t1")
    assert finished is not None
    assert finished.is_finished
    assert store.active_count == 0
    assert store.completed_count == 1


def test_store_finish_nonexistent():
    store = SessionStore()
    assert store.finish_session("nonexistent") is None


def test_store_get_completed():
    store = SessionStore()
    store.start_session("t1", "worker")
    store.finish_session("t1")
    completed = store.get_completed("t1")
    assert completed is not None
    assert completed.task_id == "t1"


def test_store_caps_completed():
    store = SessionStore(max_completed=5)
    for i in range(10):
        store.start_session(f"t{i}", "worker")
        store.finish_session(f"t{i}")
    assert store.completed_count == 5
    # Oldest sessions pruned
    assert store.get_completed("t0") is None
    assert store.get_completed("t9") is not None


def test_store_summary():
    store = SessionStore()
    s1 = store.start_session("t1", "worker")
    s1.record_tokens(input_tokens=100, output_tokens=200)
    store.finish_session("t1")

    s2 = store.start_session("t2", "worker")
    s2.record_tokens(input_tokens=300, output_tokens=400)
    s2.record_error("timeout")
    store.finish_session("t2")

    summary = store.summary()
    assert summary["completed_sessions"] == 2
    assert summary["total_tokens"] == 1000
    assert summary["total_errors"] == 1


def test_store_with_backend_info():
    store = SessionStore()
    s = store.start_session(
        "t1", "worker",
        backend="localai", model="hermes-3b",
        session_type="retry", iteration=2,
    )
    assert s.backend == "localai"
    assert s.model == "hermes-3b"
    assert s.session_type == "retry"
    assert s.iteration == 2