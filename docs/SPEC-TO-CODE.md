# Spec to Code — Design Specifications vs Implementation Reality

> **69 design docs. 94 core modules. This document maps which specs
> are implemented, which are partially done, which haven't been touched,
> and where code DIVERGES from spec.**
>
> Without this mapping, the design docs and the code are disconnected.
> A developer reads fleet-elevation/07 (architect spec) and has no idea
> if `backend_router.py` already handles what the spec describes or if
> it's completely different. This document answers that question for
> every spec.

---

## 1. Fleet Elevation Specs (31 docs) → Code

### 1.1 Architecture & Structure

| Spec | Code Status | Gap |
|------|-------------|-----|
| **02: Agent Architecture** — file structure, injection order, SRP, onion, template system | **PARTIAL** — file structure exists but injection order NOT verified in gateway code. 0/10 agent CLAUDE.md follow spec. Template validation script NOT built. | CLAUDE.md must be rewritten for ALL 10 agents. Template enforcement needed. |
| **03: Delivery Phases** — phase progressions, standards per phase, PO gates | **IMPLEMENTED** — `phases.py` loads from `config/phases.yaml`. 2 progressions (standard + release). Phase standards defined. `is_phase_gate()` exists. | Phase gate ENFORCEMENT not in orchestrator. Standards not injected into agent context by phase. |
| **04: The Brain** — orchestrator, autocomplete chains, pre-computation | **IMPLEMENTED** — `orchestrator.py` (1378 lines, 9-step cycle). Smart chains exist. Context refresh every 30s. | Autocomplete chain ENGINEERING not done — context doesn't structure response funnel per spec. Brain-evaluated heartbeats NOT implemented. |

### 1.2 Per-Role Specifications

| Spec | CLAUDE.md | HEARTBEAT.md | Role Provider | Notes |
|------|-----------|-------------|---------------|-------|
| **05: Project Manager** | Generic (not per spec) | Custom (not per spec) | ✅ `project_manager_provider` | PM CLAUDE.md needs: stage management, epic breakdown, Plane sync, inter-agent comms per spec |
| **06: Fleet-Ops** | Generic (not per spec) | Custom (not per spec) | ✅ `fleet_ops_provider` | Fleet-ops CLAUDE.md needs: REAL review protocol (not rubber stamp), methodology compliance, budget monitoring |
| **07: Architect** | Generic (not per spec) | Custom (partial) | ✅ `architect_provider` | Architect CLAUDE.md needs: design contribution protocol, ADR format, complexity assessment |
| **08: DevSecOps** | Rich (closest to spec) | Custom (best done) | ✅ `devsecops_provider` | Cyberpunk-Zero has personality. Needs: anti-corruption rules, stage protocol, security_hold documentation |
| **09: Software Engineer** | Generic (not per spec) | Template (stage-aware) | ✅ `worker_provider` | Needs: contribution consumption protocol (design input, QA tests, security reqs), humble expert character |
| **10: DevOps** | Generic (not per spec) | Custom (partial) | ✅ `worker_provider` | Needs: IaC principle documentation, infrastructure contribution protocol |
| **11: QA Engineer** | Generic (not per spec) | Template (stage-aware) | ✅ `worker_provider` | Needs: test PREDEFINITION protocol (tests defined BEFORE implementation), structured test criteria format |
| **12: Technical Writer** | Generic (not per spec) | Template (stage-aware) | ✅ `worker_provider` | Needs: Plane page maintenance protocol, documentation contribution BEFORE/DURING/AFTER work |
| **13: UX Designer** | Generic (not per spec) | Template (stage-aware) | ✅ `worker_provider` | Needs: UX at ALL levels (not just UI), component pattern library, accessibility requirements |
| **14: Accountability** | Minimal | Custom (minimal) | ✅ `worker_provider` | Needs: trail verification protocol, compliance reporting, governance artifacts |

**Summary:** 0/10 CLAUDE.md follow spec. 1/10 HEARTBEAT.md close to spec (devsecops). All role providers implemented.

### 1.3 Cross-Cutting Specs

| Spec | Code Status | Gap |
|------|-------------|-----|
| **15: Cross-Agent Synergy** — contribution matrix, parallel contributions, synergy patterns | **NOT IMPLEMENTED** — `fleet_contribute` MCP tool doesn't exist. Brain doesn't create contribution subtasks. Contribution chain exists in `event_chain.py` but no trigger. | CRITICAL gap. Blocks full agent synergy. |
| **16: Multi-Fleet Identity** — fleet naming, shared Plane, cross-fleet coordination | **NOT IMPLEMENTED** — `federation.py` has fleet identity loading. Agent.yaml doesn't have fleet_id/fleet_number/username per spec. | Needs second machine. Low priority. |
| **17: Standards Framework** — artifact types, quality criteria, per-phase standards | **IMPLEMENTED** — `standards.py` has 7 artifact types. `plan_quality.py`, `pr_hygiene.py`, `skill_enforcement.py`. | Standards not INJECTED into agent context per task type (AR-14). |
| **18: PO Governance** — gates, readiness, authority model | **PARTIAL** — `phases.py` has `is_phase_gate()`. Directives work. PO can set readiness. | Phase gate enforcement not in orchestrator. PO readiness regression not wired. |
| **19: Flow Validation** — diagrams, simulation | **NOT IMPLEMENTED** — design doc only. | Low priority — docs/INTEGRATION.md covers flows textually. |
| **20: AI Behavior** — anti-corruption rules, structural prevention, disease catalogue | **PARTIAL** — 10 anti-corruption rules DEFINED but in 0/10 CLAUDE.md files. Doctor detects 4/11 diseases. Teaching has 8/11 lesson templates. Stage gating IS enforcement. | Anti-corruption rules must go in every CLAUDE.md. 7 disease detections to implement. |
| **21: Task Lifecycle Redesign** — PRE/PROGRESS/POST | **IMPLEMENTED** — `task_lifecycle.py` exists. Fleet_task_accept (PRE), fleet_task_progress (PROGRESS), fleet_task_complete (POST). | Not fully enforced — agents can skip PRE. |
| **22: Milestones** | Tracking doc | N/A |
| **23: Agent Lifecycle** — DROWSY, brain-evaluated heartbeats, strategic Claude calls | **PARTIAL** — `agent_lifecycle.py` has DROWSY state, consecutive_heartbeat_ok, data hash. FleetLifecycle class manages states. | Brain evaluation logic NOT in orchestrator. Strategic Claude call matrix NOT implemented. |
| **24: Tool Call Tree Catalog** | **PARTIAL** — `skill_enforcement.py` has required tools per task type. | Not connected to review gates for confidence scoring. |
| **25-31: Reference docs** | Planning/reference only | N/A |

---

## 2. Agent Rework Specs (14 docs, 20 milestones) → Code

| Milestone | Spec Says | Code Reality | Gap |
|-----------|----------|-------------|-----|
| **AR-01: Fix preembed** | FULL data per role, not compressed | `preembed.py` writes FULL data. `role_providers.py` has 5 providers. | PM doesn't get Plane sprint. Workers don't get artifact completeness. Per-role data is functional but NOT per full AR-01 spec. |
| **AR-02: Wake PM** | Detect unassigned → wake PM session | **IMPLEMENTED** in `orchestrator.py:761-807`. `inject_content()` via gateway. 120s cooldown. | Wake message has FULL task details. ✅ Matches spec. |
| **AR-03: Wake fleet-ops** | Detect reviews → wake fleet-ops | **IMPLEMENTED** in `orchestrator.py:809-830`. Same pattern as PM. | ✅ Matches spec. |
| **AR-04: PM HEARTBEAT** | Full rewrite: PO directives → assign → stages → sprint → Plane → comms | **NOT PER SPEC** — custom HEARTBEAT.md exists but doesn't follow fleet-elevation/05 heartbeat priority. | Needs complete rewrite per spec. |
| **AR-05: Fleet-ops HEARTBEAT** | REAL review: read work, compare to verbatim, check trail | **NOT PER SPEC** — custom HEARTBEAT.md exists, doesn't enforce real review protocol. | Needs complete rewrite per spec. |
| **AR-06: Architect HEARTBEAT** | Design contributions, complexity assessment, ADRs | **NOT PER SPEC** — custom HEARTBEAT.md exists, doesn't follow fleet-elevation/07 protocol. | Needs rewrite. |
| **AR-07: DevSecOps HEARTBEAT** | Security contributions BEFORE implementation, PR review, security_hold | **CLOSEST TO SPEC** — structured workflow, uses fleet tools, security-focused. | Could use anti-corruption rules and stage protocol additions. |
| **AR-08: Worker HEARTBEAT** | Stage-aware: conversation→analysis→investigation→reasoning→work, progressive artifacts | **FUNCTIONAL** — template HEARTBEAT.md IS stage-aware with MUST/MUST NOT per stage. | Template is good. Per-role VARIATIONS (QA predefinition, writer continuous docs) not differentiated. |
| **AR-09: Agent.yaml updates** | fleet_id, fleet_number, username, roles | **NOT DONE** — agent.yaml has name, type, mode, backend, capabilities. Missing: fleet_id, roles.primary, roles.contributes_to. | Needs update for all 10 agents. |
| **AR-10: Per-agent CLAUDE.md** | Role-specific per fleet-elevation specs | **NOT DONE** — 0/10 follow spec. Devsecops is closest. | CRITICAL — blocks everything. |
| **AR-11: Plane data for PM** | PM heartbeat pre-embed includes Plane sprint data | **NOT DONE** — `heartbeat_context.py` has `plane_sprint`, `plane_new_items` fields but orchestrator doesn't populate them. | Wire Plane data into PM's role_provider. |
| **AR-12: Artifact pre-embed** | Workers get artifact completeness pre-embedded | **PARTIAL** — `context_assembly.py` assembles artifact data from Plane via transpose. | Not reliably included in heartbeat context for workers. |
| **AR-13: Inter-agent comms** | fleet_chat in heartbeat flows, agents communicate about work | **PARTIAL** — fleet_chat works. Messages @mention-routed to heartbeat context. | Agents don't proactively communicate per heartbeat protocol. Needs HEARTBEAT.md rewrite. |
| **AR-14: Standards in context** | Relevant standards injected based on current artifact type | **NOT DONE** — standards exist in `standards.py`. Not injected into agent context. | Wire standard for current artifact type into task context. |
| **AR-15–20: Live tests** | 35+ live test scenarios | **0/35 DONE** | ZERO live tests with real agents. |

---

## 3. Subsystem Specs (24 docs) → Code

### Immune System (7 docs)

| Doc | What It Specifies | Code Match |
|-----|------------------|-----------|
| 01-overview | Three systems working together | ✅ All three systems built |
| 02-the-doctor | Detection patterns, response actions | ✅ `doctor.py` — 4/11 detections implemented |
| 03-disease-catalogue | 11 disease categories | ✅ `teaching.py` DiseaseCategory enum — all 11 defined |
| 04-research-findings | Disease patterns from real fleet behavior | Reference doc — no code needed |
| 05-detection | Detailed detection algorithms | ⚠️ 4 implemented, 7 designed but not coded |
| 06-response | Response escalation (teach → compact → prune) | ✅ `decide_response()` in doctor.py |
| 07-integration | How immune system connects to methodology + teaching | ✅ Doctor imports from methodology + teaching. MCP stage gate is structural prevention. |

### Teaching System (1 doc)

| Doc | What It Specifies | Code Match |
|-----|------------------|-----------|
| 01-overview | Adapted lessons, injection, verification | ✅ `teaching.py` — 8/11 templates, adapt_lesson(), evaluate_response(), LessonTracker |

### Methodology System (8 docs)

| Doc | What It Specifies | Code Match |
|-----|------------------|-----------|
| 01-overview | 5 stages, readiness, progression | ✅ `methodology.py` — Stage enum, stage checks, readiness values |
| 02-conversation | Conversation protocol | ✅ `stage_context.py` — CONVERSATION instructions |
| 03-analysis | Analysis protocol | ✅ `stage_context.py` — ANALYSIS instructions |
| 04-investigation | Investigation protocol | ✅ `stage_context.py` — INVESTIGATION instructions |
| 05-reasoning | Reasoning protocol | ✅ `stage_context.py` — REASONING instructions |
| 06-work | Work protocol | ✅ `stage_context.py` — WORK instructions + tool sequence |
| 07-standards | Artifact standards per type | ✅ `standards.py` — 7 artifact types with required fields |
| new-custom-fields | Task custom fields for methodology | ✅ `models.py` TaskCustomFields — task_stage, task_readiness, requirement_verbatim |

### Context System (8 docs)

| Doc | What It Specifies | Code Match |
|-----|------------------|-----------|
| 01-overview | Context bundle architecture | ✅ `context_assembly.py` — two assembly functions |
| 02-task-mcp | Task context via MCP | ✅ `fleet_task_context()` MCP tool |
| 03-task-preembed | Task pre-embed in dispatch | ✅ `preembed.py` — `build_task_preembed()` |
| 04-heartbeat-mcp | Heartbeat context via MCP | ✅ `fleet_heartbeat_context()` MCP tool |
| 05-heartbeat-preembed | Heartbeat pre-embed | ✅ `preembed.py` — `build_heartbeat_preembed()` + `heartbeat_context.py` HeartbeatBundle |
| 06-mcp-layer-upgrade | Smart chains, group calls | ✅ `smart_chains.py` — DispatchContext, CompletionChain |
| 07-integration | Context ↔ methodology ↔ artifacts | ✅ `context_assembly.py` includes methodology state + artifact completeness |
| 08-milestones | CB01-CB05 milestones | ⚠️ Functional but not all per spec |

---

## 4. Strategic Design Specs (6 docs, 47 milestones) → Code

| System | Milestones | Unit Tests | Integration Tests | Live Tests | Code Matches Spec? |
|--------|-----------|-----------|-------------------|-----------|-------------------|
| **Labor Attribution** | M-LA01-08 | 44 ✅ | 5 ✅ | 0 | ✅ Yes — LaborStamp, tiers, analytics per spec |
| **Budget Mode** | M-BM01-06 | 93 ✅ | 4 ✅ | 0 | ✅ Yes — 6 modes, constraints, auto-transition per spec |
| **Multi-Backend Router** | M-BR01-08 | 73 ✅ | 5 ✅ | 0 | ✅ Yes — 4 backends, routing, fallback, health per spec |
| **Iterative Validation** | M-IV01-08 | 178 ✅ | 0 | 0 | ✅ Yes — 4 types, budget-aware, deferred queue per spec |
| **Model Upgrade** | M-MU01-08 | 130 ✅ | 4 ✅ | 0 | ✅ Yes — shadow, promote, tier, benchmark per spec |
| **Storm Prevention** | M-SP01-09 | 90 ✅ | 5 ✅ | 0 | ✅ Yes — 9 indicators, 5 severity, circuit breakers per spec |

**All 47 strategic milestones match their design specs.** The code implements what the docs describe. The gap is live testing — none of these have been tested with real agents.

---

## 5. What DIVERGES From Spec

Places where code does something DIFFERENT from what the spec says:

| Area | Spec Says | Code Does | Impact |
|------|----------|-----------|--------|
| **Agent file injection order** | IDENTITY→SOUL→CLAUDE→TOOLS→AGENTS→context→HEARTBEAT | **UNVERIFIED** — gateway is vendor code, order not confirmed | Could affect AI behavior if order is wrong |
| **CLAUDE.md max 4000 chars** | Gateway enforces 4000 char limit | **UNVERIFIED** — no current CLAUDE.md approaches limit | Will matter when rewritten per spec |
| **Contribution flow** | Brain creates parallel subtasks at REASONING stage | **NOT IN CODE** — no contribution logic in orchestrator | Largest functional gap |
| **Brain-evaluated heartbeats** | DROWSY/SLEEPING agents get deterministic evaluation | **NOT IN CODE** — all agents get Claude calls | Cost gap — sleeping agents cost money |
| **Stage-gated tool access** | More tools should be stage-restricted | **PARTIAL** — only fleet_commit + fleet_task_complete blocked | Spec implies broader gating |
| **Review gates** | QA, architect, devsecops review before approval | **review_gates exist in fleet_task_complete** but reviewers don't actually receive review tasks | Review chain not operational |
| **HeartbeatBundle vs preembed** | Should be unified | **TWO parallel systems** — heartbeat_context.py builds HeartbeatBundle, preembed.py builds markdown text separately | Duplication, different data |

---

## 6. What's NOT In Any Spec But Exists In Code

Modules that were built without a design spec:

| Module | Lines | What It Does | Why No Spec |
|--------|-------|-------------|-------------|
| `session_telemetry.py` | 230 | Parse Claude Code JSON, distribute to systems | Built during this session (W8) |
| `codex_review.py` | 313 | Codex plugin trigger/decision layer | Researched and built in-session |
| `router_unification.py` | 62 | FUTURE schema for AICP bridge | Schema created ahead of implementation |
| `dual_gpu.py` | 78 | FUTURE schema for dual GPU | Schema created ahead of hardware |
| `turboquant.py` | 48 | FUTURE schema for TurboQuant | Schema created ahead of ecosystem |
| `cluster_peering.py` | varies | FUTURE schema for multi-machine | Schema created ahead of hardware |
| All 8 integration wires (W1-W8) | ~200 | Cross-system connection code | Built to connect existing systems |

---

## 7. The Critical Path — What Spec Work Blocks Live Testing

```
BLOCKER 1: AR-10 (Per-agent CLAUDE.md)
  Spec: fleet-elevation/02, 05-14, 20
  Code: 0/10 CLAUDE.md follow spec
  Impact: Agents don't have anti-corruption rules, stage protocol,
          contribution model, tool chains, boundary setting
  Work: 20-40 hours of careful writing

BLOCKER 2: AR-04-08 (Per-role HEARTBEAT.md)
  Spec: fleet-elevation/05-14, agent-rework/04-08
  Code: Template exists, per-role rewrites not done
  Impact: PM doesn't follow PM protocol, fleet-ops doesn't follow
          review protocol, workers don't differentiate by role
  Work: 5-10 hours

BLOCKER 3: fleet-elevation/15 (Contribution Flow)
  Spec: Parallel contributions before work
  Code: fleet_contribute MCP tool NOT built
  Impact: Specialists can't contribute before implementation
  Work: 8-16 hours (tool + brain logic + context)

BLOCKER 4: AR-01 (Full Pre-Embed)
  Spec: PM gets Plane sprint, workers get artifacts
  Code: Functional but not per full spec
  Impact: Agents work with incomplete awareness
  Work: 4-8 hours

After fixing these: FIRST LIVE TEST POSSIBLE
```

---

## 8. Reading This Document

For each milestone/task:
1. Find the spec in this document
2. Check "Code Status" column
3. If ✅ → code matches spec, proceed to testing
4. If ⚠️ PARTIAL → read the Gap column, implement what's missing
5. If ❌ NOT DONE → read the spec, implement from scratch
6. After implementation → update this document's status

This is a LIVING document. As specs are implemented, status changes
from ❌ to ⚠️ to ✅. When everything is ✅, the fleet is spec-complete.
