# Phase F4: Governance Agent — The Fleet's Immune System

> "we would probably need one agent that will keep order in all this and offer feature like backup of the IRC and stuff like this revolving around its SRP evolutions."

> "There is going to be a lot of governance and automation and enhancement needed around the agents and the work and tooling and workflow and so on."

## Problem Statement

The fleet has no coordinator. Tasks can sit in inbox forever. PRs can sit in review
forever. Agents don't check each other's work. Nobody enforces standards. Nobody
notices when something is broken, missing, or stale. Nobody produces operational
reports. The human has to manually check everything.

## Design Principle

**The governance agent is the fleet's immune system — it detects problems and triggers responses.**

It doesn't do the work. It makes sure work GETS DONE, and gets done WELL.

## The Governance Agent

### Identity

- **Name:** `fleet-ops` (or `coordinator` — open for discussion)
- **Mode:** think + act (reads fleet state, runs checks, creates tasks, posts reports)
- **Type:** persistent (runs on heartbeat cycle, not just on task assignment)
- **Approval required:** No (it monitors, it doesn't change code)

### Core Responsibilities

#### 1. Board State Monitoring

**What it checks (every heartbeat cycle):**
- Tasks in inbox > 1 hour without assignment → alert on IRC
- Tasks in in_progress > 8 hours without a progress comment → alert on IRC
- Tasks in review > 24 hours without a review comment → alert on IRC
- Agents offline for > 2 hours → alert on IRC
- Unmerged PRs > 48 hours → alert on IRC + board memory
- Board memory entries tagged [blocked] without resolution → escalate

**What it does:**
- Posts structured alerts using fleet-irc skill
- Creates proposed tasks for stale items
- Escalates to human when automated resolution fails

#### 2. Quality Enforcement

**What it checks:**
- New commits: do they follow conventional commit format?
- New PRs: do they have a changelog section? Are URLs present?
- Task comments: are they using the structured templates?
- Board memory: are entries properly tagged?

**What it does:**
- Posts quality warnings to board memory and IRC
- Creates "fix quality" tasks for agents who violate standards
- Tracks quality metrics over time

#### 3. Operational Reporting

**Daily digest (posted to #fleet and board memory):**
```markdown
## 📊 Fleet Daily Digest — {date}

### Activity
- Tasks created: {N}
- Tasks completed: {N}
- PRs merged: {N}
- Alerts raised: {N}

### Active Work
| Agent | Task | Status | Duration |
|-------|------|--------|----------|
| {agent} | [{title}]({task_url}) | {status} | {hours}h |

### Blockers
- [{title}]({task_url}) — blocked since {date}: {reason}

### PRs Pending Review
- [{title}]({pr_url}) — waiting {hours}h

### Health
- Agents online: {N}/{total}
- IRC: {connected/disconnected}
- MC: {healthy/unhealthy}
- Gateway: {running/stopped}

---
<sub>Fleet Ops · {timestamp}</sub>
```

**Weekly summary (posted to #fleet and board memory):**
- Trends: tasks/week, PRs/week, average review time
- Highlights: notable completions, blockers resolved
- Gaps identified: missing skills, capabilities, automation
- Recommendations: what to improve next week

#### 4. Gap Detection

> "we are missing an Agent X or Y or Z... lack this skill or that... lack this knowledge"

**What it monitors:**
- Agents: are all necessary roles covered? Any role overloaded?
- Skills: are agents hitting skill gaps? (detected from task failures/blockers)
- Knowledge: are agents re-discovering the same things? (detected from repeated patterns)
- Automation: are there manual steps that should be scripted?
- Documentation: are decisions and architecture documented?

**What it does:**
- Posts gap analysis to board memory: tags [gap, {area}]
- Creates proposed tasks for addressing gaps
- Posts weekly gap report to #fleet

#### 5. IRC Operations

> "backup of the IRC and stuff like this"

**What it manages:**
- IRC log backup (export channel history periodically)
- Channel topic updates (reflect current fleet state)
- Message volume monitoring (is a channel too noisy? too quiet?)
- Notification routing verification (are alerts reaching #alerts?)

### Implementation Approach

**The governance agent runs on OpenClaw's heartbeat system.** Every N minutes,
the heartbeat triggers and the agent:
1. Reads board state from MC API
2. Checks for violations and staleness
3. Posts alerts/reports as needed
4. Creates proposed tasks as needed

This means the governance agent is ALWAYS RUNNING in the background, not just
when assigned a task. It uses the MC agent API (same as other agents) to read
board state and post.

**Alternatively:** The governance logic could run as a fleet script (Python daemon)
that doesn't use an AI agent at all — just API calls and rules. This would be:
- Cheaper (no LLM calls for routine checks)
- Faster (no agent startup time)
- More reliable (deterministic rules, not AI judgment)

**Recommended: Hybrid approach.**
- Routine checks (staleness, quality format) → Python daemon (fleet-ops service)
- Judgment calls (gap detection, weekly analysis, recommendations) → AI agent
- Daily/weekly digests → AI agent (better prose)
- IRC operations → Python daemon

## Milestones

### M97: Governance Agent Definition

**Tasks:**
1. Create `agents/fleet-ops/` with agent.yaml, SOUL.md
2. Define capabilities, mode, constraints
3. Register in OpenClaw and MC
4. Add to setup.sh agent registration flow

### M98: Board State Monitor (Python daemon)

**Tasks:**
1. Create `scripts/fleet-ops-monitor.sh` (or Python script)
2. Polls MC API every 5 minutes
3. Checks: stale inbox, stale review, offline agents, old PRs
4. Posts alerts to IRC and board memory using existing notify scripts
5. Runs as background daemon (like fleet-sync-daemon.sh)

### M99: Daily Digest

**Tasks:**
1. Create `scripts/fleet-digest.sh`
2. Collects: task counts, agent activity, PR status, blocker status
3. Formats using markdown template (from M82)
4. Posts to #fleet IRC and board memory
5. Triggered by cron or governance daemon (daily at configured time)

### M100: Quality Enforcement

**Tasks:**
1. Define quality rules:
   - Commit format: must match conventional commit regex
   - PR body: must contain ## Changelog, ## Changes, ## References sections
   - Task comments: must use structured format (check for ## headers)
   - Board memory: must have tags
2. Create checking script that validates recent output
3. Post violations to board memory and IRC
4. Create "fix quality" tasks for repeat violators

### M101: IRC Operations

**Tasks:**
1. IRC log export script (dump channel history to file)
2. Channel topic auto-update (reflect current sprint/focus)
3. Backup schedule (daily export to fleet repo or storage)
4. Health check: is fleet-bot connected? Are messages flowing?

### M102: Gap Detection (AI agent)

**Tasks:**
1. Agent analyzes fleet state periodically (weekly?)
2. Compares: agents available vs work types needed
3. Compares: skills available vs skills agents hit walls on
4. Compares: documentation vs decisions made
5. Posts gap report to board memory and #fleet

## Open Questions

1. **Should the governance agent be a real AI agent or a Python daemon?**
   - AI agent: better prose, can reason about gaps, expensive per run
   - Python daemon: deterministic, cheap, always-on, can't reason
   - Hybrid: routine=daemon, analysis=agent — recommended

2. **How often should each check run?**
   - Board state: every 5 minutes (daemon)
   - Quality: every hour (daemon)
   - Digest: daily (cron)
   - Gap analysis: weekly (agent)

3. **How aggressive should enforcement be?**
   - Start with warnings only (IRC + board memory)
   - Graduate to creating "fix" tasks for repeat issues
   - Never block agent work automatically (human decision)

4. **Should the governance agent have authority to close stale tasks?**
   - Proposal: after 7 days stale in inbox with no assignment → auto-close with comment
   - Needs human approval for this policy

## Verification

- [ ] Governance agent registered in OpenClaw and MC
- [ ] Board state monitor detects stale tasks (test with an old task)
- [ ] Daily digest appears in #fleet and board memory
- [ ] Quality violations detected and reported
- [ ] IRC backup script exports channel history
- [ ] Gap detection produces actionable report
- [ ] All running as daemons via setup.sh (no manual steps)