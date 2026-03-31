"""Delivery phases — PO-defined maturity progression.

Phases track HOW MATURE a deliverable is, distinct from methodology
stages which track HOW you work. The PO defines phases, progressions,
and standards via config/phases.yaml. The system enforces whatever
the PO decides.

The PO can:
- Create unlimited phases with any name
- Define any progression sequence
- Define any standards per phase
- Change standards at any time
- Create project-specific progressions
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PhaseDefinition:
    """A single phase in a progression — PO-defined."""

    name: str
    description: str = ""
    standards: dict[str, Any] = field(default_factory=dict)
    required_contributions: list[str] = field(default_factory=list)
    gate: bool = True  # requires PO approval to enter


@dataclass
class PhaseProgression:
    """An ordered sequence of phases — PO-defined."""

    name: str
    phases: list[PhaseDefinition] = field(default_factory=list)

    @property
    def phase_names(self) -> list[str]:
        return [p.name for p in self.phases]

    def get_phase(self, name: str) -> Optional[PhaseDefinition]:
        return next((p for p in self.phases if p.name == name), None)

    def get_next_phase(self, current: str) -> Optional[PhaseDefinition]:
        names = self.phase_names
        if current not in names:
            return self.phases[0] if self.phases else None
        idx = names.index(current)
        if idx + 1 < len(self.phases):
            return self.phases[idx + 1]
        return None

    def get_previous_phase(self, current: str) -> Optional[PhaseDefinition]:
        names = self.phase_names
        if current not in names or names.index(current) == 0:
            return None
        return self.phases[names.index(current) - 1]


# ─── Config Loading ────────────────────────────────────────────────────


def _load_phases_config() -> dict:
    """Load phases from config/phases.yaml."""
    fleet_dir = Path(__file__).parent.parent.parent
    phases_path = fleet_dir / "config" / "phases.yaml"
    if not phases_path.exists():
        logger.debug("No phases.yaml found at %s", phases_path)
        return {}
    try:
        with open(phases_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Failed to load phases.yaml: %s", e)
        return {}


def load_progressions() -> dict[str, PhaseProgression]:
    """Load all phase progressions from config."""
    config = _load_phases_config()
    progressions: dict[str, PhaseProgression] = {}

    for prog_name, phase_list in config.get("progressions", {}).items():
        if not isinstance(phase_list, list):
            continue
        phases = []
        for p in phase_list:
            if isinstance(p, dict):
                phases.append(PhaseDefinition(
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    standards=p.get("standards", {}),
                    required_contributions=p.get("required_contributions", []),
                    gate=p.get("gate", True),
                ))
        progressions[prog_name] = PhaseProgression(name=prog_name, phases=phases)

    return progressions


# ─── Public API ────────────────────────────────────────────────────────


_progressions: Optional[dict[str, PhaseProgression]] = None


def get_progressions() -> dict[str, PhaseProgression]:
    """Get all loaded progressions (cached after first load)."""
    global _progressions
    if _progressions is None:
        _progressions = load_progressions()
    return _progressions


def get_progression(name: str) -> Optional[PhaseProgression]:
    """Get a specific progression by name."""
    return get_progressions().get(name)


def get_phase_definition(
    phase_name: str,
    progression_name: str = "standard",
) -> Optional[PhaseDefinition]:
    """Get a phase definition by name within a progression."""
    prog = get_progression(progression_name)
    if prog:
        return prog.get_phase(phase_name)
    # Search all progressions if not found in specified one
    for prog in get_progressions().values():
        phase = prog.get_phase(phase_name)
        if phase:
            return phase
    return None


def get_phase_standards(
    phase_name: str,
    progression_name: str = "standard",
) -> dict[str, Any]:
    """Get the standards for a phase. Returns empty dict if not found."""
    phase = get_phase_definition(phase_name, progression_name)
    return phase.standards if phase else {}


def get_required_contributions(
    phase_name: str,
    progression_name: str = "standard",
) -> list[str]:
    """Get required contributor roles for a phase."""
    phase = get_phase_definition(phase_name, progression_name)
    return phase.required_contributions if phase else []


def get_next_phase(
    current_phase: str,
    progression_name: str = "standard",
) -> Optional[str]:
    """Get the next phase name in a progression."""
    prog = get_progression(progression_name)
    if not prog:
        return None
    next_p = prog.get_next_phase(current_phase)
    return next_p.name if next_p else None


def is_phase_gate(
    phase_name: str,
    progression_name: str = "standard",
) -> bool:
    """Check if entering this phase requires PO approval."""
    phase = get_phase_definition(phase_name, progression_name)
    return phase.gate if phase else True  # default: gate required


def reload_phases() -> None:
    """Force reload phases from config (after config change)."""
    global _progressions
    _progressions = None