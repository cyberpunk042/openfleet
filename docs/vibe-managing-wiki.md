= Vibe Managing =
'''Vibe managing''' is an emerging paradigm in artificial intelligence-assisted work that organizes and governs a fleet of intelligent agents within a structured, stateful project environment. It extends beyond prompt-based interaction by combining project management systems, operational workflows, deterministic orchestration layers, and adaptive AI execution into a unified domain.<ref name="ref1_50a166">Guo, T., Chen, X., Wang, Y., et al. "Large Language Model based Multi-Agents: A Survey of Progress and Challenges." ''*IJCAI 2024*''. [arXiv:2402.01680](<nowiki>https://arxiv.org/abs/2402.01680</nowiki>)</ref><ref name="ref2_f87207">"From vibe coding to multi-agent AI orchestration: Redefining software development." ''*CIO.com*'', 2025. [cio.com/article/4150165](<nowiki>https://www.cio.com/article/4150165/from-vibe-coding-to-multi-agent-ai-orchestration-redefining-software-development.html</nowiki>)</ref>

In vibe managing systems, artificial agents are not treated as passive tools or "bots," but as first-class operational actors — comparable to human contributors — capable of owning work, making decisions within constraints, producing validated artifacts, and participating in coordinated workflows across multiple communication surfaces.<ref name="ref3_f675de">Wu, Q., et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." Microsoft Research, 2023. [arXiv:2308.08155](<nowiki>https://arxiv.org/abs/2308.08155</nowiki>)</ref>

The paradigm represents a fundamental shift: from '''interaction-centric AI usage''' (directing a single model through prompts) to '''system-centric AI orchestration''' (governing a fleet of intelligent actors through state, policy, and lifecycle governance). It extends the concept of ''vibe coding'', coined by Andrej Karpathy in 2025,<ref name="ref4_a198d7">Karpathy, A. [@karpathy]. "There's a new kind of coding I call 'vibe coding'..." Twitter/X, February 2, 2025. [x.com/karpathy/status/1886192184808149383](<nowiki>https://x.com/karpathy/status/1886192184808149383</nowiki>)</ref> from individual AI-assisted development to organizational-scale AI-driven operations.
----

== Etymology ==
The term "vibe managing" is derived by extension from '''vibe coding''' — a practice popularized by AI researcher Andrej Karpathy, who described it as a style of programming where "you fully give in to the vibes, embrace exponentials, and forget that the code even exists."<ref name="ref4_a198d7" /> The term rapidly entered mainstream usage and was recognized by Collins Dictionary in 2025.

Where vibe coding describes a one-to-one interaction between a human and a model to produce code, vibe managing describes the governance of an entire organizational system of AI actors to produce complex, validated outcomes across a full project lifecycle.
{| class="wikitable"
|'''Concept'''
|'''Scope'''
|'''Control Surface'''
|'''State'''
|-
|'''Vibe Coding'''
|Single agent, single task
|Prompts
|Ephemeral (conversation)
|-
|'''Vibe Managing'''
|Fleet of agents, full lifecycle
|Boards, policies, modes, budgets
|Persistent, multi-dimensional
|}
The "vibe" in vibe managing refers to the overall '''operational posture''' of the system — its tempo, its phase, its risk tolerance, its economic constraints — which the human operator sets at a high level while the system handles operational mechanics. The human manages the vibe; the system manages the work.
----

== Overview ==
Vibe managing introduces a multi-layer cognitive operating environment in which:

* '''Human users''' represent Product Owners (POs) and strategic decision-makers
* '''AI agents''' act as assignable, accountable contributors with persistent identity
* '''Work''' is structured across interconnected management and execution layers
* '''System behavior''' is governed by multi-dimensional state, policies, and orchestration logic
* '''Resource consumption''' is actively managed through budget modes, deterministic gating, and tiered execution models
* '''Knowledge''' flows through RAG systems,<ref name="ref5_3efac1">Lewis, P., Perez, E., Piktus, A., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." ''*NeurIPS 2020*''. [arXiv:2005.11401](<nowiki>https://arxiv.org/abs/2005.11401</nowiki>)</ref> context injection pipelines, and persistent memory infrastructure

This environment enables continuous project lifecycle management — from ideation through execution, validation, and release — while balancing autonomy, cost, quality, and control across multiple projects, sprints, and teams simultaneously.
----

== From Intent to Impact ==
A central organizing principle of vibe managing is the '''intent-to-impact pipeline''' — the structured path through which a human's strategic intent is transformed into validated, delivered outcomes through successive layers of system coordination.

=== The Representation Ladder ===
Vibe managing defines a hierarchy of representation through which intent is progressively refined into concrete impact:
{| class="wikitable"
|'''Level'''
|'''Representation'''
|'''Actor'''
|'''Example'''
|-
|'''Intent'''
|Strategic goal or direction
|Product Owner
|"We need authentication for the platform"
|-
|'''Structure'''
|Epics, modules, phases
|PM agent / PO
|Epic: "Authentication System" with 4 modules
|-
|'''Specification'''
|Requirements, acceptance criteria
|PM agent / Architect
|Detailed spec with security requirements
|-
|'''Decomposition'''
|Tasks, subtasks, dependencies
|PM agent
|12 tasks across 3 agents with dependency graph
|-
|'''Plan'''
|Concrete action steps per task
|Assigned agent
|Implementation plan with risk assessment
|-
|'''Execution'''
|Artifacts produced
|Specialist agents
|Code, tests, documentation
|-
|'''Validation'''
|Quality signals, approval
|Validation agents / PO
|Test results, security review, sign-off
|-
|'''Impact'''
|Delivered, deployed, operational
|System / PO
|Feature live, gates satisfied
|}
The ladder operates bidirectionally. Intent flows downward through decomposition and assignment. Impact flows upward as execution results update readiness flags, satisfy gate conditions, and advance lifecycle stages. At every level, the system provides traceability (every output links to the intent that produced it), validation (quality gates at each level), and observability (the state at every level is visible and auditable).

=== Accessibility Spectrum ===
A distinguishing property of vibe managing is that it provides multiple levels of engagement for human operators:
{| class="wikitable"
|'''Engagement Level'''
|'''What the Human Does'''
|'''System Handles'''
|-
|'''Full autonomy'''
|Sets budget mode and reviews gates
|Everything: decomposition, assignment, execution, validation
|-
|'''Strategic direction'''
|Defines epics and priorities
|Decomposition, assignment, execution, scheduling
|-
|'''Tactical oversight'''
|Creates tasks, assigns agents
|Execution, validation, reporting
|-
|'''Active collaboration'''
|Writes prompts, @mentions agents
|Tool execution, state management, synchronization
|-
|'''Direct control'''
|Manages individual agent sessions
|Agent provides capabilities
|}
This spectrum means the paradigm is accessible at every level of technical sophistication — from a Product Owner who never writes a prompt to an engineer who collaborates directly with specialist agents. The same system supports all engagement levels simultaneously, with different actors operating at different positions for different aspects of the work. Higher system maturity progressively lowers the barrier between intent and impact.
----

== Human and Agent Roles ==

=== Human Actors ===
Human participants in vibe managing systems serve as:

* '''Product Owners''' — define intent, priorities, and constraints
* '''Stakeholders''' — set quality standards, approve phase transitions, define acceptance criteria
* '''Supervisors''' — adjust operational parameters, resolve escalations, approve critical decisions
* '''Contributors''' — interact through prompts, structured inputs, comments, mentions, and oversight actions

Human actors do not need to write prompts for every action. They can set direction at a strategic level and delegate operational decomposition to the system.

=== AI Agents as Assignable Users ===
AI agents are represented as first-class assignable entities, not background processes. They:

* Appear in task assignments, comments, and workflows alongside human users
* Own deliverables and carry accountability for their outputs
* Operate under defined roles with specific permissions, tool access, and autonomy levels
* Participate in collaboration — reviewing, commenting, escalating, delegating — similarly to human team members
* Maintain persistent identity across sessions, with memory, reputation, and performance history<ref name="ref6_a7d89e">Park, J.S., O'Brien, J.C., Cai, C.J., et al. "Generative Agents: Interactive Simulacra of Human Behavior." ''*ACM UIST 2023*''. [arXiv:2304.03442](<nowiki>https://arxiv.org/abs/2304.03442</nowiki>)</ref>
* Produce labor attribution — every completed task carries a stamp recording which agent, which model, which effort level, and what validation was performed

This framing enables consistent coordination between human and artificial contributors within a single operational model, without requiring separate systems or interfaces for each.
----

== Multi-Layer System Architecture ==
Vibe managing systems are composed of multiple interdependent layers, each serving a distinct function. The architecture parallels the '''control plane / data plane separation''' established in network engineering,<ref name="ref7_b4c849">Khosravi, H., Anderson, T. (eds). "Requirements for Separation of IP Control and Forwarding." ''*RFC 3654*'', IETF, November 2003. [rfc-editor.org/rfc/rfc3654](<nowiki>https://www.rfc-editor.org/rfc/rfc3654.html</nowiki>). See also: ["What is the control plane?"](<nowiki>https://www.cloudflare.com/learning/network-layer/what-is-the-control-plane/</nowiki>) Cloudflare.</ref> where routing and policy decisions are separated from execution to improve efficiency and predictability.

=== Layer 0 — Substrate (Data and State Fabric) ===
The foundational layer maintains the persistent state graph (all entities and their relationships), event streams (normalized, typed events emitted by every system action), time dimension (full history enabling diff computation), and entity relationships (hierarchical, dependency, and contribution linkages).

=== Layer 1 — Deterministic Brain / Control Layer ===
A defining characteristic of vibe managing systems is the presence of '''non-LLM deterministic control systems''', sometimes referred to as "brains" or orchestration engines.

These systems make zero AI inference calls. They operate entirely through programmatic logic:

* '''State diff engine''' — continuously computes meaningful deltas, filtering noise from signal into normalized events
* '''Event classification''' — rates each event by urgency, impact, confidence, and cost sensitivity
* '''Gating engine''' — the "do nothing" authority that prevents action when no meaningful work exists
* '''Invocation decision tree''' — when action is warranted, determines whether to invoke an agent at all, which agent, in which mode, at which budget tier
* '''Context pre-assembler''' — selects relevant state slices and assembles agent context at zero token cost
* '''Deterministic action set''' — executes state propagation, progress updates, readiness flag toggles, and dependency resolution without AI involvement
* '''Budget enforcement''' — tracks cost-vs-value signals and refuses dispatch when thresholds are exceeded
* '''Conflict detection''' — identifies contradictory state changes, overlapping responsibilities, or invalid transitions

The brain answers: '''"Should anything happen at all?"''' If the answer is no, nothing happens — no tokens spent, no agents woken, no cost incurred.

This layer is what separates vibe managing from other multi-agent approaches.<ref name="ref8_78709a">Wang, L., Ma, C., Feng, X., et al. "A Survey on Large Language Model based Autonomous Agents." ''*Frontiers of Computer Science*'', 2023. [arXiv:2308.11432](<nowiki>https://arxiv.org/abs/2308.11432</nowiki>)</ref> Most agent systems are LLM-first — the model decides what to do. Vibe managing is orchestration-first — a deterministic control plane evaluates state, decides whether action is needed, selects actors, shapes context, and enforces policies, then invokes intelligence only when justified.

=== Layer 2 — Orchestration Layer ===
Bridges deterministic evaluation with intelligent execution:

* '''Task routing''' — priority scoring, dependency resolution, blocker identification
* '''Agent selection''' — role matching, load balancing, expertise alignment
* '''Mode switching''' — adjusting behavior based on operational mode (planning, execution, crisis)
* '''Context shaping''' — assembling the precise information each agent needs
* '''Workflow enforcement''' — ensuring lifecycle rules, stage gates, and contribution requirements are respected

=== Layer 3 — Agent Execution Layer (Probabilistic) ===
The expensive layer — invoked only when Layers 1 and 2 have confirmed it is justified:

* LLM-powered reasoning, tool usage, artifact generation, interpretation, and collaboration

This layer consumes tokens, compute, and time. The entire system architecture exists to ensure it is invoked efficiently and only when necessary.

=== Layer 4 — Capability and Extension Layer ===
Defines what agents can actually do — skills, tools, plugins, MCP integrations,<ref name="ref9_553fac">"Introducing the Model Context Protocol." Anthropic, November 2024. [anthropic.com/news/model-context-protocol](<nowiki>https://www.anthropic.com/news/model-context-protocol</nowiki>). Specification: [modelcontextprotocol.io](<nowiki>https://modelcontextprotocol.io/specification/2025-11-25</nowiki>)</ref> and RAG infrastructure.<ref name="ref5_3efac1" /> This layer enables '''heterogeneous intelligence''': agents are not uniform, and each carries a different combination of capabilities suited to its role.

=== Layer 5 — Interaction Layer ===
The surfaces through which humans and systems inject intent — direct prompts, agent mentions, declarative inputs, passive delegation, and ambient automation.

=== Layer 6 — Observability and Governance Layer ===
Provides decision traces, activity logs, state histories, artifact lineage, cost metrics, performance analytics, and incident reports.

=== Support and Service Layers ===
Operating continuously and independently: state synchronization, event routing, context indexing, health monitoring, and authentication services.
{| class="wikitable"
|'''Layer'''
|'''Function'''
|'''Cost Profile'''
|-
|L0 — Substrate
|State, events, relationships
|Infrastructure
|-
|L1 — Deterministic Brain
|Evaluation, gating, scheduling
|Zero marginal
|-
|L2 — Orchestration
|Routing, selection, enforcement
|Zero marginal
|-
|L3 — Agent Execution
|LLM reasoning, artifact generation
|Token cost per invocation
|-
|L4 — Capabilities
|Skills, tools, plugins, MCP, RAG
|Per-use
|-
|L5 — Interaction
|Prompts, mentions, automation
|Varies
|-
|L6 — Observability
|Traces, metrics, governance
|Infrastructure
|}
The critical insight: Layers 1 and 2 — where the majority of decision-making occurs — operate at zero marginal cost. Layer 3 is invoked only when justified.
----

== Multi-Dimensional State Model ==
A fundamental design principle of vibe managing is that '''state is not singular'''. Entities maintain multiple independent but synchronized state dimensions:<ref name="ref10_e4f741">The multi-dimensional state model addresses a known limitation in conventional task tracking, where a single "status" field conflates lifecycle position, execution state, quality signals, and progress indicators.</ref>

* '''Lifecycle State''' — macro-level progression across defined stages (idea → design → build → validate → release → maintain)
* '''Execution State''' — operational workflow status (backlog → ready → in_progress → blocked → done)
* '''Progress State''' — continuous indicators: completion percentage, confidence level, effort burn vs. estimate, velocity
* '''Readiness State''' — structured conditions and flags governing transitions, computed from artifact completeness
* '''Validation State''' — quality and acceptance signals (unknown → pending → passed → failed → needs_revision), potentially requiring multi-agent consensus
* '''Context State''' — information availability: scope references, injection hash, freshness score, consumption record

These dimensions are '''orthogonal, not hierarchical'''. A task can be in <code>build</code> lifecycle, <code>blocked</code> execution, at 60% progress, with partial readiness, pending validation, and stale context — and the system responds to each dimension independently.

=== Multi-Axis Execution Model ===
Beyond individual entity state, the execution environment operates across simultaneous axes:
{| class="wikitable"
|'''Axis'''
|'''Dimension'''
|'''Values'''
|-
|'''Temporal Urgency'''
|How urgent
|Idle, Normal, Priority, Crisis
|-
|'''Cognitive Mode'''
|How to think
|Planning, Investigation, Execution, Validation, Recovery
|-
|'''Economic Mode'''
|How to spend
|Minimal, Balanced, High-performance, Unbounded
|-
|'''Confidence / Risk'''
|How certain
|Experimental, Draft, Verified, Critical
|}
Each task exists at the intersection of all axes simultaneously, and the system adjusts behavior — agent selection, model tier, validation requirements, escalation policies — based on the combined position.
----

== Dual-Board Architecture ==
Vibe managing systems organize work across two primary board types:<ref name="ref11_246b91">Anderson, D.J. ''*Kanban: Successful Evolutionary Change for Your Technology Business*''. Blue Hole Press, 2010. ISBN 978-0-9845214-0-1.</ref>

=== Project Management Board (PM Board) ===
The strategic layer that defines '''intent''': project stages, phases, epics, modules, readiness conditions, contribution requirements, quality gates, and strategic artifacts.

=== Operations Board (Ops / Kanban Board) ===
The execution layer that reflects '''reality''': task decomposition, work-in-progress, blockers, agent assignments, incremental artifacts, and real-time state.

'''PM Board = what should exist.''' Ops Board = what is happening. These are independent systems, neither a view of the other, synchronized through five mechanisms:

* '''Structural''' (PM → Ops) — epics spawn task graphs
* '''State''' (Ops → PM) — progress and readiness propagate upward
* '''Semantic''' (bidirectional) — artifact outcomes influence readiness and lifecycle
* '''Event-driven''' (bidirectional) — state changes trigger workflows
* '''Intent''' (PM → Ops) — goal changes reshape operational plans

----

== Agent Fleet Architecture ==

=== Role-Based Agents ===
Vibe managing systems employ a heterogeneous collection of agents:

* '''Strategic agents''' — project manager agents (planning, lifecycle enforcement, PM-Ops bridging) and fleet operations agents (system health, resource allocation, approval authority)
* '''Specialist agents''' — architecture, implementation, quality assurance, infrastructure, documentation, design, security
* '''Governance agents''' — validation (gate transitions, quality signals), accountability (compliance, audit), context management (information flow optimization)

=== Configurable Behavior ===
Agents are dynamically configured based on current lifecycle stage, operational mode, budget constraints, context requirements, and assigned responsibilities. They may use different reasoning strategies, tools, plugins, model tiers, or even different AI backends depending on conditions.<ref name="ref8_78709a" />

=== Agent Lifecycle State Machine ===
 <code>ACTIVE  -->  IDLE  -->  SLEEPING  -->  OFFLINE
   ^           |           |              |
   +-----------+-----------+--------------+
               (task assigned / wake event)</code>
The brain tracks content-aware hashes (not just timestamps) to detect whether anything meaningful changed between evaluations, preventing unnecessary agent wake-ups.
----

== Interaction Model ==
Vibe managing supports a broad interaction surface:

* '''Direct prompts''' — explicit instructions for artifact generation, task creation, or state updates
* '''Agent mentions''' — @Agent invocations within comments or external and internal chat messages, normalized into events with full thread context
* '''Declarative inputs''' — structured commands to create epics, modules, tasks with type specification and clear verbatim requirements
* '''Passive delegation''' — high-level intent left for PM agents to decompose and assign autonomously
* '''Ambient automation''' — system reacts to state changes, time-based triggers, or threshold crossings without any prompt

This allows both precise manual control and high-level strategic delegation within the same system.
----

== Methodology and Stage Progression ==
Tasks progress through a structured cognitive stage sequence, e.g.:
 <code>Conversation -> Analysis -> Investigation -> Reasoning -> Work</code>
Each stage requires specific artifacts (verbatim requirement, analysis document, research findings, plan, deliverables) and enforces tool restrictions at the system boundary. An agent that attempts to use a work-stage tool during analysis receives an error and a protocol violation event is recorded.

Task types may skip stages intelligently: subtasks enter at reasoning (parent already analyzed), spikes have no work stage (research only), concerns stop at investigation, blockers fast-track to reasoning.

Readiness is a structured enumeration linked to stages — work stage requires readiness ≥ 99, ensuring all prerequisites are satisfied before execution begins.
----

== Context Injection and Management ==
Context is dynamically assembled and delivered to agents using:

* '''Scoped injection''' — only relevant state slices per agent per interaction
* '''Layered context''' — global (project), local (task), ephemeral (current action)
* '''Event-triggered refresh''' — tracked by content-aware hashing
* '''Compression and summarization''' — maintaining density without exceeding capacity
* '''Intent preservation''' — verbatim requirement text always accessible through decomposition chains
* '''Persistent memory integration''' — board memory, MCP providers,<ref name="ref9_553fac" /> RAG indexes<ref name="ref5_3efac1" />

A key optimization: the deterministic brain pre-assembles context using direct API calls (zero tokens) before any agent is invoked. Agents wake with everything prepared — no discovery phase, no wasted tokens.
----

== Artifact-Centric Workflow ==
Artifacts — code, specifications, test results, documentation, designs, plans — are first-class versioned entities. They:

* Are typed and linked to tasks, phases, and agents
* Influence readiness computation (populating required fields advances readiness)
* Trigger validation processes when completed
* Satisfy gate conditions for lifecycle transitions
* Feed into RAG indexes and context stores, building the system's evolving knowledge base

Artifacts form the persistent memory and output surface of the system.
----

== Optimization, Economy, and Budget Modes ==

=== Internal Economy ===
Vibe managing systems maintain an internal resource economy tracking tokens (LLM inference cost), time (effort burn vs. estimates), compute (model tier usage across cloud and local backends), and attention (concurrent task limits, context utilization).

=== Budget Modes Examples ===
A single declarative setting — the budget mode — controls fleet tempo and propagates atomically: orchestration cycle speed, agent scheduling frequency, dispatch caps, heartbeat evaluation frequency, and model tier preferences.
{| class="wikitable"
|'''Mode'''
|'''Characteristics'''
|-
|'''Turbo'''
|Maximum throughput — shortest cycles, highest dispatch
|-
|'''Aggressive'''
|High urgency — fast cycles, elevated dispatch
|-
|'''Standard'''
|Normal operations — balanced timing
|-
|'''Economic'''
|Cost-conscious — longer cycles, reduced dispatch, cheaper models
|}

=== Modes of Operation Examples ===
Beyond tempo, behavior adapts based on operational context:
{| class="wikitable"
|'''Mode'''
|'''Focus'''
|'''System Behavior'''
|-
|'''Planning'''
|Structure
|High reasoning, low execution, analysis emphasis
|-
|'''Investigation'''
|Exploration
|Research tools, broad context
|-
|'''Execution'''
|Delivery
|Work tools, narrow context, production validation
|-
|'''Validation'''
|Quality
|Review tools, strict gates, multi-agent consensus
|-
|'''Crisis'''
|Rapid response
|Priority override, highest-capability models
|-
|'''Recovery'''
|Stabilization
|Diagnostic focus, conservative dispatch
|}

=== Deterministic Optimization ===
The brain enforces economic policies at zero inference cost: idle suppression, event aggregation, graduated escalation, model tier cascading, and silent heartbeat optimization (after confirming no work exists, the brain intercepts future evaluations deterministically at $0, only waking the agent when meaningful work appears).

=== Model Tier Selection and Backend Routing ===
Systems operate across multiple AI backends with selection driven by task complexity, type, agent role, and economic mode. Advanced systems support '''shadow routing'''<ref name="ref12_d82553">Shadow routing parallels canary deployment strategies in software engineering. See: ["Shadow deployment vs. canary release of ML models."](<nowiki>https://www.qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models</nowiki>) JFrog ML.</ref> — running a candidate model in parallel, comparing outputs, promoting when quality matches, with automatic rollback if post-promotion performance degrades.
----

== Communication and Notification Fabric ==
Vibe managing systems operate across a distributed interaction fabric:

* '''Internal messaging''' (board memory, task comments) — persistent, structured, searchable
* '''Real-time chat''' (IRC, Slack, Discord) — immediate, conversational, multi-channel
* '''Push notifications''' (ntfy, push services, email) — alerting, escalation, mobile reach
* '''Code platforms''' (GitHub, GitLab) — PRs, CI events, code review
* '''Project management surfaces''' (Plane, Jira, Linear) — PM-layer updates, sprint tracking
* '''Webhooks and APIs''' — integration with arbitrary external systems

All messages, regardless of source, are '''normalized into typed events''' — enabling the deterministic brain to process interactions from any surface using identical evaluation logic.

Notification intelligence includes priority-based routing, cooldown and deduplication, suppression rules, digest aggregation, and agent-triggered escalation.
----

== Knowledge Infrastructure ==
Systems integrate with knowledge management infrastructure:

* '''RAG''' (Retrieval-Augmented Generation)<ref name="ref5_3efac1" /> — indexed knowledge bases with scoped retrieval and depth control
* '''MCP''' (Model Context Protocol)<ref name="ref9_553fac" /> — standardized connections to external memory and context systems
* '''Board memory''' — persistent structured messaging tagged with semantic labels
* '''Event stores''' — persistent logs queryable for decision traces
* '''Artifact indexing''' — completed work feeds into knowledge bases for future retrieval

Knowledge follows a lifecycle: generated, indexed, delivered, validated, evolved, and retired when superseded.
----

== Safety and Governance ==

=== Storm Prevention ===
Systems protect against runaway cost and cascading failures through multi-indicator monitoring, graduated response (watch → warning → storm → critical), circuit breakers with exponential backoff, and automated incident documentation.

=== Behavioral Security ===
All inputs — task content, code diffs, agent outputs, and human directives — are analyzed for security concerns (credential exfiltration, destructive operations, security bypass, supply chain risks). Critical findings place automatic holds on the approval pipeline. Human directives are scanned but never blocked.

=== Delivery Phase Gates ===
Quality standards escalate with maturity. Early phases require architectural review; production requires contributions from all specialist roles. Gate requirements are PO-defined and system-enforced.

=== Immune System ===
At higher maturity, systems detect pathological agent behaviors (laziness, protocol violations, drift), inject corrective lessons with comprehension evaluation, and apply graduated consequences. Self-healing workflows automatically reassign stuck tasks and adjust configurations based on performance patterns.
----

== Observability ==
Vibe managing provides visibility uncommon in conventional AI systems:

* '''Decision traces''' — why the brain dispatched agent X to task Y with model Z
* '''State histories''' — every change with timestamps and causal links
* '''Artifact lineage''' — provenance from creation through validation
* '''Cost analytics''' — token usage per task, agent, model tier, time window
* '''Labor attribution''' — per-completion stamps: agent, model, effort, validation rounds, confidence
* '''Incident reports''' — automated anomaly documentation with prevention recommendations

This enables answering: '''"Why did this decision happen, what did it cost, and was it correct?"'''
----

== Operability ==
Operators can tune:
{| class="wikitable"
|'''Control'''
|'''Governs'''
|-
|Budget modes
|Fleet tempo — cycle speed, dispatch rates, heartbeat frequency
|-
|Work modes
|Dispatch policy — active, paused, finish-current-only, emergency-only
|-
|Agent permissions
|Per-role tool access, stage restrictions, approval authorities
|-
|Autonomy levels
|Per-role lifecycle thresholds
|-
|Validation policies
|Gate requirements, required contributor roles per phase
|-
|Context strategies
|Injection depth, scope rules, compression policies
|-
|Synchronization rules
|PM-Ops sync frequency, event propagation
|-
|Model selection
|Override at task, agent, or fleet level; backend preferences
|-
|Security policies
|Scan strictness, hold thresholds, escalation rules
|}
The system respects the most restrictive setting in the hierarchy.
----

== Evolution Levels ==
Vibe managing exists on a maturity spectrum:
{| class="wikitable"
|'''Level'''
|'''Name'''
|'''Key Capability'''
|'''Technical Requirements'''
|-
|'''L0'''
|Prompting
|Single agent, ephemeral
|None
|-
|'''L1'''
|Assisted Workflow
|Named agents, manual orchestration
|Task tracking, agent identities
|-
|'''L2'''
|Structured Orchestration
|Dual boards, defined roles
|Board system, role definitions, basic triggers
|-
|'''L3'''
|Stateful Multi-Agent
|Multi-dimensional state, artifact tracking
|Event bus, sync services, dependency management
|-
|'''L4'''
|Deterministic Hybrid
|Non-LLM brain, cost-aware gating
|Control layer, budget monitoring, heartbeat scheduling
|-
|'''L5'''
|Adaptive System
|Mode switching, methodology enforcement
|Dynamic configuration, budget propagation, stage gates
|-
|'''L6'''
|Autonomous Coordination
|Self-organizing, immune system
|Autonomous PM, disease detection, shadow routing
|-
|'''L7'''
|Mission Control (S-Tier)
|Predictive, self-healing, federated
|Adaptive policies, federation, strategic decision support
|}
Progression is not strictly sequential — organizations implement capabilities from different levels based on priorities. The spectrum also represents an accessibility ladder: L0–L1 requires prompt engineering expertise; L4+ enables Product Owners with no AI knowledge to manage complex fleets through strategic controls alone.
----

== Comparison with Related Paradigms ==
{| class="wikitable"
|'''Paradigm'''
|'''Relationship'''
|-
|'''Vibe coding'''<ref name="ref4_a198d7" />
|Predecessor — single-agent, prompt-driven. Vibe managing extends this to fleet-scale orchestration.
|-
|'''Multi-agent frameworks'''<ref name="ref3_f675de" /><ref name="ref8_78709a" />
|Provide coordination primitives. Vibe managing adds lifecycle governance, deterministic control, and economics.
|-
|'''Workflow automation'''
|Executes predefined sequences. Vibe managing adds adaptive, AI-powered execution within constraints.
|-
|'''DevOps pipelines'''
|Static automation. Vibe managing adds cognitive, adaptive execution with dynamic routing.
|-
|'''Project management tools'''<ref name="ref11_246b91" />
|Track human work. Vibe managing extends these to govern AI work in the same systems.
|-
|'''Autonomous agent systems'''<ref name="ref13_c60a21">MacManus, R. "AI Engineering Trends in 2025: Agents, MCP and Vibe Coding." ''*The New Stack*'', 2025. [thenewstack.io](<nowiki>https://thenewstack.io/ai-engineering-trends-in-2025-agents-mcp-and-vibe-coding/</nowiki>)</ref>
|Emphasize independence. Vibe managing emphasizes governance and controlled autonomy.
|}
----

== Criticisms and Challenges ==
'''Complexity overhead''' — The architectural investment (dual boards, sync services, control layers, multi-dimensional state) may exceed value for small-scale projects. For many use cases, direct prompting remains more efficient.

'''State explosion''' — Six independent state dimensions across potentially thousands of entities create combinatorial complexity requiring strict schema governance.

'''Agent conflict''' — Questions of authority arise when multiple agents produce contradictory evaluations. Deterministic resolution rules handle common cases but edge cases produce unexpected behaviors.

'''Drift''' — Agents may diverge from intent through successive decomposition. Intent preservation mechanisms mitigate but do not eliminate this risk.

'''Economic justification''' — Full vibe managing infrastructure requires significant investment justified only by scale and duration of the managed work.

'''Observability and privacy''' — Comprehensive decision traces and labor attribution raise questions about monitoring dynamics in collaborative human-AI environments.
----

== Applications ==

* Software development lifecycle management
* DevOps and infrastructure orchestration
* Product and project management
* Research and knowledge work coordination
* Compliance and governance workflows
* Autonomous and semi-autonomous operational systems

----

== Significance ==
Vibe managing represents a transition from prompt-centric AI usage to stateful, system-level orchestration of intelligent actors. It introduces a framework where coordination, efficiency, and lifecycle governance are integral to AI-driven work.

By combining human intent, agent autonomy, deterministic control, and resource-aware execution, vibe managing defines a foundation for managing complex, evolving systems of work at scale — where the barrier between intent and impact progressively decreases as system maturity increases, enabling non-technical stakeholders to govern complex AI operations through strategic controls rather than technical interaction.
----

== See Also ==

* Multi-agent systems
* Workflow orchestration
* Vibe coding
* DevOps
* Kanban (development)
* Human-AI collaboration
* Autonomous systems
* Model Context Protocol
* Retrieval-augmented generation
* Infrastructure as code
* Project lifecycle management

----

== References ==
<ref name="ref1_50a166" />: Guo, T., Chen, X., Wang, Y., et al. "Large Language Model based Multi-Agents: A Survey of Progress and Challenges." ''*IJCAI 2024*''. [arXiv:2402.01680](<nowiki>https://arxiv.org/abs/2402.01680</nowiki>)

<ref name="ref2_f87207" />: "From vibe coding to multi-agent AI orchestration: Redefining software development." ''*CIO.com*'', 2025. [cio.com/article/4150165](<nowiki>https://www.cio.com/article/4150165/from-vibe-coding-to-multi-agent-ai-orchestration-redefining-software-development.html</nowiki>)

<ref name="ref3_f675de" />: Wu, Q., et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." Microsoft Research, 2023. [arXiv:2308.08155](<nowiki>https://arxiv.org/abs/2308.08155</nowiki>)

<ref name="ref4_a198d7" />: Karpathy, A. [@karpathy]. "There's a new kind of coding I call 'vibe coding'..." Twitter/X, February 2, 2025. [x.com/karpathy/status/1886192184808149383](<nowiki>https://x.com/karpathy/status/1886192184808149383</nowiki>)

<ref name="ref5_3efac1" />: Lewis, P., Perez, E., Piktus, A., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." ''*NeurIPS 2020*''. [arXiv:2005.11401](<nowiki>https://arxiv.org/abs/2005.11401</nowiki>)

<ref name="ref6_a7d89e" />: Park, J.S., O'Brien, J.C., Cai, C.J., et al. "Generative Agents: Interactive Simulacra of Human Behavior." ''*ACM UIST 2023*''. [arXiv:2304.03442](<nowiki>https://arxiv.org/abs/2304.03442</nowiki>)

<ref name="ref7_b4c849" />: Khosravi, H., Anderson, T. (eds). "Requirements for Separation of IP Control and Forwarding." ''*RFC 3654*'', IETF, November 2003. [rfc-editor.org/rfc/rfc3654](<nowiki>https://www.rfc-editor.org/rfc/rfc3654.html</nowiki>). See also: ["What is the control plane?"](<nowiki>https://www.cloudflare.com/learning/network-layer/what-is-the-control-plane/</nowiki>) Cloudflare.

<ref name="ref8_78709a" />: Wang, L., Ma, C., Feng, X., et al. "A Survey on Large Language Model based Autonomous Agents." ''*Frontiers of Computer Science*'', 2023. [arXiv:2308.11432](<nowiki>https://arxiv.org/abs/2308.11432</nowiki>)

<ref name="ref9_553fac" />: "Introducing the Model Context Protocol." Anthropic, November 2024. [anthropic.com/news/model-context-protocol](<nowiki>https://www.anthropic.com/news/model-context-protocol</nowiki>). Specification: [modelcontextprotocol.io](<nowiki>https://modelcontextprotocol.io/specification/2025-11-25</nowiki>)

<ref name="ref10_e4f741" />: The multi-dimensional state model addresses a known limitation in conventional task tracking, where a single "status" field conflates lifecycle position, execution state, quality signals, and progress indicators.

<ref name="ref11_246b91" />: Anderson, D.J. ''*Kanban: Successful Evolutionary Change for Your Technology Business*''. Blue Hole Press, 2010. ISBN 978-0-9845214-0-1.

<ref name="ref12_d82553" />: Shadow routing parallels canary deployment strategies in software engineering. See: ["Shadow deployment vs. canary release of ML models."](<nowiki>https://www.qwak.com/post/shadow-deployment-vs-canary-release-of-machine-learning-models</nowiki>) JFrog ML.

<ref name="ref13_c60a21" />: MacManus, R. "AI Engineering Trends in 2025: Agents, MCP and Vibe Coding." ''*The New Stack*'', 2025. [thenewstack.io](<nowiki>https://thenewstack.io/ai-engineering-trends-in-2025-agents-mcp-and-vibe-coding/</nowiki>)

<!-- Categories: Artificial intelligence | Multi-agent systems | Project management | Software development process | Workflow technology | Human-computer interaction -->