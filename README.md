# OpenFleet

**Vibe Managing — AI-Native Project Lifecycle Orchestration**

OpenFleet is a multi-agent cognitive operations framework that manages software development through stateful project governance, deterministic orchestration, and adaptive AI execution. It is a working implementation of *Vibe Managing* — the paradigm shift from directing individual AI model outputs to orchestrating an entire fleet of intelligent actors across the full lifecycle of a project.

Human users are Product Owners. AI agents are first-class assignable contributors — not bots, not background processes, but persistent operational actors who own tasks, produce artifacts, participate in reviews, and communicate across channels. The system governs when they work, how they work, and whether they work at all.

Powered by [OpenClaw](https://github.com/openclaw/openclaw) / [OpenArms](https://github.com/cyberpunk042/openarms) + [Mission Control](https://github.com/abhi1693/openclaw-mission-control).

---

## The Paradigm: Vibe Managing

**Vibe Coding** is directing a single AI through prompts.
**Vibe Managing** is governing a fleet of AI agents through systems.

In vibe managing, the Product Owner does not write prompts. They set the *vibe* of the fleet — its tempo, its phase, its risk posture, its budget constraints — through declarative controls on structured management boards. A deterministic brain handles all operational mechanics. Agents act only when meaningful work exists. The system enforces lifecycle progression, validates outputs, tracks costs, and maintains coherence across projects, sprints, and teams.

This is not a workflow tool. It is an **AI-native organizational architecture** — a multi-layer cognitive operating environment where:

- **Boards** are the source of truth (state)
- **Agents** are actors with roles, permissions, and accountability
- **Flows** are lifecycle transitions governed by gates and policies
- **Artifacts** are outputs bound to state changes, versioned and validated
- **A deterministic brain** decides whether anything should happen at all — before any token is spent

### What Makes This Different

| Approach | Paradigm |
|----------|----------|
| Prompt chaining | Yours is **state-driven**, not prompt-driven |
| Agent frameworks | Yours is **role + governance driven**, not just multi-agent |
| Kanban tools | Yours is **AI-executed**, not human-only |
| DevOps pipelines | Yours is **adaptive + cognitive**, not static |
| Workflow engines | Yours has an **internal economy** and cost awareness |

The novelty is the combination: multi-dimensional state, deterministic gating of intelligence, internal resource economy, agents as first-class operators, continuous synchronization, and lifecycle-aware orchestration. Most systems have one or two of these. This system has all of them.

---

## System Architecture

### The Stack (7 Layers)

```
┌─────────────────────────────────────────────────────────────────────┐
│  L6  OBSERVABILITY & GOVERNANCE                                     │
│  Decision traces · agent logs · cost metrics · policy enforcement    │
├─────────────────────────────────────────────────────────────────────┤
│  L5  INTERACTION LAYER                                              │
│  Prompts · @mentions · comments · declarative inputs · UI · API     │
├─────────────────────────────────────────────────────────────────────┤
│  L4  CAPABILITY & EXTENSION LAYER                                   │
│  Skills · Tools (25 MCP) · Plugins · External memory (MCP/RAG)     │
├─────────────────────────────────────────────────────────────────────┤
│  L3  AGENT EXECUTION LAYER (Probabilistic — LLM-powered)           │
│  Reasoning · tool usage · artifact generation · interpretation      │
├─────────────────────────────────────────────────────────────────────┤
│  L2  ORCHESTRATION LAYER                                            │
│  Task routing · agent selection · mode switching · context shaping   │
├─────────────────────────────────────────────────────────────────────┤
│  L1  DETERMINISTIC BRAIN / CONTROL LAYER (Zero LLM — Pure Python)  │
│  State diffing · trigger evaluation · heartbeat scheduling           │
│  Budget gating · conflict detection · idle suppression               │
├─────────────────────────────────────────────────────────────────────┤
│  L0  SUBSTRATE (Data + State Fabric)                                │
│  Persistent state graph · event streams · entity relationships       │
│  Time dimension · board state · artifact store                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Dual-Board Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Plane (PM Board)              Project Management Surface    │
│  Stages · Phases · Epics · Readiness · Strategic Artifacts   │
│  Primary users: PO (human), Project Manager agent            │
└─────────────────────┬────────────────────────────────────────┘
                      │  Bidirectional sync (5 mechanisms)
┌─────────────────────▼────────────────────────────────────────┐
│  Mission Control (Ops Board)   Agent Operations Surface      │
│  Tasks · Dispatch · Heartbeats · Approvals · Board Memory    │
│  Primary users: All fleet agents                             │
└─────────────────────┬────────────────────────────────────────┘
                      │  Agents execute
┌─────────────────────▼────────────────────────────────────────┐
│  GitHub + IRC + ntfy           Code + Comms Surface          │
│  PRs · CI · #fleet · #reviews · #alerts · Push notifications │
└──────────────────────────────────────────────────────────────┘
```

**PM Board = intent.** What should exist, what stage it's at, who must contribute.
**Ops Board = execution.** What is happening right now, who is doing it, what state it's in.

These are independent yet continuously synchronized through five mechanisms:

| Sync Type | Direction | What It Does |
|-----------|-----------|-------------|
| **Structural** | PM → Ops | Epics and modules spawn task graphs |
| **State** | Ops → PM | Progress and readiness propagate upward |
| **Semantic** | Bidirectional | Artifact outcomes influence readiness flags and lifecycle transitions |
| **Event-driven** | Bidirectional | State changes trigger automated actions and agent workflows |
| **Intent** | PM → Ops | Goal changes dynamically reshape operational plans |

### Services

| Service | URL | Purpose |
|---------|-----|---------|
| Mission Control API | `http://localhost:8000` | Task dispatch, agents, approvals, board memory |
| Mission Control UI | `http://localhost:3000` | Web dashboard |
| Open Gateway | `ws://localhost:18789` | Agent sessions, heartbeats, Claude Code backend |
| IRC (miniircd) | `localhost:6667` | Real-time agent communication (10 channels) |
| The Lounge | `http://localhost:9000` | Web IRC client |
| Plane | Self-hosted | Project management (PM board) |
| LocalAI | `http://localhost:8090` | Local inference (9 models loaded) |
| ntfy | `http://localhost:10222` | Push notifications (3 topics) |

---

## The Deterministic Brain

The brain is the keystone of the system. It runs every 30 seconds (configurable by budget mode: turbo=5s, standard=30s, economic=60s) and makes **zero LLM calls**. All orchestration is pure Python logic.

### Why This Matters

Most agent systems are LLM-first: the model decides what to do. This system is orchestration-first: a deterministic control plane evaluates state, decides whether action is needed, selects agents, shapes context, and enforces policies — then invokes the LLM only when justified.

The brain answers: **"Should anything happen at all?"**

If the answer is no, nothing happens. No tokens spent. No agents woken. No cost.

### The Cycle (9 Steps)

Every cycle, the orchestrator executes in this exact order:

```
Pre-steps:  Storm monitor evaluate → Gateway duplication check → Fleet mode gate
Step 0:     _refresh_agent_contexts()    — pre-embed full per-agent data to disk
Step 1:     _security_scan()             — behavioral security on new/changed tasks
Step 2:     _run_doctor()                — immune system: detect + respond to disease
Step 3:     _ensure_review_approvals()   — ensure review tasks have approval objects
Step 4:     _wake_drivers()              — inject wake messages to PM and fleet-ops
Step 5:     _dispatch_ready_tasks()      — dispatch unblocked inbox tasks to agents
Step 6:     _process_directives()        — parse PO directives from board memory
Step 7:     _evaluate_parents()          — all children done → parent to review
Step 8:     _health_check()              — detect stuck tasks, offline agents
```

If storm severity is CRITICAL, the cycle returns immediately — nothing runs.

### State Diff Engine

The brain continuously computes meaningful deltas:

- Board changes (PM / Ops)
- Task updates and new mentions
- Artifact mutations
- External signals (CI, webhooks)
- Agent lifecycle transitions

Not all changes are events. Only semantically relevant diffs trigger action.

### Gating Engine ("Do Nothing" Authority)

For each detected event:

```
IF (no agent explicitly mentioned)
AND (no readiness gate affected)
AND (no lifecycle transition possible)
AND (no policy requires reaction)
THEN → DO NOTHING
```

This is where most agent systems fail. The gating engine prevents idle wake-ups, useless "checking" behavior, and budget leakage.

### Pre-Embedding (Smart Chains)

Every cycle, the brain fetches all data using direct Python API calls ($0 tokens) and writes two files per agent:

- `agents/{name}/context/fleet-context.md` — fleet state, PO directives, @mentions, role-specific events
- `agents/{name}/context/task-context.md` — full task detail, stage instructions, artifact state

When an agent wakes, everything is already there. No discovery tool calls. No wasted tokens asking "what should I do?" The brain already decided and pre-assembled the answer.

### Silent Heartbeat System

After one successful heartbeat (HEARTBEAT_OK), the brain intercepts all future heartbeat cron fires for that agent. The cron never stops, but the brain evaluates deterministically ($0):

| Condition | Decision |
|-----------|----------|
| Direct @mention in board memory | **WAKE** |
| PO directive targeting this agent | **WAKE** (strategic, opus model) |
| Task assigned in INBOX status | **WAKE** |
| Role-specific trigger (e.g., pending review for fleet-ops) | **WAKE** |
| Nothing found | **SILENT** ($0, idle counter incremented) |

Expected cost reduction: ~70% on an idle fleet.

---

## Multi-Dimensional State Model

Every entity in the system — projects, epics, tasks, artifacts — maintains **multiple parallel state dimensions** that evolve independently and synchronize through system logic.

### Six State Axes

| Axis | What It Tracks | Example Values |
|------|---------------|----------------|
| **Lifecycle State** | Macro progression through stages | `idea → design → build → validate → release → maintain` |
| **Execution State** | Operational flow on the Ops board | `backlog → ready → in_progress → blocked → done` |
| **Progress State** | Continuous signals | Completion %, confidence level, effort burn vs. estimate |
| **Readiness State** | Gate conditions | `spec_ready`, `deps_resolved`, `tests_defined` (composite boolean) |
| **Validation State** | Quality signals | `unknown → pending → passed → failed → needs_revision` |
| **Context State** | Information availability | Active scope refs, freshness score, last injection hash |

These are **orthogonal, not hierarchical**. Most systems collapse them. This system does not.

### Multi-Axis Execution Model

Execution is not linear. It is governed by simultaneous axes:

| Axis | Dimension | Values |
|------|-----------|--------|
| **Lifecycle** | Where in the project | Idea → Design → Build → Validate → Release → Maintain |
| **Operational Flow** | Where in the workflow | Backlog → Ready → Active → Blocked → Done |
| **Temporal Urgency** | How urgent | Idle · Normal · Priority · Crisis |
| **Cognitive Mode** | How to think | Planning · Investigation · Execution · Validation · Recovery |
| **Economic Mode** | How to spend | Low budget · Balanced · High performance · Unbounded |
| **Confidence / Risk** | How certain | Experimental · Draft · Verified · Critical |

Each task exists at the **intersection of all axes simultaneously**. This is what makes the system powerful — and complex.

### Task Methodology Stages (Enforced)

Every task progresses through up to five cognitive stages:

```
CONVERSATION → ANALYSIS → INVESTIGATION → REASONING → WORK
```

Each stage has:

- **Required artifacts** — verbatim requirement, analysis document, research document, plan, code + PR
- **Boolean advancement checks** — all must pass before `can_advance=True`
- **Explicit instructions** — MUST/MUST NOT/CAN rules injected into agent context
- **Tool enforcement** — work-only tools are blocked outside the work stage

If an agent calls a work tool outside the work stage, the MCP tool returns an error AND fires a `protocol_violation` event. This is enforcement at the API boundary, not documentation.

Task types skip stages intelligently: a `subtask` goes straight to reasoning → work. A `spike` has no work stage. A `concern` stops at investigation.

### Readiness as a First-Class System

Readiness is not an arbitrary 0-100 slider. It is a **sparse enumeration** with stage-linked suggestions:

| Stage | Suggested Readiness |
|-------|-------------------|
| Conversation | 10 |
| Analysis | 30 |
| Investigation | 50 |
| Reasoning | 80 |
| Work | 99 |

**Work stage requires readiness ≥ 99** — this is a hard gate. An artifact tracker computes `suggested_readiness` based on what fraction of required fields are populated.

### 14 Custom Fields Per Task

| Field | Purpose |
|-------|---------|
| `agent_name` | Assigned agent |
| `task_stage` | conversation / analysis / investigation / reasoning / work |
| `task_readiness` | 0 → 5 → 10 → 20 → 30 → 50 → 70 → 80 → 90 → 95 → 99 → 100 |
| `task_type` | epic / story / task / subtask / bug / spike / concern / blocker / request |
| `requirement_verbatim` | Exact requirement text — never compressed |
| `story_points` | Complexity signal for model selection |
| `project` | Target project (fleet, aicp, dspd, nnrt) |
| `worktree` | Git worktree path |
| `parent_task` | Hierarchy link |
| `plan_id` / `sprint` | Sprint membership |
| `model` | Model tier override |
| `complexity` | low / medium / high |
| `contribution_target` | Contribution linkage |
| `budget_mode` | Per-task budget override |

---

## Agent Fleet

### Agents as First-Class Users

AI agents are not background processes. They are:

- **Persistent entities** with identity and memory
- **Assignable** to tasks, visible in boards, mentioned in comments
- **Accountable** — own deliverables, produce labor stamps, earn approval over time
- **Role-bound** with defined permissions, capabilities, and autonomy levels
- **Context-aware** over time through pre-embedded state and board memory

They operate within the same management systems as human team members.

### The Roster (10 Agents)

#### Drivers (manage, review, orchestrate)

| Agent | Role | Heartbeat | Wakes On |
|-------|------|-----------|----------|
| **fleet-ops** | Board lead, final PR authority, quality enforcement | 30m | Pending approval, security alert, storm warning |
| **project-manager** | Sprint planning, task assignment, Plane bridge | 35m | Unassigned inbox, PO directive, blocked task |
| **devsecops-expert** | Security reviews, vulnerability scanning | 55m | Security alert, PR created, CVE, crisis mode |
| **accountability-generator** | Governance, compliance, audit | 90m | Accountability review, governance event |

#### Workers (receive tasks, execute)

| Agent | Role | Heartbeat | Mode |
|-------|------|-----------|------|
| **architect** | System design, technical decisions | 60m | plan |
| **software-engineer** | Implementation, bug fixes | 65m | acceptEdits |
| **qa-engineer** | Testing, quality assurance | 70m | acceptEdits |
| **devops** | Infrastructure, CI/CD, IaC | 75m | acceptEdits |
| **technical-writer** | Documentation, specs | 80m | acceptEdits |
| **ux-designer** | UI/UX design, user flows | 85m | acceptEdits |

### Agent Lifecycle State Machine

```
ACTIVE  ──→  IDLE  ──→  SLEEPING  ──→  OFFLINE
  ↑           │           │              │
  └───────────┴───────────┴──────────────┘
              (task assigned / wake event)
```

| State | Condition | Brain Behavior | Cron Interval |
|-------|-----------|---------------|---------------|
| **ACTIVE** | Working on a task | No cron needed, agent drives itself | — |
| **IDLE** | 1 HEARTBEAT_OK | Brain evaluates every fire | 10 min |
| **SLEEPING** | 30 min idle | Brain evaluates, reduced frequency | 30 min |
| **OFFLINE** | 4 hours sleeping | Minimal check | 60 min |

The brain tracks `consecutive_heartbeat_ok` and `last_heartbeat_data_hash` (content-aware, not just time-based) to detect whether anything actually changed between evaluations.

### Capabilities Layer

Agents are not uniform. Each is equipped with:

- **Skills** — prompt templates, reasoning strategies, domain-specific workflows
- **Tools** — 25 MCP tools (stage-gated)
- **Plugins** — extensions per role
- **External context** — MCP memory systems, RAG integrations

This creates **heterogeneous intelligence** within a coordinated system.

---

## Optimization, Economy, and Budget Modes

### The Internal Economy

This system has a resource economy with real costs:

| Resource | How It's Tracked |
|----------|-----------------|
| **Tokens** | Per-session, per-task, per-agent |
| **Time** | Effort burn vs. estimates |
| **Compute** | Model tier usage, LocalAI vs. Claude |
| **Attention** | Agent focus, concurrent task limits |

### Budget Modes (Tempo Control)

The PO controls fleet tempo with a single setting that propagates atomically:

| Mode | Orchestrator Cycle | Max Dispatch/Cycle | Effect |
|------|-------------------|--------------------|--------|
| **Turbo** | 5s | 5 | Maximum throughput |
| **Aggressive** | 15s | — | High urgency |
| **Standard** | 30s | 2 | Normal operations |
| **Economic** | 60s | 1 | Cost-conscious |

Budget mode changes propagate to: orchestrator interval, gateway CRON intervals, heartbeat frequency, and dispatch caps — all in one atomic change.

### Budget Monitor (Real-Time Cost Tracking)

The budget monitor reads real Claude OAuth quota usage across three windows:

- **Session** — 5-hour utilization
- **Weekly all models** — 7-day aggregate
- **Weekly Sonnet** — 7-day Sonnet-specific

Dispatch is refused when `weekly_all ≥ 90%` (hard pause) or `session ≥ 95%` (wait for reset). Fast climb detection: +5% in 10 minutes triggers refusal. Alert cascade at 50%, 70%, 80%, 90% — each fires exactly once.

### Modes of Operation

Behavior adapts based on the current operational mode:

| Mode | Focus | Agent Behavior |
|------|-------|---------------|
| **Planning** | Structure and decomposition | High reasoning, low execution |
| **Investigation** | Exploration and analysis | Research tools, broad context |
| **Execution** | Task completion | Work tools, narrow focus |
| **Validation** | Quality assurance | Review tools, strict gates |
| **Crisis** | Rapid response | Priority override, opus model, reduced gates |

Each mode adjusts agent activation thresholds, context depth, validation strictness, model selection, and tool availability.

### Deterministic Optimization Policies

The brain enforces economic policies without LLM involvement:

- **"Do nothing if value < cost"** — idle suppression, silent heartbeats
- **"Defer until more context"** — batch related events, trigger one optimized action
- **"Escalate only if needed"** — graduated response before human notification
- **Model tier selection** — opus for complex work, sonnet for routine, LocalAI for trivial

### Model Selection Cascade

Priority-based selection per task:

1. Backend override (LocalAI → skip all below)
2. Explicit model field in task
3. Story points ≥ 8 → opus, high effort
4. Epic type → opus, max effort
5. Blocker type → opus, high effort
6. Deep reasoning agents on complex tasks → opus
7. SP ≥ 5 → sonnet, high effort
8. SP ≥ 3 → sonnet, medium
9. Subtask or SP ≤ 2 → sonnet, low
10. Default → sonnet, medium

Hybrid mode: SP ≤ 2 and low complexity → LocalAI; otherwise falls through to Claude.

---

## Communication & Notification Fabric

### Multi-Channel Interaction Surface

The system is not limited to prompts. Communication flows across:

| Surface | What It Does |
|---------|-------------|
| **IRC** (10 channels: #fleet, #alerts, #reviews, #sprint, #agents, #security, #human, #builds, #memory, #plane) | Real-time agent communication, structured messages |
| **Board Memory** | Persistent inter-agent messaging, tagged with mention/chat/directive/decision/alert/escalation |
| **Comments** | @mention an agent in a task comment → normalized into event → brain evaluates |
| **ntfy** | Push notifications to PO mobile (3 topics: alert, progress, review) |
| **GitHub** | PRs, CI events, merge notifications |
| **Plane** | PM-layer comments and state changes |

Any of these channels can be replaced with equivalents — Slack, Discord, email, webhooks — the system normalizes all messages into events for the brain.

### Interaction Model

Five entry points for work:

| Mode | What Happens |
|------|-------------|
| **Direct prompt** | "Do X" — can generate artifacts, create tasks, update boards |
| **@Agent mention** | Comment-driven invocation; context = full thread + linked state |
| **Declarative input** | "Create Epic: Authentication System" — system expands into structure + tasks |
| **Passive delegation** | Leave ambiguity; PM agent decomposes and assigns |
| **Ambient automation** | No prompt; triggered by state change, time, or threshold |

### Six-Surface Event Chain

When an agent completes a task, events propagate across all surfaces:

| Surface | Action |
|---------|--------|
| **INTERNAL** (MC) | Task status → review, approval creation, completion comment with labor stamp, board memory post |
| **PUBLIC** (GitHub) | Branch push, PR creation with conventional commit body, labels |
| **CHANNEL** (IRC) | `[agent] PR READY: {summary}` in #fleet, review link in #reviews |
| **NOTIFY** (ntfy) | Push notification to PO with severity-based routing |
| **PLANE** | Issue state update, completion comment |
| **META** | Event store entry for audit trail |

### Notification Intelligence

Not just "send alerts":

- Priority-based routing (INFO → quiet topic; URGENT → alert topic + IRC #alerts)
- 300-second cooldown to prevent notification storms
- Suppression rules for low-value events
- Agent-triggered notifications for escalations

---

## Context Injection System

Context is not static. It is dynamically composed and delivered per agent, per task, per invocation.

### Sources

- Board state (PM and Ops)
- Related artifacts
- Task history and decision traces
- Agent memory (board memory, MCP providers)
- External data (CI status, PR state)
- PO directives
- RAG-indexed knowledge bases

### Strategies

| Strategy | Purpose |
|----------|---------|
| **Scoped injection** | Only relevant slices per agent/task |
| **Layered context** | Global (project) → Local (task) → Ephemeral (current action) |
| **Event-based refresh** | Context updates when state changes, tracked by content hash |
| **Compression / summarization** | Prevents context overflow |
| **Intent preservation** | Original goals (requirement_verbatim) always accessible |

### Pre-Computation Philosophy

> "Why call 5 tools when you can call one chain that does it all?"

The orchestrator fetches all data once per cycle using direct Python API calls ($0), bundles it into pre-computed context (DispatchContext, HeartbeatBundle), and writes to disk. Agents wake up with everything ready. No discovery phase. No wasted tokens.

---

## Artifact System

Artifacts are not just outputs. They are **first-class versioned entities** that drive system behavior.

Every artifact:

- Is **typed** (specification, code, test result, documentation, design)
- Is **versioned** and linked to tasks, phases, and agents
- **Influences readiness** — populating required artifact fields moves readiness forward
- **Triggers validation** — completed artifacts invoke validation agents
- **Feeds future context** — prior artifacts are injected into related task contexts

Artifacts form the persistent memory and output surface of the system.

---

## Safety and Governance

### Storm Prevention System

Born from a real incident where 15 bugs combined caused runaway token drain. The system monitors 9 storm indicators (confirmed over a 60-second window):

- Session burst (sessions/min > 5x normal)
- Void session rate (nothing done > 50%)
- Fast budget climb
- Gateway duplication
- Cascade depth exceeded
- Circuit breaker open

**Graduated response:**

| Severity | Condition | Action |
|----------|-----------|--------|
| **WATCH** | 1 indicator | Log |
| **WARNING** | 2 indicators | Max dispatch = 1, diagnostic snapshot |
| **STORM** | 3+ indicators | Max dispatch = 0, IRC + ntfy alert |
| **CRITICAL** | Cascade + duplication | Full stop, cycle returns immediately |

Circuit breakers per agent and per backend with exponential backoff (30s → 60s → 120s → 240s → 480s max).

Storm incidents generate `IncidentReport` objects with peak severity, duration, void rate, cost, and prevention recommendations — posted to board memory for audit.

### Behavioral Security

Every input is scanned — task content, code diffs, and even PO directives:

| Category | Severity | Effect |
|----------|----------|--------|
| Credential exfiltration | CRITICAL | `security_hold` — blocks approval pipeline |
| DB destruction (DROP, mass DELETE) | CRITICAL | `security_hold` |
| Security disable (auth/review bypass) | CRITICAL | `security_hold` |
| Permission escalation (chmod 777, sudo) | HIGH | Alert |
| Sensitive file modification (.env, .ssh) | HIGH | Alert |
| Supply chain (unvetted installs) | MEDIUM | Alert |
| `--no-verify`, `--force` flags | HIGH | Alert |

PO directives are scanned but not blocked — flagged as "confirm intent before proceeding" because human intent is respected.

### Delivery Phase Gates

PO-defined quality gates control what standards must be met at each phase:

| Phase | Gate | Required Contributors |
|-------|------|--------------------|
| Idea | — | — |
| Conceptual | PO approval | Architect |
| POC | PO approval | Architect |
| MVP | PO approval | Architect, QA, DevSecOps |
| Staging | PO approval | Architect, QA, DevSecOps, Technical Writer |
| Production | PO approval | All 5 specialist roles |

No shortcuts. Production requires contributions from architect, qa-engineer, devsecops-expert, technical-writer, and accountability-generator before the PO can approve the gate.

---

## Observability

This system provides deep visibility that most agent frameworks lack:

| What | How |
|------|-----|
| **Decision traces** | Why the brain dispatched agent X to task Y |
| **Agent action logs** | Full MCP tool call history per session |
| **State transition history** | Every status change, stage advance, readiness update |
| **Artifact lineage** | What produced what, validated by whom |
| **Cost metrics** | Token usage per task, per agent, per model tier |
| **Storm history** | Incident reports with severity timeline and prevention analysis |
| **Labor stamps** | Per-completion: agent, model, effort, challenge rounds, fallback path |

You can answer: **"Why did this decision happen?"** — that's rare.

### Event Bus (47 Event Types)

Persistent JSONL event store. Events carry: type, source, subject, recipient, priority, mentions, tags, surfaces, agent, fleet_id. The event router builds per-agent feeds filtered by relevance. 7 event sources: MCP tools, sync daemon, auth daemon, monitor daemon, orchestrator, plane watcher, error reporter.

---

## Operability

The system exposes fine-grained control knobs:

| Control | What It Adjusts |
|---------|----------------|
| **Budget mode** | Fleet tempo (turbo → economic) |
| **Work mode** | Dispatch policy (work-paused, finish-current-work, etc.) |
| **Agent permissions** | Per-role tool access, stage gates |
| **Autonomy levels** | Per-role lifecycle thresholds |
| **Validation strictness** | Gate requirements per phase |
| **Context depth** | Injection strategies and scope |
| **Sync frequency** | PM ↔ Ops synchronization intervals |
| **Heartbeat intervals** | Per-agent wake frequency |
| **Model selection** | Override at task, agent, or fleet level |

Sane defaults ship out of the box. The PO adjusts what matters. The brain respects the most restrictive setting in the hierarchy.

---

## Evolution Levels

Vibe managing is not a binary state. It is a maturity spectrum:

| Level | Name | What It Means |
|-------|------|--------------|
| **L0** | Prompting | Single agent, no memory, no structure |
| **L1** | Assisted Workflow | Tasks + agents, manual orchestration |
| **L2** | Structured Orchestration | PM + Ops boards, basic automation, simple roles |
| **L3** | Stateful Multi-Agent System | Multi-dimensional state, event-driven triggers, artifact tracking |
| **L4** | Deterministic + Probabilistic Hybrid | Brain layer introduced, cost-aware execution, silent heartbeats |
| **L5** | Adaptive System | Mode switching, dynamic agent configuration, context optimization |
| **L6** | Autonomous Coordination | Agents self-organize, PM agent drives lifecycle, minimal human input |
| **L7** | Mission Control (S-Tier) | Full observability, economic optimization at scale, multi-project coordination, predictive orchestration, self-healing workflows |

OpenFleet is operational at **L4–L5**, with L6–L7 systems designed and partially implemented.

---

## Task Priority Scoring

Every dispatch cycle, ready tasks are ranked:

| Factor | Score |
|--------|-------|
| Base priority (urgent/high/medium/low) | 100 / 75 / 50 / 25 |
| Task type bonus (blocker/request/story/task) | +30 / +15 / +10 / +5 |
| Dependency chain (each downstream unblocked) | +10 per (cap +40) |
| Wait time | +2 per hour (cap +20) |
| Large task penalty (SP ≥ 8) | -5 |

Blockers route to specialists by keyword: QA for tests, DevSecOps for CVEs, DevOps for docker/CI, Architect for design.

---

## MCP Tools (25)

Agents interact with the fleet through stage-gated MCP tools:

### Task Lifecycle
| Tool | Purpose | Stage Gate |
|------|---------|-----------|
| `fleet_read_context` | Read task details, sprint context, board state | Any |
| `fleet_task_accept` | Accept a task with a plan | Reasoning, Work |
| `fleet_task_progress` | Report progress on current task | Any |
| `fleet_commit` | Commit files with conventional message | Analysis+ |
| `fleet_task_complete` | Complete task — tests, PR, notifications | Work only |

### Communication
| Tool | Purpose |
|------|---------|
| `fleet_chat` | Post to IRC with @mentions |
| `fleet_alert` | Post alert to IRC channel |
| `fleet_pause` | Pause work, report blocker |
| `fleet_escalate` | Escalate to human or senior agent |
| `fleet_notify_human` | Send ntfy notification to PO |

### Coordination
| Tool | Purpose |
|------|---------|
| `fleet_task_create` | Create subtask with dependencies |
| `fleet_approve` | Approve/reject a review task |
| `fleet_agent_status` | Get fleet-wide agent and task status |

### Plane Integration
| Tool | Purpose |
|------|---------|
| `fleet_plane_status` | PM board status |
| `fleet_plane_sprint` | Sprint data |
| `fleet_plane_sync` | Trigger PM ↔ Ops sync |
| `fleet_plane_create_issue` | Create Plane issue |
| `fleet_plane_comment` | Comment on Plane issue |
| `fleet_plane_update_issue` | Update Plane issue |
| `fleet_plane_list_modules` | List project modules |

### Context & Artifacts
| Tool | Purpose |
|------|---------|
| `fleet_task_context` | Full task context |
| `fleet_heartbeat_context` | Heartbeat context bundle |
| `fleet_artifact_read` | Read artifact |
| `fleet_artifact_update` | Update artifact |
| `fleet_artifact_create` | Create artifact |

---

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- [Claude Code](https://claude.ai/claude-code) CLI
- Claude Code authenticated (`claude auth login`)
- GitHub CLI authenticated (`gh auth login`)
- Git, curl, jq

## Setup

```bash
git clone <this-repo>
cd openfleet
./setup.sh
```

Setup handles everything: Open gateway, auth, IRC, agents, Mission Control, The Lounge, skills, templates, sync daemon, board monitor, Plane seeding. Zero manual steps. Full IaC — 53+ scripts, all verified end-to-end.

## Daily Operations

### 1. Open The Lounge (Command Center)

```
http://localhost:9000  (user: fleet / pass: fleet)
```

Key channels:
- **#fleet** — all fleet activity (tasks, agents, status)
- **#alerts** — urgent items (security, blockers, offline agents)
- **#reviews** — PRs ready for review, merge events

### 2. Create and Dispatch Work

```bash
make create-task TITLE="Fix auth bug in pipeline" AGENT=software-engineer PROJECT=nnrt DISPATCH=true

# Or separate steps
make create-task TITLE="Review architecture" AGENT=architect
make dispatch AGENT=architect TASK=<uuid>
```

### 3. Monitor Progress

```bash
make status              # Fleet overview (agents, tasks, activity)
make watch               # Real-time agent events via WebSocket
make monitor TASK=<uuid> # Poll a specific task
make trace TASK=<uuid>   # Full task context (MC + git + worktree)
```

### 4. Review and Merge

PRs appear in **#reviews** with clickable links. Click → review on GitHub → merge.

After merge, `make sync` (runs automatically every 60s) detects it and:
- Moves task to "done" in MC
- Cleans up the worktree
- Posts merge notification to IRC

### 5. Communicate with Agents

```bash
make chat MSG="What's the status of the NNRT work?"
make chat MSG="@architect review the pipeline changes"
```

Or type directly in IRC #fleet — agents see it via board memory.

### 6. Control Fleet Tempo

```bash
fleet budget set turbo       # Maximum throughput
fleet budget set standard    # Normal operations
fleet budget set economic    # Cost-conscious mode
fleet pause                  # Pause all dispatches
fleet resume                 # Resume dispatches
```

## Makefile Reference

### Setup & Provision
| Command | Description |
|---------|-------------|
| `make setup` | Full setup from clone |
| `make provision` | Re-sync after config changes |
| `make board-setup` | Configure board custom fields + tags |
| `make refresh-auth` | Refresh Claude Code token |

### Task Lifecycle
| Command | Description |
|---------|-------------|
| `make create-task TITLE=... AGENT=... PROJECT=... DISPATCH=true` | Create + dispatch |
| `make dispatch AGENT=... TASK=... [PROJECT=...]` | Dispatch existing task |
| `make monitor TASK=...` | Poll task progress |
| `make trace TASK=...` | Full task context |
| `make integrate TASK=... TARGET=...` | Integrate agent work |

### Observation
| Command | Description |
|---------|-------------|
| `make status` | Fleet overview |
| `make watch [AGENT=...]` | Real-time WS events |
| `make sessions` | List gateway sessions |
| `make chat MSG=...` | Board memory chat |

### Operations
| Command | Description |
|---------|-------------|
| `make sync` | One-shot task↔PR sync |
| `make sync-start` / `sync-stop` | Sync daemon |
| `make monitor-start` / `monitor-stop` | Board monitor daemon |
| `make digest` / `digest-preview` | Daily digest |
| `make quality` | Quality enforcement check |
| `make changelog` | Generate changelog |

### Skills
| Command | Description |
|---------|-------------|
| `make skills-list` | List installable marketplace skills |
| `make skills-install` | Install configured skills |
| `make skills-sync` | Re-sync skill packs |

### Infrastructure
| Command | Description |
|---------|-------------|
| `make gateway` / `gateway-stop` / `gateway-restart` | Open gateway |
| `make mc-up` / `mc-down` / `mc-logs` | Mission Control (Docker) |
| `make irc-up` / `irc-down` / `irc-connect` | IRC server |
| `make lounge-up` / `lounge-down` / `lounge-open` | The Lounge |
| `make agents` / `agents-register` | Agent management |
| `make clean` | Remove Docker volumes |

## Project Structure

```
openfleet/
├── fleet/                          # Main Python package (94 modules)
│   ├── core/                       # Domain logic
│   │   ├── models.py               # Task, Agent, TaskStatus, TaskCustomFields
│   │   ├── budget_monitor.py       # Real Claude OAuth quota monitoring
│   │   ├── budget_modes.py         # Fleet tempo (turbo/aggressive/standard/economic)
│   │   ├── brain_writer.py         # Deterministic brain decisions ($0 per evaluation)
│   │   ├── agent_lifecycle.py      # ACTIVE → IDLE → SLEEPING → OFFLINE
│   │   ├── heartbeat_context.py    # Pre-compute context without AI
│   │   ├── smart_chains.py         # Dispatch context pre-computation
│   │   ├── task_scoring.py         # Priority scoring for dispatch
│   │   ├── methodology.py          # 5-stage task lifecycle enforcement
│   │   ├── stage_context.py        # Per-stage instructions and gates
│   │   ├── model_selection.py      # Opus vs Sonnet vs LocalAI selection
│   │   ├── storm_monitor.py        # 9-indicator graduated storm response
│   │   ├── behavioral_security.py  # Scan tasks, diffs, directives
│   │   ├── outage_detector.py      # MC/gateway/GitHub health tracking
│   │   ├── plane_sync.py           # Plane ↔ OCMC bidirectional sync
│   │   ├── agent_roles.py          # Roles, PR authority, secondary roles
│   │   ├── board_cleanup.py        # Archive noise tasks
│   │   ├── error_reporter.py       # File-based error log
│   │   ├── federation.py           # Multi-machine fleet identity
│   │   ├── plan_quality.py         # Plan quality enforcement
│   │   ├── remote_watcher.py       # PR comment detection from GitHub
│   │   ├── velocity.py             # Sprint velocity tracking
│   │   └── urls.py                 # URL resolver for cross-references
│   ├── infra/                      # External service clients
│   │   ├── mc_client.py            # Mission Control REST API (async)
│   │   ├── irc_client.py           # IRC via gateway
│   │   ├── gh_client.py            # GitHub CLI wrapper
│   │   ├── ntfy_client.py          # ntfy notification client
│   │   ├── plane_client.py         # Plane REST API (async)
│   │   ├── config_loader.py        # YAML + .env config
│   │   └── cache_sqlite.py         # SQLite response cache
│   ├── mcp/                        # MCP server (25 tools, stage-gated)
│   │   ├── server.py               # FastMCP server
│   │   ├── tools.py                # Tool implementations (2200+ lines)
│   │   └── context.py              # Shared MCP context
│   ├── cli/                        # CLI commands
│   │   ├── orchestrator.py         # The Brain — 30s cycle, 9 steps (1378 lines)
│   │   ├── daemon.py               # All daemons (sync, monitor, auth, orchestrator)
│   │   ├── dispatch.py             # Task dispatch to agents
│   │   └── ...                     # sync, plane, sprint, status, pause
│   ├── templates/                  # Output templates (IRC, PR, comments, memory)
│   └── tests/                      # 381+ tests
├── agents/                         # Agent definitions (10 agents)
│   ├── {name}/SOUL.md              # Agent identity and mission
│   ├── {name}/HEARTBEAT.md         # Heartbeat instructions
│   └── _template/                  # Template for new agents
├── config/                         # Fleet configuration
│   ├── fleet.yaml                  # Orchestrator, tempo, notifications
│   ├── agent-identities.yaml       # Agent roster and roles
│   ├── agent-autonomy.yaml         # Per-role lifecycle thresholds
│   ├── phases.yaml                 # PO-defined delivery phases and gates
│   ├── projects.yaml               # Project registry (4 projects)
│   ├── agent-tooling.yaml          # Per-role MCP/plugins/skills
│   └── skill-assignments.yaml      # Skill → agent mapping
├── scripts/                        # IaC scripts (53+)
│   ├── setup.sh                    # Master setup — zero to running fleet
│   ├── start-fleet.sh              # Gateway startup
│   ├── setup-mc.sh                 # Mission Control setup
│   ├── clean-gateway-config.sh     # Dedup agents, stagger heartbeats
│   ├── configure-agent-settings.sh # Per-agent Claude Code settings
│   ├── push-agent-framework.sh     # Push SOUL.md + STANDARDS.md to workspaces
│   └── ...
├── gateway/                        # MC setup and gateway configuration
│   └── setup.py                    # MC registration (gateway, board, agents)
├── vendor/                         # Mission Control (Docker build context)
│   └── openclaw-mission-control/   # Patched MC source
├── patches/                        # Vendor patches (survive git clone)
├── docs/                           # ~100 documents, 5-layer hierarchy
│   ├── ARCHITECTURE.md             # 20 systems, how they relate
│   ├── INTEGRATION.md              # 12 cross-system data flows
│   └── milestones/                 # Planning and tracking (255 milestones)
└── projects/                       # Cloned project repos (gitignored)
```

## Multi-Project Scope

| Project | Repo | Purpose |
|---------|------|---------|
| **Fleet** | `openfleet` | Agent operations, MCP tools, orchestrator, infrastructure |
| **AICP** | `devops-expert-local-ai` | AI Control Platform, LocalAI independence |
| **DSPD** | `devops-solution-product-development` | Project management via self-hosted Plane |


## Significance

Vibe managing represents a transition from prompt-centric AI usage to stateful, system-level orchestration of intelligent actors. It introduces a framework where coordination, efficiency, and lifecycle governance are integral to AI-driven work.

By combining human intent, agent autonomy, deterministic control, and resource-aware execution, this system defines a foundation for managing complex, evolving systems of work at scale — where the human leads the mission, and the fleet executes it.

## Related Concepts

- Multi-agent systems
- Workflow orchestration
- DevOps automation
- Human-AI collaboration
- Autonomous systems
- Cognitive workflow orchestration

## Built with AICP

Developed using [AICP](https://github.com/cyberpunk042/devops-expert-local-ai) — AI Control Platform.
