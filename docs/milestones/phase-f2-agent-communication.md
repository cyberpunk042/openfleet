# Phase F2: Agent Communication Protocol

> "The AIs can communicated and thats not nothing, they can even create future tasks for themselves or other agents or lift warnings about something or suggestion or improvement like the fact that we are missing an Agent X or Y or Z and whatnot or that we lack this skill or that or this or that we lack this knowledge or this or that."

> "There are also operations that deserve an internal message and there are time the AI has to know to put in pause and/or create a task to another agent and whatnot."

> "WE need order and logic for when to use what and how to use it and make it very easy and simple and reduce the complexity and make sure we do not be lazy or minimize or underuse a feature."

## Problem Statement

Agents currently operate in isolation. They receive a task, do the work, report back.
They don't talk to each other. They don't proactively alert about problems. They don't
create follow-up work. They don't know when to pause and ask. Board memory is dead.
The "chat" feature in MC is unused.

The fleet has the CAPABILITY to communicate (MC board memory, IRC, task comments) but
no PROTOCOL for when and how to use it.

## Design Principle

**Make the rules simple and clear so agents can follow them without confusion.**

The communication protocol must be:
1. Easy to understand — an agent reads it once and knows what to do
2. Unambiguous — no "use your judgment" for surface selection
3. Complete — every situation has a defined action
4. Not over-engineered — reduce complexity, don't add it

## Communication Decision Matrix (M87)

This is the core document. Agents read this and know exactly what to do in every situation.

### When do I post a TASK COMMENT?

**Always when the information is about THIS SPECIFIC TASK:**
- Accepting the task
- Progress updates on the task
- Blocked on the task
- Completing the task
- Test results for the task
- Code review results for the task

**Format:** Use the fleet-comment skill templates.

### When do I post to BOARD MEMORY?

**When the information is relevant BEYOND this specific task:**
- A decision that affects the project or fleet
- A security concern found while working
- A suggestion for improvement
- Knowledge that other agents need (architecture, patterns, gotchas)
- PR ready for review (cross-agent awareness)
- Warning about a missing skill, agent, or capability

**Tags are REQUIRED.** Every board memory entry must have:
- At least one TYPE tag: alert, decision, suggestion, knowledge, report
- At least one SCOPE tag: project:{name}, fleet, workflow, tooling
- Severity tag if it's an alert: critical, high, medium, low

**Format:** Use the fleet-memory skill templates.

### When do I post to IRC?

**When the HUMAN needs to know RIGHT NOW:**
- Task started (human awareness)
- PR ready for review (human action needed)
- Task blocked (human may need to unblock)
- Security alert (human must act)
- Task completed (human awareness)
- Merge/close events (human awareness)

**Also posted automatically by fleet scripts:**
- dispatch-task.sh posts on dispatch
- fleet-sync.sh posts on merge/close
- Future: governance agent posts daily digest

**Format:** Use the fleet-irc skill format.

### When do I CREATE A NEW TASK?

> "create future tasks for themselves or other agents"

**When I discover work that is SEPARATE from my current task:**
- Bug found while working on something else → create task for software-engineer
- Missing documentation found → create task for technical-writer
- Architecture concern found → create task for architect
- Test gap found → create task for qa-engineer
- Infrastructure issue found → create task for devops

**Rules:**
- Only the board lead can create tasks (or agents must request via board memory)
- OR: we grant task creation to all agents (needs discussion — security vs fluidity)
- New task must reference the parent task that spawned it
- New task must have proper project tag and custom fields

**Design decision needed:** Should all agents create tasks, or only the lead?
- Option A: All agents create tasks → more fluid, but risk of task spam
- Option B: Only lead creates → more controlled, but agents have to request
- Option C: Agents can create tasks tagged "proposed" → lead approves/activates
- **Recommended: Option C** — fluid for agents, controlled for the human

### When do I PAUSE AND ESCALATE?

> "the AI has to know to put in pause"

**Pause when:**
- Requirements are unclear and guessing would waste work
- The change is high-risk (security, data, infrastructure) and needs human approval
- Multiple valid approaches exist and the human should decide
- Another agent's work blocks mine and that agent isn't responding
- I've been working for a long time without progress (stuck)

**How to pause:**
1. Post a BLOCKER comment on the task (fleet-comment skill, blocker template)
2. Post to IRC: `[agent] BLOCKED: reason — task_url`
3. Post to board memory if it affects other agents: tags [blocked, project:{name}]
4. DO NOT continue guessing. Wait for human input.

### When do I WARN about something?

> "lift warnings about something or suggestion or improvement... missing an Agent X or Y or Z... lack this skill or that"

**Warn when I notice:**
- A security vulnerability (CVE, exposed secret, vulnerable dependency)
- A quality issue (no tests, low coverage, code smell, missing docs)
- A missing capability (we need a skill for X, we need an agent for Y)
- A workflow problem (this process is broken, this automation is missing)
- An architecture concern (this coupling is dangerous, this won't scale)

**How to warn:**
1. Post to board memory using the ALERT template (fleet-memory skill)
2. Post to IRC: `⚠️ [agent] SEVERITY ALERT: title — url`
3. If critical: also post a blocker on the relevant task
4. If it needs action: create a proposed task (Option C above)

---

## Follow-Up Task Skill (M88)

**Purpose:** Agents create well-formed tasks for other agents when they discover work.

**Design:**
- Skill reads TOOLS.md for credentials
- Agent provides: title, description, suggested agent, priority, parent task ID
- Skill creates the task via MC API with:
  - Proper project custom field
  - Proper tags (project, type)
  - depends_on_task_ids linking to parent
  - Status: "inbox" (or "proposed" if we implement Option C)
- Skill posts to board memory: "Proposed task: {title} for @{agent}"
- Skill posts to IRC: "[agent] PROPOSED TASK: {title} for @{target_agent}"

---

## Alert/Warning Skill (M89)

**Purpose:** Proactive alerts for security, quality, architecture concerns.

> "warn me about important CVE or security issue in general or bug or suggestion or fix or blocking or issue"

**Design:**
- Severity levels: critical, high, medium, low
- Critical: IRC immediately + board memory + task blocker
- High: IRC + board memory
- Medium: board memory only
- Low: board memory only (tagged for digest)

**Alert categories:**
- security: CVEs, exposed secrets, vulnerable deps, auth issues
- quality: missing tests, code smells, coverage gaps
- architecture: coupling, scaling, design debt
- workflow: broken automation, missing tooling
- suggestion: improvement ideas, missing capabilities

---

## Pause/Escalate Skill (M90)

**Purpose:** Agents know when to stop and how to escalate properly.

**Design:**
- Skill provides a decision tree:
  1. Am I stuck? → Post blocker, notify IRC, wait
  2. Is this high-risk? → Post for review, notify IRC, wait
  3. Do I need another agent? → Create proposed task, notify board memory
  4. Is this unclear? → Post question to board memory with @human tag
- Each path uses the right template and surface
- The skill PREVENTS agents from continuing when they should stop

---

## Gap Detection Skill (M91)

**Purpose:** Agents identify missing capabilities in the fleet.

> "we are missing an Agent X or Y or Z... lack this skill or that... lack this knowledge"

**Design:**
- Agents can invoke this when they notice something missing
- Outputs to board memory with tags [suggestion, gap, {area}]
- Categories:
  - Missing agent: "We need an agent specialized in X"
  - Missing skill: "There's no skill for Y, agents have to do it manually"
  - Missing knowledge: "No documentation about Z, agents keep re-discovering it"
  - Missing automation: "This manual step should be automated"
- Posts to IRC: `💡 [agent] GAP: {description}`

---

## Lead Agent Coordination Protocol (M90b)

> "we would probably need one agent that will keep order in all this"

**The lead agent is the fleet's coordinator.** It:
- Reviews proposed tasks and activates or rejects them
- Assigns unassigned tasks from the inbox
- Monitors task flow (stale tasks, blocked agents, review backlog)
- Posts daily digest to IRC and board memory
- Escalates to human when fleet is stuck
- Coordinates multi-agent work (architect → sw-eng → qa → writer)

**Implementation:** This is the Governance Agent (Phase F4). The protocol here defines
what it does. Phase F4 defines how to build it.

---

## Verification

- [ ] Communication decision matrix is in STANDARDS.md and agent SOUL.md
- [ ] Agents use the right surface for each situation (tested with real tasks)
- [ ] Follow-up tasks created by agents have proper references and tags
- [ ] Alerts posted to board memory AND IRC with correct severity
- [ ] Agents pause when they should (tested with ambiguous task)
- [ ] Gap detection produces actionable suggestions
- [ ] Board memory is ALIVE — multiple entries per day from different agents
- [ ] IRC has a steady stream of meaningful, actionable messages