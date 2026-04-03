"""Tests for the navigator module — the autocomplete web core."""

import pytest
from pathlib import Path

from fleet.core.navigator import Navigator, NavigatorContext, InjectionProfile


@pytest.fixture
def navigator():
    """Create a navigator instance."""
    nav = Navigator()
    nav.load()
    return nav


class TestNavigatorLoad:
    """Test that the navigator loads metadata files."""

    def test_loads_without_error(self):
        nav = Navigator()
        nav.load()
        assert nav._loaded is True

    def test_loads_intents(self, navigator):
        intents = navigator._intent_map.get("intents", {})
        assert len(intents) > 0, "Should have loaded intents from intent-map.yaml"

    def test_loads_profiles(self, navigator):
        assert "opus-1m" in navigator._profiles
        assert "sonnet-200k" in navigator._profiles
        assert "localai-8k" in navigator._profiles
        assert "heartbeat" in navigator._profiles

    def test_profile_has_levels(self, navigator):
        opus = navigator._profiles["opus-1m"]
        assert opus.context_budget > 0
        assert len(opus.levels) > 0


class TestProfileSelection:
    """Test model → profile mapping."""

    def test_opus_selects_opus_1m(self, navigator):
        profile = navigator._select_profile("opus-4-6")
        assert profile.name == "opus-1m"

    def test_sonnet_selects_sonnet_200k(self, navigator):
        profile = navigator._select_profile("sonnet-4-6")
        assert profile.name == "sonnet-200k"

    def test_hermes_selects_localai_8k(self, navigator):
        profile = navigator._select_profile("hermes-3b")
        assert profile.name == "localai-8k"

    def test_unknown_defaults_to_sonnet(self, navigator):
        profile = navigator._select_profile("unknown-model")
        assert profile.name == "sonnet-200k"


class TestIntentLookup:
    """Test role+stage → intent mapping."""

    def test_architect_reasoning_found(self, navigator):
        intent = navigator._find_intent("architect", "reasoning")
        assert intent is not None
        assert intent.name == "architect-reasoning"

    def test_engineer_work_found(self, navigator):
        intent = navigator._find_intent("software-engineer", "work")
        assert intent is not None
        assert intent.name == "engineer-work"

    def test_pm_heartbeat_found(self, navigator):
        intent = navigator._find_intent("project-manager", "heartbeat")
        assert intent is not None
        assert intent.name == "pm-heartbeat"

    def test_fleet_ops_review_found(self, navigator):
        intent = navigator._find_intent("fleet-ops", "review")
        assert intent is not None
        assert "fleet-ops-review" in intent.name

    def test_unknown_stage_returns_none(self, navigator):
        intent = navigator._find_intent("architect", "nonexistent-stage")
        assert intent is None


class TestRoleShortMapping:
    """Test role name → intent-map key mapping."""

    def test_mappings(self, navigator):
        assert navigator._role_short("software-engineer") == "engineer"
        assert navigator._role_short("project-manager") == "pm"
        assert navigator._role_short("fleet-ops") == "fleet-ops"
        assert navigator._role_short("devsecops-expert") == "devsecops"
        assert navigator._role_short("technical-writer") == "writer"
        assert navigator._role_short("accountability-generator") == "accountability"


class TestAssemble:
    """Test full context assembly."""

    def test_assemble_returns_context(self, navigator):
        ctx = navigator.assemble(role="architect", stage="reasoning", model="opus-4-6")
        assert isinstance(ctx, NavigatorContext)
        assert ctx.role == "architect"
        assert ctx.stage == "reasoning"

    def test_assemble_has_sections(self, navigator):
        ctx = navigator.assemble(role="architect", stage="reasoning", model="opus-4-6")
        # Should have at least some content assembled
        rendered = ctx.render()
        assert isinstance(rendered, str)

    def test_heartbeat_minimal_content(self, navigator):
        ctx = navigator.assemble(role="architect", stage="heartbeat", model="hermes-3b")
        # Heartbeat with localai should have minimal/no content
        rendered = ctx.render()
        # May be empty since heartbeat profile has all levels = none
        assert isinstance(rendered, str)

    def test_opus_has_more_than_localai(self, navigator):
        opus_ctx = navigator.assemble(role="software-engineer", stage="work", model="opus-4-6")
        local_ctx = navigator.assemble(role="software-engineer", stage="work", model="hermes-3b")
        opus_len = len(opus_ctx.render())
        local_len = len(local_ctx.render())
        # Opus should have more content due to fuller profile
        assert opus_len >= local_len

    def test_graph_query_failure_graceful(self, navigator):
        """Navigator should handle LightRAG being down gracefully."""
        # LightRAG is not running in test — the navigator should handle this
        ctx = navigator.assemble(
            role="architect",
            stage="reasoning",
            model="opus-4-6",
            task_context="implement auth middleware",
        )
        # Should not raise — graceful degradation
        assert isinstance(ctx, NavigatorContext)


class TestNavigatorContext:
    """Test the NavigatorContext dataclass."""

    def test_render_empty(self):
        ctx = NavigatorContext(role="test", stage="test", model="test")
        assert ctx.render() == ""

    def test_render_sections(self):
        ctx = NavigatorContext(role="test", stage="test", model="test")
        ctx.sections = ["Section 1", "Section 2"]
        rendered = ctx.render()
        assert "Section 1" in rendered
        assert "Section 2" in rendered

    def test_render_skips_empty_sections(self):
        ctx = NavigatorContext(role="test", stage="test", model="test")
        ctx.sections = ["Content", "", "More content"]
        rendered = ctx.render()
        assert rendered == "Content\n\nMore content"
