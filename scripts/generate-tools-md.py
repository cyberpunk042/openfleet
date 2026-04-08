#!/usr/bin/env python3
"""Generate per-agent TOOLS.md from all 7 capability layers.

Reads:
  fleet/mcp/tools.py             — generic tool names + docstrings
  fleet/mcp/roles/*.py           — role-specific group call names + docstrings
  config/tool-chains.yaml        — chain docs for generic tools
  config/agent-tooling.yaml      — MCP servers, plugins, skills, sub-agents per role
  config/skill-stage-mapping.yaml — stage-aware skill recommendations
  config/agent-crons.yaml        — scheduled CRON jobs per role
  config/standing-orders.yaml    — autonomous authority per role
  config/agent-hooks.yaml        — hooks per role
  config/agent-identities.yaml   — display names
  .claude/agents/*.md            — sub-agent descriptions

Produces:
  agents/{name}/TOOLS.md         — complete, 7-layer tool reference per agent

Usage:
  python scripts/generate-tools-md.py              # all agents
  python scripts/generate-tools-md.py architect     # single agent
"""

import ast
import os
import re
import sys
from pathlib import Path

import yaml

FLEET_DIR = Path(__file__).resolve().parent.parent
CONFIG = FLEET_DIR / "config"
AGENTS_DIR = FLEET_DIR / "agents"
ROLES_DIR = FLEET_DIR / "fleet" / "mcp" / "roles"
SUBAGENTS_DIR = FLEET_DIR / ".claude" / "agents"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ── Extract tool info from Python source ────────────────────────────

def extract_tools_from_py(path: Path) -> list[dict]:
    """Extract tool names and docstrings from a Python file."""
    if not path.exists():
        return []
    with open(path) as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    tools = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            name = node.name
            if name.startswith("fleet_") or name.startswith(("pm_", "ops_", "arch_",
                    "sec_", "eng_", "devops_", "qa_", "writer_", "ux_", "acct_")):
                doc = ast.get_docstring(node) or ""
                tools.append({"name": name, "doc": doc})
    return tools


def extract_role_tools(role_name: str) -> list[dict]:
    """Extract tools from the role-specific module."""
    # Map role names to file names
    file_map = {
        "project-manager": "pm.py",
        "fleet-ops": "fleet_ops.py",
        "architect": "architect.py",
        "devsecops-expert": "devsecops.py",
        "software-engineer": "engineer.py",
        "devops": "devops.py",
        "qa-engineer": "qa.py",
        "technical-writer": "writer.py",
        "ux-designer": "ux.py",
        "accountability-generator": "accountability.py",
    }
    filename = file_map.get(role_name)
    if not filename:
        return []
    path = ROLES_DIR / filename
    return extract_tools_from_py(path)


# ── Sub-agent description extraction ────────────────────────────────

def get_subagent_info(name: str) -> dict:
    """Read sub-agent frontmatter for description and model."""
    path = SUBAGENTS_DIR / f"{name}.md"
    if not path.exists():
        return {"description": "", "model": ""}
    with open(path) as f:
        content = f.read()
    if not content.startswith("---"):
        return {"description": "", "model": ""}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"description": "", "model": ""}
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {"description": "", "model": ""}
    return {
        "description": meta.get("description", "").strip(),
        "model": meta.get("model", ""),
    }


# ── Format tool docstring into TOOLS.md entry ──────────────────────

def format_tool_doc(name: str, doc: str, chain_info: dict | None = None) -> str:
    """Format a tool entry for TOOLS.md."""
    lines = [f"### {name}"]

    if chain_info:
        # Use chain docs from tool-chains.yaml
        if chain_info.get("what"):
            lines.append(f"**What:** {chain_info['what']}")
        if chain_info.get("when"):
            lines.append(f"**When:** {chain_info['when']}")
        if chain_info.get("chain"):
            lines.append(f"**Chain:** {chain_info['chain']}")
        elif chain_info.get("chain_approve"):
            lines.append(f"**Chain (approve):** {chain_info['chain_approve']}")
            lines.append(f"**Chain (reject):** {chain_info.get('chain_reject', '')}")
        if chain_info.get("input"):
            lines.append(f"**Input:** {chain_info['input']}")
        if chain_info.get("auto"):
            lines.append(f"**You do NOT need to:** {chain_info['auto']}")
        if chain_info.get("blocked"):
            lines.append(f"**{chain_info['blocked']}**")
    elif doc:
        # Extract first line as description, rest as detail
        doc_lines = doc.strip().split("\n")
        first_line = doc_lines[0].strip()
        lines.append(f"**What:** {first_line}")

        # Extract tree if present
        tree_lines = []
        in_tree = False
        for dl in doc_lines[1:]:
            stripped = dl.strip()
            if stripped.startswith("Tree:"):
                in_tree = True
                continue
            if in_tree:
                if stripped and (stripped[0].isdigit() or stripped.startswith("-")):
                    tree_lines.append(stripped)
                elif not stripped:
                    continue
                else:
                    in_tree = False
        if tree_lines:
            lines.append("**Chain:**")
            for tl in tree_lines:
                lines.append(f"  {tl}")
    else:
        lines.append("*(documentation pending)*")

    lines.append("")
    return "\n".join(lines)


# ── Main generator ──────────────────────────────────────────────────

def generate_tools_md(agent_name: str) -> str:
    """Generate complete TOOLS.md content for an agent."""

    # Load all configs
    tooling = load_yaml(CONFIG / "agent-tooling.yaml")
    chains = load_yaml(CONFIG / "tool-chains.yaml")
    identities = load_yaml(CONFIG / "agent-identities.yaml")
    skill_mapping = load_yaml(CONFIG / "skill-stage-mapping.yaml")
    crons_config = load_yaml(CONFIG / "agent-crons.yaml")
    standing_orders = load_yaml(CONFIG / "standing-orders.yaml")
    hooks_config = load_yaml(CONFIG / "agent-hooks.yaml")

    # Display name
    display_name = (identities.get("agents", {})
                    .get(agent_name, {})
                    .get("display_name", agent_name.replace("-", " ").title()))

    # Agent-specific config from agent-tooling.yaml
    defaults = tooling.get("defaults", {})
    agent_config = tooling.get("agents", {}).get(agent_name, {})
    chain_tools = chains.get("tools", {})

    sections = []

    # ── Header ──────────────────────────────────────────────────
    sections.append(f"# Tools — {display_name}\n")
    sections.append(f"> `AGENT_NAME={agent_name}`\n")

    # ── 1. Generic Fleet MCP Tools ──────────────────────────────
    generic_tools = extract_tools_from_py(FLEET_DIR / "fleet" / "mcp" / "tools.py")
    if generic_tools:
        tool_entries = []
        for tool in generic_tools:
            chain_info = chain_tools.get(tool["name"])
            tool_entries.append(format_tool_doc(tool["name"], tool["doc"], chain_info))
        sections.append("## Fleet MCP Tools\n")
        sections.append("\n".join(tool_entries))

    # ── 2. Role-Specific Group Calls ────────────────────────────
    role_tools = extract_role_tools(agent_name)
    if role_tools:
        sections.append("## Role-Specific Tools\n")
        sections.append(f"These tools are exclusive to the {display_name} role.\n")
        tool_entries = []
        for tool in role_tools:
            tool_entries.append(format_tool_doc(tool["name"], tool["doc"]))
        sections.append("\n".join(tool_entries))

    # ── 3. MCP Servers ──────────────────────────────────────────
    mcp_lines = ["## MCP Servers\n"]
    mcp_lines.append("- fleet (all fleet tools)")
    for srv in agent_config.get("mcp_servers", []):
        name = srv.get("name", "unknown")
        pkg = srv.get("package", srv.get("command", ""))
        mcp_lines.append(f"- {name} ({pkg})")
    sections.append("\n".join(mcp_lines) + "\n")

    # ── 4. Plugins ──────────────────────────────────────────────
    default_plugins = defaults.get("plugins", [])
    role_plugins = agent_config.get("plugins", [])
    all_plugins = default_plugins + role_plugins
    if all_plugins:
        plugin_lines = ["## Plugins\n"]
        for p in all_plugins:
            plugin_lines.append(f"- {p}")
        sections.append("\n".join(plugin_lines) + "\n")

    # ── 5. Skills ───────────────────────────────────────────────
    skills_section = ["## Skills\n"]

    # Stage-aware recommendations from skill-stage-mapping.yaml
    generic_mapping = skill_mapping.get("generic", {})
    role_mapping = skill_mapping.get("roles", {}).get(agent_name, {})

    stages = ["conversation", "analysis", "investigation", "reasoning", "work"]
    has_stage_recs = False

    for stage in stages:
        recs = []
        # Generic for this stage
        generic_stage = generic_mapping.get(stage, {})
        if isinstance(generic_stage, dict):
            for r in generic_stage.get("recommended", []):
                recs.append(f"  - /{r['skill']} — {r.get('why', '')}")
            for r in generic_stage.get("plugin_recommended", []):
                recs.append(f"  - /{r['skill']} ({r.get('plugin', '')}) — {r.get('why', '')}")

        # Role-specific for this stage
        role_stage = role_mapping.get(stage, [])
        if isinstance(role_stage, list):
            for r in role_stage:
                recs.append(f"  - /{r['skill']} — {r.get('why', '')}")

        # Generic all_stages
        if stage == stages[0]:  # only show all_stages once
            generic_all = generic_mapping.get("all_stages", {})
            if isinstance(generic_all, dict):
                for r in generic_all.get("recommended", []):
                    recs.insert(0, f"  - /{r['skill']} — {r.get('why', '')}")
            role_all = role_mapping.get("all_stages", [])
            if isinstance(role_all, list):
                for r in role_all:
                    recs.insert(0, f"  - /{r['skill']} — {r.get('why', '')}")

        if recs:
            has_stage_recs = True
            skills_section.append(f"### {stage.title()} Stage")
            skills_section.extend(recs)
            skills_section.append("")

    # Plugin skills
    plugin_skills = role_mapping.get("plugin_skills", [])
    if plugin_skills:
        skills_section.append("### Plugin Skills")
        for ps in plugin_skills:
            stage_info = ps.get("stage", "all")
            if isinstance(stage_info, list):
                stage_info = ", ".join(stage_info)
            skills_section.append(
                f"  - /{ps['skill']} ({ps.get('plugin', '')}, {stage_info}) — {ps.get('why', '')}"
            )
        skills_section.append("")

    # Marketplace skills from agent-tooling.yaml
    marketplace = defaults.get("skills", []) + agent_config.get("skills", [])
    if marketplace:
        skills_section.append("### Available Slash Commands")
        for s in marketplace:
            skills_section.append(f"  - /{s}")
        skills_section.append("")

    if has_stage_recs or plugin_skills or marketplace:
        sections.append("\n".join(skills_section))

    # ── 6. Sub-Agents ───────────────────────────────────────────
    default_subs = defaults.get("sub_agents", [])
    role_subs = agent_config.get("sub_agents", [])
    all_subs = default_subs + [s for s in role_subs if s not in default_subs]
    if all_subs:
        sub_lines = ["## Sub-Agents\n"]
        sub_lines.append("Launch these for isolated work that would bloat your context:\n")
        for sa in all_subs:
            info = get_subagent_info(sa)
            desc = info["description"] or "(no description)"
            model = info["model"]
            sub_lines.append(f"- **{sa}** (model: {model}) — {desc}")
        sub_lines.append("")
        sections.append("\n".join(sub_lines))

    # ── 7. CRONs ───────────────────────────────────────────────
    agent_crons = crons_config.get(agent_name, [])
    if isinstance(agent_crons, list) and agent_crons:
        cron_lines = ["## Scheduled Operations (CRONs)\n"]
        cron_lines.append("These run automatically on schedule:\n")
        for job in agent_crons:
            name = job.get("name", "unnamed")
            schedule = job.get("schedule", "")
            model = job.get("model", "sonnet")
            msg_preview = job.get("message", "").strip().split("\n")[0][:80]
            cron_lines.append(f"- **{name}** (`{schedule}`, model: {model}) — {msg_preview}")
        cron_lines.append("")
        sections.append("\n".join(cron_lines))

    # ── 8. Standing Orders ──────────────────────────────────────
    role_orders = standing_orders.get(agent_name, {})
    so_list = role_orders.get("standing_orders", [])
    authority = role_orders.get("authority_level", standing_orders.get("defaults", {}).get("authority_level", "conservative"))
    if so_list:
        so_lines = [f"## Standing Orders (authority: {authority})\n"]
        so_lines.append("You are authorized to act on these WITHOUT explicit task assignment:\n")
        for order in so_list:
            name = order.get("name", "unnamed")
            desc = order.get("description", "")
            when = order.get("when", "")
            boundary = order.get("boundary", "")
            so_lines.append(f"- **{name}**: {desc}")
            so_lines.append(f"  - When: {when}")
            so_lines.append(f"  - Boundary: {boundary}")
        so_lines.append("")
        sections.append("\n".join(so_lines))

    # ── 9. Hooks (Structural Enforcement) ───────────────────────
    default_hooks = hooks_config.get("defaults", {})
    role_hooks = hooks_config.get("roles", {}).get(agent_name, {})
    hook_entries = []
    for event_type in ["PreToolUse", "PostToolUse", "SessionStart"]:
        for hook in default_hooks.get(event_type, []):
            hook_entries.append((event_type, hook))
        for hook in role_hooks.get(event_type, []):
            hook_entries.append((event_type, hook))

    if hook_entries:
        hook_lines = ["## Hooks (Structural Enforcement)\n"]
        hook_lines.append("These fire automatically on your tool calls — you cannot bypass them:\n")
        for event_type, hook in hook_entries:
            matcher = hook.get("matcher", "*")
            desc = hook.get("description", "")
            hook_lines.append(f"- **{event_type}** on `{matcher}`: {desc}")
        hook_lines.append("")
        sections.append("\n".join(hook_lines))

    return "\n".join(sections)


def main():
    tooling = load_yaml(CONFIG / "agent-tooling.yaml")
    agents = list(tooling.get("agents", {}).keys())

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target not in agents:
            print(f"Unknown agent: {target}")
            print(f"Available: {', '.join(agents)}")
            sys.exit(1)
        agents = [target]

    print("=" * 55)
    print("  Generate TOOLS.md — all 7 capability layers")
    print("=" * 55)
    print()

    for agent_name in agents:
        agent_dir = AGENTS_DIR / agent_name
        if not agent_dir.exists():
            print(f"  [skip] {agent_name}: no agents/{agent_name}/ directory")
            continue

        content = generate_tools_md(agent_name)
        tools_path = agent_dir / "TOOLS.md"

        # Check if changed
        if tools_path.exists():
            existing = tools_path.read_text()
            if existing == content:
                print(f"  [skip] {agent_name}: unchanged")
                continue
            print(f"  [updated] {agent_name}")
        else:
            print(f"  [created] {agent_name}")

        tools_path.write_text(content)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
