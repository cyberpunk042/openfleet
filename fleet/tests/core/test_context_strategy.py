"""Tests for fleet.core.context_strategy — progressive response to context pressure."""

import pytest
from fleet.core.context_strategy import (
    ContextStrategy,
    ContextAction,
    RateLimitAction,
)


@pytest.fixture
def strategy():
    return ContextStrategy()


class TestContextEvaluation:
    def test_normal_below_thresholds(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=50.0, rate_limit_pct=40.0)
        assert ev.context_action == ContextAction.NORMAL
        assert ev.rate_limit_action == RateLimitAction.NORMAL
        assert ev.message == ""
        assert not ev.needs_attention
        assert not ev.should_block_dispatch
        assert not ev.should_compact

    def test_context_aware_at_70(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=72.0)
        assert ev.context_action == ContextAction.AWARE
        assert ev.needs_attention

    def test_context_prepare_at_80(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=83.0)
        assert ev.context_action == ContextAction.PREPARE
        assert "PREPARE" in ev.message
        assert "save working state" in ev.message

    def test_context_extract_at_90(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=92.0)
        assert ev.context_action == ContextAction.EXTRACT
        assert "EXTRACT" in ev.message

    def test_context_compact_at_95(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=96.0)
        assert ev.context_action == ContextAction.COMPACT
        assert ev.should_compact

    def test_rate_limit_inform_at_70(self, strategy):
        ev = strategy.evaluate("engineer", rate_limit_pct=73.0)
        assert ev.rate_limit_action == RateLimitAction.INFORM

    def test_rate_limit_conserve_at_85(self, strategy):
        ev = strategy.evaluate("engineer", rate_limit_pct=87.0)
        assert ev.rate_limit_action == RateLimitAction.CONSERVE
        assert "CONSERVE" in ev.message

    def test_rate_limit_critical_at_90(self, strategy):
        ev = strategy.evaluate("engineer", rate_limit_pct=91.0)
        assert ev.rate_limit_action == RateLimitAction.CRITICAL
        assert ev.should_block_dispatch

    def test_rate_limit_stop_at_95(self, strategy):
        ev = strategy.evaluate("engineer", rate_limit_pct=96.0)
        assert ev.rate_limit_action == RateLimitAction.STOP
        assert ev.should_block_dispatch

    def test_both_pressures(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=85.0, rate_limit_pct=88.0)
        assert ev.context_action == ContextAction.PREPARE
        assert ev.rate_limit_action == RateLimitAction.CONSERVE
        assert "PREPARE" in ev.message
        assert "CONSERVE" in ev.message

    def test_zero_pct_means_no_data(self, strategy):
        ev = strategy.evaluate("engineer", context_pct=0.0, rate_limit_pct=0.0)
        assert ev.context_action == ContextAction.NORMAL
        assert ev.rate_limit_action == RateLimitAction.NORMAL


class TestDispatchDecision:
    def test_dispatch_allowed_below_critical(self, strategy):
        assert strategy.should_dispatch(80.0) is True

    def test_dispatch_blocked_at_critical(self, strategy):
        assert strategy.should_dispatch(91.0) is False

    def test_dispatch_blocked_at_stop(self, strategy):
        assert strategy.should_dispatch(96.0) is False


class TestCompactionStagger:
    def test_compact_when_above_threshold(self, strategy):
        assert strategy.should_compact_agent("engineer", 96.0) is True

    def test_no_compact_below_threshold(self, strategy):
        assert strategy.should_compact_agent("engineer", 80.0) is False

    def test_stagger_prevents_simultaneous(self, strategy):
        # Record compaction for one agent
        strategy.record_compaction("architect")
        # Second agent should be staggered
        assert strategy.should_compact_agent("engineer", 96.0) is False

    def test_stagger_allows_after_cooldown(self, strategy):
        from datetime import datetime, timedelta
        # Record compaction in the past (beyond stagger window)
        strategy._last_compact["architect"] = datetime.now() - timedelta(seconds=200)
        assert strategy.should_compact_agent("engineer", 96.0) is True
