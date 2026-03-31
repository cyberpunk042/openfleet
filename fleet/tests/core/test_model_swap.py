"""Tests for LocalAI model swap management (M-BR05)."""

from fleet.core.model_swap import (
    ModelSwapManager,
    QueuedTask,
    SwapRecord,
)


# ─── SwapRecord ────────────────────────────────────────────────


def test_record_duration():
    r = SwapRecord(
        from_model="hermes-3b", to_model="codellama",
        initiated_at=100.0, completed_at=110.0, success=True,
    )
    assert r.duration_seconds == 10.0


def test_record_duration_zero():
    r = SwapRecord(from_model="hermes-3b", to_model="codellama")
    assert r.duration_seconds == 0.0


def test_record_to_dict():
    r = SwapRecord(
        from_model="hermes-3b", to_model="qwen3-8b",
        initiated_at=100.0, completed_at=180.0,
        success=True, reason="task needs qwen3-8b",
    )
    d = r.to_dict()
    assert d["from_model"] == "hermes-3b"
    assert d["to_model"] == "qwen3-8b"
    assert d["duration_seconds"] == 80.0
    assert d["success"] is True


def test_record_skipped_to_dict():
    r = SwapRecord(
        from_model="hermes-3b", to_model="codellama",
        skipped=True, skip_reason="queued tasks need hermes-3b",
    )
    d = r.to_dict()
    assert d["skipped"] is True
    assert "queued tasks" in d["skip_reason"]


# ─── Swap Decision ─────────────────────────────────────────────


def test_no_swap_needed():
    mgr = ModelSwapManager("hermes-3b")
    decision = mgr.evaluate_swap("hermes-3b")
    assert not decision.needed
    assert not decision.should_swap


def test_swap_needed():
    mgr = ModelSwapManager("hermes-3b")
    decision = mgr.evaluate_swap("codellama")
    assert decision.needed
    assert decision.should_swap


def test_swap_skipped_queue():
    mgr = ModelSwapManager("hermes-3b")
    # Queue 3 tasks needing hermes-3b, only 1 needing codellama
    mgr.enqueue(QueuedTask(task_id="q1", required_model="hermes-3b"))
    mgr.enqueue(QueuedTask(task_id="q2", required_model="hermes-3b"))
    mgr.enqueue(QueuedTask(task_id="q3", required_model="hermes-3b"))
    mgr.enqueue(QueuedTask(task_id="q4", required_model="codellama"))
    decision = mgr.evaluate_swap("codellama")
    assert decision.needed
    assert decision.should_skip
    assert not decision.should_swap


def test_swap_not_skipped_when_queue_favors_requested():
    mgr = ModelSwapManager("hermes-3b")
    mgr.enqueue(QueuedTask(task_id="q1", required_model="codellama"))
    mgr.enqueue(QueuedTask(task_id="q2", required_model="codellama"))
    decision = mgr.evaluate_swap("codellama")
    assert decision.needed
    assert not decision.should_skip
    assert decision.should_swap


# ─── Queue Management ──────────────────────────────────────────


def test_enqueue_dequeue():
    mgr = ModelSwapManager()
    mgr.enqueue(QueuedTask(task_id="t1", required_model="codellama"))
    assert mgr.queue_size == 1
    task = mgr.dequeue("t1")
    assert task is not None
    assert task.task_id == "t1"
    assert mgr.queue_size == 0


def test_dequeue_nonexistent():
    mgr = ModelSwapManager()
    assert mgr.dequeue("nope") is None


def test_clear_queue():
    mgr = ModelSwapManager()
    mgr.enqueue(QueuedTask(task_id="t1", required_model="codellama"))
    mgr.enqueue(QueuedTask(task_id="t2", required_model="hermes-3b"))
    mgr.clear_queue()
    assert mgr.queue_size == 0


def test_queued_models():
    mgr = ModelSwapManager()
    mgr.enqueue(QueuedTask(task_id="t1", required_model="codellama"))
    mgr.enqueue(QueuedTask(task_id="t2", required_model="hermes-3b"))
    mgr.enqueue(QueuedTask(task_id="t3", required_model="codellama"))
    models = mgr.queued_models()
    assert set(models) == {"codellama", "hermes-3b"}


# ─── Swap Recording ───────────────────────────────────────────


def test_record_successful_swap():
    mgr = ModelSwapManager("hermes-3b")
    record = mgr.record_successful_swap(
        "hermes-3b", "codellama", 15.0, reason="code task",
    )
    assert mgr.current_model == "codellama"
    assert record.success
    assert abs(record.duration_seconds - 15.0) < 0.1


def test_record_skipped_swap():
    mgr = ModelSwapManager("hermes-3b")
    record = mgr.record_skipped_swap(
        "hermes-3b", "codellama", "queued tasks need hermes-3b",
    )
    assert mgr.current_model == "hermes-3b"  # Unchanged
    assert record.skipped


def test_record_failed_swap():
    mgr = ModelSwapManager("hermes-3b")
    record = mgr.record_failed_swap(
        "hermes-3b", "codellama", "health check timeout", 30.0,
    )
    assert mgr.current_model == "hermes-3b"  # Unchanged
    assert not record.success
    assert record.error == "health check timeout"


def test_record_max_cap():
    mgr = ModelSwapManager(max_records=3)
    for i in range(5):
        mgr.record_successful_swap("a", "b", 1.0)
    assert len(mgr._records) == 3


# ─── Stamp Metadata ───────────────────────────────────────────


def test_swap_metadata():
    mgr = ModelSwapManager()
    record = SwapRecord(
        from_model="hermes-3b", to_model="codellama",
        initiated_at=100.0, completed_at=115.0,
        success=True,
    )
    meta = mgr.swap_metadata(record)
    assert meta["model_swap"] is True
    assert meta["swap_from"] == "hermes-3b"
    assert meta["swap_to"] == "codellama"
    assert meta["model_swap_time_s"] == 15.0
    assert meta["swap_skipped"] is False


# ─── Metrics ───────────────────────────────────────────────────


def test_total_swaps():
    mgr = ModelSwapManager()
    mgr.record_successful_swap("a", "b", 10.0)
    mgr.record_successful_swap("b", "a", 12.0)
    mgr.record_skipped_swap("a", "c", "skip")
    mgr.record_failed_swap("a", "d", "error")
    assert mgr.total_swaps == 2
    assert mgr.total_skipped == 1
    assert mgr.total_failed == 1


def test_avg_swap_duration():
    mgr = ModelSwapManager()
    mgr.record_successful_swap("a", "b", 10.0)
    mgr.record_successful_swap("b", "a", 20.0)
    assert abs(mgr.avg_swap_duration() - 15.0) < 0.2


def test_avg_swap_duration_empty():
    mgr = ModelSwapManager()
    assert mgr.avg_swap_duration() == 0.0


def test_swap_frequency():
    mgr = ModelSwapManager()
    mgr.record_successful_swap("hermes-3b", "codellama", 10.0)
    mgr.record_successful_swap("codellama", "hermes-3b", 10.0)
    mgr.record_successful_swap("hermes-3b", "codellama", 10.0)
    freq = mgr.swap_frequency()
    assert freq["hermes-3b → codellama"] == 2
    assert freq["codellama → hermes-3b"] == 1


def test_model_load_count():
    mgr = ModelSwapManager()
    mgr.record_successful_swap("hermes-3b", "codellama", 10.0)
    mgr.record_successful_swap("codellama", "hermes-3b", 10.0)
    mgr.record_successful_swap("hermes-3b", "codellama", 10.0)
    counts = mgr.model_load_count()
    assert counts["codellama"] == 2
    assert counts["hermes-3b"] == 1


# ─── Summary & Report ─────────────────────────────────────────


def test_summary():
    mgr = ModelSwapManager("hermes-3b")
    mgr.record_successful_swap("hermes-3b", "codellama", 15.0)
    s = mgr.summary()
    assert s["current_model"] == "codellama"
    assert s["total_swaps"] == 1
    assert s["avg_swap_duration_seconds"] == 15.0


def test_summary_empty():
    mgr = ModelSwapManager()
    s = mgr.summary()
    assert s["total_swaps"] == 0
    assert s["total_skipped"] == 0


def test_format_report():
    mgr = ModelSwapManager("hermes-3b")
    mgr.record_successful_swap("hermes-3b", "codellama", 15.0)
    mgr.record_successful_swap("codellama", "hermes-3b", 10.0)
    mgr.record_skipped_swap("hermes-3b", "codellama", "queue")
    report = mgr.format_report()
    assert "Model Swap Report" in report
    assert "codellama" in report
    assert "hermes-3b" in report
    assert "Swap Frequency" in report


def test_format_report_empty():
    mgr = ModelSwapManager()
    report = mgr.format_report()
    assert "Model Swap Report" in report
    assert "hermes-3b" in report