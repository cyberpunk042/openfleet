"""Source Parsers — Extract entities + relationships from non-KB fleet content.

Each parser reads a specific file type (Python, YAML, Markdown) and produces
Entity + Relationship objects compatible with kb_sync's LightRAGClient.

Relationship types designed per source:

PYTHON FILES:
  module IMPORTS module           — import dependency
  module DEFINES function/class   — code structure
  module BELONGS TO system        — system membership (from path)
  function CALLS function         — call chain (from known patterns)
  module USES module              — functional dependency

CONFIG YAML:
  config ASSIGNS tool TO agent    — tooling assignment
  config ASSIGNS plugin TO agent  — plugin assignment
  config ASSIGNS skill TO agent   — skill assignment
  config DEFINES setting          — configuration definition

AGENT CLAUDE.MD:
  agent HAS ROLE role             — role definition
  agent USES tool                 — tool usage
  agent FOLLOWS methodology       — methodology reference

MANUALS / DESIGN DOCS:
  document DESCRIBES entity       — documentation coverage
  document REFERENCES entity      — cross-reference
  document DEFINES concept        — concept definition

Usage:
    from fleet.core.source_parsers import parse_python, parse_yaml_config, parse_markdown
    entities, relationships = parse_python(Path("fleet/cli/orchestrator.py"))
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fleet.core.kb_sync import Entity, Relationship

FLEET_DIR = Path(__file__).parent.parent.parent


# ── Python Parser ──────────────────────────────────────────────────

# Map module paths to known systems
MODULE_SYSTEM_MAP = {
    # S01 Methodology
    "fleet/core/methodology": "System 01: Methodology",
    "fleet/core/stage_context": "System 01: Methodology",
    "fleet/core/phases": "System 01: Methodology",
    "fleet/core/plane_methodology": "System 01: Methodology",
    # S02 Immune System
    "fleet/core/doctor": "System 02: Immune System",
    "fleet/core/behavioral_security": "System 02: Immune System",
    "fleet/core/self_healing": "System 02: Immune System",
    # S03 Teaching
    "fleet/core/teaching": "System 03: Teaching",
    # S04 Event Bus
    "fleet/core/events": "System 04: Event Bus",
    "fleet/core/event_chain": "System 04: Event Bus",
    "fleet/core/event_router": "System 04: Event Bus",
    "fleet/core/event_display": "System 04: Event Bus",
    # S05 Control Surface
    "fleet/core/fleet_mode": "System 05: Control Surface",
    "fleet/core/directives": "System 05: Control Surface",
    "fleet/core/config_watcher": "System 05: Control Surface",
    "fleet/core/config_sync": "System 05: Control Surface",
    # S06 Agent Lifecycle
    "fleet/core/agent_lifecycle": "System 06: Agent Lifecycle",
    "fleet/core/agent_roles": "System 06: Agent Lifecycle",
    "fleet/core/heartbeat_gate": "System 06: Agent Lifecycle",
    "fleet/core/heartbeat_stamp": "System 06: Agent Lifecycle",
    "fleet/core/heartbeat_context": "System 06: Agent Lifecycle",
    "fleet/core/memory_structure": "System 06: Agent Lifecycle",
    # S07 Orchestrator
    "fleet/cli/orchestrator": "System 07: Orchestrator",
    "fleet/cli/dispatch": "System 07: Orchestrator",
    "fleet/core/driver": "System 07: Orchestrator",
    "fleet/core/change_detector": "System 07: Orchestrator",
    "fleet/core/gateway_guard": "System 07: Orchestrator",
    "fleet/core/task_lifecycle": "System 07: Orchestrator",
    "fleet/core/task_scoring": "System 07: Orchestrator",
    "fleet/core/review_gates": "System 07: Orchestrator",
    # S08 MCP Tools
    "fleet/mcp/tools": "System 08: MCP Tools",
    "fleet/mcp/server": "System 08: MCP Tools",
    "fleet/mcp/context": "System 08: MCP Tools",
    # S09 Standards
    "fleet/core/standards": "System 09: Standards",
    "fleet/core/plan_quality": "System 09: Standards",
    "fleet/core/pr_hygiene": "System 09: Standards",
    # S10 Transpose
    "fleet/core/transpose": "System 10: Transpose",
    "fleet/core/artifact_tracker": "System 10: Transpose",
    # S11 Storm Prevention
    "fleet/core/storm_monitor": "System 11: Storm Prevention",
    "fleet/core/storm_integration": "System 11: Storm Prevention",
    "fleet/core/storm_analytics": "System 11: Storm Prevention",
    "fleet/core/incident_report": "System 11: Storm Prevention",
    "fleet/core/outage_detector": "System 11: Storm Prevention",
    # S12 Budget
    "fleet/core/budget_monitor": "System 12: Budget",
    "fleet/core/budget_modes": "System 12: Budget",
    "fleet/core/budget_analytics": "System 12: Budget",
    "fleet/core/budget_ui": "System 12: Budget",
    # S13 Labor Attribution
    "fleet/core/labor": "System 13: Labor Attribution",
    "fleet/core/labor_stamp": "System 13: Labor Attribution",
    "fleet/core/labor_analytics": "System 13: Labor Attribution",
    "fleet/core/trail_recorder": "System 13: Labor Attribution",
    # S14 Multi-Backend Router
    "fleet/core/backend_router": "System 14: Multi-Backend Router",
    "fleet/core/backend_health": "System 14: Multi-Backend Router",
    "fleet/core/model_swap": "System 14: Multi-Backend Router",
    "fleet/core/model_selection": "System 14: Multi-Backend Router",
    "fleet/core/model_configs": "System 14: Multi-Backend Router",
    "fleet/core/model_promotion": "System 14: Multi-Backend Router",
    "fleet/core/model_benchmark": "System 14: Multi-Backend Router",
    "fleet/core/routing": "System 14: Multi-Backend Router",
    "fleet/core/shadow_routing": "System 14: Multi-Backend Router",
    "fleet/core/router_unification": "System 14: Multi-Backend Router",
    "fleet/core/openai_client": "System 14: Multi-Backend Router",
    "fleet/core/turboquant": "System 14: Multi-Backend Router",
    # S15 Challenge
    "fleet/core/challenge": "System 15: Challenge",
    "fleet/core/challenge_protocol": "System 15: Challenge",
    "fleet/core/challenge_automated": "System 15: Challenge",
    "fleet/core/challenge_cross_model": "System 15: Challenge",
    "fleet/core/challenge_scenario": "System 15: Challenge",
    "fleet/core/challenge_analytics": "System 15: Challenge",
    "fleet/core/challenge_deferred": "System 15: Challenge",
    "fleet/core/challenge_readiness": "System 15: Challenge",
    "fleet/core/codex_review": "System 15: Challenge",
    # S16 Models
    "fleet/core/models": "System 16: Models",
    # S17 Plane Integration
    "fleet/core/plane_sync": "System 17: Plane Integration",
    "fleet/core/plane_watcher": "System 17: Plane Integration",
    # S18 Notifications
    "fleet/core/notification_router": "System 18: Notifications",
    "fleet/core/cross_refs": "System 18: Notifications",
    "fleet/core/urls": "System 18: Notifications",
    # S19 Session & Context
    "fleet/core/session_manager": "System 19: Session & Context",
    "fleet/core/session_telemetry": "System 19: Session & Context",
    "fleet/core/session_metrics": "System 19: Session & Context",
    "fleet/core/preembed": "System 19: Session & Context",
    "fleet/core/context_writer": "System 19: Session & Context",
    "fleet/core/context_assembly": "System 19: Session & Context",
    # S20 Infrastructure
    "fleet/core/auth": "System 20: Infrastructure",
    "fleet/core/cache": "System 20: Infrastructure",
    "fleet/core/federation": "System 20: Infrastructure",
    "fleet/core/interfaces": "System 20: Infrastructure",
    "fleet/core/cluster_peering": "System 20: Infrastructure",
    "fleet/core/dual_gpu": "System 20: Infrastructure",
    "fleet/core/health": "System 20: Infrastructure",
    "fleet/core/error_reporter": "System 20: Infrastructure",
    "fleet/infra/config_loader": "System 20: Infrastructure",
    "fleet/infra/mc_client": "System 20: Infrastructure",
    "fleet/infra/irc_client": "System 20: Infrastructure",
    # S21 Agent Tooling
    "fleet/core/skill_enforcement": "System 21: Agent Tooling",
    # S22 Agent Intelligence
    "fleet/core/navigator": "System 22: Agent Intelligence",
    "fleet/core/autocomplete": "System 22: Agent Intelligence",
    "fleet/core/smart_chains": "System 22: Agent Intelligence",
    "fleet/core/chain_runner": "System 22: Agent Intelligence",
    # Knowledge Map Infrastructure
    "fleet/core/kb_sync": "Knowledge Map Infrastructure",
    "fleet/core/source_parsers": "Knowledge Map Infrastructure",
    "fleet/core/graph_enrichment": "Knowledge Map Infrastructure",
    # Contribution System
    "fleet/core/contributions": "Contribution System",
    # Gateway
    "gateway/executor": "Gateway",
    "gateway/ws_server": "Gateway",
    "gateway/setup": "Gateway",
    "gateway/server": "Gateway",
    "gateway/operations": "Gateway",
    "gateway/models": "Gateway",
    # Watchers
    "fleet/core/remote_watcher": "System 07: Orchestrator",
    "fleet/core/ocmc_watcher": "System 07: Orchestrator",
    "fleet/core/board_cleanup": "System 07: Orchestrator",
    # Velocity / Progression
    "fleet/core/velocity": "System 07: Orchestrator",
    "fleet/core/tier_progression": "System 06: Agent Lifecycle",
    "fleet/core/role_providers": "System 19: Session & Context",
}


def parse_python(filepath: Path) -> tuple[list[Entity], list[Relationship]]:
    """Parse a Python file for imports, classes, functions → entities + relationships."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    rel_path = str(filepath.relative_to(FLEET_DIR))
    module_name = rel_path.replace("/", ".").replace(".py", "")
    module_key = rel_path.replace(".py", "")

    entities = []
    relationships = []

    # Module entity
    docstring = _extract_docstring(text)
    system = MODULE_SYSTEM_MAP.get(module_key, "")
    desc = docstring[:300] if docstring else f"Python module: {module_name}"
    if system:
        desc += f" Part of {system}."

    entities.append(Entity(
        name=rel_path,
        entity_type="module",
        description=desc,
        source_file=rel_path,
    ))

    # System membership
    if system:
        relationships.append(Relationship(
            src=rel_path, tgt=system,
            rel_type="belongs to",
            description=f"{rel_path} belongs to {system}",
            source_file=rel_path,
        ))

    # Imports → IMPORTS relationships
    for line in lines:
        imp = _parse_import(line)
        if imp and imp.startswith("fleet.") or (imp and imp.startswith("gateway.")):
            imp_path = imp.replace(".", "/") + ".py"
            relationships.append(Relationship(
                src=rel_path, tgt=imp_path,
                rel_type="imports",
                description=f"{rel_path} imports {imp_path}",
                source_file=rel_path,
            ))

    # Classes → DEFINES relationships
    for match in re.finditer(r"^class (\w+)", text, re.MULTILINE):
        class_name = match.group(1)
        class_doc = _extract_class_doc(text, match.start())
        entities.append(Entity(
            name=f"{module_name}.{class_name}",
            entity_type="class",
            description=class_doc[:200] if class_doc else f"Class {class_name} in {module_name}",
            source_file=rel_path,
        ))
        relationships.append(Relationship(
            src=rel_path, tgt=f"{module_name}.{class_name}",
            rel_type="defines",
            description=f"{rel_path} defines class {class_name}",
            source_file=rel_path,
        ))

    # Functions → DEFINES relationships (top-level and async)
    for match in re.finditer(r"^(?:async )?def (\w+)\(", text, re.MULTILINE):
        func_name = match.group(1)
        if func_name.startswith("_") and func_name != "__init__":
            continue  # skip private functions
        func_doc = _extract_func_doc(text, match.start())
        entities.append(Entity(
            name=f"{module_name}.{func_name}",
            entity_type="function",
            description=func_doc[:200] if func_doc else f"Function {func_name} in {module_name}",
            source_file=rel_path,
        ))
        relationships.append(Relationship(
            src=rel_path, tgt=f"{module_name}.{func_name}",
            rel_type="defines",
            description=f"{rel_path} defines {func_name}",
            source_file=rel_path,
        ))

    return entities, relationships


def _parse_import(line: str) -> Optional[str]:
    """Extract module path from import line."""
    line = line.strip()
    m = re.match(r"from ([\w.]+) import", line)
    if m:
        return m.group(1)
    m = re.match(r"import ([\w.]+)", line)
    if m:
        return m.group(1)
    return None


def _extract_docstring(text: str) -> str:
    """Extract module-level docstring."""
    m = re.match(r'^"""(.*?)"""', text, re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0]
    m = re.match(r"^'''(.*?)'''", text, re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0]
    return ""


def _extract_class_doc(text: str, pos: int) -> str:
    """Extract class docstring."""
    after = text[pos:pos + 500]
    m = re.search(r'"""(.*?)"""', after, re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0]
    return ""


def _extract_func_doc(text: str, pos: int) -> str:
    """Extract function docstring."""
    after = text[pos:pos + 500]
    m = re.search(r'"""(.*?)"""', after, re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0]
    return ""


# ── Config YAML Parser ────────────────────────────────────────────

def parse_yaml_config(filepath: Path) -> tuple[list[Entity], list[Relationship]]:
    """Parse a YAML config file for agent/tool/skill assignments."""
    text = filepath.read_text(encoding="utf-8")
    rel_path = str(filepath.relative_to(FLEET_DIR))
    config_name = filepath.stem

    entities = []
    relationships = []

    # Config entity
    entities.append(Entity(
        name=config_name,
        entity_type="config",
        description=f"Fleet configuration: {config_name}",
        source_file=rel_path,
    ))

    if config_name == "agent-tooling":
        # Parse agent → tool/plugin/skill assignments
        current_agent = None
        current_section = None
        for line in text.split("\n"):
            # Agent name
            m = re.match(r"  (\w[\w-]+):", line)
            if m and not line.strip().startswith("-") and not line.strip().startswith("#"):
                if m.group(1) not in ("mcp_servers", "plugins", "skills", "defaults",
                                       "name", "command", "args", "env", "package"):
                    current_agent = m.group(1)

            # Section within agent
            if current_agent:
                if "mcp_servers:" in line:
                    current_section = "mcp"
                elif "plugins:" in line:
                    current_section = "plugins"
                elif "skills:" in line:
                    current_section = "skills"

            # Items
            m = re.match(r"\s+- (\S+)", line)
            if m and current_agent and current_section:
                item = m.group(1).rstrip("#").strip()
                if item and not item.startswith("{") and len(item) > 1:
                    rel_type = {
                        "mcp": "has mcp server",
                        "plugins": "has plugin",
                        "skills": "has skill",
                    }.get(current_section, "uses")

                    relationships.append(Relationship(
                        src=current_agent, tgt=item,
                        rel_type=rel_type,
                        description=f"{current_agent} {rel_type} {item}",
                        source_file=rel_path,
                    ))

    elif config_name == "synergy-matrix":
        # Parse contribution relationships
        for line in text.split("\n"):
            m = re.match(r"  (\w[\w-]+):", line)
            if m:
                target_role = m.group(1)
            m2 = re.match(r"\s+- role: (\S+)", line)
            if m2:
                contributor = m2.group(1)
                relationships.append(Relationship(
                    src=contributor, tgt=target_role,
                    rel_type="contributes to",
                    description=f"{contributor} contributes to {target_role}",
                    source_file=rel_path,
                ))

    elif config_name == "agent-identities":
        # Parse agent identity fields
        current_agent = None
        for line in text.split("\n"):
            m = re.match(r"(\w[\w-]+):", line)
            if m and not line.startswith(" "):
                current_agent = m.group(1)
                entities.append(Entity(
                    name=current_agent,
                    entity_type="agent",
                    description=f"Agent identity: {current_agent}",
                    source_file=rel_path,
                ))

    return entities, relationships


# ── Markdown Document Parser ───────────────────────────────────────

def parse_markdown_doc(filepath: Path) -> tuple[list[Entity], list[Relationship]]:
    """Parse a markdown document for entity references and section structure."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    rel_path = str(filepath.relative_to(FLEET_DIR))

    # Title
    title = filepath.stem
    for line in lines:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    entities = []
    relationships = []

    # Document entity
    doc_type = "design_doc"
    if "research" in rel_path:
        doc_type = "research"
    elif "fleet-elevation" in rel_path:
        doc_type = "design_doc"
    elif "knowledge-map" in rel_path:
        doc_type = "concept"

    # First paragraph as description
    desc = title
    for line in lines[2:20]:
        if line.strip() and not line.startswith("#") and not line.startswith("**"):
            desc = line.strip()[:300]
            break

    entities.append(Entity(
        name=title,
        entity_type=doc_type,
        description=desc,
        source_file=rel_path,
    ))

    # Find references to known fleet entities in the text
    # Systems: S01-S22, System XX
    for m in re.finditer(r"S(\d{2})\b|System (\d{1,2})", text):
        sys_num = m.group(1) or m.group(2)
        relationships.append(Relationship(
            src=title, tgt=f"S{sys_num.zfill(2)}",
            rel_type="references",
            description=f"{title} references system S{sys_num.zfill(2)}",
            source_file=rel_path,
        ))

    # Tools: fleet_xxx
    for m in re.finditer(r"\bfleet_(\w+)\b", text):
        tool_name = f"fleet_{m.group(1)}"
        relationships.append(Relationship(
            src=title, tgt=tool_name,
            rel_type="references",
            description=f"{title} references tool {tool_name}",
            source_file=rel_path,
        ))

    # Agents
    for agent in ["architect", "software-engineer", "qa-engineer", "devops",
                   "devsecops-expert", "fleet-ops", "project-manager",
                   "technical-writer", "ux-designer", "accountability-generator"]:
        if agent in text.lower():
            relationships.append(Relationship(
                src=title, tgt=agent,
                rel_type="references",
                description=f"{title} references agent {agent}",
                source_file=rel_path,
            ))

    # Commands: /xxx
    for m in re.finditer(r"\B/(\w[\w-]+)\b", text):
        cmd = f"/{m.group(1)}"
        if len(cmd) > 3 and cmd not in ("/dev", "/var", "/tmp", "/usr", "/etc",
                                         "/app", "/home", "/bin"):
            relationships.append(Relationship(
                src=title, tgt=cmd,
                rel_type="references",
                description=f"{title} references command {cmd}",
                source_file=rel_path,
            ))

    # Modules: xxx.py
    for m in re.finditer(r"\b(\w+\.py)\b", text):
        module = m.group(1)
        if module not in ("setup.py", "__init__.py"):
            relationships.append(Relationship(
                src=title, tgt=module,
                rel_type="references",
                description=f"{title} references module {module}",
                source_file=rel_path,
            ))

    # Deduplicate relationships
    seen = set()
    unique_rels = []
    for r in relationships:
        key = (r.src.upper(), r.rel_type, r.tgt.upper())
        if key not in seen:
            unique_rels.append(r)
            seen.add(key)

    return entities, unique_rels


# ── Agent CLAUDE.md Parser ─────────────────────────────────────────

def parse_agent_claude_md(filepath: Path) -> tuple[list[Entity], list[Relationship]]:
    """Parse an agent CLAUDE.md template for role definition and tool references."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    rel_path = str(filepath.relative_to(FLEET_DIR))

    # Agent name from filename
    agent_name = filepath.stem

    entities = []
    relationships = []

    # Agent entity with mission from first paragraph
    mission = ""
    for line in lines[2:10]:
        if line.strip() and not line.startswith("#"):
            mission = line.strip()[:300]
            break

    entities.append(Entity(
        name=f"agent-template:{agent_name}",
        entity_type="agent",
        description=f"Agent template for {agent_name}. {mission}",
        source_file=rel_path,
    ))

    # Link to the agent
    relationships.append(Relationship(
        src=f"agent-template:{agent_name}", tgt=agent_name,
        rel_type="defines template for",
        description=f"CLAUDE.md template defines instructions for {agent_name}",
        source_file=rel_path,
    ))

    # Find fleet tool references
    for m in re.finditer(r"\bfleet_(\w+)\b", text):
        tool = f"fleet_{m.group(1)}"
        relationships.append(Relationship(
            src=f"agent-template:{agent_name}", tgt=tool,
            rel_type="instructs to use",
            description=f"{agent_name} template instructs use of {tool}",
            source_file=rel_path,
        ))

    # Find skill references
    for m in re.finditer(r"\B/(\w[\w-]+)\b", text):
        skill = m.group(1)
        if len(skill) > 3 and skill not in ("dev", "var", "tmp", "usr", "etc",
                                              "app", "home", "bin"):
            relationships.append(Relationship(
                src=f"agent-template:{agent_name}", tgt=f"/{skill}",
                rel_type="recommends",
                description=f"{agent_name} template recommends /{skill}",
                source_file=rel_path,
            ))

    # Deduplicate
    seen = set()
    unique = []
    for r in relationships:
        key = (r.src.upper(), r.rel_type, r.tgt.upper())
        if key not in seen:
            unique.append(r)
            seen.add(key)

    return entities, unique
