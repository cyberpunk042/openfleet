# Strategic Vision — LocalAI Independence & Fleet Economics

## What This Document Is

The long-term strategic vision for fleet economics and independence. This is
the FIRST mission for DSPD/Plane once the fleet is operational: make LocalAI
functional, progressively offload work from Claude, and build toward
independent operation.

This is not a quick fix — it's a multi-stage, long-run epic. Every word of
the user's vision is preserved here and will be answered with concrete plans.

---

## Part 1: User Vision (Verbatim — Complete)

> "This is not in the scope but we will also look how to wise ourself through
> aicp and localai when its online especially for but that we will need to plan
> after all this and we will be basically able to pass through it first and it
> should only call claude when needed otherwise do mcp / tool calls and whatever
> but we will need to validate the project and make sure we can support all that
> properly too. this will be work and it will be the first project in the plane /
> dspd board that we will need to obviously make as a milestone / epic with a
> very long run. a very long plan and strategic passes on it."

> "DO not corrupt or minimize or compress my words. take them as is. and you will
> need to quote them into the new documents in order to achieve all this properly
> and not forget a single thing and so that we meet the requirements or above and
> deliver a great product / a great solution that will make the work even stronger
> and economic."

> "Its important the the main first mission for the plane / dspd is to make
> localAI functional and then make it more and more reliable to offload as much
> as possible the work from claude till one day maybe even if probably not entirely
> even try to actually run independently as much as possible, especially for things
> and loops and events that do not require heavy works and especially for very well
> defined and structured orders or directives that we can find out how to route
> perfectly to the right model and tools everytime for a mix of multiple advantages
> so it will be multiple targets always aligned with the same mission of being more
> independent and having our full 2 cluster LocalAI peered in the network with one
> Plane and eventually 2 or even 3 fleets. there will be multiple stage to this
> including trial of the multiple features and attempt to put in place and such."

> "I feel like you are trying to hack again.. why would you need to start the board
> to clean it up? a manual operation again? you are doing what a tool should do and
> I or a responsible agent should use when appropriate and only then and even then
> we need to be able to keep track of it and store them as archive."

> "We will continue working with the fleet for now till we are really at this point
> and ready to put into work safely the agent into moving toward the target at a
> reasonable pace with proper guidance and flow and keeping in the loop and making
> sure that the requirements are the right one and the planning the right one and
> that the project Plane will be used accordingly and engrained into them."

> "important to remember the plane place and yet how oc agent still work on ocmc,
> that's why we need smart tools, chains that will trigger multiple things for one
> call or one event and that will keep listening to all side and keep in sync for
> if I do a manual change or adding or task or information and such that everything
> is kept track of and triggering the right event that will wake the right agent or
> will influence it for its next heartbeat."

> "we need to really make this strong."

> "I will certainly not manually enter the mission nor will I do a manual request.
> it will be proper IaC with proper configs and scripts and with proper methods of
> works and augmentations"

---

## Part 2: The Mission — LocalAI Independence

### 2.1 What This Means

The fleet currently depends 100% on Claude for all agent work. Every heartbeat,
every task execution, every review, every chat response — all Claude tokens.
This is expensive, rate-limited, and creates the catastrophic drain risk we
just experienced.

The mission: **progressively reduce Claude dependency by routing work through
LocalAI for everything that doesn't require Claude's reasoning.**

### 2.2 What LocalAI Handles vs What Claude Handles

| Operation | Today (Claude) | Target (LocalAI) | Why |
|-----------|---------------|-------------------|-----|
| Heartbeat check (no work) | Claude session (~8K tokens) | LocalAI (0 Claude tokens) | Just reading context + HEARTBEAT_OK |
| fleet_read_context | Claude tool call | Direct API call (no LLM needed) | It's HTTP calls to MC API |
| fleet_agent_status | Claude tool call | Direct API call | Same — just HTTP |
| fleet_chat post | Claude session | LocalAI or direct API | Posting a message doesn't need reasoning |
| Board memory read | Claude context | Direct API call | Reading is not reasoning |
| Simple task dispatch | Claude orchestrator | Fleet daemon (Python, no LLM) | Already done — orchestrator is Python |
| Task acceptance (simple) | Claude session | LocalAI (structured response) | "Accept plan: do X then Y" |
| Complex implementation | Claude (opus) | Claude (opus) — KEEP | Needs deep reasoning |
| Architecture design | Claude (opus) | Claude (opus) — KEEP | Needs creative thinking |
| Security analysis | Claude (opus) | Claude (opus) — KEEP | Can't compromise on security |
| Code review (simple) | Claude session | LocalAI (pattern matching) | Test pass/fail, lint results |
| Code review (complex) | Claude (sonnet) | Claude (sonnet) — KEEP | Needs understanding |
| Sprint planning | Claude (opus) | Claude (opus) — KEEP | Strategic thinking |

### 2.3 The Architecture

```
Request / Event
    ↓
Fleet Control Plane (Python — no LLM)
    ↓
Router: Does this need reasoning?
    ├── NO → LocalAI (local, free, fast)
    │         ├── 3B model for structured responses
    │         ├── MCP tool calls (direct HTTP, no LLM)
    │         └── Template-based responses
    └── YES → Claude (cloud, paid, powerful)
              ├── opus for complex (architecture, security, planning)
              └── sonnet for standard (implementation, review)
```

### 2.4 The Infrastructure Target

> "having our full 2 cluster LocalAI peered in the network with one Plane
> and eventually 2 or even 3 fleets"

```
Network Topology (Target):

  Machine 1: Fleet Alpha
    ├── LocalAI Cluster 1 (GPU: 8GB VRAM)
    ├── OpenClaw Gateway + MC
    ├── Fleet Daemons (orchestrator, sync, monitor)
    └── 10 Agents (alpha-prefixed)

  Machine 2: Fleet Bravo
    ├── LocalAI Cluster 2 (GPU: 8GB VRAM)
    ├── OpenClaw Gateway + MC
    ├── Fleet Daemons
    └── 10 Agents (bravo-prefixed)

  Shared Services:
    ├── Plane (one instance, shared by all fleets)
    ├── GitHub (shared repos)
    └── ntfy (shared notifications)

  LocalAI Peering:
    ├── Cluster 1 ↔ Cluster 2 (load balance, failover)
    └── Routing: simple tasks → local cluster, complex → Claude
```

---

## Part 3: Stages

### Stage 1: Make LocalAI Functional (AICP Milestone)

**Work:**
1. Assess current state of LocalAI and AICP — what works, what doesn't
2. Get local inference working: model loaded, API responding
3. Verify OpenAI-compatible API: chat completions endpoint
4. Benchmark: latency, throughput, quality for structured responses
5. Validate the 2-cluster network setup (both machines)

### Stage 2: Route Simple Operations to LocalAI

**Work:**
1. Build fleet/core/inference_router.py — routes requests to LocalAI or Claude
2. Routing rules: heartbeat checks → LocalAI, implementation → Claude
3. Direct MCP tool calls (HTTP) bypass LLM entirely for read operations
4. fleet_read_context → direct API call (no LLM wrapper needed)
5. fleet_agent_status → direct API call
6. Measure: what % of fleet operations can run on LocalAI?

### Stage 3: Progressive Offload

**Work:**
1. Agent heartbeats with no work → LocalAI (just check context, respond OK)
2. Simple task acceptance → LocalAI (structured plan generation)
3. Simple reviews (test pass/fail) → LocalAI
4. Chat responses (factual, not creative) → LocalAI
5. Board memory summarization → LocalAI
6. Measure and validate quality: LocalAI vs Claude for each operation type

### Stage 4: Reliability and Failover

**Work:**
1. If LocalAI fails → fall back to Claude (graceful degradation)
2. If Claude is rate-limited → queue work for LocalAI where possible
3. Cluster peering: Machine 1's LocalAI can serve Machine 2's fleet
4. Load balancing between clusters
5. Health monitoring for both inference backends

### Stage 5: Near-Independent Operation

**Work:**
1. Fleet runs primarily on LocalAI for routine operations
2. Claude called only for: complex code, architecture, security, strategic planning
3. Budget impact: 80%+ reduction in Claude token usage
4. Fleet can operate during Claude outages (degraded but functional)
5. Continuous optimization: identify more operations that can go local

---

## Part 4: Smart Tools and Chains

> "we need smart tools, chains that will trigger multiple things for one call
> or one event and that will keep listening to all side and keep in sync"

### 4.1 One Call → Multiple Actions

When a task completes, ONE event triggers:
- MC task status update (direct API)
- Plane issue status update (direct API)
- IRC notification (direct API)
- ntfy notification (direct API)
- Board memory update (direct API — only for decisions/knowledge)
- Dependency check (Python — no LLM)
- Next task dispatch if unblocked (Python — no LLM)

ALL of this without a single Claude token. The event chain executor
calls APIs directly. Only the AGENT's work (the actual task implementation)
needs Claude.

### 4.2 Listen to All Sides

The fleet sync system must detect changes from:
- MC board (task status, comments, memory — polling or webhooks)
- Plane (issues, sprints, comments — polling or webhooks)
- GitHub (PRs, comments, merges — polling or webhooks)
- IRC (human messages — via bot)
- ntfy (human responses — if ntfy supports it)
- Human direct actions (manual task edit, manual PR comment)

Each change → event → router → right agent's heartbeat context OR
immediate wake if urgent.

### 4.3 Sync Across Surfaces

When the human makes a change on ANY surface, it propagates:
- Human edits task on MC → Plane issue updated → agents see in context
- Human comments on GitHub PR → MC task comment added → agent notified
- Human creates issue in Plane → MC task created → agent dispatched
- Human merges PR → MC task completed → Plane updated → IRC notified

Nothing manual. Everything tracked. Everything triggering the right flow.

---

## Part 5: Board Cleanup as a Tool, Not Manual

> "why would you need to start the board to clean it up? a manual operation again?
> you are doing what a tool should do"

Board cleanup should be a fleet tool, not a manual operation:

```python
fleet_board_cleanup(
    archive_heartbeats=True,    # Archive done heartbeat tasks
    archive_review_process=True, # Archive done review process tasks
    archive_resolve_conflict=True, # Archive done conflict tasks
    keep_sprint_tasks=True,     # Keep sprint work visible
    keep_recent_days=7,         # Keep last 7 days of everything
)
```

This tool:
1. Archives noise tasks (heartbeats, review process, conflicts) — doesn't delete,
   stores in a separate archive for reference
2. Keeps sprint work and real tasks visible
3. Can be called by fleet-ops during heartbeat when board gets cluttered
4. Can be scheduled (e.g., weekly cleanup)
5. Tracks what was archived (audit trail)

The responsible agent (fleet-ops) uses this tool when appropriate. The human
can also trigger it via `fleet board cleanup` CLI command.

---

## Part 6: DSPD/Plane First Epic

This entire vision becomes the FIRST epic in Plane/DSPD once the fleet
is operational:

```
EPIC: Fleet Independence — LocalAI Integration
  Project: DSPD
  Priority: High (strategic)
  Duration: Long-run (months)

  Stories:
  1. Make LocalAI functional (AICP fix)
  2. Build inference router (fleet/core/inference_router.py)
  3. Route heartbeats to LocalAI
  4. Route simple operations to LocalAI
  5. Progressive offload measurement
  6. Cluster peering (2 LocalAI instances)
  7. Multi-fleet coordination (2-3 fleets, shared Plane)
  8. Near-independent operation validation
  9. Budget impact measurement and optimization
```

Each story has its own tasks, dependencies, and acceptance criteria.
The PM breaks this down using proper sprint planning.
This epic runs alongside other DSPD work.

---

## Part 7: Method of Work

> "I will certainly not manually enter the mission nor will I do a manual request.
> it will be proper IaC with proper configs and scripts and with proper methods of
> works and augmentations"

Everything is:
- **Configured**: YAML configs, .env files, fleet.yaml
- **Scripted**: setup.sh, configure-plane.sh, configure-gateway.sh
- **Automated**: orchestrator dispatches, sync daemon syncs, heartbeats cycle
- **Tracked**: MC tasks, Plane issues, board memory, IRC, ntfy
- **Reproducible**: clone + setup.sh = running fleet on new machine

No manual operations. No manual entries. No manual requests.
The human sets direction via Plane (create epics, set priorities).
The PM breaks it down. The fleet executes. The review chain validates.
The sync keeps everything in alignment.

---

## Part 8: How This Connects to Everything Else

```
Current work (this session):
  ├── Fix catastrophic bugs (C0-C14) ✅ mostly done
  ├── Pre-relaunch preparation (PR1-PR8) → in progress
  └── Verify communication works → pending
       ↓
Fleet relaunch (next):
  ├── PM drives Sprint 3 properly
  ├── Agents communicate and collaborate
  └── Review chain with quality
       ↓
DSPD/Plane operational:
  ├── Plane configured via IaC
  ├── Bidirectional sync working
  └── PM uses Plane for sprint management
       ↓
FIRST Plane epic — LocalAI Independence:
  ├── Stage 1: Make LocalAI functional
  ├── Stage 2: Route simple operations
  ├── Stage 3: Progressive offload
  ├── Stage 4: Reliability and failover
  └── Stage 5: Near-independent operation
       ↓
Target state:
  ├── 2 LocalAI clusters peered
  ├── 1 Plane instance shared
  ├── 2-3 fleets collaborating
  ├── 80%+ work on LocalAI
  ├── Claude only for complex reasoning
  └── Economic, independent, strong fleet
```