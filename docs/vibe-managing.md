# Vibe Managing

**Vibe Managing** is an emerging paradigm in artificial intelligence-assisted work that organizes and governs fleets of intelligent agents within structured, stateful project environments. It extends beyond prompt-based interaction by combining project management systems, operational workflows, deterministic orchestration layers, adaptive AI execution, communication fabrics, knowledge infrastructure, and resource-aware economics into a unified operational domain.

In vibe managing systems, artificial agents are not treated as passive tools or "bots," but as **first-class operational actors** — comparable to human contributors — capable of owning work, making decisions within constraints, producing validated artifacts, and participating in coordinated workflows across multiple communication surfaces.

The paradigm represents a fundamental shift: from **interaction-centric AI usage** (directing a single model through prompts) to **system-centric AI orchestration** (governing a fleet of intelligent actors through state, policy, and lifecycle governance).

---

## Overview

Vibe managing introduces a multi-layer cognitive operating environment in which:

- **Human users** represent Product Owners (POs), stakeholders, and strategic decision-makers
- **AI agents** act as assignable, accountable contributors with persistent identity
- **Work** is structured across interconnected management, execution, and communication layers
- **System behavior** is governed by multi-dimensional state, policies, and orchestration logic
- **Resource consumption** is actively managed through budget modes, deterministic gating, and tiered execution models
- **Knowledge** flows through RAG systems, context injection pipelines, and persistent memory infrastructure

This environment enables continuous project lifecycle management — from ideation through execution, validation, and release — while balancing autonomy, cost, quality, and control across multiple projects, sprints, and teams simultaneously.

---

## Etymology and Distinction

The term "vibe managing" draws a deliberate contrast with "vibe coding" — a practice where a developer iteratively guides a single AI model through conversational prompts to produce code. Where vibe coding operates at the level of individual interaction, vibe managing operates at the level of organizational systems.

| Concept | Scope | Control Surface | State |
|---------|-------|----------------|-------|
| **Vibe Coding** | Single agent, single task | Prompts | Ephemeral (conversation) |
| **Vibe Managing** | Fleet of agents, full lifecycle | Boards, policies, modes, budgets | Persistent, multi-dimensional |

The "vibe" in vibe managing refers to the overall operational posture of the system — its tempo, its phase, its risk tolerance, its economic constraints — which the human operator sets at a high level while the system handles operational mechanics.

---

## Human and Agent Roles

### Human Actors

Human participants in vibe managing systems serve as:

- **Product Owners** — define intent, priorities, and constraints
- **Stakeholders** — set quality standards, approve phase transitions, define acceptance criteria
- **Supervisors** — adjust operational parameters, resolve escalations, approve critical decisions
- **Contributors** — interact through prompts, structured inputs, comments, mentions, and oversight actions

Human actors do not need to write prompts for every action. They can set direction at a strategic level and delegate operational decomposition to the system.

### AI Agents as Assignable Users

AI agents are represented as first-class assignable entities within the same management systems used by humans. They:

- **Appear in task assignments**, comments, and workflows alongside human users
- **Own deliverables** and carry accountability for their outputs
- **Operate under defined roles** with specific permissions, tool access, and autonomy levels
- **Participate in collaboration** — reviewing, commenting, escalating, delegating — similarly to human team members
- **Maintain persistent identity** across sessions, with memory, reputation, and performance history
- **Produce labor attribution** — every completed task carries a stamp recording which agent, which model, which effort level, and what validation was performed

This framing enables consistent coordination between human and artificial contributors within a single operational model, without requiring separate systems or interfaces for each.

---

## Multi-Layer System Architecture

Vibe managing systems are composed of multiple interdependent layers, each serving a distinct function. These layers form a stack from raw data substrate through intelligent execution to governance and observability.

### Layer 0 — Substrate (Data and State Fabric)

The foundational layer maintains:

- **Persistent state graph** — all entities (projects, epics, tasks, artifacts, agents) and their relationships
- **Event streams** — normalized, typed events emitted by every system action
- **Time dimension** — full history of state changes, enabling diff computation and trend analysis
- **Entity relationships** — hierarchical (project → epic → story → task → subtask), dependency (blocks/depends_on), and contribution linkages

This is the ground truth reality layer from which all other layers derive their understanding.

### Layer 1 — Deterministic Brain / Control Layer

A defining characteristic of vibe managing systems is the presence of **non-LLM deterministic control systems**, sometimes referred to as "brains" or orchestration engines.

These systems make **zero AI inference calls**. They operate entirely through programmatic logic:

- **State diff engine** — continuously computes meaningful deltas across all entities, filtering noise from signal
- **Trigger evaluation** — classifies events by urgency, impact, confidence, and cost sensitivity
- **Gating engine** — the "do nothing" authority that prevents action when no meaningful work exists
- **Heartbeat scheduling** — adaptive timing for when to evaluate each subsystem, based on activity levels rather than fixed intervals
- **Budget gating** — evaluates whether the value of an action justifies its cost before any token is spent
- **Conflict detection** — identifies contradictory state changes, overlapping agent responsibilities, or invalid transitions
- **Idle suppression** — prevents agents from "working just to work" when no mentions, state changes, deadlines, or blockers exist

The brain answers: **"Should anything happen at all?"** If the answer is no, nothing happens. No tokens spent. No agents woken. No cost incurred.

This layer is what separates vibe managing from other multi-agent approaches. Most agent systems are LLM-first — the model decides what to do. Vibe managing is orchestration-first — a deterministic control plane evaluates state, decides whether action is needed, selects actors, shapes context, and enforces policies, then invokes intelligence only when justified.

### Layer 2 — Orchestration Layer

Bridges deterministic evaluation with intelligent execution:

- **Task routing** — priority scoring, dependency resolution, blocker identification
- **Agent selection** — role matching, load balancing, expertise alignment, availability checking
- **Mode switching** — adjusting system behavior based on operational mode (planning, investigation, execution, validation, crisis, recovery)
- **Context shaping** — assembling the precise information each agent needs, no more, no less
- **Workflow enforcement** — ensuring lifecycle rules, stage gates, and contribution requirements are respected

This layer answers: **"If something should happen, who does it, how, and with what information?"**

### Layer 3 — Agent Execution Layer (Probabilistic)

The expensive layer — invoked only when the deterministic brain and orchestration layer have confirmed it is justified:

- **LLM-powered reasoning** — analysis, planning, decision-making
- **Tool usage** — interacting with external systems through defined interfaces
- **Artifact generation** — producing code, documentation, test results, designs
- **Interpretation** — understanding ambiguous inputs, resolving unclear requirements
- **Collaboration** — communicating with other agents, escalating, delegating

This layer consumes tokens, compute, and time. The entire system architecture exists to ensure this layer is invoked efficiently and only when necessary.

### Layer 4 — Capability and Extension Layer

Defines what agents can actually do:

- **Skills** — prompt templates, reasoning strategies, domain-specific workflows
- **Tools** — APIs, code execution environments, system integrations
- **Plugins** — domain-specific extensions that augment agent capabilities
- **MCP integrations** — Model Context Protocol connections to external memory systems, knowledge bases, and context providers
- **RAG infrastructure** — Retrieval-Augmented Generation systems for accessing indexed knowledge bases, documentation, and historical artifacts

This layer enables **heterogeneous intelligence** — agents are not uniform. Each carries a different combination of skills, tools, and knowledge access suited to its role.

### Layer 5 — Interaction Layer

The surfaces through which humans and systems inject intent:

- **Direct prompts** — explicit instructions that can generate artifacts, create tasks, or update boards
- **Agent mentions** (@Agent) — contextual invocation through comments or annotations, with full thread context
- **Declarative inputs** — structured commands to create epics, modules, tasks, or other entities
- **Passive delegation** — high-level intent left for PM agents to decompose and assign autonomously
- **Ambient automation** — system reacts to state changes, time-based triggers, or threshold crossings without any explicit prompt

These interaction patterns allow control ranging from precise manual direction to full autonomous operation.

### Layer 6 — Observability and Governance Layer

Provides comprehensive visibility and control:

- **Decision traces** — why the brain dispatched agent X to task Y with model Z
- **Agent activity logs** — full tool call history per session
- **State transition histories** — every status change, stage advance, readiness update
- **Artifact lineage** — what produced what, validated by whom, linked to which decisions
- **Cost metrics** — token usage per task, per agent, per model tier, per time window
- **Performance analytics** — agent efficiency, completion rates, validation outcomes
- **Policy enforcement** — ensuring all system behavior conforms to defined rules
- **Incident reports** — automated documentation of system anomalies, storms, or failures

This layer enables answering: **"Why did this decision happen, what did it cost, and was it correct?"**

### Support and Service Layers

Operating continuously and independently of agent execution:

- **State synchronization services** — maintaining consistency across PM and Ops boards
- **Event routing and trigger handling** — normalizing and distributing events to relevant consumers
- **Context indexing and retrieval** — maintaining searchable, up-to-date context stores
- **Metrics collection and logging** — continuous operational telemetry
- **Authentication and authorization** — managing agent and service credentials
- **Health monitoring** — detecting service outages, degraded performance, and connectivity issues

---

## Multi-Dimensional State Model

A fundamental design principle of vibe managing is that **state is not singular**. Every entity in the system maintains multiple parallel state dimensions that evolve independently and are synchronized through system logic.

### State Dimensions

#### Lifecycle State (Macro Progression)

Represents where an entity sits in its overall journey:

```
idea -> design -> build -> validate -> release -> maintain
```

Controlled by gates and readiness flags. Transitions require defined conditions to be met and may require explicit approval from human actors.

#### Execution State (Operational Flow)

Tracks the operational workflow status within the Ops layer:

```
backlog -> ready -> in_progress -> blocked -> done
```

Owned by the operations board and updated in real time as agents work.

#### Progress State (Continuous Signals)

Unlike discrete states, progress is a continuous dimension:

- **Completion percentage** — how much of the work is done
- **Confidence level** — how certain the system is about the output quality
- **Effort consumption** — actual effort vs. original estimate
- **Velocity indicators** — rate of progress over time

Progress evolves dynamically and is distinct from execution state — a task can be "in progress" at 10% or 90%, and the system behaves differently in each case.

#### Readiness State (Gatekeeping Logic)

Structured conditions that must be satisfied before transitions occur:

- Boolean or composite conditions (e.g., `spec_ready AND deps_resolved AND tests_defined`)
- Stage-linked suggestions (each lifecycle stage has expected readiness levels)
- Artifact-driven computation (readiness updates automatically as required fields are populated)

Readiness is not an arbitrary slider. It is a **structured enumeration** with defined meaning at each level, enforced by the system.

#### Validation State (Quality Signals)

Quality and acceptance signals produced by validation agents or human reviewers:

```
unknown -> pending -> passed -> failed -> needs_revision
```

Validation state can involve multi-agent consensus, where multiple specialist agents must independently approve before a transition is permitted.

#### Context State (Information Availability)

Tracks what information is currently available to each entity:

- **Active scope references** — what related entities are linked
- **Last injection hash** — content-aware tracking of what context was last delivered (not just when, but what)
- **Freshness score** — how current the available context is
- **Consumption record** — what information has been consumed vs. what remains unprocessed

These six dimensions are **orthogonal, not hierarchical**. Most systems collapse them into a single status field. Vibe managing systems maintain their independence, enabling fine-grained control, observability, and automation at each dimension independently.

---

## Multi-Axis Execution Model

Beyond the state dimensions of individual entities, the overall execution environment operates across simultaneous axes that define the system's operational posture:

| Axis | Dimension | Representative Values |
|------|-----------|----------------------|
| **Lifecycle** | Where in the project | Idea, Design, Build, Validate, Release, Maintain |
| **Operational Flow** | Where in the workflow | Backlog, Ready, Active, Blocked, Done |
| **Temporal Urgency** | How urgent | Idle, Normal, Priority, Crisis |
| **Cognitive Mode** | How to think | Planning, Investigation, Execution, Validation, Recovery |
| **Economic Mode** | How to spend | Minimal, Balanced, High-performance, Unbounded / Research |
| **Confidence / Risk** | How certain | Experimental, Draft, Verified, Critical |

Each task exists at the **intersection of all axes simultaneously**. An entity might be in `build` lifecycle stage, `in_progress` execution, `priority` urgency, `execution` cognitive mode, `balanced` economy, and `draft` confidence — and the system adjusts its behavior accordingly across all dimensions.

This multi-axis model is what enables the system to make nuanced decisions about resource allocation, agent selection, validation requirements, and escalation policies.

---

## Dual-Board Architecture

Vibe managing systems organize work across two primary board types that serve fundamentally different purposes while remaining continuously synchronized.

### Project Management Board (PM Board)

The strategic layer that defines **intent**:

- **Project stages and phases** — the macro-level progression model
- **Epics, modules, and long-lived components** — structural decomposition of work
- **Readiness conditions and governance rules** — what must be true before transitions
- **Strategic artifacts and deliverables** — the high-level outputs that define success
- **Contribution requirements** — which specialist roles must contribute at each phase
- **Quality gates** — PO-defined standards that escalate with maturity (e.g., POC requires basic tests; production requires comprehensive testing, security audit, full documentation)

Primary users: Product Owner (human), Project Manager agent.

### Operations Board (Ops / Kanban Board)

The execution layer that reflects **reality**:

- **Task decomposition and tracking** — the atomic units of work
- **Work-in-progress management** — what is happening right now
- **Blockers and dependencies** — what is preventing progress
- **Agent assignments** — who is doing what
- **Incremental artifact production** — the outputs being generated
- **Real-time state mutations** — continuous updates as work progresses

Primary users: All fleet agents.

### Critical Distinction

**PM Board = what should exist.** It drives intent, structure, and constraints.
**Ops Board = what is happening.** It reflects execution reality and real-time state.

These are independent systems. Neither is a view of the other. They are synchronized through explicit mechanisms, allowing each to serve its purpose without compromising the other.

---

## Synchronization Mechanisms

Consistency between system layers is maintained through multiple synchronization models, each serving a distinct purpose:

### Structural Synchronization (PM -> Ops)

High-level elements generate corresponding operational structures. When an epic is defined in the PM board, the system can decompose it into a task graph in the Ops board — either automatically through agent decomposition or through structured templates.

### State Synchronization (Ops -> PM)

Execution progress propagates upward. As tasks complete, progress percentages update, and readiness flags are set, the PM board reflects these changes in its lifecycle and readiness states.

### Semantic Synchronization (Bidirectional)

Artifact outcomes influence both layers. A completed code artifact may satisfy a readiness flag in the PM board, while a failed validation in the PM board may generate corrective tasks in the Ops board.

### Event-Driven Synchronization (Bidirectional)

State changes in either board trigger automated responses. A task completion event might trigger a validation agent, which updates a readiness flag, which enables a lifecycle transition, which spawns new tasks — all through event propagation.

### Intent Synchronization (PM -> Ops)

When project goals or constraints change at the PM level, the operational plan dynamically reshapes. This is not simple re-prioritization — it can involve restructuring task graphs, reassigning agents, or adjusting validation requirements.

These mechanisms operate continuously through dedicated synchronization services, not through periodic batch operations or manual intervention.

---

## Agent Fleet Architecture

### Role-Based Agent Types

Vibe managing systems employ a heterogeneous collection of agents organized by function:

#### Strategic Agents
- **Project Manager Agents** — interpret PM board intent, enforce lifecycle constraints, decompose work, coordinate sprints, bridge between PM and Ops layers
- **Fleet Operations Agents** — maintain system health, manage agent lifecycle, handle resource allocation, perform quality enforcement, serve as final approval authority

#### Specialist Agents
- **Architecture Agents** — system design, technical decision-making, design review
- **Implementation Agents** — code production, bug fixes, feature development
- **Quality Assurance Agents** — testing, validation, coverage analysis
- **Infrastructure Agents** — CI/CD, deployment, infrastructure as code
- **Documentation Agents** — specifications, technical writing, knowledge capture
- **Design Agents** — UI/UX design, user flow analysis, accessibility review
- **Security Agents** — vulnerability scanning, security review, compliance checking, behavioral analysis

#### Governance Agents
- **Validation Agents** — gate transitions, produce quality signals, enforce standards
- **Accountability Agents** — governance, compliance, audit trail maintenance
- **Context Management Agents** — control information flow, optimize context delivery, manage knowledge infrastructure

### Agent Identity and Persistence

Unlike stateless API calls, agents in vibe managing systems are persistent entities:

- **Identity** — each agent has a name, role definition, and mission document
- **Memory** — agents accumulate context through board memory, workspace state, and external memory systems
- **Reputation** — approval rates, completion quality, and validation outcomes build an implicit performance profile
- **Lifecycle** — agents transition through active, idle, sleeping, and offline states based on activity and system needs

### Configurable Behavior

Agents are dynamically configured based on multiple factors:

- **Current lifecycle stage** — different tools and permissions at each stage
- **Operational mode** — planning mode vs. execution mode vs. crisis mode
- **Budget constraints** — model tier, effort level, and context depth adjust with economic mode
- **Context requirements** — what information is injected depends on the task and role
- **Assigned responsibilities** — permissions and tool access vary by role

Agents may use different reasoning strategies, tools, plugins, model tiers, or even different AI backends depending on these conditions. This creates a system of **heterogeneous intelligence** — not a uniform fleet, but a diverse organization where each member brings different capabilities to the work.

### Agent Lifecycle State Machine

Agents transition through defined states based on activity:

```
ACTIVE  -->  IDLE  -->  SLEEPING  -->  OFFLINE
  ^           |           |              |
  +-----------+-----------+--------------+
              (task assigned / wake event)
```

- **Active** — currently working on a task; the agent drives itself, no external scheduling needed
- **Idle** — one successful idle cycle completed; the deterministic brain evaluates on each scheduled check
- **Sleeping** — extended idle period; reduced evaluation frequency
- **Offline** — prolonged inactivity; minimal checks

The brain tracks content-aware hashes (not just timestamps) to detect whether anything meaningful changed between evaluations. This prevents waking agents when only irrelevant state has shifted.

---

## Interaction Model

Vibe managing supports a broad interaction surface that enables control at every level of specificity:

### Direct Prompting

Users or agents issue explicit instructions. These can:
- Generate artifacts directly
- Create tasks on either PM or Ops boards
- Update board state
- Trigger agent invocations
- Modify system configuration

### Agent Mentions

Contextual invocation through comments or annotations. When a user or agent writes `@AgentName` in a comment, the system:
- Normalizes the mention into a typed event
- Attaches the full thread context and linked entity state
- Routes the event to the deterministic brain for evaluation
- The brain decides whether to wake the mentioned agent based on current state and policies

This enables conversational, contextual interaction without requiring formal task creation.

### Declarative Inputs

Structured commands that create entities within the system:
- "Create Epic: Authentication System" — the system expands this into a structured element with appropriate fields, stages, and potentially a decomposed task graph
- "Create Module: Payment Processing" — establishes a long-lived component in the PM board
- Task creation with type specification (story, bug, spike, concern, blocker, request)

### Passive Delegation

High-level intent is left for the system to interpret and decompose:
- A broad goal is stated without specific task breakdown
- PM agents analyze the intent, decompose it into actionable structures, and assign work to appropriate specialists
- The human retains override authority but does not need to micromanage decomposition

### Ambient Automation

No explicit prompt or interaction required:
- **State-driven triggers** — a task completion triggers validation, which triggers readiness update, which enables lifecycle transition
- **Time-based triggers** — scheduled evaluations, periodic health checks, deadline approaching alerts
- **Threshold triggers** — budget consumption exceeding a level, error rates crossing a threshold, agent idle time exceeding limits

---

## Context Injection and Management

Context management is a core technical challenge in vibe managing systems. Context is not static — it is dynamically composed, scoped, and delivered to each agent interaction based on relevance, state, and intent.

### Context Sources

- **Board state** — current PM and Ops board data relevant to the agent and task
- **Related artifacts** — specifications, code, test results, designs linked to the current work
- **Task history** — prior decisions, comments, state changes for the entity being worked on
- **Agent memory** — board memory entries, persistent workspace state, cross-session knowledge
- **External data** — CI/CD status, PR state, deployment health, monitoring signals
- **PO directives** — high-level instructions from human operators
- **RAG-indexed knowledge** — documentation, historical artifacts, indexed codebases
- **MCP providers** — external memory and context systems connected through Model Context Protocol

### Context Strategies

#### Scoped Injection
Only the relevant slice of system state is delivered to each agent for each interaction. A QA agent reviewing a test failure receives the test output, related code, and acceptance criteria — not the entire project history.

#### Layered Context
Context is composed in layers:
- **Global** — project-wide information, fleet status, active directives
- **Local** — task-specific details, dependencies, related artifacts
- **Ephemeral** — current action context, recent events, immediate triggers

#### Event-Based Refresh
Context updates when state changes, tracked by content-aware hashing. The system knows not just when context was last delivered, but whether its content actually changed.

#### Compression and Summarization
At scale, raw context exceeds what any single agent interaction can process. The system applies compression and summarization strategies to maintain information density without exceeding capacity limits.

#### Intent Preservation
Original goals and requirements are always accessible, even through multiple layers of decomposition and delegation. The verbatim requirement text — the exact words of the original request — is preserved and linked through the entire task hierarchy, ensuring agents never lose sight of what was actually asked for.

### Pre-Computation Philosophy

A key optimization in vibe managing systems: the deterministic brain can **pre-assemble context** using direct API calls and data lookups (zero tokens, zero AI cost) and write it to structured files before any agent is invoked. When agents wake, everything they need is already prepared. No discovery phase. No wasted tokens asking "what should I do?" The brain already decided and pre-assembled the answer.

This "smart chains" or "pre-embedding" pattern eliminates entire categories of wasted computation.

---

## Artifact-Centric Workflow

Artifacts in vibe managing systems are not incidental outputs. They are **first-class entities** that participate actively in system behavior.

### Artifact Properties

- **Typed** — specification, code, test result, documentation, design, analysis, research document, plan
- **Versioned** — changes are tracked, previous versions are accessible
- **Linked** — to tasks, phases, agents, and other artifacts through explicit relationships
- **Stateful** — artifacts carry their own validation and acceptance state

### Artifact Influence on System Behavior

- **Readiness computation** — populating required artifact fields automatically advances readiness scores
- **Validation triggering** — completed artifacts invoke validation agents for quality review
- **Context feeding** — prior artifacts are injected into the context of related future operations
- **Gate satisfaction** — lifecycle transitions may require specific artifacts to exist and pass validation
- **Knowledge accumulation** — artifacts feed into RAG indexes and context stores, building the system's evolving knowledge base

Artifacts form the **persistent memory and output surface** of the system. They are the tangible record of what the fleet has produced, how it was validated, and how it connects to the broader project structure.

---

## Optimization, Economy, and Budget Modes

A central innovation in vibe managing is the integration of **resource-aware execution models** that treat computational cost as a first-class concern, not an afterthought.

### The Internal Economy

Vibe managing systems maintain an internal economy with real resources and real costs:

| Resource | Description |
|----------|-------------|
| **Tokens** | LLM inference consumption — the primary cost driver |
| **Time** | Wall-clock time, effort burn vs. estimates, deadline proximity |
| **Compute** | Model tier usage (high-capability vs. efficient models, cloud vs. local inference) |
| **Attention** | Agent focus — concurrent task limits, context window utilization |

### Budget Modes (Tempo Control)

The system's operational tempo is controlled through budget modes — a single declarative setting that propagates atomically across the entire system:

| Mode | Characteristics |
|------|----------------|
| **Turbo** | Maximum throughput — shortest cycle times, highest dispatch rates, most aggressive scheduling |
| **Aggressive** | High urgency — fast cycles, elevated dispatch |
| **Standard** | Normal operations — balanced cycle timing, moderate dispatch |
| **Economic** | Cost-conscious — longer cycles, reduced dispatch, preference for cheaper model tiers |

When a budget mode changes, it propagates to: orchestration cycle interval, agent scheduling frequency, maximum dispatches per cycle, heartbeat evaluation frequency, and model tier preferences — all atomically.

### Budget Monitoring

Real-time tracking of actual resource consumption across multiple time windows:
- **Session window** — short-term utilization
- **Rolling daily/weekly windows** — medium-term trends
- **Per-agent and per-task accounting** — granular cost attribution

Budget monitors can **refuse dispatch** when consumption exceeds defined thresholds, **detect fast climbs** (rapid cost acceleration), and **fire graduated alerts** at increasing severity levels.

### Modes of Operation

Beyond tempo, the system adapts its behavioral posture based on operational context:

| Mode | Focus | System Behavior |
|------|-------|----------------|
| **Planning** | Structure and decomposition | High reasoning depth, low execution, emphasis on analysis artifacts |
| **Investigation** | Exploration and analysis | Research-oriented tools, broad context injection, exploratory reasoning |
| **Execution** | Task completion and delivery | Work-focused tools, narrow context, production-grade validation |
| **Validation** | Quality assurance and review | Review tools, strict gates, multi-agent consensus requirements |
| **Crisis** | Rapid response and recovery | Priority override, highest-capability models, reduced gate requirements, maximum urgency |
| **Recovery** | Post-incident stabilization | Diagnostic focus, conservative dispatch, enhanced monitoring |

Each mode adjusts: agent activation thresholds, context depth and breadth, validation strictness, model tier selection, tool availability, and escalation policies.

### Deterministic Optimization

The deterministic brain enforces economic policies without any AI inference cost:

- **"Do nothing if value < cost"** — idle suppression, silent heartbeats when no meaningful work exists
- **"Defer until more context"** — batch related events, trigger one optimized action instead of many small ones
- **"Escalate only if needed"** — graduated response chains before human notification
- **Model tier cascading** — highest-capability models for complex reasoning, efficient models for routine work, local inference for trivial operations
- **Silent heartbeat optimization** — after initial confirmation that an agent has no work, the brain intercepts future evaluation cycles and handles them deterministically at zero token cost, only waking the agent when meaningful work appears

### Model Tier Selection

Vibe managing systems can operate across multiple AI backends and model tiers:

- **High-capability models** — for complex reasoning, architectural decisions, nuanced interpretation
- **Efficient models** — for routine execution, straightforward tasks, standard workflows
- **Local inference** — for trivial operations, classification, simple routing decisions

Selection is driven by: task complexity, task type, agent role, story point estimation, explicit overrides, and current economic mode. The goal is to use the minimum capability tier that achieves adequate quality for each specific operation.

---

## Communication and Notification Fabric

Vibe managing systems operate across a **distributed interaction fabric** — not a single communication channel, but a network of interconnected surfaces that normalize all messages into system events.

### Communication Channels

Any combination of:
- **Internal messaging** (board memory, task comments) — persistent, structured, searchable
- **Real-time chat** (IRC, Slack, Discord) — immediate, conversational, multi-channel
- **Push notifications** (ntfy, push services, email) — alerting, escalation, mobile reach
- **Code platforms** (GitHub, GitLab) — PRs, CI events, merge notifications, code review
- **Project management surfaces** (Plane, Jira, Linear) — PM-layer updates, sprint tracking
- **Webhooks and APIs** — integration with arbitrary external systems

### Unified Event Normalization

Regardless of source channel, all messages are normalized into typed events:

```
MessageEvent:
  source: {internal | slack | discord | email | api | webhook}
  author: {user | agent}
  content: text
  mentions: [agent_names]
  linked_entities: [task_ids, artifact_ids]
  timestamp: datetime
```

This normalization enables the deterministic brain to process interactions from any surface using the same evaluation logic.

### Cross-Channel Behaviors

- A mention in Slack triggers an agent evaluation, which updates a task, which posts a reply back to Slack
- A GitHub PR comment triggers a security scan, which creates an alert in the internal channel, which sends a push notification to the PO
- An email from a stakeholder is normalized into a directive event, which the PM agent decomposes into operational tasks

### Notification Intelligence

Notification systems in vibe managing are not simple alert pipes:

- **Priority-based routing** — different severity levels route to different channels and recipients
- **Cooldown and deduplication** — prevents notification storms during high-activity periods
- **Suppression rules** — low-value events are filtered before notification
- **Digest aggregation** — periodic summaries instead of per-event notifications for non-urgent items
- **Agent-triggered escalation** — agents can escalate through notification channels when they encounter blockers or require human input

---

## Knowledge Infrastructure

Vibe managing systems integrate with knowledge management infrastructure to maintain and leverage organizational memory:

### RAG (Retrieval-Augmented Generation) Integration

- **Indexed knowledge bases** — documentation, historical artifacts, codebases
- **Scoped retrieval** — queries are scoped to task, epic, project, or global level depending on context needs
- **Depth control** — shallow retrieval for quick lookups, deep retrieval for complex research
- **Feed-forward** — new artifacts automatically feed into knowledge indexes for future retrieval

### External Memory Systems

- **MCP (Model Context Protocol) providers** — standardized connections to external memory and context systems
- **Persistent workspace state** — agent workspaces maintain state across sessions
- **Board memory** — structured persistent messaging tagged with semantic labels (mention, directive, decision, alert, escalation)
- **Event stores** — persistent logs of all system events, queryable for decision traces and historical context

### Knowledge Lifecycle

Knowledge in vibe managing systems is not static:
- **Generated** by agent work (artifacts, decisions, analysis)
- **Indexed** into retrieval systems
- **Delivered** through context injection pipelines
- **Validated** through quality processes
- **Evolved** as new work builds on previous knowledge
- **Retired** when superseded or invalidated

---

## Observability

Vibe managing systems provide extensive visibility into system behavior, enabling auditing, debugging, optimization, and accountability:

### Decision Traces
Complete records of why the deterministic brain made each decision: what state it observed, what events it evaluated, what gating logic it applied, which agent it selected, and what context it assembled.

### Agent Activity Logs
Full tool call history per agent session, including inputs, outputs, and timing.

### State Transition Histories
Every status change, stage advance, readiness update, and validation outcome, with timestamps and causal links.

### Artifact Lineage
What produced what, validated by whom, linked to which decisions, evolving through which versions.

### Cost Metrics
Token usage per task, per agent, per model tier, per time window. Cost attribution enables economic analysis and optimization.

### Performance Analytics
Agent efficiency metrics, completion rates, validation pass rates, time-to-completion distributions.

### Incident Reports
Automated documentation of system anomalies — peak severity, duration, impact assessment, root cause indicators, and prevention recommendations.

### Labor Attribution
Every completed work item carries a stamp recording: which agent performed the work, which model tier was used, what effort level was applied, how many validation rounds occurred, what fallback paths were taken, and what the confidence assessment was.

This level of observability enables a question that most AI systems cannot answer: **"Why did this decision happen, what did it cost, and was it correct?"**

---

## Operability

Vibe managing systems expose configurable control surfaces allowing operators to tune system behavior across multiple dimensions:

| Control Surface | What It Governs |
|----------------|----------------|
| **Budget modes** | Fleet tempo — orchestration speed, dispatch rates, heartbeat frequency |
| **Work modes** | Dispatch policy — active, paused, finish-current-only, emergency-only |
| **Agent permissions** | Per-role tool access, stage-based restrictions, approval authorities |
| **Autonomy levels** | Per-role lifecycle thresholds — how long before idle, sleeping, offline |
| **Validation policies** | Gate requirements per lifecycle phase, required contributor roles |
| **Context strategies** | Injection depth, scope rules, compression policies |
| **Synchronization rules** | PM-Ops sync frequency, event propagation policies |
| **Heartbeat intervals** | Per-agent evaluation frequency, adaptive scheduling parameters |
| **Model selection** | Override at task, agent, or fleet level; backend preferences |
| **Security policies** | Scan strictness, hold thresholds, escalation rules |

These controls allow adaptation to different operational contexts — from tightly supervised workflows with human approval at every step, to highly autonomous systems where agents self-organize and the human intervenes only by exception.

Sane defaults should ship out of the box. The operator adjusts what matters. The system respects the most restrictive setting in the hierarchy (fleet-level policy overrides agent-level preference).

---

## Safety and Governance

### Storm Prevention

Vibe managing systems must protect against runaway cost, cascading failures, and emergent pathological behaviors:

- **Multi-indicator monitoring** — tracking session rates, void rates (sessions where nothing useful was done), budget climb speed, gateway anomalies, cascade depth
- **Graduated response** — watch (log), warning (restrict dispatch), storm (halt dispatch, alert operators), critical (full system stop)
- **Circuit breakers** — per-agent and per-backend automatic disable with exponential backoff and half-open recovery testing
- **Incident documentation** — automated reports with severity timeline, impact analysis, and prevention recommendations

### Behavioral Security

All inputs — task content, code diffs, agent outputs, and even human directives — are analyzed for security concerns:

- **Credential exfiltration detection** — identifying attempts to expose secrets
- **Destructive operation detection** — database drops, mass deletions, permission escalation
- **Security bypass detection** — attempts to disable authentication, review processes, or safety checks
- **Supply chain analysis** — unvetted dependency installations, unknown external connections

Critical findings can place automatic holds that block the approval pipeline until reviewed. Human directives are scanned but never blocked — the system respects human intent while ensuring awareness.

### Delivery Phase Gates

Quality standards escalate with maturity:

- Early phases (idea, conceptual) may require only architectural review
- Middle phases (POC, MVP) require testing, security review, and documentation
- Final phases (staging, production) require contributions from all specialist roles and comprehensive standards across testing, documentation, security, and observability

No shortcuts are permitted. Gate requirements are defined by the Product Owner and enforced by the system. Production release requires all required contributors to have participated.

---

## Evolution Levels

Vibe managing is not a binary state. It is a **maturity spectrum** with defined levels that systems can progress through, potentially in different orders depending on organizational needs:

| Level | Name | Characteristics |
|-------|------|----------------|
| **L0** | Prompting | Single agent, no memory, no structure, ephemeral conversations |
| **L1** | Assisted Workflow | Tasks and agents exist, manual orchestration, basic tracking |
| **L2** | Structured Orchestration | PM + Ops boards, basic automation, defined agent roles |
| **L3** | Stateful Multi-Agent System | Multi-dimensional state, event-driven triggers, artifact tracking, synchronization |
| **L4** | Deterministic + Probabilistic Hybrid | Brain layer introduced, cost-aware execution, idle suppression, silent heartbeats |
| **L5** | Adaptive System | Mode switching, dynamic agent configuration, context optimization, budget-responsive behavior |
| **L6** | Autonomous Coordination | Agents self-organize, PM agent drives lifecycle autonomously, minimal human input required for routine operations |
| **L7** | Mission Control (S-Tier) | Full observability, economic optimization at scale, multi-project coordination, predictive orchestration, self-healing workflows, strategic decision support |

These levels are not strictly sequential. An organization might implement L4 deterministic gating before achieving full L3 artifact tracking, or reach L5 adaptive modes before completing L3 synchronization. The levels describe capability tiers, not a mandatory progression path.

---

## Applications

Vibe managing is applicable to any domain where coordinated, validated, lifecycle-aware work is performed:

- **Software development lifecycle management** — from ideation through architecture, implementation, testing, security review, documentation, and release
- **DevOps and infrastructure orchestration** — automated infrastructure management with validation gates and rollback capabilities
- **Product and project management** — strategic planning translated into operational execution with continuous progress tracking
- **Research and analysis workflows** — structured exploration with artifact generation, peer review, and knowledge accumulation
- **Autonomous and semi-autonomous operational systems** — continuous operations with graduated human oversight
- **Compliance and governance workflows** — audit-ready processes with full decision traces and accountability
- **Knowledge work coordination** — any domain requiring structured collaboration between multiple specialized actors

---

## Significance

Vibe managing represents a fundamental transition in how artificial intelligence is integrated into complex work:

- **From interaction to orchestration** — AI is not a conversation partner; it is an operational workforce
- **From ephemeral to stateful** — work persists across sessions, builds on prior outputs, and maintains institutional memory
- **From uniform to heterogeneous** — different agents bring different capabilities, and the system leverages this diversity
- **From wasteful to economical** — deterministic gating ensures intelligence is applied only where it creates value
- **From opaque to observable** — every decision, cost, and outcome is traceable
- **From fragile to resilient** — storm prevention, circuit breakers, and graduated response handle failure gracefully

By embedding intelligence within structured operational frameworks and governing it through deterministic control systems, vibe managing enables scalable, traceable, and adaptive management of complex work — where coordination, validation, and lifecycle control are as critical as raw generation capability.

---

## See Also

- Multi-agent systems
- Workflow orchestration
- DevOps automation
- Human-AI collaboration
- Autonomous systems
- Cognitive workflow orchestration
- Model Context Protocol (MCP)
- Retrieval-Augmented Generation (RAG)
- Infrastructure as Code (IaC)
- Kanban methodology
- Project lifecycle management
