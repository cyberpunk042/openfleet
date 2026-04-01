# Fleet Integration — How Everything Connects

> **Every major operation crosses multiple systems. This document traces
> the FULL data flow for each operation — which systems it touches, what
> data passes between them, what events fire, what gets persisted.**
>
> The system docs (docs/systems/) describe each system in isolation.
> This document shows how they CHAIN together. If a developer needs
> to understand "what happens when an agent completes a task," this
> document answers with every system, every module, every event.

---

## 1. Flow Index

| # | Flow | Systems Crossed | Section |
|---|------|----------------|---------|
| 1 | Task Dispatch | Control, Budget, Storm, Router, Lifecycle, Orchestrator, Context, MCP, Events | §2 |
| 2 | Agent Heartbeat | Lifecycle, Context, Preembed, Gateway, MCP, Methodology | §3 |
| 3 | Stage Progression | Methodology, Standards, Artifacts, Transpose, Context, Events | §4 |
| 4 | Task Completion | MCP, Events (6 surfaces), Labor, Notifications, Plane, GitHub | §5 |
| 5 | Approval/Review | MCP, Standards, Skill Enforcement, Events, Notifications | §6 |
| 6 | Contribution Flow | Orchestrator, MCP, Context, Methodology, Events | §7 |
| 7 | Storm Response | Storm, Budget, Control, Orchestrator, Lifecycle, Notifications | §8 |
| 8 | Disease Detection → Correction | Immune, Teaching, Gateway, Lifecycle, Events | §9 |
| 9 | Plane Sync Cycle | Plane, Methodology, Transpose, Context, Events, Notifications | §10 |
| 10 | Agent Wake | Lifecycle, Orchestrator, Gateway, Context | §11 |
| 11 | PO Directive | Control, Orchestrator, Context, Events | §12 |
| 12 | Model Upgrade | Models, Router, Labor, Challenge | §13 |

---

## 2. Flow 1: Task Dispatch

**Trigger:** Orchestrator Step 5 — unblocked inbox task with assigned agent.

```
Orchestrator reads board state (MC API)
  │
  ├── FleetControlState check (fleet_mode.py)
  │   work-paused? → skip dispatch
  │   cycle_phase → filter active agents (get_active_agents_for_phase)
  │
  ├── EffortProfile check (effort_profiles.py)
  │   profile.allow_dispatch? → if False, skip
  │   max_dispatch_per_cycle → cap dispatches
  │
  ├── StormMonitor check (storm_monitor.py)
  │   CRITICAL → abort entire cycle
  │   STORM → max_dispatch = 0
  │   WARNING → max_dispatch = min(current, 1)
  │
  ├── BudgetMonitor check (budget_monitor.py)
  │   check_quota() → safe_to_dispatch?
  │   weekly ≥ 90% → refuse dispatch
  │   fast_climb (+5% in 10min) → refuse dispatch
  │
  ├── DoctorReport check (doctor.py)
  │   agents_to_skip → don't dispatch to flagged agents
  │   tasks_to_block → don't dispatch flagged tasks
  │
  ├── Route decision (backend_router.py)
  │   route_task(task, agent, budget_mode, localai_available, storm_monitor, health_dashboard)
  │   → assess complexity → route by budget mode
  │   → health check (W5: backend DOWN → fallback)
  │   → circuit breaker check (storm: breaker OPEN → fallback)
  │   → RoutingDecision(backend, model, effort, confidence_tier)
  │
  ├── Dispatch context (smart_chains.py)
  │   DispatchContext: task + project + worktree + model + acceptance criteria
  │   format_message() → dispatch message for agent
  │
  ├── Labor stamp: DispatchRecord created
  │   Records: task_id, agent, backend, model, effort, budget_mode
  │
  ├── Context refresh (context_writer.py)
  │   Write task-context.md with stage instructions
  │   Write fleet-context.md with latest heartbeat data
  │
  └── Events
      fleet.task.dispatched → IRC #fleet, board memory
```

**Systems crossed:** Control (3 checks) → Budget (quota) → Storm (severity) → Immune (doctor) → Router (backend selection) → Context (write files) → Labor (dispatch record) → Events (propagation).

**Data that flows:**
```
FleetControlState ──→ dispatch gate
BudgetMonitor ──────→ quota gate
StormMonitor ───────→ severity gate
DoctorReport ───────→ agent/task skip list
RoutingDecision ────→ backend + model + effort
DispatchContext ────→ agent receives task details
DispatchRecord ─────→ labor stamp provenance
```

---

## 3. Flow 2: Agent Heartbeat

**Trigger:** Gateway fires heartbeat per cron schedule (interval depends on agent lifecycle status).

```
Gateway cron fires for agent
  │
  ├── Gateway reads agent files (injection order):
  │   1. IDENTITY.md (grounding)
  │   2. SOUL.md (boundaries)
  │   3. CLAUDE.md (role rules, anti-corruption, max 4000 chars)
  │   4. TOOLS.md (chain-aware tool reference)
  │   5. AGENTS.md (colleague knowledge)
  │   6. context/fleet-context.md (heartbeat data — written by orchestrator)
  │   7. context/task-context.md (task data — if in-progress task exists)
  │   8. HEARTBEAT.md (action prompt — last, drives behavior)
  │
  ├── Gateway builds system prompt from files
  │
  ├── Gateway runs: claude --permission-mode bypassPermissions
  │   → Claude Code session with MCP server (fleet tools)
  │
  ├── Agent reads pre-embedded context (in system prompt, FREE):
  │   ├── PO directives (highest priority)
  │   ├── Messages (@mentions)
  │   ├── Assigned tasks (FULL: verbatim, stage, readiness, artifacts)
  │   ├── Role-specific data (from role_providers)
  │   ├── Fleet state (mode, phase, backend, agents online)
  │   └── Events since last heartbeat
  │
  ├── Agent follows HEARTBEAT.md protocol:
  │   ├── Has work? → follow stage protocol for current task
  │   │   ├── conversation → ask questions (NO code)
  │   │   ├── analysis → produce analysis artifact (NO solutions)
  │   │   ├── investigation → research options (NO decisions)
  │   │   ├── reasoning → produce plan referencing verbatim (NO code)
  │   │   └── work → execute plan (fleet_commit, fleet_task_complete)
  │   ├── Has messages? → respond via fleet_chat
  │   ├── Has domain events? → participate if relevant
  │   └── Nothing? → HEARTBEAT_OK
  │
  ├── Agent calls MCP tools → each fires event chains
  │   fleet_commit → git commit + event
  │   fleet_artifact_update → Plane HTML + completeness + readiness
  │   fleet_chat → board memory + @mention routing + IRC
  │   fleet_task_complete → push + PR + review + approval + 6-surface chain
  │
  ├── Heartbeat result recorded:
  │   ├── HEARTBEAT_OK → consecutive_heartbeat_ok += 1
  │   │   2 → DROWSY (reduced heartbeat frequency)
  │   │   3 → SLEEPING (brain evaluates, zero Claude calls)
  │   └── Work done → consecutive_heartbeat_ok = 0 (ACTIVE)
  │
  └── Orchestrator Step 0 (next cycle): refresh context/ files
```

**Systems crossed:** Gateway → Context (files) → Methodology (stage instructions) → MCP (tools) → Events (chains) → Lifecycle (state update) → Orchestrator (context refresh).

**Data that flows:**
```
context/fleet-context.md ──→ agent awareness (directives, messages, tasks, role data)
context/task-context.md ───→ task detail + stage instructions
HEARTBEAT.md ──────────────→ action protocol (what to do)
CLAUDE.md ─────────────────→ role rules + anti-corruption (how to behave)
MCP tool calls ────────────→ event chains across 6 surfaces
HEARTBEAT_OK count ────────→ lifecycle state (ACTIVE → DROWSY → SLEEPING)
```

---

## 4. Flow 3: Stage Progression

**Trigger:** Agent produces stage artifact, PO reviews, readiness advances.

```
Agent in analysis stage produces analysis_document artifact:
  │
  ├── fleet_artifact_create("analysis_document", "Header Analysis")
  │   → transpose.to_html() → Plane description updated with rich HTML
  │   → artifact_tracker.check_artifact_completeness()
  │      → required_pct: 20% (1/5 required fields)
  │      → suggested_readiness: 10
  │
  ├── fleet_artifact_update("scope", "DashboardShell.tsx header")
  │   → transpose.update_artifact() → HTML re-rendered
  │   → completeness: 40% (2/5)
  │   → suggested_readiness: 20
  │
  ├── fleet_artifact_update("findings", append=True, value={...})
  │   → completeness: 60% (3/5)
  │   → suggested_readiness: 50
  │
  ├── fleet_artifact_update("implications", "Controls can be injected...")
  │   → completeness: 80% (4/5)
  │   → suggested_readiness: 80
  │
  ├── fleet_artifact_update("current_state", "Header has 3 sections...")
  │   → completeness: 100% (5/5 required)
  │   → suggested_readiness: 90
  │
  ├── PO reviews analysis → confirms findings
  │
  ├── Methodology check: check_analysis_stage()
  │   has_analysis_document: True ✓
  │   po_reviewed: True ✓
  │   can_advance: True
  │
  ├── Stage transition: analysis → reasoning
  │   MethodologyTracker.record_transition()
  │   → event: fleet.methodology.stage_changed
  │   → Plane labels: stage:analysis → stage:reasoning
  │   → readiness updated
  │
  └── Agent next heartbeat: receives reasoning stage instructions
      "Produce a plan that REFERENCES the verbatim requirement"
```

**Systems crossed:** MCP (artifact tools) → Transpose (object↔HTML) → Standards (completeness check) → Artifacts (readiness suggestion) → Methodology (stage check + transition) → Events (stage change) → Plane (label update) → Context (next heartbeat gets reasoning instructions).

**Data that flows:**
```
Artifact object dict ──────→ transpose → Plane HTML
ArtifactCompleteness ──────→ suggested_readiness
StageCheckResult ──────────→ can_advance (all checks pass)
StageTransition ───────────→ event + Plane labels + readiness
Stage instructions ────────→ next heartbeat context
```

---

## 5. Flow 4: Task Completion

**Trigger:** Agent calls `fleet_task_complete(summary)` in work stage.

```
Agent calls fleet_task_complete(summary="Added FleetControlBar component")
  │
  ├── Stage gate check: _check_stage_allowed("fleet_task_complete")
  │   stage == "work" → allowed ✓
  │   (if NOT work → error returned + protocol_violation event)
  │
  ├── Labor stamp assembly: assemble_stamp()
  │   DispatchRecord + session metrics → full LaborStamp
  │   confidence_tier auto-derived from backend + model
  │   challenge_rounds_survived, challenge_types_faced
  │   budget_mode, fallback_from (if routed through fallback)
  │
  ├── Review gates: _build_review_gates(task_type, has_code)
  │   Code task → QA required
  │   Epic/story → Architect required
  │   Security → DevSecOps required
  │   Fleet-ops ALWAYS final gate
  │
  ├── Event chain: build_task_complete_chain()
  │   ├── INTERNAL: update task status → review
  │   ├── INTERNAL: create approval for fleet-ops
  │   ├── INTERNAL: post completion comment (with labor stamp table)
  │   ├── INTERNAL: post board memory (tagged: completed, project:X)
  │   ├── PUBLIC: push branch (git push)
  │   ├── PUBLIC: create PR (title, body with changelog + stamp)
  │   ├── CHANNEL: IRC #fleet "[agent] PR READY: {summary}"
  │   ├── CHANNEL: IRC #reviews "[agent] Review: {pr_url}"
  │   ├── NOTIFY: ntfy "Task completed: {summary}" (INFO)
  │   ├── PLANE: update issue state → "In Review"
  │   ├── PLANE: post comment "OCMC task completed by {agent}"
  │   └── META: update metrics
  │
  ├── Cross-references: generate_cross_refs(fleet.task.completed)
  │   → Plane comment with PR link
  │   → IRC #reviews with review request
  │   → Board memory completion record
  │
  ├── Skill enforcement: check_compliance(task_type, tools_called)
  │   Required tools called? → confidence score for approval
  │
  ├── Notification routing: classify(task_done) → INFO
  │   → ntfy progress topic (quiet)
  │
  └── Fleet-ops wakes (orchestrator Step 4):
      tasks in review → inject_content(fleet-ops session, wake message)
```

**Systems crossed:** MCP (tool) → Methodology (stage gate) → Labor (stamp) → Standards (review gates, skill enforcement) → Events (6-surface chain) → Notifications (classify + route) → Plane (state + comment) → GitHub (push + PR) → Orchestrator (wake fleet-ops).

**ALL 20 systems participate** in task completion. This is the most cross-cutting operation.

---

## 6. Flow 5: Approval/Review

**Trigger:** Fleet-ops calls `fleet_approve(approval_id, decision, comment)`.

```
Fleet-ops reviews task (pre-embedded: requirement + criteria + PR + completion summary):
  │
  ├── REAL review (NOT rubber stamp):
  │   ├── Read verbatim requirement → does work match?
  │   ├── Read acceptance criteria → each one met with evidence?
  │   ├── Read PR → clean? conventional commits? task ref?
  │   ├── Read methodology trail → stages followed? work only in work stage?
  │   ├── Read labor stamp → confidence tier → challenge results?
  │   ├── Read contributor validation → QA validated? DevSecOps reviewed?
  │   └── Decision: APPROVE (with specifics) or REJECT (with actionable feedback)
  │
  ├── fleet_approve(approval_id, "approved", "Requirements met: X, Y, Z")
  │   │
  │   ├── PR authority check: can_agent_reject("fleet-ops") → True ✓
  │   │   is_final_authority → True ✓
  │   │
  │   ├── MC: update approval → approved
  │   ├── MC: update task status → done
  │   ├── Event: fleet.task.approved
  │   ├── IRC #reviews: "[fleet-ops] ✅ Approved: Requirements met..."
  │   └── If parent task: orchestrator evaluates (all children done?)
  │
  ├── OR: fleet_approve(approval_id, "rejected", "Missing criteria #3")
  │   │
  │   ├── PR authority: can_agent_reject → True ✓
  │   ├── should_create_fix_task → True
  │   │   → auto-create fix task for original agent
  │   │   → fix task: verbatim = rejection feedback
  │   │
  │   ├── Event chain: build_rejection_chain()
  │   │   → Board memory: "REJECTED by fleet-ops: {reason}"
  │   │     tagged: mention:{original_agent}
  │   │   → IRC #reviews: "[rejected] {task}: {reason}"
  │   │   → Trail event for accountability
  │   │
  │   └── Original agent sees rejection on next heartbeat
  │       → pre-embedded: rejection reason + fix task assigned
  │       → agent re-reads requirement → corrects work
```

**Systems crossed:** MCP (approve tool) → Agent Roles (PR authority check) → Standards (review quality) → Events (approval/rejection chain) → Notifications (IRC) → Labor (stamp reviewed) → Orchestrator (parent evaluation).

---

## 7. Flow 6: Contribution Flow (NOT YET BUILT)

**Trigger:** Task enters REASONING stage, brain creates parallel contribution subtasks.

```
PM task reaches REASONING stage with readiness ~80
  │
  ├── Orchestrator detects: task needs contributions (brain logic)
  │   Check task_type against contribution matrix (fleet-elevation/15):
  │   ├── epic/story → architect design_input REQUIRED
  │   ├── epic/story → qa test_definition REQUIRED
  │   ├── epic/story → devsecops security_requirement (if applicable)
  │   ├── UI task → ux ux_spec
  │   └── all → writer documentation_outline (recommended)
  │
  ├── Brain creates parallel contribution subtasks:
  │   fleet_task_create(title="Design input for: {pm_task}",
  │     agent_name="architect", parent_task=pm_task_id,
  │     contribution_type="design_input", auto_created=True,
  │     task_stage="analysis", task_readiness=50)
  │   → PARALLEL: same for QA, DevSecOps, UX, Writer
  │
  ├── Each contributor works through THEIR OWN stages:
  │   Architect:
  │   ├── Analysis: examine codebase for the PM task's domain
  │   │   → fleet_artifact_create("analysis_document") → findings
  │   ├── Reasoning: produce design input
  │   │   → fleet_artifact_create("design_input") → approach, patterns, files
  │   └── fleet_contribute(pm_task_id, "design_input", {content})
  │       → Contribution posted on PM task
  │       → Event: fleet.contribution.received
  │       → IRC #contributions
  │       → PM task custom fields updated
  │
  ├── Brain checks: all REQUIRED contributions received?
  │   architect design_input: ✓
  │   qa test_definition: ✓
  │   devsecops security_requirement: ✓ (or N/A)
  │   → ALL received → PM task can advance to WORK stage
  │
  ├── Worker (engineer) receives in pre-embedded context:
  │   ├── Architect's design input (approach, patterns, target files)
  │   ├── QA's test criteria (test IDs, descriptions, priorities)
  │   ├── DevSecOps's security requirements (what MUST/MUST NOT do)
  │   └── UX spec (if applicable)
  │
  ├── Worker implements FOLLOWING ALL CONTRIBUTIONS:
  │   Design input → follow approach and patterns
  │   QA test criteria → satisfy EACH criterion (they're requirements)
  │   Security requirements → follow absolutely
  │
  └── Task completes → challenge engine checks against contributions
```

**Systems that WILL cross:** Orchestrator (brain creates subtasks) → MCP (fleet_contribute, fleet_task_create) → Context (contributions in pre-embed) → Methodology (contribution tasks have their own stages) → Standards (contribution artifacts have their own completeness) → Events (contribution events) → Challenge (cross-check against contributions).

**NOT BUILT:** fleet_contribute MCP tool, brain subtask creation logic, contribution pre-embedding.

---

## 8. Flow 7: Storm Response

**Trigger:** Storm indicators accumulate, severity escalates.

```
Void session rate climbing (agents heartbeating without doing work):
  │
  ├── storm_monitor.report_session(void=True) — called per session
  │   _void_sessions += 1
  │   void rate = _void_sessions / _total_sessions
  │   void > 50% → report_indicator("void_sessions", "62%")
  │
  ├── Indicator confirmation (60-second window):
  │   indicator.detected_at + CONFIRMATION_SECONDS < now → confirmed
  │   (exception: gateway_duplication → immediate confirmation)
  │
  ├── storm_monitor.evaluate() — called every orchestrator cycle
  │   Count confirmed indicators:
  │   1 confirmed → WATCH
  │   2 confirmed → WARNING
  │   3+ OR critical indicator → STORM
  │   cascade + gateway_duplication → CRITICAL
  │
  ├── Orchestrator pre-check:
  │   WARNING:
  │   ├── config["max_dispatch_per_cycle"] = min(current, 1)
  │   ├── capture_diagnostic(budget_mode) → save snapshot to disk
  │   ├── IRC #alerts: "[storm] WARNING: {status}"
  │   └── evaluate_storm_response() → force_budget_mode = "economic"
  │       STORM_BUDGET_FORCING[WARNING] = "economic" (W3 wiring)
  │
  │   STORM:
  │   ├── config["max_dispatch_per_cycle"] = 0
  │   ├── diagnostic snapshot
  │   ├── IRC #alerts + ntfy PO
  │   └── force_budget_mode = "survival"
  │
  │   CRITICAL:
  │   ├── IRC #alerts + ntfy PO URGENT
  │   ├── return state (HALT — no further steps execute)
  │   └── force_budget_mode = "blackout"
  │
  ├── Budget mode forced → affects ALL subsequent routing:
  │   economic → sonnet only, no opus
  │   survival → LocalAI only, no Claude
  │   blackout → direct only, fleet frozen
  │
  ├── Circuit breakers (per-agent, per-backend):
  │   Backend failures accumulate → breaker trips → OPEN state
  │   Router checks: backend breaker OPEN? → execute_fallback()
  │   Both primary + fallback OPEN → task queued
  │   Cooldown → HALF_OPEN → success → CLOSED (or fail → OPEN, cooldown doubles)
  │
  ├── Storm ends (indicators clear):
  │   StormEventTracker.process_cycle() detects severity dropped
  │   Generate IncidentReport:
  │     peak_severity, duration, indicators, responses, cost, void rate
  │     prevention_recommendations
  │   Post to board memory: [storm, incident, postmortem]
  │   StormAnalytics records for trend analysis
  │
  └── De-escalation (slower than escalation):
      Budget mode relaxes: blackout → survival → economic → standard
      Agent lifecycle: sleeping agents can wake again
      Circuit breakers: cooldown timers expire → HALF_OPEN → test → CLOSED
```

**Systems crossed:** Storm (detection + severity) → Budget (mode forcing, W3) → Control (dispatch limiting) → Router (circuit breakers, backend fallback) → Lifecycle (agent sleeping) → Notifications (IRC + ntfy) → Events (storm events) → Analytics (trend tracking).

---

## 9. Flow 8: Disease Detection → Correction

**Trigger:** Doctor (orchestrator Step 2) detects agent misbehavior.

```
Agent called fleet_commit during analysis stage:
  │
  ├── MCP tool: _check_stage_allowed("fleet_commit")
  │   stage = "analysis" ≠ "work" → BLOCKED
  │   → emit event: fleet.methodology.protocol_violation
  │   → return error to agent: "Methodology violation..."
  │   (agent sees error, tool call FAILS)
  │
  ├── Doctor cycle (Step 2, 30s later):
  │   detect_protocol_violation(agent, task, stage, tool_calls)
  │   → Detection(disease=PROTOCOL_VIOLATION, severity=MEDIUM,
  │               signal="Work tools called during analysis stage")
  │
  ├── decide_response(detection, agent_health):
  │   ├── In lesson already? → NONE (don't pile on)
  │   ├── 3+ corrections? → PRUNE
  │   ├── Critical severity? → PRUNE
  │   ├── High + repeat? → PRUNE
  │   ├── Stuck? → FORCE_COMPACT
  │   └── Medium, first time → TRIGGER_TEACHING ✓
  │
  ├── build_intervention(detection, TRIGGER_TEACHING, lesson_context)
  │   lesson_context = {
  │     requirement_verbatim: "Add fleet controls...",
  │     current_stage: "analysis",
  │     what_agent_did: "fleet_commit",
  │   }
  │
  ├── Orchestrator applies intervention:
  │   adapt_lesson(PROTOCOL_VIOLATION, "software-engineer", "abc123", context)
  │   → Template: "Your task is in {current_stage} stage.
  │     During {current_stage}, the protocol allows: {allowed_actions}
  │     You did: {what_agent_did}"
  │   → Exercise: "State what stage, what protocol allows,
  │     what you did wrong, what you should have done."
  │
  ├── format_lesson_for_injection(lesson)
  │   → "═══ TEACHING SYSTEM — LESSON ═══\n..."
  │
  ├── inject_content(session_key, formatted_lesson)
  │   → Gateway: chat.send → lesson appears in agent context
  │   → Agent MUST complete exercise before continuing work
  │
  ├── Agent responds (exercise):
  │   "I was in analysis stage. The protocol allows reading code and
  │   producing analysis documents. I called fleet_commit which is
  │   only allowed in work stage. I should have produced an analysis
  │   artifact instead of committing code."
  │
  ├── evaluate_response(lesson, agent_response):
  │   Indicators: references requirement ✓, acknowledges mistake ✓,
  │   has substance ✓, doesn't parrot lesson ✓ → 4/4
  │   → COMPREHENSION_VERIFIED
  │
  ├── Health profile updated:
  │   is_in_lesson = False
  │   total_lessons += 1
  │   → Agent can resume work
  │
  └── If comprehension NOT verified (3 attempts):
      → ResponseAction.PRUNE
      → gateway_client.prune_agent(session_key)
      → Agent session killed
      → health.is_pruned = True, total_prunes += 1
      → Agent regrows fresh on next heartbeat
      → Contaminated context gone
```

**Systems crossed:** MCP (stage gate enforcement) → Events (violation) → Immune/Doctor (detection) → Teaching (lesson adaptation + injection) → Gateway (inject_content) → Lifecycle (lesson state, prune state) → Events (teaching events).

---

## 10. Flow 9: Plane Sync Cycle

**Trigger:** Monitor daemon runs sync at configured interval.

```
PlaneSyncer runs:
  │
  ├── ingest_from_plane():
  │   Discover Plane issues NOT linked to OCMC tasks
  │   → For each new issue:
  │     Create OCMC PM task with plane_issue_id, plane_project_id
  │     Map priority (Plane → OCMC)
  │     Event: fleet.plane.issue_created
  │     IRC #fleet: "[plane] New issue: {title}"
  │     Board memory: "New Plane issue: {title}"
  │
  ├── push_completions_to_plane():
  │   Find done OCMC PM tasks with plane_issue_id
  │   → Update Plane issue state → "Done"
  │   → Cross-ref: Plane comment "OCMC PM task completed"
  │
  ├── sync_methodology_fields():
  │   For each linked task:
  │   ├── OCMC stage/readiness → Plane labels
  │   │   stage:reasoning → stage:work (label update)
  │   │   readiness:80 → readiness:99 (label update)
  │   ├── Plane labels → OCMC fields (if changed on Plane)
  │   └── Verbatim injection into Plane description HTML
  │       inject_verbatim_into_html() with fleet-verbatim markers
  │
  ├── config_sync.py:
  │   Plane state changes → update DSPD config YAML files
  │   → optionally git commit (IaC persistence)
  │
  └── Events: fleet.plane.sync
```

**Systems crossed:** Plane (sync) → Methodology (labels) → Transpose (verbatim HTML injection) → Events (sync events) → Notifications (IRC announcements) → Config (IaC persistence).

---

## 11. Flow 10: Agent Wake

**Trigger:** Orchestrator Step 4 or task assignment.

```
Orchestrator detects: 3 unassigned inbox tasks
  │
  ├── PM wake (120s cooldown):
  │   PM agent has session_key?
  │   last PM wake > 120s ago?
  │   │
  │   ├── Build wake message:
  │   │   "# PM WAKE — 3 UNASSIGNED TASKS\n\n"
  │   │   + format_task_full(task_1)
  │   │   + format_task_full(task_2)
  │   │   + format_task_full(task_3)
  │   │   (FULL task details, not count only)
  │   │
  │   ├── inject_content(pm.session_key, wake_message)
  │   │   → Gateway: chat.send → PM receives wake data
  │   │
  │   ├── IRC: "[orchestrator] Woke PM — 3 unassigned tasks"
  │   │
  │   └── PM heartbeats with FULL awareness:
  │       Sees 3 unassigned tasks with details
  │       → Assigns agents, sets stages, breaks down work
  │       → Each assignment triggers: MC update → event → IRC
  │
  ├── Fleet-ops wake (120s cooldown):
  │   Tasks in review status exist?
  │   │
  │   ├── inject_content(ops.session_key, wake_message)
  │   │   "# FLEET-OPS WAKE — 2 PENDING REVIEWS\n\n"
  │   │
  │   └── Fleet-ops heartbeats → processes approvals
  │
  └── Agent lifecycle:
      Sleeping agent gets task assigned:
        should_wake_for_task() → True (DROWSY/SLEEPING/OFFLINE)
        agent.wake(now) → status = IDLE, consecutive_ok = 0
        → Next heartbeat at IDLE interval (30 min, not 2h)
```

**Systems crossed:** Orchestrator (detect work) → Gateway (inject_content) → Context (wake data with full task details) → Lifecycle (wake state transition) → Notifications (IRC).

---

## 12. Flow 11: PO Directive

**Trigger:** PO posts directive to board memory.

```
PO posts to board memory:
  content: "PM: start working on AICP Stage 1"
  tags: ["directive", "to:project-manager", "from:human", "urgent"]
  │
  ├── Orchestrator Step 6: _process_directives()
  │   parse_directives(board_memory)
  │   → Directive(id, content, target="project-manager", urgent=True)
  │
  ├── Directive routed to PM's heartbeat context:
  │   Included in next context refresh (Step 0)
  │   PM's fleet-context.md:
  │     "## PO DIRECTIVES
  │      - 🚨 URGENT DIRECTIVE from human:
  │        PM: start working on AICP Stage 1"
  │
  ├── PM heartbeats → sees directive as HIGHEST PRIORITY
  │   → Executes immediately per HEARTBEAT.md protocol
  │   → Creates tasks, assigns agents, sets priorities
  │
  ├── Directive marked processed:
  │   Tag "processed" added to board memory entry
  │   → Won't be re-processed next cycle
  │
  └── Events: fleet.system.directive_processed
```

**Systems crossed:** Control (directives) → Orchestrator (parse + route) → Context (pre-embed in heartbeat) → Events (processed event).

---

## 13. Flow 12: Model Upgrade

**Trigger:** PO decides to promote a model based on shadow routing evidence.

```
Shadow routing has run for 50 tasks:
  ShadowRouter: upgrade_worthy_rate = 85% → READY verdict
  │
  ├── PO reviews shadow report → decides to promote
  │
  ├── mgr.promote_from_shadow("qwen3-8b", shadow_router)
  │   PromotionRecord created:
  │     shadow_comparisons: 50
  │     shadow_agreement_rate: 0.92
  │     pre_promotion_approval_rate: 0.85
  │
  ├── mgr.routing_model() returns "qwen3-8b" (W6 wiring)
  │   → Router uses "qwen3-8b" for localai_model parameter
  │   → All subsequent LocalAI routing uses new model
  │
  ├── Tier progression:
  │   tier_progression.set_tier("qwen3-8b", "trainee-validated")
  │   → Codex review still triggered (W7: trainee-validated in REVIEW_TIERS)
  │   → Challenge engine: mandatory for trainee-validated (3 rounds)
  │
  ├── Post-promotion monitoring:
  │   mgr.promotion_health() every cycle:
  │   post_rate vs pre_rate:
  │   ├── post ≥ 90% of pre → "healthy" (keep)
  │   ├── post ≥ 70% of pre → "degraded" (warning)
  │   └── post < 70% of pre → "unhealthy" → rollback()
  │
  ├── If rollback:
  │   mgr.rollback("health degraded")
  │   → routing_model() returns "hermes-3b" again
  │   → Router reverts to previous model
  │   → PromotionRecord.rollback = True
  │
  └── Labor stamps record which model produced each artifact
      → Analytics show per-model quality over time
      → PO can see: "qwen3-8b approval rate: 82% on tasks, 71% on stories"
```

**Systems crossed:** Models (shadow → promote) → Router (routing_model W6) → Challenge (tier-driven depth) → Codex Review (tier trigger W7) → Labor (model in stamps) → Budget (model constraints still apply).

---

## 14. Cross-System Data Dependencies

### What Each System READS From Others

```
                    Reads From
System              ────────────────────────────────────────────
Orchestrator        ALL systems (central coordinator)
MCP Tools           Methodology (stage gate), Standards (compliance),
                    Labor (stamp assembly), Events (chains), Transpose (artifacts)
Context/Session     Methodology (stage instructions), Plane (issue data),
                    Events (activity), Transpose (artifact completeness)
Doctor              Methodology (stage rules), Teaching (disease categories)
Storm               Budget (MODE_ORDER for forcing), Session Telemetry (indicators)
Budget              Storm (forced mode), Session Telemetry (real cost)
Router              Budget (model constraints), Storm (circuit breakers),
                    Health (backend status), Models (promoted model)
Challenge           Budget (depth), Labor (tier → mandatory)
Models              Budget (constraints), Router (selection), Shadow (evidence)
Plane               Methodology (stage/readiness labels), Transpose (artifact HTML)
Notifications       Events (what to route), Storm (alert severity)
```

### What Each System WRITES That Others Read

```
                    Writes For
System              ────────────────────────────────────────────
Methodology         Context (stage instructions), MCP (stage gate),
                    Plane (labels), Events (stage_changed)
Immune/Doctor       Orchestrator (skip/block lists), Teaching (disease trigger),
                    Lifecycle (prune flag)
Teaching            Gateway (inject lesson), Events (teaching events)
Events              EVERYTHING (47 event types consumed by all systems)
Control             Orchestrator (dispatch gates), Budget (mode changes)
Lifecycle           Orchestrator (heartbeat scheduling), Budget (cost model)
Context             Gateway (agent system prompt via context/ files)
Storm               Orchestrator (severity gate), Budget (mode forcing),
                    Router (circuit breakers)
Budget              Router (model constraints), Challenge (depth),
                    Storm (mode targets)
Labor               Events (completion), Templates (PR body, comments)
Router              Orchestrator (dispatch decision), Labor (routing provenance)
Standards           Artifacts (completeness), MCP (plan quality, PR hygiene)
Transpose           Plane (HTML), Context (artifact data), Standards (completeness)
Models              Router (promoted model), Labor (model in stamp)
Plane               Context (issue data), Methodology (labels)
Session Telemetry   Labor (real cost), Health (real quota), Storm (indicators),
                    Budget (real cost)
```

---

## 15. Summary: Everything Connects

No system operates in isolation. The simplest operation (agent
heartbeat) crosses 7 systems. The most complex (task completion)
crosses all 20. Understanding these flows is essential for:

1. **Debugging:** When something goes wrong, trace the flow to find
   which system's data is missing or wrong.
2. **Building:** When adding a feature, identify ALL systems it
   affects — not just the primary one.
3. **Testing:** Integration tests should follow these flows, not
   test systems in isolation.
4. **Evolving:** When changing one system, check the dependency
   map to see what breaks downstream.

The system documentation (docs/systems/) describes WHAT each system
does. This document describes HOW they work TOGETHER.
