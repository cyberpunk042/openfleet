"""Tests for the fleet event system — CloudEvents store and agent feeds."""

import json
import os
import tempfile

import pytest

from fleet.core.events import (
    EVENT_TYPES,
    EventStore,
    FleetEvent,
    create_event,
)


@pytest.fixture
def store():
    """Create a temporary event store."""
    tmpdir = tempfile.mkdtemp()
    return EventStore(os.path.join(tmpdir, "test-events.jsonl"))


class TestFleetEvent:
    def test_create_with_defaults(self):
        event = FleetEvent(type="fleet.test", source="test")
        assert event.id  # auto-generated UUID
        assert event.time  # auto-generated timestamp
        assert event.recipient == "all"
        assert event.priority == "info"

    def test_create_event_factory(self):
        event = create_event(
            "fleet.task.completed",
            source="test",
            subject="task-123",
            recipient="fleet-ops",
            priority="important",
            mentions=["fleet-ops"],
            tags=["review"],
            surfaces=["internal", "channel"],
            summary="test summary",
        )
        assert event.type == "fleet.task.completed"
        assert event.recipient == "fleet-ops"
        assert event.priority == "important"
        assert event.mentions == ["fleet-ops"]
        assert event.tags == ["review"]
        assert event.surfaces == ["internal", "channel"]
        assert event.data["summary"] == "test summary"

    def test_event_types_defined(self):
        assert len(EVENT_TYPES) > 20
        assert "fleet.task.completed" in EVENT_TYPES
        assert "fleet.plane.issue_created" in EVENT_TYPES
        assert "fleet.chat.mention" in EVENT_TYPES
        assert "fleet.alert.posted" in EVENT_TYPES
        assert "fleet.system.config_changed" in EVENT_TYPES


class TestEventStore:
    def test_append_and_query(self, store):
        event = create_event("fleet.test", source="test", recipient="all")
        store.append(event)
        results = store.query()
        assert len(results) == 1
        assert results[0].type == "fleet.test"

    def test_query_by_agent(self, store):
        e1 = create_event("fleet.test.1", source="test", recipient="agent-a")
        e2 = create_event("fleet.test.2", source="test", recipient="agent-b")
        e3 = create_event("fleet.test.3", source="test", recipient="all")
        store.append(e1)
        store.append(e2)
        store.append(e3)

        results_a = store.query(agent_name="agent-a")
        assert len(results_a) == 2  # agent-a + all

        results_b = store.query(agent_name="agent-b")
        assert len(results_b) == 2  # agent-b + all

    def test_query_by_mentions(self, store):
        e1 = create_event("fleet.chat.mention", source="test",
                          recipient="all", mentions=["architect"])
        e2 = create_event("fleet.chat.message", source="test",
                          recipient="all")
        store.append(e1)
        store.append(e2)

        results = store.query(agent_name="architect")
        assert len(results) == 2  # both (all recipient)

    def test_pm_gets_unassigned(self, store):
        e1 = create_event("fleet.task.created", source="test",
                          recipient="unassigned")
        store.append(e1)

        pm_results = store.query(agent_name="project-manager")
        assert len(pm_results) == 1  # PM sees unassigned

        other_results = store.query(agent_name="software-engineer")
        assert len(other_results) == 0  # Others don't

    def test_fleet_ops_gets_lead(self, store):
        e1 = create_event("fleet.escalation", source="test",
                          recipient="lead")
        store.append(e1)

        ops_results = store.query(agent_name="fleet-ops")
        assert len(ops_results) == 1

        other_results = store.query(agent_name="architect")
        assert len(other_results) == 0

    def test_seen_unseen_tracking(self, store):
        e1 = create_event("fleet.test.1", source="test", recipient="all")
        e2 = create_event("fleet.test.2", source="test", recipient="all")
        store.append(e1)
        store.append(e2)

        # Both unseen
        unseen = store.query(agent_name="agent-a", unseen_only=True)
        assert len(unseen) == 2

        # Mark one seen
        store.mark_seen("agent-a", [e1.id])

        unseen_after = store.query(agent_name="agent-a", unseen_only=True)
        assert len(unseen_after) == 1
        assert unseen_after[0].id == e2.id

    def test_seen_persists(self, store):
        e1 = create_event("fleet.test", source="test", recipient="all")
        store.append(e1)
        store.mark_seen("agent-a", [e1.id])

        # Recreate store from same path
        store2 = EventStore(store._path)
        unseen = store2.query(agent_name="agent-a", unseen_only=True)
        assert len(unseen) == 0

    def test_query_by_type(self, store):
        e1 = create_event("fleet.task.completed", source="test")
        e2 = create_event("fleet.chat.message", source="test")
        store.append(e1)
        store.append(e2)

        results = store.query(event_types=["fleet.task.completed"])
        assert len(results) == 1
        assert results[0].type == "fleet.task.completed"

    def test_query_limit(self, store):
        for i in range(20):
            store.append(create_event(f"fleet.test.{i}", source="test"))

        results = store.query(limit=5)
        assert len(results) == 5

    def test_count_unseen(self, store):
        for i in range(5):
            store.append(create_event(f"fleet.test.{i}", source="test", recipient="all"))

        assert store.count_unseen("agent-a") == 5
        store.mark_seen("agent-a", [store.query()[0].id])
        assert store.count_unseen("agent-a") == 4

    def test_newest_first(self, store):
        e1 = create_event("fleet.test.1", source="test")
        e1.time = "2026-03-29T10:00:00Z"
        e2 = create_event("fleet.test.2", source="test")
        e2.time = "2026-03-29T11:00:00Z"
        store.append(e1)
        store.append(e2)

        results = store.query()
        assert results[0].type == "fleet.test.2"  # newer first

    def test_empty_store(self, store):
        results = store.query()
        assert results == []
        assert store.count_unseen("anyone") == 0