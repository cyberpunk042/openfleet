# Critical Bugs and Missing Work — 2026-03-28 Late Session

## Bug 0: CRITICAL — Fleet Drains Entire Usage Plan in Minutes

**Severity:** CRITICAL — costs real money, makes fleet unusable.

**Symptom:** With no work to do, the fleet burned through the user's entire
Claude Code usage plan in a few minutes. Agents cycling through heartbeats,
each heartbeat triggering a full Claude Code session that consumes tokens.

**Root cause (multiple layers):**

1. **Every gateway wake = full Claude Code session.** When the orchestrator
   calls `_send_chat(session_key, message)`, the gateway starts a Claude Code
   execution. Even if the agent has nothing to do, it still reads CLAUDE.md,
   HEARTBEAT.md, processes the message, calls tools, and responds. That's
   thousands of tokens per heartbeat per agent.

2. **10 agents × heartbeat every 30 min = 20 sessions/hour minimum.**
   Each session is ~5,000-20,000 tokens (read context, call tools, respond).
   That's 100,000-400,000 tokens/hour doing NOTHING.

3. **The gateway's own heartbeat system also cycles agents.** Independent of
   the orchestrator, the gateway triggers agent heartbeats based on
   `heartbeat_config.every: "10m"`. So agents get woken TWICE — by orchestrator
   AND by gateway. Double drain.

4. **No token budget awareness.** The orchestrator has no concept of cost.
   It wakes agents regardless of whether there's work, regardless of how
   many tokens have been consumed, regardless of the user's plan limits.

5. **Board was 90% noise.** 75 heartbeat tasks + 5 review tasks + 10 conflict
   tasks = 90 noise tasks out of 100. Every agent session processed this
   noise list, consuming tokens just to read garbage.

**What must happen:**

1. **Token budget system.** The orchestrator must track estimated token usage
   and stop waking agents when budget is exhausted. Hard daily limit.

2. **Gateway heartbeat interval must be LONG.** Default "10m" is insane for
   10 agents. Should be "60m" minimum, "120m" for workers.
   Change in openclaw.json AND per-agent heartbeat_config.

3. **Don't wake agents with no work.** The orchestrator already checks for
   assigned work before waking — but the GATEWAY heartbeat system doesn't.
   The gateway wakes agents on its own schedule regardless.

4. **Batch operations.** Instead of waking each agent individually, the
   orchestrator should batch: check all agents' state, determine who
   ACTUALLY needs waking (has work, has chat, has events), only wake those.

5. **Short heartbeat responses.** Agent HEARTBEAT.md should say: "If nothing
   needs attention, respond with just HEARTBEAT_OK — do NOT call tools,
   do NOT read context, just respond immediately." Minimize token usage
   for empty heartbeats.

6. **Usage monitoring.** Track tokens consumed per agent per session.
   Alert if usage exceeds threshold. Auto-stop if daily budget exceeded.

7. **Fleet OFF by default.** Daemons should NOT run continuously.
   Run orchestrator on-demand or on a very long interval (5+ min).
   Only wake agents when there's ACTUAL work.

**Immediate actions taken:**
- Fleet processes KILLED. No daemons running.
- Do NOT restart until all fixes verified.

---

## What The User Said (Verbatim)

> "the agents seems constantly blocked into a heartbeat sequence.... all at the
> same time taking all the space.... and the project doesn't seem to move forward.
> and no one is still using the chat system... wtf..... this fucking internal chat
> system is very important why is it not used?"

> "EVERYTHING IS LOCKED AGAIN AND NO ONE IS COMMUNICATING"

> "the fleet cannot work on a project management tool till it HASN'T LEARNED TO
> COMMUNICATE PROPERLY"

> "ITS IAC YOU FUCKING RETARD... ITS CONFIGURATION USING CONFIG FILES AND SCRIPTS"

> "I WANT MY 10 MAJOR BUGFIXES AND MY 7+ MISSING MILESTONES"

---

## Bug 1: Heartbeat Model Is Fundamentally Wrong

**Symptom:** The MC board is flooded with heartbeat tasks. All 10 agents get
heartbeats every few minutes. Sprint work gets buried under heartbeat noise.

**Root cause:** The orchestrator creates heartbeat TASKS on the MC board for
every agent. This is wrong on multiple levels:

1. **Don't create heartbeat tasks when an agent already has assigned work.**
   If a task is assigned to an agent, the agent should just WORK ON IT.
   The heartbeat for that agent is: check on your task, post progress,
   participate in discussions about it. NOT a separate heartbeat task.

2. **Heartbeats are for the OTHER things** — proactive communication,
   answering questions, participating in architecture discussions,
   reviewing UX proposals, checking board memory for relevant decisions,
   contributing to backlog management, and fulfilling their soul/role
   beyond just executing assigned tasks.

3. **Heartbeats should NOT be MC tasks.** They should be gateway-level
   wake calls. The gateway has `wake`, `chat.send(deliver=true)`,
   and the agent's `HEARTBEAT.md` tells them what to do.

4. **The orchestrator should wake agents based on EVENTS:**
   - Task assigned to agent → wake that agent
   - Agent tagged/mentioned in chat → wake that agent
   - Agent's review gate triggered → wake that agent
   - New decision in board memory relevant to agent's domain → wake
   - Question posted that matches agent's expertise → wake
   - No events for 30 minutes → periodic heartbeat (check in, participate)

**What a heartbeat actually IS:**
- NOT: "check if you have work"
- IS: "participate in the fleet — check chat, respond to discussions,
  review decisions, contribute opinions, check if your domain has open
  questions, filter events and judge if they need your participation,
  help with backlog management, proactive security scanning, etc."

**When an agent has an assigned task:**
- Don't send heartbeat — the agent is WORKING
- If the agent needs a nudge (stuck too long) → send a check-in wake,
  NOT a heartbeat task
- If someone @mentions the agent → wake them to respond,
  they'll context-switch from their task

**Fix needed:**
- Remove heartbeat task creation from orchestrator entirely
- Implement event-driven agent wake via gateway
- Wake triggers: task assigned, @mention, review gate, domain-relevant event
- Periodic heartbeat (30+ min) ONLY for idle agents with no assigned work
- Heartbeat via gateway wake, NOT MC task
- Agent HEARTBEAT.md describes what to do during heartbeat:
  check chat, check events, participate, contribute to discussions

---

## Bug 2: MCP Server Doesn't Reload Tools

**Symptom:** fleet_chat (tool #15) was added to tools.py but agents can't see it.
The MCP server process was started before fleet_chat existed.

**Root cause:** The OpenClaw gateway starts the MCP server process once at agent
provisioning. The process reads `tools.py` at startup and caches the tool list.
New tools added to `tools.py` are invisible until the MCP server process restarts.
There is no hot-reload mechanism.

**Impact:** Every time we add a new MCP tool, ALL agents are blind to it until
their MCP server is restarted. This means:
- fleet_chat (tool #15) — invisible
- fleet_notify_human (#14) — may be invisible depending on when server started
- Any tool added mid-session — invisible

**Fix needed:**
- Restart all agent MCP server processes after adding tools
- OR: implement MCP server restart in the gateway lifecycle
- OR: add a `fleet mcp restart` command that kills and restarts MCP processes
- Long-term: gateway should detect .mcp.json changes and hot-reload

---

## Bug 3: Internal Chat Not Used — Nobody Communicates

**Symptom:** The OCMC internal chat has 4 messages from 2 days ago. Agents
don't post to chat. Agent work requests go unanswered. No collaboration.

**Root causes (multiple):**
1. fleet_chat tool is invisible to agents (Bug 2)
2. Agents' HEARTBEAT.md doesn't mention checking or using chat (partially fixed
   for template but not pushed to all agent-specific heartbeats)
3. fleet_read_context doesn't surface chat messages prominently enough
4. No agent is instructed to RESPOND to chat messages from other agents
5. The PM doesn't respond to work requests in chat (ux-designer, devops asked)
6. Board memory "chat" tag isn't being used by the fleet tools that DO exist

**Fix needed:**
- Fix Bug 2 first (agents need the fleet_chat tool)
- ALL agent HEARTBEAT.md files: add "Check internal chat FIRST"
- PM HEARTBEAT.md: "Respond to work requests in chat, assign idle agents"
- fleet-ops HEARTBEAT.md: "Check chat for @lead messages"
- Push framework to all agent workspaces
- Re-provision agents so they pick up new tools
- fleet_read_context should show chat as the FIRST section, not buried

---

## Bug 4: Sprint Work Blocked — Orchestrator Doesn't React to Events

**Symptom:** Sprint 3 was loaded but tasks sit in inbox even when dependencies
are met. The orchestrator polls every 30 seconds but doesn't prioritize
sprint tasks over system noise.

**Root cause:** The orchestrator is a polling loop that treats all tasks equally.
It doesn't react to events. When a task completes and unblocks a dependency,
the orchestrator doesn't immediately dispatch the next task — it waits for
the next 30-second cycle. Meanwhile heartbeat tasks consume dispatch slots.

**What should happen:**
1. When a task moves to done → immediately check what it unblocks → dispatch
2. When a sprint is loaded → immediately dispatch all unblocked tasks
3. Sprint tasks always dispatched before system tasks
4. Event-driven: task.status_changed → orchestrator reacts immediately
5. Agent assignment → wake agent immediately (deliver=true)

**Fix needed:**
- Orchestrator reacts to change_detector results: if tasks unblocked → dispatch NOW
- Sprint tasks scored higher than system tasks in task_scoring
- Agent wake uses deliver=true for immediate dispatch (not polling)
- Consider: MC activity events or webhooks for real-time reaction

---

## Bug 5: Plane Configuration Can't Be Done by Agents Via Web Forms

**Symptom:** Sprint 3 task "god-mode setup" dispatched to devops. But Plane's
god-mode is a web form at http://localhost:8080/god-mode/. An AI agent
working in CLI can't fill out web forms.

**Root cause:** I assumed agents would configure Plane via the web UI. But the
user said clearly: "ITS IAC — configuration using config files and scripts."

**What should happen:** Plane configuration should be done via:
1. Plane's Docker environment variables (plane.env) — admin credentials, instance name
2. Plane's API after initial bootstrap — workspaces, projects, states, labels
3. A setup script (scripts/configure-plane.sh) that does everything via API
4. The god-mode setup may need to be done via API or environment variable seeding

**Fix needed:**
- Research if Plane supports headless admin setup via env vars or API
- If yes: script it in configure-plane.sh
- If no: document the ONE manual step (god-mode web form) and script everything after
- The Sprint 3 task descriptions need to reflect this — agents run scripts, not web forms

---

## Bug 6: Agent Framework Not Fully Pushed/Provisioned

**Symptom:** push-agent-framework.sh copies files to workspaces but agents
don't read them until their next session start. Running agents have stale
HEARTBEAT.md, STANDARDS.md, MC_WORKFLOW.md.

**Root cause:** The gateway starts agent sessions and they read workspace files
at session start. Pushing new files to the workspace doesn't trigger a re-read.
The agent continues with whatever it loaded at provisioning.

**Fix needed:**
- After pushing framework files, agents need to be re-provisioned
- OR: agents need to be explicitly re-started (session reset)
- Need a `fleet agents reprovision` command that:
  1. Pushes framework files
  2. Restarts MCP server processes
  3. Sends re-provision message to each agent via gateway

---

## Bug 7: Board Memory Pollution — Too Many Low-Value Entries

**Symptom:** Board memory has merge notifications, heartbeat logs, cleanup
records — low-value noise that buries important decisions and chat messages.

**Root cause:** Every fleet sync, every heartbeat completion, every PR merge
posts to board memory. There's no distinction between operational noise and
valuable knowledge.

**Fix needed:**
- Separate operational logs from knowledge memory
- Board memory should be for: decisions, alerts, knowledge, chat
- Merge notifications → IRC only (not board memory)
- Heartbeat results → IRC #agents only (not board memory)
- Cleanup records → log file only (not board memory)
- Implement memory categories with filtering

---

## Bug 8: Orchestrator Creates Too Many Review Tasks for Fleet-Ops

**Symptom:** fleet-ops is overwhelmed with "[review] Process N pending approvals"
tasks. Multiple review tasks created per cycle.

**Root cause:** The `_wake_lead_for_reviews` function creates a new review task
every 5 minutes if there are pending approvals. But fleet-ops takes time to
process each one, so they accumulate.

**Fix needed:**
- Never create a review task if fleet-ops already has one active
- Increase the review wake cooldown significantly (30+ minutes)
- OR: don't create review tasks at all — fleet-ops should check approvals
  during regular heartbeats, not via special review tasks

---

## Bug 9: No Agent Re-provisioning After Code Changes

**Symptom:** We add code (tools, heartbeats, skills) but agents never see it.
The fleet runs with stale configuration from hours ago.

**Root cause:** No mechanism to push changes to running agents. The workflow is:
1. Developer changes tools.py, heartbeats, skills
2. push-agent-framework.sh copies files to workspaces
3. But running agents don't re-read anything
4. MCP server doesn't reload
5. Agent keeps using old tools and old instructions

**Fix needed:**
- Build `fleet agents reprovision` command:
  1. Stop all agent MCP server processes
  2. Push framework files
  3. Update .claude/settings.json
  4. Restart MCP servers
  5. Send re-provision message to each agent via gateway
- Add to Makefile: `make agents-reprovision`
- Run this after ANY change to tools, heartbeats, or skills

---

## Bug 10: Fleet Doesn't Learn From Failures

**Symptom:** Same problems keep recurring. Heartbeat flooding happened before,
was "fixed", happened again. MCP tool visibility was identified early, never
properly fixed. Chat was built but never verified working.

**Root cause:** No feedback loop. When something breaks:
1. We patch it quickly
2. We claim it's done
3. We move to the next thing
4. The same issue comes back because the root cause wasn't fixed

**Fix needed:**
- Every fix needs verification (not just "code changed, committed")
- Regression tests for systemic issues
- fleet-ops should detect recurring problems and flag them
- Post-incident analysis: why did this happen, why wasn't it caught,
  what prevents it from happening again

---

## Missing Milestones

### MM1: Event-Driven Agent Wake System (Replace Task-Based Heartbeats)

Complete replacement of the task-based heartbeat system with event-driven
agent wake. Agents are woken by EVENTS, not by periodic task creation.

**Wake triggers (orchestrator detects and wakes):**

| Event | Who to Wake | Method |
|-------|------------|--------|
| Task assigned to agent | That agent | gateway wake (deliver=true) |
| Agent @mentioned in chat | That agent | gateway wake |
| Agent's review gate triggered | That agent (reviewer) | gateway wake |
| Task completed in agent's project | PM (sprint progress) | gateway wake |
| Security finding in agent's domain | devsecops-expert | gateway wake |
| Architecture decision posted | architect | gateway wake |
| Test failure detected | qa-engineer | gateway wake |
| Human responds to escalation | The agent who escalated | gateway wake |
| New Plane issue in agent's project | PM + relevant agent | gateway wake |
| PR comment on agent's PR | That agent | gateway wake |

**Periodic heartbeat (for idle agents only):**
- Agent with NO assigned tasks and NO recent events → heartbeat every 30 min
- Heartbeat via gateway `chat.send(deliver=true)` with HEARTBEAT.md context
- Agent checks: chat, board memory, domain events, backlog, discussions
- Agent participates: answers questions, reviews decisions, contributes opinions
- NOT a MC task — a session-level message

**What the orchestrator does differently:**
1. change_detector detects events each cycle
2. For each event: determine which agents are affected
3. Wake affected agents via gateway (not MC task)
4. Only create MC tasks for REAL assigned work
5. Heartbeat is a FALLBACK for agents with no events for 30+ min

**Sub-milestones:**
| # | Scope |
|---|-------|
| MM1a | Remove heartbeat task creation from orchestrator |
| MM1b | Implement gateway wake for event-driven agent activation |
| MM1c | Event → agent mapping (which events affect which agents) |
| MM1d | Tag/mention detection → wake mentioned agent |
| MM1e | Agent event filtering (agent judges which events need participation) |
| MM1f | Periodic heartbeat as fallback (30 min, gateway wake, not MC task) |
| MM1g | Agent HEARTBEAT.md: participation-focused (chat, decisions, domain events) |

### MM2: MCP Server Hot-Reload / Reprovision Command

Agents need to see new tools without full re-provisioning.
- `fleet agents reprovision` command
- Kills MCP server processes
- Pushes framework files
- Restarts MCP servers
- Gateway re-provision lifecycle

### MM3: Communication Verification End-to-End

Before ANY more feature work:
- Agent A posts fleet_chat → Agent B sees it in fleet_read_context
- Agent B responds → Agent A sees response
- fleet-ops sees @lead messages
- PM responds to work requests
- Verified with REAL running agents, not just code review

### MM4: Board Memory Hygiene — Separate Ops Logs From Knowledge

- Merge notifications → IRC only
- Heartbeat results → IRC #agents only
- Board memory reserved for: decisions, alerts, chat, knowledge
- Memory categories with filtering in fleet_read_context

### MM5: Sprint Work Priority Over System Tasks

- Sprint tasks dispatched BEFORE any system/heartbeat work
- System tasks (heartbeats, reviews) get lowest priority
- Orchestrator explicitly prioritizes sprint plan tasks
- Task scoring penalizes system/auto-created tasks

### MM6: Plane IaC Configuration Script

- Research Plane headless setup (env vars, API seeding)
- scripts/configure-plane.sh does everything via API
- God-mode: either env var seed or ONE documented manual step
- Everything else automated: workspace, projects, states, labels, API keys

### MM7: Agent Re-provisioning Pipeline

- push framework + restart MCP + re-provision = one command
- Triggered after any tool/heartbeat/skill change
- Verified: agent can see and use new tools after reprovision
- Added to CI/CD: tool changes trigger automatic reprovision

---

### MM8: Agent Event Filtering and Participation Judgment

> "we need also a way for them to filter events and have them look at them
> during their heartbeat and judge if it require participation"

Agents need to see a filtered event stream and decide what needs their attention.
During heartbeat or when woken, agents receive events and judge:
- Does this architecture decision affect my current work? → participate
- Is this security alert in my domain? → investigate
- Is this UX question something I can help with? → respond
- Is this backlog item something I should pick up? → volunteer
- Is this discussion relevant to my expertise? → contribute

**Design: Agent Event Feed**

Each agent gets a filtered event feed in fleet_read_context:
```
events_for_me: [
  {type: "chat_mention", from: "architect", content: "...", needs_response: true},
  {type: "decision", about: "API design", domain_match: 0.8, participation: "optional"},
  {type: "review_gate", task: "S3-2", my_role: "qa", action: "run tests"},
  {type: "backlog_item", title: "Add caching", matches_skill: true},
]
```

The agent reads this and decides what to act on. Not everything needs action —
some are informational (FYI a decision was made), some need response (someone
asked you a question), some are work (review gate triggered).

**Sub-milestones:**
| # | Scope |
|---|-------|
| MM8a | Event feed builder: filter board events by agent domain/expertise |
| MM8b | fleet_read_context includes filtered events_for_me |
| MM8c | Agent HEARTBEAT.md: judge events, participate where appropriate |
| MM8d | Tag system: agents can be tagged in board memory, tasks, chat |
| MM8e | Domain matching: events auto-tagged with domain → matched to agent capabilities |

---

## Priority Order

```
BUG FIXES (do these FIRST, in order):
  Bug 2: MCP server tool reload / reprovision → agents can see fleet_chat
  Bug 1: Heartbeat not-as-tasks (or at minimum stop flooding)
  Bug 3: Chat actually working end-to-end with running agents
  Bug 6: Framework push + reprovision pipeline
  Bug 4: Sprint tasks priority over system tasks
  Bug 8: Review task flooding
  Bug 7: Board memory hygiene
  Bug 5: Plane IaC approach (research + script)
  Bug 9: Reprovision after code changes
  Bug 10: Verification culture — test before claiming done

MISSING MILESTONES (after bugs fixed):
  MM1: Gateway heartbeat (proper fix for Bug 1)
  MM2: MCP hot-reload (proper fix for Bug 2)
  MM3: Communication verification (verify Bug 3 is actually fixed)
  MM4: Board memory hygiene (proper fix for Bug 7)
  MM5: Sprint priority (proper fix for Bug 4)
  MM6: Plane IaC (proper fix for Bug 5)
  MM7: Reprovision pipeline (proper fix for Bug 6 + Bug 9)
```

The fleet CANNOT work on Plane until it can communicate. Communication
means: agents see new tools, agents use chat, agents respond to each other,
sprint work takes priority over system noise.