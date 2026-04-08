#!/usr/bin/env python3
"""Generate per-agent AGENTS.md — fleet awareness from configs.

Reads:
  config/synergy-matrix.yaml     — who contributes what to whom
  config/standing-orders.yaml    — what each agent does autonomously
  config/agent-crons.yaml        — scheduled operations per role
  config/agent-identities.yaml   — display names

Produces:
  agents/{name}/AGENTS.md        — team awareness per agent

Each agent sees: who they contribute TO, who contributes TO THEM,
what each colleague does (standing orders, CRONs), and when to
@mention each agent.

Usage:
  python scripts/generate-agents-md.py              # all agents
  python scripts/generate-agents-md.py architect     # single agent
"""

import sys
from pathlib import Path

import yaml

FLEET_DIR = Path(__file__).resolve().parent.parent
CONFIG = FLEET_DIR / "config"
AGENTS_DIR = FLEET_DIR / "agents"

AGENT_ROSTER = [
    "architect", "software-engineer", "qa-engineer", "devops",
    "devsecops-expert", "fleet-ops", "project-manager",
    "technical-writer", "ux-designer", "accountability-generator",
]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def generate_agents_md(agent_name: str) -> str:
    identities = load_yaml(CONFIG / "agent-identities.yaml")
    synergy = load_yaml(CONFIG / "synergy-matrix.yaml")
    orders_config = load_yaml(CONFIG / "standing-orders.yaml")
    crons_config = load_yaml(CONFIG / "agent-crons.yaml")

    contributions = synergy.get("contributions", {})

    def display(name: str) -> str:
        return (identities.get("agents", {})
                .get(name, {})
                .get("display_name", name.replace("-", " ").title()))

    # Build contribution maps
    # i_contribute_to: {target_agent: [{type, priority, description}]}
    i_contribute_to: dict[str, list] = {}
    # they_contribute_to_me: {source_agent: [{type, priority, description}]}
    they_contribute_to_me: dict[str, list] = {}

    for target_agent, contribs in contributions.items():
        for c in contribs:
            source_role = c.get("role", "")
            ctype = c.get("type", "")
            priority = c.get("priority", "")
            desc = c.get("description", "")
            condition = c.get("condition", "")

            if source_role == agent_name:
                # I contribute TO target_agent
                if target_agent not in i_contribute_to:
                    i_contribute_to[target_agent] = []
                entry = {"type": ctype, "priority": priority, "description": desc}
                if condition:
                    entry["condition"] = condition
                i_contribute_to[target_agent].append(entry)

            if target_agent == agent_name:
                # source_role contributes TO me
                if source_role not in they_contribute_to_me:
                    they_contribute_to_me[source_role] = []
                entry = {"type": ctype, "priority": priority, "description": desc}
                if condition:
                    entry["condition"] = condition
                they_contribute_to_me[source_role].append(entry)

    lines = [f"# Fleet Awareness — {display(agent_name)}\n"]

    # My contribution relationships
    lines.append("## Contribution Relationships\n")

    if they_contribute_to_me:
        lines.append("### They Contribute to Me")
        lines.append("Before my tasks enter work stage, I receive:\n")
        for source, contribs in sorted(they_contribute_to_me.items()):
            for c in contribs:
                priority_tag = f" ({c['priority']})" if c["priority"] else ""
                cond = f" — *when: {c['condition']}*" if c.get("condition") else ""
                lines.append(
                    f"- **{c['type']}** from {display(source)}{priority_tag}: "
                    f"{c['description']}{cond}"
                )
        lines.append("")
    else:
        lines.append("*(No direct contributions to me — I receive input contextually.)*\n")

    if i_contribute_to:
        lines.append("### I Contribute To")
        lines.append("When contribution tasks are assigned, I provide:\n")
        for target, contribs in sorted(i_contribute_to.items()):
            for c in contribs:
                priority_tag = f" ({c['priority']})" if c["priority"] else ""
                cond = f" — *when: {c['condition']}*" if c.get("condition") else ""
                lines.append(
                    f"- **{c['type']}** to {display(target)}{priority_tag}: "
                    f"{c['description']}{cond}"
                )
        lines.append("")
    else:
        lines.append("*(No direct contributions from me — my work is standalone.)*\n")

    # Fleet colleagues
    lines.append("## Fleet Colleagues\n")

    for colleague in AGENT_ROSTER:
        if colleague == agent_name:
            continue

        col_display = display(colleague)
        col_lines = [f"### {col_display} — `{colleague}`"]

        # What they do (standing orders summary)
        col_orders = orders_config.get(colleague, {})
        so_list = col_orders.get("standing_orders", [])
        authority = col_orders.get("authority_level", "conservative")

        if so_list:
            col_lines.append(f"**Authority:** {authority}")
            duties = [o.get("description", o.get("name", "")) for o in so_list[:3]]
            col_lines.append(f"**Duties:** {'; '.join(duties)}")

        # CRONs (what they run on schedule)
        col_crons = crons_config.get(colleague, [])
        if isinstance(col_crons, list) and col_crons:
            cron_names = [j.get("name", "") for j in col_crons[:3]]
            col_lines.append(f"**Scheduled:** {', '.join(cron_names)}")

        # Contribution relationship to/from me
        my_contribs_to_them = i_contribute_to.get(colleague, [])
        their_contribs_to_me = they_contribute_to_me.get(colleague, [])

        if my_contribs_to_them:
            types = [c["type"] for c in my_contribs_to_them]
            col_lines.append(f"**I provide:** {', '.join(types)}")
        if their_contribs_to_me:
            types = [c["type"] for c in their_contribs_to_me]
            col_lines.append(f"**They provide:** {', '.join(types)}")
        if not my_contribs_to_them and not their_contribs_to_me:
            col_lines.append("**Relationship:** fleet colleague (no direct contributions)")

        # When to @mention
        mention_guide = _get_mention_guide(agent_name, colleague)
        if mention_guide:
            col_lines.append(f"**@mention when:** {mention_guide}")

        col_lines.append("")
        lines.extend(col_lines)

    # How to create contribution tasks
    lines.append("## Creating Contribution Tasks\n")
    lines.append("When you need input from a colleague, create a contribution task:")
    lines.append("```")
    lines.append("fleet_task_create(")
    lines.append('  title="{contribution_type} for: {task_title}",')
    lines.append('  agent_name="{colleague_agent_name}",')
    lines.append('  task_type="subtask",')
    lines.append('  parent_task="{your_task_id}"')
    lines.append(")")
    lines.append("```")
    lines.append("Or use `fleet_request_input(task_id, role, question)` for quick requests.\n")

    return "\n".join(lines)


def _get_mention_guide(me: str, them: str) -> str:
    """Context-appropriate @mention guidance."""
    guides = {
        "project-manager": "blocked, scope unclear, need assignment, sprint question",
        "fleet-ops": "review pending, compliance question, quality concern",
        "architect": "design question, pattern decision, architectural impact",
        "software-engineer": "implementation question, feasibility check, code context needed",
        "qa-engineer": "test criteria unclear, acceptance criteria question",
        "devsecops-expert": "security concern, vulnerability found, auth question",
        "devops": "infrastructure need, CI/CD issue, deployment question",
        "technical-writer": "documentation needed, API reference question",
        "ux-designer": "UX spec unclear, interaction question, accessibility concern",
        "accountability-generator": "compliance question, trail gap",
    }
    return guides.get(them, "")


def main():
    agents = AGENT_ROSTER[:]

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target not in agents:
            print(f"Unknown agent: {target}")
            sys.exit(1)
        agents = [target]

    print("=" * 55)
    print("  Generate AGENTS.md — fleet awareness from configs")
    print("=" * 55)
    print()

    for agent_name in agents:
        agent_dir = AGENTS_DIR / agent_name
        if not agent_dir.exists():
            print(f"  [skip] {agent_name}: no directory")
            continue

        content = generate_agents_md(agent_name)
        agents_path = agent_dir / "AGENTS.md"

        if agents_path.exists():
            existing = agents_path.read_text()
            if existing == content:
                print(f"  [skip] {agent_name}: unchanged")
                continue
            print(f"  [updated] {agent_name}")
        else:
            print(f"  [created] {agent_name}")

        agents_path.write_text(content)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
