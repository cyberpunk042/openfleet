"""Fleet control state — read fleet_config from board.

The fleet control surface stores state in the board's fleet_config JSON
field. The orchestrator reads this every cycle to determine:
- Work Mode: where new work comes from
- Cycle Phase: what kind of work agents do
- Backend Mode: which AI backend processes requests

These three axes are independent. Any combination is valid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ─── Valid Values ────────────────────────────────────────────────────────

WORK_MODES = [
    "full-autonomous",
    "project-management-work",
    "local-work-only",
    "finish-current-work",
    "work-paused",
]

CYCLE_PHASES = [
    "execution",
    "planning",
    "analysis",
    "investigation",
    "review",
    "crisis-management",
]

BACKEND_MODES = [
    "claude",
    "localai",
    "openrouter",
    "claude+localai",
    "claude+openrouter",
    "localai+openrouter",
    "claude+localai+openrouter",
]


@dataclass
class FleetControlState:
    """Current fleet control state from the board's fleet_config."""
    work_mode: str = "work-paused"
    cycle_phase: str = "execution"
    backend_mode: str = "claude"
    budget_mode: str = "standard"
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


def read_fleet_control(board_data: dict) -> FleetControlState:
    """Read fleet control state from board data.

    Args:
        board_data: The board dict from MC API (includes fleet_config).

    Returns:
        FleetControlState with current mode/phase/backend.
    """
    config = board_data.get("fleet_config") or {}
    return FleetControlState(
        work_mode=config.get("work_mode", "full-autonomous"),
        cycle_phase=config.get("cycle_phase", "execution"),
        backend_mode=config.get("backend_mode", "claude"),
        budget_mode=config.get("budget_mode", "standard"),
        updated_at=config.get("updated_at"),
        updated_by=config.get("updated_by"),
    )


def should_dispatch(state: FleetControlState) -> bool:
    """Check if dispatch is allowed based on work mode."""
    return state.work_mode not in ("work-paused", "finish-current-work")


def should_pull_from_plane(state: FleetControlState) -> bool:
    """Check if PM should pull new work from Plane.

    'Local Work Only' means agents work on OCMC tasks only.
    PM does NOT pull new work from Plane. Plane sync still runs.
    """
    return state.work_mode not in ("local-work-only", "work-paused", "finish-current-work")


def get_active_agents_for_phase(state: FleetControlState) -> Optional[list[str]]:
    """Get the list of agents that should be active for the current cycle phase.

    Returns None if all agents are active (no filter).
    """
    phase_agents = {
        "planning": ["project-manager", "architect"],
        "analysis": ["architect", "project-manager"],
        "investigation": None,  # any assigned agent
        "review": ["fleet-ops"],
        "crisis-management": ["fleet-ops", "devsecops-expert"],
        "execution": None,  # all agents
    }
    return phase_agents.get(state.cycle_phase)