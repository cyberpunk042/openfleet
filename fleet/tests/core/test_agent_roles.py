"""Tests for agent roles and PR authority."""

from fleet.core.agent_roles import (
    can_agent_block_approval,
    can_agent_close_pr,
    can_agent_reject,
    get_agent_role,
    get_review_domains,
    should_create_fix_task,
)


def test_fleet_ops_is_final_authority():
    role = get_agent_role("fleet-ops")
    assert role is not None
    assert role.pr_authority.is_final_authority
    assert role.pr_authority.can_reject
    assert role.pr_authority.can_close_pr


def test_qa_can_reject():
    assert can_agent_reject("qa-engineer")
    assert should_create_fix_task("qa-engineer")


def test_architect_can_reject():
    assert can_agent_reject("architect")
    assert should_create_fix_task("architect")


def test_sw_engineer_cannot_reject():
    assert not can_agent_reject("software-engineer")


def test_security_can_block_and_close():
    assert can_agent_reject("devsecops-expert")
    assert can_agent_close_pr("devsecops-expert")
    assert can_agent_block_approval("devsecops-expert")


def test_only_security_and_ops_can_close():
    assert can_agent_close_pr("devsecops-expert")
    assert can_agent_close_pr("fleet-ops")
    assert not can_agent_close_pr("qa-engineer")
    assert not can_agent_close_pr("architect")
    assert not can_agent_close_pr("software-engineer")


def test_only_security_can_block_approval():
    assert can_agent_block_approval("devsecops-expert")
    assert not can_agent_block_approval("fleet-ops")
    assert not can_agent_block_approval("qa-engineer")


def test_review_domains():
    domains = get_review_domains("devsecops-expert")
    assert "security" in domains
    assert "cve" in domains

    domains = get_review_domains("qa-engineer")
    assert "test" in domains
    assert "coverage" in domains


def test_unknown_agent():
    assert get_agent_role("nonexistent") is None
    assert not can_agent_reject("nonexistent")