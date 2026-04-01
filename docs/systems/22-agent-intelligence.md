# Agent Intelligence — Autonomy, Escalation, Research, Context Awareness

> **Cross-cutting specification. NOT a single module — touches lifecycle,
> orchestrator, context, router, budget, MCP tools, agent files.**
>
> This document covers the INTELLIGENCE layer that makes agents smart,
> adaptive, and responsive. How agents tune their own autonomy. How
> effort/model/source escalates dynamically. How agents research online
> and in code. How agents manage their own context strategically.
> These are the behaviors that make agents top-tier experts, not
> generic task executors.

### PO Requirements (Verbatim)

> "fine tune the timing for the sleep and offline and silent heartbeat
> and all the reasoning and real logical settings for a proficient
> autonomous fleet. that do not waste breath and yet is very responsive
> and prompt to work."

> "very strategical in context switching and mindful of the current
> context size relative to the next forced compact that require adapting
> preparing and potentially even triggering it ourself before rechaining
> to regather the context to continue working"

> "a logic of escalation of effort and model and source that is also
> necessary also adaptive based on the settings."

> "make sure that AI agents do series of research onlines. And then
> also research in the code. the repo docs of it and the modules /
> codes docs."

> "we need to be smart and fine tune the brain we know that a lot
> does not require agent."

---

## 1. Agent Autonomy Tuning

### 1.1 Current State (What Exists)

Agent lifecycle (docs/systems/06) defines 5 states with thresholds:
```
ACTIVE (working) → IDLE (10min) → DROWSY (2 HEARTBEAT_OK) →
SLEEPING (3 HEARTBEAT_OK) → OFFLINE (4h)
```

Heartbeat intervals: ACTIVE=0, IDLE=30min, DROWSY=60min, SLEEPING=2h.

Effort profiles (docs/systems/05) define 4 throttle levels:
full, conservative, minimal, paused.

### 1.2 What's Missing — The Tuning Layer

The thresholds are HARDCODED. A proficient fleet needs ADAPTIVE tuning:

```
CURRENT: Every agent, same thresholds
  IDLE_AFTER = 10 * 60      (10 min, hardcoded)
  SLEEPING_AFTER = 30 * 60  (30 min, hardcoded)

NEEDED: Per-agent, per-role, adaptive thresholds
  PM: faster wake (tasks queue up), slower sleep (always monitoring)
    idle_after: 5 min, drowsy_ok: 1, sleeping_ok: 2
  fleet-ops: moderate (reviews come in bursts)
    idle_after: 10 min, drowsy_ok: 2, sleeping_ok: 3
  workers: slower wake (work is dispatched), faster sleep (idle is expensive)
    idle_after: 15 min, drowsy_ok: 2, sleeping_ok: 3
  devsecops: fast wake on security events, slow sleep otherwise
    idle_after: 10 min, drowsy_ok: 3, sleeping_ok: 4
    wake_on: ["security_alert", "pr_ready_for_review"]
```

### 1.3 Configuration Spec

```yaml
# config/agent-autonomy.yaml
defaults:
  idle_after_seconds: 600
  drowsy_after_heartbeat_ok: 2
  sleeping_after_heartbeat_ok: 3
  offline_after_seconds: 14400

overrides:
  project-manager:
    idle_after_seconds: 300      # faster to notice work
    drowsy_after_heartbeat_ok: 1 # goes drowsy quickly when idle
    wake_triggers:
      - unassigned_inbox          # always wake for this
      - po_directive              # PO commands are urgent
      
  fleet-ops:
    wake_triggers:
      - pending_approval          # reviews are core job
      - security_alert            # security is urgent
      - storm_warning             # storm needs attention

  devsecops-expert:
    wake_triggers:
      - security_alert            # immediate
      - pr_created                # review every PR
    sleeping_after_heartbeat_ok: 4  # stays aware longer

  workers:  # software-engineer, devops, qa, writer, ux
    idle_after_seconds: 900       # 15 min — work is dispatched to them
    sleeping_after_heartbeat_ok: 3
```

### 1.4 Silent Heartbeat Protocol

The PO said: "do not waste breath." A sleeping agent should cost ZERO:

```
Agent is SLEEPING:
  ↓
Brain evaluates deterministically (Python, no Claude call):
  ├── Has pre-embed data hash changed since last heartbeat?
  │   YES → data changed, something might need attention → WAKE
  │   NO → nothing new
  │
  ├── New task assigned to this agent?
  │   YES → WAKE immediately
  │
  ├── @mention in board memory?
  │   YES → WAKE
  │
  ├── PO directive targeting this agent?
  │   YES → WAKE immediately
  │
  ├── Role-specific trigger? (from config)
  │   PM: unassigned_inbox → WAKE
  │   fleet-ops: pending_approval → WAKE
  │   devsecops: security_alert → WAKE
  │
  └── None of the above → SKIP (zero cost)
      Agent stays sleeping. No Claude call. $0.

Cost: 10 agents, 7 sleeping = 70% reduction on idle fleet.
```

This is fleet-elevation/23 — the data structures exist in
agent_lifecycle.py (consecutive_heartbeat_ok, last_heartbeat_data_hash)
but the brain evaluation logic is NOT in the orchestrator.

---

## 2. Escalation Logic

### 2.1 What Escalation Means

Not just "ask a human." Escalation is ADAPTIVE — the system adjusts
effort level, model tier, and backend source based on task complexity,
agent confidence, budget pressure, and outcome history.

```
ESCALATION DIMENSIONS:

  Effort:   low → medium → high → max
  Model:    hermes-3b → sonnet → opus
  Backend:  localai → openrouter → claude
  Session:  compact → continue → fresh → plan mode
  Turns:    5 → 10 → 15 → 25 → 30

These scale INDEPENDENTLY based on signals.
```

### 2.2 Escalation Triggers

```
Task complexity signals:
  SP ≥ 8                    → opus, high effort, 25 turns
  SP ≥ 5                    → sonnet, high effort, 15 turns
  SP < 5                    → sonnet, medium effort, 10 turns
  SP = 1, simple subtask    → hermes-3b (localai), low effort, 5 turns

Agent confidence signals:
  confidence_tier = expert  → can use lower effort (work is reliable)
  confidence_tier = trainee → MUST use higher effort (work needs quality)
  correction_count ≥ 2      → escalate to opus (model might be wrong)
  
Budget pressure signals:
  blitz mode               → opus allowed, max effort, 30 turns
  standard mode            → opus for complex only
  economic mode            → sonnet only, medium effort
  frugal mode              → localai only, low effort, 5 turns
  survival mode            → localai, minimal, skip if possible

Outcome signals:
  task rejected by fleet-ops → escalate effort on retry
  challenge failed           → escalate model tier on re-attempt
  3 corrections             → prune (not escalate — model is fundamentally wrong)
  
Context signals:
  context at 70%+           → compact before next heavy work
  context at 90%+           → extract artifacts to memory, prepare for compact
  agent in DROWSY           → if waking, use compact session (not fresh)
```

### 2.3 Strategic Claude Call Matrix (from fleet-elevation/23)

| Situation | Model | Effort | Session | Turns |
|-----------|-------|--------|---------|-------|
| Sleeping, nothing new | NO CALL | — | — | — |
| Sleeping, gradual wake | sonnet | medium | compact | 5 |
| Sleeping, prompt wake (task) | Per complexity | high | fresh | 15 |
| Active, heartbeat | sonnet | medium | continue | 5 |
| Active, complex work | opus | high | continue | 25 |
| Active, simple contribution | sonnet | medium | fresh | 10 |
| Bloated context | sonnet | high | compact then continue | 15 |
| Planning | opus | high | plan mode | 20 |
| Crisis | opus | max | fresh | 30 |
| Budget 80%+ | sonnet | medium | compact | 5 |
| Budget 90%+ | NO CALL | — | — | — |

### 2.4 Implementation Location

Escalation logic belongs in the orchestrator's dispatch decision:

```python
def decide_claude_call(agent_state, task, budget_mode, health):
    """Decide model, effort, session strategy, and max turns."""
    
    # Budget gate — can we call at all?
    if budget_mode in ("blackout", "survival") and not task:
        return None  # no call
    
    # Complexity → base model
    sp = task.custom_fields.story_points if task else 0
    if sp >= 8: model = "opus"
    elif sp >= 5: model = "sonnet"
    else: model = "sonnet"
    
    # Budget constrains
    model, effort, _ = constrain_model_by_budget(model, "high", "", budget_mode)
    
    # Confidence escalation
    if health.correction_count >= 2:
        model = "opus"  # model might be wrong, use best
    
    # Context strategy
    if agent_state.context_used_pct and agent_state.context_used_pct > 70:
        session = "compact"
    elif agent_state.status == AgentStatus.SLEEPING:
        session = "fresh"
    else:
        session = "continue"
    
    return ClaudeCallConfig(model=model, effort=effort, 
                           session=session, max_turns=turns)
```

---

## 3. Agent Research Capabilities

### 3.1 Online Research

Agents need to research online: frameworks, libraries, CVEs, patterns,
standards. This is NOT just browsing — it's structured investigation
as part of methodology stages.

```
INVESTIGATION stage:
  Agent reads stage instructions:
    "Research solutions, explore options, examine prior art"
  
  Agent has access to:
    ├── WebSearch (Claude built-in) → find relevant resources
    ├── WebFetch (Claude built-in) → read specific URLs
    ├── Context7 plugin → up-to-date library docs
    └── MCP servers → specialized searches (GitHub, npm, PyPI)
  
  Agent produces investigation_document artifact:
    ├── Sources cited
    ├── Multiple options with tradeoffs
    ├── Recommendations with evidence
    └── Links to reference material
```

**Per-agent research tools:**

| Agent | Research Tools | What They Research |
|-------|---------------|-------------------|
| architect | WebSearch, Context7, GitHub MCP | Frameworks, patterns, libraries, architectural approaches |
| devsecops | WebSearch, CVE databases | Vulnerabilities, security patterns, compliance standards |
| software-engineer | WebSearch, Context7, npm/PyPI | Libraries, APIs, implementation patterns |
| devops | WebSearch, Docker Hub | Infrastructure tools, deployment patterns, container images |
| qa-engineer | WebSearch | Testing frameworks, coverage tools, test patterns |
| technical-writer | WebSearch | Documentation standards, API doc generators |
| ux-designer | WebSearch | Accessibility standards (WCAG), component libraries, interaction patterns |

**Configuration:** Per-agent `allowed-tools` in SKILL.md or CLAUDE.md
determines which research tools each agent can use and WHEN (investigation
stage primarily, analysis stage for codebase research).

### 3.2 Code/Docs Research

Agents need to research IN the codebase: understand existing code,
read module documentation, find patterns, trace dependencies.

```
ANALYSIS stage:
  Agent reads stage instructions:
    "Read and examine the codebase, existing implementation"
  
  Agent has access to:
    ├── Read tool (Claude built-in) → read specific files
    ├── Grep tool (Claude built-in) → search code patterns
    ├── Glob tool (Claude built-in) → find files by pattern
    ├── Filesystem MCP → structured file operations
    └── Agent tool (Claude built-in) → spawn Explore subagent for deep search
  
  Agent produces analysis_document artifact:
    ├── Scope (what was examined, what was excluded)
    ├── Current state (specific files, line numbers)
    ├── Findings (concrete observations)
    ├── Implications (what this means for the task)
    └── Open questions
```

**The system docs we created ARE part of this:**

When an agent needs to understand the storm system, they can read
`docs/systems/11-storm.md`. When they need to understand how
events propagate, they read `docs/INTEGRATION.md` Flow 7. This is
why we wrote 9,491 lines of system documentation — so agents can
research the fleet's own code and architecture.

**The ARCHITECTURE.md and INTEGRATION.md are agent research resources.**

### 3.3 Knowledge Persistence (RAG Integration)

Research findings should persist and be reusable:

```
Agent researches "best React select component for accessibility"
  ↓
Finds: Radix Select, headless, ARIA-compliant, fleet already uses Radix
  ↓
This finding should:
  1. Appear in investigation_document artifact (immediate)
  2. Be posted to board memory tagged [architecture, decision] (team knowledge)
  3. Be ingested into RAG knowledge base (persistent, searchable)
  4. Be available to OTHER agents on future tasks
  
Future task: "Add another dropdown to the UI"
  ↓
Agent context includes RAG result:
  "Previous decision: Use Radix Select for all dropdowns (architect, 2026-04-01)"
  ↓
Agent follows existing decision instead of re-researching
```

**RAG pipeline (exists in AICP, needs fleet connection):**
```
Research finding → ingest into kb.py
  → chunk via chunking.py
  → embed via LocalAI /v1/embeddings (nomic-embed, CPU, free)
  → store in SQLite (rag.py) — persists through docker purge
  → query: cosine similarity search
  → rerank via LocalAI /v1/rerank (bge-reranker, CPU, free)
  → inject top-K chunks into agent context (pre-embed or MCP response)
```

---

## 4. Context Endgame — The Strategic Shift

### PO Requirement (Verbatim)

> "do we strategically suggest when the status line tells us that we
> have 7% context remaining? that we better get to dumping into
> artifact(s), plan(s) or execute already defined work(s)."

> "there is a fine tune notion there that if you find just the right
> time to stop in order to prevent premature compaction that completely
> destroy the context."

> "exactly like the shift we did a little while ago that you took
> very well and started to barely consume context at this point"

### 4.1 The Two Modes

An agent session operates in TWO modes:

```
EXPANSION MODE (context < 70%):
  Agent is BUILDING understanding:
  ├── Reading files, exploring code
  ├── Researching online, comparing options
  ├── Producing analysis/investigation artifacts
  ├── Having conversations with PO and colleagues
  └── Context GROWS with each action

DELIVERY MODE (context ≥ 70%):
  Agent is PRODUCING output from understood work:
  ├── Writing code from confirmed plans
  ├── Committing changes (small, focused)
  ├── Saving artifacts (fleet_artifact_update)
  ├── Posting decisions to board memory
  └── Context BARELY grows — actions are small and focused
```

The shift from expansion to delivery is NOT sudden. It's a GRADIENT
that the agent manages based on context pressure. The key insight:
**once the work is fully understood, every remaining action should
PRODUCE OUTPUT rather than CONSUME INPUT.**

### 4.2 The Context Pressure Zones

```
┌─────────────────────────────────────────────────────────┐
│  ZONE 1: EXPANSION (context 0-70%)                      │
│                                                          │
│  Normal operation. Read, research, explore freely.       │
│  Produce analysis artifacts progressively.               │
│  No restrictions on context growth.                      │
│                                                          │
│  Actions: Read files, WebSearch, fleet_read_context,     │
│           fleet_artifact_create, investigation, analysis  │
├─────────────────────────────────────────────────────────┤
│  ZONE 2: EFFICIENCY (context 70-85%)                     │
│                                                          │
│  Still working but AWARE of pressure.                    │
│  No unnecessary reads (don't re-read files already seen).│
│  Finish current artifact section, don't start new ones.  │
│  Consider: should remaining work be a SUBTASK?           │
│                                                          │
│  Actions: fleet_artifact_update (save work), commit code │
│           that's ready, post progress updates             │
├─────────────────────────────────────────────────────────┤
│  ZONE 3: DELIVERY (context 85-93%)                       │
│                                                          │
│  STOP EXPANDING. Start DELIVERING.                       │
│  Execute already-defined work. Follow confirmed plan.    │
│  Every action should produce output, not consume input.  │
│  Save ALL in-progress work to artifacts.                 │
│  Post ALL decisions to board memory.                     │
│                                                          │
│  Actions: fleet_commit (code that's written),            │
│           fleet_artifact_update (save analysis/plan),     │
│           fleet_task_progress (current state),            │
│           fleet_chat (decisions, findings to memory)      │
│                                                          │
│  DO NOT: start new file reads, start new research,       │
│          open new investigation branches                  │
├─────────────────────────────────────────────────────────┤
│  ZONE 4: EXTRACTION (context 93-97%)                     │
│                                                          │
│  EVERYTHING MUST BE SAVED before compaction.             │
│  Complete any in-progress commits.                       │
│  fleet_task_complete if work is done.                    │
│  fleet_task_progress with full state if work continues.  │
│  All learnings to memory (MEMORY.md).                    │
│                                                          │
│  Actions: ONLY output tools. No reads. No research.     │
│           Every action = producing a recoverable artifact │
├─────────────────────────────────────────────────────────┤
│  ZONE 5: COMPACT OR COMPLETE (context 97%+)              │
│                                                          │
│  If work is DONE → fleet_task_complete (triggers full    │
│  completion chain — PR, review, approval, IRC, Plane)    │
│                                                          │
│  If work is NOT done → strategic /compact:               │
│  "Preserve: task {id}, stage {stage}, verbatim,          │
│   artifact state ({N}/{M} fields), plan reference"       │
│  → After compact: pre-embed has task state               │
│  → Agent continues from where artifacts show             │
│                                                          │
│  NEVER: let compaction happen uncontrolled. Either        │
│  complete the work OR compact with instructions.         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Why This Works — The Pattern Observed

The PO observed this pattern happen naturally in a real session:

1. Early session: heavy research, file reads, design exploration
   → context grew rapidly
2. Understanding crystallized: requirements clear, plan confirmed
3. **Shift happened:** AI switched to small edits, focused commits,
   minimal reads — context barely grew
4. Artifacts produced efficiently from understood material
5. Work delivered BEFORE compaction hit

This shift was EFFECTIVE because the AI had FULLY UNDERSTOOD the work
before the context filled. The efficiency zone wasn't forced — it was
natural because all remaining actions were well-defined.

**The system should ENGINEER this shift:**
- Session telemetry provides `context_used_pct`
- HeartbeatBundle can include context pressure zone (1-5)
- CLAUDE.md can include context management protocol
- The ACTION directive in heartbeat can change based on zone:
  - Zone 1-2: "Work on your assigned tasks"
  - Zone 3: "DELIVERY MODE: produce output from understood work"
  - Zone 4: "EXTRACTION: save all work to artifacts NOW"

### 4.4 Implementation Across Systems

This isn't one module — it's a cross-cutting behavior:

| System | What It Does |
|--------|-------------|
| **Session Telemetry** | Provides `context_used_pct` and `context_pressure` |
| **HeartbeatBundle** | Includes context zone in ACTION directive |
| **CLAUDE.md** | Includes context management protocol (5 zones) |
| **Orchestrator** | Brain can adjust max_turns based on context pressure |
| **Storm Monitor** | context_pressure at 70%+ → storm indicator |
| **Methodology** | Zone 3+ → prioritize completing current stage over starting new |
| **MCP Tools** | Could warn on Read/Grep calls in Zone 4+ |
| **Memory** | Zone 4 → auto-save learnings to MEMORY.md |

### 4.5 The Right Time to Shift

The PO said: "if you find just the right time to stop in order to
prevent premature compaction." The RIGHT time is:

```
WRONG: Shift at fixed percentage (always at 85%)
  → Sometimes work isn't understood enough at 85%
  → Forces premature delivery of half-baked work

RIGHT: Shift when understanding is COMPLETE
  → Requirement understood (verbatim processed)
  → Plan confirmed (PO approved, readiness 99)
  → All contributions received (if applicable)
  → Remaining work is EXECUTION, not EXPLORATION
  → THEN shift to delivery mode regardless of context %

The zone system is a FALLBACK for when the natural shift doesn't
happen soon enough. If context hits 85% and the agent is still
exploring, the system FORCES the shift to prevent context waste.
```

### 4.6 Connection to Agent Lifecycle

Context endgame connects to the lifecycle system:

```
Agent completes work in delivery mode → fleet_task_complete
  → Context was used efficiently → task delivered
  → Compaction doesn't matter — work is done

Agent runs out of context before completing → strategic compact
  → Preserve task state in compact instructions
  → Next heartbeat: pre-embed has artifact state
  → Agent resumes from artifacts (not from scratch)
  → Consecutive HEARTBEAT_OK doesn't increment (agent has work)

Agent context is wasted (expansion too long, no delivery)
  → Doctor detects: "context at 95%, no artifacts produced"
  → This IS a disease: context_contamination
  → Teaching lesson: "Extract work to artifacts before context fills"
  → Force compact if agent doesn't respond
```

Agent is pruned (by doctor):
  → Session killed. ALL context lost.
  → Agent regrows fresh on next heartbeat
  → Pre-embedded context has: task details, artifact state, stage
  → Claude-Mem has: learned patterns from previous sessions
  → Agent resumes from where artifacts + pre-embed show
```

### 4.3 How This Connects to Session Telemetry

Session telemetry (W8) provides the data:
```
SessionSnapshot.context_used_pct → agent can read this
SessionSnapshot.context_pressure → "critical" / "high" / "moderate" / "low"
```

Currently this data feeds STORM indicators (context_pressure at 70%+).
It should ALSO be available to the agent itself — either pre-embedded
in heartbeat context or accessible via a tool.

### 4.4 Memory System Integration

Claude Code's auto-memory (`~/.claude/projects/*/memory/`) provides
cross-session persistence. Claude-Mem plugin adds semantic retrieval.
Together with fleet's pre-embed, agents have 3 layers of context recovery:

```
Layer 1: Pre-embedded context (FREE, every heartbeat)
  Task details, stage, verbatim, artifact state, messages
  Written by orchestrator. Always available.

Layer 2: Claude auto-memory (per-session, file-based)
  MEMORY.md + topic files. Loaded at session start.
  Survives compaction. Agent-written.

Layer 3: Claude-Mem plugin (semantic, cross-session)
  Captures tool usage patterns, generates summaries.
  Injected into future sessions based on relevance.
  Survives prune + regrow.

Layer 4: Fleet RAG (persistent, shared)
  Knowledge base with embedded project knowledge.
  Ingested findings available to ALL agents.
  Survives docker purge (SQLite on host filesystem).
```

---

## 5. Brain Intelligence — What Doesn't Need an Agent

The PO said: "we need to be smart and fine tune the brain we know
that a lot does not require agent."

### 5.1 What the Brain Already Does (No AI)

The orchestrator's 9 steps are ALL deterministic Python:

```
Step 0: Context refresh        ← direct API calls, file writes
Step 1: Security scan          ← regex pattern matching
Step 2: Doctor cycle           ← rule-based detection
Step 3: Review approvals       ← MC API calls
Step 4: Wake drivers           ← condition checks + inject
Step 5: Dispatch tasks         ← routing logic
Step 6: Process directives     ← tag parsing
Step 7: Evaluate parents       ← child status aggregation
Step 8: Health check           ← threshold comparison
```

NONE of these steps use an LLM. The brain is pure Python logic.

### 5.2 What Else Should Be Brain, Not Agent

```
BRAIN (no AI needed, deterministic):
  ├── Heartbeat evaluation for sleeping agents (check triggers)
  ├── Contribution subtask creation (check matrix, create tasks)
  ├── Budget auto-transitions (check quota thresholds)
  ├── Storm severity evaluation (count confirmed indicators)
  ├── Circuit breaker state management (failure counting)
  ├── Plane sync (API calls, label management)
  ├── Cross-reference generation (event → refs)
  ├── Notification routing (classify → topic)
  ├── Config sync to IaC YAML (Plane → config files)
  └── Diagnostic snapshot capture (data collection)

AGENT (AI needed, requires reasoning):
  ├── Understanding requirements (conversation stage)
  ├── Analyzing codebase (finding patterns, implications)
  ├── Investigating options (research, comparison)
  ├── Planning approach (referencing verbatim, mapping criteria)
  ├── Implementing code (writing, testing, committing)
  ├── Reviewing work (quality assessment, finding issues)
  ├── Communicating with team (contextual responses)
  └── Research (online and in-code, requires judgment)
```

### 5.3 The Three-Tier Decision Model

```
Tier 1: BRAIN (deterministic, free)
  "Is there a new task for this sleeping agent?" → yes/no
  "Has budget crossed 90%?" → auto-transition to frugal
  "Are all children of parent task done?" → move parent to review
  Cost: $0

Tier 2: LOCAL AI (LocalAI, free, fast)
  "Is this task simple enough for hermes-3b?" → structured evaluation
  "Generate heartbeat response for idle agent" → template + context
  "Parse this structured response" → JSON extraction
  Cost: $0 (local inference)

Tier 3: CLAUDE (cloud, paid, powerful)
  "Design the architecture for this feature" → deep reasoning
  "Review this PR for security issues" → expert analysis
  "Plan implementation referencing requirements" → creative planning
  Cost: $$ (but high quality)
```

The fleet should route decisions to the CHEAPEST tier that can handle
them. Most operational decisions are Tier 1 (brain). Simple evaluations
are Tier 2 (LocalAI). Only real work is Tier 3 (Claude).

---

## 6. Agent Files Review — Structure for Instinctive AI

### 6.1 What "Instinctive" Means

The agent's context should create an AUTOCOMPLETE CHAIN — each section
narrows the AI's response space so the correct action is the most
natural next token:

```
IDENTITY.md: "I am the architect. I am a top-tier expert."
  → AI generates from architect identity
  
SOUL.md: "I value design before implementation. I respect process."
  → AI behavior bounded by values
  
CLAUDE.md: "In analysis stage, I produce analysis_document artifacts.
            I do NOT produce solutions. I do NOT call fleet_commit."
  → AI knows exactly what to do and NOT do
  
TOOLS.md: "fleet_artifact_create triggers: object → Plane HTML → completeness.
           Call it with type='analysis_document' and title."
  → AI knows which tool to call and what happens
  
AGENTS.md: "Engineers depend on my design input. QA defines tests
            based on my architecture. PM consults me for complexity."
  → AI understands its role in the team
  
context/fleet-context.md: "You have 1 assigned task in analysis stage.
                           Readiness 30%. Missing: findings, implications."
  → AI knows exactly what's needed RIGHT NOW
  
HEARTBEAT.md: "Work on your assigned task. Follow stage protocol."
  → AI acts
```

By the time the AI reaches HEARTBEAT.md, there's a NARROW BAND
of correct responses. The identity, values, rules, tools, team
knowledge, current state, and action prompt all point the same
direction. The correct action is the EASIEST thing to generate.

### 6.2 What Needs to Change in Agent Files

| File | Current State | What's Needed |
|------|--------------|---------------|
| CLAUDE.md | Generic for 9/10 agents | Role-specific per fleet-elevation/05-14. Max 4000 chars. 10 anti-corruption rules. Stage protocol. Tool chains. Contribution model. |
| HEARTBEAT.md | Template for workers, custom for 3 drivers | Per-role per fleet-elevation specs. Different heartbeat priorities per role. |
| IDENTITY.md | Blank template for workers | Generated from template with fleet identity, role description, top-tier expert designation. |
| SOUL.md | Generic template | Role-specific values + shared anti-corruption. Humility clause. |
| TOOLS.md | Auto-generated list | Chain-aware per role: what tool does + what chain fires + WHEN to use in which stage. |
| AGENTS.md | Generic for workers | Per-role synergy: who contributes what to this agent, who this agent contributes to. |
| mcp.json | Template (fleet server only) | Per-role MCP servers (filesystem, github, playwright, docker). |

### 6.3 The 10 Anti-Corruption Rules (Every CLAUDE.md)

From fleet-elevation/20:
```
1. PO's words are sacrosanct. Do not deform the verbatim requirement.
2. Do not summarize when original needed. 20 things = address 20.
3. Do not replace PO's words with your own.
4. Do not add scope not in the requirement.
5. Do not compress scope. Large system = large system.
6. Do not skip reading. Read before modifying.
7. Do not produce code outside work stage.
8. Three corrections = model is wrong. Stop, re-read, start fresh.
9. Follow the autocomplete chain. Context tells you what to do.
10. When uncertain, ask — don't guess.
```

---

## 7. Connections to Other Systems

This intelligence layer touches nearly every system:

| Intelligence Area | Systems It Touches |
|------------------|-------------------|
| Autonomy tuning | Lifecycle, Orchestrator, Config |
| Escalation logic | Router, Budget, Models, Lifecycle, Orchestrator |
| Online research | MCP Tools (WebSearch, Context7), Methodology (investigation stage) |
| Code research | MCP Tools (Read, Grep, Glob, Filesystem), Methodology (analysis stage) |
| Context awareness | Session Telemetry, Lifecycle, Gateway, Teaching (force compact) |
| RAG integration | AICP RAG, LocalAI (embeddings, reranker), Context Assembly |
| Brain intelligence | Orchestrator (all 9 steps), Lifecycle, Budget, Storm |
| Agent file structure | All agent files, Gateway (injection order), Templates |

---

## 8. What Needs Building

### Code Changes

| Item | Where | Complexity |
|------|-------|-----------|
| Per-agent autonomy config | config/agent-autonomy.yaml + agent_lifecycle.py | Low |
| Brain-evaluated heartbeats | orchestrator.py + agent_lifecycle.py | Medium |
| Escalation logic | New: escalation.py + orchestrator integration | Medium |
| Strategic Claude call config | orchestrator.py dispatch decision | Medium |
| Context awareness in agents | CLAUDE.md instructions + session telemetry | Low (config) |
| RAG → fleet integration | Custom MCP server or context_assembly enhancement | Medium |
| Agent CLAUDE.md × 10 | Per fleet-elevation specs | High (careful writing) |

### Configuration

| Item | File |
|------|------|
| Per-agent autonomy thresholds | config/agent-autonomy.yaml |
| Per-agent wake triggers | config/agent-autonomy.yaml |
| Escalation matrix | config/escalation.yaml |
| RAG config | config/rag.yaml |

---

## 9. Test Coverage

This is a specification document. Testing means:
- Autonomy config loads correctly, thresholds respected
- Escalation logic produces correct model/effort per scenario
- Brain evaluation detects wake triggers without Claude call
- RAG queries return relevant results
- Agent CLAUDE.md within 4000 char limit
- Context pressure thresholds trigger correct agent behavior
