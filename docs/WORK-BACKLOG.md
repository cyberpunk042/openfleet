# Work Backlog — Every Gap Consolidated

> **Every "What's Needed" from all 22 system docs, consolidated into
> one prioritized backlog. Categorized by what BLOCKS live testing vs
> what improves quality vs what's future optimization.**

---

## 1. BLOCKERS — Must Fix Before First Live Test

### B0: Agent Directory Cleanup (BEFORE writing agent files)

**Source:** agent-directory-cleanup.md
**Work:** Restructure agents/ so templates+config are committed, agent directories are fully untracked runtime output. Create provision script. Update .gitignore. Move accountability src/ to fleet module.
**Why first:** New CLAUDE.md files must go into `_template/CLAUDE.md/{role}.md`, not `agents/{name}/CLAUDE.md`. If we write B1 before B0, the files go in the wrong place.
**Effort:** 4-8 hours

### B1: Agent CLAUDE.md (0/10 per spec)

**Source:** SPEC-TO-CODE §1.2, fleet-elevation/02+05-14+20, AR-10
**Systems:** All agents
**Work:** Write role-specific CLAUDE.md for all 10 agents. Max 4000 chars each. Include:
- 10 anti-corruption rules (fleet-elevation/20)
- Stage protocol per role
- Tool → chain documentation per role
- Contribution model (what agent contributes to others)
- Boundary setting (what agent does NOT do)

**Read before writing:** fleet-elevation/02 (structure), fleet-elevation/{role number} (per-role spec), fleet-elevation/20 (anti-corruption), fleet-elevation/15 (synergy)
**Effort:** 20-40 hours (2-4h per agent × 10 agents)

### B2: Agent HEARTBEAT.md (1/10 per spec)

**Source:** SPEC-TO-CODE §2, fleet-elevation/05-14, agent-rework/04-08
**Systems:** All agents
**Work:** 5 unique heartbeats:
- PM: PO directives → unassigned tasks → stage progression → epic breakdown → sprint → Plane → comms
- Fleet-ops: PO directives → REAL review (not rubber stamp) → compliance → health → budget → immune
- Architect: contributions → complexity → ADRs → progressive artifacts
- DevSecOps: security contributions → PR review → infra health → crisis
- Worker template: stage-aware with per-role variations (QA predefinition, writer continuous docs)

**Effort:** 5-10 hours

### B3: Template Files Deployed

**Source:** SPEC-TO-CODE §1.1, fleet-vision-architecture-part2 §27
**Work:** Copy `MC_WORKFLOW.md`, `STANDARDS.md`, `MC_API_REFERENCE.md` from `_template/` to each agent directory. Or verify gateway reads from `_template/` automatically.
**Effort:** 1 hour

### B4: Agent.yaml Updates

**Source:** SPEC-TO-CODE §2 (AR-09)
**Work:** Add to all 10 agent.yaml: fleet_id, fleet_number, username, roles.primary, roles.contributes_to, heartbeat_config
**Effort:** 2 hours

---

## 2. HIGH PRIORITY — Needed for Effective Fleet Operation

### H1: Contribution Flow (fleet_contribute)

**Source:** fleet-elevation/15, SPEC-TO-CODE §1.3, INTEGRATION.md Flow 6
**Systems:** MCP Tools, Orchestrator, Context, Methodology
**Work:**
1. Build `fleet_contribute` MCP tool
2. Build brain logic: task enters REASONING → create parallel contribution subtasks
3. Build `fleet_request_input` MCP tool
4. Pre-embed contributions into worker task context
**Chain builder exists:** `build_contribution_chain()` in event_chain.py
**Effort:** 8-16 hours

### H2: Session Telemetry Wired to Runtime

**Source:** docs/systems/19-session, every system doc mentions "W8 not wired"
**Systems:** Labor, Budget, Storm, Health (all waiting for real data)
**Work:** Orchestrator calls `to_labor_fields()`, `to_claude_health()`, `to_storm_indicators()`, `to_cost_delta()` from session_telemetry.py
**Adapter exists:** 230 lines, 30 tests. Just needs wiring.
**Effort:** 2-4 hours

### H3: Full Pre-Embed per Role (AR-01)

**Source:** agent-rework/02, docs/systems/19-session, SPEC-TO-CODE §2
**Systems:** Context, Orchestrator
**Work:**
- PM gets Plane sprint data in pre-embed
- Workers get artifact completeness + suggested readiness
- All agents get contributions received (after H1)
**Effort:** 4-8 hours

### H4: Standards Injection (AR-14)

**Source:** fleet-elevation/17, docs/systems/09-standards
**Systems:** Standards, Context
**Work:** Inject relevant standards into agent context based on current task artifact type. Agent producing an analysis_document should see analysis_document standard in context.
**Effort:** 2-4 hours

### H5: Brain-Evaluated Heartbeats

**Source:** fleet-elevation/23, docs/systems/06-agent-lifecycle, 22-agent-intelligence
**Systems:** Lifecycle, Orchestrator
**Work:** When agent is DROWSY/SLEEPING, brain evaluates deterministically (no Claude call): data hash changed? Task assigned? @mention? Directive? Role-specific trigger?
**Data structures exist:** consecutive_heartbeat_ok, last_heartbeat_data_hash in AgentState
**Effort:** 4-8 hours
**Impact:** ~70% cost reduction on idle fleet

### H6: Ecosystem Tier 1

**Source:** ecosystem-deployment-plan.md
**Work:**
- E-01: Enable prompt caching (90% savings, config change)
- E-02: Install Claude-Mem plugin (cross-session memory)
- E-03: Install Context7 plugin (library docs for architect+engineer)
- E-04: Filesystem MCP per agent (structured file ops)
**Effort:** 1-2 hours
**Impact:** 40-60% cost reduction, better agent awareness

### H7: Qwen3.5 Models

**Source:** docs/systems/16-models §8
**Work:** Download Qwen3.5-4B and Qwen3.5-9B GGUF. Create model YAML configs. Run `make optimize-models`. Benchmark against fleet prompts.
**Effort:** 2-4 hours

---

## 3. MEDIUM PRIORITY — Quality Improvements

### M1: Missing Disease Detections (7 of 11)

**Source:** docs/systems/02-immune-system §8
**Work:** Implement: abstraction, code_without_reading, scope_creep, cascading_fix, context_contamination, not_listening, compression
**Depends on:** Some need contribution flow (contribution_avoidance, synergy_bypass)
**Effort:** 8-16 hours

### M2: Missing Artifact Renderers (5)

**Source:** docs/systems/10-transpose §10
**Work:** Add renderers for: security_assessment, qa_test_definition, ux_spec, documentation_outline, compliance_report
**Effort:** 4-8 hours

### M3: Challenge → Review Flow Connection

**Source:** docs/systems/15-challenge §9
**Work:** Challenge results available to fleet-ops during review. Trainee tier triggers challenge before approval.
**Effort:** 4-8 hours

### M4: Cross-Reference Execution

**Source:** docs/systems/18-notifications §10
**Work:** `generate_cross_refs()` returns refs but no caller executes them. Wire into event chain execution.
**Effort:** 2-4 hours

### M5: Event Cleanup

**Source:** docs/systems/04-event-bus §10
**Work:** JSONL grows without bound. Implement rotation/archival strategy.
**Effort:** 2-4 hours

### M6: HeartbeatBundle ↔ Preembed Unification

**Source:** docs/systems/19-session §7
**Work:** heartbeat_context.py and preembed.py produce overlapping data. Unify into one path.
**Effort:** 4-8 hours

### M7: Phase Gate Enforcement

**Source:** docs/systems/01-methodology §10, SPEC-TO-CODE §1.1
**Work:** Orchestrator enforces PO approval at phase boundaries. `is_phase_gate()` exists, enforcement doesn't.
**Effort:** 2-4 hours

### M8: Escalation Logic

**Source:** docs/systems/22-agent-intelligence §2
**Work:** Dynamic escalation of effort/model/source/session based on complexity, confidence, budget, outcomes. `decide_claude_call()` in orchestrator.
**Effort:** 4-8 hours

---

## 4. LOW PRIORITY — Future Optimization

### L1: Per-Agent Autonomy Config

**Source:** docs/systems/22-agent-intelligence §1
**Work:** `config/agent-autonomy.yaml` with per-role thresholds and wake triggers
**Effort:** 2-4 hours

### L2: OpenRouter Client

**Source:** docs/systems/14-router §9, ecosystem plan
**Work:** Build client for 29 free models
**Effort:** 4-8 hours

### L3: The Lounge Deployment (M92-96)

**Source:** docs/systems/18-notifications §10
**Work:** Deploy web IRC client for PO visibility
**Effort:** 2-4 hours

### L4: LocalAI RAG → Fleet

**Source:** docs/systems/22-agent-intelligence §3.3, ecosystem plan E-09
**Work:** Wire AICP rag.py + kb.py into fleet agent context
**Effort:** 8-16 hours

### L5: AICP ↔ Fleet Bridge

**Source:** docs/systems/14-router §9, ecosystem plan E-12
**Work:** router_unification.py bridge
**Effort:** 8-16 hours

### L6: FleetControlBar Frontend (M-CS01-10)

**Source:** docs/systems/05-control-surface §10
**Work:** TSX component in DashboardShell.tsx header
**Effort:** 8-16 hours

### L7: Multi-Fleet Identity

**Source:** SPEC-TO-CODE §1.3, fleet-elevation/16
**Work:** Agent naming, shared Plane, cross-fleet coordination
**Depends on:** Second machine
**Effort:** 8-16 hours

### L8: TurboQuant Integration

**Source:** docs/systems/16-models §8.3
**Work:** When llama.cpp merges (Q3 2026), update model YAMLs
**Depends on:** llama.cpp merge
**Effort:** 1-2 hours (config only)

### L9: Agent Teams Evaluation

**Source:** docs/systems/21-agent-tooling §8.4, ecosystem plan E-11
**Work:** Enable `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, pilot on one epic
**Effort:** 4-8 hours

### L10: Batch API

**Source:** ecosystem plan E-10
**Work:** Route non-urgent work through Batch API (50% savings)
**Effort:** 2-4 hours

---

## 5. Summary

| Category | Items | Total Effort |
|----------|-------|-------------|
| **BLOCKERS** (must fix) | B1-B4 | 28-53 hours |
| **HIGH** (needed for effective operation) | H1-H7 | 23-46 hours |
| **MEDIUM** (quality improvements) | M1-M8 | 30-60 hours |
| **LOW** (future optimization) | L1-L10 | 47-98 hours |
| **TOTAL** | **30 items** | **128-257 hours** |

Realistic timeline to spec-complete fleet: **4-8 weeks of focused work.**

Realistic timeline to first live test: **Blockers only = 1-2 weeks.**
