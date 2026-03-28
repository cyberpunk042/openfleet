# Fleet Autonomy Milestones — Full Analysis and Roadmap

## What This Document Is

This is the comprehensive analysis and milestone plan for making the OpenClaw Fleet
a fully autonomous, self-organizing, high-quality development operation. It captures
EVERY issue discovered during the 2026-03-28 session, EVERY requirement the user stated,
and EVERY milestone needed — including the ones from existing design docs that haven't
been started, plus new milestones from what we learned today.

**This is not a summary. This is the full picture.**

---

## Part 1: What We Learned Today — The Full Systemic Analysis

### 1.1 The Fleet Doesn't Do Its Job

The fleet has 10 agents with well-defined roles. When we dispatched DSPD Sprint 1 and
observed the flow, here's what happened:

- **S1-1 completed** by devops → moved to review → PR created → then NOTHING happened
- No agent reviewed the work
- No agent approved the completion
- No agent dispatched the next task
- No agent checked test quality
- The PM posted a sprint plan as TEXT to board memory instead of creating actual tasks
- fleet-ops was offline and nobody restarted it
- 6 tasks accumulated in review with nobody processing them

**Root cause:** Agents are not alive. They only wake on explicit dispatch via `fleet dispatch`.
They don't react to events, don't monitor board state, don't fulfill their ongoing roles.

### 1.2 The Orchestrator Was Built Wrong

We built an orchestrator daemon that auto-approves based on confidence score (>= 80%).
This is **brainless rubber-stamping**. The problems:

1. **No reasoning** — auto-approve just checks a number, doesn't evaluate the actual work
2. **No test validation** — approves code tasks without verifying tests pass
3. **No agent involvement** — bypasses fleet-ops and QA entirely
4. **No quality check** — doesn't verify conventional commits, PR body structure, cross-references
5. **Agents wrote failing tests** — software-engineer committed async tests without pytest-asyncio,
   and the orchestrator approved and moved them to done anyway
6. **PRs not reviewed** — auto-merge without any agent actually reading the diff

> **The user's exact concern:** "WTF THAT YOU ARE AUTO MERGING PR WITHOUT REASONING ???
> WHERE IS THE AGENTS ROLES ?????"

**What approval SHOULD look like:**
- Agent completes task → creates approval with confidence and rubric
- fleet-ops receives notification → reads the task, checks quality
- If code task: qa-engineer runs tests, architect reviews design
- If tests pass AND quality check passes → fleet-ops approves with reasoning
- If tests fail → fleet-ops rejects with specific feedback, creates fix task
- THEN the task can transition to done
- THEN the sync daemon can merge the PR

The orchestrator should **route approvals to reviewing agents**, not rubber-stamp them.

### 1.3 Agents Produce Broken Code That Nobody Catches

The software-engineer agent completed 3 DSPD tasks (S1-5, S1-6, S1-7) and committed
code directly to main. That code includes:

- `fleet/infra/plane_client.py` — PlaneClient REST wrapper
- `fleet/core/plane_sync.py` — Plane ↔ OCMC bidirectional sync
- `fleet/cli/plane.py` — CLI commands
- Tests for all of the above

**43 tests are failing.** The agent used `@pytest.mark.asyncio` but `pytest-asyncio`
is not in the project dependencies. Nobody caught this because:

1. The agent didn't run tests before completing
2. qa-engineer was never triggered to test
3. fleet-ops didn't spot-check quality
4. The orchestrator auto-approved without validation
5. No CI pipeline exists to catch this

### 1.4 Missing Claude Code Feature Exploitation

The user raised a critical question: are we even using Claude Code's capabilities properly?

**Features to evaluate:**

| Feature | What It Does | Are Agents Using It? | Should They? |
|---------|-------------|---------------------|-------------|
| **Extended thinking** | Deep reasoning before acting | Unknown — needs investigation | Yes, for architecture, security, complex tasks |
| **Compact execution** | Efficient execution of well-understood tasks | Unknown | Yes, for routine tasks (docs, simple fixes) |
| **Dream mode** | Creative exploration, brainstorming | Unknown | Yes, for PM roadmap planning, architect design |
| **Effort index** | Controls how much effort the model puts in | Unknown — needs investigation | Yes, high effort for complex, low for routine |
| **Memory** | Persistent memory across sessions | MEMORY.md exists but unclear if agents use it | Yes, critical for context across heartbeats |
| **MCP tools** | Native tool calls | Partially — env vars broken, agents sometimes use exec | Must be 100% MCP tools |
| **Slash commands** | Custom commands via .claude/commands/ | Not used | Could be powerful for agent workflows |

**This is a whole milestone of investigation and optimization.** We need to:
1. Research each Claude Code feature and what it offers
2. Test how agents currently use (or don't use) these features
3. Design optimal feature exploitation per agent role
4. Update SOUL.md / CLAUDE.md / agent configs to leverage features
5. Measure improvement

### 1.5 Communication Between Agents Is Dead

Board memory exists. IRC exists. But agents don't communicate meaningfully:

- Agents don't read each other's board memory posts before starting work
- Agents don't create follow-up tasks for other agents
- Agents don't flag concerns about each other's work
- No agent has ever posted a decision for team discussion
- No agent has ever posted a suggestion or improvement idea
- Board memory is a write-only graveyard

**What communication should look like:**
- Architect designs → posts decision to board memory → PM reads it → creates subtasks
- Software-engineer finds a security concern → creates task for Cyberpunk-Zero
- QA finds test failure → creates blocker task for software-engineer
- PM evaluates sprint → posts velocity report → fleet-ops tracks trends
- Cyberpunk-Zero finds CVE → alerts all via fleet_alert → PM reprioritizes sprint
- Any agent discovers missing docs → creates task for technical-writer

### 1.6 Agent Identity and Personal Planning

> "We need to make every member a strong independent person and yet so synergic
> and responsive for the others too and humble and adaptative"

Each agent needs:
1. **Personal planning capability** — break down their own work, set their own approach
2. **Situational awareness** — read board state, understand what others are doing
3. **Initiative** — create tasks when they discover work, don't wait to be told
4. **Quality ownership** — run tests on their own output, verify before completing
5. **Collaboration instinct** — read board memory, build on others' work, flag concerns
6. **Humility** — hand off work outside their expertise, ask for help, pause when stuck
7. **Persistence** — use MEMORY.md to maintain context across sessions

### 1.7 The Sync Daemon Auto-Merges Without Review

The sync daemon (`fleet/cli/sync.py`) has this logic:
```
if task.status == "done" and pr_state == "OPEN" → MERGE PR
```

This means once a task is "done" (which the orchestrator now does automatically),
the sync daemon merges the PR without any review. No agent looks at the diff.
No tests are run against the branch. No human gets a chance to review.

**This is dangerous.** PRs should be merged only after:
1. At least one reviewing agent has looked at the code
2. Tests pass (CI or agent-run)
3. The PR body meets quality standards (changelog, references, diff table)
4. For high-risk changes: human approval

---

## Part 2: Platform Capabilities We're Not Using (OCMC + OpenClaw Gateway)

This is the result of deep investigation into the MC vendor code and gateway protocol.
The platform already provides most of what we need for a proper review chain, event-driven
triggers, and continuous operation. We built workarounds for things that already exist.

### 2.1 OCMC Board Lead System — The Review Chain Already Exists

OCMC has a **board lead** concept that we're completely ignoring:

```
Board Lead (is_board_lead: true):
  - ONE agent per board designated as lead
  - When any task moves to "review" → MC AUTO-ASSIGNS it to the lead
  - Lead can: review → done (approve) or review → inbox (request changes)
  - When lead sends back to inbox → MC notifies the ORIGINAL worker with "Changes requested"
  - Lead MUST provide reasoning when approving (lead_reasoning field required)
  - Lead can only modify tasks that are in "review" status
  - Lead cannot self-assign tasks (prevents conflict of interest)
```

**This is fleet-ops.** fleet-ops should be the board lead. When any agent completes
a task and moves to review, MC automatically assigns it to fleet-ops for review.
fleet-ops evaluates, and either approves (→ done) or requests changes (→ inbox, back
to the original agent with feedback).

**We are currently bypassing this entire system** with the brainless auto-approve orchestrator.

### 2.2 Board Configuration Gates — Built-In Quality Enforcement

OCMC has 5 boolean flags we can configure on the board:

| Flag | Current | Should Be | What It Does |
|------|---------|-----------|-------------|
| `require_approval_for_done` | **true** | true | Task can't move to done without approved approval |
| `require_review_before_done` | **false** | **true** | Task MUST go through review before done (no skip) |
| `comment_required_for_review` | **false** | **true** | Agent MUST post a comment to move task to review |
| `block_status_changes_with_pending_approval` | **false** | **true** | Can't change status while approval pending |
| `only_lead_can_change_status` | **false** | evaluate | Only board lead can change task status |

**Enabling these 3 flags (`require_review_before_done`, `comment_required_for_review`,
`block_status_changes_with_pending_approval`) would enforce the review chain at the
platform level — not in our code.** MC would reject status changes that violate the flow.

### 2.3 The Full Review Chain (Using What MC Already Provides)

Here is how the task lifecycle SHOULD work, using OCMC's native capabilities:

```
1. AGENT WORKS
   - Agent accepts task (inbox → in_progress)
   - MC auto-assigns agent and records in_progress_at
   - Agent does work, commits, pushes

2. AGENT COMPLETES → REVIEW
   - Agent calls fleet_task_complete
   - Task moves to "review" (requires comment — enforced by MC)
   - MC AUTO-ASSIGNS task to board lead (fleet-ops)
   - fleet_task_complete creates approval with confidence + rubric
   - IRC notification goes out
   - fleet-ops is WOKEN by MC (assignee wake on task assign)

3. FLEET-OPS REVIEWS (as board lead)
   - fleet-ops reads the task, checks quality:
     a. Were tests run? Did they pass?
     b. Does the PR body have changelog, references?
     c. Are conventional commits used?
     d. Any security concerns?
   - If code task → fleet-ops creates a review subtask for qa-engineer:
     "Run tests for PR #{N} on branch fleet/{agent}/{task}"
   - qa-engineer runs tests, reports results as comment
   - fleet-ops evaluates qa results

4. FLEET-OPS DECIDES
   Option A: APPROVE (review → done)
     - fleet-ops approves the approval with reasoning
     - MC moves task to done (requires approved approval — enforced)
     - Sync daemon detects done + open PR → merges
     - MC unblocks dependent tasks (native dependency resolution)
     - Orchestrator dispatches newly unblocked tasks

   Option B: REQUEST CHANGES (review → inbox)
     - fleet-ops moves task back to inbox
     - MC auto-notifies original agent: "Changes requested"
     - MC re-assigns to original agent (rework notification)
     - Agent reads feedback, fixes issues, re-submits to review
     - Cycle repeats

   Option C: ESCALATE TO HUMAN
     - fleet-ops posts to IRC #alerts: "Needs human attention"
     - fleet-ops posts to board memory: detailed analysis + question
     - fleet-ops calls fleet_pause on the task with specific question
     - Human responds via:
       a. IRC message (agents monitor)
       b. Edit task description/comment in MC dashboard
       c. Post to board memory with directive
     - fleet-ops reads human response → continues review chain

5. AFTER DONE — CHAIN CONTINUES
   - MC unblocks dependent tasks (is_blocked becomes false)
   - Orchestrator sees unblocked inbox tasks → dispatches to assigned agents
   - Parent task: when all children done → orchestrator moves parent to review
   - New cycle begins for each unlocked task
```

### 2.4 Multiple Reviewers — Gates on Tasks

OCMC only supports single task assignment (`assigned_agent_id`). It doesn't have
native multi-reviewer support. But we can model gates using custom fields + subtasks:

**Gate Model (via custom fields):**

```yaml
# Task custom field: review_gates (json type)
review_gates:
  - agent: qa-engineer
    type: required        # required | optional
    status: pending       # pending | approved | rejected | skipped
    reason: ""
  - agent: fleet-ops
    type: required
    status: pending
    reason: ""
  - agent: architect      # for design tasks
    type: optional
    status: pending
    reason: ""
```

**How this works with the review chain:**

1. Agent completes work → fleet_task_complete populates `review_gates` based on task type:
   - Code tasks: qa-engineer (required) + fleet-ops (required)
   - Architecture tasks: architect (required) + fleet-ops (required)
   - Documentation: fleet-ops (required)
   - Security-related: devsecops-expert (required) + fleet-ops (required)
   - Infrastructure: devsecops-expert (optional) + fleet-ops (required)

2. MC assigns to fleet-ops (board lead) as first reviewer

3. fleet-ops reads review_gates → creates review subtasks for each required reviewer:
   ```
   fleet_task_create(
     title="Review: Run tests for S1-5 — PlaneClient",
     agent_name="qa-engineer",
     parent_task=task_id,
     task_type="subtask",
     depends_on=[]  # can start immediately
   )
   ```

4. Each reviewer completes their review subtask → fleet-ops checks if all required
   gates are approved → if yes, fleet-ops approves the parent task

5. If any required reviewer rejects → fleet-ops sends back to inbox with feedback

**The key insight:** fleet-ops is the **orchestrator of the review chain**, not a
rubber stamp. fleet-ops creates review subtasks, tracks gate completion, and makes
the final decision. Just like a real team lead.

### 2.5 Gateway Capabilities We Should Exploit

The OpenClaw gateway has capabilities we're not using at all:

| Capability | What It Does | How We Should Use It |
|------------|-------------|---------------------|
| **`wake` method** | Actively wake any agent on demand | Orchestrator wakes agents when their tasks are ready |
| **`nudge_board_agent()`** | Agent-to-agent message with deliver=true | PM nudges architect, fleet-ops nudges workers for rework |
| **Gateway cron** | Scheduled tasks on the gateway itself | Heartbeat scheduling, periodic health checks |
| **SSE `/approvals/stream`** | Real-time stream of approval changes | Orchestrator subscribes instead of polling |
| **Webhooks** | Board webhooks with queue + retry + HMAC | MC fires webhooks on task changes → fleet handles |
| **Activity events** | Full audit trail of all mutations | Fleet reads events for change detection instead of polling task list |
| **Agent `agent.wait`** | Hold connection open waiting for agent completion | Orchestrator waits for review completion |
| **Session compact/reset** | Manage session memory | Reset agent sessions that are too long |

### 2.6 The Continuous-Running Engine Design

Instead of a polling daemon that runs every 30 seconds, the fleet should have a
**change-detection engine** that reacts to events:

**Option A: Webhook-based (best)**
```
MC fires webhook on: task.status_changed, task.comment, approval.resolved
  ↓
Fleet webhook receiver (HTTP endpoint)
  ↓
Event router:
  task.status_changed to "review" → Create review subtasks, wake fleet-ops
  task.status_changed to "done" → Check parent completion, unblock deps, dispatch next
  task.status_changed to "inbox" (rework) → Wake original agent with feedback
  approval.resolved "approved" → Transition task review → done
  approval.resolved "rejected" → Move task back to inbox with reason
  task.comment → Check if human directive, route to relevant agent
```

**Option B: SSE stream (good)**
```
Orchestrator subscribes to /approvals/stream and polls /tasks every 30s
  ↓
On approval change → process immediately
On task list change → detect status transitions → react
```

**Option C: Polling + wake (current, minimum viable)**
```
Orchestrator polls every 30s
  ↓
Detects changes → uses gateway wake to trigger agents
  ↓
Agents respond via heartbeat
```

**We should start with Option C (already built) and evolve to Option A.**

### 2.7 Self-Healing: When Things Break, Someone Fixes Them

> "I mean blocking if it was because the test fails for example or something like
> that you just put someone on the idea of fixing it and so on. a real dev team."

When a blocker occurs, the fleet should react like a real team:

| Blocker | Who Detects | Who Fixes | How |
|---------|------------|-----------|-----|
| Tests fail | qa-engineer (during review) | software-engineer (original author) | QA creates fix task assigned to author |
| PR has conflicts | fleet-ops (during sync) | software-engineer | fleet-ops creates resolve-conflicts task |
| Missing dependency | devops (during build) | devops (self) or software-engineer | Agent creates blocker task |
| Security concern | devsecops-expert | software-engineer + devops | Cyberpunk-Zero creates remediation task |
| Architecture issue | architect (during review) | software-engineer | Architect creates rework task with design guidance |
| Agent offline | fleet-ops (heartbeat check) | orchestrator | Orchestrator attempts wake, escalates if fails |
| Human input needed | any agent (fleet_pause) | human | IRC alert + board memory with specific question |
| Unclear requirements | any agent (fleet_pause) | PM + human | PM evaluates, human clarifies |

**The principle:** Every blocker gets turned into a task assigned to someone.
Nothing stays blocked without someone actively working to unblock it.
If an automated fix fails, escalate. If escalation fails, alert human.

---

## Part 3: Existing Milestones Not Started

From the design documents in `docs/milestones/`, these milestones were planned
but have NOT been implemented:

### From design-event-chains.md (M153-M156)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M153 | Event chain model | NOT STARTED | EventChainResult exists as stub in models.py but nothing uses it |
| M154 | Event chain runner | NOT STARTED | Engine that executes multi-surface publishing |
| M155 | Operation → event chain mapping | NOT STARTED | Each fleet operation defines its event chain |
| M156 | Multi-surface integration test | NOT STARTED | E2E test that verifies events propagate correctly |

### From design-lifecycle-health.md (M163-M169)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M163 | Stuck agent auto-detection | NOT STARTED | Detect agents with no progress for X hours |
| M164 | Service health monitoring | PARTIAL | Monitor daemon does IRC alerts only, no action |
| M165 | Config change detection + auto-push | NOT STARTED | When fleet config changes, push to agent workspaces |
| M166 | Worktree and branch cleanup | PARTIAL | Sync daemon cleans done tasks, nothing else |
| M167 | Health dashboard reporting | NOT STARTED | Rich health reports in board memory |
| M168 | Self-healing restart | NOT STARTED | Auto-restart failed services and agents |
| M169 | Resource cleanup automation | PARTIAL | Stale worktrees, old branches |

### From design-agent-framework-routing.md (M148-M152)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M148 | Framework base class | PARTIAL | MC_WORKFLOW.md + STANDARDS.md exist but agents don't follow them |
| M149 | Routing engine | NOT STARTED | Match tasks to agents by capability, availability, workload |
| M150 | Management agent (fleet-admin) | NOT STARTED | Maintains framework, distributes updates |
| M151 | Framework distribution | NOT STARTED | Auto-push SOUL.md / STANDARDS.md to all agents |
| M152 | Compliance monitoring | NOT STARTED | Track which agents follow the framework |

### From design-project-management.md (M170-M177)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M170 | Project manager agent definition | DONE | CLAUDE.md exists |
| M171 | Task evaluation system | NOT STARTED | Automated complexity, risk, story point assessment |
| M172 | Sprint management | PARTIAL | Sprint loader exists but PM doesn't drive sprints |
| M173 | Multi-model dispatch | NOT STARTED | Choose opus vs sonnet based on task complexity |
| M174 | Workload tracking | NOT STARTED | Which agents are overloaded, which are idle |
| M175 | Velocity and metrics | NOT STARTED | Story points per sprint, cycle time, throughput |
| M176 | Bottleneck detection | NOT STARTED | Identify what's slowing the fleet down |
| M177 | Sprint retrospectives | NOT STARTED | What went well, what didn't, what to change |

### From design-autonomous-drivers.md (M178-M183)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M178 | Driver agent model | PARTIAL | PM and AG have CLAUDE.md with driver roles, but don't act autonomously |
| M179 | DSPD product definition | DONE | design doc exists |
| M180 | Inter-driver dependency resolution | NOT STARTED | AG realizes it needs PM's DSPD first |
| M181 | Autonomous work queue | NOT STARTED | Drivers create work for themselves when idle |
| M182 | Product roadmap tracking | NOT STARTED | Drivers track progress toward their product vision |
| M183 | Cross-driver coordination | NOT STARTED | PM and AG coordinate on shared dependencies |

### From agent-command-center.md (M106-M117)
| # | Milestone | Status | What's Needed |
|---|-----------|--------|---------------|
| M106 | Research OCMC approvals system | PARTIAL | We know the API, but approval flow is broken |
| M107 | Research OCMC tags system | DONE | Tags configured |
| M108 | Research OCMC custom fields | DONE | Fields configured |
| M109 | Agent command center architecture | NOT STARTED | PRE → PROGRESS → POST lifecycle engine |
| M110 | Smart context resolution (PRE) | PARTIAL | fleet_read_context exists but incomplete |
| M111 | Directive resolution (PRE) | NOT STARTED | Which skills/rules apply to THIS task |
| M112 | Middleware/checkpoints (PROGRESS) | NOT STARTED | Structured quality gates during work |
| M113 | Output validation (POST) | NOT STARTED | Verify agent output meets standards |
| M114 | Self-validation | NOT STARTED | Agent checks own work before completing |
| M115 | Post-hooks | PARTIAL | fleet_task_complete does some, but no validation |
| M116 | Integration test | NOT STARTED | Full PRE → PROGRESS → POST test |
| M117 | Agent onboarding | NOT STARTED | New agents automatically get framework |

---

## Part 3: New Milestones Discovered Today

### M200: Task Lifecycle Redesign — Board Lead, Review Gates, Agent-Reviewed

**Problem:** The orchestrator auto-approves at >= 80% confidence without any reasoning
or validation. PRs get merged without review. Failing tests pass through. We bypass
OCMC's built-in board lead and review system entirely.

**Discovery:** OCMC already has a board lead system where review tasks are auto-assigned
to the lead agent. It has board configuration gates that enforce review-before-done,
comment-required-for-review, and approval blocking. We're using NONE of this.

**The Full Redesign:**

1. **fleet-ops becomes board lead** (`is_board_lead: true`)
   - MC auto-assigns review tasks to fleet-ops
   - fleet-ops is the review gatekeeper for all work

2. **Enable board configuration gates:**
   - `require_review_before_done: true` — tasks must go through review
   - `comment_required_for_review: true` — agents must explain their work
   - `block_status_changes_with_pending_approval: true` — no status change while approval pending

3. **Review gates custom field** (`review_gates`, json type):
   - Each task gets reviewers based on task type
   - Code: qa-engineer (required) + fleet-ops (required)
   - Architecture: architect (required) + fleet-ops (required)
   - Security: devsecops-expert (required) + fleet-ops (required)
   - fleet-ops creates review subtasks for each required reviewer

4. **fleet-ops orchestrates the review chain:**
   - Reads review_gates → creates review subtasks for each reviewer
   - Tracks gate completion
   - When all required gates pass → fleet-ops approves with reasoning
   - When any gate fails → fleet-ops sends back to inbox with feedback
   - When human attention needed → escalates to IRC with specific question

5. **Human in the loop:**
   - fleet-ops can escalate: "needs human attention"
   - Human responds via IRC, task edit, or board memory
   - fleet-ops reads response and continues the chain

6. **Remove auto-approve from orchestrator** — the orchestrator should NOT approve tasks.
   It should only:
   - Dispatch unblocked inbox tasks
   - Evaluate parent completion
   - Wake driver agents
   - Monitor health
   Approval is fleet-ops' job as board lead, not the orchestrator's.

**Milestones:**
| # | Scope |
|---|-------|
| M200a | Set fleet-ops as board lead + enable 3 board config gates |
| M200b | Design review_gates custom field schema + registration |
| M200c | fleet_task_complete populates review_gates based on task type |
| M200d | fleet-ops HEARTBEAT.md: review chain orchestration (create subtasks, track gates) |
| M200e | qa-engineer HEARTBEAT.md: test execution for review subtasks |
| M200f | Remove auto-approve from orchestrator, replace with review routing |
| M200g | Sync daemon: only merge PRs with fleet-ops lead approval |
| M200h | Rework flow: fleet-ops → inbox → original agent notified → fix → re-review |
| M200i | Escalation flow: fleet-ops → IRC #alerts → human responds → fleet continues |
| M200j | End-to-end test: full review chain from task completion to PR merge |

### M201: Quality Gates — Tests Must Pass Before Approval

**Problem:** Agents commit code without running tests. 43 tests failing in production.

**What must happen:**
1. `fleet_task_complete` runs tests before creating the approval
2. Test results included in the approval's rubric scores
3. If tests fail, task stays in review with a blocker comment
4. qa-engineer automatically triggered to investigate test failures
5. CI pipeline (GitHub Actions) as additional validation layer

**Milestones:**
| # | Scope |
|---|-------|
| M201a | fleet_task_complete runs pytest and includes results in approval |
| M201b | Approval rubric includes test_pass/test_fail counts |
| M201c | Orchestrator rejects approvals where tests failed |
| M201d | GitHub Actions CI for all fleet projects |

### M202: Claude Code Feature Exploitation

**Problem:** We don't know if agents are using Claude Code's full capabilities.
Extended thinking, effort index, compact execution, dream mode, memory, slash commands —
all potentially available but unevaluated.

**What must happen:**
1. Research each Claude Code feature:
   - What it does, how it works, what controls it
   - How agents can use it (config, SOUL.md, environment)
   - Which agent roles benefit most from which features
2. Test current agent behavior:
   - Do agents use extended thinking for complex tasks?
   - Do agents use memory across sessions?
   - What effort level are agents running at?
3. Design optimal configuration per agent:
   - Architect: high effort, extended thinking, dream mode for design
   - Software-engineer: balanced effort, compact for routine, high for complex
   - QA: high effort for test analysis, compact for routine checks
   - PM: dream mode for roadmap planning, extended thinking for evaluation
   - fleet-ops: compact for routine checks, high for quality analysis
   - Cyberpunk-Zero: high effort always (security can't be rushed)
4. Update agent configurations and SOUL.md files
5. Measure improvement in output quality

**Milestones:**
| # | Scope |
|---|-------|
| M202a | Research Claude Code features — effort, dream, compact, memory, slash commands |
| M202b | Audit current agent configuration and behavior |
| M202c | Design optimal feature configuration per agent role |
| M202d | Implement configurations (SOUL.md, .claude/, env vars) |
| M202e | Test and measure improvement |

### M203: Agent Communication and Teamwork Protocol

**Problem:** Agents don't communicate. Board memory is write-only. No agent reads
what others posted. No agent creates tasks for others. No agent flags concerns.

**What must happen:**
1. Every agent reads board memory FIRST via fleet_read_context
2. Agents create tasks for other agents when they discover work (fleet_task_create)
3. Agents post decisions, concerns, and knowledge to board memory with proper tags
4. Agents READ recent decisions before making their own
5. Agents reference each other's work with task URLs and PR links
6. PM coordinates — reads all board memory, creates assignments, tracks dependencies

**Milestones:**
| # | Scope |
|---|-------|
| M203a | Update all agent CLAUDE.md files with collaboration requirements |
| M203b | fleet_read_context returns richer board memory (recent decisions, alerts, blockers) |
| M203c | Add "team_recent" to fleet_agent_status — what each agent is working on |
| M203d | Agents create follow-up tasks proactively (test this with PM + software-engineer) |
| M203e | Measure board memory activity — posts, reads, cross-references per cycle |

### M204: Agent Personal Planning and Self-Organization

**Problem:** Agents execute tasks linearly without planning. They don't break down
complex work, don't estimate effort, don't consider alternatives.

**What must happen:**
1. Every agent plans before executing (documented in fleet_task_accept)
2. Complex tasks (L/XL) are broken down into subtasks via fleet_task_create
3. Agents estimate effort and complexity on their own work
4. Agents consider risks and unknowns before starting
5. Agents use extended thinking for planning phase

**Milestones:**
| # | Scope |
|---|-------|
| M204a | SOUL.md update — mandatory planning phase with structure |
| M204b | fleet_task_accept validates plan quality (minimum fields) |
| M204c | Test: give architect an epic, verify it creates subtask breakdown |
| M204d | Test: give PM a high-level goal, verify it creates sprint plan as tasks not text |

### M205: Agent Soul Evolution — Independent, Humble, Adaptive

**Problem:** Agent CLAUDE.md files are role descriptions, not personality and behavior guides.
Agents don't have personal judgment, don't adapt to situations, don't show initiative.

**What must happen:**
1. Every agent CLAUDE.md includes:
   - **Personality** — how they think, what they care about, their judgment style
   - **Initiative rules** — when to act without being told
   - **Collaboration principles** — how to work with others
   - **Quality ownership** — responsibility for their own output
   - **Learning** — use MEMORY.md to improve over time
2. SOUL.md (provisioned by MC) reinforces the behavioral expectations
3. Agent personalities emerge from consistent behavior, not just text

**Milestones:**
| # | Scope |
|---|-------|
| M205a | Audit all 10 CLAUDE.md files — what's there, what's missing |
| M205b | Write enhanced CLAUDE.md for each agent with full personality and behavior |
| M205c | Update SOUL.md template with behavioral expectations |
| M205d | Test: observe agent behavior before and after soul evolution |

### M206: Fix the Sync Daemon — No Blind Merging

**Problem:** Sync daemon merges PRs when task is done, without any review check.

**What must happen:**
1. Sync daemon checks for agent review approval before merging
2. PRs need at least one reviewing agent's approval
3. High-risk PRs (security, infrastructure) need human approval
4. Merge only after CI passes (when CI exists)

**Milestones:**
| # | Scope |
|---|-------|
| M206a | Sync daemon checks for review approval type (not just any approval) |
| M206b | Add "review_approved" custom field or tag for reviewed PRs |
| M206c | High-risk detection — security/infra tasks require human review |

### M209: Continuous-Running Engine — Change Detection and Event-Driven Triggers

**Problem:** The fleet operates on a 30-second polling loop. It can't react immediately
to events. When a task completes, the next task waits up to 30 seconds to be dispatched.
When a human responds, nobody notices for 30 seconds. The fleet feels sluggish and
disconnected.

**Discovery:** OCMC supports webhooks (with queue + retry + HMAC), SSE streaming for
approvals, and activity events with full audit trail. The gateway supports `wake`,
`nudge_board_agent()`, cron scheduling, and `agent.wait`. We use none of this.

**The Continuous Engine Design:**

1. **Phase 1: Webhook receiver** — Fleet HTTP endpoint that MC calls on events
   - Register webhooks for: task.status_changed, task.comment, approval.resolved
   - Webhook handler routes events to appropriate actions
   - Immediate reaction instead of polling

2. **Phase 2: Gateway cron** — Use gateway's native cron for heartbeats
   - Instead of orchestrator creating heartbeat tasks, use gateway cron
   - Gateway fires heartbeat directly to agent sessions on schedule
   - More reliable than our daemon-based approach

3. **Phase 3: Gateway wake for dispatching** — Use `wake` method with `deliver=true`
   - When orchestrator dispatches a task, use gateway wake instead of `chat.send(deliver=false)`
   - Agent is immediately woken and starts working
   - No waiting for next heartbeat poll

4. **Phase 4: Agent-to-agent nudge** — Use `nudge_board_agent()`
   - When fleet-ops creates a review subtask for qa-engineer, nudge qa-engineer
   - When PM creates a task for architect, nudge architect
   - Immediate agent-to-agent communication

5. **Phase 5: Activity event stream** — Read MC activity events for change detection
   - Instead of polling task list, read activity_events table
   - Detect: task.status_changed, task.comment, agent.heartbeat
   - More efficient, captures exact changes

**Milestones:**
| # | Scope |
|---|-------|
| M209a | Design webhook receiver endpoint (fleet/infra/webhook_server.py) |
| M209b | Register fleet webhooks on MC board for task + approval events |
| M209c | Event router: map MC events → fleet actions |
| M209d | Gateway wake integration in dispatch (deliver=true) |
| M209e | Gateway cron for agent heartbeats (replace orchestrator heartbeat tasks) |
| M209f | Agent-to-agent nudge via coordination_service |
| M209g | Activity event polling as fallback (when webhooks aren't available) |
| M209h | Full event-driven operation test: task change → immediate fleet reaction |

### M210: Full OCMC Exploitation — Use What The Platform Provides

**Problem:** We built custom solutions for things OCMC already handles natively.
We bypass the board lead system, ignore board config gates, don't use webhooks,
don't use SSE streams, don't use activity events, don't use agent wake properly.

**What OCMC provides that we should use:**

| OCMC Feature | What It Does | Current Usage | Should Be |
|-------------|-------------|---------------|-----------|
| Board lead (`is_board_lead`) | Auto-assigns review tasks to lead | Not set | fleet-ops = board lead |
| `require_review_before_done` | Tasks must go through review | false | true |
| `comment_required_for_review` | Agent must comment to enter review | false | true |
| `block_status_changes_with_pending_approval` | No status change with pending approval | false | true |
| Review → inbox rework flow | Lead sends back with notification | Not used | fleet-ops uses for rework |
| `lead_reasoning` on approvals | Lead must provide reasoning | Bypassed by auto-approve | fleet-ops provides reasoning |
| Task wake on assignment | MC wakes agent when task assigned | Partially used | Should be primary dispatch |
| SSE `/approvals/stream` | Real-time approval updates | Not used | Orchestrator subscribes |
| Webhooks | Event-driven task notifications | Not used | Primary event source |
| Activity events | Full mutation audit trail | Not used | Change detection |
| Dependency blocking | MC blocks transitions on unmet deps | Model exists, not fully exploited | Full dependency chain |
| `auto_created` + `auto_reason` | Track agent-created tasks | Field exists on MC, we tried but got 409 | Need to verify MC support |
| Task comments API | Structured comments per task | Used sparingly | Every status change has comment |
| Agent heartbeat API | Health check + wake | Used but unreliable | Gateway cron + proper monitoring |
| Board groups | Group multiple boards | Not used | Could organize per-project boards |

**Milestones:**
| # | Scope |
|---|-------|
| M210a | Configure fleet-ops as board lead |
| M210b | Enable board config gates (3 flags) |
| M210c | Verify and fix auto_created field support |
| M210d | Use MC's task-wake-on-assignment for dispatch |
| M210e | SSE subscription for real-time approval updates |
| M210f | Audit: list every OCMC feature and our usage level |

### M207: Dependency and Flow Management

**Problem:** MC blocks task creation with unmet dependencies. The sprint loader
failed to create 3 of 9 tasks because of this. `update_task` didn't support `depends_on`.

**What was fixed this session:**
- `update_task` now accepts `depends_on` parameter
- Sprint loader needs to be updated to create-then-wire pattern

**What still needs work:**
1. Sprint loader two-pass: create all tasks, then wire dependencies
2. Orchestrator properly handles dependency chains — when task completes,
   check if blocked tasks are now unblocked
3. MC's `is_blocked` field is properly read and used throughout
4. Parent task completion when all children done

**Milestones:**
| # | Scope |
|---|-------|
| M207a | Sprint loader two-pass (create then wire deps) |
| M207b | Orchestrator dependency chain validation |
| M207c | Parent-child completion flow end-to-end test |

### M208: Agent Heartbeat Reliability

**Problem:** fleet-ops was offline for hours. Nobody restarted it. PM has no active
heartbeat. Most agents have template-only HEARTBEAT.md files.

**What was done this session:**
- Real HEARTBEAT.md for PM, fleet-ops, Cyberpunk-Zero
- Worker template HEARTBEAT.md
- Orchestrator wakes driver agents

**What still needs work:**
1. Verify heartbeats actually fire (gateway heartbeat system)
2. Orchestrator monitors heartbeat health
3. Auto-restart for agents that fail their heartbeat
4. Heartbeat results tracked (did the agent actually do anything useful?)

**Milestones:**
| # | Scope |
|---|-------|
| M208a | Verify gateway heartbeat delivery to agents |
| M208b | Heartbeat result tracking in board memory |
| M208c | Orchestrator auto-restart for failed agents |
| M208d | Heartbeat dashboard in fleet status |

---

## Part 4: Milestone Priority and Sequencing

### Tier 1: CRITICAL — Fleet Produces Safe, Reviewed Output

These must be done FIRST. Without them, the fleet produces unreviewed, untested code
and merges it blindly. The auto-approve must be replaced with proper review chain.

```
M210a-b (OCMC exploitation: board lead + config gates)
  ↓  Enables the platform to enforce the review chain natively
M200a-j (Task lifecycle redesign: board lead, review gates, review chain)
  ↓  fleet-ops reviews all work, QA tests, architect reviews design
M201a-d (Quality gates: tests must pass before approval)
  ↓  No more broken code getting approved
M206a-c (Fix sync daemon: no blind merging)
  ↓  PRs only merge after proper agent review
M207a-c (Dependency and flow: sprint loader fix, chain validation)
```

**Estimated: 5 major milestones, ~15 sub-milestones**

### Tier 2: FOUNDATION — Agents Are Capable, Intelligent, Collaborative

Without these, agents are dumb task runners. With these, they're independent contributors
who think, plan, communicate, and use the full power of Claude Code.

```
M202a-e (Claude Code feature exploitation: effort, dream, compact, memory)
  ↓  Agents use the right mode for the right task
M205a-d (Agent soul evolution: personality, initiative, collaboration)
  ↓  Every agent is a strong, independent, humble, adaptive person
M203a-e (Communication protocol: board memory, follow-ups, cross-references)
  ↓  Agents read each other's work, create tasks, share knowledge
M204a-d (Personal planning: breakdown, estimation, risk assessment)
  ↓  Every agent plans before building
M208a-d (Heartbeat reliability: verify delivery, track results, auto-restart)
```

**Estimated: 5 major milestones, ~20 sub-milestones**

### Tier 3: SCALE — Fleet Self-Organizes Across Projects

The fleet can handle multiple projects, multiple sprints, cross-project dependencies,
and operates continuously with event-driven triggers.

```
M209a-h (Continuous engine: webhooks, gateway cron, nudge, event-driven)
  ↓  Fleet reacts immediately to changes, not on 30s polling
M210c-f (Full OCMC exploitation: all platform features)
  ↓  Every OCMC capability properly leveraged
M109-M117 (Agent command center: PRE/PROGRESS/POST lifecycle)
  ↓  Smart context resolution, directive injection, output validation
M148-M152 (Framework routing: capability matching, workload balancing)
  ↓  Right agent for the right task, automatically
M163-M169 (Lifecycle health: stuck detection, self-healing, cleanup)
  ↓  Fleet recovers from failures without human intervention
M170-M177 (Project management: velocity, metrics, sprint retrospectives)
  ↓  PM drives sprints with data, not guesses
M178-M183 (Autonomous drivers: PM drives DSPD, AG drives NNRT)
  ↓  Driver agents create their own work when human isn't directing
M153-M156 (Event chains: multi-surface publishing, operation mapping)
  ↓  Every operation cascades across all surfaces automatically
```

**Estimated: 8 major milestones, ~45 sub-milestones**

### Full Dependency Map

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: CRITICAL (do first)                                  │
│                                                              │
│  M210a-b ──→ M200a-j ──→ M201a-d ──→ M206a-c               │
│  (OCMC       (review      (quality     (sync                │
│   config)     chain)       gates)       fix)                 │
│                               ↓                              │
│                            M207a-c                            │
│                            (deps/flow)                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│ TIER 2: FOUNDATION           │                               │
│                              ↓                               │
│  M202 ──→ M205 ──→ M203 ──→ M204                            │
│  (Claude   (souls)  (comms)  (planning)                      │
│   Code)                                                      │
│              ↓                                               │
│           M208 (heartbeat reliability)                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│ TIER 3: SCALE                │                               │
│                              ↓                               │
│  M209 (continuous engine) ──→ M210c-f (full OCMC)            │
│       ↓                                                      │
│  M109-M117 (command center)                                  │
│       ↓                                                      │
│  M148-M152 (routing) ──→ M163-M169 (lifecycle)               │
│       ↓                       ↓                              │
│  M170-M177 (PM/velocity) ──→ M178-M183 (drivers)            │
│       ↓                                                      │
│  M153-M156 (event chains)                                    │
└─────────────────────────────────────────────────────────────┘
```

**Total: ~18 major milestones, ~80 sub-milestones across all 3 tiers.**

---

## Part 5: What Was Done This Session (For the Record)

### Bugs Fixed
1. **PR URL resolution** — worktree detection didn't set ctx.project_name (tools.py:212)
2. **Agent identity propagation** — agent_name not stored in task custom fields, not resolved from task when env var empty
3. **Dispatch custom fields** — dispatch now writes agent_name + worktree to MC task custom fields

### Built
1. **Data model expansion** — TaskType enum, TaskCustomFields +3 (parent_task, task_type, plan_id), Task +4 (is_blocked, blocked_by_task_ids, auto_created, due_at)
2. **MCClient updates** — approve_approval(), extended _parse_task (all 12+ custom fields, blocking fields, timestamps), extended create_task (auto_created, auto_reason, due_at), update_task +depends_on
3. **3 new MCP tools** — fleet_task_create, fleet_approve, fleet_agent_status (7 → 10 tools)
4. **Orchestrator daemon** — 5-step cycle (approve → transition → dispatch → parents → wake drivers), configurable, dry_run mode
5. **Sprint plan system** — YAML-based sprint plans, fleet sprint load/status CLI
6. **Agent heartbeats** — Real HEARTBEAT.md for PM, fleet-ops, Cyberpunk-Zero, worker template
7. **MC board config** — 12 custom fields, 20 tags registered
8. **Evolved MC_WORKFLOW.md** — 10 tools, planning phase, collaboration principles, driver section
9. **Evolved STANDARDS.md** — Agent identity, personal planning, Claude Code features, collaboration ethos
10. **Investigation document** — Full systemic analysis of fleet flow gaps

### Discovered Issues (Not Fixed)
1. **Auto-approve is brainless** — needs agent-reviewed approval flow (M200)
2. **No test validation** — agents commit failing tests, nobody catches it (M201)
3. **Sync daemon blind merges** — no review check before PR merge (M206)
4. **43 failing tests** — agent-produced Plane code has wrong async test markers (M201)
5. **Sprint loader can't create tasks with deps** — MC blocks creation with unmet deps (M207a)
6. **Claude Code features unexploited** — effort, dream, compact unknown/unused (M202)
7. **Agent communication dead** — board memory write-only, no collaboration (M203)
8. **Gateway doesn't propagate MCP env vars** — workaround exists but not a proper fix

### Tests
- 91 passing (70 original + 21 new from agent-produced Plane code that parse correctly)
- 43 failing (agent-produced async tests with wrong marker)
- 16 failing (agent-produced plane_sync tests)

---

## Part 6: DSPD Sprint 1 Status

| Task | Agent | Status | PR | Issues |
|------|-------|--------|-----|--------|
| S1-epic | — | inbox | — | No agent assigned, just a grouping task |
| S1-1: Research Plane Docker | devops | done | [PR #1](https://github.com/cyberpunk042/devops-solution-product-development/pull/1) | PR URLs pointed to NNRT (fixed), PR still open |
| S1-2: Deploy Plane Docker | devops | inbox [BLOCKED] | — | Depends on S1-1 (in review, not done) |
| S1-3: Configure workspace | devops | review | [PR #3](https://github.com/cyberpunk042/devops-solution-product-development/pull/3) | Agent completed in MC workspace, not DSPD repo |
| S1-4: API key + test API | devops | inbox [BLOCKED] | — | Depends on S1-3 |
| S1-5: plane_client.py | software-engineer | review | — | Completed but 43 test failures |
| S1-6: fleet plane CLI | software-engineer | inbox [BLOCKED] | — | Depends on S1-5 |
| S1-7: Plane ↔ OCMC sync | software-engineer | review | — | 16 test failures in plane_sync |
| S1-8: Security review | devsecops-expert | review | — | Completed but no approval |

**Sprint is stuck** because:
1. No agent review process exists (M200)
2. Tests are failing and nobody is fixing them (M201)
3. Auto-approve moved some tasks to done without validation
4. Blocked tasks can't be dispatched until dependencies complete
5. The orchestrator auto-approved without quality checks

---

## Part 7: What The User Said (Verbatim Requirements)

These are the user's exact words, preserved for reference:

> "we need to think about this really deeply. DSPD will unlock a lot of scale but
> before that the fleet has to be able to handle task with sub tasks and related to
> a plan and chained tasks that appear or unlock when they are possible to analyse
> or start working or start thinking about"

> "we need to evolve the command center after all this and the souls and methods of
> works and so on. WE need to make every member a strong independent person and yet
> so synergic and responsive for the others too and humble and adaptative"

> "do we even use the claude code effort indice and strategic compact execution and
> dream? we will need to evaluate all this after and see the rooms for improvements
> and better exploitation of the technologies and a better fleet and agents in general
> and them properly tooled and directed"

> "sometime the Architect and the Project Manager or anyone else like Software engineer
> will make plan and break down into even smaller task or follow up or blocker or
> request or UX demand or concern, we need to instaure strong communication and
> teamwork and strong lifecycle health and flow"

> "it could start with one task that lead to a plan that lead to three first task
> and then unlock two other group of tasks and so one till all the children are done
> and the requirements of the parent parent task is meet through all the children
> tasks and a collaborative work and a continuous advancement, evolution, improvement
> and desire to meet the request(s) and push for excellence"

> "WHY IS THERE AUTO MERGING PR WITHOUT REASONING ??? WHERE IS THE AGENTS ROLES ?????"

> "IF TEST ARE FAILING AND NOTHING IS DONE ABOUT IT ITS THAT MULTIPLE AGENTS ARE
> NOT DOING THEIR FUCKING JOB"