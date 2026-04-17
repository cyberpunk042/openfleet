---
title: "Plan: TK-01 Golden Path — 200+ Lines of High-Value Output"
type: reference
domain: architecture
status: draft
created: 2026-04-11
updated: 2026-04-11
tags: [plan, context-injection, output-quality, TK-01, design]
epic: E001
related:
  - analysis-output-quality-blockers.md
  - investigation-output-quality-blockers.md
confidence: medium
sources: []
---

# Plan: TK-01 Golden Path Output

## Summary

Design plan for TK-01 golden-path output quality: what the 200+-line target deliverable looks like (every autocomplete-chain section task-specific, tier-adapted, verbatim-anchored) and how we reach there. Architecture, data flow (preembed + Navigator + orchestrator), target files, traceability back to the verbatim operator requirement.

## What we deliver

A correct TK-01 output where every section of the autocomplete chain contains real, task-specific, tier-adapted content from the systems that produce it. The output demonstrates that the rendering pipeline works — that the 20+ systems feed into 3 context files that give an agent everything they need without a single MCP call.

The target output structure for TK-01 (software-engineer, work stage, 40% progress, expert tier, all contributions received, MVP phase):

### task-context.md (~120 lines)

```
§0  Mode header + fleet state                              3 lines
    injection level, model name, fleet mode/phase/backend, timestamp

§1  Identity                                               2 lines
    agent name, grounding

§2  Task detail (expert: full)                            10 lines
    title, ID, priority, type, story points, parent title,
    description, PR, Plane ID

§3  Stage                                                  2 lines

§4  Readiness + Progress                                   3 lines
    99% readiness, 40% progress

    WHAT CHANGED (events since last cycle)                 8 lines
    task dispatched, 2 contributions received,
    fleet_task_accept, 2 commits

§5  Verbatim requirement                                   3 lines
    the PO's exact words — the anchor

§6  Stage protocol (expert: full, work stage)             15 lines
    MUST: execute plan, stay in scope, consume contributions,
    conventional commits, complete via fleet_task_complete
    MUST NOT: deviate, add scope, skip tests

§6b Confirmed plan (design plan, not TODO list)           25 lines
    architecture: React component hierarchy under DashboardShell
    data flow: useFleetStatus hook → MC status API → child components
    component relationships: AgentGrid, TaskPipeline, StormIndicator,
      BudgetGauge — each receives typed props from parent
    patterns: Observer (real-time), Adapter (API → component)
    target files: fleet/ui/components/DashboardHealth.tsx,
      fleet/ui/hooks/useFleetStatus.ts
    constraints: existing MC build pipeline, no new deps
    acceptance criteria mapping: TC-001 → AgentGrid 10 cards,
      TC-003 → TaskPipeline segments sum, TC-005 → BudgetGauge API %

§7  Inputs from colleagues                               30 lines
    checklist: design_input ✓, qa_test_definition ✓
    
    ## CONTRIBUTION: design_input (from architect)        ~15 lines
    approach, target files, patterns, constraints,
    component relationships, integration points
    
    ## CONTRIBUTION: qa_test_definition (from qa-engineer) ~10 lines
    TC-001 through TC-007 with specific assertions,
    priority, type (unit/integration/e2e)

§8  Delivery phase: MVP                                    5 lines
    tests: main flows and critical edges
    docs: setup, usage, API for public
    security: auth, validation, dep audit

§9  Action directive                                       3 lines
    progress-adapted: "Continue implementation. fleet_commit() per logical change."
```

### knowledge-context.md (~80 lines)

Produced by Navigator.assemble() for engineer-work intent at opus-1m profile:

```
    Agent manual: engineer section                        10 lines
    mission, primary tools, key rules

    Methodology: work stage                               15 lines
    full MUST/MUST NOT/CAN with work-specific guidance,
    tool sequence, artifact expectations

    Skills with descriptions                              15 lines
    fleet-engineer-workflow, fleet-contribution-consumption,
    fleet-conventional-commits, fleet-completion-checklist
    + superpowers: TDD, verification-before-completion,
      systematic-debugging, subagent-driven-development

    Commands                                               8 lines
    /debug, /diff, /fast, /compact, /batch
    with what each does and when to use it

    Fleet tools with purpose                               8 lines
    fleet_read_context, fleet_task_accept, fleet_commit,
    fleet_task_complete — each with one-line purpose

    MCP servers                                            5 lines
    fleet, filesystem, github, playwright, context7

    Standards                                              8 lines
    plan format, pull_request format, completion_claim format

    Trail awareness                                        3 lines
    every tool call recorded, fleet-ops verifies trail

    Context awareness                                      3 lines
    context %, rate limit %, when to compact

    Sub-agents                                             3 lines
    test-runner, code-explorer — purpose and when to use

    Related systems (from cross-references)                5 lines
    S01 Methodology, S08 MCP Tools, S09 Standards
    connected to engineer-work via tools
```

**Total: ~200 lines of task-specific, role-adapted, tier-appropriate content.**

## How we reach there

### The contribution content problem

The contribution content is the highest-value data in the output. It's the architect's design decisions and the QA's acceptance criteria — without it, the engineer is working blind.

The rendering pipeline has two paths for contribution content:

**Production path**: `fleet_contribute()` → `append_contribution_to_task_context()` → appends `## CONTRIBUTION:` blocks to the existing task-context.md file. On the next 30s cycle, the orchestrator reads the existing file, extracts these blocks, and re-inserts them into the fresh preembed output at `<!-- CONTRIBUTIONS_ABOVE -->`.

**Generator path**: The generator passes contribution text to `render_task_scenario()` which tries to insert it at `<!-- CONTRIBUTIONS_ABOVE -->` in the preembed output.

Both paths fail because `build_task_preembed()` strips the marker before returning. The marker must stay. It's an invisible HTML comment — it doesn't affect the rendered output. The 3-line strip at preembed.py:344-347 is removed.

After this fix, both the orchestrator's contribution preservation AND the generator's content insertion work. The production path and the scenario path use the same mechanism.

### The knowledge context problem

The generator hardcodes a 10-line skill menu. The real system has Navigator.assemble() which reads intent-map.yaml, injection-profiles.yaml, 90+ KB entries, LightRAG, and claude-mem.

The generator should call Navigator directly. Navigator already handles missing services gracefully — LightRAG and claude-mem queries return None when the services aren't running. The static knowledge-map assembly (agent manual, methodology, skills, commands, tools from KB files) works without any external services. This is 60+ lines of curated content from files that exist in the repo right now.

The generator creates a Navigator instance and calls `nav.assemble(role="software-engineer", stage="work", model="opus-4-6", task_context="Add fleet health dashboard")`. The output replaces the hardcoded NAV_WORK constant.

### The fleet state problem

build_task_preembed doesn't receive fleet state. The orchestrator HAS it (fleet_state_dict at orchestrator.py:472-477) but doesn't pass it. Adding a `fleet_state: dict = None` parameter to build_task_preembed and rendering it as a line after §0 makes the agent aware of fleet conditions during task work. The generator passes a representative fleet state.

### The events problem

The generator doesn't simulate events. The WHAT CHANGED section is produced by the orchestrator AFTER build_task_preembed returns (orchestrator.py:671-690). The generator needs to prepend event lines manually, following the same format the orchestrator uses. For TK-01: task dispatched, 2 contributions delivered, plan accepted, 2 commits — matching the 40% progress narrative.

### The confirmed plan problem

The fixture demonstrates the anti-pattern: a TODO list instead of a design plan. Per the plan types directive, the confirmed plan section should show architecture, data flow, component relationships, constraints, and acceptance criteria mapping. The fixture is rewritten to demonstrate what a real reasoning-stage output looks like — tracing from the architect's contribution to specific implementation decisions.

### The contribution depth problem

tier-profiles.yaml defines `status_only` and `summary` depths. preembed.py only checks for `names_only`. Adding elif branches for `status_only` (shows type + from + received/awaiting status per contribution) and `summary` (shows type + from + first 100 chars of content) completes the tier adaptation for contributions. This doesn't affect TK-01 (expert tier = full_inline) but is required for capable and flagship scenarios.

### The heartbeat dead code problem

heartbeat_context.py:302-312 calls build_heartbeat_preembed with wrong parameter names. The orchestrator calls it correctly. The heartbeat_context.py call is removed — it's dead code that silently fails. The HeartbeatBundle.format_message() method remains for legacy/fallback.

### The plan loading brittleness problem

fleet_task_accept should post comments with a structured marker. The comment format changes from free-text to `[CONFIRMED_PLAN]\n{plan_content}`. The orchestrator searches for `[CONFIRMED_PLAN]` instead of guessing from substrings. This is a format change in one MCP tool and one search pattern in the orchestrator.

## Data flow after changes

```
Orchestrator cycle (30s)
│
├── Per agent:
│   │
│   ├── build_heartbeat_preembed(
│   │     ..., fleet_state, renderer, events)
│   │   → fleet-context.md (heartbeat pre-embed)
│   │
│   ├── build_task_preembed(
│   │     task, renderer, fleet_state,          ← NEW: fleet_state
│   │     rejection_feedback, target_task,
│   │     confirmed_plan, parent_task_title,
│   │     received_contribution_types)
│   │   → raw task text WITH marker
│   │   │
│   │   ├── Orchestrator prepends WHAT CHANGED events
│   │   ├── Orchestrator inserts contribution content at marker
│   │   ├── Orchestrator updates checklist status
│   │   └── → task-context.md
│   │
│   └── Navigator.assemble(role, stage, model, task_context)
│       → knowledge-context.md (3-layer knowledge assembly)
│
Generator (offline)
│
├── Calls build_task_preembed → gets text WITH marker
├── Inserts contribution fixtures at marker
├── Prepends event fixtures
├── Calls Navigator.assemble → gets real knowledge context
└── → validation-matrix/TK-01-work-full-contrib.md
```

## Constraints

- No changes to the autocomplete chain ORDER (§0 through §9). Preembed owns order, renderer owns depth. This is additive.
- No changes to tier-profiles.yaml or methodology.yaml structure. The config is correct — the code needs to implement what the config says.
- Navigator must work without LightRAG and claude-mem running. Static assembly only for the generator. Production uses all 3 layers.
- The marker fix must not break the production contribution preservation path. Both paths (orchestrator re-insertion and fleet_contribute direct append) must work.
- All 2453 existing tests must pass. New tests added for each change.

## Acceptance criteria

- TK-01 output is 200+ lines
- task-context.md has contribution content inline (architect design + QA criteria)
- knowledge-context.md is produced by Navigator from real KB files
- WHAT CHANGED section shows events
- Fleet state is visible in task context
- Confirmed plan is a design plan, not a TODO list
- Capable tier scenario (TK-30) shows status_only contributions
- Lightweight tier scenario (TK-31) shows names_only contributions
- All existing tests pass
- New tests cover: marker preservation, contributions depth, fleet_state rendering

## Relationships

- DERIVED FROM: [[Analysis: Why TK-01 Produces 88 Lines of Low-Value Output]]
- DERIVED FROM: [[Investigation: Solutions for Context Output Quality]]
- RELATES TO: [[Tier Rendering Design Rationale]]
- RELATES TO: [[Context Injection Decision Tree]]
- FEEDS INTO: TK-01 validation scenario
