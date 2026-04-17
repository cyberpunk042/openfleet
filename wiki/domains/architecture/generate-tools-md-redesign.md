---
title: "generate-tools-md.py Redesign — Algorithm Specification"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, generation-pipeline, tools-md, algorithm, IaC]
sources:
  - id: generate-tools-md
    type: documentation
    file: scripts/generate-tools-md.py
  - id: tool-roles
    type: documentation
    file: config/tool-roles.yaml
  - id: tool-chains
    type: documentation
    file: config/tool-chains.yaml
epic: E001
phase: "1 — Design"
---

# generate-tools-md.py Redesign — Algorithm Specification

## Summary

Algorithm specification for the redesigned generate-tools-md.py. Today's script produces 15–18K-char TOOLS.md per agent in 9 sections — over the gateway truncation threshold and mixed in role-irrelevant content. The redesign reshapes into focused desk + detail-on-demand structure aligned with tier-aware loading.

## Current Algorithm (9 sections, produces 15-18K)

```
1. Header (agent name)
2. ALL 26+ generic tools from tools.py (with chain docs from tool-chains.yaml)
   → merged with role-specific descriptions from tool-roles.yaml when available
3. Role group calls from fleet/mcp/roles/{role}.py
4. MCP servers from agent-tooling.yaml (with package names)
5. Plugins from agent-tooling.yaml (names + defaults)
6. Skills per stage from skill-stage-mapping.yaml (~3K of descriptions)
7. Sub-agents from .claude/agents/ (full descriptions from frontmatter)
8. CRONs from agent-crons.yaml
9. Standing orders from standing-orders.yaml
10. Hooks from agent-hooks.yaml
```

**Problem:** Section 2 dumps ALL generic tools for every agent. Section 6 is ~3K of skill descriptions. Sections 7-10 add content that belongs elsewhere.

## Redesigned Algorithm (5 sections, produces 2-4K)

```
INPUT:
  - config/tool-roles.yaml (PRIMARY FILTER — which tools this role uses)
  - config/tool-chains.yaml (chain docs for those tools only)
  - fleet/mcp/roles/{role}.py (role group calls via AST extraction)
  - config/agent-tooling.yaml (MCP server + plugin NAMES only)
  - config/standing-orders.yaml (brief authority statement)

OUTPUT per agent:
  1. Header
  2. Tools THIS role uses (filtered by tool-roles.yaml + cross-role)
  3. Role group calls (from roles/*.py)
  4. Available tooling (MCP servers + plugins — names only)
  5. Boundaries + standing orders (brief)
```

## Detailed Algorithm

### Step 1: Load configs

```python
tool_roles = load_yaml("config/tool-roles.yaml")
chains = load_yaml("config/tool-chains.yaml")
tooling = load_yaml("config/agent-tooling.yaml")
standing = load_yaml("config/standing-orders.yaml")
identities = load_yaml("config/agent-identities.yaml")
```

### Step 2: Resolve agent's tool set

```python
# Primary tools from tool-roles.yaml
agent_tools = tool_roles[agent_name]["tools"]  # dict of tool_name → {usage, when, note}

# Cross-role tools where this agent is listed
cross_role = tool_roles.get("_cross_role_tools", {})
for tool_name, desc in cross_role.items():
    if agent_name in desc.get("roles", []):
        agent_tools[tool_name] = desc

# Result: agent_tools is the COMPLETE set of generic tools this agent uses
```

### Step 3: Format tools with role-specific descriptions

For each tool in agent_tools:

```python
def format_focused_tool(name, role_desc, chain_info):
    """Format a tool for the focused TOOLS.md.
    
    Uses role-specific usage/when from tool-roles.yaml.
    Adds chain summary from tool-chains.yaml.
    Adds critical notes (BLOCKED, special behavior).
    """
    lines = [f"### {name}"]
    
    # Role-specific description (NOT generic docstring)
    usage = role_desc.get("usage", "")
    when = role_desc.get("when", "")
    lines.append(usage)
    if when:
        lines.append(f"**When:** {when}")
    
    # Chain awareness (one line)
    if chain_info:
        chain = chain_info.get("chain", "")
        if chain:
            lines.append(f"**→** {chain}")
    
    # Critical notes
    note = role_desc.get("note", "")
    if note:
        lines.append(f"_{note}_")
    
    # Blocked indicator from chain doc
    if chain_info and chain_info.get("blocked"):
        lines.append(f"**{chain_info['blocked']}**")
    
    return "\n".join(lines) + "\n"
```

**Format per tool: 3-5 lines. ~80-120 chars.** Role-specific, not generic.

### Step 4: Extract and format role group calls

```python
role_tools = extract_tools_from_py(ROLES_DIR / role_file_map[agent_name])
for tool in role_tools:
    # Use docstring first line as description
    # Use "Tree:" section if present as chain
    format_focused_tool(tool["name"], {...}, role_chain_info)
```

### Step 5: Format available tooling (names only)

```python
# MCP servers — just names
mcp_names = ["fleet"] + [s["name"] for s in agent_config.get("mcp_servers", [])]

# Plugins — just names
all_plugins = defaults.get("plugins", []) + agent_config.get("plugins", [])
```

Output:
```markdown
## Available
MCP: fleet · filesystem · github · playwright
Plugins: claude-mem · safety-net · context7 · superpowers · pyright-lsp
```

~200 chars total. No descriptions. Agent knows what these do from the tools themselves.

### Step 6: Format boundaries + standing orders

```python
# Boundaries: hardcoded per role based on fleet-elevation specs
# These define what the agent does NOT do
boundaries = get_role_boundaries(agent_name)

# Standing orders: brief authority statement
authority = standing.get(agent_name, {}).get("authority_level", "conservative")
orders = standing.get(agent_name, {}).get("standing_orders", [])
```

Output:
```markdown
## Boundaries
- Architecture decisions → architect
- Test predefinition → qa-engineer
- Work approval → fleet-ops

## Standing Orders (conservative)
- work-assigned-tasks: Execute confirmed plans in work stage. No scope addition.
```

~300 chars. Brief. Essential.

## What's NOT Generated (moved to Navigator/removed)

| Previously Generated | Reason for Removal | Where It Goes |
|---------------------|-------------------|---------------|
| Skills per stage (§6, ~3K) | Dynamic — changes per stage | Navigator → knowledge-context.md |
| Sub-agent descriptions (§7, ~500) | Only relevant in specific stages | Navigator → knowledge-context.md |
| CRON documentation (§8, ~300) | CRONs run in isolated sessions | Removed entirely |
| Hook detail (§10, ~400) | Hooks self-teach via error messages | Removed entirely |
| Plugin descriptions | Agent knows plugins from gateway | Names only kept |
| Tools agent doesn't use | Noise — PM doesn't need fleet_commit docs | Filtered by tool-roles.yaml |

## Boundary Definitions Per Role

These are hardcoded in the generator (from fleet-elevation specs) because they're stable:

```python
ROLE_BOUNDARIES = {
    "project-manager": [
        "Implementation → software-engineer, devops",
        "Design decisions → architect",
        "Security decisions → devsecops-expert",
        "Work approval → fleet-ops",
        "PO gates → fleet_gate_request, don't decide",
    ],
    "fleet-ops": [
        "Task assignment → project-manager",
        "Implementation → software-engineer",
        "Design → architect",
        "PO decisions → escalate, don't decide",
    ],
    "architect": [
        "Implementation → software-engineer (transfer after design)",
        "Test predefinition → qa-engineer",
        "Security review → devsecops-expert",
        "Task assignment → project-manager",
    ],
    "devsecops-expert": [
        "Implementation → software-engineer",
        "Architecture → architect",
        "Task assignment → project-manager",
        "Work approval → fleet-ops (security_hold is separate)",
    ],
    "software-engineer": [
        "Architecture decisions → architect",
        "Test predefinition → qa-engineer",
        "Work approval → fleet-ops",
        "Security decisions → devsecops-expert",
        "Missing contributions → fleet_request_input, don't skip",
    ],
    "devops": [
        "Architecture decisions → architect",
        "Security decisions → devsecops-expert",
        "Work approval → fleet-ops",
        "Task assignment → project-manager",
    ],
    "qa-engineer": [
        "Implementation → software-engineer",
        "Architecture decisions → architect",
        "Work approval → fleet-ops",
        "Task assignment → project-manager",
    ],
    "technical-writer": [
        "Implementation → software-engineer",
        "Architecture decisions → architect",
        "Work approval → fleet-ops",
        "Technical accuracy → verify with engineer before publishing",
    ],
    "ux-designer": [
        "Implementation → software-engineer",
        "Architecture decisions → architect",
        "Work approval → fleet-ops",
        "UX at ALL levels — not just UI",
    ],
    "accountability-generator": [
        "Enforcement → feed immune system, don't enforce directly",
        "Task assignment → project-manager",
        "Work approval → fleet-ops",
        "Verify process, not quality (quality is fleet-ops)",
    ],
}
```

## Size Projections

Based on tool counts from tool-roles.yaml + cross-role tools:

| Agent | Tools | Group Calls | Est. Tool Section | + Available + Boundaries | Total |
|-------|-------|-------------|-------------------|-------------------------|-------|
| project-manager | 18 | 5 | ~1800 | ~500 | ~2300 |
| fleet-ops | 11 | 4 | ~1200 | ~400 | ~1600 |
| architect | 15 | 4 | ~1500 | ~500 | ~2000 |
| devsecops-expert | 11 | 6 | ~1400 | ~400 | ~1800 |
| software-engineer | 14 | 2 | ~1300 | ~500 | ~1800 |
| devops | 11 | 4 | ~1200 | ~400 | ~1600 |
| qa-engineer | 12 | 4 | ~1300 | ~400 | ~1700 |
| technical-writer | 11 | 2 | ~1000 | ~400 | ~1400 |
| ux-designer | 9 | 2 | ~900 | ~400 | ~1300 |
| accountability | 6 | 3 | ~750 | ~400 | ~1150 |

**All within 2-4K target.** Average: ~1,770 chars. Down from ~17K average.

## Implementation Notes

1. **Backward compatible:** The script still reads the same config files. It just filters differently.
2. **Testable:** Output can be validated against tool-roles.yaml (every listed tool must appear).
3. **IaC:** `make agents-push` regenerates and deploys. Same pipeline, different output.
4. **Reversible:** Old generator can be kept as generate-tools-md-full.py for reference.

## Relationships

- PART_OF: E001 Phase 2 (Scaffold — rewrite the script)
- DEPENDS_ON: tool-roles.yaml being complete (verified: it is)
- FEEDS_INTO: TOOLS.md per agent (the output)
- VALIDATED_BY: fleet/tests/integration/test_end_to_end_pipeline.py (update tests)
