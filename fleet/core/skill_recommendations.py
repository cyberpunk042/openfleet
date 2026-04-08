"""Stage-aware skill recommendations.

Reads config/skill-stage-mapping.yaml and returns recommendations
for a given agent + methodology stage combination.

Used by context_assembly to include skill recommendations in
fleet_task_context() responses.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cached config — loaded once, reused.
_config: dict | None = None
_config_path: Path | None = None


def _load_config() -> dict:
    """Load skill-stage-mapping.yaml, caching the result."""
    global _config, _config_path

    if _config is not None:
        return _config

    # Find config relative to this file
    fleet_dir = Path(__file__).resolve().parent.parent.parent
    config_path = fleet_dir / "config" / "skill-stage-mapping.yaml"

    if not config_path.exists():
        logger.debug("skill-stage-mapping.yaml not found at %s", config_path)
        _config = {}
        return _config

    try:
        import yaml
        with open(config_path) as f:
            _config = yaml.safe_load(f) or {}
        _config_path = config_path
        logger.debug("Loaded skill-stage-mapping.yaml: %d top-level keys", len(_config))
    except Exception as e:
        logger.warning("Failed to load skill-stage-mapping.yaml: %s", e)
        _config = {}

    return _config


def get_skill_recommendations(
    agent_name: str,
    stage: str,
) -> dict[str, Any]:
    """Get skill recommendations for an agent at a given methodology stage.

    Returns a dict with:
      - always: skills recommended at all stages
      - stage: skills recommended for this specific stage
      - blocked: skills that should NOT be used at this stage
      - stage_name: the stage name (for display)

    Args:
        agent_name: The agent's role name (e.g., "architect", "software-engineer").
        stage: The methodology stage (conversation, analysis, investigation, reasoning, work).
    """
    config = _load_config()
    if not config:
        return {"always": [], "stage": [], "blocked": [], "stage_name": stage}

    generic = config.get("generic", {})
    roles = config.get("roles", {})
    restrictions = config.get("restrictions", {})
    role_config = roles.get(agent_name, {})

    # Always-available skills (generic + role all_stages)
    always = []
    generic_all = generic.get("all_stages", {})
    if isinstance(generic_all, dict):
        for r in generic_all.get("recommended", []):
            always.append({"skill": r["skill"], "why": r.get("why", "")})

    role_all = role_config.get("all_stages", [])
    if isinstance(role_all, list):
        for r in role_all:
            always.append({"skill": r["skill"], "why": r.get("why", "")})

    # Stage-specific skills
    stage_recs = []
    seen = set()

    # Generic stage
    generic_stage = generic.get(stage, {})
    if isinstance(generic_stage, dict):
        for r in generic_stage.get("recommended", []):
            if r["skill"] not in seen:
                seen.add(r["skill"])
                stage_recs.append({"skill": r["skill"], "why": r.get("why", "")})
        for r in generic_stage.get("plugin_recommended", []):
            key = f"{r['skill']}:{r.get('plugin', '')}"
            if key not in seen:
                seen.add(key)
                stage_recs.append({
                    "skill": r["skill"],
                    "plugin": r.get("plugin", ""),
                    "why": r.get("why", ""),
                })

    # Role stage
    role_stage = role_config.get(stage, [])
    if isinstance(role_stage, list):
        for r in role_stage:
            if r["skill"] not in seen:
                seen.add(r["skill"])
                stage_recs.append({"skill": r["skill"], "why": r.get("why", "")})

    # Blocked skills at this stage
    blocked = []
    stage_restrictions = restrictions.get(stage, {})
    if isinstance(stage_restrictions, dict):
        blocked = stage_restrictions.get("blocked_skills", [])

    return {
        "always": always,
        "stage": stage_recs,
        "blocked": blocked,
        "stage_name": stage,
    }
