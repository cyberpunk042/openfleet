# System Manuals — Minimal Versions (22 Systems)

**Part of:** Fleet Knowledge Map → System Manuals branch
**Purpose:** One-paragraph essence per system (~5 lines each). Used in LocalAI 8K injection profile.
**Condensed versions:** knowledge-map/system-manuals-condensed.md
**Full versions:** docs/systems/01-22 (10,283 lines total)

---

**01 Methodology:** Forces agents through 5 stages (conversation→analysis→investigation→reasoning→work) before code. Boolean gate checks must ALL pass. Work requires PO-confirmed readiness ≥99%. Stage-gated MCP tools block fleet_commit outside work stage. 877 lines, 55+ tests, fully implemented except contribution flow and phase gates.

**02 Immune System:** Hidden doctor detects agent diseases (protocol violations, laziness, stuck, 3+ corrections) every 30s. Behavioral security scans for credential exfiltration. Responses: teach, compact, prune, escalate. Per-agent health profiles persist. 4 of 11 detections implemented. 746 lines, 50+ tests.

**03 Teaching:** Injects adapted lessons when disease detected. Templates filled with specific context (the requirement, the stage, the violation). Agent must complete practice exercise (3 attempts before prune). Deterministic templates — free, fast, ungameable. 8 of 11 templates. 485 lines, 25+ tests.

**04 Event Bus:** Every operation produces CloudEvents across 6 surfaces (MC, GitHub, IRC, ntfy, Plane, metrics). 47 event types. 8 chain builders for multi-surface publishing. 5-level routing. JSONL storage with per-agent feeds. 1248 lines, 60+ tests.

**05 Control Surface:** PO controls fleet via 3 independent axes: Work Mode (autonomous→paused), Cycle Phase (execution→crisis), Backend Mode (claude/localai/hybrid). Read from OCMC every 30s. PO directives via tagged board memory. 189 lines, 35+ tests.

**06 Agent Lifecycle:** States ACTIVE→IDLE→SLEEPING→OFFLINE for cost control. Silent heartbeat design: brain evaluates sleeping agents for $0 (mentions? tasks? directives?). PR authority per role. CRITICAL: brain interception NOT implemented — sleeping agents still cost money. 423 lines, 35+ tests.

**07 Orchestrator:** The brain. 9-step cycle every 30s: refresh contexts, security scan, doctor, approvals, wake drivers, dispatch (10 gates), directives, parent evaluation, health check. Never creates Claude sessions. Writes files for context delivery. 2595 lines, 75+ tests.

**08 MCP Tools:** 25 agent operations via FastMCP. fleet_task_complete does 12+ operations in one call (push→PR→MC→approval→IRC→ntfy→Plane→event). Stage gating blocks work tools in non-work stages. 3 missing tools block contribution flow. 2517 lines, 40+ tests.

**09 Standards:** 7 artifact type standards with required fields and quality criteria. Plan quality assessment (keyword-based, free). PR hygiene (5 issue types). Tool enforcement per task type. Compliance feeds readiness suggestions. 739 lines, 50+ tests.

**10 Transpose:** Bidirectional dict ↔ rich HTML for Plane. 7 renderers. Hidden JSON blob as source of truth. Content outside markers never touched. Completeness maps to readiness. 5 contribution renderers missing. 573 lines, 35+ tests.

**11 Storm Prevention:** 9-10 indicators with confirmation windows. 5 severity levels (CLEAR→CRITICAL). Circuit breakers per agent and backend. Diagnostic snapshots. Post-incident reports. Built after March catastrophe. 1440 lines, 90 tests — most tested system.

**12 Budget:** Tempo setting (orchestrator speed, heartbeat frequency), NOT cost envelope. Real quota monitoring via Claude OAuth (pause at 90% weekly, 95% session). Major savings NOT deployed: silent heartbeats 70%, prompt caching 90%, LocalAI routing 100% simple tasks.

**13 Labor:** Every artifact stamped: agent, model, tier (expert/standard/trainee/community), cost, duration. Tier auto-derived from backend+model. Trainee/community → mandatory challenge. Heartbeat cost tracking. NOT wired to runtime. 901 lines, 59+ tests.

**14 Router:** 4 backends (Claude paid, LocalAI free, OpenRouter free, direct no-LLM). Cheapest capable wins. Fallback chain. Security agents always Claude. Model swap management for 8GB VRAM. NOT connected to live dispatch. 1611 lines, 141 tests.

**15 Challenge Engine:** Largest system. 4 types: automated (free patterns), agent (expert review), cross-model (different LLM), scenario (reproduce bugs). Depth by tier (trainee=3 rounds mandatory). Deferred queue. Progress: 70%→80%→90%→100%. NOT in review flow yet. 2831 lines, 235 tests.

**16 Models:** Full lifecycle: select→benchmark→shadow route→promote→monitor→tier progression. Shadow routing: 80% upgrade-worthy = ready. Post-promotion auto-rollback if <70% baseline. Qwen3.5 recommended but not configured. 1767 lines, 130 tests.

**17 Plane:** Bridges PO (Plane issues/sprints) and agents (OCMC work queue). PM promotes Plane issues → PM tasks → 10-20+ ops tasks. Methodology via labels + hidden HTML spans. Bidirectional sync. Several reverse flows not implemented. 1208 lines, 40+ tests.

**18 Notifications:** 3 levels (INFO/IMPORTANT/URGENT) routed to ntfy with emoji tags. Cross-reference engine generates propagation actions across 6 surfaces. IRC channels: #fleet, #alerts, #reviews, #sprint, #gates, #contributions. Execution layer not built. 536 lines, 35+ tests.

**19 Session/Context:** Data backbone. Every 30s: full context per agent written to files → gateway injects → agent wakes knowing everything. Session telemetry adapter parses Claude JSON → distributes to labor/health/storm/cost. NOT wired to runtime. 1157 lines, 65+ tests.

**20 Infrastructure:** 8 typed clients (gateway WS, MC REST, Plane REST, IRC, ntfy, GitHub CLI, config YAML, SQLite cache). IaC scripts. Massive ecosystem gap: prompt caching, Claude-Mem, 1000+ MCP servers researched but not deployed. 1908 lines, 30+ tests.

**21 Agent Tooling:** Specification for per-role tools (MCP servers, plugins, skills, commands). Currently all agents share generic config. Maps Claude Code's 6 extension points. Nothing built — specification only.

**22 Agent Intelligence:** Cross-cutting spec: autonomy tuning (silent heartbeats 70% savings), escalation (5 dimensions), three-tier decisions (brain $0/LocalAI free/Claude paid), context endgame (organic 7%/5% flow), autocomplete chain (8-layer onion). Entirely specification — nothing built.
