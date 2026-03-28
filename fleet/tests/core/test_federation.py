"""Tests for fleet federation — multi-machine identity."""

import os
import tempfile

from fleet.core.federation import (
    FleetIdentity,
    generate_fleet_identity,
    get_namespaced_agent_name,
    load_fleet_identity,
)


def test_generate_creates_identity():
    with tempfile.TemporaryDirectory() as tmpdir:
        identity = generate_fleet_identity(tmpdir, fleet_name="Test Fleet", agent_prefix="test")
        assert identity.fleet_id.startswith("fleet-")
        assert identity.fleet_name == "Test Fleet"
        assert identity.agent_prefix == "test"
        assert identity.machine_id  # hostname should be set
        assert identity.instance_uuid  # UUID generated


def test_generate_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        id1 = generate_fleet_identity(tmpdir, fleet_name="First")
        id2 = generate_fleet_identity(tmpdir, fleet_name="Second")
        assert id1.fleet_id == id2.fleet_id  # Same identity returned
        assert id1.fleet_name == "First"  # Original name preserved


def test_load_identity():
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_fleet_identity(tmpdir, fleet_name="Loaded", agent_prefix="ld")
        loaded = load_fleet_identity(tmpdir)
        assert loaded is not None
        assert loaded.fleet_name == "Loaded"
        assert loaded.agent_prefix == "ld"


def test_load_missing_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert load_fleet_identity(tmpdir) is None


def test_namespaced_agent_name():
    identity = FleetIdentity(
        fleet_id="fleet-abc", fleet_name="Alpha",
        machine_id="host", instance_uuid="uuid",
        agent_prefix="alpha", created_at="",
    )
    assert get_namespaced_agent_name("architect", identity) == "alpha-architect"
    assert get_namespaced_agent_name("devops", identity) == "alpha-devops"


def test_namespaced_no_prefix():
    identity = FleetIdentity(
        fleet_id="fleet-abc", fleet_name="Solo",
        machine_id="host", instance_uuid="uuid",
        agent_prefix="", created_at="",
    )
    assert get_namespaced_agent_name("architect", identity) == "architect"


def test_auto_generate_names():
    with tempfile.TemporaryDirectory() as tmpdir:
        identity = generate_fleet_identity(tmpdir)
        assert identity.fleet_name  # Auto-generated from hostname
        assert identity.agent_prefix  # Auto-generated from UUID
        assert len(identity.agent_prefix) == 4