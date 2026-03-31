"""Tests for fleet.core.phases — PO-defined delivery phase system."""

import pytest
from fleet.core.phases import (
    PhaseDefinition,
    PhaseProgression,
    load_progressions,
    get_phase_definition,
    get_phase_standards,
    get_required_contributions,
    get_next_phase,
    is_phase_gate,
    reload_phases,
)


class TestPhaseDefinition:
    def test_basic_phase(self):
        p = PhaseDefinition(name="poc", description="Proof of concept")
        assert p.name == "poc"
        assert p.gate is True  # default: gate required

    def test_phase_with_standards(self):
        p = PhaseDefinition(
            name="mvp",
            standards={"tests": "main flows", "docs": "setup guide"},
            required_contributions=["architect", "qa-engineer"],
        )
        assert p.standards["tests"] == "main flows"
        assert len(p.required_contributions) == 2

    def test_phase_no_gate(self):
        p = PhaseDefinition(name="idea", gate=False)
        assert p.gate is False


class TestPhaseProgression:
    def setup_method(self):
        self.prog = PhaseProgression(
            name="standard",
            phases=[
                PhaseDefinition(name="idea", gate=False),
                PhaseDefinition(name="conceptual", gate=True),
                PhaseDefinition(name="poc", gate=True),
                PhaseDefinition(name="mvp", gate=True),
                PhaseDefinition(name="production", gate=True),
            ],
        )

    def test_phase_names(self):
        assert self.prog.phase_names == ["idea", "conceptual", "poc", "mvp", "production"]

    def test_get_phase(self):
        p = self.prog.get_phase("poc")
        assert p is not None
        assert p.name == "poc"

    def test_get_phase_not_found(self):
        assert self.prog.get_phase("nonexistent") is None

    def test_get_next_phase(self):
        nxt = self.prog.get_next_phase("poc")
        assert nxt is not None
        assert nxt.name == "mvp"

    def test_get_next_phase_last(self):
        assert self.prog.get_next_phase("production") is None

    def test_get_next_phase_unknown(self):
        nxt = self.prog.get_next_phase("unknown")
        assert nxt is not None
        assert nxt.name == "idea"  # returns first phase

    def test_get_previous_phase(self):
        prev = self.prog.get_previous_phase("mvp")
        assert prev is not None
        assert prev.name == "poc"

    def test_get_previous_phase_first(self):
        assert self.prog.get_previous_phase("idea") is None


class TestConfigLoading:
    def setup_method(self):
        reload_phases()

    def test_load_progressions(self):
        progs = load_progressions()
        assert "standard" in progs
        assert "release" in progs

    def test_standard_progression_has_phases(self):
        progs = load_progressions()
        standard = progs["standard"]
        assert len(standard.phases) >= 6
        assert standard.phases[0].name == "idea"
        assert standard.phases[-1].name == "production"

    def test_release_progression(self):
        progs = load_progressions()
        release = progs["release"]
        assert release.phase_names == ["alpha", "beta", "rc", "release"]

    def test_idea_has_no_gate(self):
        progs = load_progressions()
        idea = progs["standard"].get_phase("idea")
        assert idea is not None
        assert idea.gate is False

    def test_production_has_gate(self):
        progs = load_progressions()
        prod = progs["standard"].get_phase("production")
        assert prod is not None
        assert prod.gate is True

    def test_mvp_requires_contributions(self):
        progs = load_progressions()
        mvp = progs["standard"].get_phase("mvp")
        assert "architect" in mvp.required_contributions
        assert "qa-engineer" in mvp.required_contributions
        assert "devsecops-expert" in mvp.required_contributions


class TestPublicAPI:
    def setup_method(self):
        reload_phases()

    def test_get_phase_definition(self):
        p = get_phase_definition("poc")
        assert p is not None
        assert p.name == "poc"

    def test_get_phase_definition_with_progression(self):
        p = get_phase_definition("alpha", "release")
        assert p is not None
        assert p.name == "alpha"

    def test_get_phase_standards(self):
        standards = get_phase_standards("mvp")
        assert "tests" in standards
        assert "docs" in standards

    def test_get_phase_standards_empty(self):
        standards = get_phase_standards("idea")
        assert standards == {}

    def test_get_phase_standards_unknown(self):
        standards = get_phase_standards("nonexistent")
        assert standards == {}

    def test_get_required_contributions(self):
        contribs = get_required_contributions("production")
        assert "architect" in contribs
        assert "qa-engineer" in contribs
        assert "accountability-generator" in contribs

    def test_get_required_contributions_idea(self):
        assert get_required_contributions("idea") == []

    def test_get_next_phase(self):
        assert get_next_phase("poc") == "mvp"
        assert get_next_phase("production") is None

    def test_is_phase_gate(self):
        assert is_phase_gate("idea") is False
        assert is_phase_gate("poc") is True
        assert is_phase_gate("production") is True

    def test_reload_phases(self):
        # First load
        p1 = get_phase_definition("poc")
        assert p1 is not None
        # Reload
        reload_phases()
        p2 = get_phase_definition("poc")
        assert p2 is not None
        assert p2.name == p1.name


class TestNewCustomFields:
    """Verify the new fields on TaskCustomFields."""

    def test_delivery_phase_default(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields()
        assert cf.delivery_phase is None

    def test_contribution_fields_default(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields()
        assert cf.contribution_type is None
        assert cf.contribution_target is None

    def test_coworkers_default(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields()
        assert cf.coworkers is None

    def test_delivery_phase_set(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields(delivery_phase="mvp", phase_progression="standard")
        assert cf.delivery_phase == "mvp"
        assert cf.phase_progression == "standard"

    def test_contribution_set(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields(
            contribution_type="qa_test_definition",
            contribution_target="task-123",
        )
        assert cf.contribution_type == "qa_test_definition"
        assert cf.contribution_target == "task-123"

    def test_coworkers_set(self):
        from fleet.core.models import TaskCustomFields
        cf = TaskCustomFields(coworkers=["devops", "technical-writer"])
        assert len(cf.coworkers) == 2
        assert "devops" in cf.coworkers