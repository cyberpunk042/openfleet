---
title: "TOOLS.md Redesign — Focused Desk, Detail On-Demand"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, tools-md, generation-pipeline, navigator, autocomplete, injection, focused]
sources:
  - id: tool-roles
    type: documentation
    file: config/tool-roles.yaml
  - id: source
    type: documentation
    file: fleet/mcp/roles/*.py
  - id: generate-tools-md
    type: documentation
    file: scripts/generate-tools-md.py
  - id: intent-map
    type: documentation
    file: docs/knowledge-map/intent-map.yaml
epic: E001
phase: "1 — Design"
---

# TOOLS.md Redesign — Focused Desk, Detail On-Demand

## Summary

Redesign of per-agent TOOLS.md to end the 15–18K-char bloat that exceeds the gateway injection threshold and stuffs role-irrelevant content into every agent's context. Target: focused desk (essential commands, current-cycle tooling) plus detail-on-demand pointers — tier-aware, role-aware, mode-aware.

## PO Directive

> "we do not want to flood our agent with things it doesn't need to know... bloated files are still sign that there might be something wrong"

> "the AI assistant does not need to know every single tools but only a few group calls and then if he need to know more he gets it per-case via skills or other injection"

## Problem

Current TOOLS.md per agent: **15,110 — 18,215 chars** (10 agents).

| Agent | Current Chars | Tools Documented |
|-------|--------------|-----------------|
| devsecops-expert | 18,215 | 26 generic + 2 role + all layers |
| architect | 18,041 | 26 generic + 2 role + all layers |
| fleet-ops | 18,004 | 26 generic + 4 role + all layers |
| project-manager | 17,979 | 26 generic + 2 role + all layers |
| qa-engineer | 17,683 | 26 generic + 2 role + all layers |
| software-engineer | 17,251 | 26 generic + 2 role + all layers |
| devops | 17,249 | 26 generic + 2 role + all layers |
| accountability | 16,031 | 26 generic + 2 role + all layers |
| technical-writer | 15,420 | 26 generic + 1 role + all layers |
| ux-designer | 15,110 | 26 generic + 2 role + all layers |

Every agent receives documentation for ALL 26 generic tools (6K chars identical across all) regardless of whether they use them. Engineer sees fleet_approve chain docs. PM sees fleet_commit chain docs. Accountability sees fleet_plane_create_issue docs.

On top of that: ~3K of skill descriptions per stage, ~500 of sub-agent descriptions, ~400 of hook docs, ~300 of CRON docs, ~300 of standing orders. All of this is "the manual next to you" when you only need "the reference card."

## Design Principle: Three Layers

| Layer | What | Size | When |
|-------|------|------|------|
| **Desk** (TOOLS.md) | Tools THIS role calls + chain awareness + boundaries | 2-4K | Always injected at position 4 |
| **Room** (Navigator → knowledge-context.md) | Stage-specific skills, sub-agent guidance, contribution status, plugin capabilities | Up to 7.5K | Injected by Navigator every 30s, changes per stage |
| **Filing cabinet** (skills, invoked per-case) | Full protocols — conventional commits, methodology guide, implementation planning | Loaded on /invoke | Agent invokes when they need depth |

**Desk is the baseline.** If Navigator fails or knowledge map is missing, the agent still has their tools, their chains, and their boundaries. Nothing critical depends on the room — the room enriches.

**Room changes per stage.** An engineer in analysis stage gets different skill recommendations than an engineer in work stage. The Navigator already handles this via intent-map.yaml. Moving skill recommendations from TOOLS.md to Navigator means they become DYNAMIC instead of static.

**Filing cabinet is already built.** 78 SKILL.md files exist. Gateway skill scanner discovers them. Agent invokes by name. No change needed.

## What Goes ON the Desk (TOOLS.md)

### Filter: tool-roles.yaml

tool-roles.yaml already defines which tools each role uses with role-specific usage/when descriptions. This becomes the PRIMARY filter. The generation pipeline produces ONLY tools listed in tool-roles.yaml for the target agent, plus cross-role tools where the agent is in the roles list.

### Per-Role Desk Contents

#### Project Manager (Conductor)

**Generic tools used (from tool-roles.yaml):** fleet_read_context, fleet_task_create, fleet_chat, fleet_gate_request, fleet_escalate, fleet_alert, fleet_agent_status, fleet_artifact_create, fleet_plane_status, fleet_plane_sync, fleet_phase_advance

**Cross-role tools:** fleet_notify_human, fleet_heartbeat_context, fleet_plane_sprint, fleet_plane_create_issue, fleet_plane_comment, fleet_plane_update_issue, fleet_plane_list_modules

**Role group calls:** pm_sprint_standup, pm_contribution_check

**Total: 20 tools.** PM has the largest desk — the conductor needs every control surface. With condensed format (~100 chars per tool average), this is ~2000 chars for tools + ~200 chars for MCP/plugins + ~200 chars for boundaries = **~2400 chars**.

#### Fleet-Ops (Quality Guardian)

**Generic tools used:** fleet_read_context, fleet_approve, fleet_alert, fleet_escalate, fleet_chat, fleet_agent_status

**Cross-role tools:** fleet_notify_human, fleet_heartbeat_context, fleet_task_context, fleet_artifact_read, fleet_plane_comment

**Role group calls:** ops_real_review, ops_board_health_scan, ops_compliance_spot_check, ops_budget_assessment

**Total: 15 tools.** ~1500 + 200 + 200 = **~1900 chars**.

#### Architect (Designer)

**Generic tools used:** fleet_read_context, fleet_contribute, fleet_artifact_create, fleet_artifact_update, fleet_task_accept, fleet_task_complete, fleet_transfer, fleet_chat, fleet_alert, fleet_escalate, fleet_commit

**Cross-role tools:** fleet_task_context, fleet_artifact_read, fleet_task_progress, fleet_plane_list_modules

**Role group calls:** arch_design_contribution, arch_codebase_assessment

**Total: 17 tools.** ~1700 + 200 + 200 = **~2100 chars**.

#### DevSecOps — Cyberpunk-Zero (Security)

**Generic tools used:** fleet_read_context, fleet_contribute, fleet_alert, fleet_artifact_create, fleet_artifact_update, fleet_task_accept, fleet_commit, fleet_task_complete, fleet_escalate, fleet_chat

**Cross-role tools:** fleet_task_context, fleet_task_progress

**Role group calls:** sec_contribution, sec_pr_security_review (+ sec_dependency_audit, sec_code_scan, sec_secret_scan, sec_infrastructure_health when implemented)

**Total: 14-18 tools.** ~1800 + 200 + 200 = **~2200 chars**.

#### Software Engineer (Builder)

**Generic tools used:** fleet_read_context, fleet_task_accept, fleet_artifact_create, fleet_artifact_update, fleet_commit, fleet_task_complete, fleet_task_create, fleet_request_input, fleet_chat, fleet_pause, fleet_alert

**Cross-role tools:** fleet_task_progress, fleet_task_context, fleet_artifact_read

**Role group calls:** eng_contribution_check, eng_fix_task_response

**Total: 16 tools.** ~1600 + 200 + 200 = **~2000 chars**.

#### DevOps (Infrastructure Builder)

**Generic tools used:** fleet_read_context, fleet_task_accept, fleet_artifact_create, fleet_artifact_update, fleet_commit, fleet_task_complete, fleet_contribute, fleet_request_input, fleet_alert, fleet_chat

**Cross-role tools:** fleet_task_progress

**Role group calls:** devops_infrastructure_health, devops_deployment_contribution

**Total: 13 tools.** ~1300 + 200 + 200 = **~1700 chars**.

#### QA Engineer (Test Guardian)

**Generic tools used:** fleet_read_context, fleet_contribute, fleet_task_accept, fleet_artifact_create, fleet_artifact_update, fleet_commit, fleet_task_complete, fleet_chat, fleet_alert

**Cross-role tools:** fleet_task_progress, fleet_task_context, fleet_artifact_read

**Role group calls:** qa_test_predefinition, qa_test_validation

**Total: 14 tools.** ~1400 + 200 + 200 = **~1800 chars**.

#### Technical Writer (Documenter)

**Generic tools used:** fleet_read_context, fleet_contribute, fleet_task_accept, fleet_artifact_create, fleet_artifact_update, fleet_commit, fleet_task_complete, fleet_chat, fleet_alert, fleet_plane_status

**Cross-role tools:** fleet_task_progress

**Role group calls:** writer_doc_contribution, writer_staleness_scan

**Total: 13 tools.** ~1300 + 200 + 200 = **~1700 chars**.

#### UX Designer (Experience Guardian)

**Generic tools used:** fleet_read_context, fleet_contribute, fleet_task_accept, fleet_artifact_create, fleet_artifact_update, fleet_task_complete, fleet_chat, fleet_alert

**Cross-role tools:** fleet_task_progress

**Role group calls:** ux_spec_contribution, ux_accessibility_audit

**Total: 11 tools.** ~1100 + 200 + 200 = **~1500 chars**.

#### Accountability Generator (Governance)

**Generic tools used:** fleet_read_context, fleet_artifact_create, fleet_alert, fleet_chat

**Cross-role tools:** fleet_heartbeat_context, fleet_artifact_read

**Role group calls:** acct_trail_reconstruction, acct_sprint_compliance (+ acct_pattern_detection when implemented)

**Total: 9 tools.** ~900 + 200 + 200 = **~1300 chars**.

### Size Summary

| Agent | Current | Redesign Target | Reduction |
|-------|---------|-----------------|-----------|
| project-manager | 17,979 | ~2,400 | 87% |
| fleet-ops | 18,004 | ~1,900 | 89% |
| architect | 18,041 | ~2,100 | 88% |
| devsecops-expert | 18,215 | ~2,200 | 88% |
| software-engineer | 17,251 | ~2,000 | 88% |
| devops | 17,249 | ~1,700 | 90% |
| qa-engineer | 17,683 | ~1,800 | 90% |
| technical-writer | 15,420 | ~1,700 | 89% |
| ux-designer | 15,110 | ~1,500 | 90% |
| accountability | 16,031 | ~1,300 | 92% |

Average reduction: **89%.** From 17K average → 1.9K average.

## What Moves to the Room (Navigator)

### Already In Place

The Navigator (fleet/core/navigator.py) already:
1. Reads intent-map.yaml for role×stage injection recipes
2. Selects injection profile based on model capacity
3. Assembles from knowledge map content files
4. Writes knowledge-context.md to agents/{name}/context/
5. Enforces 7500 char limit per context file
6. Runs every orchestrator cycle (30s)

### What Needs to Move

| Content | Currently In | Moves To | intent-map.yaml Change |
|---------|-------------|----------|----------------------|
| Stage-specific skill recommendations | TOOLS.md § Skills (~3K) | Navigator → knowledge-context.md | Add `skills` branch to all role×stage intents with skill names from skill-stage-mapping.yaml |
| Sub-agent descriptions | TOOLS.md § Sub-Agents (~500) | Navigator → knowledge-context.md | Add `sub_agents` branch with name + one-line when-to-use |
| Plugin capabilities per stage | TOOLS.md § Plugins (descriptions) | Navigator → knowledge-context.md | Add `plugins` branch (already exists in intent-map.yaml, verify complete) |
| Hook awareness | TOOLS.md § Hooks (~400) | REMOVE — hooks teach via error/warning messages | N/A |
| CRON documentation | TOOLS.md § CRONs (~300) | REMOVE — CRONs run in isolated sessions | N/A |
| Standing orders | TOOLS.md § Standing Orders (~300) | KEEP in TOOLS.md — it's tool-adjacent and brief | N/A |

### Navigator Changes Required

1. **Verify all role×stage intents have `skills` entries.** intent-map.yaml currently has intents for PM (3 stages), fleet-ops (2 modes), architect (4 stages + contribution). Need to verify: engineer (5 stages), devops, QA, writer, UX, accountability, devsecops all have intents.

2. **Add sub-agent guidance to intents.** Each role×stage intent that has sub-agents should include them. Example: engineer-work should include `sub_agents: [test-runner, code-explorer]`.

3. **Verify knowledge map KB has skill content.** docs/knowledge-map/kb/skills/ exists with content. Verify it covers all 78 skills or at minimum the stage-recommended ones.

4. **Test Navigator output for each role×stage.** Run Navigator.assemble() for all 10 roles × 5-7 stages and verify output is coherent and within 7500 chars.

## What Stays in Filing Cabinet (Skills)

No change. 78 SKILL.md files in .claude/skills/fleet-*/SKILL.md. Gateway discovers them. Agent invokes per-case. The Navigator tells them WHICH skills to consider (room); the skill itself provides the PROTOCOL (filing cabinet).

## What DOES NOT Move

**Standing orders stay in TOOLS.md.** They are tool-adjacent ("you are authorized to act on these") and brief (~200-300 chars). They define WHEN the agent can use tools without being told — that belongs on the same card as the tools.

**Boundaries stay in TOOLS.md.** They define what tools the agent does NOT call and who does instead. Essential for the reference card.

**MCP server names and plugin names stay in TOOLS.md.** Just names, no descriptions. ~200 chars. The agent needs to know what's available.

## Generation Pipeline Changes

### Current: generate-tools-md.py (9 sections)

```
1. Header
2. ALL 26 generic tools (with chain docs from tool-chains.yaml)
3. Role group calls
4. MCP servers (with package names)
5. Plugins (with descriptions from agent-tooling.yaml)
6. Skills per stage (from skill-stage-mapping.yaml) — ~3K
7. Sub-agents (with full descriptions from .claude/agents/)
8. CRONs (from agent-crons.yaml)
9. Standing orders (from standing-orders.yaml)
10. Hooks (from agent-hooks.yaml)
```

### Redesigned: generate-tools-md.py (5 sections)

```
1. Header
2. Tools THIS ROLE uses (filtered by tool-roles.yaml, role-specific usage/when)
   — includes generic tools WHERE THIS ROLE IS IN THE ROLES LIST
   — includes cross-role tools where agent matches
   — role-specific group calls from fleet/mcp/roles/*.py
3. MCP servers (names only)
4. Plugins (names only)
5. Boundaries + Standing orders (brief)
```

### Removed from generator:

| Section | Reason | Where It Goes |
|---------|--------|---------------|
| Skills per stage | Dynamic — changes per stage | Navigator knowledge-context.md |
| Sub-agent descriptions | Only relevant during work | Navigator knowledge-context.md |
| CRONs | Run in isolated sessions | Nowhere — agent doesn't need this |
| Hooks detail | Agent experiences hooks, doesn't study them | Nowhere — hook messages self-teach |
| Plugin descriptions | Available via plugin itself | Names stay, descriptions to Navigator |

### Format Per Tool

Follow the standard's structure but condensed for focused output:

```markdown
### {tool_name}
{role-specific usage from tool-roles.yaml}
**When:** {role-specific condition}
**Chain:** {chain summary from tool-chains.yaml — one line}
{note if critical: BLOCKED, special behavior}
```

~80-120 chars per tool. Clean, scannable, reference card format.

## Validation

### Nothing Falls Through the Cracks

For each role, verify these coverage checks:

1. **Every tool the agent calls** is in TOOLS.md (from tool-roles.yaml)
2. **Every skill the agent should know** is reachable via Navigator OR .claude/skills/ discovery
3. **Every behavioral rule** is in CLAUDE.md or HEARTBEAT.md (not TOOLS.md)
4. **Every chain awareness** is in TOOLS.md (chain field per tool)
5. **Every boundary** is in TOOLS.md boundaries section
6. **Sub-agents** are reachable via Navigator context AND discoverable via .claude/agents/

### Resilience

If Navigator fails (knowledge map missing, orchestrator error):
- Agent still has TOOLS.md (focused but complete for their tools)
- Agent still has CLAUDE.md (rules, stage protocol, contribution model)
- Agent still has HEARTBEAT.md (action protocol)
- Skills are discoverable via /skill-name regardless of Navigator
- MCP tool docstrings are visible via MCP protocol regardless of TOOLS.md
- Sub-agents are discoverable via .claude/agents/ regardless of Navigator

TOOLS.md is the **floor**, not the ceiling. Navigator is enrichment.

## Concern Separation Verification

| Content | Belongs In | NOT In |
|---------|-----------|--------|
| What tools I call + chains | TOOLS.md | — |
| Who I am, my personality | IDENTITY.md | TOOLS.md |
| My values, anti-corruption | SOUL.md | TOOLS.md |
| Stage protocol, contribution model, rules | CLAUDE.md | TOOLS.md |
| Action priority, what to do now | HEARTBEAT.md | TOOLS.md |
| Fleet state, tasks, messages | context/fleet-context.md | TOOLS.md |
| Task detail, verbatim, stage instructions | context/task-context.md | TOOLS.md |
| Stage-specific skills, sub-agent guidance | context/knowledge-context.md | TOOLS.md |
| Tool boundaries, standing orders | TOOLS.md | — |
| MCP server + plugin names | TOOLS.md | — |

No concern mixing. Each file owns its content. TOOLS.md is purely: **what I call, what it triggers, what I don't call, what I'm authorized to do.**

## Implementation Order

1. **Update tool-roles.yaml** — verify all roles have complete tool listings including cross-role tools. Fill gaps.
2. **Rewrite generate-tools-md.py** — filter by tool-roles.yaml, produce 5-section output, test per-agent char counts.
3. **Update Navigator intent-map.yaml** — add skill/sub-agent/plugin entries for all missing role×stage intents.
4. **Verify Navigator output** — run assemble() for all role×stage combinations, verify content.
5. **Regenerate TOOLS.md for all 10 agents** — run pipeline, verify 2-4K target.
6. **Update tools-agents-standard.md** — reflect new focused scope and size target.
7. **Update validation tests** — test_end_to_end_pipeline.py, test_tooling_pipeline.py.
8. **Deploy and observe** — push to agent workspaces, verify agents function correctly.

## Relationships

- PART_OF: E001 (Agent Directive Chain Evolution)
- DEPENDS_ON: tool-roles.yaml completeness
- DEPENDS_ON: Navigator intent-map.yaml completeness
- ENABLES: E002 (agents know their chains — focused, not drowned)
- ENABLES: E003 (brain delivers right context at right time via Navigator)
- RELATES_TO: E007 (plugin/skill ecosystem — skills move to Navigator delivery)
- RELATES_TO: E014 (autocomplete web — Navigator IS the delivery mechanism)
