"""Tests for fleet.core.tier_renderer — TierRenderer and tier profile loading."""

import pytest
from fleet.core.tier_renderer import TierRenderer, load_tier_rules
from fleet.core.models import Task, TaskCustomFields, TaskStatus


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_task(**kwargs) -> Task:
    defaults = {
        "id": "task-abcdef12",
        "board_id": "board-1",
        "title": "Design the new header component",
        "status": TaskStatus.IN_PROGRESS,
        "description": "Add FleetControlBar to DashboardShell",
        "priority": "high",
        "custom_fields": TaskCustomFields(
            task_readiness=80,
            task_stage="reasoning",
            requirement_verbatim="Add three Select dropdowns to the DashboardShell header bar",
            project="fleet",
        ),
    }
    defaults.update(kwargs)
    return Task(**defaults)


# ─── TestTierProfileLoading ───────────────────────────────────────────────────


class TestTierProfileLoading:
    def test_load_expert_profile(self):
        rules = load_tier_rules("expert")
        assert rules["task_detail"] == "full"

    def test_load_capable_profile(self):
        rules = load_tier_rules("capable")
        assert rules["task_detail"] == "core_fields"

    def test_load_lightweight_profile(self):
        rules = load_tier_rules("lightweight")
        assert rules["chain_awareness"] == "omit"

    def test_flagship_extends_capable(self):
        """flagship_local extends capable — overrides applied on top of base."""
        capable = load_tier_rules("capable")
        flagship = load_tier_rules("flagship_local")
        # Inherits base capable values
        assert flagship["task_detail"] == capable["task_detail"]
        assert flagship["messages"] == capable["messages"]
        # Overrides
        assert flagship["contributions"] == "summary"
        assert flagship["role_data"] == "counts_plus_top5"
        assert flagship["events_limit"] == 8
        # Not equal to capable's overridden values
        assert flagship["events_limit"] != capable["events_limit"]

    def test_unknown_tier_defaults_to_expert(self):
        """Unknown tier name falls back to expert rules."""
        expert = load_tier_rules("expert")
        unknown = load_tier_rules("totally_unknown_tier_xyz")
        assert unknown["task_detail"] == expert["task_detail"]
        assert unknown["role_data"] == expert["role_data"]

    def test_description_stripped(self):
        """description key must NOT appear in returned rules."""
        for tier in ("expert", "capable", "flagship_local", "lightweight"):
            rules = load_tier_rules(tier)
            assert "description" not in rules


# ─── TestFormatRoleData ───────────────────────────────────────────────────────


class TestFormatRoleData:
    def test_fleet_ops_no_raw_dicts(self):
        """Output must NOT contain raw dict repr — must have formatted lines."""
        renderer = TierRenderer("expert")
        data = {
            "pending_approvals": 2,
            "approval_details": [
                {"id": "apr-001", "task_id": "task-abc", "status": "pending"},
                {"id": "apr-002", "task_id": "task-def", "status": "pending"},
            ],
            "review_queue": [
                {"id": "task-111", "title": "Review header PR", "agent": "architect"},
            ],
            "offline_agents": ["devops", "qa-engineer"],
        }
        result = renderer.format_role_data("fleet-ops", data)
        # Must NOT contain raw dict repr
        assert "{'id'" not in result
        assert "{'task_id'" not in result
        # Must have formatted lines
        assert "## ROLE DATA" in result
        assert "apr-001" in result
        assert "task-abc" in result
        assert "pending" in result
        assert "Review header PR" in result
        assert "architect" in result
        assert "devops" in result

    def test_pm_no_raw_dicts(self):
        """PM role data: formatted task list, priorities visible."""
        renderer = TierRenderer("expert")
        data = {
            "unassigned_tasks": 3,
            "unassigned_details": [
                {"id": "task-aaa", "title": "Build login page", "priority": "high"},
                {"id": "task-bbb", "title": "Fix auth bug", "priority": "critical"},
            ],
            "blocked_tasks": 1,
            "progress": "5/15 done",
        }
        result = renderer.format_role_data("project-manager", data)
        assert "{'id'" not in result
        assert "## ROLE DATA" in result
        assert "task-aaa" in result
        assert "Build login page" in result
        assert "high" in result
        assert "critical" in result
        assert "5/15 done" in result

    def test_worker_contributions_formatted(self):
        """Worker contributions_received shown as 'type (from, status)' not raw dict."""
        renderer = TierRenderer("expert")
        data = {
            "my_tasks_count": 2,
            "contributions_received": [
                {"type": "qa_test_definition", "from": "qa-engineer", "status": "ready"},
                {"type": "design_input", "from": "architect", "status": "pending"},
            ],
        }
        result = renderer.format_role_data("software-engineer", data)
        assert "{'type'" not in result
        assert "## ROLE DATA" in result
        # Must show type (from, status) format
        assert "qa_test_definition (qa-engineer, ready)" in result
        assert "design_input (architect, pending)" in result

    def test_worker_contributions_received_dict_shape(self):
        """Worker contributions_received as dict keyed by task ID (real provider shape)."""
        renderer = TierRenderer("expert")
        data = {
            "my_tasks_count": 1,
            "contributions_received": {
                "task-a1b": [
                    {"type": "design_input", "from": "architect", "status": "done"},
                    {"type": "qa_test_definition", "from": "qa-engineer", "status": "done"},
                ]
            },
        }
        result = renderer.format_role_data("software-engineer", data)
        assert "{'type'" not in result
        assert "task-a1b" in result
        assert "design_input" in result
        assert "architect" in result
        assert "qa_test_definition" in result
        assert "qa-engineer" in result

    def test_lightweight_counts_only(self):
        """Lightweight tier: counts shown, no item detail lines."""
        renderer = TierRenderer("lightweight")
        data = {
            "pending_approvals": 4,
            "approval_details": [
                {"id": "apr-001", "task_id": "task-abc", "status": "pending"},
                {"id": "apr-002", "task_id": "task-def", "status": "pending"},
            ],
            "review_queue": [
                {"id": "task-111", "title": "Review header PR", "agent": "architect"},
            ],
        }
        result = renderer.format_role_data("fleet-ops", data)
        assert "## ROLE DATA" in result
        assert "4" in result  # count present
        # No item detail lines (no individual approval IDs)
        assert "apr-001" not in result
        assert "apr-002" not in result
        assert "Review header PR" not in result

    def test_empty_data_returns_empty(self):
        """Empty data dict returns empty string."""
        renderer = TierRenderer("expert")
        result = renderer.format_role_data("fleet-ops", {})
        assert result == ""


# ─── TestFormatRejectionContext ───────────────────────────────────────────────


class TestFormatRejectionContext:
    def test_iteration_1_empty(self):
        """Iteration 1 (first attempt) returns empty string."""
        renderer = TierRenderer("expert")
        result = renderer.format_rejection_context(1, "some feedback")
        assert result == ""

    def test_iteration_2_shows_feedback(self):
        """Iteration 2: shows iteration number, feedback, eng_fix_task_response."""
        renderer = TierRenderer("expert")
        feedback = "The implementation misses edge case handling for empty inputs."
        result = renderer.format_rejection_context(2, feedback)
        assert "iteration 2" in result
        assert "eng_fix_task_response" in result
        assert feedback in result
        assert "ROOT CAUSE" in result

    def test_iteration_3_shows_warning(self):
        """Iteration 3+: shows WARNING about escalation."""
        renderer = TierRenderer("expert")
        result = renderer.format_rejection_context(3, "Still failing tests.")
        assert "WARNING" in result
        assert "escalated" in result.lower() or "escalation" in result.lower()
        assert "3" in result


# ─── TestFormatActionDirective ────────────────────────────────────────────────


class TestFormatActionDirective:
    def test_work_progress_0(self):
        """Progress 0 in work stage mentions fleet_task_accept."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("work", 0, 1)
        assert "fleet_task_accept" in result

    def test_work_progress_70(self):
        """Progress 70 in work stage mentions test/testing."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("work", 70, 1)
        assert "test" in result.lower()

    def test_work_progress_90(self):
        """Progress 90 in work stage mentions fleet_task_complete."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("work", 90, 1)
        assert "fleet_task_complete" in result

    def test_work_rework(self):
        """Iteration >= 2 in work stage mentions REWORK and eng_fix_task_response."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("work", 50, 2)
        assert "REWORK" in result
        assert "eng_fix_task_response" in result

    def test_conversation_stage(self):
        """Conversation stage directive mentions clarifying questions."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("conversation", 0, 1)
        assert "clarif" in result.lower() or "question" in result.lower()

    def test_reasoning_stage(self):
        """Reasoning stage directive mentions plan."""
        renderer = TierRenderer("expert")
        result = renderer.format_action_directive("reasoning", 0, 1)
        assert "plan" in result.lower()

    def test_one_line_depth_returns_single_sentence(self):
        """one_line depth returns just the first sentence (no backtick tool names)."""
        renderer = TierRenderer("lightweight")
        result = renderer.format_action_directive("work", 0, 1)
        # Should be short — one sentence only
        assert len(result) < 100
        # Should still indicate starting work
        assert "work" in result.lower() or "start" in result.lower()


# ─── TestFormatContributionTaskContext ────────────────────────────────────────


class TestFormatContributionTaskContext:
    def test_no_contribution_type_empty(self):
        """No contribution_type → returns empty string."""
        renderer = TierRenderer("expert")
        result = renderer.format_contribution_task_context("", "task-abcdef12")
        assert result == ""

    def test_contribution_with_target(self):
        """With target task: shows title, verbatim, fleet_contribute."""
        renderer = TierRenderer("expert")
        target = _make_task(
            id="task-target1",
            title="Implement dashboard header",
            custom_fields=TaskCustomFields(
                requirement_verbatim="Add three Select dropdowns to the DashboardShell header bar",
                delivery_phase="mvp",
                task_stage="work",
            ),
        )
        result = renderer.format_contribution_task_context(
            "qa_test_definition", "task-target1", target
        )
        assert "## CONTRIBUTION TASK" in result
        assert "qa_test_definition" in result
        assert "Implement dashboard header" in result
        assert "Select dropdowns" in result
        assert "mvp" in result
        assert "fleet_contribute" in result

    def test_contribution_without_target_task(self):
        """Without target Task object: shows type, short target ID, fleet_contribute."""
        renderer = TierRenderer("expert")
        result = renderer.format_contribution_task_context(
            "design_input", "task-12345678", None
        )
        assert "## CONTRIBUTION TASK" in result
        assert "design_input" in result
        assert "task-123" in result  # short ID (first 8 chars)
        assert "fleet_contribute" in result


# ─── TestFormatStageProtocol ──────────────────────────────────────────────────


class TestFormatStageProtocol:
    def test_reasoning_engineer_says_implementation(self):
        """Reasoning stage for software-engineer mentions 'implementation plan'."""
        renderer = TierRenderer("expert")
        result = renderer.format_stage_protocol("reasoning", "software-engineer")
        assert "implementation plan" in result.lower()

    def test_reasoning_architect_says_design_input(self):
        """Reasoning stage for architect mentions design_input."""
        renderer = TierRenderer("expert")
        result = renderer.format_stage_protocol("reasoning", "architect")
        assert "design_input" in result

    def test_reasoning_qa_says_test_criteria(self):
        """Reasoning stage for qa-engineer mentions qa_test_definition or test criteria."""
        renderer = TierRenderer("expert")
        result = renderer.format_stage_protocol("reasoning", "qa-engineer")
        assert "qa_test_definition" in result or "test criteria" in result.lower()

    def test_work_stage_not_role_specific(self):
        """Work stage protocol is the same for all roles and contains 'WORK'."""
        renderer = TierRenderer("expert")
        result_eng = renderer.format_stage_protocol("work", "software-engineer")
        result_arch = renderer.format_stage_protocol("work", "architect")
        assert result_eng == result_arch
        assert "WORK" in result_eng

    def test_work_rework_adapts_protocol(self):
        """BUG-03: Work protocol adapts for rework — no 'Execute the confirmed plan'."""
        renderer = TierRenderer("expert")
        result = renderer.format_stage_protocol("work", "software-engineer", iteration=2)
        assert "ROOT CAUSE" in result
        assert "rejection feedback" in result.lower()
        # Should NOT say "Execute the confirmed plan"
        assert "Execute the confirmed plan" not in result
