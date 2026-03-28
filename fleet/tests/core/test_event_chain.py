"""Tests for event chain building."""

from fleet.core.event_chain import (
    EventSurface,
    build_alert_chain,
    build_sprint_complete_chain,
    build_task_complete_chain,
)


def test_task_complete_chain_has_all_surfaces():
    chain = build_task_complete_chain(
        task_id="t1", agent_name="devops", summary="Added docker config",
        pr_url="https://github.com/test/pr/1", branch="fleet/devops/t1",
        project="dspd",
    )
    assert chain.operation == "task_complete"
    assert len(chain.internal_events) >= 2  # status + approval + memory
    assert len(chain.public_events) >= 1    # push + PR
    assert len(chain.channel_events) >= 1   # IRC
    assert len(chain.notify_events) >= 1    # ntfy
    assert len(chain.meta_events) >= 1      # metrics


def test_task_complete_chain_no_code():
    chain = build_task_complete_chain(
        task_id="t1", agent_name="architect", summary="Designed architecture",
    )
    assert len(chain.public_events) == 0  # No branch/PR


def test_alert_chain_critical():
    chain = build_alert_chain(
        agent_name="devsecops-expert", severity="critical",
        title="CVE found", details="Details", category="security",
    )
    assert len(chain.internal_events) == 1
    assert len(chain.channel_events) == 1
    irc = chain.channel_events[0]
    assert irc.params["channel"] == "#alerts"  # Critical goes to #alerts

    notify = chain.notify_events[0]
    assert notify.params["priority"] == "urgent"


def test_alert_chain_medium():
    chain = build_alert_chain(
        agent_name="qa-engineer", severity="medium",
        title="Test coverage low", details="50% coverage",
    )
    irc = chain.channel_events[0]
    assert irc.params["channel"] == "#fleet"  # Medium goes to #fleet

    notify = chain.notify_events[0]
    assert notify.params["priority"] == "important"


def test_sprint_complete_chain():
    chain = build_sprint_complete_chain(
        plan_id="dspd-s1", total_tasks=8, story_points=24,
    )
    assert chain.operation == "sprint_complete"
    assert len(chain.internal_events) == 1
    assert len(chain.channel_events) == 1
    assert len(chain.notify_events) == 1
    assert "dspd-s1" in chain.channel_events[0].params["message"]


def test_chain_required_vs_optional():
    chain = build_task_complete_chain(
        task_id="t1", agent_name="devops", summary="Test",
    )
    required = [e for e in chain.events if e.required]
    optional = [e for e in chain.events if not e.required]
    assert len(required) >= 2   # Status update + approval are required
    assert len(optional) >= 1   # IRC, ntfy, metrics are optional