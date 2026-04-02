# System Manuals — Condensed Versions (22 Systems)

**Part of:** Fleet Knowledge Map → System Manuals branch
**Purpose:** Key concepts per system (~50 lines each). Used in Sonnet 200K injection profile.
**Full versions:** docs/systems/01-22 (10,283 lines total)

---

## System 01: Methodology (877 lines, 3 files)

5-stage progression: CONVERSATION → ANALYSIS → INVESTIGATION → REASONING → WORK. Each stage has boolean gate checks that ALL must pass. Work requires readiness ≥ 99 (PO confirmed). Task types skip stages (subtasks start at reasoning, spikes never reach work). Stage instructions injected via stage_context.py into agent context. MCP enforcement: WORK_ONLY_TOOLS blocks fleet_commit/fleet_task_complete outside work stage → protocol_violation event → doctor → teaching. Readiness values are discrete: 0,5,10,20,30,50,70,80,90,95,99,100. MethodologyTracker records transitions. Delivery phases (poc/mvp/staging/production) are separate from stages — phases track deliverable maturity, PO declares. Not implemented: contribution flow at reasoning stage, standards injection, phase gate enforcement. 55+ tests.

## System 02: Immune System (746 lines, 3 files)

Three defense lines: structural prevention (stage gating, verbatim anchoring), detection (doctor runs hidden every 30s), correction (teach/compact/prune/escalate). Doctor has 4 of 11 detections: protocol_violation, laziness (<2min/SP or <80% criteria), stuck (60min no activity), correction_threshold (3+ corrections → prune). 7 unimplemented: abstraction, code_without_reading, scope_creep, cascading_fix, context_contamination, not_listening, compression. Behavioral security scanner (Step 1): 10 regex patterns for credential exfil, DB destruction, security disable. Critical → security_hold. Self-healing (Step 8): plans actions for stuck tasks, offline agents. AgentHealth profiles persist across cycles. Doctor is HIDDEN from agents to prevent gaming. 50+ tests.

## System 03: Teaching System (485 lines, 1 file)

Treatment arm of immune system. Pipeline: doctor detects → adapt_lesson() fills template with {requirement_verbatim}, {current_stage}, {what_agent_did} → inject via gateway → agent completes exercise → evaluate_response() checks 4 indicators (references requirement, acknowledges mistake, substance >100 chars, doesn't parrot). Score 2+/4 → verified. Max 3 attempts before prune. 8 of 11 templates registered. Templates are deterministic, free, instant — no LLM. Key insight: "Seeing the pattern does not break the pattern, it's forging the right path multiple times." 25+ tests.

## System 04: Event Bus (1248 lines, 4 files)

Fleet nervous system. 47 event types across 9 domains. 6 surfaces: INTERNAL (MC, required), PUBLIC (GitHub, required for code), CHANNEL (IRC, optional), NOTIFY (ntfy, optional), PLANE (optional), META (optional). 8 chain builders: task_complete fires ALL 6 surfaces. 5-level routing: DIRECT → PRIORITY → MENTIONS → TAG MATCH → BROADCAST. JSONL append-only storage with per-agent seen tracking. EventStore supports query with filters. Agent feeds filtered by tag subscriptions. Not implemented: event cleanup/rotation, full Plane handlers, mention routing reliability. 60+ tests.

## System 05: Control Surface (189 lines, 2 files)

PO controls fleet via 3 independent axes: Work Mode (full-autonomous to work-paused), Cycle Phase (execution to crisis-management), Backend Mode (claude/localai/hybrid). Read from OCMC board fleet_config JSON every cycle. Gates: should_dispatch(), should_pull_from_plane(), get_active_agents_for_phase(). PO directives via tagged board memory (directive + to:{agent} + optional urgent). Mode changes emit events + IRC. Not implemented: frontend UI (FleetControlBar), directive processed tagging. 35+ tests.

## System 06: Agent Lifecycle (423 lines, 2 files)

States: ACTIVE → IDLE → SLEEPING → OFFLINE. Content-aware transitions (HEARTBEAT_OK count) + time-based fallbacks. Silent heartbeat design: gateway cron fires → brain intercepts → if IDLE/SLEEPING, evaluate deterministically ($0): mentions? tasks? contributions? directives? → wake or stay silent. PR authority matrix: only architect/QA/devsecops/fleet-ops can reject. Fleet-ops final authority. Rejection auto-creates fix task. CRITICAL GAP: brain interception layer NOT implemented — sleeping agents still get expensive Claude calls. ~70% cost savings blocked. 35+ tests.

## System 07: Orchestrator (2595 lines, 8 files)

The brain. 9-step cycle every 30s: Step 0 refresh contexts (FULL data, all agents), Step 1 security scan, Step 2 doctor, Step 3 ensure approvals, Step 4 wake drivers (PM on unassigned, fleet-ops on reviews, 120s cooldown), Step 5 dispatch (10 gates: work_mode, storm, budget, readiness≥99, agent, blocked, busy, doctor, phase, max/cycle), Step 6 directives, Step 7 parent evaluation, Step 8 health check. Pre-checks: storm severity, gateway duplication, fleet mode. NEVER creates Claude sessions (gateway does). Writes files, not API calls, for context delivery. Supporting: context_assembly, preembed, context_writer, role_providers (5), change_detector, smart_chains, driver. Not implemented: brain-evaluated heartbeats, contribution subtasks, full role pre-embed, strategic Claude call config. 75+ tests.

## System 08: MCP Tools (2517 lines, 3 files)

25 agent operations via FastMCP stdio server. Stage gating: WORK_ONLY_TOOLS blocks fleet_commit/fleet_task_complete outside work. fleet_task_complete is the flagship — one call: push → PR → MC update → approval → IRC → ntfy → Plane → event (12+ operations). 6 categories: task lifecycle (6), communication (5), review (1), fleet awareness (3), Plane (7), artifacts (3). Tool pattern: context → validate → resolve → primary action → side effects (try/except each) → result. 3 missing: fleet_contribute, fleet_request_input, fleet_gate_request. 40+ tests.

## System 09: Standards (739 lines, 4 files)

7 artifact type standards with required/optional fields and quality criteria. Plan quality assessment at fleet_task_accept: 4 dimensions (steps 40pts, verification 30pts, risks 20pts, length 10pts), keyword-based, free. PR hygiene: 5 issue types (conflicting, stale, duplicate, orphaned, long-open). Tool enforcement: required MCP tools per task type (tasks need read+accept+commit+complete, epics MUST create subtasks). Compliance feeds artifact completeness → readiness suggestions → gates work stage. Not implemented: standards injection into context, phase-dependent bars, contribution artifact types. 50+ tests.

## System 10: Transpose (573 lines, 2 files)

Bidirectional structured object ↔ rich HTML for Plane. to_html: type-specific renderer → rich HTML + hidden JSON data blob (fleet-data span, display:none). from_html: regex extracts hidden JSON → dict. 7 renderers (analysis, investigation, plan, progress, bug, completion, PR). Content OUTSIDE artifact markers NEVER touched. Progressive work: agent fills fields across cycles, completeness rises, PO reviews at 100%. Suggested readiness via 8-tier scale. Not implemented: 5 contribution renderers, quality enhancements, live Plane round-trip. 35+ tests.

## System 11: Storm Prevention (1440 lines, 4 files)

9-10 indicators with confirmation windows (60-300s, gateway_dup immediate). 5 severity levels: CLEAR → WATCH → WARNING (dispatch≤1, diagnostic snapshot) → STORM (dispatch=0, alert PO) → CRITICAL (halt cycle). De-escalation slower than escalation. Circuit breakers per-agent and per-backend (3 failures → OPEN, cooldown doubles, max 1hr). Diagnostic snapshots on WARNING+. Post-incident reports: peak severity, duration, root cause, cost, prevention. Built after March catastrophe. Not implemented: session telemetry feeding indicators, aggregate_context (#10), auto-post reports. 90 tests — highest of any system.

## System 12: Budget (4 files)

Budget mode = tempo setting (orchestrator cycle speed, heartbeat frequency), NOT cost envelope. Independent from backend_mode and model selection. Real quota monitoring via Claude OAuth API: weekly ≥90% PAUSE, session ≥95% PAUSE, fast climb +5%/10min PAUSE. Cached 5 minutes. Mode definitions TBD. Cost optimization potential: silent heartbeats ~70%, prompt caching ~90%, LocalAI routing ~100% simple tasks, batch API ~50%. Only quota monitoring is implemented.

## System 13: Labor Attribution (901 lines, 3 files)

Every artifact carries a labor stamp: agent, backend, model, confidence tier (expert/standard/trainee/community auto-derived from backend+model), cost, duration, tokens, lines changed, skills, challenge rounds. Trainee/community → mandatory adversarial challenge. Heartbeat cost tracking: per-agent average, anomaly detection (>2x), alert if heartbeats >30% of total. Analytics: rolling 500 stamps, per-agent/model/tier metrics. NOT WIRED: session telemetry not feeding real values, stamps not populated at completion, orchestrator doesn't call heartbeat stamps. 59+ tests.

## System 14: Multi-Backend Router (1611 lines, 5 files)

4 backends: claude-code (paid, expert/standard), localai (free, trainee), openrouter-free (free, community), direct (no LLM). Routing: assess complexity → filter by backend_mode → cheapest capable → health check → circuit breaker → RoutingDecision. Security/architecture agents NEVER go to free/trainee. Fallback: LocalAI → OpenRouter → sonnet → opus → queue. Model swap management for 8GB VRAM: skip-swap logic (next 3 tasks need current model? don't swap). Codex review trigger: trainee/community tiers. NOT DONE: connected to real dispatch, live LocalAI test, OpenRouter client, AICP bridge. 141 tests.

## System 15: Challenge Engine (2831 lines, 8 files)

Largest system. 4 types: AUTOMATED (free, 7 regex pattern checks), AGENT (domain expert, costs tokens), CROSS-MODEL (different LLM), SCENARIO (reproduce-and-break for bugs). Depth by confidence tier: trainee/community MANDATORY 3 rounds, standard 2 rounds SP≥5, expert optional 1. Findings lifecycle: OPEN → ADDRESSED → VERIFIED → WONT_FIX → INVALID. Progress: 70% work complete → 80% challenge passed → 90% review passed → 95% PO approved → 100% done. Deferred queue persists to JSON. Analytics feed teaching signals. NOT WIRED: not in review flow, no live test, no LocalAI cross-model, deferred drain not in orchestrator. 235 tests.

## System 16: Model Management (1767 lines, 9 files)

Full model lifecycle: select (SP + type + role → model/effort), benchmark (fleet-specific prompts not generic), shadow route (dual-run, 80% upgrade-worthy → ready), promote (PO decides with evidence, post-promotion health: ≥90% baseline = healthy, <70% = auto rollback), tier progression (trainee → validated → standard → expert per model per task type). 6 LocalAI configs. Recommended: Qwen3.5-4B/9B to replace hermes-3b. Future: dual_gpu, turboquant (Q3 2026), cluster_peering. NOT DONE: Qwen models not configured, real benchmarks never run, shadow routing untested. 130 tests.

## System 17: Plane Integration (1208 lines, 4 files)

Two surfaces: Plane (PO strategic — issues, sprints, modules) and OCMC (agent operational — work queue). Two-level task model: PM selects Plane issues → creates PM tasks on OCMC → each spawns 10-20+ ops tasks. Methodology via Plane labels (stage:X, readiness:N). Verbatim in description HTML via hidden spans. PlaneSyncer: ingest, push completions, sync fields, sync metadata. NOT IMPLEMENTED: ops comment → Plane sync, PM pre-embed sprint data, writer auto-update, full artifact HTML. 40+ tests.

## System 18: Notifications (536 lines, 3 files)

3 priority levels: INFO (silent ntfy), IMPORTANT (badge+sound), URGENT (full-screen + Windows toast). 300s deduplication cooldown. Cross-reference engine: generate_cross_refs(event) → list of CrossReference actions across 9 event types. URL resolution config-driven. IRC channels: #fleet, #alerts, #reviews, #sprint, #gates, #contributions. NOT DONE: The Lounge, channel creation, ntfy topics, cross-reference EXECUTION (generator built but no caller). 35+ tests.

## System 19: Session and Context (1157 lines, 5 files)

Data backbone. Every 30s: MC API (cached, 10 agents = 1 call) → per-agent: tasks + messages + directives + role_data → HeartbeatBundle (20+ fields, FULL, not compressed) → write context/ files → gateway injects → agent wakes knowing everything. Session telemetry adapter: Claude Code JSON → SessionSnapshot → distributes to labor/health/storm/cost. Context assembly: 7 sections for task, 5 role providers for heartbeat. NOT WIRED: telemetry not connected (systems use estimates), full role pre-embed missing, contribution data missing. 65+ tests.

## System 20: Infrastructure (1908 lines, 8 clients + scripts)

8 typed clients: gateway (WebSocket RPC), MC (REST + SQLite cache), Plane (REST), IRC (via gateway WS), ntfy (HTTP push), GitHub (gh CLI), config (YAML loader), cache (SQLite TTL). IaC scripts for setup. Ecosystem gap: researched 5400+ skills, 9000+ plugins, 1000+ MCP servers. Deployed: codex plugin, statusline, KV cache, Flash Attention, .claudeignore, Docker /data, function calling grammar. Immediate wins available: prompt caching (param change), Claude-Mem (install), MCP servers (config). 30+ tests.

## System 21: Agent Tooling (specification)

Per-role tool specialization spec. Currently all agents share generic mcp.json with fleet MCP only. Specifies per-role needs: MCP servers, plugins, skills, commands. Maps Claude Code's 6 extension points (MCP, subagents, hooks, skills, plugins, Agent Teams) and 5 config layers (rules, memory, keybindings, statusline, settings). Agent Teams evaluation needed (complement vs compete with orchestrator). Tool → methodology stage mapping defined. NOTHING BUILT — this is specification only.

## System 22: Agent Intelligence (specification)

Cross-cutting spec: autonomy tuning (per-role adaptive thresholds, silent heartbeats → 70% idle savings), escalation (5 dimensions: effort/model/backend/session/turns), three-tier decision model (brain $0 / LocalAI free / Claude paid), context endgame (organic flow at 7%/5% remaining, rate limit rollover spike prevention via pre-compaction, aggregate fleet context math), autocomplete chain (8-layer onion: identity → soul → CLAUDE.md → TOOLS.md → AGENTS.md → context → HEARTBEAT), 4-layer context recovery (pre-embed / auto-memory / Claude-Mem / fleet RAG). ENTIRELY SPECIFICATION — adaptive thresholds, brain evaluation, escalation engine, per-role agent files not built.
