# CATASTROPHIC: Fleet Drained 20% of Usage Plan in 5 Seconds

## Severity: CATASTROPHIC

This is the most critical bug in the fleet's history. The fleet consumed 20% of
the user's Claude Code plan in approximately 5 seconds while doing NO useful work.
The weekly budget is now critically low with 6 days until reset.

This happened while there was no real work to do — agents were idle, Sprint 3 was
mostly blocked, the board was 90% noise. Yet the fleet burned through tokens at
an alarming rate.

**This must be the #1 priority. Nothing else matters until this is investigated,
understood, and prevented permanently.**

---

## Part 1: User Report (Verbatim)

> "wtf is happening the agents are not working and they are draining all my usage"

> "20% of plan was gone in 5 seconds.... this is fucking highly serious"

> "we need a thorough investigation of everything and what happened when there are
> task and they are blocked or what else happens that create a cluster fuck of
> phantom operation that consume token to do dunno what..... void work? infinite
> parallel loop work?"

> "the fleet cp is also going to have to keep track of the plan usage in general
> and detect irregularities, detect 50%, detect 5% fast climb, 10% fast climb, etc,
> and 70% 80% and 90% and detect outage (official and non-official, potentially
> local trouble or really cloud issues or in between)"

> "we really need to avoid brainless loop and recursive chain that don't end and
> infinite loop or trying to take a task or work on something blocked and things
> like this. always with awareness of the session of the user and when it reset
> be logical and then announce when the work has started to resume and so on"

> "fleet-ops comes to my mind. the fleet program is supposed to be strong and smart
> and the fleet-ops has to observe and operate and report things or act on them.
> we need to be able to pause all the work or reduce the efforts and strategy like
> that strategic and driven by the user and circumstances"

> "stop minimizing what I said and the job of the agent... you need to think of
> them as real employees with real role that even when there is no tasks they can
> work unless there is really no recent work or events and there is no backlog or
> project backlog to go pull from. But do not forget for example that before a task
> is executed usually the project manager created it yeah but there was an analysis
> done before the official task(s)"

> "obviously this all start by finding the sources of this catastrophy.... so much
> money down the drain in such a fraction of seconds.... possibly not even agent
> but the fleet process themselves?"

> "there seem to be two budget and somehow the weekly budget which I never was before
> even on lower plan is getting close really fast and the reset is in 6 days....
> we need to track that properly and do our diagnosis and continuous tracking and
> analysis from the agent"

> "This is not in the scope but we will also look how to wise ourself through aicp
> and localai when its online especially for but that we will need to plan after all
> this and we will be basically able to pass through it first and it should only call
> claude when needed otherwise do mcp / tool calls and whatever"

> "DO not corrupt or minimize or compress my words. take them as is. and you will
> need to quote them into the new documents in order to achieve all this properly
> and not forget a single thing and so that we meet the requirements or above and
> deliver a great product / a great solution that will make the work even stronger
> and economic"

---

## Part 2: Investigation — What Happened

### 2.1 Timeline of Events

1. Fleet daemons running: sync (60s), monitor (300s), auth (120s), orchestrator (30s)
2. Orchestrator cycle every 30 seconds:
   - Security scan → ensure approvals → wake fleet-ops → dispatch tasks → parent eval → health check → heartbeats
3. Gateway ALSO cycling agent heartbeats independently (every 10 minutes per agent heartbeat_config)
4. Sprint 3 loaded: 10 tasks, 8 blocked, 1 unblocked (god-mode done), 1 epic
5. God-mode completed → s3-workspace unblocked → dispatched to devops
6. Devops works → completes → moves to review → fleet-ops woken for review
7. Meanwhile: ALL other agents have NO work but gateway keeps waking them

### 2.2 Sources of Token Drain

**Source 1: Gateway heartbeat system (INDEPENDENT of orchestrator)**

The OpenClaw gateway has its own heartbeat system:
```json
"heartbeat": {
  "every": "10m",
  "target": "last",
  "includeReasoning": false
}
```

Every 10 minutes, the gateway sends a heartbeat to EACH agent session.
Each heartbeat triggers a Claude Code execution:
- Reads CLAUDE.md, HEARTBEAT.md, STANDARDS.md, MC_WORKFLOW.md
- Processes the heartbeat message
- Calls fleet tools (fleet_read_context, fleet_agent_status)
- Generates a response
- All of this consumes tokens

10 agents × every 10 min = **60 heartbeat sessions per hour**.
Each session: estimated 5,000-20,000 tokens.
Total: **300,000 - 1,200,000 tokens/hour from gateway heartbeats alone.**

**Source 2: Orchestrator wake calls**

The orchestrator was sending `_send_chat(session_key, message)` to wake
PM and fleet-ops every 30 minutes. Each wake triggers a full session.
This is ON TOP of the gateway heartbeats.

**Source 3: Possible infinite loop / rapid cycling**

> "possibly not even agent but the fleet process themselves?"

The orchestrator runs every 30 seconds. If the orchestrator's dispatch
or wake logic had a condition that kept triggering (e.g., detecting the same
unblocked task but failing to dispatch it, then retrying next cycle), it
could create rapid-fire wake calls.

INVESTIGATION NEEDED:
- Was the orchestrator calling `_send_chat` multiple times per cycle?
- Was the dispatch failing silently, causing retry on next cycle?
- Were there race conditions between orchestrator and gateway heartbeats?
- Was the same agent being woken by BOTH orchestrator and gateway simultaneously?

**Source 4: Agent sessions doing void work**

When an agent is woken with nothing to do:
- It reads context (tool calls → tokens)
- It reads board memory (tool calls → tokens)
- It finds no work
- It responds "HEARTBEAT_OK"
- All of this cost tokens for ZERO useful output

With a board that's 90% noise (75 heartbeat tasks, 5 review tasks, 10 conflict
tasks), just reading the task list consumes significant tokens.

**Source 5: The 30-second orchestrator cycle itself**

The orchestrator makes MC API calls every 30 seconds:
- list_tasks (fetches all 100 tasks)
- list_agents (fetches all 11 agents)
- list_approvals (fetches all approvals)
- These are HTTP calls, not token-consuming — BUT if the orchestrator was
  triggering agent wakes on each cycle, that's wake calls every 30 seconds.

### 2.3 Hard Evidence From Logs

**MCP server starts today: 2,123**
Each MCP server start = an agent session = token consumption.
2,123 sessions × minimum 1,000 tokens = **2+ million tokens minimum today.**

**Gateway heartbeat cycles logged: 9**
Each cycle fires heartbeats for ALL 11 agents with heartbeat config.
9 cycles × 11 agents = 99 sessions from heartbeats alone.

**Gateway restarts: 4**
Each restart re-initializes ALL heartbeat timers — so immediately after
restart, ALL agents get heartbeated simultaneously. 4 restarts × 11 agents
= 44 simultaneous sessions in bursts.

**Edit failures: 12**
Agents failing to edit MEMORY.md repeatedly — each failure consumes tokens
on the attempt, then retries, consuming more tokens.

**22 agents in gateway config — DUPLICATES**
Every agent appears TWICE:
- Once from initial registration (no heartbeat config)
- Once from MC provisioning (heartbeat.every=10m)
This means the gateway manages 22 agent entries, 11 with active heartbeats.

### 2.4 Why It Happened So Fast

> "20% of plan was gone in 5 seconds"

The 2,123 MCP server starts prove this wasn't just heartbeats. Something
caused a BURST of agent sessions. Possible causes:

1. **Gateway restart fires ALL heartbeats simultaneously.** After each of
   the 4 restarts, all 11 agents get heartbeated at once = 11 parallel
   Claude Code sessions consuming tokens simultaneously.

2. **Orchestrator dispatch + gateway heartbeat overlapping.** The orchestrator
   dispatched tasks via `_send_chat` while the gateway was ALSO firing
   heartbeats for the same agents. Double sessions for the same agents.

3. **MCP server respawning rapidly.** 2,123 MCP starts in one day is
   ~88 per hour or ~1.5 per minute. If these cluster (which they do
   around gateway restarts), that's dozens of sessions in seconds.

4. **Agent sessions triggering MORE agent sessions.** When fleet-ops
   reviews a task, it calls fleet_task_create which creates MC tasks,
   which triggers MC activity events, which could trigger more agent wakes.
   Cascading effect.

5. **The orchestrator _send_chat calls might have been firing every 30
   seconds** (the orchestrator cycle) if the wake conditions were always met
   (e.g., always detecting pending reviews, always detecting idle drivers).

### 2.5 THE ACTUAL ROOT CAUSE

**Normal heartbeats (15-60 min) are fine and expected.** The problem is NOT
the heartbeat interval. The problem is that code changes in commit `9ed54b3`
introduced `_send_chat` calls into the orchestrator that create uncontrolled
Claude Code sessions. Combined with multiple gateway processes still running,
this created a runaway token drain.

**What changed in commit `9ed54b3`:**
- `_lifecycle_heartbeats` rewritten to call `_send_chat(session_key, message)`
- `_wake_lead_for_reviews` rewritten to call `_send_chat`
- Every `_send_chat` = WebSocket to gateway = gateway spawns Claude Code session
- The orchestrator runs every 30 seconds
- Module-level globals (`_last_review_wake`, `_fleet_lifecycle`) RESET on process restart
- On fresh start: `_last_review_wake is None` → immediately triggers `_send_chat`
- There are ALWAYS review tasks on board → fleet-ops woken EVERY restart

**The cascade:**
1. Daemon starts → first orchestrator cycle
2. `_last_review_wake` is None → `_send_chat` to fleet-ops (Claude Code session spawned)
3. `_lifecycle_heartbeats` checks PM and fleet-ops → `_send_chat` to both (2 more sessions)
4. 30 seconds later → next cycle → conditions may still trigger → more sessions
5. Gateway ALSO fires its own heartbeats independently → more sessions on top
6. Each session spawns MCP server → reads all tools → consumes tokens just starting
7. **2,123 MCP server starts in one day = 2,123 token-consuming sessions**

**The second drain (when user thought agents were "down"):**
- User killed fleet daemon processes → our code stopped
- BUT: OpenClaw gateway (PID 8761) was STILL RUNNING
- AND: a stale gateway from March 26 (PID 17858) was ALSO running
- Gateway fires heartbeats independently → spawns Claude Code sessions
- Reprovision script killed MCP servers → gateway auto-respawned them
- **The gateway is autonomous — killing our code doesn't stop it**

**The fundamental problem:**
ANY process that calls the gateway creates Claude Code sessions that consume
tokens. The gateway, the orchestrator's `_send_chat`, the dispatch function —
all of them. There is ZERO rate limiting, ZERO token budget awareness, ZERO
circuit breaker anywhere in the chain. A single bad condition in the
orchestrator can trigger unlimited sessions in rapid succession.

### 2.6 The Two Budget Problem

> "there seem to be two budget and somehow the weekly budget which I never was
> before even on lower plan is getting close really fast"

Claude Code has:
- **Daily budget**: tokens per day
- **Weekly budget**: tokens per week (rolling)
- The fleet was consuming from BOTH simultaneously
- Weekly budget is harder to recover from (6 day reset)

---

## Part 3: Required Fixes (Priority Order)

### FIX 0: REVERT — Orchestrator Must NOT Call _send_chat

**The commit `9ed54b3` introduced `_send_chat` calls in the orchestrator.**
This was the catastrophic mistake. `_send_chat` bypasses all gateway controls
and directly spawns Claude Code sessions. The orchestrator ran every 30 seconds
and could trigger unlimited sessions.

**REVERT to MC task creation for heartbeats and reviews.**
MC task creation is CHEAP (one HTTP POST, no tokens consumed).
The gateway then controls when the agent actually runs.
The gateway has its own heartbeat system and rate controls.
We should work WITH the gateway, not bypass it.

**The orchestrator should NEVER call `_send_chat` or any function that
directly triggers Claude Code sessions.** Only the dispatch function should
do that, and only when explicitly dispatching a real task.

**Fix:**
1. Revert `_lifecycle_heartbeats` to create MC tasks (or remove entirely
   and let gateway heartbeats handle it)
2. Revert `_wake_lead_for_reviews` to create MC tasks (or remove entirely)
3. Add a HARD RULE in orchestrator: no `_send_chat` imports, no gateway calls
4. Add guard: track number of sessions spawned per hour, hard-stop at threshold

### FIX 0b: Gateway Process Cleanup

**The single most impactful fix.** The gateway config has 22 agents (duplicates)
all heartbeating at 10-minute intervals independently of our orchestrator.

**Problem 1: 22 agents, should be 11**
Every agent appears twice in `~/.openclaw/openclaw.json`:
- Once from `scripts/register-agents.sh` (id: agent-name, no heartbeat)
- Once from MC provisioning (id: mc-UUID, heartbeat: 10m)
The duplicates must be removed. Only the MC-provisioned versions should remain.

**Problem 2: heartbeat.every=10m is far too aggressive**
10 minutes × 11 agents = 66 sessions/hour of pure overhead.
The gateway heartbeat should be the FALLBACK, not the primary driver.
When the fleet has work, the orchestrator dispatches explicitly.
When idle, heartbeats should be rare (60m minimum, 480m when sleeping).

**Problem 3: Gateway restarts fire ALL heartbeats simultaneously**
Each of the 4 gateway restarts today triggered 11 parallel sessions.
This is the burst that caused the 5-second 20% drain.

**Fix:**
1. Remove duplicate agents from openclaw.json (keep only mc-UUID versions)
2. Set heartbeat.every to "never" or "480m" for all agents
3. The fleet orchestrator controls when agents wake (via dispatch + events)
4. Gateway heartbeat becomes emergency-only fallback
5. Script this cleanup in scripts/configure-gateway.sh for reproducibility
6. Add guard: if gateway restarts, DON'T fire all heartbeats immediately —
   stagger them or skip the first cycle

### FIX 1: Fleet Pause / Kill Switch

> "we need to be able to pause all the work or reduce the efforts"

Build `fleet pause` and `fleet resume` commands:
- `fleet pause` → stops all daemons, sets gateway heartbeat to "never",
  posts to IRC/ntfy "Fleet paused by human"
- `fleet resume` → restarts daemons, restores heartbeat intervals
- `fleet pause --reason "budget conservation"` with reason tracking

### FIX 2: Token Budget Awareness and Monitoring

> "the fleet cp is also going to have to keep track of the plan usage"
> "detect irregularities, detect 50%, detect 5% fast climb, 10% fast climb"

Build fleet/core/budget_monitor.py:
- Track estimated token usage per agent session
- Alert thresholds: 5% fast climb, 10% fast climb, 50%, 70%, 80%, 90%
- Auto-pause fleet when threshold exceeded
- ntfy URGENT notification on budget alerts
- Daily/weekly budget reporting
- Detect anomalies: if usage rate exceeds historical average by 3x → pause

### FIX 3: Prevent Infinite Loops and Void Work

> "avoid brainless loop and recursive chain that don't end"
> "infinite loop or trying to take a task or work on something blocked"

Safeguards in the orchestrator:
- **Dispatch guard**: if dispatch fails for a task, mark it with a retry count.
  After 3 failures, skip it and alert.
- **Wake guard**: track wake calls per agent per hour. If > 3 wakes/hour for
  an agent with no work → stop waking that agent.
- **Blocked task guard**: NEVER try to dispatch blocked tasks. Check is_blocked
  before ANY dispatch attempt.
- **Session guard**: if an agent session runs for > 5 minutes with no tool calls
  → something is wrong → abort session.
- **Cycle guard**: orchestrator tracks actions per cycle. If a cycle has 0 actions
  for 5 consecutive cycles → reduce check frequency to 5 minutes.

### FIX 4: Short-Circuit Heartbeats

When an agent is woken for a heartbeat and has NOTHING to do:
- Agent should respond with "HEARTBEAT_OK" immediately
- Do NOT call fleet_read_context (costs tokens to fetch context)
- Do NOT call fleet_agent_status (costs tokens)
- Just check: any assigned tasks? No → HEARTBEAT_OK. Done.
- This minimizes token usage for empty heartbeats

HEARTBEAT.md should say:
```
FIRST: Do you have assigned tasks or chat messages?
  If NO and nothing in your domain needs attention: respond HEARTBEAT_OK immediately.
  Do NOT call any tools. Do NOT read context. Just respond.
  If YES: then read context and proceed with your heartbeat duties.
```

### FIX 5: Fleet-Ops as Budget Guardian

> "fleet-ops has to observe and operate and report things or act on them"

Fleet-ops should monitor:
- Token usage trends
- Agent session frequency and duration
- Void sessions (sessions with no useful output)
- Auto-pause recommendation when usage is abnormal

### FIX 6: Outage and Reset Detection

> "detect outage (official and non-official, potentially local trouble or
> really cloud issues or in between)"
> "awareness of the session of the user and when it reset"

The fleet needs to know:
- When the weekly/daily budget resets
- Current usage level (if API provides it)
- When rate limits are hit → back off, don't keep hammering
- When API is down → pause operations, notify human
- When budget resets → announce "Budget reset, work can resume"

### FIX 7: Effort and Strategy Control

> "reduce the efforts and strategy like that strategic and driven by the
> user and circumstances"

Build configurable effort profiles:
- **Full**: all agents active, normal heartbeats, opus for complex tasks
- **Conservative**: only drivers active, long heartbeats, sonnet only
- **Minimal**: only fleet-ops monitoring, no heartbeats, emergency only
- **Paused**: nothing runs, gateway heartbeats off

Human selects profile via `fleet effort conservative` or config.

---

## Part 3b: Deeper Design Flaws

### Design Flaw 1: Why Pass Through Claude to Call a Tool You Can Call Directly?

> "why pass through claude to call a tool when you can call it directly?
> it make no sense"

The fleet's MCP tools (fleet_read_context, fleet_agent_status, etc.) are
HTTP calls to the MC API wrapped in Claude Code tool handlers. When the
ORCHESTRATOR needs to check task status, it calls `mc.list_tasks()` directly
— that's a cheap HTTP call, no tokens.

But when an AGENT needs to check task status, it calls `fleet_read_context()`
which runs inside a Claude Code session consuming tokens just to make the
same HTTP call.

**The problem:** Agent heartbeats call fleet_read_context + fleet_agent_status
+ fleet_chat = 3 tool calls inside a Claude session = thousands of tokens
for what is essentially 3 HTTP requests.

**What should happen:**
- The orchestrator calls MC API directly (it already does — this is correct)
- Agent heartbeats should be MINIMAL — if there's nothing to do, don't call tools
- For routine checks (is there work for me?), the orchestrator should PRE-CHECK
  and only wake the agent if there IS something for them
- The agent should never be woken just to call fleet_agent_status and say
  "nothing to do" — that's wasting tokens on a question the orchestrator
  already knows the answer to

### Design Flaw 2: Why Call 5 Tools When a Chain Does It All?

> "And when call 5 tools when you can just call a chain that does it all?
> it a mix of communication and logic and pragmatism"

An agent heartbeat currently does:
1. `fleet_read_context()` — fetch task, memory, chat (API calls + tokens)
2. `fleet_agent_status()` — fetch agents, tasks, approvals (more API calls + tokens)
3. Read results, think about them (tokens for reasoning)
4. `fleet_chat("HEARTBEAT_OK")` — post to memory (API call + tokens)
5. Respond with summary (more tokens)

That's 5 tool calls + reasoning for what could be ONE optimized operation.

**What should happen:**
- A single `fleet_heartbeat()` tool that does everything in one call:
  checks assigned tasks, checks chat, checks events, returns a summary
- The agent reads the summary and only acts if something needs attention
- OR better: the orchestrator pre-computes the heartbeat context and sends
  it WITH the wake message, so the agent doesn't need to call any tools
  just to learn there's nothing to do

### Design Flaw 3: Events That Trigger Agents Are Not ALL Events

> "events that trigger agent are not all events and the reason we have
> heartbeat is to avoid uncontrolled loop"

The heartbeat IS the controlled rhythm. It prevents uncontrolled loops by
ensuring agents only check in at fixed intervals. The catastrophic bug was
BYPASSING this rhythm by calling `_send_chat` directly, which created
sessions outside the heartbeat cycle.

**Rules for event-driven waking:**
- Task assigned to agent → wake (this is dispatch, controlled by orchestrator)
- Agent @mentioned in chat → wake at NEXT heartbeat (not immediately)
- Review gate triggered → wake at NEXT heartbeat
- Sprint milestone → notification only (ntfy), not agent wake
- Task completed by another agent → orchestrator checks deps, dispatches if needed
- Board memory posted → do NOT wake anyone (they'll see it at next heartbeat)

**The heartbeat is the ONLY rhythm.** Everything else either:
1. Waits for the next heartbeat (non-urgent)
2. Goes through dispatch (urgent, controlled, one-time)
3. Goes to notification (ntfy/IRC, no token cost)

There must NEVER be a code path that creates Claude Code sessions outside
of dispatch (for real tasks) and heartbeat (on the gateway's controlled timer).

### Design Flaw 4: Cascade Prevention

> "we really need to avoid brainless loop and recursive chain that don't
> end and infinite loop"

Cascades happen when:
- Agent A completes task → creates follow-up task for Agent B
- Agent B gets woken → completes → creates task for Agent C
- Agent C → Agent D → ... infinite chain

**Prevention:**
- Auto-created tasks do NOT trigger immediate dispatch
- They go to inbox and wait for the NEXT orchestrator cycle
- The orchestrator has a max-dispatch-per-cycle limit (e.g., 3)
- If more than 3 tasks are ready, dispatch 3 and wait for next cycle
- The orchestrator tracks chain depth — if a task was auto-created by an
  agent that was auto-created by another agent → alert, don't dispatch
- Maximum chain depth: 3 levels (human → PM → agent → subtask). Beyond
  that requires human approval.

---

## Part 3c: Complete Bug List (10+)

1. **Orchestrator called _send_chat directly** — bypassed gateway controls,
   created unlimited Claude Code sessions every 30 seconds
2. **Gateway has 22 duplicate agents** — 11 extra entries from initial registration,
   doubling heartbeat targets
3. **Stale gateway processes** — old gateway from March 26 still running,
   independently cycling agents
4. **Module globals reset on restart** — `_last_review_wake` resets to None,
   triggering immediate wake on every daemon restart
5. **No session rate limiting** — nothing prevents 100 sessions/minute
6. **No token budget awareness** — fleet has no concept of cost
7. **Agent heartbeats call unnecessary tools** — fleet_read_context +
   fleet_agent_status just to say "nothing to do" = wasted tokens
8. **No cascade depth limit** — agent-created tasks can trigger infinite chains
9. **No max-dispatch-per-cycle** — orchestrator can dispatch ALL unblocked tasks
   in one cycle, spawning 10 sessions simultaneously
10. **fleet_task_complete calls fleet_read_context internally** — nested tool calls
    inside tool calls, doubling token usage
11. **Board has 90% noise tasks** — reading task list costs tokens proportional
    to list size; 90 noise tasks = 90% wasted context
12. **Gateway restart fires ALL heartbeats immediately** — no stagger, no warmup,
    11 parallel sessions at once
13. **No fleet pause command** — can't stop the drain without killing processes
14. **No outage/rate-limit detection** — fleet keeps hammering when API is throttled
15. **Orchestrator creates review/heartbeat MC tasks that consume agent sessions
    to process** — even "cheap" MC tasks trigger agent sessions when dispatched

---

## Part 4: Agent Role Reality Check

> "think of them as real employees with real role that even when there is no
> tasks they can work unless there is really no recent work or events and
> there is no backlog or project backlog to go pull from"

> "before a task is executed usually the project manager created it yeah but
> there was an analysis done before the official task(s)"

Agents are not just task executors. They are:

**Project Manager:**
- Analyzes work BEFORE creating tasks
- Does requirements gathering, scope definition
- Creates tasks with clear acceptance criteria
- Drives Scrum: standup, retrospective, sprint planning
- Resolves blockers proactively (never > 2 simultaneously)
- Assigns work based on capability AND current workload
- Tracks velocity and adjusts pace

**Software Engineer:**
- Reads architecture decisions before implementing
- Participates in design discussions with implementation perspective
- Reviews own work for loose ends (tests? docs?)
- Checks PRs for conflicts and reviewer comments
- Helps other engineers when they're stuck
- Pulls from backlog when idle (doesn't just say "no work")

**Architect:**
- Reviews implementations for architectural drift
- Participates in discussions about patterns and approaches
- Posts observations and recommendations proactively
- Helps PM break down complex work into implementable tasks

**QA Engineer:**
- Checks test health proactively (flaky tests, coverage gaps)
- Reviews recently completed code for test adequacy
- Runs tests before anyone asks (proactive quality)
- Creates test infrastructure tasks when needed

**fleet-ops:**
- Monitors everything: budget, usage, agent health, board state
- Acts on anomalies (not just reports them)
- Pauses fleet when something is wrong
- Quality gate for all completed work

**Cyberpunk-Zero:**
- Scans PRs proactively for security
- Monitors dependencies for CVEs
- Reviews infrastructure changes
- Behavioral analysis of agent output

**All agents:**
- Check chat and respond to teammates
- Read decisions and participate in discussions
- Pull work from backlog when idle (with PM's guidance)
- Create follow-up tasks when they discover work
- Never sit idle without telling lead

---

## Part 5: Future — AICP and LocalAI Integration

> "we will also look how to wise ourself through aicp and localai when its
> online especially for but that we will need to plan after all this and we
> will be basically able to pass through it first and it should only call
> claude when needed otherwise do mcp / tool calls and whatever"

This is a future milestone but important to note:
- AICP + LocalAI can handle routine operations without Claude tokens
- MCP tool calls through LocalAI for: fleet_read_context, fleet_agent_status
- Only escalate to Claude for: complex reasoning, code generation, design
- This dramatically reduces Claude token usage
- Will be a major epic in DSPD/Plane once the fleet is stable

---

## Part 6: Milestone Summary

### CRITICAL (before ANY fleet restart):

| # | Milestone | Bugs Fixed |
|---|-----------|-----------|
| C0 | REVERT orchestrator _send_chat calls — no direct session creation | Bug 1, 4, 9 |
| C1 | Clean gateway config — remove 11 duplicate agents | Bug 2 |
| C2 | Kill stale gateway processes — script to detect and clean | Bug 3 |
| C3 | Build fleet pause/resume — kill switch for the fleet | Bug 13 |
| C4 | Session rate limiter — max N sessions per hour, hard stop | Bug 5, 9 |
| C5 | Token budget monitor — track usage, alert thresholds, auto-pause | Bug 6 |
| C6 | Max dispatch per cycle — orchestrator dispatches max 3 per cycle | Bug 8, 9 |
| C7 | Cascade depth limit — max 3 levels of auto-created tasks | Bug 8 |

### HIGH (safety and efficiency):

| # | Milestone | Bugs Fixed |
|---|-----------|-----------|
| C8 | Optimized heartbeat — fleet_heartbeat single tool OR pre-computed context | Bug 7, Design 1+2 |
| C9 | Event filtering — only relevant events wake agents, rest waits for heartbeat | Design 3 |
| C10 | Board cleanup — remove 90 noise tasks before relaunch | Bug 11 |
| C11 | Gateway restart stagger — don't fire all heartbeats simultaneously | Bug 12 |
| C12 | Outage and rate-limit detection — back off when throttled | Bug 14 |
| C13 | Effort profiles — full/conservative/minimal/paused | FIX 7 |
| C14 | fleet-ops as budget guardian — monitor usage, detect anomalies | FIX 5 |

### After fleet is safe to restart:

| # | Milestone | Priority |
|---|-----------|----------|
| C9 | All agent heartbeats rewritten (active participation) | HIGH |
| C10 | Board cleanup (remove 90 noise tasks) | HIGH |
| C11 | Chat verification end-to-end | HIGH |
| C12 | PM as Scrum Master (proper task management) | HIGH |
| C13 | Communication 8-point verification | HIGH |
| C14 | Sprint 3 relaunch with proper flow | MEDIUM |

### Future (after fleet stable):

| # | Milestone | Priority |
|---|-----------|----------|
| C15 | AICP + LocalAI integration planning | FUTURE |
| C16 | Token optimization via local inference | FUTURE |
| C17 | DSPD/Plane epic for fleet economics | FUTURE |

---

## Part 7: What We Need to Deliver

> "deliver a great product / a great solution that will make the work even
> stronger and economic"

The fleet must be:
1. **Safe** — never drain budget, auto-pause on anomalies
2. **Smart** — only consume tokens when there's actual work
3. **Economic** — minimize token usage for overhead, maximize for real work
4. **Observable** — budget tracking, usage reporting, anomaly detection
5. **Controllable** — pause/resume, effort profiles, human override
6. **Productive** — agents follow roles, communicate, flow work properly
7. **Sustainable** — works within budget indefinitely, not in bursts