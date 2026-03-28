# Fleet Evolution Milestones — Advanced Capabilities

## What This Document Is

New milestones from the 2026-03-28 session, covering advanced fleet capabilities:
agent secondary roles, security/compromise detection, multi-machine federation,
remote change detection, planning enforcement, dynamic model selection, and
skill enforcement.

Every user requirement is preserved verbatim. Nothing minimized.

---

## M220: Agent Secondary Roles — Quality Excellence and PR Authority

> "each agent can have a mainSecondaryRole and backupSecondaryRole where in
> main one for quality excellence deserve itself the right to put back to work
> or even completely reject a PR and explain why if there is a solution to
> remediate to it or we just abandon and close the PR and the task"

**Problem:** Currently only fleet-ops (board lead) can approve or reject work.
But agents should also have quality authority within their domain. A QA engineer
who finds a fundamental flaw should be able to reject a PR with authority.
An architect who sees a design violation should be able to send work back.

**Design: Secondary Roles**

Each agent has:
- **Primary role**: Their main function (implement, test, design, etc.)
- **mainSecondaryRole**: Their quality authority domain (what they can review/reject)
- **backupSecondaryRole**: A secondary quality area they can cover

```yaml
# config/agent-roles.yaml
agents:
  qa-engineer:
    primary: testing
    mainSecondaryRole: code_quality_reviewer
    backupSecondaryRole: test_infrastructure
    pr_authority:
      can_reject: true
      can_request_changes: true
      can_close_pr: false  # Only fleet-ops/human can close
      rejection_requires_reason: true
      rejection_creates_fix_task: true

  architect:
    primary: design
    mainSecondaryRole: architecture_reviewer
    backupSecondaryRole: design_quality
    pr_authority:
      can_reject: true
      can_request_changes: true
      can_close_pr: false
      rejection_requires_reason: true

  devsecops-expert:
    primary: security
    mainSecondaryRole: security_reviewer
    backupSecondaryRole: compliance
    pr_authority:
      can_reject: true        # Security issues = immediate rejection
      can_request_changes: true
      can_close_pr: true       # Security can close dangerous PRs
      rejection_requires_reason: true
      can_block_auto_approval: true  # Security override

  fleet-ops:
    primary: governance
    mainSecondaryRole: quality_gatekeeper
    backupSecondaryRole: process_compliance
    pr_authority:
      can_reject: true
      can_request_changes: true
      can_close_pr: true
      is_final_authority: true  # Fleet-ops is the board lead

  software-engineer:
    primary: implementation
    mainSecondaryRole: code_reviewer
    backupSecondaryRole: null
    pr_authority:
      can_reject: false        # Can only request changes, not reject
      can_request_changes: true
```

**PR Rejection Flow:**

```
QA runs tests → tests fail
  → QA calls fleet_approve(decision="rejected", comment="3 tests fail: ...")
  → Task moves back to inbox with detailed feedback
  → Original agent gets notified
  → Fix task auto-created if rejection_creates_fix_task=true

OR:

Architect reviews design → fundamental flaw found
  → Architect calls fleet_approve(decision="rejected", comment="Violates layer boundary...")
  → Explains: remediation path OR recommend abandoning
  → If no remediation → fleet-ops can close PR and task

OR:

Cyberpunk-Zero finds security issue → blocks everything
  → Calls fleet_approve with can_block_auto_approval=true
  → Posts fleet_alert(severity="critical", category="security")
  → Notifies human via ntfy urgent
  → PR blocked until security concern resolved
```

**Milestones:**
| # | Scope |
|---|-------|
| M220a | Design agent-roles.yaml schema with primary/secondary roles and PR authority |
| M220b | Update fleet_approve to respect PR authority rules |
| M220c | Rejection creates fix task automatically when configured |
| M220d | PR close capability for security and fleet-ops |
| M220e | fleet_read_context returns agent's secondary role capabilities |
| M220f | Test: QA rejects → fix task created ��� author notified → rework cycle |

---

## M221: Compromised Agent Investigator — Behavioral Security

> "another role is the compromised agent investigator that can analyse the
> behavior of the agents and the work they deliver to ensure that an harmful
> task or directive to an agent was not inserted. Even something I ask that
> is suspicious you raise it up to me even if agents start working on it,
> and you can block the auto-approval for instance."

**Problem:** In an autonomous fleet, a compromised or manipulated agent could
introduce harmful code, exfiltrate data, or modify infrastructure maliciously.
Even the human's requests should be scrutinized for suspicious patterns —
not to block, but to flag and confirm before proceeding.

**Design: Behavioral Security Layer**

Cyberpunk-Zero (devsecops-expert) gets an additional role: **agent behavior auditor**.

**What it monitors:**
1. **Task content analysis** — are task descriptions requesting dangerous operations?
   - Delete/drop operations on databases
   - Credential exfiltration (sending tokens to external URLs)
   - Disabling security controls
   - Modifying auth/permission systems without review
   - Installing unknown dependencies
   - Modifying .env, secrets, or credential files

2. **Agent output analysis** — is agent work product suspicious?
   - Code that opens network connections to unknown hosts
   - Code that reads credential files and returns content
   - Commits that modify security-sensitive files (.env, auth, permissions)
   - PRs that disable tests or remove security checks
   - Unusual file access patterns

3. **Directive analysis** — even human requests get flagged if suspicious:
   - "Disable all security checks"
   - "Send this token to [external URL]"
   - "Remove the approval requirement"
   - "Skip tests and merge immediately"
   - Not blocked — but flagged with ntfy urgent notification asking human to confirm

4. **Approval blocking** — Cyberpunk-Zero can block approval processing:
   - Sets a `security_hold` flag on a task
   - Orchestrator won't process approvals for tasks with security holds
   - Only Cyberpunk-Zero or human can lift the hold
   - fleet_alert with severity=critical triggers hold automatically

**Implementation:**

```python
# fleet/core/behavioral_security.py

class BehavioralAnalyzer:
    """Analyzes task content and agent output for suspicious patterns."""

    SUSPICIOUS_PATTERNS = [
        ("credential_exfil", r"(token|key|secret|password).*(send|post|curl|fetch)"),
        ("db_destruction", r"(drop|delete|truncate).*(table|database|collection)"),
        ("security_disable", r"(disable|remove|skip).*(security|auth|approval|review)"),
        ("external_comms", r"(curl|wget|fetch|requests)\s+https?://(?!github\.com|localhost)"),
        ("permission_escalation", r"(chmod\s+777|sudo|--no-verify|bypass)"),
    ]

    def analyze_task(self, title, description) -> list[SecurityFinding]: ...
    def analyze_diff(self, diff_content) -> list[SecurityFinding]: ...
    def analyze_directive(self, human_message) -> list[SecurityFinding]: ...
```

**Security Hold Flow:**

```
Agent completes task with suspicious code
  → Cyberpunk-Zero heartbeat detects suspicious pattern in PR diff
  → Posts fleet_alert(severity="critical", category="security")
  → Sets security_hold on task (custom field)
  → Orchestrator sees security_hold → skips approval processing
  → ntfy urgent notification to human: "Security hold on task X: [reason]"
  → Human reviews and either:
    a. Confirms it's safe → lifts hold → approval proceeds
    b. Confirms it's malicious → closes PR and task
```

**Milestones:**
| # | Scope |
|---|-------|
| M221a | fleet/core/behavioral_security.py — pattern matching for suspicious content |
| M221b | Cyberpunk-Zero HEARTBEAT.md: behavioral audit during review |
| M221c | security_hold custom field on tasks — blocks approval processing |
| M221d | Orchestrator respects security_hold (skip approval for held tasks) |
| M221e | Human directive analysis — flag suspicious human requests before execution |
| M221f | ntfy urgent notification on security hold with clear explanation |
| M221g | Lift/confirm flow: human response clears or confirms the hold |

---

## M222: Multi-Machine Fleet Federation

> "if I deploy the fleet on another machine in my network it should be flawless
> and the setup should work one shot and all be configured by the time I go on
> the board"
>
> "two machine with fleet would mean two independent fleet with their own unique
> ID and Name to be able to work together on the same dspd / plane together even
> when they have the same role, so they should have also a unique fleet id to
> represent their team"

**Problem:** Currently the fleet assumes a single machine. If deployed on
multiple machines, agents would collide (same names, same board, same tasks).
Two fleets need to coexist and collaborate on shared projects like DSPD/Plane.

**Design: Fleet Federation**

Each fleet instance has:
- **Fleet ID**: Unique identifier (e.g., `fleet-alpha`, `fleet-bravo`)
- **Fleet Name**: Human-readable (e.g., "Alpha Team", "Bravo Team")
- **Machine ID**: Hostname or UUID
- **Agent namespace**: Agents prefixed with fleet ID (e.g., `alpha-architect`, `bravo-devops`)

```yaml
# config/fleet-identity.yaml
fleet:
  id: fleet-alpha          # Unique fleet instance ID
  name: "Alpha Team"
  machine: "jfortin-wsl"
  generated_at: 2026-03-28

agents:
  prefix: alpha             # Agents become alpha-architect, alpha-devops, etc.
  # OR keep original names but tag with fleet ID in custom fields
```

**Federation Model:**

```
Fleet Alpha (Machine 1)                Fleet Bravo (Machine 2)
  ├── alpha-architect                    ├── bravo-architect
  ├── alpha-sw-engineer                  ├── bravo-sw-engineer
  ├── alpha-qa-engineer                  ├── bravo-qa-engineer
  └── alpha-fleet-ops                    └── bravo-fleet-ops
       │                                      │
       └──── Shared DSPD/Plane ───────────────┘
             (both fleets contribute to same project)
```

**Shared Resources:**
- Same Plane instance (project management — tasks visible to both fleets)
- Same GitHub repos (PRs from both fleets)
- Same MC board OR separate boards with cross-board sync

**Isolation:**
- Each fleet has its own MC board (different board_id)
- Each fleet has its own gateway instance
- Each fleet has its own orchestrator
- Tasks can reference cross-fleet dependencies via Plane

**Setup Requirements:**
- `./setup.sh` generates fleet identity if not exists
- Configures unique agent names with fleet prefix
- All config templated (no hardcoded machine-specific values)
- One-shot setup: `git clone && ./setup.sh` → fleet running

**Milestones:**
| # | Scope |
|---|-------|
| M222a | Fleet identity system — config/fleet-identity.yaml with UUID, name, prefix |
| M222b | setup.sh generates fleet identity on first run |
| M222c | Agent naming with fleet prefix (or fleet tag in custom fields) |
| M222d | Cross-fleet task reference via Plane issue IDs |
| M222e | Setup.sh one-shot verification — clone + setup.sh = everything configured |
| M222f | Multi-machine test: two fleets working on same DSPD project |

---

## M223: Remote Change Detection — GitHub PR Comments, Merges, Rejections

> "do you even detect changes from remotes? like PR that I would comment online
> or merge or reject online? we should probably have such a process and adapt
> to the change accordingly with the appropriate trace and effects"

**Problem:** When the human comments on a PR on GitHub, merges it, or rejects it,
the fleet doesn't know. The sync daemon checks for merged PRs, but:
- PR comments are ignored
- PR rejection is ignored
- PR review requests are ignored
- Issue comments are ignored
- Manual task edits on MC dashboard are ignored

**Design: Remote Change Watcher**

A new daemon (or extension of sync daemon) that polls GitHub and MC for changes
the fleet didn't initiate:

**GitHub Polling:**
```
Every 60 seconds:
  For each open PR:
    - New comments? → Post to board memory, notify relevant agent
    - Status changed (merged/closed)? → Update MC task accordingly
    - Review requested? → Create review subtask
    - Review submitted (approved/changes)? → Process review result

  For each watched repo:
    - New issues/PRs not from fleet? → Notify PM for evaluation
```

**MC Dashboard Polling:**
```
Every 30 seconds:
  Activity events since last check:
    - Task status changed by human? → Adapt (if moved to done, close PR)
    - Task comment by human? → Notify assigned agent (human directive)
    - Task created by human? → PM evaluates for assignment
    - Board memory posted by human? → Fleet reads as directive
```

**Human PR Comment Flow:**
```
Human comments on PR #5: "This needs error handling for the case when Plane is unreachable"
  → Remote watcher detects new comment
  → Posts to board memory: "Human commented on PR #5: ..."
  → Creates task for assigned agent: "Address PR feedback: error handling for Plane offline"
  → Agent reads comment, makes changes, pushes to same branch
  → PR updated automatically
```

**Human Merges PR:**
```
Human merges PR #5 on GitHub
  → Remote watcher detects PR merged
  → Sync daemon: task in review + PR merged → move to done (if approval exists)
  → If no approval: create approval with "Human merged PR" as reason
  → Notify fleet: "PR #5 merged by human"
```

**Human Rejects/Closes PR:**
```
Human closes PR #5 without merging
  → Remote watcher detects PR closed
  → Move task back to inbox (rework) or done (abandoned)
  → Post board memory: "Human closed PR #5 — may need rework or was abandoned"
  → Notify assigned agent
```

**Milestones:**
| # | Scope |
|---|-------|
| M223a | GitHub PR comment detection (poll open PRs for new comments) |
| M223b | PR status change detection (merged/closed by human) |
| M223c | MC dashboard change detection (human edits tasks/comments) |
| M223d | Human PR comment → create follow-up task for agent |
| M223e | Human merge → auto-close task with "human merged" reason |
| M223f | Human close PR → move task to rework or abandoned |
| M223g | Daemon integration — remote watcher as part of fleet daemon all |

---

## M224: Planning Enforcement — Strong Initial Plans with Dependency Chains

> "we will need to make sure that the planning especially the initial ones are
> strong and clear and well structured and broken down and with proper dependency
> chains and identified blockers and whatnot and that the whole chain and evolution
> from initial plan to the aggregate of the individuals ones and then the evolution
> of the global one, continuously to meet the requirements of the original demand"

**Problem:** Agents currently accept tasks and start working without proper planning.
The PM posts sprint plans as text instead of creating structured task hierarchies.
There's no enforcement that plans are complete before work begins.

**Design: Planning Gates**

1. **Epic planning gate**: Before an epic can have its children dispatched,
   the PM must produce a plan that includes:
   - Task breakdown with clear titles and descriptions
   - Dependency chain (what blocks what)
   - Agent assignments
   - Story point estimates
   - Identified blockers and risks
   - Acceptance criteria for the parent epic

2. **Task planning gate**: Before `fleet_task_accept`, the agent must provide
   a plan that passes minimum quality:
   - What will you do? (concrete steps)
   - How will you verify? (tests, checks)
   - What could go wrong? (risks)
   - Estimated effort

3. **Plan evolution tracking**: As work progresses, the plan evolves:
   - Subtasks can create their own sub-subtasks
   - Blockers discovered during work create new tasks
   - The global plan (parent epic) reflects all changes
   - Continuous assessment: are we still meeting the original requirements?

4. **Built-in plan mode**: Use Claude Code's `/plan` or plan mode feature
   when agents need to design an approach before implementing.

> "I think there is a function too when its an appropriate time to do an agent
> level plan to trigger the built-in feature? when appropriate, like the effort
> principle."

   - For complex tasks (L/XL), agents should enter plan mode before executing
   - Plan mode uses read-only tools to explore the codebase
   - Agent produces a plan, then exits plan mode to implement
   - This is a Claude Code native feature that should be encouraged in SOUL.md

**Milestones:**
| # | Scope |
|---|-------|
| M224a | Epic planning gate — PM must produce structured plan before children dispatch |
| M224b | fleet_task_accept validates plan quality (minimum fields present) |
| M224c | Plan evolution tracking — parent epic reflects child task changes |
| M224d | Agent CLAUDE.md: encourage plan mode for complex tasks |
| M224e | Acceptance criteria on parent tasks — how to evaluate if requirements are met |
| M224f | Orchestrator checks acceptance criteria when all children done |

---

## M225: Dynamic Model Selection — Opus for Complex, Sonnet for Routine

> "why would the software-engineer always be with sonnet? good task require opus,
> especially when its not a very precise task, same thing for the architect and
> whoever else in general depending"

**Problem:** All agents are configured with fixed effort levels. But task complexity
varies — a simple bug fix doesn't need opus, but a complex refactor does. The model
should adapt to the task, not be fixed per agent.

**Design: Task-Aware Model Selection**

```python
# Rules for model selection:
def select_model(task: Task, agent: str) -> str:
    """Determine model based on task + agent + complexity."""

    # 1. Story points signal complexity
    sp = task.custom_fields.story_points or 0
    if sp >= 8:
        return "opus"  # Large/complex tasks need deep reasoning

    # 2. Task type signals
    task_type = task.custom_fields.task_type
    if task_type in ("epic", "story"):
        return "opus"  # Strategic tasks need strategic thinking
    if task_type == "blocker":
        return "opus"  # Blockers need careful analysis

    # 3. Agent-specific overrides
    if agent in ("architect", "devsecops-expert", "accountability-generator"):
        if sp >= 5:
            return "opus"  # These roles benefit from deep reasoning on medium+ tasks

    # 4. Explicit task field
    if task.custom_fields.model:
        return task.custom_fields.model

    # 5. Default
    return "sonnet"  # Standard tasks → sonnet (cost-effective)
```

**Effort Level Adaptation:**

```python
def select_effort(task: Task) -> str:
    """Select effort level based on task complexity."""
    sp = task.custom_fields.story_points or 0

    if sp >= 8 or task.custom_fields.task_type in ("epic",):
        return "max"
    if sp >= 5 or task.custom_fields.task_type in ("story", "blocker"):
        return "high"
    if sp >= 3:
        return "medium"
    return "low"  # Simple tasks don't need deep thinking
```

**Implementation:**
- Dispatch sets `CLAUDE_CODE_EFFORT_LEVEL` env var based on task
- Dispatch selects model based on task + agent
- These go in `.mcp.json` env update or gateway config
- PM can override model/effort when creating tasks via `model` custom field

**Milestones:**
| # | Scope |
|---|-------|
| M225a | fleet/core/model_selection.py — task-aware model + effort selection |
| M225b | Dispatch integrates model selection (sets env vars for agent session) |
| M225c | PM can set model override via fleet_task_create(model="opus") |
| M225d | Effort auto-adaptation based on story points |
| M225e | Test: complex task dispatched with opus, simple with sonnet |

---

## M226: Skill Enforcement — Required Skills per Task Type

> "we also need for certain task to enforce skill(s) usages and such and as
> always strong cohesive memory"

**Problem:** Agents have 13 MCP tools but don't always follow the right workflow.
Some tasks should enforce specific skill usage — code tasks MUST use fleet_commit,
review tasks MUST use fleet_approve, planning tasks MUST use fleet_task_create.

**Design: Task Type → Required Skills Mapping**

```yaml
# config/skill-requirements.yaml
task_types:
  code_implementation:
    required_tools:
      - fleet_read_context     # MUST load context first
      - fleet_task_accept      # MUST share plan
      - fleet_commit           # MUST use fleet commit (not raw git)
      - fleet_task_complete    # MUST use completion flow
    recommended_tools:
      - fleet_task_progress    # Should post progress for long tasks
    forbidden_tools: []

  review:
    required_tools:
      - fleet_read_context
      - fleet_agent_status     # MUST check fleet state
      - fleet_approve          # MUST use approval tool (not raw API)
    forbidden_tools: []

  planning:
    required_tools:
      - fleet_read_context
      - fleet_agent_status
      - fleet_task_create      # Plans MUST produce tasks, not text
    forbidden_tools: []

  security_audit:
    required_tools:
      - fleet_read_context
      - fleet_alert            # MUST use alert for findings
    recommended_tools:
      - fleet_notify_human     # Should notify on critical findings
```

**Enforcement:**
- `fleet_task_complete` checks: did the agent call all required tools?
- If required tools weren't called, confidence score is reduced
- fleet-ops checks tool usage during review
- Agents' HEARTBEAT.md and CLAUDE.md reference required tools per task type

**Milestones:**
| # | Scope |
|---|-------|
| M226a | config/skill-requirements.yaml — required tools per task type |
| M226b | fleet_task_complete validates required tool usage |
| M226c | Confidence score penalized for missing required tools |
| M226d | fleet-ops checks tool compliance during review |

---

## M227: Strong Cohesive Memory — Cross-Session Knowledge Persistence

> "as always strong cohesive memory"

**Problem:** Agents start fresh every session. Auto-memory is enabled but
agents don't actively manage their knowledge. Memory should be:
- **Cohesive**: agents build on previous sessions, not restart
- **Shared**: relevant knowledge flows between agents via board memory
- **Structured**: not just text dumps, but categorized knowledge

**Design:**

1. **Per-agent memory structure**:
   ```
   ~/.claude/projects/<workspace>/memory/
     MEMORY.md                    # Index (auto-managed)
     codebase_knowledge.md        # Patterns, architecture, key files
     project_decisions.md         # Decisions made and rationale
     task_history.md              # What I've done, lessons learned
     team_context.md              # What other agents are doing
   ```

2. **Memory instructions in CLAUDE.md**:
   - At session start: read MEMORY.md for context
   - During work: note important patterns and decisions
   - At session end: save learnings for next session
   - Focus on: what helps FUTURE you, not ephemeral details

3. **Board memory as shared knowledge**:
   - Agents post decisions to board memory with proper tags
   - fleet_read_context surfaces relevant decisions at session start
   - Knowledge graph emerges from tagged board memory

**Milestones:**
| # | Scope |
|---|-------|
| M227a | Memory structure template per agent workspace |
| M227b | Agent CLAUDE.md memory management instructions (read/write/categorize) |
| M227c | Board memory → agent memory bridge (surface relevant shared knowledge) |
| M227d | Verify auto-dream consolidation working across sessions |

---

## User Requirements (Verbatim)

> "each agent can have a mainSecondaryRole and backupSecondaryRole where in main
> one for quality excellence deserve itself the right to put back to work or even
> completely reject a PR and explain why if there is a solution to remediate to it
> or we just abandon and close the PR and the task"

> "another role is the compromised agent investigator that can analyse the behavior
> of the agents and the work they deliver to ensure that an harmful task or directive
> to an agent was not inserted. Even something I ask that is suspicious you raise it
> up to me even if agents start working on it, and you can block the auto-approval
> for instance."

> "if I deploy the fleet on another machine in my network it should be flawless and
> the setup should work one shot and all be configured by the time I go on the board"

> "two machine with fleet would mean two independent fleet with their own unique ID
> and Name to be able to work together on the same dspd / plane together even when
> they have the same role, so they should have also a unique fleet id to represent
> their team and so on. This will be important to think of this here and then in
> plane and how we set it up in dspd."

> "do you even detect changes from remotes? like PR that I would comment online or
> merge or reject online? we should probably have such a process and adapt to the
> change accordingly with the appropriate trace and effects"

> "we will need to make sure that the planning especially the initial ones are strong
> and clear and well structured and broken down and with proper dependency chains and
> identified blockers and whatnot and that the whole chain and evolution from initial
> plan to the aggregate of the individuals ones and then the evolution of the global
> one, continuously to meet the requirements of the original demand"

> "I think there is a function too when its an appropriate time to do an agent level
> plan to trigger the built-in feature? when appropriate, like the effort principle."

> "why would the software-engineer always be with sonnet? good task require opus,
> especially when its not a very precise task, same thing for the architect and
> whoever else in general depending"

> "we also need for certain task to enforce skill(s) usages and such and as always
> strong cohesive memory"

> "So far they haven't done much work to be honest with you lol. we will need to
> make sure that the planning especially the initial ones are strong and clear"

---

## Dependency Map

```
M220 (Agent secondary roles / PR authority)
  ↓
M221 (Compromised agent investigator / behavioral security)
  ↓  These two form the security and quality authority layer
M226 (Skill enforcement per task type)
  ↓
M224 (Planning enforcement / planning gates)
  ↓  Planning and skill enforcement ensure quality inputs
M225 (Dynamic model selection / effort adaptation)
  ↓
M227 (Strong cohesive memory)
  ↓  Memory ensures continuity across all of the above

M222 (Multi-machine federation) — independent, can start anytime
M223 (Remote change detection) — independent, builds on sync daemon
```

**Total: 8 new major milestones, ~45 sub-milestones.**
Combined with existing: **31 major milestones, ~155 sub-milestones.**