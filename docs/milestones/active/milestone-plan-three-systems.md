# Milestone Plan — Immune System, Teaching System, Methodology System

**Date:** 2026-03-30
**Status:** In progress — 23/44 milestones implemented (2026-03-30)
**Scope:** 44 milestones across three systems plus Plane integration
and cross-cutting platform evolutions

---

## Implementation Progress (2026-03-30)

| Category | Done | Total | Key Modules Built |
|----------|------|-------|-------------------|
| A. Foundation | 7 | 8 | plane_methodology.py, custom fields on both platforms |
| B. Methodology | 3 | 9 | methodology.py (stages/checks), standards.py (7 artifact types) |
| C. Teaching | 6 | 6 | **COMPLETE** — teaching.py (8 templates, adaptation, tracking) |
| D. Immune | 10 | 10 | **COMPLETE** — doctor.py (detection, response, health profiles) |
| E. Platform | 4 | 6 | gateway_client.py, orchestrator wired, events, MCP stage enforcement |
| G. OCMC UI | 0 | 5 | Not started (depends on backend data) |
| **Total** | **30** | **44** | |

**Tests:** 534 passing (153 new this session)
**Commits:** 17 this session
**New modules:** 7 (methodology, standards, teaching, doctor, plane_methodology, gateway_client, MCP stage enforcement)

---

## PO Requirements (Verbatim)

> "This is going to be 2000+ hours of work and its an entire system in
> the program."

> "we will need to use the state of the work items and such from Plane
> in our system. as the updates happens keeping in right state in parallel
> of the ocmc. state assignees, start date...."

> "we will need a series of evolutions for the immune system and the brain
> and orchestrator."

---

## Milestone Categories

### A. Foundation — Custom Fields & Plane Integration (A01-A06)

These must come first. Everything else depends on custom fields existing
on both platforms and Plane state flowing properly.

**A01: task_readiness custom field on OCMC**

The first custom field. Foundation for everything — the orchestrator
won't dispatch tasks below 99% readiness, the methodology system tracks
progress through this field, and the PO controls the fleet through it.

- Add integer field (0-100) to fleet board
- Script: `scripts/configure-board.sh` — add to the existing 14 fields
- API call: `POST /api/v1/organizations/me/custom-fields` with
  `field_key: "task_readiness"`, `field_type: "integer"`,
  `ui_visibility: "always"`, `default_value: 0`
- Orchestrator change: in `fleet/cli/orchestrator.py`, before dispatch,
  read `task.custom_fields.task_readiness` — skip if < 99
- MC client change: in `fleet/infra/mc_client.py`, parse task_readiness
  from custom field values in `_parse_task()`
- Model change: in `fleet/core/models.py`, add `task_readiness: int = 0`
  to `TaskCustomFields`
- Verification: create a task with readiness 0, confirm orchestrator
  skips it. Set to 99, confirm it gets dispatched.

**A02: task_readiness custom field on Plane**

Mirror on Plane so PO can set readiness from either platform.

- Add matching integer field on Plane issues
- Script: `scripts/plane-setup-members.sh` or direct Plane API
- Plane custom field API: Plane CE supports custom properties on issues
- Verify the sync worker can read this field from Plane
- Verify the field appears in the Plane UI on issues

**A03: requirement_verbatim custom field on OCMC**

The first cure. PO's words go here and cannot be modified by agents.

- Add text_long field to fleet board
- `field_key: "requirement_verbatim"`, `field_type: "text_long"`,
  `ui_visibility: "always"`
- No default value — empty until PO populates
- MC client: parse from custom fields in `_parse_task()`
- Model: add `requirement_verbatim: Optional[str] = None` to
  `TaskCustomFields`
- Heartbeat context: in `fleet/core/heartbeat_context.py`, include
  requirement_verbatim in the task context bundle. Always present.
  Never compacted. Never summarized. The anchor.
- Permission enforcement: agents should not write to this field.
  MC doesn't have per-field write permissions — enforcement must be
  in the fleet layer (MCP tools don't offer a way to modify it,
  doctor flags if it changes unexpectedly)

**A04: requirement_verbatim custom field on Plane**

Mirror on Plane. PO creates issues in Plane with verbatim requirements
that sync to OCMC.

- Add matching text_long field on Plane issues
- PO writes requirements directly in Plane when creating issues
- Sync worker mirrors to OCMC requirement_verbatim field
- Verify round-trip: PO writes in Plane → sync → appears on OCMC task

**A05: task_stage custom field on OCMC and Plane**

Tracks which methodology stage a task is in. Each stage has a protocol.

- Add text field on both platforms
- `field_key: "task_stage"`, `field_type: "text"`,
  `ui_visibility: "always"`
- Valid values: `conversation` | `analysis` | `investigation` |
  `reasoning` | `work` (enforced by fleet layer, not MC)
- Default: depends on task type and requirements. Probably
  `conversation` for new tasks without clear requirements, or a later
  stage for well-specified tasks.
- MC client: parse from custom fields
- Model: add `task_stage: Optional[str] = None` to `TaskCustomFields`
- Orchestrator: dispatch behavior varies by stage. `work` stage tasks
  go to agents for execution. Earlier stages go to agents for the
  appropriate protocol (conversation, analysis, etc.)

**A06: Sync new custom fields between Plane and OCMC**

The three new fields must flow between platforms.

- Extend `fleet/core/plane_sync.py` to handle task_readiness,
  requirement_verbatim, and task_stage
- Map field names between Plane custom properties and OCMC custom fields
- Direction: bidirectional — changes on either platform propagate
- Sync interval: same as current sync worker (120s) initially,
  possibly faster for critical fields like readiness
- Handle type mapping: integer (readiness), text_long (verbatim),
  text (stage) — verify Plane supports these types
- Test: change readiness in Plane → verify it appears on OCMC within
  sync interval. Change stage on OCMC → verify it appears in Plane.

**A07: Sync Plane state metadata to OCMC**

Plane has rich metadata the fleet systems need. Currently the sync is
basic — extend it to cover the full state.

- State (backlog/unstarted/started/completed/cancelled):
  Map to OCMC task status (inbox/in_progress/review/done)
  Define the mapping — Plane has more states than OCMC
- Assignees: Map Plane assignee to OCMC agent_name custom field
  (Plane has agent accounts from plane-setup-members.sh)
- Start date: Plane tracks when work started. Needed for stuck detection
  (immune system). Sync to OCMC custom field or use existing date field.
- Due date: Plane tracks deadlines. Sync to OCMC.
- Priority: Map Plane priority to OCMC priority
- Estimates: Map Plane estimate to story_points custom field
- Extend `fleet/core/plane_sync.py` and `fleet/infra/plane_client.py`
- Test: update each field in Plane → verify reflected on OCMC

**A08: Bidirectional sync conflict resolution**

Both platforms can be updated. What happens when they disagree?

- Define source of truth per field:
  - requirement_verbatim: Plane is source (PO writes there)
  - task_readiness: PO can update on either — last-write-wins with
    timestamp comparison
  - task_stage: fleet layer is source (methodology system manages it)
  - task status: need to define — OCMC drives during execution,
    Plane drives during planning?
- Implement conflict detection: if both sides changed since last sync,
  log the conflict and apply the resolution rule
- Emit conflict events to the event bus for observability
- Alert the PO on critical conflicts (readiness, verbatim changes)
- Test: update same field on both platforms between sync cycles,
  verify resolution is correct

---

### B. Methodology System (B01-B09)

The methodology system defines stages and protocols. Must be designed
before the immune system can detect violations of it.

**B01: Stage progression logic**

The brain of the methodology system. Determines which stages a task
needs and what checks must pass to advance.

- Define stage list: conversation, analysis, investigation, reasoning, work
- Define per-task-type stage requirements:
  - Epic: conversation → analysis → investigation → reasoning → work
  - Story: conversation → reasoning → work (if requirements are clear)
  - Task/subtask: reasoning → work (if well-specified)
  - Spike: conversation → investigation → reasoning
  - Bug: analysis → reasoning → work
  - These are defaults — PO can override for any task
- Define methodology checks per stage:
  - Conversation: PO responded, understanding confirmed, no open questions
  - Analysis: analysis document produced and reviewed
  - Investigation: research findings documented
  - Reasoning: plan produced and PO-confirmed
  - Work: readiness at 99-100%, plan exists
- Implementation: `fleet/core/methodology.py` (NEW)
  - `get_required_stages(task_type, task) → list[str]`
  - `check_stage_complete(task, stage) → bool`
  - `advance_stage(task, from_stage, to_stage)` — validates and transitions
- Stage transitions require PO confirmation (readiness increase)
- The methodology checks are the link to the immune system — if an
  agent violates a check, the immune system detects it

**B02: Conversation protocol implementation**

How agents discuss with the PO when requirements are unclear.

- Agent enters conversation when task_stage = "conversation"
- Agent behavior rules (encoded in agent context/heartbeat):
  - Extract knowledge from PO through task comments
  - Identify and state uncertainty explicitly
  - Propose understanding, accept correction
  - Produce WIP artifacts (research, analysis) — not deliverables
  - Do NOT produce finished work (code, PRs)
  - Do NOT leave conversation until PO confirms
- Communication through task comments (visible on OCMC and Plane)
- PO receives notification when agent has questions (ntfy, IRC)
- Asynchronous — agent can work on other ready tasks while waiting
- Implementation:
  - Conversation rules as context content for agents (context/ files)
  - Orchestrator dispatches conversation-stage tasks differently —
    agent gets a "discuss" instruction, not a "build" instruction
  - fleet_task_accept for conversation stage produces questions/
    proposals, not implementation plans

**B03: Analysis protocol implementation**

How agents analyze the problem space and current state.

- Agent enters analysis when task_stage = "analysis"
- Agent behavior:
  - Read and examine codebase, existing implementation, architecture
  - Produce analysis documents (iterative, WIP)
  - Present findings to PO via task comments or board memory
  - Do NOT produce solutions (that's reasoning)
  - Do NOT produce code (that's work)
- Methodology checks for analysis completion:
  - Analysis document exists
  - Key areas of codebase examined (specific to task)
  - PO reviewed findings
- Implementation: analysis rules in agent context, orchestrator
  dispatches analysis-stage tasks with analysis instructions

**B04: Investigation protocol implementation**

How agents research solutions and explore options.

- Agent enters investigation when task_stage = "investigation"
- Agent behavior:
  - Research solutions, explore options, examine prior art
  - Produce investigation documents and research findings
  - Explore thoroughly — not just the first option
  - Present options to PO — do NOT decide (that's reasoning)
  - Do NOT produce code
- Methodology checks for investigation completion:
  - Research document exists
  - Multiple options explored (not just one)
  - PO reviewed findings
- Implementation: investigation rules in agent context, orchestrator
  dispatches investigation-stage tasks with research instructions

**B05: Reasoning protocol implementation**

How agents plan their approach and make decisions.

- Agent enters reasoning when task_stage = "reasoning"
- Agent behavior:
  - Decide on approach based on requirements + analysis + investigation
  - Produce planning documents with specific implementation details
  - Map approach to specific files, components, patterns
  - Plan must reference the verbatim requirement explicitly
  - Present plan to PO for confirmation
- Methodology checks for reasoning completion:
  - Plan document exists
  - Plan references verbatim requirement
  - Plan specifies target files/components
  - PO confirmed the plan
  - Readiness at or approaching 99-100%
- Implementation: reasoning rules in agent context, fleet_task_accept
  becomes the plan submission point, plan validated against verbatim
  requirement

**B06: Work protocol implementation**

How agents execute — the only stage where finished deliverables are
produced.

- Agent enters work when task_stage = "work" AND task_readiness >= 99
- Agent behavior:
  - Execute the confirmed plan
  - Produce deliverables: code, PRs, config, documentation
  - Follow existing conventions: conventional commits, tests, task lifecycle
  - Stay within scope — work from verbatim requirement and confirmed plan
  - Do NOT add unrequested scope
- Integrates with existing fleet systems:
  - Task lifecycle PRE/PROGRESS/POST stages
  - MCP tools: fleet_task_accept, fleet_commit, fleet_task_complete
  - Skill enforcement: required tools per task type
  - Review chain: fleet-ops reviews completed work
- Methodology checks for work completion:
  - Acceptance criteria met
  - PR submitted (if code task)
  - Tests pass
  - Required MCP tools called
  - Verbatim requirement addressed
- Implementation: work rules in agent context, orchestrator only
  dispatches work-stage tasks for execution

**B07: Methodology observability**

Track everything. The PO must be able to see agents following protocols.

- Track per task:
  - Current stage
  - Stage history (when entered, when exited, who authorized)
  - Methodology checks: which passed, which failed, when
  - Protocol violations (agent produced code during conversation stage)
- Track per agent:
  - Which stages the agent is in across all its tasks
  - Compliance rate: how often does the agent follow protocol
  - Stage transition patterns
- Implementation:
  - Events emitted on stage changes → event bus → event store
  - Custom fields updated on stage changes → visible in OCMC and Plane
  - Board memory entries for significant transitions
  - IRC notifications for PO
- Integration point with immune system: protocol violations are
  detectable through observability data

**B08: Orchestrator evolution — methodology-aware dispatch**

The orchestrator must understand stages and readiness.

- Before dispatch, read task_stage and task_readiness
- Dispatch behavior by stage:
  - `conversation`: dispatch with conversation instructions. Agent
    discusses, doesn't produce deliverables.
  - `analysis`: dispatch with analysis instructions
  - `investigation`: dispatch with investigation instructions
  - `reasoning`: dispatch with reasoning instructions
  - `work`: dispatch for execution (existing behavior, enhanced)
- Readiness gate: tasks with readiness < 99 are NOT dispatched for
  work. They can be dispatched for earlier-stage protocols.
- Stage-appropriate context: heartbeat context includes different
  rules and instructions based on the current stage
- Implementation: modify `fleet/cli/orchestrator.py` dispatch logic,
  modify `fleet/core/heartbeat_context.py` to include stage-aware
  instructions

---

**B09: Standards and examples library**

The methodology system enforces high standards for everything agents
produce. Standards define what "complete" and "correct" looks like for
every artifact type, with examples.

- Define standards for each artifact type:
  - Full task (all required fields, verbatim requirement, acceptance
    criteria, assignment, priority, story points)
  - Full bug report (steps to reproduce, expected/actual, evidence,
    impact)
  - Full analysis document (scope, current state with file/line refs,
    findings, implications)
  - Full investigation document (scope, sources, findings, options,
    recommendations)
  - Full plan/reasoning document (requirement quoted, approach,
    target files, steps, criteria mapping)
  - Full PR (title, description, changes, testing, task reference)
  - Full completion claim (PR URL, summary, criteria check, evidence)
- Provide positive examples (what "done right" looks like) and negative
  examples (what gets flagged)
- Standards stored in accessible format — config/standards/ or
  fleet/core/standards/
- Standards accessible to agents when needed (via heartbeat context
  or on-demand loading)
- Standards evolve: PO adds new standards, refines existing, as fleet
  matures
- Methodology checks reference standards: "does this output meet the
  standard for its type?"
- Teaching system uses standards in lessons: "here's the standard,
  here's what you produced, here's the gap, practice producing to
  standard"
- Implementation: `fleet/core/standards.py` (NEW)
  - Standard definitions per artifact type
  - `get_standard(artifact_type) → Standard`
  - `check_standard(artifact, standard) → ComplianceResult`

---

### C. Teaching System (C01-C06)

The teaching system delivers adapted lessons and verifies comprehension
through practice.

**C01: Lesson store**

Where rules and lessons live. Not in agent context at start — agents
work light. Rules exist as references, pre-embedded, available but not
loaded until needed.

- Directory: `config/lessons/` or `fleet/core/lessons/`
- Organized by disease category:
  - `deviation/` — scope rules, verbatim requirement adherence
  - `laziness/` — thoroughness rules, completion criteria
  - `abstraction/` — process exact words, no interpretation
  - `reading/` — read before write, grep before analysis
  - `protocol/` — methodology stage compliance
- Format: markdown files with structured content
  - Each lesson has: the rule, why it exists, practice exercise,
    verification criteria
  - Smart format that forces practice — not "acknowledge this rule"
    but "apply this rule to your current task and show me"
- Content sources:
  - devops-control-plane 24 rules (translated to fleet context)
  - Fleet-specific lessons (from this session's evidence)
  - Disease catalogue patterns
  - New lessons as diseases are discovered
- Implementation: `fleet/core/lesson_store.py` (NEW)
  - `get_lesson(disease_category, agent, task) → Lesson`
  - `list_lessons(category) → list[Lesson]`
  - Lesson dataclass: content, practice_exercise, verification_criteria

**C02: Injection mechanism**

How lessons get forced into the agent's context. The PO described this
precisely: "forcing into the AI context text/token and forcing him to
autocomplete from it before continuing the autocomplete from the
original work."

Two injection paths (from gateway investigation):

Path 1 — In-session injection via `chat.send`:
- Send lesson content as a message into the active session
- Agent's next response must autocomplete from the lesson
- Immediate, within the current conversation
- Used for mid-task lessons: agent is working, doctor detects disease,
  lesson is injected, agent must process before continuing

Path 2 — Persistent injection via `context/` files:
- Write lesson content to agent's `context/` directory
- Next execution picks it up in system prompt (rebuilt fresh each time)
- Persistent — stays until removed
- Used for ongoing lessons: agent needs this rule reinforced across
  multiple executions

Both paths may be used together. Acute lesson via chat.send for
immediate processing, then persistent reminder via context/ file.

- Implementation: `fleet/core/teaching.py` (NEW)
  - `inject_lesson(agent, lesson, path="session"|"persistent")`
  - Uses gateway RPC: `chat.send` for session path
  - Uses filesystem: write to agent's `context/` for persistent path
  - Coordinates with doctor: doctor triggers, teaching delivers

**C03: Comprehension verification**

Agents must PROVE they processed the lesson. Not "I understand." The
PO said: "they need to do the lessons and prove it and if not they
continue doing the lesson till there is no change and they get pruned."

Seeing the pattern does not break the pattern. Forging the right path
multiple times does.

- Verification mechanism:
  - After lesson injection, agent receives a practice exercise
  - Practice exercise is specific to the disease and the current task
  - Example: "Re-read the verbatim requirement for task #42. Now
    produce a plan that addresses each specific term in the requirement.
    Show me how your plan maps to the words."
  - Agent produces response. Teaching system evaluates.
  - If response demonstrates comprehension → agent returns to work
  - If response does NOT demonstrate comprehension → lesson continues
  - If repeated attempts show no change → report to immune system → prune
- "No change" threshold: TBD — possibly 3 attempts (matching the
  devops-control-plane three-strike rule)
- Implementation: `fleet/core/teaching.py`
  - `verify_comprehension(agent, lesson, response) → bool`
  - `practice_exercise(lesson, task) → str` — generates the exercise
  - Track attempts per lesson per agent

**C04: Adapted lesson generation**

Lessons must be adapted to the specific disease, task, and agent. Not
generic. The agent drifted from a specific requirement on a specific
task — the lesson addresses that specific drift.

- Adaptation dimensions:
  - Disease: which disease was detected? Scope the lesson to that disease.
  - Task: what's the verbatim requirement? Use it in the practice exercise.
  - Agent: has this agent shown this disease before? If repeated, the
    lesson may be more intensive.
- Template-based with parameters:
  - Lesson templates in the lesson store have placeholders
  - `{verbatim_requirement}`, `{agent_name}`, `{task_title}`,
    `{what_went_wrong}`, `{what_should_have_happened}`
  - Teaching system fills placeholders from the current context
- Example adapted lesson:
  - Template: "The verbatim requirement says: '{verbatim_requirement}'.
    Your plan said: '{agent_plan}'. These don't match because
    {what_went_wrong}. Re-read the requirement. Produce a new plan
    that addresses each word. Show the mapping."
  - Filled: "The verbatim requirement says: 'Add three Select dropdowns
    to the DashboardShell header bar'. Your plan said: 'Create a new
    /fleet-control page in the sidebar'. These don't match because you
    changed the location from header to sidebar. Re-read the requirement.
    Produce a new plan that addresses each word. Show the mapping."
- Implementation: `fleet/core/teaching.py`
  - `adapt_lesson(template, disease, task, agent) → Lesson`

**C05: Lesson tracking**

Track everything about teaching. Feed data back to immune system for
agent health profiling.

- Per agent:
  - Which lessons received, when, for what disease
  - Comprehension verified or not
  - Number of attempts per lesson
  - Outcomes: returned to work successfully, or pruned
- Per disease:
  - Which agents get this lesson most often
  - Effectiveness: does the lesson reduce recurrence?
- Per task:
  - Which lessons were triggered during this task
  - Impact on task completion
- Storage: event store (JSONL) — teaching events alongside other events
- Event types:
  - `fleet.teaching.lesson_started`
  - `fleet.teaching.practice_attempted`
  - `fleet.teaching.comprehension_verified`
  - `fleet.teaching.comprehension_failed`
  - `fleet.teaching.escalated_to_prune`
- Feed to immune system: agent health profile includes teaching history.
  Agent that frequently needs lessons for the same disease → higher
  vigilance by doctor.

**C06: Teaching system integration**

Wire the teaching system to the immune system, methodology system, and
gateway.

- Immune system interface:
  - Doctor calls `teaching.deliver_lesson(agent, disease, task)`
  - Teaching system delivers, verifies, reports outcome
  - If outcome is "no change" → doctor decides to prune
- Methodology system interface:
  - Teaching system can teach protocol compliance
  - Lessons reference the correct protocol for the current stage
  - Agent learns what it should be doing in this stage
- Gateway interface:
  - Lesson injection via `chat.send` (in-session)
  - Lesson injection via `context/` files (persistent)
  - Session information for targeting the right agent session
- Implementation: integration points in `fleet/core/teaching.py`,
  called by doctor in `fleet/core/doctor.py`

---

### D. Immune System (D01-D10)

The immune system observes, reports, and acts. Depends on methodology
being defined (to detect violations) and teaching system existing
(to deliver lessons when triggered).

**D01: Doctor daemon architecture**

The doctor is the active component. It observes, reports, and acts.
It is hidden from agents. Where it runs and how it accesses information
shapes everything else in the immune system.

- Architectural decision: part of orchestrator cycle vs separate daemon
  - Orchestrator already runs every 30s — doctor checks could run
    as a step in the orchestrator cycle (like the existing approval
    and dispatch steps)
  - Separate daemon: independent timing, doesn't slow orchestrator
  - Or both: lightweight checks in orchestrator cycle, heavy checks
    in separate daemon
- Data access:
  - Agent state: via MC API (task assignments, status, custom fields)
  - Agent work: via git (diffs, commits, branches)
  - Agent behavior: via event store (MCP tool calls, events emitted)
  - Plane state: via Plane API or sync worker data
  - Task specs: via MC API (custom fields including verbatim requirement)
- Hiddenness:
  - Doctor doesn't inject itself into agent context
  - Doctor doesn't appear as an agent on the board
  - Agent experiences consequences (prune, compact, lesson) but doesn't
    see the detection mechanism
  - Doctor's detection patterns are not in agent-accessible files
- Implementation: `fleet/core/doctor.py` (NEW)
  - `run_doctor_cycle(mc, board_id, config)` — main loop
  - Called from orchestrator or separate daemon
  - Reads all active tasks and agent states
  - Runs detection patterns
  - Triggers responses

**D02: Detection — laziness**

Identify agents doing partial work, taking shortcuts, skipping hard parts.

- Signals:
  - Acceptance criteria: task has N criteria, agent addressed < N
  - Call site coverage: task says "update all callers", grep shows 7,
    diff shows 3 updated
  - Missing artifacts: task type requires tests, no test files in diff
  - Speed anomaly: 5-story-point task completed in 2 minutes
  - Correction pattern: agent's work consistently comes back with
    reviewer requesting more
  - Methodology checks failed: stage-specific checks not met
- Data sources:
  - Task custom fields (acceptance criteria, story points)
  - Git diff (files changed, scope of changes)
  - Event store (tool calls, timing)
  - Plane metadata (estimates, start dates)
  - Review history (correction frequency)
- Implementation: `fleet/core/doctor.py`
  - `detect_laziness(task, agent, work) → Detection | None`

**D03: Detection — deviation**

Identify agents drifting from the spec. Spectrum from minor to severe.

- Signals:
  - Plan mismatch: agent's plan uses different terms than verbatim
    requirement
  - File scope: agent touched files not related to the task
  - Scope addition: agent added features/changes not in requirement
  - Term absence: key terms from verbatim requirement not addressed
    in agent's output
- Detection at multiple stages:
  - Plan stage: cheapest — compare plan text against requirement
  - Code stage: compare diff against requirement and plan
  - Completion stage: compare deliverables against acceptance criteria
- Implementation: `fleet/core/doctor.py`
  - `detect_deviation(task, agent, plan_or_work) → Detection | None`

**D04: Detection — confident-but-wrong (Z when A)**

The most dangerous. Agent confidently builds the wrong thing.

- Signals:
  - Plan describes fundamentally different approach than requirement
  - Agent creates artifacts the requirement didn't ask for
  - Agent is productive (many commits, fast progress) but output
    doesn't match requirement
  - Agent doesn't flag uncertainty despite ambiguous requirement
- Early detection is critical:
  - At plan submission (fleet_task_accept): compare plan against
    verbatim requirement. If plan says Z and requirement says A,
    stop before any code is written.
  - At first commit: compare diff direction against requirement
- This detection DEPENDS on requirement_verbatim being populated.
  Without the original words, Z-when-A is undetectable.
- Implementation: `fleet/core/doctor.py`
  - `detect_z_when_a(task, agent, plan) → Detection | None`

**D05: Detection — stuck/spinning**

Agent going in circles without progress.

- Signals:
  - No commits for extended period despite active session
  - No MCP tool calls for extended period
  - High token usage with no artifacts produced
  - Start date (from Plane) vs current time with no state change
  - Agent re-reading same files repeatedly (if observable)
- This disease doesn't need a lesson — agent isn't misbehaving,
  it's struggling. Force compact is the right response.
- Implementation: `fleet/core/doctor.py`
  - `detect_stuck(task, agent, timing) → Detection | None`

**D06: Detection — context contamination**

Old context warping new work. Agent brings concepts from previous tasks
or earlier conversation into current work.

- Signals:
  - Agent references systems/topics not mentioned in current task
  - Agent's output includes terminology from previous tasks
  - Agent applies patterns from a different project to current project
- Hardest to detect deterministically — may need heuristic matching
  of agent output against task scope
- This session's example: agent injected LocalAI/AICP concepts into
  the immune system design. Those topics were from earlier work,
  not from the PO's requirements.
- Implementation: `fleet/core/doctor.py`
  - `detect_contamination(task, agent, output) → Detection | None`

**D07: Detection — protocol violation**

Agent not following the methodology for its current stage.

- Signals:
  - Agent in conversation stage but producing code (detected via
    fleet_commit calls or git commits)
  - Agent in analysis stage but submitting PRs
  - Agent skipping required stages (task_stage jumps from conversation
    to work without investigation/reasoning)
  - Agent claiming done (fleet_task_complete) but methodology checks
    haven't passed
  - Agent modifying task_stage without PO confirmation
- Data source: event store (MCP tool calls), custom field changes,
  methodology system checks
- Integration: methodology system provides the rules, immune system
  detects violations
- Implementation: `fleet/core/doctor.py`
  - `detect_protocol_violation(task, agent, events) → Detection | None`

**D08: Response — prune**

Kill the sick agent session. It grows back fresh.

- Mechanism: call gateway API `sessions.delete(session_key)`
- Before pruning:
  - Save any committed work (it's in git, survives pruning)
  - Record what was happening (task, disease detected, response chain)
  - Emit event: `fleet.immune.agent_pruned`
- After pruning:
  - Fresh session created on next heartbeat via `sessions.patch`
  - Task either re-dispatched to same agent (fresh context) or
    reassigned to different agent
  - Verbatim requirement preserved — new session gets the original words
- Event: `fleet.immune.agent_pruned` with disease info, task info,
  agent info. Visible in event stream. IRC notification. ntfy to PO
  if configured.
- Implementation: `fleet/core/doctor.py`
  - `prune_agent(agent, reason, task)`

**D09: Response — force compact**

Reduce agent context. Agent continues with lean context.

- Mechanism: call gateway API `sessions.compact(session_key)`
  (need to verify what this does — may need additional logic)
- What to preserve:
  - Verbatim requirement (ALWAYS — the first cure)
  - Work done so far (committed code, artifacts)
  - Current task assignment and stage
  - Any lesson from rules reinjection if chained
- What to strip:
  - What is unwanted, unnecessary, or superfluous
  - Dead-end reasoning, failed attempts, old context
  - Intermediate thinking that led nowhere
- Triggers:
  - Doctor detects stuck/spinning
  - After correction (contaminated context)
  - Agent working too long without compaction
  - Chained after rules reinjection (clean up after lesson)
- Event: `fleet.immune.context_compacted`
- Implementation: `fleet/core/doctor.py`
  - `force_compact(agent, reason, preserve)`

**D10: Response — trigger teaching**

When the doctor detects disease that can be cured with a lesson, it
triggers the teaching system.

- Mechanism:
  - Doctor detects disease (D02-D07)
  - Doctor decides: lesson or prune? (severity-based)
  - If lesson: call teaching system with disease info, task, agent
  - Teaching system delivers adapted lesson (C02-C04)
  - Teaching system verifies comprehension (C03)
  - Teaching system reports outcome to doctor
  - If comprehension verified → agent returns to work
  - If no change after attempts → doctor prunes (D08)
- This is the chain: detect → teach → verify → continue or prune
- Event: `fleet.immune.teaching_triggered`
- Implementation: `fleet/core/doctor.py`
  - `trigger_teaching(agent, disease, task)`
  - Calls `fleet/core/teaching.py` interface

---

### E. Cross-Cutting Platform Evolution (E01-E06)

Changes to existing fleet systems that all three systems depend on.

**E01: Orchestrator evolution — immune system integration**

The orchestrator is the fleet's brain. It needs to run doctor checks
and respect immune system decisions.

- Add doctor cycle step to orchestrator:
  - Existing steps: approve, transition, dispatch, evaluate parents, wake drivers
  - New step: doctor checks (between dispatch and evaluate, or as first step)
- Orchestrator respects immune system state:
  - Don't dispatch to agent currently being pruned
  - Don't dispatch to agent currently in a lesson
  - Don't dispatch work-stage tasks if readiness < 99
  - Don't dispatch tasks to agents the doctor flagged as sick
- Doctor results feed into dispatch decisions
- Implementation: modify `fleet/cli/orchestrator.py`
  - Import and call `fleet/core/doctor.py` functions
  - Add doctor cycle step

**E02: Gateway integration — use existing session APIs**

The gateway already has the APIs. We need fleet wrapper functions.

- Gateway APIs available:
  - `sessions.delete(key)` → prune
  - `sessions.compact(key)` → force compact
  - `sessions.reset(key)` → reset
  - `chat.send(sessionKey, message)` → rules injection
  - `sessions.patch(key, label)` → create fresh session (regrowth)
- Investigation needed:
  - What does `sessions.compact` actually do? Test it.
  - Can `chat.send` inject lesson content mid-session while agent is
    working? Or only between executions?
  - What happens to in-flight work when session is deleted?
- Implementation: `fleet/infra/gateway_client.py` (NEW or extend existing)
  - `prune_session(agent) → bool`
  - `compact_session(agent) → bool`
  - `inject_content(agent, content) → bool`
  - `create_fresh_session(agent) → Session`
- Wrapper functions called by doctor and teaching system

**E03: Event bus — new event types**

All three systems emit events for observability.

- Immune system events:
  - `fleet.immune.disease_detected` (disease type, agent, task, severity)
  - `fleet.immune.agent_pruned` (agent, reason, task)
  - `fleet.immune.context_compacted` (agent, reason)
  - `fleet.immune.teaching_triggered` (agent, disease, task)
- Teaching system events:
  - `fleet.teaching.lesson_started` (agent, lesson, disease)
  - `fleet.teaching.practice_attempted` (agent, attempt number)
  - `fleet.teaching.comprehension_verified` (agent, lesson)
  - `fleet.teaching.comprehension_failed` (agent, lesson)
  - `fleet.teaching.escalated_to_prune` (agent, lesson, attempts)
- Methodology system events:
  - `fleet.methodology.stage_changed` (task, from, to, authorized_by)
  - `fleet.methodology.protocol_violation` (task, agent, violation)
  - `fleet.methodology.readiness_changed` (task, old, new, changed_by)
  - `fleet.methodology.check_passed` (task, stage, check)
  - `fleet.methodology.check_failed` (task, stage, check)
- Implementation: extend `fleet/core/events.py` with new event types
  - Add to event type definitions
  - Chain runner handles routing to surfaces (IRC, board memory, ntfy, Plane)

**E04: Heartbeat context evolution**

Agent heartbeat bundles must include the new systems' data.

- Include in every heartbeat:
  - `task_stage` — current methodology stage
  - `task_readiness` — current readiness percentage
  - `requirement_verbatim` — ALWAYS present, NEVER compacted, the anchor
  - Stage-appropriate instructions (what this agent should be doing
    in this stage, per the protocol)
- For rules reinjection:
  - Heartbeat can include lesson content when the teaching system
    is active for this agent
  - Lesson content in heartbeat forces agent to process it on next
    execution
- Implementation: modify `fleet/core/heartbeat_context.py`
  - Add new fields to context bundle
  - Stage-aware instruction selection
  - Lesson injection support

**E05: Sync worker evolution**

The sync worker must handle the new custom fields and Plane state.

- New custom field sync:
  - task_readiness (integer) — bidirectional
  - requirement_verbatim (text_long) — Plane → OCMC primarily
  - task_stage (text) — bidirectional
- Plane state metadata sync:
  - State → OCMC status mapping
  - Assignees → agent_name
  - Start date, due date, priority, estimates
- Sync timing:
  - Current: 120s polling interval
  - Critical fields (readiness, stage) may need faster sync
  - Consider event-driven sync for critical changes
- Implementation: extend `fleet/core/plane_sync.py`
  - Add new field mappings
  - Add state metadata sync
  - Add conflict resolution per A08

**E06: MCP tools evolution**

MCP tools must be methodology-aware and observable by the immune system.

- Stage awareness:
  - `fleet_commit`: blocked during conversation/analysis/investigation
    stages. Only available during work stage.
  - `fleet_task_complete`: blocked unless methodology checks pass for
    the work stage.
  - `fleet_task_accept`: becomes the plan submission point. Plan
    validated against verbatim requirement before acceptance.
  - `fleet_task_create`: available during reasoning stage for task
    breakdown.
- Immune system observability:
  - All MCP tool calls logged to event store (already partially done)
  - Doctor reads tool call patterns for detection:
    - Agent calling fleet_commit without fleet_read_context → code
      without reading
    - Agent calling fleet_task_complete without fleet_commit → lazy
    - Agent calling fleet_commit during conversation stage → protocol
      violation
- Implementation: modify `fleet/mcp/tools.py`
  - Add stage checks before tool execution
  - Ensure all tool calls emit events for doctor observation

---

## Dependency Order

These systems are prerequisites FOR autonomous fleet operation — not
things added after. Running agents without the immune system, teaching
system, and methodology is running agents without protection. They'll
get sick immediately with no way to detect or cure it.

```
A01-A08 (Foundation: custom fields + Plane sync)
  ↓
B01-B08 (Methodology: stages, protocols, checks)
  ↓
C01-C06 (Teaching: lessons, practice, verification)
  ↓
D01-D10 (Immune: doctor, detection, response)
  ↓
E01-E06 (Platform: orchestrator, gateway, events, heartbeat, sync, MCP)
```

The foundation (A) must come first — everything reads custom fields.
The methodology (B) must be designed before detection (D) can know what
to detect. The teaching system (C) must exist before the immune system
can trigger lessons (D10). Platform evolution (E) spans all categories.

In practice, some milestones from different categories can be worked
in parallel. But the logical dependency holds — you can't detect
methodology violations before methodology exists.

---

## Total: 44 Milestones

| Category | Count | Milestones |
|----------|-------|-----------|
| A. Foundation | 8 | Custom fields, Plane sync, conflict resolution |
| B. Methodology | 9 | Stages, protocols, observability, standards |
| C. Teaching | 6 | Lessons, injection, practice, tracking |
| D. Immune | 10 | Doctor, detection, response |
| E. Platform | 6 | Orchestrator, gateway, events, heartbeat, sync, MCP |
| G. OCMC UI | 5 | Immune/teaching/methodology visibility, dashboard, events |
| **Total** | **44** | |

The control surface milestones (fleet-control-surface.md) and fleet
autonomy milestones (existing plan) are separate and tracked in their
own documents.

---

### G. OCMC Vendor UI Integration (G01-G05+)

After the three systems are built, we inject into the OCMC vendor
frontend (Next.js) to surface everything in the UI. Not just the fleet
control dropdowns in the header — the immune system, teaching system,
and methodology system all need their activities and reporting visible
in the OCMC UI.

This goes beyond the control surface (fleet mode dropdowns). This is
the full reporting and visibility layer:

**G01: Immune system activity in OCMC UI**

The PO needs to see what the doctor is doing. Prunes, compactions,
lessons — all visible in the OCMC interface.

- New component(s) injected into MC vendor frontend
- Shows:
  - Recent doctor actions: what happened, to which agent, why
  - Active interventions: which agents are currently being pruned,
    compacted, or in a lesson
  - Agent health indicators: healthy, sick, in-lesson, recently-pruned
  - History per agent: intervention timeline
- Data source: event bus events (fleet.immune.* event types from E03)
- Real-time via SSE streams (same pattern as task/agent/memory streams)
- Location in UI: TBD — could be a section on the board page, a panel
  accessible from the header, or a dedicated view. Needs discussion
  with PO.
- Implementation: new React component(s) in vendor frontend, consuming
  immune system events via SSE

**G02: Teaching system activity in OCMC UI**

The PO needs to see lessons in progress and their outcomes.

- Shows:
  - Active lessons: which agent, which disease, which lesson
  - Practice attempts: how many attempts, what the agent produced
  - Comprehension status: verified / failed / in progress
  - Lesson history: which agents got which lessons, outcomes
  - Teaching effectiveness: lessons that cured vs led to prune
- Data source: event bus events (fleet.teaching.* event types)
- Real-time via SSE
- Location in UI: alongside or integrated with immune system activity
- Implementation: new React component(s) consuming teaching events

**G03: Methodology system in OCMC UI**

The PO needs to see stages, protocol compliance, and readiness.

- Task stage already visible via custom field on task cards
- Additional visibility:
  - Protocol compliance per agent: is the agent respecting the protocol
    for its current stage?
  - Stage progression history per task: when it entered each stage,
    who authorized transitions, how long each stage took
  - Readiness percentage visible and EDITABLE by PO directly in UI
    (PO can click the readiness field and set a new value)
  - Methodology check results: which checks passed/failed per stage
- Data source: custom fields + event bus events (fleet.methodology.*)
- Readiness editing: uses existing MC custom field editing UI — integer
  field is already editable on task cards
- Stage history: from methodology events in event store
- Implementation: enhancements to existing task card display + new
  components for stage history and compliance

**G04: Reporting dashboard**

Fleet health at a glance. The PO opens OCMC and immediately sees the
state of the fleet — not just tasks and agents, but health, teaching,
and methodology compliance.

- Fleet health overview:
  - Agents: N healthy / N sick / N in-lesson / N recently-pruned
  - Disease frequency: how often each disease is detected, trending
  - Teaching load: how many lessons active, completion rate
  - Methodology compliance: percentage of agents following protocol
- Time-based trends (using Recharts, already in MC frontend):
  - Disease detection over time (are things getting better or worse?)
  - Teaching effectiveness over time
  - Readiness progression across tasks
  - Prune frequency over time
- Location: could be part of the existing dashboard page (localhost:3000
  /dashboard) or a new section. The existing dashboard already shows
  task KPIs, approval summary, agent status. Fleet health would extend
  this.
- Data source: aggregated from event store + custom fields
- Implementation: new dashboard section or components, using existing
  Recharts + React Query patterns from the MC dashboard

**G05: Event stream integration**

All three systems' events visible in the existing event stream /
activity feed.

- Immune, teaching, and methodology events appear alongside task,
  agent, and memory events in the activity feed
- Color-coded by system for visual distinction:
  - Immune events: red/orange tones (disease, prune, compact)
  - Teaching events: amber/yellow tones (lesson, practice, verification)
  - Methodology events: blue/indigo tones (stage change, compliance)
  - Existing events keep their current colors
- Filterable: PO can filter the event stream by system
  (show only immune events, only methodology events, etc.)
- Real-time via SSE — same infrastructure as existing event streams
- Location: existing activity feed (localhost:3000/activity) and board
  event stream
- Implementation: extend existing ActivityFeed and FeedCard components
  to handle new event types. Add color mapping. Add filter controls.

---

All G milestones are injected into the MC vendor frontend — same
approach as the FleetControlBar in the header. New components patched
into the existing Next.js app. Uses existing Radix UI + Tailwind
component library, SSE streams for real-time updates, React Query for
data fetching.

This is the most advanced UI work and depends on the backend systems
(immune, teaching, methodology) being built and producing events and
data. G milestones come last in the dependency chain.

---

## Plane Project Management Structure

The 44 milestones go into Plane as the project management surface. Each
milestone becomes an Epic. PM breaks epics into stories and tasks.

**Project:** Fleet (OF — OpenClaw Fleet)

**Modules (one per system/category):**

| Module | Milestones | Description |
|--------|-----------|-------------|
| Foundation | A01-A08 | Custom fields on OCMC + Plane, sync evolution |
| Methodology System | B01-B09 | Stages, protocols, observability, standards |
| Teaching System | C01-C06 | Lessons, injection, practice, tracking |
| Immune System | D01-D10 | Doctor, detection, response |
| Platform Evolution | E01-E06 | Orchestrator, gateway, events, heartbeat, sync, MCP |
| OCMC UI Integration | G01-G05 | UI for immune/teaching/methodology visibility |

**Issue types:**
- Each milestone = 1 Epic
- PM breaks each epic into Stories (user-facing chunks)
- Stories break into Tasks (implementation units)
- Bugs, spikes, and blockers as needed

**Cycles:**
- Module-level cycles in Plane for tracking progress per system
- Cross-module cycle for the overall three-systems program

**Labels:**
- `immune-system`, `teaching-system`, `methodology`, `foundation`,
  `platform`, `ocmc-ui` — per system
- `standards`, `detection`, `response`, `protocol` — per concern
- Priority labels as needed

**Module-level methodology:**
Each module itself has a stage. The Immune System module starts in
investigation/reasoning (we've done conversation and research). The
Foundation module can start in reasoning/work (the custom fields are
well-understood). The methodology stages on modules track the overall
phase of each body of work.

---

## Next Step: Seed to Plane

The milestones can be seeded to Plane via the existing IaC scripts. A
config YAML (like `config/fleet-board.yaml` in the DSPD repo) defines
the modules, epics, and structure. The `plane-seed-mission.sh` script
creates everything via the Plane REST API.

This would create:
- 6 modules in the Fleet project
- 44 epics (one per milestone) assigned to the right modules
- Module leads assigned from fleet-roles.yaml
- Labels for cross-referencing

The PM agent then breaks each epic into stories and tasks as the
fleet begins work on them — following the methodology system's own
protocols (conversation → analysis → investigation → reasoning → work).

---

## Open Questions

- Priority within categories — which milestones should be done first
  within each category?
- Parallelism — which milestones from different categories can be done
  simultaneously?
- Effort estimates per milestone — the PO said 2000+ hours total, how
  does that distribute?
- Who works on what? Which agents are capable of which milestones?
- Testing strategy — how do we verify each milestone works?
- Rollout strategy — do all three systems deploy together or
  incrementally?
- Should the Plane seed config go in the DSPD repo (alongside other
  board configs) or in the Fleet repo?