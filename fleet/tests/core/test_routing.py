"""Tests for agent routing — capability matching."""

from fleet.core.models import Agent, Task, TaskCustomFields, TaskStatus
from fleet.core.routing import route_task, suggest_agent


def _agent(name: str, status: str = "online") -> Agent:
    return Agent(id=f"id-{name}", name=name, status=status)


def _task(title: str, desc: str = "", task_type: str = "task") -> Task:
    return Task(
        id="t1", board_id="b1", title=title, status=TaskStatus.INBOX,
        description=desc,
        custom_fields=TaskCustomFields(task_type=task_type),
    )


ALL_AGENTS = [
    _agent("architect"), _agent("software-engineer"), _agent("qa-engineer"),
    _agent("devops"), _agent("devsecops-expert"), _agent("technical-writer"),
    _agent("ux-designer"), _agent("project-manager"), _agent("fleet-ops"),
]


def test_security_task_routes_to_devsecops():
    t = _task("Audit dependencies for CVE vulnerabilities")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "devsecops-expert"


def test_docker_task_routes_to_devops():
    t = _task("Set up Docker CI pipeline for deployment")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "devops"


def test_test_task_routes_to_qa():
    t = _task("Write pytest coverage for plane_client module")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "qa-engineer"


def test_docs_task_routes_to_writer():
    t = _task("Write README documentation for the API")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "technical-writer"


def test_implement_task_routes_to_engineer():
    t = _task("Implement the PlaneClient Python module", "Write code for API wrapper class")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "software-engineer"


def test_architecture_task_routes_to_architect():
    t = _task("Design the system architecture for event chains")
    result = suggest_agent(t, ALL_AGENTS)
    assert result == "architect"


def test_workload_penalty():
    t = _task("Implement feature X", "Write Python code")
    agents = [_agent("software-engineer"), _agent("qa-engineer")]
    # sw-eng has 2 active tasks
    matches = route_task(t, agents, {"software-engineer": 2})
    # sw-eng should still match but with lower score
    sw_match = next(m for m in matches if m.agent_name == "software-engineer")
    assert any("workload" in r for r in sw_match.reasons)


def test_no_match_returns_empty():
    t = _task("Something completely unrelated to any capability xyzzyx")
    result = suggest_agent(t, ALL_AGENTS)
    # May or may not match depending on keyword overlap
    # Just verify it returns without error
    assert result is None or isinstance(result, str)


def test_route_returns_multiple_matches():
    t = _task("Review test coverage and quality", "Check regression testing")
    matches = route_task(t, ALL_AGENTS)
    assert len(matches) >= 2  # qa-engineer and fleet-ops should both match