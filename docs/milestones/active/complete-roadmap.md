# Complete Roadmap — Every Milestone In Order

**Date:** 2026-04-02
**Status:** ACTIVE — PO-driven, no shortcuts, no minimizing
**Source:** Every gap, requirement, and work item from ALL design docs

> "WE HAVE 800+ remaining milestones. I want them all in a new file in order."
> "starting with the 120 foundations one and the 300 infrastructure and then
> the 300 features and then fine-tuning and testing"
> "EVERY FUCKING THING. ITS TIME TO TRANSPOSE THE VISION INTO A CLEAR ROAD MAP"

**Rules:**
- Every item references its source doc
- No item is skipped or compressed
- Foundation before infrastructure before features before tuning
- SRP — one thing per milestone
- Each milestone is independently testable

---

## PHASE 1: FOUNDATION (120 milestones)

Everything that other systems depend on. Without these, nothing else works.
No feature work, no agent files, no autocomplete — these FIRST.

### 1.1 Bug Fixes (done this session)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-001 | fleet_commit stage gating — allow stages 2-5 | §33.1 B-01, tools.py:130 | 🔧 READY TO TEST |
| F-002 | Gateway truncation — CLAUDE.md 2000→4000, context 1000→8000 | §33.1 B-02, ws_server.py:345 | 🔧 READY TO TEST |
| F-003 | Gateway missing 5 of 8 files — add IDENTITY/SOUL/TOOLS/AGENTS/HEARTBEAT | §33.1 B-03, executor.py:94 | 🔧 READY TO TEST |
| F-004 | backend_mode not passed to router — wire orchestrator→dispatch→route_task | §33.1 B-04, orchestrator.py | 🔧 READY TO TEST |
| F-005 | budget_mode definitions empty — define turbo/aggressive/standard/economic | §33.1 B-05, budget_modes.py | 🔧 READY TO TEST |

### 1.2 Settings Wiring (done this session)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-006 | budget_mode field on FleetControlState | §22, fleet_mode.py | 🔧 READY TO TEST |
| F-007 | budget_mode tempo_multiplier applied to orchestrator cycle | §29, orchestrator.py daemon | 🔧 READY TO TEST |
| F-008 | budget_mode CRON sync — update gateway heartbeat intervals | §29, gateway_client.py | 🔧 READY TO TEST |
| F-009 | LocalAI health check before routing (GET /v1/models) | §23.4, dispatch.py | 🔧 READY TO TEST |
| F-010 | budget_mode change detection + event emission | §22.1, orchestrator.py | 🔧 READY TO TEST |

### 1.3 IaC Scripts (done this session)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-011 | scripts/validate-agents.sh — standards validation | iac-mcp-standard §2.6 | 🔧 READY TO TEST |
| F-012 | scripts/setup-agent-tools.sh — per-agent mcp.json from config | iac-mcp-standard §2.2 | 🔧 READY TO TEST |
| F-013 | scripts/provision-agent-files.sh — template→workspace | iac-mcp-standard §2.1 | 🔧 READY TO TEST |
| F-014 | scripts/generate-tools-md.sh — TOOLS.md from code | iac-mcp-standard §2.4 | 🔧 READY TO TEST |
| F-015 | scripts/generate-agents-md.sh — AGENTS.md from synergy | iac-mcp-standard §2.5 | 🔧 READY TO TEST |
| F-016 | scripts/install-plugins.sh — claude-mem + context7 per role | iac-mcp-standard §2.3 | 🔧 READY TO TEST |
| F-017 | Makefile targets: setup-tools, validate-agents, provision-files, etc. | iac-mcp-standard | 🔧 READY TO TEST |

### 1.4 Data Model Fixes (partially done)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-018 | task_progress field on TaskCustomFields (0-100 post-dispatch) | §45, §33.24, models.py | 🔧 READY TO TEST |
| F-019 | delivery_phase in preembed format_task_full() | §33.6, §37, preembed.py | 🔧 READY TO TEST |
| F-020 | delivery_phase Plane label sync (phase:{value}) | §33.6, plane_methodology.py | 🔧 READY TO TEST |
| F-021 | Readiness vs progress: fleet_task_progress sets task_progress not readiness | §45.4, tools.py | 🔧 READY TO TEST |
| F-022 | fleet_task_complete sets task_progress=70 (WORK_COMPLETE) | §45.3, tools.py | PENDING |
| F-023 | Challenge system uses task_progress (80) not task_readiness | §45.5, challenge.py | PENDING |
| F-024 | fleet_approve uses task_progress (90) not task_readiness | §45.5, tools.py | PENDING |
| F-025 | Brain transition: task_progress=100 → task status DONE | §45.3, orchestrator.py | PENDING |
| F-026 | Plane sync: task_progress as separate label (progress:{value}) | §45.4, plane_methodology.py | PENDING |
| F-027 | Pre-embed shows both: "Readiness: 99% | Progress: 50%" | §45.5, preembed.py | PENDING |

### 1.5 Trail System (done this session)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-028 | trail_recorder.py — TrailRecorder class | §33.7, §38 | 🔧 READY TO TEST |
| F-029 | 33 TrailEventType enum values | §38.1 | 🔧 READY TO TEST |
| F-030 | TrailEvent with tags, content, mini-signature | §38.2, §44.1 | 🔧 READY TO TEST |
| F-031 | check_trail_completeness() — required events per task type | §38.4 | 🔧 READY TO TEST |
| F-032 | Wire trail recording into fleet_task_complete | §38.4, tools.py | PENDING |
| F-033 | Wire trail recording into fleet_commit | §38.4, tools.py | PENDING |
| F-034 | Wire trail recording into fleet_task_accept | §38.4, tools.py | PENDING |
| F-035 | Wire trail recording into fleet_approve | §38.4, tools.py | PENDING |
| F-036 | Wire trail recording into fleet_contribute | §38.4, tools.py | PENDING |
| F-037 | Wire trail recording into fleet_transfer | §38.4, tools.py | PENDING |
| F-038 | Wire trail recording into fleet_gate_request | §38.4, tools.py | PENDING |
| F-039 | Wire trail recording into orchestrator dispatch | §38.4, orchestrator.py | PENDING |
| F-040 | Wire trail recording into orchestrator stage transitions | §38.4, orchestrator.py | PENDING |
| F-041 | Wire trail recording into doctor disease detection | §38.4, orchestrator.py | PENDING |

### 1.6 MCP Tools Foundation (partially done)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-042 | fleet_contribute MCP tool | §33.2, fleet-elevation/24 | 🔧 READY TO TEST |
| F-043 | fleet_request_input MCP tool | §33.2, fleet-elevation/24 | 🔧 READY TO TEST |
| F-044 | fleet_gate_request MCP tool | §33.2, fleet-elevation/24 | 🔧 READY TO TEST |
| F-045 | fleet_transfer MCP tool | §33.2, fleet-elevation/24 | 🔧 READY TO TEST |
| F-046 | fleet_task_accept: add methodology check (plan references verbatim?) | §33.3, fleet-elevation/24 | PENDING |
| F-047 | fleet_task_accept: add Plane sync on acceptance | §33.3, fleet-elevation/24 | PENDING |
| F-048 | fleet_task_accept: add trail event recording | §33.3, fleet-elevation/24 | PENDING |
| F-049 | fleet_task_progress: add Plane sync on progress | §33.3, fleet-elevation/24 | PENDING |
| F-050 | fleet_task_progress: add readiness threshold events (50%, 90%) | §33.3, fleet-elevation/24 | PENDING |
| F-051 | fleet_commit: add Plane sync on commit | §33.3, fleet-elevation/24 | PENDING |
| F-052 | fleet_commit: add trail event recording | §33.3, fleet-elevation/24 | PENDING |
| F-053 | fleet_approve: add QA validation integration | §33.3, fleet-elevation/24 | PENDING |
| F-054 | fleet_approve: add security review integration | §33.3, fleet-elevation/24 | PENDING |
| F-055 | fleet_approve: add parent task evaluation on approval | §33.3, fleet-elevation/24 | PENDING |
| F-056 | fleet_approve: add sprint progress update | §33.3, fleet-elevation/24 | PENDING |
| F-057 | fleet_artifact_create: add security_assessment renderer | §33.3, System 10 | PENDING |
| F-058 | fleet_artifact_create: add qa_test_definition renderer | §33.3, System 10 | PENDING |
| F-059 | fleet_artifact_create: add ux_spec renderer | §33.3, System 10 | PENDING |
| F-060 | fleet_artifact_create: add documentation_outline renderer | §33.3, System 10 | PENDING |
| F-061 | fleet_artifact_create: add compliance_report renderer | §33.3, System 10 | PENDING |

### 1.7 Contribution System (partially done)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-062 | contributions.py brain module | §33.5, fleet-elevation/15 | 🔧 READY TO TEST |
| F-063 | config/synergy-matrix.yaml | §33.5, fleet-elevation/15 | 🔧 READY TO TEST |
| F-064 | Contribution pre-embed section in preembed.py | §33.5 item 5, preembed.py | PENDING |
| F-065 | build_contribution_chain() wired in event_chain.py | §33.5 item 6, event_chain.py | PENDING |
| F-066 | Contribution completeness as dispatch gate in orchestrator | §33.5 item 9, orchestrator.py | PENDING |
| F-067 | PM notification when all contributions arrive | §33.5 item 8, orchestrator.py | PENDING |
| F-068 | Anti-pattern: siloed_work detection in doctor | §33.5 item 10, doctor.py | PENDING |
| F-069 | Anti-pattern: ghost_contributions detection | §33.5 item 10, doctor.py | PENDING |

### 1.8 Immune System Foundation

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-070 | detect_abstraction — compare agent terms vs PO verbatim | §33.16, System 2, doctor.py | PENDING |
| F-071 | detect_code_without_reading — tool call order analysis | §33.16, System 2, doctor.py | PENDING |
| F-072 | detect_scope_creep — committed files vs plan target_files | §33.16, System 2, doctor.py | PENDING |
| F-073 | detect_cascading_fix — fix→break→fix chain detection | §33.16, System 2, doctor.py | PENDING |
| F-074 | detect_context_contamination — patterns across compaction | §33.16, System 2, doctor.py | PENDING |
| F-075 | detect_not_listening — same correction repeated | §33.16, System 2, doctor.py | PENDING |
| F-076 | detect_compression — task scope vs agent plan scope | §33.16, System 2, doctor.py | PENDING |
| F-077 | Teaching lesson template: cascading_fix | System 3 | PENDING |
| F-078 | Teaching lesson template: context_contamination | System 3 | PENDING |
| F-079 | Teaching lesson template: not_listening | System 3 | PENDING |

### 1.9 Brain Modules Foundation (partially done)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-080 | heartbeat_gate.py — brain evaluation for idle agents | §33.21, fleet-elevation/23 | 🔧 READY TO TEST |
| F-081 | session_manager.py — context + rate limit awareness | §33.11, fleet-elevation/23 | 🔧 READY TO TEST |
| F-082 | trail_recorder.py — audit trail recording | §33.7, §38 | 🔧 READY TO TEST |
| F-083 | chain_registry.py — event→handler registration (Layer 2) | §33.4, fleet-elevation/04 | PENDING |
| F-084 | logic_engine.py — configurable dispatch gates (Layer 3) | §33.4, fleet-elevation/04 | PENDING |
| F-085 | autocomplete.py — chain assembly from real sources | §33.15, §36 | NEEDS REWORK |
| F-086 | Readiness regression logic in MCP tools + orchestrator | §33.22, §41.3 | PENDING |
| F-087 | Readiness regression event chain | §33.22, event_chain.py | PENDING |
| F-088 | Context refresh with regression feedback | §33.22, context_writer.py | PENDING |

### 1.10 Agent Signatures Foundation

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-089 | LaborStamp: add context_window_size field | §33.25, §44.2, labor_stamp.py | PENDING |
| F-090 | LaborStamp: add budget_mode field | §33.25, §44.2, labor_stamp.py | PENDING |
| F-091 | LaborStamp: add context_used_pct field | §33.25, §44.2, labor_stamp.py | PENDING |
| F-092 | LaborStamp: add rate_limit_pct field | §33.25, §44.2, labor_stamp.py | PENDING |
| F-093 | Wire session telemetry → stamp assembly (to_labor_fields) | §33.25, §44.4 item 2 | PENDING |
| F-094 | Populate lines_added/lines_removed from git diff | §33.25, §44.2 | PENDING |
| F-095 | Emit fleet.labor.recorded event on completion | §33.25, §44.4 item 3 | PENDING |
| F-096 | Mini-signatures on trail events (agent, model, context%) | §44.3 Level 1 | PENDING |
| F-097 | Review signature on fleet_approve (reviewer identity, duration) | §44.3 Level 6 | PENDING |
| F-098 | Write all 15+ labor fields to TaskCustomFields | §33.25, §44.2 | PENDING |

### 1.11 Skills Deployment

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-099 | Deploy AICP skills to agent workspaces (.claude/skills/) | §33.8 item 1, agent-tooling.yaml | PENDING |
| F-100 | Deploy fleet custom skills to agent workspaces | §33.8 item 1 | PENDING |
| F-101 | Validate skills accessible per agent (scripts/validate-agents.sh) | §33.8 item 8 | PENDING |
| F-102 | Per-stage skill recommendations in agent context | §33.8 item 6, §34.5 | PENDING |

### 1.12 Plugins Deployment

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-103 | Install claude-mem on all agents (from github.com/thedotmack/claude-mem) | §33.9 item 1, agent-tooling.yaml | PENDING |
| F-104 | Install context7 on architect + engineer workspaces | §33.9 item 2, agent-tooling.yaml | PENDING |
| F-105 | Verify codex-plugin-cc availability and install path | §33.9 item 6 | PENDING |
| F-106 | Enable prompt caching configuration per agent | §33.12, E-01 | PENDING |
| F-107 | Configure cacheRetention per agent (short vs long) | §33.12 item 2 | PENDING |

### 1.13 Commands & Agent Training

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-108 | Document /plan usage in agent CLAUDE.md (when to use) | §33.10, §66.3 | PENDING |
| F-109 | Document /compact strategy per role in CLAUDE.md | §33.10, §66.4 | PENDING |
| F-110 | Document /context inspection in TOOLS.md | §33.10, §66.5 | PENDING |
| F-111 | Document /debug workflow in engineer/devops CLAUDE.md | §33.10, §66.6 | PENDING |
| F-112 | Document /model selection guidance in CLAUDE.md | §33.10, §66.1 | PENDING |
| F-113 | Document /clear between tasks strategy | §33.10 | PENDING |
| F-114 | Stage-specific command recommendations in context | §34.5 | PENDING |

### 1.14 Session Telemetry Wiring

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| F-115 | Orchestrator calls to_labor_fields(snap) from session_telemetry | System 13, System 19 | PENDING |
| F-116 | Orchestrator calls to_claude_health(snap) | System 19 | PENDING |
| F-117 | Orchestrator calls to_storm_indicators(snap) | System 11, System 19 | PENDING |
| F-118 | Orchestrator calls to_cost_delta(snap) | System 12, System 19 | PENDING |
| F-119 | Storm indicator #10: aggregate_context from session data | System 11 | PENDING |
| F-120 | Heartbeat stamp integration — orchestrator calls create_heartbeat_stamp | System 13 | PENDING |

---

## PHASE 2: INFRASTRUCTURE (300 milestones)

Systems that enable agent operation. Agents can't function properly
without these. Built on top of the foundation.

### 2.1 Brain Architecture — Missing Steps

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-001 | Brain Step 1b: Event queue processing (chain_registry) | §33.4, fleet-elevation/04 Step 1 | PENDING |
| I-002 | Brain Step 3b: Gate processing (PO gates at readiness 90%) | §33.4, fleet-elevation/04 Step 3 | PENDING |
| I-003 | Brain Step 4b: Contribution management (create subtasks per synergy) | §33.4, fleet-elevation/04 Step 4 | PENDING |
| I-004 | Brain Step 9: Cross-task propagation (child→parent, contribution→target) | §33.4, fleet-elevation/04 Step 9 | PENDING |
| I-005 | Brain Step 10: Session management (two countdowns, aggregate math) | §33.4, fleet-elevation/04 Step 10 | PENDING |
| I-006 | Brain Step 11: Extended health + budget assessment | §33.4, fleet-elevation/04 Step 11 | PENDING |
| I-007 | Brain Step 12: Extended directive processing | §33.4, fleet-elevation/04 Step 12 | PENDING |

### 2.2 Brain Module: Chain Registry (Layer 2)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-008 | chain_registry.py: register(event_type, handlers) | §43.1, fleet-elevation/04 | PENDING |
| I-009 | chain_registry.py: dispatch(event) — fire all handlers | §43.1 | PENDING |
| I-010 | Cascade depth tracking (prevent infinite loops) | §43.1 | PENDING |
| I-011 | Handler result collection (success/failure per handler) | §43.1 | PENDING |
| I-012 | Dead letter queue (events with no handlers) | §43.1 | PENDING |
| I-013 | Register fleet.task.completed handlers | §43.1 | PENDING |
| I-014 | Register fleet.contribution.posted handlers | §43.1 | PENDING |
| I-015 | Register fleet.gate.requested handlers | §43.1 | PENDING |
| I-016 | Register fleet.task.transferred handlers | §43.1 | PENDING |
| I-017 | Register fleet.disease.detected handlers | §43.1 | PENDING |

### 2.3 Brain Module: Logic Engine (Layer 3)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-018 | logic_engine.py: evaluate_gates(task, agent, state) → GateResult | §43.2, fleet-elevation/04 | PENDING |
| I-019 | config/dispatch-gates.yaml: 10 configurable gates | §43.2 | PENDING |
| I-020 | Gate 1: agent_assigned | §43.2 | PENDING |
| I-021 | Gate 2: agent_has_capacity (max 1 concurrent) | §43.2 | PENDING |
| I-022 | Gate 3: blockers_cleared (depends_on all DONE) | §43.2 | PENDING |
| I-023 | Gate 4: contributions_received (per synergy matrix) | §43.2 | PENDING |
| I-024 | Gate 5: verbatim_present (requirement_verbatim not empty) | §43.2 | PENDING |
| I-025 | Gate 6: delivery_phase_set | §43.2 | PENDING |
| I-026 | Gate 7: readiness_met (>= 99) | §43.2 | PENDING |
| I-027 | Gate 8: stage_allows_dispatch (stage == work) | §43.2 | PENDING |
| I-028 | Gate 9: budget_allows (budget_monitor.is_safe) | §43.2 | PENDING |
| I-029 | Gate 10: work_mode_allows (not paused/finish-current) | §43.2 | PENDING |
| I-030 | Gate configuration hot-reload (PO changes without restart) | §43.2 | PENDING |

### 2.4 Autocomplete Chain (depends on ALL of 1.x)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-031 | autocomplete.py: assemble task chain from context_assembly output | §36, §33.15 | NEEDS REWORK |
| I-032 | Task chain: verbatim anchoring at multiple points | §36.5 | PENDING |
| I-033 | Task chain: stage protocol from stage_context.py | §36.3 | PENDING |
| I-034 | Task chain: contribution embedding (INPUTS FROM COLLEAGUES) | §36.3 | PENDING |
| I-035 | Task chain: skills per role from agent-tooling.yaml | §34.3, §34.5 | PENDING |
| I-036 | Task chain: plugins per role from agent-tooling.yaml | §34.2 | PENDING |
| I-037 | Task chain: commands per stage (/plan, /compact, /debug) | §34.4, §66 | PENDING |
| I-038 | Task chain: tool chains per role from fleet-elevation/24 | §20, §74 | PENDING |
| I-039 | Task chain: standards for artifact type from standards.py | §34.5, System 9 | PENDING |
| I-040 | Task chain: challenge status (pending/passed/failed) | §59, challenge.py | PENDING |
| I-041 | Task chain: codex review awareness | codex_review.py | PENDING |
| I-042 | Task chain: anti-corruption focus per stage | §39.2, fleet-elevation/20 | PENDING |
| I-043 | Heartbeat chain: PO directives → messages → tasks → contributions | §36.4 | PENDING |
| I-044 | Heartbeat chain: skills + plugins + commands per role | §34 | PENDING |
| I-045 | Heartbeat chain: codex availability | codex_review.py | PENDING |
| I-046 | context_writer.py: use autocomplete.py for chain assembly | §36.6 | PENDING |

### 2.5 Agent Identity System (70+ files)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-047 | agent.yaml: all 10 agents per standard (14 required fields) | B4, agent-yaml-standard.md | PENDING |
| I-048 | IDENTITY.md: all 10 agents per standard | identity-soul-standard.md | PENDING |
| I-049 | SOUL.md: all 10 agents per standard (10 anti-corruption rules) | identity-soul-standard.md, fleet-elevation/20 | PENDING |
| I-050 | CLAUDE.md: project-manager per fleet-elevation/05 | B1, claude-md-standard.md | PENDING |
| I-051 | CLAUDE.md: fleet-ops per fleet-elevation/06 | B1 | PENDING |
| I-052 | CLAUDE.md: architect per fleet-elevation/07 | B1 | PENDING |
| I-053 | CLAUDE.md: devsecops per fleet-elevation/08 | B1 | PENDING |
| I-054 | CLAUDE.md: software-engineer per fleet-elevation/09 | B1 | PENDING |
| I-055 | CLAUDE.md: devops per fleet-elevation/10 | B1 | PENDING |
| I-056 | CLAUDE.md: qa-engineer per fleet-elevation/11 | B1 | PENDING |
| I-057 | CLAUDE.md: technical-writer per fleet-elevation/12 | B1 | PENDING |
| I-058 | CLAUDE.md: ux-designer per fleet-elevation/13 | B1 | PENDING |
| I-059 | CLAUDE.md: accountability per fleet-elevation/14 | B1 | PENDING |
| I-060 | HEARTBEAT.md: PM heartbeat per heartbeat-md-standard | B2, fleet-elevation/05 | PENDING |
| I-061 | HEARTBEAT.md: fleet-ops heartbeat (7-step review) | B2, fleet-elevation/06 | PENDING |
| I-062 | HEARTBEAT.md: architect heartbeat (stage-driven) | B2, fleet-elevation/07 | PENDING |
| I-063 | HEARTBEAT.md: devsecops heartbeat (security layer) | B2, fleet-elevation/08 | PENDING |
| I-064 | HEARTBEAT.md: worker template (6 role variants) | B2, fleet-elevation/09-14 | PENDING |
| I-065 | TOOLS.md: regenerate all 10 with chain-aware tool reference | tools-agents-standard.md, fleet-elevation/24 | PENDING |
| I-066 | AGENTS.md: regenerate all 10 with synergy matrix | tools-agents-standard.md, fleet-elevation/15 | PENDING |

### 2.6 Wave 1 — Storm Prevention (Safety Net)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-067 | M-SP01: Storm monitor core | implementation-roadmap Wave 1 | PENDING |
| I-068 | M-SP02: Automatic graduated response | Wave 1 | PENDING |
| I-069 | M-SP04: Per-agent circuit breaker | Wave 1 | PENDING |
| I-070 | M-SP06: Gateway duplication detection | Wave 1 | PENDING |
| I-071 | M-SP03: Diagnostic snapshot on WARNING+ | Wave 2 | PENDING |
| I-072 | M-SP05: Per-backend circuit breaker | Wave 2 | PENDING |
| I-073 | M-SP07: Post-incident report generation | Wave 3 | PENDING |
| I-074 | M-SP08: Orchestrator storm integration (every cycle) | Wave 3 | PENDING |
| I-075 | M-SP09: Storm analytics (frequency, duration, cost) | Wave 4 | PENDING |

### 2.7 Wave 1 — Labor Attribution

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-076 | M-LA01: LaborStamp data model (complete fields) | Wave 1 | PENDING |
| I-077 | M-LA02: Dispatch records intent (brain records WHY) | Wave 1 | PENDING |
| I-078 | M-LA04: Stamp assembly in fleet_task_complete | Wave 1 | PENDING |
| I-079 | M-LA05: Updated comment + PR templates with stamps | Wave 1 | PENDING |
| I-080 | M-LA03: Session metrics collection (tokens, duration, cost) | Wave 2 | PENDING |
| I-081 | M-LA06: Confidence-aware review gates (trainee → deeper review) | Wave 2 | PENDING |
| I-082 | M-LA07: Labor analytics (cost per agent/model/tier) | Wave 4 | PENDING |
| I-083 | M-LA08: Heartbeat labor stamps (cost trends) | Wave 4 | PENDING |

### 2.8 Wave 1 — Budget Modes

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-084 | M-BM01: BudgetMode data model (4 modes defined) | Wave 1 | 🔧 READY TO TEST |
| I-085 | M-BM02: Mode-constrained model selection | Wave 1 | PENDING |
| I-086 | M-BM03: Automatic mode transitions on pressure | Wave 2 | PENDING |
| I-087 | M-BM04: Budget mode in fleet CLI | Wave 2 | PENDING |
| I-088 | M-BM05: Budget mode in OCMC UI | Wave 5 | PENDING |
| I-089 | M-BM06: Budget analytics (cost breakdown by mode) | Wave 4 | PENDING |

### 2.9 Wave 2 — Multi-Backend Routing

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-090 | M-BR01: Backend registry (Claude, LocalAI, OpenRouter, direct) | Wave 2 | PARTIAL |
| I-091 | M-BR02: Routing decision engine (cheapest capable wins) | Wave 2 | PARTIAL |
| I-092 | M-BR03: Fallback chain (LocalAI→OpenRouter→Claude) | Wave 2 | PENDING |
| I-093 | M-BR04: OpenRouter free tier integration (29 models) | Wave 2 | PENDING |
| I-094 | M-BR05: LocalAI model swap management | Wave 5 | PENDING |
| I-095 | M-BR06: Codex CLI adversarial review integration | Wave 5 | PENDING |
| I-096 | M-BR07: Backend health dashboard | Wave 5 | PENDING |
| I-097 | M-BR08: AICP router unification | Wave 5 | PENDING |

### 2.10 Wave 3 — Challenge System

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-098 | M-IV01: Challenge loop data model | Wave 3 | PARTIAL |
| I-099 | M-IV02: Automated challenge generator (free, pattern-based) | Wave 3 | PARTIAL |
| I-100 | M-IV03: Agent challenge protocol (different role reviews) | Wave 3 | PARTIAL |
| I-101 | M-IV04: Cross-model challenge (different LLM) | Wave 3 | PARTIAL |
| I-102 | M-IV05: Scenario challenge for bug fixes | Wave 3 | PARTIAL |
| I-103 | M-IV06: Challenge-aware readiness/progress progression | Wave 3 | PENDING |
| I-104 | M-IV07: Deferred challenge queue (budget-aware) | Wave 3 | PARTIAL |
| I-105 | M-IV08: Challenge analytics (pass rates, categories) | Wave 4 | PARTIAL |

### 2.11 Notification Routing

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-106 | IRC #gates channel creation | §33.14, §42.1 | PENDING |
| I-107 | IRC #contributions channel creation | §33.14, §42.1 | PENDING |
| I-108 | ntfy fleet-gates topic | §33.14, §42.1 | PENDING |
| I-109 | ntfy fleet-review topic | §33.14, §42.1 | PENDING |
| I-110 | Contribution routing (mention:target, mention:role) | §33.14, §42.2 | PENDING |
| I-111 | Readiness regression routing | §33.14, §42.2 | PENDING |
| I-112 | Phase advancement routing | §33.14, §42.2 | PENDING |
| I-113 | QA/security review routing | §33.14, §42.2 | PENDING |
| I-114 | Gate request routing (IRC + ntfy + board) | §33.14, §42.2 | PENDING |

### 2.12 Anti-Corruption Structural (Line 1)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-115 | Autocomplete chain engineering (data ordering prevents disease) | §39.2, §36 | PENDING |
| I-116 | Contribution requirements as dispatch block | §39.2, §33.5 item 9 | PENDING |
| I-117 | Phase-aware standards injection | §39.2, System 9 | PENDING |
| I-118 | Verbatim anchoring in every context level | §39.2, §36.5 | PENDING |
| I-119 | Stage reversion on rejection/disease | §39.4, §41.3 | PENDING |

### 2.13 Cowork & Transfer Protocols

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-120 | Cowork: owner vs coworker distinction | §41.1, §33.17 | PENDING |
| I-121 | Cowork: coworker permissions (can commit, can't complete) | §41.1 | PENDING |
| I-122 | Cowork: brain dispatches to owner, notifies coworkers | §41.1 | PENDING |
| I-123 | Cowork: trail records who did what | §41.1 | PENDING |
| I-124 | Transfer: context packaging (artifacts, comments, contributions) | §41.2 | PENDING |
| I-125 | Transfer: receiving agent gets transfer context | §41.2 | PENDING |
| I-126 | Transfer: trail records transfer with source/target/stage | §41.2 | PENDING |

### 2.14 Pre-Embed Per Role

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-127 | PM pre-embed: Plane sprint data | U-14, H3, System 7 | PENDING |
| I-128 | PM pre-embed: unassigned task count + details | U-03, System 7 | PENDING |
| I-129 | Worker pre-embed: artifact completeness + suggested readiness | U-13, System 7 | PENDING |
| I-130 | Worker pre-embed: contributions received for their task | §30.5, preembed.py | PENDING |
| I-131 | Fleet-ops pre-embed: pending approvals with full task context | System 7 | PENDING |
| I-132 | Architect pre-embed: tasks needing design review | System 7 | PENDING |
| I-133 | All agents pre-embed: delivery phase visible | §33.6, §37 | PENDING |
| I-134 | All agents pre-embed: both readiness + progress visible | §45.5 | PENDING |
| I-135 | Standards injection into context based on task artifact type | H4, §39.2 | PENDING |

### 2.15 Event System Completion

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-136 | Event cleanup: JSONL rotation/archival strategy | M5, System 4 | PENDING |
| I-137 | Event chain: all 8 builders wired and tested | event_chain.py | PENDING |
| I-138 | Cross-reference execution: generate_cross_refs() → callers | M4, System 18 | PENDING |
| I-139 | Bidirectional Plane events: all change types emit | System 4 | PENDING |
| I-140 | Mention routing: events with mention reliably surfaced | System 4 | PENDING |

### 2.16 Board & Memory

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-141 | Board cleanup: archive heartbeat/review noise tasks | §62.1, §62.2 | PENDING |
| I-142 | Board memory retention: hot/warm/cold/frozen tiers | §62.3 | PENDING |
| I-143 | Agent memory lifecycle: pruning stale entries | §62.4, U-11 | PENDING |
| I-144 | Agent MEMORY.md initial population per role | U-11 | PENDING |

### 2.17 Agent Self-Knowledge

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-145 | USER.md populated per agent | U-09 | PENDING |
| I-146 | MEMORY.md initial content per agent | U-11 | PENDING |
| I-147 | Per-agent MCP servers tested (verified they start) | §33.18 | PENDING |
| I-148 | MCP servers: filesystem verified in agent context | §33.18, agent-tooling.yaml | PENDING |
| I-149 | MCP servers: github verified in agent context | §33.18 | PENDING |
| I-150 | MCP servers: playwright verified in agent context | §33.18 | PENDING |
| I-151 | MCP servers: docker verified in agent context | §33.18 | PENDING |
| I-152 | Agent research: WebSearch for architect/devsecops | U-10 | PENDING |
| I-153 | Agent research: CVE databases for devsecops | U-10 | PENDING |
| I-154 | Agent research: test framework docs for QA | U-10 | PENDING |

### 2.18 Context Strategy

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-155 | CW-03: Strategic compaction protocol documented per role | §35.1, §33.11 | PENDING |
| I-156 | CW-04: Efficient regathering protocol per role | §35.1 | PENDING |
| I-157 | CW-07: Rate limit rollover awareness in brain | §35.1, §35.3 | PENDING |
| I-158 | CW-08: Pre-rollover preparation (force compact at 85%) | §35.1, §35.4 | PENDING |
| I-159 | CW-09: Context-size-proportional awareness (1M aggressive) | §35.1 | PENDING |
| I-160 | CW-10: Multi-agent rollover coordination (stagger compactions) | §35.1, §35.5 | PENDING |
| I-161 | Smart artifacts dumping (heavy context → synthesized artifact) | §35.7 | PENDING |
| I-162 | config/fleet.yaml session_management section | §35.9 | PENDING |

### 2.19 Operational Protocols

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| I-163 | PO daily workflow runbook (§48) | §33.28, §48 | PENDING |
| I-164 | Crisis response playbook: budget drain | §33.30, §50.1 | PENDING |
| I-165 | Crisis response playbook: MC down | §33.30, §50.2 | PENDING |
| I-166 | Crisis response playbook: gateway down | §33.30, §50.3 | PENDING |
| I-167 | Crisis response playbook: bad agent output | §33.30, §50.4 | PENDING |
| I-168 | Crisis response playbook: storm escalation | §33.30, §50.5 | PENDING |
| I-169 | Canonical deployment specification | §33.29, §49 | PENDING |
| I-170 | Sprint/PM ceremony protocols | §33.32, §52 | PENDING |
| I-171 | Agent permissions formalization | §33.33, §53 | PENDING |

---

## PHASE 3: FEATURES (300 milestones)

Full system capabilities. Built on foundation + infrastructure.
Each feature enables real agent operation.

### 3.1 Unified Plan Phase A: Agent Foundation (U-01 to U-03)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-001 | U-01: Agent identity + config (all agents per fleet-elevation specs) | unified-implementation-plan | PENDING |
| FT-002 | U-02: Fix preembed — full data per role, no compression | unified-implementation-plan | PENDING |
| FT-003 | U-03: Orchestrator wake logic (content-aware, brain-evaluated) | unified-implementation-plan | PENDING |

### 3.2 Unified Plan Phase B: Heartbeat Rewrites (U-04 to U-08)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-004 | U-04: PM heartbeat rewrite per fleet-elevation/05 | unified-implementation-plan | PENDING |
| FT-005 | U-05: Fleet-ops heartbeat rewrite per fleet-elevation/06 | unified-implementation-plan | PENDING |
| FT-006 | U-06: Architect heartbeat rewrite per fleet-elevation/07 | unified-implementation-plan | PENDING |
| FT-007 | U-07: DevSecOps heartbeat rewrite per fleet-elevation/08 | unified-implementation-plan | PENDING |
| FT-008 | U-08: Worker template heartbeat (6 role variants) per fleet-elevation/09-14 | unified-implementation-plan | PENDING |

### 3.3 Unified Plan Phase C: Self-Knowledge & Comms (U-09 to U-12)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-009 | U-09: Agent self-knowledge (USER.md, TOOLS.md, SKILL.md, MCP) | unified-implementation-plan | PENDING |
| FT-010 | U-10: Agent research capabilities per role | unified-implementation-plan | PENDING |
| FT-011 | U-11: Agent memory lifecycle (MEMORY.md, daily logs, archival) | unified-implementation-plan | PENDING |
| FT-012 | U-12: Inter-agent communication (fleet_chat, @mention, Agent Teams eval) | unified-implementation-plan | PENDING |

### 3.4 Unified Plan Phase D: Data Integration (U-13 to U-16)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-013 | U-13: Pre-embed task artifacts (completeness, missing fields) | unified-implementation-plan | PENDING |
| FT-014 | U-14: Pre-embed Plane data (sprint, issue, state) | unified-implementation-plan | PENDING |
| FT-015 | U-15: Standards in agent context (by artifact type) | unified-implementation-plan | PENDING |
| FT-016 | U-16: Context injection standard (FleetContext validation) | unified-implementation-plan | PENDING |

### 3.5 Unified Plan Phase E: Autonomy & Intelligence (U-17 to U-20)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-017 | U-17: No-agent decision layer (direct HTTP, MCP, templates — $0) | unified-implementation-plan | PENDING |
| FT-018 | U-18: Context-aware lifecycle (two countdowns, organic flow, smart dumping) | unified-implementation-plan | PENDING |
| FT-019 | U-19: Escalation engine (complexity→effort→model→backend, adaptive) | unified-implementation-plan | PENDING |
| FT-020 | U-20: Silent heartbeat protocol (brain evaluates, ~70% cost reduction) | unified-implementation-plan | PENDING |

### 3.6 Unified Plan Phase F: Knowledge & RAG (U-21 to U-23)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-021 | U-21: Connect AICP RAG to fleet (kb.py via MCP/API) | unified-implementation-plan | PENDING |
| FT-022 | U-22: Domain knowledge bases (per-project) | unified-implementation-plan | PENDING |
| FT-023 | U-23: Knowledge persistence & sharing (SQLite in git) | unified-implementation-plan | PENDING |
| FT-024 | LightRAG deployment (Docker service, port 9621) | §46, §33.26 | PENDING |
| FT-025 | LightRAG → OCMC sync (board memory → knowledge graph) | §46.8 Phase 2 | PENDING |
| FT-026 | LightRAG agent MCP query tool (fleet_query_knowledge) | §46.8 Phase 3 | PENDING |
| FT-027 | LightRAG cross-project mesh (AICP + Fleet + DSPD + NNRT) | §46.8 Phase 4 | PENDING |
| FT-028 | LightRAG Plane artifact sync | §46.8 Phase 5 | PENDING |

### 3.7 Unified Plan Phase G: Plane & Writer (U-24 to U-25)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-029 | U-24: Plane auto-update on milestone completion | unified-implementation-plan | PENDING |
| FT-030 | U-25: Writer notification on content changes | unified-implementation-plan | PENDING |
| FT-031 | Plane comment sync: OCMC task comments → Plane issue comments | §13 item 10 | PENDING |
| FT-032 | Parent task comment propagation: subtask done → parent comment | §13 item 11 | PENDING |

### 3.8 Wave 4: Model Evolution

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-033 | M-MU01: Qwen3.5 evaluation + benchmarks | Wave 4 | PENDING |
| FT-034 | M-MU02: Model config templates for new models | Wave 4 | PENDING |
| FT-035 | M-MU03: Shadow routing (test new model in production) | Wave 4 | PENDING |
| FT-036 | M-MU04: Default model promotion | Wave 4 | PENDING |
| FT-037 | M-MU07: Confidence tier progression tracking | Wave 4 | PENDING |

### 3.9 Cross-Project Integration

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-038 | AICP RAG accessible from fleet agents | §33.31, §51.2 | PENDING |
| FT-039 | AICP ↔ Fleet router bridge (router_unification.py) | §33.31, U-36 | PENDING |
| FT-040 | Cross-project cost attribution (project field on stamps) | §33.31, §51.3 | PENDING |
| FT-041 | U-37: Fleet runtime deployment (orchestrator operational) | unified-implementation-plan | PENDING |
| FT-042 | U-38: Cost optimization (caching 90%, Batch API 50%) | unified-implementation-plan | PENDING |

### 3.10 Wave 5: Scale

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-043 | M-MU05: Dual-GPU configuration | Wave 5 | PENDING |
| FT-044 | M-MU06: TurboQuant integration (Q3 2026) | Wave 5 | PENDING |
| FT-045 | M-MU08: Cluster peering (Machine 1 ↔ Machine 2) | Wave 5 | PENDING |
| FT-046 | Multi-fleet identity: Fleet Alpha + Fleet Bravo | §67, U-37, L7 | PENDING |
| FT-047 | The Lounge deployment (IRC web UI) | L3 | PENDING |
| FT-048 | FleetControlBar frontend (TSX in DashboardShell) | L6 | PENDING |
| FT-049 | Agent Teams evaluation (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS) | L9, §33.13 | PENDING |
| FT-050 | Batch API integration (50% savings on async work) | L10, E-10 | PENDING |

### 3.11 Economic Model

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| FT-051 | ROI analysis per LocalAI stage | §33.27, §47 | PENDING |
| FT-052 | Cost-per-task breakdown dashboard | §47.4 | PENDING |
| FT-053 | LocalAI payback timeline projection | §47.3 | PENDING |
| FT-054 | Budget variance tracking (actual vs projected) | §47 | PENDING |

---

## PHASE 4: FINE-TUNING & TESTING (remaining milestones)

No mocks. Real agents, real tasks, real data.

### 4.1 Live Tests (U-26 to U-31)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-001 | U-26: Live test PM heartbeat (10 scenarios) | unified-implementation-plan | PENDING |
| T-002 | U-27: Live test fleet-ops heartbeat (7 scenarios) | unified-implementation-plan | PENDING |
| T-003 | U-28: Live test worker heartbeat (8 scenarios) | unified-implementation-plan | PENDING |
| T-004 | U-29: Live test inter-agent flow (PM→worker→fleet-ops→done) | unified-implementation-plan | PENDING |
| T-005 | U-30: Live test progressive work (3+ cycles, artifact grows) | unified-implementation-plan | PENDING |
| T-006 | U-31: Live test Plane integration | unified-implementation-plan | PENDING |
| T-007 | 24h fleet observation with storm protection | path-to-live Step 12 | PENDING |

### 4.2 Agent Behavior Tests (§56)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-008 | PM sees unassigned inbox tasks in pre-embed | §82.1 test 1 | PENDING |
| T-009 | PM assigns agent AND sets agent_name + assigned_agent_id | §82.1 test 2 | PENDING |
| T-010 | PM sets task type, stage, readiness, story_points | §82.1 test 3 | PENDING |
| T-011 | PM breaks epic into subtasks with dependencies | §82.1 test 4 | PENDING |
| T-012 | PM routes question to PO with context summary | §82.1 test 5 | PENDING |
| T-013 | PM creates sprint plan with assignments | §82.1 test 6 | PENDING |
| T-014 | PM evaluates sprint progress from child task states | §82.1 test 7 | PENDING |
| T-015 | PM handles blocker by creating resolution task | §82.1 test 8 | PENDING |
| T-016 | PM filters routine updates, routes gates to PO | §82.1 test 9 | PENDING |
| T-017 | PM triggers contribution tasks at reasoning stage | §82.1 test 10 | PENDING |
| T-018 | Fleet-ops sees tasks in review in approval queue | §82.2 test 11 | PENDING |
| T-019 | Review takes >30s and references requirement | §82.2 test 12 | PENDING |
| T-020 | Approval fires complete chain (status, Plane, IRC, trail) | §82.2 test 13 | PENDING |
| T-021 | Rejection fires regression chain (readiness, stage, feedback) | §82.2 test 14 | PENDING |
| T-022 | Fleet-ops checks methodology compliance | §82.2 test 15 | PENDING |
| T-023 | Fleet-ops reviews trail completeness before approval | §82.2 test 16 | PENDING |
| T-024 | Fleet-ops overridden by PO decision | §82.2 test 17 | PENDING |
| T-025 | Agent reads context with fleet_read_context (full, not truncated) | §82.3 test 18 | PENDING |
| T-026 | Agent follows stage protocol (no code in analysis) | §82.3 test 19 | PENDING |
| T-027 | Agent produces artifact appropriate to stage | §82.3 test 20 | PENDING |
| T-028 | Agent references verbatim requirement in plan | §82.3 test 21 | PENDING |
| T-029 | Agent satisfies QA predefined tests | §82.3 test 22 | PENDING |
| T-030 | Task readiness increases through progression | §82.3 test 23 | PENDING |
| T-031 | Agent calls fleet_task_complete with proper summary | §82.3 test 24 | PENDING |
| T-032 | Agent receives and processes colleague contributions | §82.3 test 25 | PENDING |

### 4.3 System Flow Tests

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-033 | Full simple task flow: inbox→assign→stages→work→review→done | §82.4 test 26 | PENDING |
| T-034 | Full epic flow: create→subtasks→dependencies→aggregate→done | §82.4 test 27 | PENDING |
| T-035 | Rejection flow: complete→review→reject→regress→re-plan→done | §82.4 test 28 | PENDING |
| T-036 | Contribution flow: reasoning→brain creates→agents contribute→dispatch | §82.4 test 29 | PENDING |
| T-037 | Immune flow: violation→doctor detects→teach→comprehension | §82.4 test 30 | PENDING |
| T-038 | Doctor disease test: agent violates, doctor catches | §82.4 test 31 | PENDING |
| T-039 | Teaching test: agent receives lesson, demonstrates comprehension | §82.4 test 32 | PENDING |
| T-040 | Budget test: threshold breach→mode adjustment→recovery | §82.4 test 33 | PENDING |
| T-041 | Escalation test: agent escalates→ntfy→PO notified | §82.4 test 34 | PENDING |
| T-042 | Trail test: complete lifecycle produces complete audit trail | §82.4 test 35 | PENDING |

### 4.4 Gateway Integration Tests

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-043 | Gateway reads all 8 files in onion order (verified with real agent) | B0.7 | PENDING |
| T-044 | Gateway respects char limits (4000 CLAUDE.md, 8000 context) | B-02 | PENDING |
| T-045 | Gateway CRON sync responds to budget_mode changes | §29 | PENDING |
| T-046 | Gateway session management (inject, prune, compact, create) | §28.3 | PENDING |

### 4.5 LocalAI Integration Tests

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-047 | LocalAI heartbeat response (hermes-3b, structured JSON) | §61 | PENDING |
| T-048 | LocalAI MCP tool calling (fleet_read_context via LocalAI) | §61.2 | PENDING |
| T-049 | LocalAI fallback to Claude on failure | §61.3 | PENDING |
| T-050 | Model swap timing verification (<15s for 3B, <90s for 7B) | §54.4 | PENDING |

### 4.6 Fine-Tuning

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| T-051 | Autonomy tuning: sleep/offline/silent heartbeat timing | PO req §2 | PENDING |
| T-052 | Brain escalation tuning: effort/model/source adaptive | PO req §4 | PENDING |
| T-053 | Context strategy tuning: compact/dump/fresh thresholds | PO req §3 | PENDING |
| T-054 | Agent character review: top-tier expert validation per role | PO req §12 | PENDING |
| T-055 | Model compression validation: right model + right quantization | PO req §13 | PENDING |

---

---

## PHASE 2 EXPANSION: Per-Agent File Breakdown

Each "write CLAUDE.md ×10" is actually 10 individual milestones.
Each agent file references a specific fleet-elevation design doc.

### Agent.yaml — 10 individual milestones (B4)

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-200 | agent.yaml: project-manager (14 fields) | fleet-elevation/05 | PENDING |
| I-201 | agent.yaml: fleet-ops (14 fields) | fleet-elevation/06 | PENDING |
| I-202 | agent.yaml: architect (14 fields) | fleet-elevation/07 | PENDING |
| I-203 | agent.yaml: devsecops-expert (14 fields) | fleet-elevation/08 | PENDING |
| I-204 | agent.yaml: software-engineer (14 fields) | fleet-elevation/09 | PENDING |
| I-205 | agent.yaml: devops (14 fields) | fleet-elevation/10 | PENDING |
| I-206 | agent.yaml: qa-engineer (14 fields) | fleet-elevation/11 | PENDING |
| I-207 | agent.yaml: technical-writer (14 fields) | fleet-elevation/12 | PENDING |
| I-208 | agent.yaml: ux-designer (14 fields) | fleet-elevation/13 | PENDING |
| I-209 | agent.yaml: accountability-generator (14 fields) | fleet-elevation/14 | PENDING |

### IDENTITY.md — 10 individual milestones

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-210 | IDENTITY.md: project-manager | fleet-elevation/05, identity-soul-standard | PENDING |
| I-211 | IDENTITY.md: fleet-ops | fleet-elevation/06 | PENDING |
| I-212 | IDENTITY.md: architect | fleet-elevation/07 | PENDING |
| I-213 | IDENTITY.md: devsecops-expert | fleet-elevation/08 | PENDING |
| I-214 | IDENTITY.md: software-engineer | fleet-elevation/09 | PENDING |
| I-215 | IDENTITY.md: devops | fleet-elevation/10 | PENDING |
| I-216 | IDENTITY.md: qa-engineer | fleet-elevation/11 | PENDING |
| I-217 | IDENTITY.md: technical-writer | fleet-elevation/12 | PENDING |
| I-218 | IDENTITY.md: ux-designer | fleet-elevation/13 | PENDING |
| I-219 | IDENTITY.md: accountability-generator | fleet-elevation/14 | PENDING |

### SOUL.md — 10 individual milestones

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-220 | SOUL.md: project-manager (10 anti-corruption + role values) | fleet-elevation/05, /20 | PENDING |
| I-221 | SOUL.md: fleet-ops | fleet-elevation/06, /20 | PENDING |
| I-222 | SOUL.md: architect | fleet-elevation/07, /20 | PENDING |
| I-223 | SOUL.md: devsecops-expert | fleet-elevation/08, /20 | PENDING |
| I-224 | SOUL.md: software-engineer | fleet-elevation/09, /20 | PENDING |
| I-225 | SOUL.md: devops | fleet-elevation/10, /20 | PENDING |
| I-226 | SOUL.md: qa-engineer | fleet-elevation/11, /20 | PENDING |
| I-227 | SOUL.md: technical-writer | fleet-elevation/12, /20 | PENDING |
| I-228 | SOUL.md: ux-designer | fleet-elevation/13, /20 | PENDING |
| I-229 | SOUL.md: accountability-generator | fleet-elevation/14, /20 | PENDING |

### CLAUDE.md — 10 individual milestones (B1, HEAVIEST)

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-230 | CLAUDE.md: project-manager (8 sections, 4000 chars, role-specific) | fleet-elevation/05, claude-md-standard | PENDING |
| I-231 | CLAUDE.md: fleet-ops (7-step review protocol) | fleet-elevation/06 | PENDING |
| I-232 | CLAUDE.md: architect (design authority, SRP/DDD/onion) | fleet-elevation/07 | PENDING |
| I-233 | CLAUDE.md: devsecops-expert (security layer, crisis) | fleet-elevation/08 | PENDING |
| I-234 | CLAUDE.md: software-engineer (TDD, process respect) | fleet-elevation/09 | PENDING |
| I-235 | CLAUDE.md: devops (IaC, CI/CD, deployment) | fleet-elevation/10 | PENDING |
| I-236 | CLAUDE.md: qa-engineer (test predefinition, pessimistic) | fleet-elevation/11 | PENDING |
| I-237 | CLAUDE.md: technical-writer (living docs, continuous) | fleet-elevation/12 | PENDING |
| I-238 | CLAUDE.md: ux-designer (UX everywhere, accessibility) | fleet-elevation/13 | PENDING |
| I-239 | CLAUDE.md: accountability-generator (trail verification) | fleet-elevation/14 | PENDING |

### HEARTBEAT.md — 5 unique types (B2)

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-240 | HEARTBEAT.md: PM type (assignment, contribution, gate, sprint) | fleet-elevation/05, heartbeat-md-standard | PENDING |
| I-241 | HEARTBEAT.md: fleet-ops type (7-step review, trail, board health) | fleet-elevation/06 | PENDING |
| I-242 | HEARTBEAT.md: architect type (stage-driven, design contributions) | fleet-elevation/07 | PENDING |
| I-243 | HEARTBEAT.md: devsecops type (security, PR review, crisis) | fleet-elevation/08 | PENDING |
| I-244 | HEARTBEAT.md: worker type (6 variants: engineer/devops/QA/writer/UX/accountability) | fleet-elevation/09-14 | PENDING |

### TOOLS.md — 10 individual milestones (chain-aware, not list)

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-245 | TOOLS.md: project-manager (chain-aware, fleet_task_create chains) | fleet-elevation/24, tools-agents-standard | PENDING |
| I-246 | TOOLS.md: fleet-ops (fleet_approve chain, 7-step review tools) | fleet-elevation/24 | PENDING |
| I-247 | TOOLS.md: architect (fleet_contribute chain, design_input) | fleet-elevation/24 | PENDING |
| I-248 | TOOLS.md: devsecops-expert (fleet_alert chain, security_hold) | fleet-elevation/24 | PENDING |
| I-249 | TOOLS.md: software-engineer (fleet_task_complete full tree) | fleet-elevation/24 | PENDING |
| I-250 | TOOLS.md: devops (fleet_commit chain, docker MCP) | fleet-elevation/24 | PENDING |
| I-251 | TOOLS.md: qa-engineer (fleet_contribute chain, qa_test_definition) | fleet-elevation/24 | PENDING |
| I-252 | TOOLS.md: technical-writer (fleet_artifact_create chain) | fleet-elevation/24 | PENDING |
| I-253 | TOOLS.md: ux-designer (fleet_contribute chain, ux_spec) | fleet-elevation/24 | PENDING |
| I-254 | TOOLS.md: accountability-generator (fleet_artifact_create compliance) | fleet-elevation/24 | PENDING |

### AGENTS.md — 10 individual milestones (synergy-aware)

| # | Milestone | Design Doc | Status |
|---|-----------|-----------|--------|
| I-255 | AGENTS.md: project-manager (receives status from all) | fleet-elevation/15, tools-agents-standard | PENDING |
| I-256 | AGENTS.md: fleet-ops (reviews all, receives nothing) | fleet-elevation/15 | PENDING |
| I-257 | AGENTS.md: architect (contributes design_input to engineer/devops/QA/writer/devsecops) | fleet-elevation/15 | PENDING |
| I-258 | AGENTS.md: devsecops-expert (contributes security_req to engineer/devops) | fleet-elevation/15 | PENDING |
| I-259 | AGENTS.md: software-engineer (receives design_input+qa+security, contributes feasibility) | fleet-elevation/15 | PENDING |
| I-260 | AGENTS.md: devops (receives infra_design+security+app_req) | fleet-elevation/15 | PENDING |
| I-261 | AGENTS.md: qa-engineer (receives impl_context+design_context, contributes qa_test_def) | fleet-elevation/15 | PENDING |
| I-262 | AGENTS.md: technical-writer (receives tech_accuracy+arch_context) | fleet-elevation/15 | PENDING |
| I-263 | AGENTS.md: ux-designer (contributes ux_spec) | fleet-elevation/15 | PENDING |
| I-264 | AGENTS.md: accountability-generator (verifies trail) | fleet-elevation/15 | PENDING |

---

## PHASE 2 EXPANSION: Tool Call Tree Elevation (per tool)

Each tool needs its full chain implemented per fleet-elevation/24.

### Existing Tools — Chain Elevation

| # | Milestone | What's Missing | Source |
|---|-----------|---------------|--------|
| I-270 | fleet_read_context: add context_assembly integration | §33.3, fleet-elevation/24 | PENDING |
| I-271 | fleet_read_context: add phase standards lookup | fleet-elevation/24 line 57 | PENDING |
| I-272 | fleet_task_accept: add methodology check (plan references verbatim) | fleet-elevation/24 line 73 | PENDING |
| I-273 | fleet_task_accept: add Plane sync | fleet-elevation/24 line 75 | PENDING |
| I-274 | fleet_task_accept: add trail event | fleet-elevation/24 line 77 | PENDING |
| I-275 | fleet_task_progress: add Plane sync | fleet-elevation/24 line 91 | PENDING |
| I-276 | fleet_task_progress: add readiness 50% checkpoint event | fleet-elevation/24 line 96 | PENDING |
| I-277 | fleet_task_progress: add readiness 90% gate request event | fleet-elevation/24 line 99 | PENDING |
| I-278 | fleet_task_progress: add trail event | fleet-elevation/24 line 94 | PENDING |
| I-279 | fleet_commit: add Plane sync | fleet-elevation/24 line 118 | PENDING |
| I-280 | fleet_commit: add trail event | fleet-elevation/24 line 121 | PENDING |
| I-281 | fleet_task_complete: add challenge engine invocation | fleet-elevation/24, §59 | PENDING |
| I-282 | fleet_task_complete: add codex adversarial review trigger | fleet-elevation/24, codex_review.py | PENDING |
| I-283 | fleet_task_complete: add contributor notification loop | fleet-elevation/24, §30 | PENDING |
| I-284 | fleet_task_complete: add parent task aggregate evaluation | fleet-elevation/24 line 183 | PENDING |
| I-285 | fleet_task_complete: add trail event | fleet-elevation/24 line 181 | PENDING |
| I-286 | fleet_task_complete: set task_progress=70 | §45, fleet-elevation/24 | PENDING |
| I-287 | fleet_alert: add security_hold on critical security alerts | fleet-elevation/24 line 211 | PENDING |
| I-288 | fleet_alert: add trail event | fleet-elevation/24 line 213 | PENDING |
| I-289 | fleet_chat: add trail event when task_id present | fleet-elevation/24 line 238 | PENDING |
| I-290 | fleet_task_create: add contribution task fields | fleet-elevation/24 line 264 | PENDING |
| I-291 | fleet_task_create: add Plane sync for subtasks | fleet-elevation/24 line 270 | PENDING |
| I-292 | fleet_task_create: add trail event | fleet-elevation/24 line 273 | PENDING |
| I-293 | fleet_approve: (approved) add evaluate_parent | fleet-elevation/24 line 307 | PENDING |
| I-294 | fleet_approve: (approved) add update_sprint_progress | fleet-elevation/24 line 308 | PENDING |
| I-295 | fleet_approve: (rejected) add readiness regression | fleet-elevation/24 line 312 | PENDING |
| I-296 | fleet_approve: (rejected) add stage reversion | fleet-elevation/24 line 313 | PENDING |
| I-297 | fleet_approve: (rejected) add doctor rejection signal | fleet-elevation/24 line 318 | PENDING |
| I-298 | fleet_approve: add trail event (approved or rejected) | fleet-elevation/24 | PENDING |
| I-299 | fleet_artifact_create: add trail event | fleet-elevation/24 line 376 | PENDING |
| I-300 | fleet_artifact_update: add trail event | fleet-elevation/24 line 400 | PENDING |
| I-301 | fleet_escalate: add trail event | fleet-elevation/24 line 339 | PENDING |

### New Tools — Chain Completion

| # | Milestone | What | Source |
|---|-----------|------|--------|
| I-302 | fleet_contribute: add context.update_target_task | fleet-elevation/24 line 459 | PENDING |
| I-303 | fleet_contribute: add check_contribution_completeness | fleet-elevation/24 line 476 | PENDING |
| I-304 | fleet_contribute: wire #contributions IRC channel | fleet-elevation/24 line 474 | PENDING |
| I-305 | fleet_transfer: add context packaging (artifacts, comments, contributions) | fleet-elevation/24 line 492-498 | PENDING |
| I-306 | fleet_transfer: add context_writer.write_task_context with transfer package | fleet-elevation/24 line 505 | PENDING |
| I-307 | fleet_request_input: add contribution task existence check | fleet-elevation/24 line 539 | PENDING |
| I-308 | fleet_gate_request: wire #gates IRC channel | fleet-elevation/24 line 556 | PENDING |

---

## PHASE 2 EXPANSION: Per-System Gaps (from 22 system docs)

### System 1: Methodology gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-310 | Stage check automation — brain auto-advances when checks pass | System 1 | PENDING |
| I-311 | Phase gate enforcement — orchestrator enforces PO approval at boundaries | System 1, M7 | PENDING |

### System 3: Teaching gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-312 | Teaching lesson template: cascading_fix | System 3 | PENDING |
| I-313 | Teaching lesson template: context_contamination | System 3 | PENDING |
| I-314 | Teaching lesson template: not_listening | System 3 | PENDING |
| I-315 | Comprehension evaluation evolution (beyond basic heuristics) | System 3 | PENDING |

### System 4: Event Bus gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-316 | Chain runner Plane surface handler completion | System 4 | PENDING |
| I-317 | Bidirectional Plane events — all change types emit | System 4 | PENDING |
| I-318 | Mention routing reliability in heartbeat context | System 4 | PENDING |

### System 5: Control Surface gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-319 | Frontend M-CS01: work_mode dropdown | System 5, L6 | PENDING |
| I-320 | Frontend M-CS02: cycle_phase dropdown | System 5 | PENDING |
| I-321 | Frontend M-CS03: backend_mode dropdown | System 5 | PENDING |
| I-322 | Frontend M-CS04: budget_mode dropdown | System 5 | PENDING |
| I-323 | Frontend M-CS05: directive posting UI | System 5 | PENDING |
| I-324 | Frontend M-CS06: agent status overview | System 5 | PENDING |
| I-325 | Frontend M-CS07: task board with methodology stages | System 5 | PENDING |
| I-326 | Frontend M-CS08: approval queue for fleet-ops | System 5 | PENDING |
| I-327 | Frontend M-CS09: sprint progress visualization | System 5 | PENDING |
| I-328 | Frontend M-CS10: cost/budget dashboard | System 5 | PENDING |

### System 6: Agent Lifecycle gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-329 | Per-agent cron enable/disable (not just all-or-nothing) | System 6 | PENDING |
| I-330 | Per-agent cron interval adaptation based on role | System 6 | PENDING |
| I-331 | Wake triggers per role — complete implementation | System 6, fleet-elevation/23 | PENDING |

### System 9: Standards gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-332 | Standards: security_assessment artifact definition | System 9, §33.3 | PENDING |
| I-333 | Standards: deployment_manifest artifact definition | System 9 | PENDING |
| I-334 | Standards: compliance_report artifact definition | System 9 | PENDING |
| I-335 | Standards: ux_spec artifact definition | System 9 | PENDING |
| I-336 | Standards: qa_test_definition artifact definition | System 9 | PENDING |
| I-337 | Standards: documentation_outline artifact definition | System 9 | PENDING |
| I-338 | Phase-dependent quality bars (poc=basic, production=comprehensive) | System 9 | PENDING |
| I-339 | Quality criteria automation (machine-readable, not just human) | System 9 | PENDING |

### System 10: Transpose gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-340 | Renderer: security_assessment → HTML | System 10, M2 | PENDING |
| I-341 | Renderer: qa_test_definition → HTML | System 10 | PENDING |
| I-342 | Renderer: ux_spec → HTML | System 10 | PENDING |
| I-343 | Renderer: documentation_outline → HTML | System 10 | PENDING |
| I-344 | Renderer: compliance_report → HTML | System 10 | PENDING |
| I-345 | Renderer quality: syntax highlighting | System 10 | PENDING |
| I-346 | Renderer quality: collapsible sections | System 10 | PENDING |
| I-347 | Renderer quality: status indicators | System 10 | PENDING |

### System 11: Storm gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-348 | Storm indicator #10: aggregate_context (from session_manager) | System 11 | PENDING |
| I-349 | Post-incident reports posted to board memory | System 11 | PENDING |
| I-350 | Prevention recommendations engine (rule-based) | System 11 | PENDING |
| I-351 | De-escalation tuning (currently same speed as escalation) | System 11 | PENDING |
| I-352 | End-to-end storm cycle integration test | System 11 | PENDING |

### System 12: Budget gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-353 | Silent heartbeat cost reduction (70% savings) | System 12, H5 | PENDING |
| I-354 | Prompt caching deployment (90% savings) | System 12, E-01 | PENDING |
| I-355 | LocalAI routing connected (100% simple task savings) | System 12 | PENDING |
| I-356 | Batch API integration (50% async savings) | System 12, E-10, L10 | PENDING |

### System 13: Labor Attribution gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-357 | Session telemetry → stamp assembly wiring (W8) | System 13 | PENDING |
| I-358 | All 15+ stamp fields written to TaskCustomFields | System 13, §44 | PENDING |
| I-359 | Heartbeat stamp integration in orchestrator | System 13 | PENDING |
| I-360 | Analytics dashboard: cost per agent/model/tier | System 13, M-LA07 | PENDING |

### System 14: Router gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-361 | LocalAI routing live test (real agent, real task) | System 14 | PENDING |
| I-362 | OpenRouter free tier client (29 models) | System 14, L2 | PENDING |
| I-363 | AICP ↔ Fleet router bridge (router_unification.py) | System 14, L5, U-36 | PENDING |

### System 15: Challenge Engine gaps

| # | Milestone | Source |
|---|-----------|--------|
| I-364 | Challenge results available to fleet-ops during review | System 15, M3 | PENDING |
| I-365 | Automated challenge live test (real code diff) | System 15 | PENDING |
| I-366 | Cross-model challenge with LocalAI (hermes-3b free challenger) | System 15 | PENDING |
| I-367 | Codex adversarial review integration (codex_review.py → completion flow) | System 15, codex_review.py | PENDING |
| I-368 | Deferred queue drain in orchestrator (budget recovers → drain) | System 15 | PENDING |
| I-369 | Teaching signals: ChallengeAnalytics → teaching system | System 15 | PENDING |

---

## PHASE 3 EXPANSION: Ecosystem Deployment (15 items broken down)

### Tier 1 — Immediate (config only)

| # | Milestone | Source |
|---|-----------|--------|
| FT-100 | E-01: Enable prompt caching — set cacheRetention per agent | ecosystem-deployment-plan | PENDING |
| FT-101 | E-01: Configure short vs long cache per agent type | §35.6 | PENDING |
| FT-102 | E-01: Document known Anthropic cache bugs | §35.6 | PENDING |
| FT-103 | E-02: Install claude-mem on all 10 agent workspaces | ecosystem-deployment-plan | PENDING |
| FT-104 | E-02: Verify claude-mem cross-session memory works | agent-tooling.yaml | PENDING |
| FT-105 | E-03: Install context7 on architect workspace | ecosystem-deployment-plan | PENDING |
| FT-106 | E-03: Install context7 on software-engineer workspace | ecosystem-deployment-plan | PENDING |
| FT-107 | E-04: Verify filesystem MCP starts for architect | agent-tooling.yaml | PENDING |
| FT-108 | E-04: Verify filesystem MCP starts for engineer | agent-tooling.yaml | PENDING |
| FT-109 | E-04: Verify filesystem MCP starts for devops | agent-tooling.yaml | PENDING |
| FT-110 | E-04: Verify filesystem MCP starts for devsecops | agent-tooling.yaml | PENDING |
| FT-111 | E-04: Verify filesystem MCP starts for QA | agent-tooling.yaml | PENDING |
| FT-112 | E-04: Verify filesystem MCP starts for writer | agent-tooling.yaml | PENDING |
| FT-113 | E-04: Verify filesystem MCP starts for UX | agent-tooling.yaml | PENDING |
| FT-114 | E-04: Verify filesystem MCP starts for accountability | agent-tooling.yaml | PENDING |

### Tier 1 — MCP Server Verification (per server type)

| # | Milestone | Source |
|---|-----------|--------|
| FT-115 | Verify github MCP server starts and authenticates | agent-tooling.yaml | PENDING |
| FT-116 | Verify playwright MCP server starts | agent-tooling.yaml | PENDING |
| FT-117 | Verify docker MCP server starts | agent-tooling.yaml | PENDING |
| FT-118 | Verify fleet MCP server starts per agent | agent-tooling.yaml | PENDING |
| FT-119 | Verify codex-plugin-cc installation path | §33.9, codex_review.py | PENDING |

### Tier 2 — Short-term

| # | Milestone | Source |
|---|-----------|--------|
| FT-120 | E-05: GitHub MCP server deployed to all agents with github role | ecosystem-deployment-plan | PENDING |
| FT-121 | E-06: Playwright MCP deployed to engineer/QA/UX | ecosystem-deployment-plan | PENDING |
| FT-122 | E-07: Docker MCP deployed to devops/devsecops | ecosystem-deployment-plan | PENDING |
| FT-123 | E-08: Per-agent skills deployed from .claude/skills/ | ecosystem-deployment-plan, §33.8 | PENDING |
| FT-124 | E-09: LocalAI RAG → fleet (AICP rag.py via MCP) | ecosystem-deployment-plan | PENDING |
| FT-125 | E-10: Batch API for non-urgent work (50% savings) | ecosystem-deployment-plan | PENDING |

### Tier 3 — Strategic

| # | Milestone | Source |
|---|-----------|--------|
| FT-126 | E-11: Agent Teams evaluation (enable experimental flag, pilot) | ecosystem-deployment-plan, L9 | PENDING |
| FT-127 | E-12: AICP ↔ Fleet bridge (router_unification.py) | ecosystem-deployment-plan, L5, U-36 | PENDING |
| FT-128 | E-13: LocalAI v4.0 agents evaluation | ecosystem-deployment-plan | PENDING |
| FT-129 | E-14: OpenRouter free tier client (29 models) | ecosystem-deployment-plan, L2 | PENDING |
| FT-130 | E-15: Multi-fleet identity (Fleet Alpha + Bravo) | ecosystem-deployment-plan, L7, §67 | PENDING |

---

## PHASE 3 EXPANSION: Context Strategy (CW-01 to CW-10)

| # | Milestone | Source |
|---|-----------|--------|
| FT-140 | CW-01: Validate context window size (1M vs 200K) per agent | §35.1 | PARTIAL |
| FT-141 | CW-02: Document cost dynamics per context size | §35.2 | PARTIAL |
| FT-142 | CW-03: Strategic compaction protocol per role | §35.1, §33.11 | PENDING |
| FT-143 | CW-04: Efficient regathering protocol per role | §35.1 | PENDING |
| FT-144 | CW-05: .claudeignore per project (prevent bloat) | §35.1 | 🔧 READY TO TEST |
| FT-145 | CW-06: Document settings and awareness proof | §35.1 | PARTIAL |
| FT-146 | CW-07: Rate limit rollover awareness in brain | §35.1, §35.3 | PENDING |
| FT-147 | CW-08: Pre-rollover preparation (force compact at 85%) | §35.1, §35.4 | PENDING |
| FT-148 | CW-09: Context-proportional awareness (1M managed aggressively) | §35.1 | PENDING |
| FT-149 | CW-10: Multi-agent rollover coordination (stagger compactions) | §35.1, §35.5 | PENDING |
| FT-150 | Smart artifacts dumping implementation | §35.7 | PENDING |
| FT-151 | config/fleet.yaml session_management section | §35.9 | PENDING |

---

## PHASE 3 EXPANSION: LocalAI Independence (5 stages)

| # | Milestone | Source |
|---|-----------|--------|
| FT-160 | Stage 1: LocalAI operational — free heartbeats on hermes-3b | strategic-vision-localai-independence | PENDING |
| FT-161 | Stage 1: Trainee-tier detection for LocalAI output | strategic-vision | PENDING |
| FT-162 | Stage 2: Model swapping — GPU memory management | strategic-vision | PENDING |
| FT-163 | Stage 2: Skip-swap logic (keep warm model loaded) | strategic-vision, §54.4 | PENDING |
| FT-164 | Stage 3: Hybrid workflows — Claude for critical, LocalAI routine | strategic-vision | PENDING |
| FT-165 | Stage 3: Quality measurement per operation type | strategic-vision | PENDING |
| FT-166 | Stage 4: Autonomous routing — cheapest-capable without PO override | strategic-vision | PENDING |
| FT-167 | Stage 5: Cost-neutral — fleet cost approaches $0 with LocalAI + OpenRouter | strategic-vision | PENDING |

---

## PHASE 4 EXPANSION: Additional Live Tests

### Per-Role Heartbeat Tests (from §82)

| # | Milestone | Source |
|---|-----------|--------|
| T-060 | PM test 1: sees unassigned inbox tasks in pre-embed | §82.1 | PENDING |
| T-061 | PM test 2: assigns agent AND sets all fields | §82.1 | PENDING |
| T-062 | PM test 3: sets task type, stage, readiness, SP | §82.1 | PENDING |
| T-063 | PM test 4: breaks epic into subtasks with deps | §82.1 | PENDING |
| T-064 | PM test 5: routes question to PO | §82.1 | PENDING |
| T-065 | PM test 6: creates sprint plan | §82.1 | PENDING |
| T-066 | PM test 7: evaluates sprint from children | §82.1 | PENDING |
| T-067 | PM test 8: handles blocker with resolution task | §82.1 | PENDING |
| T-068 | PM test 9: filters noise, routes gates to PO | §82.1 | PENDING |
| T-069 | PM test 10: triggers contributions at reasoning | §82.1 | PENDING |
| T-070 | Fleet-ops test 1: sees review queue | §82.2 | PENDING |
| T-071 | Fleet-ops test 2: review >30s, references requirement | §82.2 | PENDING |
| T-072 | Fleet-ops test 3: approval fires complete chain | §82.2 | PENDING |
| T-073 | Fleet-ops test 4: rejection fires regression chain | §82.2 | PENDING |
| T-074 | Fleet-ops test 5: checks methodology compliance | §82.2 | PENDING |
| T-075 | Fleet-ops test 6: reviews trail before approval | §82.2 | PENDING |
| T-076 | Fleet-ops test 7: PO can override | §82.2 | PENDING |
| T-077 | Worker test 1: reads full context (not truncated) | §82.3 | PENDING |
| T-078 | Worker test 2: follows stage protocol | §82.3 | PENDING |
| T-079 | Worker test 3: produces stage-appropriate artifact | §82.3 | PENDING |
| T-080 | Worker test 4: references verbatim in plan | §82.3 | PENDING |
| T-081 | Worker test 5: satisfies QA predefined tests | §82.3 | PENDING |
| T-082 | Worker test 6: readiness progresses 0→99 | §82.3 | PENDING |
| T-083 | Worker test 7: fleet_task_complete with summary | §82.3 | PENDING |
| T-084 | Worker test 8: processes colleague contributions | §82.3 | PENDING |

### Cross-System Flow Tests (from §82.4)

| # | Milestone | Source |
|---|-----------|--------|
| T-085 | Full simple flow: inbox→assign→stages→work→review→done | §82.4 test 26 | PENDING |
| T-086 | Full epic flow: create→subtasks→deps→aggregate→done | §82.4 test 27 | PENDING |
| T-087 | Rejection flow: complete→reject→regress→replan→done | §82.4 test 28 | PENDING |
| T-088 | Contribution flow: reasoning→create→contribute→dispatch | §82.4 test 29 | PENDING |
| T-089 | Immune flow: violation→detect→teach→comprehension | §82.4 test 30 | PENDING |
| T-090 | Disease test: agent violates, doctor catches | §82.4 test 31 | PENDING |
| T-091 | Teaching test: lesson received, comprehension shown | §82.4 test 32 | PENDING |
| T-092 | Budget test: threshold→adjustment→recovery | §82.4 test 33 | PENDING |
| T-093 | Escalation test: escalate→ntfy→PO notified | §82.4 test 34 | PENDING |
| T-094 | Trail test: complete lifecycle → complete audit trail | §82.4 test 35 | PENDING |

---

---

## PHASE 5: KNOWLEDGE MAP + ECOSYSTEM (from research groups 01-04)

> PO: "The most advanced and sophisticated metadata and maps net
> in order to create our own autocomplete web that organically and
> very easily access the right branches and leaves of the tree."

### 5.1 Knowledge Map Architecture

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| KM-001 | Design _map.yaml schema (metadata format for all manuals) | research/group-03 | PENDING |
| KM-002 | System manuals: condensed versions (22 systems × 50 lines) | research/group-03, docs/systems/ | PENDING |
| KM-003 | System manuals: minimal versions (22 systems × 5 lines) | research/group-03 | PENDING |
| KM-004 | System manuals: _map.yaml cross-references (22 systems) | research/group-03 | PENDING |
| KM-005 | Agent manuals: full specs from fleet-elevation (10 agents) | fleet-elevation/05-14 | PENDING |
| KM-006 | Agent manuals: condensed versions (10 agents) | research/group-03 | PENDING |
| KM-007 | Agent manuals: minimal versions (10 agents) | research/group-03 | PENDING |
| KM-008 | Agent manuals: _map.yaml (role, tools, skills, plugins, commands) | research/group-03 | PENDING |
| KM-009 | Module manuals: per-module purpose + signature (94 modules) | research/group-03, §86 | PENDING |
| KM-010 | Module manuals: _map.yaml (imports, exports, called-by) | research/group-03 | PENDING |
| KM-011 | Tool manuals: fleet MCP tools full call trees (29 tools) | fleet-elevation/24 | PENDING |
| KM-012 | Tool manuals: built-in tools reference (33 tools) | research/group-02 | PENDING |
| KM-013 | Tool manuals: _map.yaml (chain, who-uses, stage-gating) | research/group-03 | PENDING |
| KM-014 | Skill manuals: all 37 substantive skills documented | research/group-04 | PENDING |
| KM-015 | Skill manuals: _map.yaml (role, stage, priority) | research/group-04 | PENDING |
| KM-016 | Plugin manuals: codex-plugin-cc capabilities + config | research/group-01 | PENDING |
| KM-017 | Plugin manuals: claude-mem capabilities + SQLite-only mode | research/group-01 | PENDING |
| KM-018 | Plugin manuals: Superpowers methodology integration | research/group-04 | PENDING |
| KM-019 | Plugin manuals: safety-net hook protection | research/group-02 | PENDING |
| KM-020 | Command manuals: 50+ commands with per-role/stage guidance | research/group-02 | PENDING |
| KM-021 | Standards manual: 8 standards + 13 artifact types | standards/ | PENDING |
| KM-022 | Methodology manual: 5 stages × tool/skill/command recs | stage_context.py, research/group-02 | PENDING |
| KM-023 | cross-references.yaml (system→module→tool→agent relationships) | research/group-03 | PENDING |
| KM-024 | intent-map.yaml (situation → what to inject) | research/group-03 | PENDING |
| KM-025 | Injection profile: opus-1m (full detail) | research/group-03 | PENDING |
| KM-026 | Injection profile: sonnet-200k (condensed) | research/group-03 | PENDING |
| KM-027 | Injection profile: localai-8k (minimal) | research/group-03 | PENDING |
| KM-028 | Injection profile: heartbeat (just enough for idle check) | research/group-03 | PENDING |
| KM-029 | Navigator module: brain reads map, selects content, assembles chain | research/group-03 | PENDING |
| KM-030 | Integrate navigator with context_writer.py | research/group-03 | PENDING |
| KM-031 | Integrate navigator with preembed.py | research/group-03 | PENDING |
| KM-032 | Integrate navigator with autocomplete.py (rework) | research/group-03 | PENDING |
| KM-033 | LightRAG indexes full manual content | §46, research/group-03 | PENDING |

### 5.2 Ecosystem Adoption

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| EA-001 | Install claude-mem on all agents (SQLite-only mode for WSL2) | research/group-01 | PENDING |
| EA-002 | Install context7 on architect + engineer | research/group-02 | PENDING |
| EA-003 | Evaluate + install Superpowers on coding agents | research/group-04 | PENDING |
| EA-004 | Adapt Superpowers autonomy level for fleet guardrails | research/group-04 | PENDING |
| EA-005 | Install safety-net hook on ALL agents | research/group-02 | PENDING |
| EA-006 | Evaluate codex-plugin-cc for fleet-ops + devsecops | research/group-01 | PENDING |
| EA-007 | Implement review gate pattern natively (from codex concept) | research/group-01 | PENDING |
| EA-008 | Install pyright-lsp on all Python agents | research/group-02 | PENDING |
| EA-009 | Evaluate pr-review-toolkit for fleet-ops reviews | research/group-02 | PENDING |
| EA-010 | Evaluate claude-octopus for multi-model review | research/group-02 | PENDING |
| EA-011 | Evaluate Plane official MCP server vs direct API | research/group-02 | PENDING |
| EA-012 | Install Snyk MCP for devsecops (11 security tools) | research/group-02 | PENDING |
| EA-013 | Install Trivy MCP for devsecops (open source scanner) | research/group-02 | PENDING |
| EA-014 | Install Semgrep MCP for devsecops (30+ language SAST) | research/group-02 | PENDING |
| EA-015 | Install pytest-mcp-server for QA + engineer | research/group-02 | PENDING |
| EA-016 | Evaluate sequential-thinking MCP for architect | research/group-02 | PENDING |
| EA-017 | Evaluate diagram-bridge MCP for architect + writer | research/group-02 | PENDING |
| EA-018 | Trail of Bits security skills for devsecops (21 skills) | research/group-04 | PENDING |
| EA-019 | alirezarezvani agent-designer + rag-architect for architect | research/group-04 | PENDING |
| EA-020 | HashiCorp Terraform skills for devops (11 skills) | research/group-04 | PENDING |

### 5.3 Skills Infrastructure

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| SK-001 | Update agent-tooling.yaml: add 7 fleet skills to roles | research/group-04 | PENDING |
| SK-002 | Update agent-tooling.yaml: add fleet-communicate to ALL | research/group-04 | PENDING |
| SK-003 | Update agent-tooling.yaml: equip fleet-ops (7+ missing) | research/group-04 | PENDING |
| SK-004 | Update agent-tooling.yaml: equip PM (fleet-plan/sprint/plane) | research/group-04 | PENDING |
| SK-005 | Update agent-tooling.yaml: add reactive ops to devops | research/group-04 | PENDING |
| SK-006 | Differentiate 48 template skills with real content | research/group-04 | PENDING |
| SK-007 | Build skill deployment script (AICP→agent workspaces) | research/group-04 | PENDING |
| SK-008 | Per-stage skill recommendations in agent context | research/group-04, §34.5 | PENDING |
| SK-009 | Skill evaluation: which actually help (measure impact) | research/group-04 | PENDING |
| SK-010 | AICP skill adaptation for fleet agent context | research/group-04 | PENDING |

### 5.4 Hooks Infrastructure

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| HK-001 | Evaluate safety-net hook pattern for fleet agents | research/group-02 | PENDING |
| HK-002 | Implement PreToolUse hook: destructive command protection | research/group-02, 26 hooks | PENDING |
| HK-003 | Implement PostToolUse hook: trail event recording | research/group-02 | PENDING |
| HK-004 | Implement Stop hook: review gate pattern (from codex concept) | research/group-01 | PENDING |
| HK-005 | Implement PreCompact hook: save state before compaction | research/group-02 | PENDING |
| HK-006 | Implement SessionStart hook: inject fleet knowledge map context | research/group-02 | PENDING |
| HK-007 | Implement FileChanged hook: watch for config changes | research/group-02 | PENDING |
| HK-008 | Per-agent hook configuration via IaC | research/group-02 | PENDING |

### 5.5 AICP Parity (from claw-code-parity research)

| # | Milestone | Source | Status |
|---|-----------|--------|--------|
| AP-001 | Extract 184-tool list from claw-code-parity surface snapshot | research/group-03 | PENDING |
| AP-002 | Classify 122 "missing" tools (relevant vs internal/UI) | research/group-03 | PENDING |
| AP-003 | Identify AICP features missing from Claude Code parity | research/group-03 | PENDING |
| AP-004 | Router decision matrix: which ops need Claude vs LocalAI | research/group-03, §94 | PENDING |

---

## STATUS SUMMARY (EXPANDED)

| Phase | Total | Ready to Test | Pending | Researched |
|-------|-------|--------------|---------|-----------|
| 1: Foundation (F-001 to F-120) | 120 | 36 | 84 | — |
| 2: Infrastructure (I-001 to I-369) | 369 | 1 | 368 | — |
| 3: Features (FT-001 to FT-167) | 167 | 1 | 166 | — |
| 4: Testing & Tuning (T-001 to T-094) | 94 | 0 | 94 | — |
| 5: Knowledge Map (KM-001 to KM-033) | 33 | 0 | 33 | ✓ groups 01-04 |
| 5: Ecosystem Adoption (EA-001 to EA-020) | 20 | 0 | 20 | ✓ groups 01-04 |
| 5: Skills Infrastructure (SK-001 to SK-010) | 10 | 0 | 10 | ✓ group 04 |
| 5: Hooks Infrastructure (HK-001 to HK-008) | 8 | 0 | 8 | ✓ group 02 |
| 5: AICP Parity (AP-001 to AP-004) | 4 | 0 | 4 | ✓ group 03 |
| **TOTAL** | **825** | **38** | **787** | **4 groups** |

**Status definitions:**
- **READY TO TEST** = code exists, unit tests pass, NOT live tested with real agents
- **PENDING** = requirements known, code not written
- **RESEARCHED** = research groups 01-04 complete, findings documented

**Research workflow established:**
1. Research the actual tool/plugin/capability (read repos, docs)
2. Classify per agent role (specialized vs general)
3. Document requirements, directives, usage instructions
4. THEN build

Every item references its source document.
Every item is SRP — one thing per milestone.
PO drives priority and sequencing. No shortcuts.
Nothing is DONE until live tested and verified.
