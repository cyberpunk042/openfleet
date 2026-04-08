"""Tests for stage-aware skill recommendations.

Verifies:
  - Config loads and caches correctly
  - Generic all_stages skills returned for all agents
  - Role-specific skills returned for correct roles only
  - Stage-specific skills returned for correct stages only
  - Blocked skills listed for restricted stages
  - Unknown agents/stages handled gracefully
"""

import pytest
from fleet.core.skill_recommendations import get_skill_recommendations, _load_config


class TestSkillRecommendations:

    def test_config_loads(self):
        config = _load_config()
        assert isinstance(config, dict)
        assert "generic" in config
        assert "roles" in config

    def test_returns_dict_structure(self):
        r = get_skill_recommendations("architect", "reasoning")
        assert "always" in r
        assert "stage" in r
        assert "blocked" in r
        assert "stage_name" in r
        assert r["stage_name"] == "reasoning"

    def test_generic_always_skills_present(self):
        """All agents should get generic all_stages skills."""
        r = get_skill_recommendations("architect", "work")
        skill_names = [s["skill"] for s in r["always"]]
        assert "fleet-methodology-guide" in skill_names
        assert "fleet-contribution" in skill_names

    def test_role_always_skills_present(self):
        """PM should get PM-specific all_stages skills."""
        r = get_skill_recommendations("project-manager", "conversation")
        skill_names = [s["skill"] for s in r["always"]]
        assert "fleet-pm-orchestration" in skill_names

    def test_architect_reasoning_has_design(self):
        """Architect at reasoning stage should have design contribution skill."""
        r = get_skill_recommendations("architect", "reasoning")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-design-contribution" in stage_skills

    def test_architect_reasoning_has_adr(self):
        """Architect at reasoning should have ADR creation skill."""
        r = get_skill_recommendations("architect", "reasoning")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-adr-creation" in stage_skills

    def test_engineer_work_has_completion(self):
        """Engineer at work stage should have completion checklist."""
        r = get_skill_recommendations("software-engineer", "work")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-completion-checklist" in stage_skills

    def test_qa_reasoning_has_predefinition(self):
        """QA at reasoning should have test predefinition."""
        r = get_skill_recommendations("qa-engineer", "reasoning")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-qa-predefinition" in stage_skills

    def test_qa_reasoning_has_boundary_analysis(self):
        """QA at reasoning should have boundary value analysis."""
        r = get_skill_recommendations("qa-engineer", "reasoning")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-boundary-value-analysis" in stage_skills

    def test_fleet_ops_work_has_trail_verification(self):
        """Fleet-ops at work should have trail verification."""
        r = get_skill_recommendations("fleet-ops", "work")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-trail-verification" in stage_skills

    def test_devsecops_analysis_has_threat_modeling(self):
        """DevSecOps at analysis should have threat modeling."""
        r = get_skill_recommendations("devsecops-expert", "analysis")
        stage_skills = [s["skill"] for s in r["stage"]]
        assert "fleet-threat-modeling" in stage_skills

    def test_conversation_blocks_commit(self):
        """Conversation stage should block commit-related skills."""
        r = get_skill_recommendations("software-engineer", "conversation")
        assert "fleet-commit" in r["blocked"]

    def test_conversation_blocks_tdd(self):
        """Conversation stage should block TDD skill."""
        r = get_skill_recommendations("software-engineer", "conversation")
        assert "test-driven-development" in r["blocked"]

    def test_work_stage_no_blocked(self):
        """Work stage should have no blocked skills."""
        r = get_skill_recommendations("software-engineer", "work")
        assert r["blocked"] == []

    def test_unknown_agent_returns_generic(self):
        """Unknown agent should still get generic skills."""
        r = get_skill_recommendations("nonexistent-agent", "work")
        skill_names = [s["skill"] for s in r["always"]]
        assert "fleet-methodology-guide" in skill_names
        # No role-specific skills
        assert len(r["always"]) == 2  # only generic all_stages

    def test_unknown_stage_returns_empty(self):
        """Unknown stage should return empty stage recommendations."""
        r = get_skill_recommendations("architect", "unknown-stage")
        assert r["stage"] == []

    def test_plugin_skills_have_plugin_field(self):
        """Plugin-recommended skills should include plugin name."""
        r = get_skill_recommendations("architect", "conversation")
        plugin_skills = [s for s in r["stage"] if "plugin" in s]
        if plugin_skills:
            assert plugin_skills[0]["plugin"] != ""

    def test_skills_have_why(self):
        """Each recommended skill should have a 'why' explanation."""
        r = get_skill_recommendations("architect", "reasoning")
        for s in r["always"] + r["stage"]:
            assert "why" in s, f"Skill {s['skill']} missing 'why'"
            assert s["why"] != "", f"Skill {s['skill']} has empty 'why'"
