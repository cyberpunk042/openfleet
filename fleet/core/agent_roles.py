"""Agent roles and PR authority — quality excellence per domain.

Each agent has:
- primary_role: their main function
- main_secondary_role: their quality authority domain (what they can review/reject)
- backup_secondary_role: secondary quality area they can cover

PR authority rules:
- can_reject: agent can reject a PR with reasoning
- can_request_changes: agent can send work back for rework
- can_close_pr: agent can close a PR entirely (abandon)
- can_block_approval: agent can set security_hold (blocks approval processing)
- rejection_creates_fix_task: auto-create fix task for original author

Only fleet-ops and devsecops-expert can close PRs. Only devsecops-expert
can block approval processing (security hold).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PRAuthority:
    """What an agent can do with pull requests during review."""

    can_reject: bool = False
    can_request_changes: bool = True
    can_close_pr: bool = False
    can_block_approval: bool = False
    rejection_creates_fix_task: bool = True
    is_final_authority: bool = False


@dataclass
class AgentRole:
    """Full role definition for an agent."""

    name: str
    primary_role: str
    main_secondary_role: str = ""
    backup_secondary_role: str = ""
    pr_authority: PRAuthority = field(default_factory=PRAuthority)
    review_domains: list[str] = field(default_factory=list)


# Full role definitions for all fleet agents
AGENT_ROLES: dict[str, AgentRole] = {
    "architect": AgentRole(
        name="architect",
        primary_role="system_design",
        main_secondary_role="architecture_reviewer",
        backup_secondary_role="design_quality",
        pr_authority=PRAuthority(
            can_reject=True,
            can_request_changes=True,
            can_close_pr=False,
            rejection_creates_fix_task=True,
        ),
        review_domains=["architecture", "design", "coupling", "abstraction", "pattern"],
    ),
    "software-engineer": AgentRole(
        name="software-engineer",
        primary_role="implementation",
        main_secondary_role="code_reviewer",
        backup_secondary_role="",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
            rejection_creates_fix_task=False,
        ),
        review_domains=["code", "implementation", "python", "refactor"],
    ),
    "qa-engineer": AgentRole(
        name="qa-engineer",
        primary_role="testing",
        main_secondary_role="code_quality_reviewer",
        backup_secondary_role="test_infrastructure",
        pr_authority=PRAuthority(
            can_reject=True,
            can_request_changes=True,
            can_close_pr=False,
            rejection_creates_fix_task=True,
        ),
        review_domains=["test", "quality", "coverage", "regression", "validation"],
    ),
    "devops": AgentRole(
        name="devops",
        primary_role="infrastructure",
        main_secondary_role="infra_reviewer",
        backup_secondary_role="ci_cd",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
        ),
        review_domains=["docker", "ci", "deploy", "infrastructure", "pipeline"],
    ),
    "devsecops-expert": AgentRole(
        name="devsecops-expert",
        primary_role="security",
        main_secondary_role="security_reviewer",
        backup_secondary_role="compliance",
        pr_authority=PRAuthority(
            can_reject=True,
            can_request_changes=True,
            can_close_pr=True,
            can_block_approval=True,
            rejection_creates_fix_task=True,
        ),
        review_domains=["security", "cve", "vulnerability", "secret", "credential", "compliance"],
    ),
    "technical-writer": AgentRole(
        name="technical-writer",
        primary_role="documentation",
        main_secondary_role="doc_reviewer",
        backup_secondary_role="",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
        ),
        review_domains=["documentation", "readme", "api_doc", "changelog"],
    ),
    "ux-designer": AgentRole(
        name="ux-designer",
        primary_role="interface_design",
        main_secondary_role="ux_reviewer",
        backup_secondary_role="accessibility",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
        ),
        review_domains=["ui", "ux", "accessibility", "layout", "user_flow"],
    ),
    "project-manager": AgentRole(
        name="project-manager",
        primary_role="project_management",
        main_secondary_role="sprint_reviewer",
        backup_secondary_role="requirements",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
        ),
        review_domains=["planning", "sprint", "requirements", "priority"],
    ),
    "fleet-ops": AgentRole(
        name="fleet-ops",
        primary_role="governance",
        main_secondary_role="quality_gatekeeper",
        backup_secondary_role="process_compliance",
        pr_authority=PRAuthority(
            can_reject=True,
            can_request_changes=True,
            can_close_pr=True,
            rejection_creates_fix_task=True,
            is_final_authority=True,
        ),
        review_domains=["quality", "governance", "compliance", "standard"],
    ),
    "accountability-generator": AgentRole(
        name="accountability-generator",
        primary_role="accountability_systems",
        main_secondary_role="evidence_reviewer",
        backup_secondary_role="",
        pr_authority=PRAuthority(
            can_reject=False,
            can_request_changes=True,
        ),
        review_domains=["accountability", "evidence", "traceability"],
    ),
}


def get_agent_role(agent_name: str) -> Optional[AgentRole]:
    """Get the full role definition for an agent."""
    return AGENT_ROLES.get(agent_name)


def can_agent_reject(agent_name: str) -> bool:
    """Check if an agent has PR rejection authority."""
    role = AGENT_ROLES.get(agent_name)
    return role.pr_authority.can_reject if role else False


def can_agent_close_pr(agent_name: str) -> bool:
    """Check if an agent can close PRs (abandon work)."""
    role = AGENT_ROLES.get(agent_name)
    return role.pr_authority.can_close_pr if role else False


def can_agent_block_approval(agent_name: str) -> bool:
    """Check if an agent can set security holds on tasks."""
    role = AGENT_ROLES.get(agent_name)
    return role.pr_authority.can_block_approval if role else False


def should_create_fix_task(agent_name: str) -> bool:
    """Check if rejection by this agent should auto-create a fix task."""
    role = AGENT_ROLES.get(agent_name)
    return role.pr_authority.rejection_creates_fix_task if role else False


def get_review_domains(agent_name: str) -> list[str]:
    """Get the review domains an agent is qualified to evaluate."""
    role = AGENT_ROLES.get(agent_name)
    return role.review_domains if role else []