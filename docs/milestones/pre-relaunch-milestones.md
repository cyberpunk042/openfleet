# Pre-Relaunch Milestones — What WE Must Fix Before the Fleet Can Work

## What This Document Is

The fleet is broken. We built 26 core modules, 13 MCP tools, 237 tests —
but the fleet still can't communicate, still doesn't follow its roles,
and still doesn't flow. This document covers everything WE need to fix
before relaunching the fleet to work on DSPD Sprint 3.

These are OUR milestones. Not the fleet's milestones. The fleet can't
create its own milestones until it can actually work.

After these are done, we create the FLEET milestones — where the PM
drives Scrum, assigns work properly, gives clear requirements to agents,
and the whole chain flows.

---

## User Requirements (Verbatim)

> "the fleet is just retard and no one is proactive and ready to work and
> nothing flow properly again because the agent dont have their role and
> follow them properly"

> "the heartbeat was important especially the software engineer and the
> project manager but also the others.... we need to do this right"

> "the project-manager will have to do a better job of assigning work and
> directing or giving requirements to the other agents"

> "it should also drive Scrum Master tasks or various time like any good one"

> "more than 2 blocking at the same time is technically almost impossible"

> "we need to do this right... This does not remove any of the rest we
> already need to fix"

---

## Part 1: Remaining Bug Fixes

### Bug 3: Chat Not Working End-to-End

**Status:** fleet_chat tool exists and MCP server sees it. But NO agent
has ever used it. We've never verified that:
- Agent A calls fleet_chat → message appears in board memory with chat tag
- Agent B calls fleet_read_context → sees the message in chat_messages
- Agent B responds via fleet_chat → Agent A sees response

**What must be done:**
1. Verify fleet_chat tool works by calling it from a test script
2. Verify fleet_read_context returns chat_messages
3. Verify @mention filtering works
4. Push updated HEARTBEAT.md to all agents (check chat FIRST)
5. Re-provision agents so they have the latest instructions
6. Observe: do agents actually use chat during their next heartbeat?

**Verification criteria:** Two agents exchange messages via fleet_chat
and both see each other's messages.

### Bug 5: Plane IaC — Research Headless Setup

**Status:** Plane god-mode task was completed by devops agent, but we
haven't verified what that actually means. Did the agent configure Plane
via scripts? Via the web UI? Did it work?

**What must be done:**
1. Check what the devops agent actually did for the god-mode task
2. Research Plane's Docker env vars for headless admin seeding
3. Research Plane's API for post-bootstrap configuration
4. Document the approach: what can be scripted vs what needs ONE manual step
5. Build scripts/configure-plane.sh skeleton (even if incomplete)

### Bug 7: Board Memory Pollution

**Status:** Board memory has merge notifications, heartbeat logs, cleanup
records — operational noise that buries decisions and chat.

**What must be done:**
1. Audit current board memory — categorize entries by type
2. Remove operational noise from board memory posting:
   - Sync daemon: stop posting merge notifications to board memory (IRC only)
   - Orchestrator: stop posting health reports to board memory (IRC only)
3. Board memory reserved for: decisions, alerts, chat, knowledge, suggestions
4. fleet_read_context filters out operational entries

### Bug 10: Verification Culture

**Status:** We keep claiming things are done without testing. Heartbeat
"fixed" 3 times. Chat "built" but never verified. Tools "added" but
agents can't see them.

**What must be done:**
1. Every fix gets a verification step — not "code changed" but "observed working"
2. For agent-facing changes: re-provision → observe agent behavior → confirm
3. For communication: post message → verify received → verify response
4. For orchestrator: restart daemon → observe next cycle → verify behavior
5. Document verification results in commit messages

---

## Part 2: Orchestrator and Event System

### PR1: Event-Driven Wake (MM1 from bugs doc)

**Status:** Heartbeat tasks removed (gateway wake instead). But the orchestrator
still only wakes agents on:
- Periodic heartbeat (idle drivers, 30 min)
- Pending reviews (fleet-ops, 5 min)

It does NOT wake agents on:
- Task assigned to them
- @mentioned in chat
- Review gate triggered
- PR comment on their work
- Domain-relevant event

**What must be done:**
1. When orchestrator dispatches a task → the agent is woken by dispatch
   (this already happens via _send_chat in dispatch.py — VERIFY it works)
2. When chat mentions an agent → orchestrator detects in change_detector →
   wakes that agent via gateway
3. When a review task's gate includes an agent → wake that agent
4. When a PR gets a comment → wake the agent who created the PR
5. Build the event → agent mapping (which events affect which agents)

### PR2: Agent Event Filtering (MM8 from bugs doc)

**Status:** Not started. Agents receive raw board memory but can't filter
events by relevance to their domain.

**What must be done:**
1. fleet_read_context includes events_for_me — filtered by agent capabilities
2. Events tagged with domains (security, architecture, testing, infra, etc.)
3. Agent's routing.py capabilities matched against event domains
4. Agent judges: respond/participate/ignore based on event relevance
5. This is how agents participate in discussions and decisions proactively

### PR3: Sprint Task Priority (MM5 from bugs doc)

**Status:** task_scoring.py exists but the orchestrator doesn't explicitly
prioritize sprint tasks over system tasks. And with heartbeat tasks gone,
this is less urgent — but still needed for when there's competing work.

**What must be done:**
1. Sprint tasks get bonus score in task_scoring
2. Orchestrator dispatches highest-scored task first (already does this)
3. Verify: when sprint task and non-sprint task compete, sprint wins

---

## Part 3: Agent Role Enforcement

### PR4: PM as Scrum Master

> "the project-manager will have to do a better job of assigning work and
> directing or giving requirements to the other agents"
> "it should also drive Scrum Master tasks"
> "more than 2 blocking at the same time is technically almost impossible"

**Status:** PM has CLAUDE.md and HEARTBEAT.md describing its role. But PM
doesn't actually:
- Break down epics into tasks with clear requirements
- Assign work with specific instructions (not just "do this")
- Track sprint progress and adjust priorities
- Identify blockers and resolve them (reassign, split, escalate)
- Ensure no more than 2 things are blocking simultaneously
- Run standup-style checks (who's doing what, who's blocked)
- Provide acceptance criteria so agents know when they're done

**What must be done:**
1. PM HEARTBEAT.md rewrite — Scrum Master duties:
   - Check sprint progress → identify what's blocking
   - If > 2 blockers → resolve (reassign, split, create unblock tasks)
   - For each inbox task: verify it has clear requirements and acceptance criteria
   - For each blocked task: create unblock action
   - Post sprint standup to chat (@all: who's doing what, who's blocked)
2. PM must use fleet_task_create with DETAILED descriptions:
   - Not "Configure workspace" but specific steps, expected outcome, acceptance criteria
   - Not just agent assignment but WHY this agent and what they need to know
3. PM reads board memory for context before creating tasks
4. PM responds to work requests in chat (ux-designer, devops asked and got nothing)

### PR5: Software Engineer Heartbeat — Active, Not Passive

> "the heartbeat was important especially the software engineer"

**Status:** Software engineer's HEARTBEAT.md says "check assignments, report
status, HEARTBEAT_OK if no work." This is passive. The sw-eng should be:
- Checking PRs they own for conflicts or comments
- Reading architecture decisions that affect their implementation
- Reviewing code from other engineers (code_reviewer secondary role)
- Participating in design discussions when they have implementation insight
- Checking if their completed work needs follow-up (tests added? docs updated?)

**What must be done:**
1. sw-eng HEARTBEAT.md rewrite — active participation:
   - Check chat for @mentions and questions
   - Check PRs for conflicts/comments
   - Read recent architecture decisions
   - Participate in design discussions with implementation perspective
   - Review recently completed work for loose ends
2. Similar active heartbeats for ALL worker agents — not just "check inbox"

### PR6: All Agents — Active Participation in Heartbeats

**Status:** Most agents have "check assignments, HEARTBEAT_OK" heartbeats.
This makes them passive executors, not team members.

**What each agent should do during heartbeat (beyond checking inbox):**

| Agent | Heartbeat Participation |
|-------|----------------------|
| architect | Read chat for design questions. Review recent implementations for drift. Post architecture observations. |
| software-engineer | Check PRs for conflicts/comments. Read design decisions. Offer implementation perspective. |
| qa-engineer | Check recently completed tasks for test gaps. Review test health. Flag flaky tests. |
| devops | Check infrastructure health. Monitor CI pipeline. Flag automation gaps. |
| devsecops-expert | Scan recent PRs for security. Check dependency updates. Monitor for CVEs. |
| technical-writer | Check for undocumented recent work. Review changelog accuracy. |
| ux-designer | Review CLI output and dashboards. Check accessibility. Propose improvements. |
| project-manager | Sprint standup. Blocker resolution. Work assignment. Backlog grooming. |
| fleet-ops | Review queue processing. Quality enforcement. Board health. |
| accountability-gen | Product roadmap check. NNRT progress. Create next milestone tasks. |

**What must be done:**
1. Rewrite ALL 10 HEARTBEAT.md files with active participation duties
2. Every heartbeat checks chat FIRST (fleet_chat responses)
3. Every heartbeat includes domain-specific proactive work
4. Push framework + reprovision after rewrite

---

## Part 4: Board Memory Cleanup

### PR7: Clean the Board Before Relaunch

**Status:** The MC board has 100+ tasks, most of which are done heartbeats,
done reviews, done sprints. The board is cluttered. New sprint work gets
buried.

**What must be done:**
1. Audit: how many tasks are done heartbeat/review tasks?
2. Consider: can done heartbeat/review tasks be archived or hidden?
3. Board memory: remove/archive operational noise entries
4. Ensure Sprint 3 tasks are clearly visible and prioritized
5. Clean up stale dependencies and orphaned tasks

---

## Part 5: Communication Verification Before Relaunch

### PR8: End-to-End Communication Test

Before relaunching the fleet:
1. **fleet_chat test**: Post a message, verify it appears in board memory with chat tag
2. **@mention test**: Post @architect message, verify architect sees it in context
3. **fleet_read_context test**: Call from an agent workspace, verify all 15 fields return
4. **IRC test**: Verify all 10 channels exist and receive messages
5. **ntfy test**: Publish to all 3 topics, verify human receives on device
6. **Reprovision test**: Push framework, verify agents have latest tools and instructions
7. **Dispatch test**: Create a task, assign agent, verify orchestrator dispatches it
8. **Review chain test**: Complete a task, verify fleet-ops reviews it

All 8 must pass before relaunching the fleet for Sprint 3.

---

## Part 6: After OUR Fixes — Fleet Milestones

Once communication works and agents follow their roles:

### Fleet Milestone F1: PM Drives Sprint 3 Properly
- PM evaluates each S3 task: clear requirements? acceptance criteria? right agent?
- PM adjusts task descriptions with specific instructions
- PM tracks blockers: never > 2 blocking simultaneously
- PM posts sprint standup to chat daily

### Fleet Milestone F2: Agents Communicate During Work
- Agents use fleet_chat to ask questions, share context, request help
- Agents read board memory before starting work
- Agents create follow-up tasks when they discover work outside scope
- Architecture discussions happen in chat, decisions recorded in memory

### Fleet Milestone F3: Review Chain With Quality
- fleet-ops reviews with reasoning (not rubber stamp)
- QA actually runs tests (not just marks as done)
- Architect reviews design tasks for coherence
- Rejected work comes back with specific feedback

### Fleet Milestone F4: Sprint 3 Completes With Quality
- All tasks done with tests passing
- All PRs merged without conflicts
- Plane configured via IaC scripts
- Documentation complete and accurate

---

## Priority Order

```
OUR FIXES (sequential, each verified before next):
  PR7  — Clean board before relaunch
  PR6  — Rewrite ALL heartbeats with active participation
  PR4  — PM as Scrum Master
  PR5  — Software engineer active heartbeat
  PR1  — Event-driven wake (dispatch → wake)
  Bug 3 — Verify chat end-to-end
  Bug 7 — Board memory hygiene
  Bug 5 — Plane IaC research
  PR8  — Full communication verification (8 checks)

THEN FLEET MILESTONES:
  F1 → F2 → F3 → F4
```

Estimated: 9 pre-relaunch tasks + 4 fleet milestones.
The fleet CANNOT work until OUR fixes are done and verified.