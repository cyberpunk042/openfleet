# Tools System Elevation — Session Index

**Date:** 2026-04-07
**Status:** Active session — planning and execution tracking
**Scope:** Complete tools system elevation across all 7 capability layers for 10 top-tier expert agents

---

## Session Context

This session regathered full context from compacted previous session, then conducted deep research across the entire fleet system — 31 fleet-elevation docs, 22 system docs, 8 standards, gateway automation capabilities, skills ecosystem, Claude Code extension points, and the full path-to-live.

The PO's direction: this is 42+ hours of work. No minimizing. No disconnected pieces. Each agent is a TOP-TIER EXPERT with their own tools, MCPs, chains, group calls, skills, plugins, CRONs, sub-agents, hooks, standing orders, and directives — generic AND role-specific, adapted per methodology stage.

---

## Documents Produced This Session

### Research & Analysis (8)

| # | Document | What It Covers |
|---|----------|---------------|
| 1 | [tool-chain-elevation-plan.md](tool-chain-elevation-plan.md) | Fleet group calls (Layer 1): tree execution, cross-platform propagation, per-tool gap analysis, chain builder inventory, ChainRunner evolution |
| 2 | [role-specific-tooling-elevation-plan.md](role-specific-tooling-elevation-plan.md) | Layers 2-7: MCP servers, plugins, skills, CRONs, sub-agents, hooks/standing orders/extended thinking. Current state, gaps, architecture |
| 3 | [gateway-automation-capabilities.md](gateway-automation-capabilities.md) | Full technical reference: CRONs, Tasks, TaskFlow, Hooks (14 gateway + 23 Claude Code events), Standing Orders, Heartbeat config |
| 4 | [skills-and-plugins-ecosystem-research.md](skills-and-plugins-ecosystem-research.md) | 5 skill sources, 32 official Anthropic plugins, 9 superpowers marketplace plugins, skill loading pipeline, stage-aware recommendation pattern |
| 5 | [strategic-agent-capabilities-research.md](strategic-agent-capabilities-research.md) | Sub-agents, Agent Teams, extended thinking, hook-based monitoring, session management, 9 strategic call dimensions |
| 6 | [tools-system-full-capability-map.md](tools-system-full-capability-map.md) | THE REAL SCOPE: 3-layer architecture, per-role group calls/skills/CRONs/sub-agents, review ecosystem, plugin details, secondary/backup roles, phase/labor/context connections |
| 7 | [tools-system-session-decisions.md](tools-system-session-decisions.md) | PO requirements verbatim, decisions made, open questions needing PO input, connections to existing work |
| 8 | [tools-system-directives-and-usage.md](tools-system-directives-and-usage.md) | HOW agents know when to use what: 7 directive types, injection order, input/output clarity, strategic features, autocomplete chain, immune system |
| 9 | [phase-a-operations-analysis.md](phase-a-operations-analysis.md) | EVERY operation in every elevated tree: 10 categories, what exists vs needs building, 9 new functions/modules, 18 conditional logic items, implementation order for Phase A |
| 10 | [phase-b-mcp-plugin-findings.md](phase-b-mcp-plugin-findings.md) | MCP package verification (npm registry), workspace deployment state, config corrections, plugin evaluation priorities, blocked items |
| 11 | [phase-c-group-call-architecture.md](phase-c-group-call-architecture.md) | Role-aware registration, code structure, naming convention, per-role module pattern |
| 12 | [tools-system-session-handoff.md](tools-system-session-handoff.md) | SESSION HANDOFF: everything done, honest status per phase, files modified, what next session needs |

### Pre-Existing (from previous session)

| Document | What It Covers |
|----------|---------------|
| [tool-chain-investigation.md](tool-chain-investigation.md) | Original investigation: what's wired vs disconnected, propagation model, dual-board strategy |

### Legacy Chunk Plans (from early this session — SUPERSEDED by revised phases below)

| Document | Status | Notes |
|----------|--------|-------|
| chunk-01 through chunk-09 | SUPERSEDED | Written before full capability map revealed real scope. Kept for reference but the revised 8-phase structure below replaces them. |

---

## Code Changes This Session

| File | Change | Status | Quality |
|------|--------|--------|---------|
| scripts/push-soul.sh | Per-agent mcp.json deployment + .claude/skills/ symlink | DONE | Solid |
| fleet/core/chain_runner.py | 3 new handler actions (update_custom_fields, update_labels, create_issue) | DONE | Solid |
| fleet/core/event_chain.py | 8 new chain builders | DONE | Chain builders provide propagation layer |
| fleet/mcp/tools.py | ALL 16 state-modifying tools elevated to match fleet-elevation/24 + fleet_phase_advance built | DONE | Full elevated trees — verbatim check, security_hold, contribution completeness, readiness regression, sprint progress, doctor signaling, context packaging, notify_contributors, auto-gate at 90%, phase standards check |
| fleet/core/phases.py | check_phase_standards() + PhaseStandardResult | DONE | Evaluates task against PO-defined quality bars |
| fleet/core/plan_quality.py | check_plan_references_verbatim() | DONE | Key term extraction, coverage analysis |
| fleet/core/contributor_notify.py | notify_contributors() | DONE | NEW — mentions contributors at review stage |
| fleet/core/transfer_context.py | package_transfer_context() + TransferPackage | DONE | NEW — gathers all data for task handoff |
| fleet/core/context_writer.py | append_contribution_to_task_context() | DONE | Embeds contributions into target agent's context |
| fleet/core/velocity.py | update_sprint_progress_for_task() | DONE | Sprint metrics after task completion |
| fleet/core/doctor.py | signal_rejection() | DONE | Feeds rejection signals to immune system |
| fleet/core/context_assembly.py | Phase data + contribution status sections | DONE | Context now includes phase standards + contribution completeness |
| fleet/core/preembed.py | Phase standards + required contributions in pre-embed | DONE | Agent sees quality bars and required inputs before starting |
| fleet/tests/core/test_new_chain_builders.py | 17 tests for chain builders (all pass) | DONE | 42 total tests, 0 failures |

**Phase A status: ~75% done.**
- 7 building block modules built and comprehensively tested
- 16 state-modifying tools elevated with full operations matching fleet-elevation/24
- Chain builders evolved (Plane state/labels/comments, IRC at checkpoints, trail)
- Context assembly + preembed updated with phase standards + contribution status
- 2107 tests total: building blocks (94), chain builders (42), tool operations (84), role tools (65), skill recommendations (18), standing orders (12), context assembly (17), tooling pipeline (52), + others
- Tests verify BEHAVIORAL outcomes: security_hold, verbatim warnings, readiness regression, doctor signaling, auto-gate at 90%, ChainRunner invocation, stage gate blocking, contribution completeness, context packaging, cascade limits, plan scoring, mention routing, trail recording
- 6 pre-existing test failures fixed (backend count, stage enforcement, path, imports)
- Remaining: more chain builder operations, some edge cases

**Phase B: ~40% done.** Config fixed, MCP packages verified, deployed to 7/10 workspaces. Phantom pytest-mcp removed, semgrep installed. Plugins + 3 missing workspaces blocked on running gateway.

**Phase C: ~65% done.** Role-aware registration architecture built. 36 role-specific group calls implemented across all 10 roles (PM:5, fleet-ops:4, architect:4, devsecops:6, engineer:2, devops:4, QA:4, writer:2, UX:2, accountability:3). 50 role tool tests (36 registration + 14 behavioral). Remaining: deeper behavioral tests for remaining roles.

**Phase D: ~50% done.** 30 workspace skills. skill-stage-mapping.yaml (140 entries). Dynamic skill recommendations wired into context_assembly + preembed via skill_recommendations.py. Remaining: plugin evaluation/install, more granular skills.

**Phase E: ~35% done.** 17 CRONs, 14 standing orders. Standing orders wired into heartbeat preembed via standing_orders.py. Remaining: gateway CRON deployment, PO authority review.

**Phase F: ~25% done.** 12 sub-agents with role-aware deployment. Hook configs + deployment. Remaining: Agent Teams eval, stage-aware effort.

**Phase G: ~70% done.** generate-tools-md.py reads 7 layers + tool-roles.yaml + role_tools chain docs. TOOLS.md per agent deployed. tool-chains.yaml has chain docs for all 56 tools. Remaining: minor enrichment.

**Phase H: ~35% done.** validate-tooling-configs.py (0 errors). 52 pipeline + 30 skill/orders + 2 context tests. STATUS-TRACKER + MASTER-INDEX updated. 2107 tests passing. Remaining: per-agent smoke test (needs gateway).

---

## Revised Trajectory — 8 Phases

### PHASE A: Foundation Infrastructure
**Status:** IN PROGRESS (~15-20% done — building blocks exist but untested, chain builders still stubs, no end-to-end verification)
**What was done:** 7 building block functions, operations added to 16 tools, context assembly + preembed updated. 42 import tests pass.
**What remains:** Comprehensive tests for every building block. Chain builders rewritten to match full elevated trees. End-to-end verification. Conditional logic paths all tested. This is 80%+ of the work.
**Depends on:** Nothing (foundation infrastructure exists)
**Blocks:** Everything else

**Sub-items:**
- A1: ChainRunner evolution — methodology verification, contribution completeness, security holds, readiness regression, phase standards, context packaging, sprint progress, doctor signaling
- A2: Rewrite all 30 fleet tool trees to match fleet-elevation/24 elevated trees FULLY
- A3: Phase config evolution (flexible predefinable groups, per-epic assignment)
- A4: Context system quadrant updates (phase standards, contribution status, skill recommendations)

### PHASE B: MCP + Plugin Deployment
**Status:** PARTIAL (config fixed, deployed to 7/10 workspaces. Plugins + 3 missing workspaces blocked on running gateway.)
**Findings:** [phase-b-mcp-plugin-findings.md](phase-b-mcp-plugin-findings.md)
**Scope:** Verify all MCP server packages per role. Verify and install all plugins per role. Evaluate unassigned plugins. Fix full deployment pipeline. End-to-end workspace verification.
**Depends on:** Phase A (stable tools.py before verifying MCP integration)
**Blocks:** Phase C (role-specific tools registered on same MCP server), Phase D (plugin skills)

**Sub-items:**
- B1: ✅ Verify MCP server packages — filesystem, github, playwright, plane AVAILABLE. Docker + github-actions package names FIXED. semgrep + pytest-mcp need pip install.
- B2: BLOCKED — Plugin installation requires running gateway CLI or workspace-level claude CLI
- B3: DEFERRED — Plugin evaluation requires install + test
- B4: ✅ Config fixed (agent-tooling.yaml corrected), mcp.json regenerated (10 agents), deployed to 7/10 workspaces with per-agent servers + .claude/skills/
- B5: ✅ Verified — software-engineer workspace has fleet+filesystem+github+playwright+pytest-mcp + 7 fleet skills. Architect has fleet+filesystem+github. Correct.

### PHASE C: Role-Specific Group Calls (BIGGEST PHASE)
**Status:** ARCHITECTURE ONLY (roles/ module structure created, registration mechanism built, 10 empty stub files. 0% of actual group call implementation.)
**Architecture:** [phase-c-group-call-architecture.md](phase-c-group-call-architecture.md)
**Scope:** Build ~35-40 role-specific group calls as new MCP tools, each with tree execution, input validation, chain propagation, and tests.
**Scale:** ~35-40 NEW tools, each comparable to fleet_task_complete in complexity
**Depends on:** Phase A (ChainRunner capable), Phase B (MCP servers verified)
**Blocks:** Phase G (configs must document these tools)

**Sub-items:**
- C1: Group call architecture design (registration, tree builder pattern, per-role vs shared)
- C2: PM group calls (~5: sprint standup, epic breakdown, contribution check, gate route, blocker resolve)
- C3: Fleet-ops group calls (~4: real review, board health, compliance spot check, budget assessment)
- C4: Architect group calls (~4: design contribution, codebase assessment, option comparison, complexity estimate)
- C5: DevSecOps group calls (~6: dependency audit, code scan, secret scan, PR security review, security contribution, infra health)
- C6: Engineer group calls (~3: contribution check, implementation cycle, fix task response)
- C7: DevOps group calls (~4: infra health, deployment contribution, CI/CD review, phase infrastructure)
- C8: QA group calls (~4: test predefinition, test validation, coverage analysis, acceptance criteria review)
- C9: Writer group calls (~3: staleness scan, doc contribution, doc from completion)
- C10: UX group calls (~2: spec contribution, accessibility audit)
- C11: Accountability group calls (~3: trail reconstruction, sprint compliance, pattern detection)

### PHASE D: Skills
**Status:** IN PROGRESS (~30%)
**Scope:** Ecosystem evaluation per role. Build foundation skills (M81-M86). Build/install generic methodology skills. Build/install role-specific skills (40+ per role). Stage-aware mapping.
**Scale:** 10-20 generic + 80-100 role-specific skills (many from ecosystem, some custom)
**Depends on:** Phase B (plugin skills available), Phase C (group calls exist to reference)
**Blocks:** Phase G (skills must exist for TOOLS.md)

**Sub-items:**
- D1: Ecosystem evaluation per role (1000+ available → what fits?)
- D2: ✅ Foundation skills (M81-M86: URLs, templates, PR, comments, memory, IRC) — pre-existed
- D3: ✅ 13 broad workspace skills covering all 10 roles (methodology-guide, contribution, completion-checklist, qa-predefinition, design-contribution, security-contribution, ops-review-protocol, engineer-workflow, pm-orchestration, devops-iac, doc-lifecycle, ux-every-level, accountability-trail)
- D3b: ✅ 10 deep role-specific skills (epic-breakdown, sprint-planning, trail-verification, threat-modeling, adr-creation, boundary-value-analysis, phase-testing, cicd-pipeline, api-documentation, accessibility-audit)
- D4: Role-specific skills remaining (Codex, adversarial-review, plugin-provided skills)
- D5: ✅ Stage-aware mapping (config/skill-stage-mapping.yaml — 140 entries, all refs verified)

### PHASE E: CRONs + Standing Orders
**Status:** IN PROGRESS (~30%)
**Scope:** Design standing orders per role (PO input needed). Design CRONs per role. Config + sync script. Fleet state integration.
**Scale:** ~20-25 CRONs + 10 standing order programs
**Depends on:** Phase C (group calls that CRONs invoke), Phase D (skills that CRONs reference)
**Blocks:** Phase G (CRONs documented in TOOLS.md)

**Sub-items:**
- E1: ✅ Standing order design per role — config/standing-orders.yaml (14 orders, 10 roles, conservative defaults, PO REVIEW markers)
- E2: ✅ CRON design per role — config/agent-crons.yaml (17 jobs, 8 roles, model/effort/schedule per job)
- E3: ✅ scripts/sync-agent-crons.sh — deploys CRONs from config to gateway (dry-run verified)
- E4: ✅ Fleet state integration — guard prefix in CRON messages, standing orders suspended when paused/over budget
- E5: BLOCKED — Actual gateway deployment needs running gateway

### PHASE F: Sub-Agents + Hooks + Thinking
**Status:** IN PROGRESS (~15%)
**Scope:** Custom sub-agent definitions per role. Agent Teams evaluation. Per-role hook configurations. Stage-aware effort. Monitoring hooks.
**Scale:** ~10-15 sub-agents + per-role hook configs + effort system + monitoring
**Depends on:** Phase B (plugin sub-agents available), Phase D (skills sub-agents reference)
**Blocks:** Phase G (sub-agents/hooks in TOOLS.md)

**Sub-items:**
- F1: ✅ 12 sub-agent definitions — code-explorer, test-runner, trail-reconstructor, dependency-scanner, sprint-analyzer, pattern-analyzer, dependency-mapper, secret-detector, security-auditor, container-inspector, regression-checker, coverage-analyzer (all read-only, model-appropriate, tool-restricted)
- F2: Agent Teams evaluation (complement or conflict with orchestrator?)
- F3: ✅ Per-role hook configurations — config/agent-hooks.yaml (defaults + 3 role-specific: engineer test warning, fleet-ops review enforcement, devsecops security_hold reminder)
- F3b: ✅ Hook deployment — configure-agent-settings.sh reads YAML, generates JSON with hooks, deployed to 7 workspaces
- F4: Stage-aware effort system (connect brain decisions to session effort)
- F5: Monitoring hooks (PO observation stream — documented but needs service)
- F6: Security hook content detection fix
- F7: More sub-agents per role (each role should have 1-3 specialized sub-agents)

### PHASE G: Generation Pipeline + Configs
**Status:** IN PROGRESS (~50%)
**Scope:** Write tool-chains.yaml from scratch (ALL tools). Validate tool-roles.yaml. Update agent-tooling.yaml. Create skill-stage-mapping.yaml, agent-crons.yaml. Rewrite generate-tools-md.sh for all 7 layers with directives and input/output clarity.
**Scale:** Complete config rewrite + generation pipeline rewrite
**Depends on:** ALL previous phases (configs document what actually exists)
**Blocks:** Phase H (TOOLS.md generation)

**Sub-items:**
- G1: ✅ tool-chains.yaml exists for 20+ generic tools. Role-specific group calls auto-extract from docstrings.
- G2: tool-roles.yaml validation + evolution (per-role filtering — TODO)
- G3: ✅ agent-tooling.yaml updated with sub_agents per role, all MCP servers, plugins, skills
- G4: ✅ skill-stage-mapping.yaml — 140 entries, all refs verified
- G5: ✅ agent-crons.yaml — 17 CRONs across 8 roles
- G6: ✅ generate-tools-md.py rewritten in Python — reads all 7 layers (tools.py, roles/*.py, tool-chains.yaml, agent-tooling.yaml, skill-stage-mapping.yaml, agent-crons.yaml, standing-orders.yaml, agent-hooks.yaml, identities, sub-agent frontmatter)
- G7: ✅ TOOLS.md generated for all 10 agents (270-324 lines each), deployed to 7 workspaces

### PHASE H: Validation + Deployment
**Status:** IN PROGRESS (~10%)
**Scope:** Config cross-validation. TOOLS.md accuracy per agent. Workspace deployment. Smoke test. Documentation updates.
**Depends on:** Phase G
**Blocks:** Live fleet operation with proper tooling

**Sub-items:**
- H1: Config cross-validation (all configs internally consistent) — TODO
- H2: ✅ TOOLS.md generated and spot-checked (architect, fleet-ops, engineer, PM verified)
- H3: ✅ Workspace deployment verified (7 workspaces: TOOLS.md + skills + sub-agents + hooks + settings)
- H4: Smoke test (1 agent end-to-end with generic + role-specific tools) — TODO (needs gateway)
- H5: Documentation updates (STATUS-TRACKER, MASTER-INDEX, path-to-live) — TODO

---

## Dependency Chain

```
PHASE A (foundation)
  ↓
PHASE B (MCP + plugins)
  ↓
PHASE C (role-specific group calls)  ←── BIGGEST: ~35-40 new tools
  ↓
PHASE D (skills)                     ←── MOST ITEMS: 80-100+ skills
  ↓
PHASE E (CRONs + standing orders)    ←── NEEDS PO INPUT on authority
  ↓
PHASE F (sub-agents + hooks + thinking)
  ↓
PHASE G (generation pipeline + configs)
  ↓
PHASE H (validation + deployment)
```

Some parallelism possible:
- Phase D can START during Phase C (foundation skills don't depend on role group calls)
- Phase E standing order DESIGN can start during Phase C (writing authority docs)
- Phase F sub-agent EVALUATION can start during Phase B (plugin sub-agents)

---

## Cross-References

| Document | Relationship |
|----------|-------------|
| [path-to-live.md](path-to-live.md) | Phase A maps to path-to-live Phase C. Phase B maps to Phase A Step 4. Phase C is NEW (not in original path). Phase D maps to Phase B Step 9. Phase G-H map to Phase B Step 9 + Phase D. |
| [fleet-elevation/05-14](fleet-elevation/) | Per-role specs — source of truth for role-specific capabilities |
| [fleet-elevation/24](fleet-elevation/24-tool-call-tree-catalog.md) | Tool call tree catalog — target for Phase A elevated trees |
| [fleet-elevation/04](fleet-elevation/04-the-brain.md) | Brain design — chain registry, strategic calls |
| [fleet-elevation/23](fleet-elevation/23-agent-lifecycle-and-strategic-calls.md) | Strategic calls — effort, model, context decisions |
| [fleet-elevation/15](fleet-elevation/15-cross-agent-synergy.md) | Synergy matrix — contribution model |
| [fleet-elevation/20](fleet-elevation/20-ai-behavior.md) | Anti-corruption — directives as structural prevention |
| [systems/04](../../../docs/systems/04-event-bus.md) | Event bus — chain propagation target |
| [systems/08](../../../docs/systems/08-mcp-tools.md) | MCP tools system reference |
| [systems/21](../../../docs/systems/21-agent-tooling.md) | Agent tooling system reference |
| [standards/tools-agents-standard.md](standards/tools-agents-standard.md) | TOOLS.md validation criteria |
| [ecosystem-deployment-plan.md](ecosystem-deployment-plan.md) | Ecosystem items E-01 through E-15 |
| [skills-ecosystem.md](skills-ecosystem.md) | Skills milestones M48-M52 |
| [phase-f1-foundation-skills.md](phase-f1-foundation-skills.md) | Foundation skills M81-M86 |
| [context-system/01-08](context-system/) | Context delivery mechanism for directives |
| [methodology-system/01-06](methodology-system/) | Stage protocols — per-stage capability recommendations |

---

## Rules

1. **Plan before execute** — understand the full scope before coding
2. **Full coverage** — no stubs, no partial delivery, no "done" at 5%
3. **Dependency order** — follow the phase chain
4. **Match fleet-elevation/24** — every tool tree matches the design spec FULLY
5. **Directives with every capability** — when/how/input/impact/output for everything
6. **Verify before advancing** — each phase verified before next starts
7. **Update this index** — as phases complete
8. **No premature configs** — tool-chains.yaml and TOOLS.md wait for Phase G after all capabilities exist
