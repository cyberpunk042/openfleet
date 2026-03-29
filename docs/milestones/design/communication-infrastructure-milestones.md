# Communication Infrastructure Milestones — Full Investigation and Planning

## What This Document Covers

A thorough investigation of the fleet's communication state, what's broken,
what's missing, and what needs to be built before Plane integration.
This is prerequisite work — DSPD can't scale without proper communication
infrastructure.

---

## Part 1: Current State Investigation

### 1.1 OCMC Internal Chat — Nearly Dead

> The user sees the OCMC board chat with only 4 messages from Mar 27-28.
> Agents post to board memory but NOT to the internal chat.
> ux-designer and devops posted idle messages but nobody responded.

**What the internal chat IS in OCMC:**
- It's the board-level chat visible in the MC dashboard
- Messages are stored as board memory entries tagged with `chat`
- The "lead" agent sees messages addressed to `@lead`
- Other agents see messages tagged with `@their-name`

**What's broken:**
1. Agents don't post to internal chat — they use board memory without `chat` tag
2. fleet_read_context doesn't surface chat messages specifically
3. No agent has instructions to check or respond to internal chat
4. The `@lead` and `@agent-name` mention system isn't implemented in fleet tools
5. Agents requesting work (ux-designer, devops) get no response because nobody
   monitors the chat
6. There's no `fleet_chat` MCP tool — agents can't post to internal chat natively

**What needs to happen:**
- New MCP tool: `fleet_chat(message, mention="")` — posts to internal chat
- fleet_read_context surfaces recent chat messages (not just board memory)
- fleet-ops (board lead) monitors chat and responds to `@lead` mentions
- PM monitors chat for work requests and assigns agents
- All agents check chat during heartbeat
- @mention routing: `@devops` → devops agent gets notified

### 1.2 IRC Channels — Only 3, Need 7+

**Current:**
| Channel | Purpose | Activity |
|---------|---------|----------|
| #fleet | General fleet activity | Active (dispatch, completion, merge notifications) |
| #alerts | Critical alerts | Active (security, infrastructure) |
| #reviews | PR review notifications | Some activity |

**What's missing:**
| Channel | Purpose | Why Needed |
|---------|---------|-----------|
| #sprint | Sprint progress, velocity updates, milestone alerts | PM needs dedicated sprint visibility |
| #agents | Agent status changes, heartbeat summaries, sleep/wake | fleet-ops needs agent health channel |
| #security | Security findings, CVE alerts, behavioral security holds | Cyberpunk-Zero needs dedicated security channel |
| #human | Human directives, escalations requiring response, decisions needed | Human needs ONE place for things needing attention |
| #builds | CI/CD, test results, build status | devops + qa-engineer build monitoring |
| #memory | Board memory highlights, important decisions, knowledge sharing | Fleet-wide awareness |
| #plane | Plane sync activity, sprint management, cross-project deps (future) | DSPD integration channel |

**IRC channel design principles:**
- Each channel has a clear purpose (no "dump everything in #fleet")
- Agents post to the RIGHT channel (routing in irc.py template)
- Human subscribes to channels they care about (#human always, #sprint for project, #security for awareness)
- The Lounge gives persistent history for all channels

### 1.3 ntfy — Topics Configured but Unused

**Current state:**
- ntfy at http://192.168.40.11:10222 is running and reachable
- 3 topics configured: fleet-progress, fleet-review, fleet-alert
- `fleet_notify_human` MCP tool exists
- Orchestrator has `_notify_human` helper
- **ZERO notifications have been sent.** The user never received anything.

**Why no notifications:**
1. The NtfyClient is built but the orchestrator's `_notify_human` only fires on
   parent task completion (sprint milestones) — Sprint 2 hasn't completed a parent yet
2. `fleet_escalate` sends ntfy but no agent has escalated this session
3. The sync daemon sends ntfy on PR close by human, but that just happened
4. Nobody subscribes the user to the topics — user doesn't know which topics to watch

**What needs to happen:**
- User subscribes to: `fleet-progress`, `fleet-review`, `fleet-alert` on ntfy app/web
- More events should trigger ntfy notifications:
  - Sprint task completed → fleet-progress
  - PR merged → fleet-progress
  - Agent stuck or offline → fleet-review
  - Daily digest ready → fleet-progress
  - Agent requesting work → fleet-progress
  - Security finding → fleet-alert
- Orchestrator should send periodic summary via ntfy (not just milestone events)

### 1.4 Windows Notifications — Not Installed

`wsl-notify-send` is NOT installed. No Windows toast notifications work.

**Options:**
1. Install `wsl-notify-send`: `sudo apt install wsl-notify-send` (if available)
2. Use PowerShell BurntToast: `powershell.exe -Command "New-BurntToastNotification ..."`
3. Use ntfy desktop app on Windows (ntfy has a Windows client)
4. Use ntfy web notifications (browser push notifications from ntfy web UI)

**Recommendation:** Option 4 is easiest — open ntfy web UI at http://192.168.40.11:10222
in a browser and subscribe to topics. Browser push notifications work without installing
anything.

### 1.5 What Agents See vs What They Should See

**Current agent session start (fleet_read_context returns):**
- Task details (title, status, description)
- Project URLs
- Recent board memory (5 entries, 300 chars each)
- Recent decisions (tagged "decision")
- Active alerts (tagged "alert")
- Escalations (tagged "escalation")
- Team activity (who's working on what)
- Task hierarchy (parent, siblings)

**What's MISSING from agent context:**
- Internal chat messages addressed to them (`@agent-name`)
- Work requests from other agents
- Human directives posted in chat
- Sprint context (which sprint is active, what's the deadline, velocity)
- Their own recent history (what they did last session — memory)
- Security holds on any tasks they're involved with
- PR status for tasks they're working on (conflicts, comments)

---

## Part 2: Communication Architecture for DSPD/Plane

### 2.1 How Communication Should Work With Plane

When DSPD/Plane is operational, the communication landscape changes:

```
HUMAN-FACING:
  Plane (web UI)        — Project management, sprint planning, work items
  ntfy (push)           — Classified alerts, progress, escalations
  IRC (#human)          — Direct human attention items only
  OCMC Dashboard        — Agent operations, board state, approvals

AGENT-FACING:
  OCMC Board Chat       — Agent-to-agent communication, @mentions
  OCMC Board Memory     — Shared knowledge, decisions, alerts
  Fleet MCP Tools       — Structured operations (13+ tools)
  IRC (per channel)     — Real-time event stream

ORCHESTRATION:
  Plane → OCMC          — PM creates Plane items → fleet creates OCMC tasks
  OCMC → Plane          — Agent completes → fleet updates Plane item
  Plane Webhooks        — Plane events → fleet reacts
  ntfy Routing          — Classified notifications to human
```

### 2.2 The Project Manager Is Not Going To Do Everything

> "the project manager is not going to do everything, its going to be a mix of
> automated work and autonomous agent work and project management work and
> consolidation and tracking"

The PM agent manages the project but the SYSTEM handles:
- **Automated**: Orchestrator dispatches, approves routing, dependency unblocking,
  PR hygiene, health checks, heartbeats
- **PM agent**: Sprint planning, task evaluation, assignment, velocity tracking,
  roadmap decisions
- **fleet-ops**: Quality review, approval decisions, governance
- **Plane**: Source of truth for project state — PM reads and writes to Plane,
  but the sync system keeps OCMC and Plane in sync automatically
- **Human**: Direction, decisions, priority overrides — via Plane, IRC, or ntfy response

### 2.3 The Plane Sync Must Be Smart

The existing `fleet/core/plane_sync.py` (built by software-engineer in Sprint 1)
has basic ingest (Plane → OCMC) and push (OCMC → Plane) logic. But for real
DSPD operation, the sync needs:

1. **Bidirectional state mapping**: Plane states ↔ OCMC states
   ```
   Plane: Backlog → Todo → In Progress → In Review → Done
   OCMC:  inbox   → inbox → in_progress → review   → done
   ```

2. **Sprint cycle management**: PM creates Plane cycle (sprint) → fleet loads tasks

3. **Cross-project dependency**: Plane modules/issues → OCMC depends_on

4. **Assignment sync**: Plane assignee → OCMC assigned_agent_id (mapped by capability)

5. **Comment sync**: Human comments on Plane → OCMC task comment → agent notified

6. **Consolidated tracking**: Sprint velocity computed from both Plane and OCMC data

---

## Part 3: Milestones

### M230: Internal Chat System — Agents Communicate in Real-Time

**Problem:** Agents don't use the OCMC internal chat. Messages go unresponded.
No `fleet_chat` tool. No @mention routing.

**What must happen:**
1. New MCP tool: `fleet_chat(message, mention="")` — posts to board memory with `chat` tag
2. `@agent-name` mention routing: when chat mentions an agent, that agent gets notified
   via their next heartbeat context
3. `@lead` routing: fleet-ops (board lead) always sees `@lead` messages
4. fleet_read_context surfaces recent chat messages as a dedicated field
5. All agent HEARTBEAT.md: "Check internal chat for messages addressed to you"
6. PM responds to work requests in chat (ux-designer, devops asking for work)

**Milestones:**
| # | Scope |
|---|-------|
| M230a | `fleet_chat` MCP tool — post to internal chat with optional @mention |
| M230b | fleet_read_context adds `chat_messages` field (recent messages mentioning this agent) |
| M230c | @mention routing: detect @agent-name and surface in their context |
| M230d | HEARTBEAT.md update: all agents check and respond to chat |
| M230e | PM heartbeat: respond to work requests, assign idle agents |
| M230f | Test: agent posts to chat → mentioned agent sees it in next session |

### M231: IRC Channel Expansion — 7+ Channels with Purpose

**Problem:** Only 3 IRC channels (#fleet, #alerts, #reviews). Need dedicated
channels for sprints, agents, security, human, builds, memory, and Plane.

**What must happen:**
1. Create channels: #sprint, #agents, #security, #human, #builds, #memory, #plane
2. Update irc.py `route_channel()` to route to correct channel by event type
3. All fleet tools use proper channel routing
4. Orchestrator posts sprint updates to #sprint
5. fleet-ops posts agent health to #agents
6. Cyberpunk-Zero posts to #security
7. Human-directed items go to #human exclusively
8. Build/test results go to #builds
9. Important board memory decisions go to #memory

**Channel routing matrix:**

| Event Type | Channel | Who Posts |
|------------|---------|-----------|
| Task dispatched/completed | #fleet | Orchestrator |
| Sprint milestone/velocity | #sprint | Orchestrator, PM |
| Agent online/offline/sleep | #agents | Orchestrator |
| Agent stuck, heartbeat fail | #agents | fleet-ops |
| Security alert, CVE, hold | #security | Cyberpunk-Zero |
| Escalation needs human | #human | Any agent |
| Decision needed from human | #human | PM, fleet-ops |
| PR ready for review | #reviews | Agent (via fleet_task_complete) |
| PR merged/closed | #fleet | Sync daemon |
| Build/test results | #builds | QA, CI |
| Important decisions | #memory | Any agent |
| Plane sync events | #plane | Sync daemon |

**Milestones:**
| # | Scope |
|---|-------|
| M231a | Create 7 new IRC channels via miniircd config |
| M231b | Update irc.py route_channel with full routing matrix |
| M231c | Update all fleet tools to use proper channel routing |
| M231d | Orchestrator posts to #sprint, #agents |
| M231e | fleet-ops posts to #agents, #security |
| M231f | The Lounge configuration for all 10 channels |
| M231g | Test: event → correct channel verified for each type |

### M232: ntfy Operational — Human Actually Receives Notifications

**Problem:** ntfy is configured but zero notifications sent. User doesn't know
which topics to subscribe to. Not enough events trigger notifications.

**What must happen:**
1. Document the 3 ntfy topics for the user:
   - `fleet-progress` — subscribe for: task done, PR merged, sprint updates
   - `fleet-review` — subscribe for: escalations, decisions needed, agents stuck
   - `fleet-alert` — subscribe for: security, infrastructure, critical issues
2. More events trigger ntfy:
   - Every task completion → fleet-progress (currently only parent completion)
   - PR merged → fleet-progress
   - Daily digest → fleet-progress
   - Agent offline > 1 hour → fleet-review
   - Agent requesting work → fleet-progress
   - Security finding → fleet-alert
   - Health issue detected → fleet-review
   - Sprint velocity update → fleet-progress
3. Orchestrator sends periodic summary via ntfy (every 30 min if activity)
4. Test: verify user receives notification on phone/browser

**Windows notifications:**
- Option 1: Install wsl-notify-send (`apt install wsl-notify-send`)
- Option 2: Use ntfy browser push (open http://192.168.40.11:10222 in browser,
  subscribe to topics, enable browser notifications)
- Option 3: Install ntfy Windows desktop client

**Milestones:**
| # | Scope |
|---|-------|
| M232a | Expand ntfy event triggers in orchestrator (task done, PR merged, digest, agent status) |
| M232b | Orchestrator periodic summary via ntfy (if activity in last 30 min) |
| M232c | Document ntfy topics for user (what to subscribe to, how) |
| M232d | Install wsl-notify-send OR configure ntfy browser push |
| M232e | Sync daemon sends ntfy on PR merge/close |
| M232f | Test: dispatch task → complete → ntfy notification arrives on user device |

### M233: Agent Context Enrichment — Everything They Need to Know

**Problem:** Agents don't see chat messages, sprint context, security holds,
or PR status in their context. They start each session partially blind.

**What fleet_read_context should return:**
```
{
  // Existing (already implemented)
  task: { ... },
  urls: { ... },
  recent_memory: [...],
  recent_decisions: [...],
  active_alerts: [...],
  escalations: [...],
  team_activity: [...],
  parent_task_id: "...",
  sibling_tasks: [...],

  // NEW — needs implementation
  chat_messages: [...],        // Internal chat messages mentioning this agent
  sprint_context: {            // Active sprint status
    plan_id: "dspd-s2",
    completion_pct: 25,
    done: 2, total: 8,
    deadline: "2026-04-12",
  },
  security_holds: [...],       // Tasks with security_hold that involve this agent
  pr_status: {                 // PR status for current task
    url: "...",
    mergeable: "CONFLICTING",  // or MERGEABLE, UNKNOWN
    comments: 3,
    reviews: 1,
  },
  agent_role: {                // This agent's role and authority
    primary: "testing",
    secondary: "code_quality_reviewer",
    can_reject: true,
    review_domains: ["test", "quality", ...],
  },
  fleet_health: {              // Quick health summary
    agents_online: 8,
    tasks_blocked: 2,
    pending_approvals: 1,
  },
}
```

**Milestones:**
| # | Scope |
|---|-------|
| M233a | Add chat_messages to fleet_read_context (filter by @agent-name) |
| M233b | Add sprint_context to fleet_read_context (active sprint metrics) |
| M233c | Add security_holds to fleet_read_context |
| M233d | Add pr_status to fleet_read_context (mergeable state, comments) |
| M233e | Add agent_role to fleet_read_context (from agent_roles module) |
| M233f | Add fleet_health summary to fleet_read_context |

### M234: Pre-Plane Communication Verification

**Problem:** Before integrating Plane, the fleet's communication must work
reliably. Plane adds complexity — if basic communication is broken,
Plane integration will be chaos.

**Verification checklist:**
1. Internal chat: agents can post and read chat messages
2. IRC: all 10 channels active with proper routing
3. ntfy: human receives notifications on all 3 topics
4. Board memory: tagged, searchable, agents read before working
5. fleet_read_context: returns comprehensive context including chat, sprint, health
6. Heartbeats: all agents check for messages and respond
7. Escalations: agent → ntfy → human → response → agent continues
8. PR lifecycle: create → review → merge/close → cleanup (fully automated)
9. Sprint lifecycle: load → dispatch → work → review → done → next task (fully automated)
10. Review chain: complete → fleet-ops reviews → QA tests → approve/reject → rework cycle

**Milestones:**
| # | Scope |
|---|-------|
| M234a | End-to-end communication test: post chat → agent sees → responds → human notified |
| M234b | All 10 IRC channels verified with test messages |
| M234c | ntfy test: each topic delivers to user device |
| M234d | Sprint lifecycle test: load sprint → all tasks flow to completion |
| M234e | Full review chain test: with rejection, rework, re-approval |

### M235: Plane Integration Communication Layer

> "we should start thinking of how they are going to work with plane too"
> "the project manager is not going to do everything"

**Problem:** Plane adds a new communication surface. The fleet needs to sync
communication between Plane, OCMC, IRC, and ntfy without duplicating or losing
information.

**What Plane adds:**
- Human creates work items in Plane (sprints, stories, issues)
- PM agent reads Plane → creates OCMC tasks for agents
- Agents complete work → PM updates Plane items with results
- Human sees progress in Plane (burn-down, velocity, analytics)
- Plane comments → routed to agent via OCMC
- Plane status changes → synced to OCMC

**Communication flow with Plane:**

```
HUMAN creates in Plane:
  "Build user authentication for NNRT"
    ↓
  Plane webhook → fleet sync → PM evaluates
    ↓
  PM breaks down into OCMC tasks:
    - "Design auth architecture" → architect
    - "Implement auth middleware" → software-engineer (depends: design)
    - "Write auth tests" → qa-engineer (depends: implement)
    - "Security review auth" → devsecops-expert (depends: implement)
    ↓
  Each task → orchestrator dispatches → agent works → review chain
    ↓
  Agent completes → fleet sync updates Plane item:
    - Plane issue status: In Progress → In Review → Done
    - Plane issue comment: "Completed: PR #X merged. Summary: ..."
    ↓
  Human sees in Plane:
    - Sprint burn-down updating
    - Velocity tracked
    - All sub-issues completing
```

**What the PM manages vs what's automated:**
| Responsibility | Who | How |
|---------------|-----|-----|
| Create sprint in Plane | Human + PM | PM suggests, human approves |
| Break down into tasks | PM agent | fleet_task_create from Plane items |
| Assign agents | PM agent | Capability routing |
| Dispatch tasks | Orchestrator (automated) | Unblocked → dispatch |
| Track progress | Orchestrator (automated) | Velocity, health |
| Review completed work | fleet-ops (automated) | Review chain |
| Update Plane with results | Sync daemon (automated) | OCMC done → Plane done |
| Sprint retrospective | PM agent | Board memory + Plane analytics |
| Cross-project deps | Orchestrator (automated) | Plane modules → OCMC depends_on |
| Escalate to human | Any agent (via tools) | ntfy + IRC #human |

**Milestones:**
| # | Scope |
|---|-------|
| M235a | Plane webhook receiver in fleet (HTTP endpoint for Plane events) |
| M235b | Plane → OCMC sync: new Plane issue → PM evaluates → OCMC tasks created |
| M235c | OCMC → Plane sync: task done → Plane issue updated |
| M235d | Plane comment sync: human comments on Plane → agent notified |
| M235e | Sprint sync: Plane cycle ↔ fleet sprint plan |
| M235f | PM agent Plane integration: read Plane state, manage sprints |
| M235g | #plane IRC channel for sync activity |
| M235h | ntfy notifications for Plane events (new issue, sprint started, etc.) |

### M236: Documentation and Skills for DSPD

> "the documentation and the skills and the other core files and such"

**Problem:** The fleet has 25 core modules but limited documentation and no
Claude Code skills for the new workflows. Agents need skills for Plane
operations, sprint management, and the review chain.

**Skills needed:**
- `/fleet-review` — How to review a task as board lead or QA
- `/fleet-plan` — How to break down an epic into sprint tasks
- `/fleet-test` — How to run and analyze test results
- `/fleet-security-audit` — How to conduct a security review
- `/fleet-plane-sync` — How to manage Plane ↔ OCMC sync
- `/fleet-sprint` — How to manage a sprint lifecycle

**Documentation needed:**
- Architecture overview of all 25 core modules
- MCP tool reference (13 tools with parameters and examples)
- Sprint workflow guide (create → load → dispatch → review → done)
- Review chain guide (complete → fleet-ops → QA → approve/reject)
- Communication guide (which surface for what)
- Plane integration guide (how the sync works)

**Milestones:**
| # | Scope |
|---|-------|
| M236a | .claude/skills/ directory with 6 fleet skills |
| M236b | Architecture documentation for fleet/core/ modules |
| M236c | MCP tool reference documentation |
| M236d | Sprint workflow guide |
| M236e | Review chain guide |
| M236f | Communication guide (IRC, ntfy, chat, board memory, Plane) |

---

## Part 4: User Requirements (Verbatim)

> "we need a thorough investigation and analysis and milestones planning to achieve
> a high level of communication before we start using and integrating plane"

> "I also never received any windows notification is it normal? and the ntfy where
> did we agree on the channel so that I know which to subscribe to?"

> "on IRC there should be at least 7 different channels and 3 at least on ntfy and
> we should start thinking of how they are going to work with plane too"

> "the project manager is not going to do everything, its going to be a mix of
> automated work and autonomous agent work and project management work and
> consolidation and tracking and so on"

> "Do not minimize this is huge again. treat it as such. remember my words remember
> toward where we are going and what we are going to need the agent to build into
> dspd too and the connection to ocmc and the documentation and the skills and the
> other core files and such."

> "Leave nothing to chance. no stone unturned, no bullshit, no random.
> A thorough planning now."

---

## Part 5: Dependency Map and Sequencing

```
M230 (Internal chat system)
  ↓  Agents can communicate in real-time
M231 (IRC channel expansion)
  ↓  Events routed to proper channels
M232 (ntfy operational)
  ↓  Human receives classified notifications
M233 (Agent context enrichment)
  ↓  Agents have full situational awareness

ALL ABOVE must complete before:

M234 (Pre-Plane verification)
  ↓  Communication works reliably end-to-end
M235 (Plane integration communication)
  ↓  Plane ↔ OCMC ↔ IRC ↔ ntfy all connected
M236 (Documentation and skills)
  ↓  Agents have skills and docs for new workflows
```

**Total: 7 new milestones, ~40 sub-milestones.**
**Combined with all previous: 38 major milestones, ~195 sub-milestones.**