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

    # Imports → weighted relationships based on WHAT is imported
    imported_names = {}  # track what names are imported from where
    for line in lines:
        line_stripped = line.strip()
        imp_module = _parse_import(line_stripped)
        if not imp_module:
            continue
        if not (imp_module.startswith("fleet.") or imp_module.startswith("gateway.")):
            continue

        imp_path = imp_module.replace(".", "/") + ".py"
        imp_system = MODULE_SYSTEM_MAP.get(imp_path.replace(".py", ""), "")

        # Extract what is imported: "from fleet.core.doctor import DoctorReport, run_doctor_cycle"
        names = []
        m = re.match(r"from [\w.]+ import (.+)", line_stripped)
        if m:
            names = [n.strip().split(" as ")[0] for n in m.group(1).split(",")]
            for name in names:
                imported_names[name.strip()] = imp_module

        # Smart description based on what's imported
        if names:
            desc = f"{rel_path} imports {', '.join(names[:3])} from {imp_path}"
        else:
            desc = f"{rel_path} imports {imp_path}"
        if imp_system:
            desc += f" ({imp_system})"

        # Weight: same-system imports = 0.5, cross-system = 1.0, orchestrator imports = 1.5
        weight = 1.0
        if system and imp_system and system == imp_system:
            weight = 0.5  # internal dependency
        elif "orchestrator" in rel_path.lower():
            weight = 1.5  # orchestrator dependencies are critical

        relationships.append(Relationship(
            src=rel_path, tgt=imp_path,
            rel_type="imports",
            description=desc,
            source_file=rel_path,
            weight=weight,
        ))

    # Detect CALL PATTERNS — known orchestrator step functions, tool dispatches, etc.
    call_patterns = {
        r"run_doctor_cycle\(": ("runs", "fleet/core/doctor.py", "executes immune system check"),
        r"StormMonitor\(\)\.evaluate": ("evaluates", "fleet/core/storm_monitor.py", "checks storm severity"),
        r"write_heartbeat_context\(": ("writes", "fleet/core/context_writer.py", "writes heartbeat pre-embed"),
        r"write_task_context\(": ("writes", "fleet/core/context_writer.py", "writes task pre-embed"),
        r"write_knowledge_context\(": ("writes", "fleet/core/context_writer.py", "writes navigator output"),
        r"Navigator\(\)": ("uses", "fleet/core/navigator.py", "assembles knowledge context"),
        r"parse_directives\(": ("parses", "fleet/core/directives.py", "reads PO directives"),
        r"check_gateway_duplication\(": ("checks", "fleet/core/gateway_guard.py", "detects gateway duplication"),
        r"adapt_lesson\(": ("adapts", "fleet/core/teaching.py", "creates teaching lesson"),
        r"FleetLifecycle\(": ("manages", "fleet/core/agent_lifecycle.py", "manages agent lifecycle"),
        r"BudgetMonitor\(": ("monitors", "fleet/core/budget_monitor.py", "tracks budget"),
        r"fleet_should_dispatch\(": ("gates", "fleet/core/fleet_mode.py", "checks dispatch eligibility"),
        r"get_role_provider\(": ("loads", "fleet/core/role_providers.py", "loads role-specific data"),
        r"build_heartbeat_preembed\(": ("builds", "fleet/core/preembed.py", "builds heartbeat context"),
        r"build_task_preembed\(": ("builds", "fleet/core/preembed.py", "builds task context"),
    }
    for pattern, (verb, target, context) in call_patterns.items():
        if re.search(pattern, text):
            relationships.append(Relationship(
                src=rel_path, tgt=target,
                rel_type=verb,
                description=f"{rel_path} {verb} {target} — {context}",
                source_file=rel_path,
                weight=1.5,  # runtime call = high-value relationship
            ))

    # Classes → DEFINES with inheritance detection
    for match in re.finditer(r"^class (\w+)(?:\(([^)]+)\))?:", text, re.MULTILINE):
        class_name = match.group(1)
        bases = match.group(2)
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
        # Inheritance
        if bases:
            for base in bases.split(","):
                base = base.strip()
                if base and base not in ("object",) and not base.startswith("("):
                    # Resolve base class to full path if imported
                    full_base = imported_names.get(base, base)
                    relationships.append(Relationship(
                        src=f"{module_name}.{class_name}", tgt=full_base,
                        rel_type="extends",
                        description=f"{class_name} extends {base}",
                        source_file=rel_path,
                        weight=1.2,
                    ))

    # Public functions only — with meaningful descriptions
    for match in re.finditer(r"^(async )?def (\w+)\(([^)]*)\)", text, re.MULTILINE):
        is_async = bool(match.group(1))
        func_name = match.group(2)
        params = match.group(3)
        if func_name.startswith("_"):
            continue
        func_doc = _extract_func_doc(text, match.start())

        desc = func_doc[:200] if func_doc else ""
        if not desc:
            # Build description from signature
            param_names = [p.strip().split(":")[0].split("=")[0].strip()
                          for p in params.split(",") if p.strip() and p.strip() != "self"]
            prefix = "async " if is_async else ""
            desc = f"{prefix}{func_name}({', '.join(param_names[:4])})"

        entities.append(Entity(
            name=f"{module_name}.{func_name}",
            entity_type="function",
            description=desc,
            source_file=rel_path,
        ))
        relationships.append(Relationship(
            src=rel_path, tgt=f"{module_name}.{func_name}",
            rel_type="defines",
            description=f"{rel_path} defines {func_name}",
            source_file=rel_path,
        ))

    return entities, relationships


# ── SKILL.md Parser (AICP repo) ────────────────────────────────────

AICP_SKILLS_DIR = FLEET_DIR.parent / "devops-expert-local-ai" / ".claude" / "skills"


def parse_skill_md(filepath: Path) -> tuple[list[Entity], list[Relationship]]:
    """Parse an AICP SKILL.md file for skill metadata and relationships."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    skill_name = filepath.parent.name
    rel_path = f"aicp:skills/{skill_name}/SKILL.md"

    entities = []
    relationships = []

    # Extract frontmatter
    description = ""
    effort = ""
    allowed_tools = []

    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            if line.startswith("description:"):
                description = line.split(":", 1)[1].strip()
            elif line.startswith("effort:"):
                effort = line.split(":", 1)[1].strip()
            elif line.startswith("allowed-tools:"):
                allowed_tools = [t.strip() for t in line.split(":", 1)[1].split(",")]

    # Extract process steps for richer description
    process = ""
    in_process = False
    for line in lines:
        if re.match(r"^#{1,3}\s+Process", line):
            in_process = True
            continue
        elif in_process and re.match(r"^#{1,3}\s+", line):
            break
        elif in_process and line.strip():
            process += line.strip() + " "
    if process:
        description += " " + process[:200]

    entities.append(Entity(
        name=skill_name,
        entity_type="skill",
        description=f"{description.strip()[:400]} Effort: {effort}.",
        source_file=rel_path,
    ))

    # Allowed tools → USES relationships
    for tool in allowed_tools:
        tool = tool.strip()
        if tool and len(tool) > 1:
            relationships.append(Relationship(
                src=skill_name, tgt=tool,
                rel_type="uses tool",
                description=f"Skill {skill_name} uses {tool}",
                source_file=rel_path,
                weight=0.8,
            ))

    # Detect fleet tool references in the process
    for m in re.finditer(r"\bfleet_(\w+)\b", text):
        tool = f"fleet_{m.group(1)}"
        relationships.append(Relationship(
            src=skill_name, tgt=tool,
            rel_type="calls",
            description=f"Skill {skill_name} calls {tool}",
            source_file=rel_path,
            weight=1.0,
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

    # Systems: S01-S22 — high value references (weight 1.5)
    seen_systems = set()
    for m in re.finditer(r"S(\d{2})\b|System (\d{1,2})\b", text):
        sys_num = (m.group(1) or m.group(2)).zfill(2)
        if sys_num not in seen_systems:
            seen_systems.add(sys_num)
            relationships.append(Relationship(
                src=title, tgt=f"S{sys_num}",
                rel_type="references system",
                description=f"{title} references system S{sys_num}",
                source_file=rel_path,
                weight=1.5,
            ))

    # Tools: fleet_xxx — medium value (weight 1.0)
    seen_tools = set()
    for m in re.finditer(r"\bfleet_(\w+)\b", text):
        tool_name = f"fleet_{m.group(1)}"
        if tool_name not in seen_tools:
            seen_tools.add(tool_name)
            relationships.append(Relationship(
                src=title, tgt=tool_name,
                rel_type="references tool",
                description=f"{title} references tool {tool_name}",
                source_file=rel_path,
                weight=1.0,
            ))

    # Agents — medium value (weight 1.0), only if mentioned substantively (3+ times)
    for agent in ["architect", "software-engineer", "qa-engineer", "devops",
                   "devsecops-expert", "fleet-ops", "project-manager",
                   "technical-writer", "ux-designer", "accountability-generator"]:
        count = text.lower().count(agent)
        if count >= 3:  # substantive mention, not just passing
            relationships.append(Relationship(
                src=title, tgt=agent,
                rel_type="discusses",
                description=f"{title} discusses agent {agent} ({count} mentions)",
                source_file=rel_path,
                weight=min(1.0 + count * 0.1, 2.0),
            ))

    # Modules: xxx.py — low value (weight 0.5), skip common names
    skip_modules = {"setup.py", "__init__.py", "conftest.py", "test.py",
                    "main.py", "run.py", "manage.py", "wsgi.py"}
    seen_modules = set()
    for m in re.finditer(r"\b(\w+\.py)\b", text):
        module = m.group(1)
        if module not in skip_modules and module not in seen_modules:
            seen_modules.add(module)
            relationships.append(Relationship(
                src=title, tgt=module,
                rel_type="references module",
                description=f"{title} references module {module}",
                source_file=rel_path,
                weight=0.5,
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
