# Design: Lifecycle Management & Health Monitoring

## User Requirements

> "There is also auto tracking for like when a agent take a long time on something or is possibly stuck for whatever reason that we might wanna inspect or even report with details and so on."

> "we need logical chains and we need probably an agent for the lifecycle of everything and making sure it all stay alive and up to date"

> "taking the latest change if working on itself and so on and updating about the status"

## What This Means

### Auto-Tracking

Agents don't always know they're stuck. The system needs to detect it:
- Agent accepted task 4 hours ago, no progress comment → maybe stuck
- Agent's last tool call was 30 minutes ago → maybe crashed or blocked
- Agent made 10 commits but no PR → maybe going in circles
- Agent posted a blocker 2 hours ago, no resolution → still blocked
- Agent's session file stopped growing → agent may have errored out

**Detection requires METRICS:**
- Time since task accepted
- Time since last progress comment
- Time since last commit
- Time since last tool call (from session file)
- Number of commits vs expected (1 commit for 5 files = suspicious batch)
- Session file size growth rate

**Reporting requires DETAIL:**
- Not just "agent is stuck" — WHY?
- Last known action (from session file or MC activity)
- Last tool call and result
- Worktree state (uncommitted changes? conflicts?)
- Agent error log if available

### Lifecycle Management

> "the lifecycle of everything and making sure it all stay alive"

Not just task lifecycle. EVERYTHING has a lifecycle:

**Services:**
- OpenClaw gateway → is it running? responsive?
- MC backend → healthy? database connected?
- IRC daemon → running? fleet-bot connected?
- The Lounge → accessible?
- fleet-sync daemon → running? last sync time?
- fleet-monitor daemon → running? last check time?

**Agent Sessions:**
- Are agents' OpenClaw sessions active?
- Are MCP servers running for active agents?
- Are credentials still valid? (token rotation)

**Data:**
- Are worktrees accumulating? (cleanup stale ones)
- Is board memory growing unbounded? (archive old entries)
- Are IRC logs backing up? (export periodically)
- Are git branches accumulating? (prune merged branches)

**Config:**
- Has openclaw.json changed? (agents need updated config)
- Have skills been updated? (agents need refreshed symlinks)
- Has STANDARDS.md changed? (agents need SOUL.md push)

> "taking the latest change if working on itself"

Self-update: when the fleet system itself is modified (new skill, new template,
config change), the lifecycle agent:
1. Detects the change (watches key files)
2. Pushes updates to agent workspaces
3. Notifies agents of changes
4. Reports what was updated

### The Lifecycle Agent

This agent (or daemon) is the fleet's **systems administrator:**

| Responsibility | Frequency | Method |
|---------------|-----------|--------|
| Service health | Every 1 minute | Ping endpoints |
| Agent session health | Every 5 minutes | Check session files |
| Stuck agent detection | Every 10 minutes | Check activity timestamps |
| Credential validation | Every 30 minutes | Test MC API call |
| Worktree cleanup | Every hour | Find stale worktrees |
| Config change detection | Every 5 minutes | Watch file timestamps |
| IRC log backup | Daily | Export channel history |
| Branch cleanup | Daily | Prune merged remote branches |
| Board memory archival | Weekly | Archive old entries |

### Reporting

When something is detected, the lifecycle agent reports with DETAIL:

```
IRC #alerts:
🟡 [fleet-lifecycle] AGENT SLOW: software-engineer working on "Add type hints"
   for 6h with no progress comment.
   Last activity: commit 2h ago (8223d7c)
   Worktree: /projects/nnrt/worktrees/sw-eng-abc123
   Session: 42 messages, last at 14:32 UTC
   Suggestion: check if agent is stuck or needs input
```

```
IRC #fleet:
🔴 [fleet-lifecycle] SERVICE DOWN: fleet-sync daemon not running
   Last sync: 45 minutes ago
   PID file: missing
   Action: restarting... ✅ restarted
```

```
Board memory:
## 🔧 Fleet Health Report

### Services
| Service | Status | Last Check |
|---------|--------|------------|
| Gateway | ✅ UP | 14:55 UTC |
| MC Backend | ✅ UP | 14:55 UTC |
| IRC | ✅ UP | 14:55 UTC |
| The Lounge | ✅ UP | 14:55 UTC |
| fleet-sync | ⚠️ SLOW | last sync 12min ago |
| fleet-monitor | ✅ UP | 14:53 UTC |

### Agents
| Agent | Status | Current Task | Duration |
|-------|--------|-------------|----------|
| architect | 🟢 online | Review pipeline | 2h |
| software-engineer | 🟡 slow | Add type hints | 6h (no progress 2h) |
| qa-engineer | 🟢 idle | — | — |

### Cleanup Needed
- 3 stale worktrees (tasks completed >48h ago)
- 5 merged branches not pruned

Tags: report, health, fleet
```

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M163 | Stuck agent detection | Time-based thresholds, session file analysis |
| M164 | Service health monitoring | Ping all services, restart if possible |
| M165 | Config change detection + auto-push | Watch files, push to agents |
| M166 | Stale resource cleanup | Worktrees, branches, board memory archival |
| M167 | Detailed health reporting | IRC + board memory reports with tables |
| M168 | Lifecycle agent definition | SOUL.md, capabilities, frequency |
| M169 | Self-healing: auto-restart daemons | Detect down, restart, report |

---