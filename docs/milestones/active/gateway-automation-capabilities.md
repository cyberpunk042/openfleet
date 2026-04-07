# Gateway Automation Capabilities — CRONs, Tasks, TaskFlow, Hooks, Standing Orders

**Date:** 2026-04-07
**Status:** Research — full technical capabilities documented from OpenClaw/OpenArms gateway
**Scope:** Every automation mechanism the gateway provides that the fleet can leverage
**Sources:** docs.openclaw.ai/automation/ (cron-jobs, tasks, taskflow, hooks, standing-orders, heartbeat)
**Note:** OpenClaw is one vendor. OpenArms is the fleet's default gateway (resolved via scripts/lib/vendor.sh). Both share these capabilities.

---

## Why This Document Exists

The gateway provides 6 automation mechanisms that the fleet barely uses. The fleet currently uses only heartbeats. CRONs, tasks, taskflow, hooks (beyond basic permissions), and standing orders are all available but unconfigured. This document captures the FULL technical capabilities so the fleet can design proper utilization.

---

## 1. The 6 Automation Mechanisms

| Mechanism | Purpose | Fleet Current Use |
|-----------|---------|-------------------|
| **Heartbeat** | Periodic main-session turn (default 30min) | ACTIVE — core fleet operation |
| **Scheduled Tasks (CRONs)** | Precise-timing background jobs | NONE — zero configured |
| **Background Tasks** | Activity ledger for detached work | PASSIVE — tracks ACP/subagent spawns |
| **Task Flow** | Multi-step durable orchestration | NONE |
| **Hooks** | Event-driven lifecycle scripts | MINIMAL — basic permission allows only |
| **Standing Orders** | Persistent autonomous authority | NONE — not defined in any agent file |

### Decision Guide (from gateway docs)

| Need | Mechanism | Why |
|------|-----------|-----|
| Schedule work at exact time | CRON | Precise timing, isolated execution |
| Periodic awareness check | Heartbeat | Batches with other checks, full session context |
| Track detached work | Background Tasks | Activity ledger with lifecycle tracking |
| Multi-step pipeline | Task Flow | Durable orchestration with revision tracking |
| React to lifecycle events | Hooks | Event-driven, fires on specific events |
| Persistent instructions | Standing Orders | Injected into every session automatically |

---

## 2. Scheduled Tasks (CRONs) — Full Technical Reference

### How CRONs Work

CRONs run INSIDE the gateway process (not inside the model). Jobs persist at `~/.openclaw/cron/jobs.json` so restarts do not lose schedules. All cron executions create background task records.

### Schedule Types

| Kind | CLI Flag | Description |
|------|----------|-------------|
| at | --at | One-shot timestamp (ISO 8601 or relative like "20m") |
| every | --every | Fixed interval (e.g., "2h", "30m") |
| cron | --cron | 5-field or 6-field cron expression with optional --tz |

Timestamps without timezone are treated as UTC. Recurring top-of-hour expressions are automatically staggered by up to 5 minutes to reduce load spikes (override with --exact or --stagger).

### Execution Styles

| Style | --session value | Runs In | Best For |
|-------|----------------|---------|----------|
| Main session | main | Next heartbeat turn | Reminders, system events |
| Isolated | isolated | Dedicated cron:{jobId} session | Reports, background chores |
| Current session | current | Bound at creation time | Context-aware recurring work |
| Custom session | session:custom-id | Persistent named session | Workflows that build on history |

**Main session** jobs enqueue a system event and optionally wake the heartbeat (--wake now or --wake next-heartbeat).

**Isolated** jobs run a dedicated agent turn with a fresh session. Best for fleet CRONs — no context contamination between scheduled tasks and main work.

**Custom sessions** (session:xxx) persist context across runs. A daily standup CRON could use a custom session so each day's standup builds on the previous summary.

### Payload Options for Isolated Jobs

| Option | What It Does |
|--------|-------------|
| --message | Prompt text (required for isolated) |
| --model | Model override (e.g., opus, sonnet) |
| --thinking | Thinking level override (off, low, medium, high) |
| --light-context | Skip workspace bootstrap file injection (reduces cost) |
| --tools | Restrict which tools the job can use (e.g., "exec,read") |
| --agent | Target a specific agent in multi-agent setup |
| --timeout-seconds | Maximum execution time |

**Model selection precedence for isolated jobs:**
1. Per-job payload model
2. Stored cron session model override
3. Agent/default model selection

If the requested model is not allowed, CRON logs a warning and falls back. Fast mode follows resolved live selection.

### Delivery and Output

| Mode | What Happens |
|------|-------------|
| announce | Deliver summary to target channel (default for isolated) |
| webhook | POST finished event payload to a URL |
| none | Internal only, no delivery |

Channel delivery: --announce --channel telegram --to "target-id"
Supported channels: Telegram, Slack, Discord, Mattermost, custom.
Failure notifications: configurable globally (cron.failureDestination) or per job.

### Retry Behavior

**One-shot:** Transient errors retry up to 3 times with exponential backoff (60s, 120s, 300s). Permanent errors disable immediately.

**Recurring:** Exponential backoff (30s to 60m) between retries. Backoff resets after the next successful run.

Retryable error types: rate_limit, overloaded, network, server_error.

### Interim Result Handling

Isolated CRON runs guard against stale acknowledgement replies. If the first result is just an interim status update ("on it", "pulling everything together") and no descendant subagent run is still responsible for the final answer, the gateway re-prompts once for the actual result before delivery.

### Configuration

```json
{
  "cron": {
    "enabled": true,
    "store": "~/.openclaw/cron/jobs.json",
    "maxConcurrentRuns": 1,
    "retry": {
      "maxAttempts": 3,
      "backoffMs": [60000, 120000, 300000],
      "retryOn": ["rate_limit", "overloaded", "network", "server_error"]
    },
    "sessionRetention": "24h",
    "runLog": { "maxBytes": "2mb", "keepLines": 2000 }
  }
}
```

Disable: cron.enabled: false or OPENCLAW_SKIP_CRON=1.

### CLI Reference

```bash
# Add one-shot reminder
openclaw cron add --name "Reminder" --at "2026-02-01T16:00:00Z" \
  --session main --system-event "Check draft" --wake now --delete-after-run

# Add recurring isolated job with delivery
openclaw cron add --name "Morning brief" --cron "0 7 * * *" \
  --tz "America/Los_Angeles" --session isolated \
  --message "Summarize overnight updates." --announce --channel slack --to "channel:C123"

# Add isolated job with model override
openclaw cron add --name "Deep analysis" --cron "0 6 * * 1" \
  --tz "America/Los_Angeles" --session isolated \
  --message "Weekly deep analysis." --model "opus" --thinking high --announce

# Target specific agent
openclaw cron add --name "Ops sweep" --cron "0 6 * * *" \
  --session isolated --message "Check ops queue" --agent ops

# Management
openclaw cron list
openclaw cron edit <jobId> --message "Updated prompt" --model "opus"
openclaw cron run <jobId>           # Manual trigger
openclaw cron run <jobId> --due     # Check if due, run if so
openclaw cron runs --id <jobId> --limit 50   # Run history
openclaw cron remove <jobId>
openclaw cron edit <jobId> --clear-agent     # Remove agent targeting
```

### Maintenance

sessionRetention (default 24h) prunes isolated run-session entries.
runLog.maxBytes / runLog.keepLines auto-prune run-log files.

### Fleet Implications

CRONs are the mechanism for scheduled agent operations — security scans, daily standups, review queue sweeps, coverage reports, architecture health checks, documentation staleness scans. Each CRON:

- Runs in an isolated session (no contamination with main work)
- Uses the right model and effort for the task
- References standing orders for the procedure
- Can be paused by the fleet (when CRON is disabled or fleet is paused)
- Creates a task record for auditing
- Can deliver results to IRC channels or webhooks

The fleet needs:
- config/agent-crons.yaml defining CRONs per agent
- scripts/sync-agent-crons.sh reading config and managing CRONs via CLI
- Fleet state integration: disable CRONs when fleet paused or over budget
- Standing orders per agent: CRONs reference these for their instructions

---

## 3. Background Tasks — Activity Ledger

### What Creates Tasks

| Source | Runtime Type | When Created |
|--------|-------------|--------------|
| ACP background runs | acp | Spawning a child ACP session |
| Subagent orchestration | subagent | Spawning via sessions_spawn |
| Cron jobs (all types) | cron | Every cron execution |
| CLI operations | cli | openclaw agent commands via gateway |

What does NOT create tasks: heartbeat turns, normal interactive chat turns, direct /command responses.

### Task Lifecycle

States: queued -> running -> succeeded | failed | timed_out | cancelled | lost

| Status | Meaning |
|--------|---------|
| queued | Created, waiting for agent to start |
| running | Agent turn actively executing |
| succeeded | Completed successfully |
| failed | Completed with an error |
| timed_out | Exceeded configured timeout |
| cancelled | Stopped by operator via openclaw tasks cancel |
| lost | Runtime lost backing state after 5-minute grace period |

"lost" is runtime-aware: the sweeper checks if the backing session/job still exists. If the backing state disappeared and 5 minutes have elapsed, the task is marked lost.

### Delivery

Two paths:
- **Direct delivery** — completion message goes to the channel the task originated from
- **Session-queued delivery** — queued as system event in requester's session, surfaces on next heartbeat

Task completion triggers an immediate heartbeat wake.

### Notification Policies

| Policy | Behavior |
|--------|----------|
| done_only (default) | Only terminal state delivered |
| state_changes | Every state transition and progress update |
| silent | Nothing delivered |

### Storage

SQLite at $OPENCLAW_STATE_DIR/tasks/runs.sqlite. Sweeper runs every 60 seconds:
1. Reconciliation — checks active tasks still have backing state
2. Cleanup stamping — sets cleanupAfter (endedAt + 7 days)
3. Pruning — deletes records past cleanupAfter

### CLI

```bash
openclaw tasks list [--runtime <acp|subagent|cron|cli>] [--status <status>]
openclaw tasks show <lookup>        # By task ID, run ID, or session key
openclaw tasks cancel <lookup>      # Kills child session
openclaw tasks notify <lookup> <done_only|state_changes|silent>
openclaw tasks audit                # Find stale, lost, inconsistent tasks
openclaw tasks maintenance          # Preview reconciliation
openclaw tasks maintenance --apply  # Execute reconciliation
```

### Audit Findings

| Finding | Severity | Trigger |
|---------|----------|---------|
| stale_queued | warn | Queued > 10 minutes |
| stale_running | error | Running > 30 minutes |
| lost | error | Backing state disappeared |
| delivery_failed | warn | Delivery failed, notify not silent |
| missing_cleanup | warn | Terminal with no cleanup timestamp |
| inconsistent_timestamps | warn | Timeline violation |

### Fleet Implications

Background tasks are the audit trail for all detached work — subagent spawns, CRON executions, CLI operations. The fleet can:
- Monitor agent activity via openclaw tasks list
- Detect stuck/lost operations via openclaw tasks audit
- Cancel runaway operations via openclaw tasks cancel
- Track CRON execution history via openclaw cron runs

---

## 4. Task Flow — Multi-Step Orchestration

### When to Use

| Scenario | Use |
|----------|-----|
| Single background job | Plain task |
| Multi-step pipeline (A then B then C) | Task Flow (managed) |
| Observe externally created tasks | Task Flow (mirrored) |
| One-shot reminder | Cron job |

### Sync Modes

**Managed mode:** Task Flow owns the lifecycle. Creates tasks as flow steps, drives them to completion, advances flow state automatically.

**Mirrored mode:** Task Flow observes externally created tasks. Keeps flow state in sync without taking task ownership. Useful when tasks come from CRONs or CLI and you want unified progress tracking.

### Durable State

Each flow persists its own state and tracks revisions. Progress survives gateway restarts. Revision tracking enables conflict detection when multiple sources advance the same flow.

### Cancel Behavior

openclaw tasks flow cancel sets a sticky cancel intent. Active tasks cancelled, no new steps started. Cancel intent persists across restarts.

### CLI

```bash
openclaw tasks flow list [--status <status>]
openclaw tasks flow show <lookup>
openclaw tasks flow cancel <lookup>
```

### Fleet Implications

Task Flow is relevant for complex fleet operations that span multiple steps:
- Sprint rollover: archive old sprint -> create new sprint -> assign tasks -> notify agents
- Phase advancement: check standards -> route to PO -> await approval -> update labels -> notify
- Deployment pipeline: build -> test -> stage -> verify -> produce (each step is a task)

The fleet orchestrator currently handles multi-step operations in its 30-second cycle. Task Flow could complement this for operations that span multiple cycles or need durable state tracking.

---

## 5. Hooks — Event-Driven Scripts

### Gateway Internal Hooks (14 Event Types)

| Event | When It Fires |
|-------|---------------|
| command:new | /new command issued |
| command:reset | /reset command issued |
| command:stop | /stop command issued |
| command | Any command event (general listener) |
| session:compact:before | Before compaction summarizes history |
| session:compact:after | After compaction completes |
| session:patch | When session properties are modified |
| agent:bootstrap | Before workspace bootstrap files are injected |
| gateway:startup | After channels start and hooks are loaded |
| message:received | Inbound message from any channel |
| message:transcribed | After audio transcription completes |
| message:preprocessed | After all media and link understanding completes |
| message:sent | Outbound message delivered |

### Claude Code Hooks (23+ Event Types)

| Category | Events |
|----------|--------|
| Session | SessionStart, InstructionsLoaded, SessionEnd, PreCompact, PostCompact |
| Tool | PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied |
| User | UserPromptSubmit, Stop, StopFailure |
| Agent | SubagentStart, SubagentStop, TeammateIdle, TaskCreated, TaskCompleted |
| File/Environment | FileChanged, CwdChanged, WorktreeCreate, WorktreeRemove |
| Other | Notification, ConfigChange, Elicitation, ElicitationResult |

### Hook Types

| Type | How It Works |
|------|-------------|
| command | Shell script receiving JSON on stdin. Exit 0 = success, exit 2 = blocking error. |
| http | POST request to endpoint with JSON body. Async option for non-blocking. |
| prompt | Single-turn LLM evaluation with structured schema. |
| agent | Sub-agent with full tool access that can reason and respond. |

### Hook Input Data

All hooks receive standard context:
- session_id, transcript_path, cwd, permission_mode, hook_event_name

Event-specific fields:
- PreToolUse: tool_name, tool_input, tool_arguments
- PermissionRequest: permission_type, tool_name, requested_rules
- FileChanged: file_path, change_type (added/modified/deleted)
- SessionStart: session_source (startup/resume/clear/compact)

### Hook Output and Decision Control

PreToolUse can:
- allow: let the tool call proceed
- deny: block the tool call with reason
- ask: escalate to user permission prompt
- defer: let other hooks or default logic decide
- updatedInput: modify tool parameters before execution

PostToolUse can:
- block: stop further processing with reason

Exit codes:
- Exit 0: success, JSON output processed
- Exit 2: blocking error, stderr becomes error message
- Other: non-blocking, stderr shown in verbose mode only

### Matcher Patterns

Hooks filter when they fire using regex:

| Event Type | Filters On | Examples |
|-----------|-----------|----------|
| Tool events | Tool name | "Bash", "Edit\|Write", "mcp__.*" |
| SessionStart | Session source | "startup", "resume", "clear", "compact" |
| Notification | Notification type | "permission_prompt", "idle_prompt" |
| FileChanged | Filename pattern | ".env", ".envrc" |

Further narrowing with "if" field for content-based matching.

### Hook Configuration Locations

| Location | Scope | Precedence |
|----------|-------|-----------|
| ~/.claude/settings.json | Global (all projects) | Lowest |
| .claude/settings.json | Project (shareable) | Medium |
| .claude/settings.local.json | Project (local only) | High |
| Plugin hooks | Plugin scope (when enabled) | When active |
| Skill/Agent frontmatter | Component-level | Highest |

### Gateway Hook Discovery Hierarchy

1. Bundled hooks (lowest precedence)
2. Plugin hooks
3. Managed hooks: ~/.openclaw/hooks/
4. Workspace hooks: workspace/hooks/ (disabled by default)

Workspace hooks can add new names but cannot override higher-precedence hooks.

### Bundled Gateway Hooks

| Hook | Events | What It Does |
|------|--------|-------------|
| session-memory | command:new, command:reset | Saves session context to workspace/memory/ |
| bootstrap-extra-files | agent:bootstrap | Injects additional bootstrap files from glob patterns |
| command-logger | command | Logs all commands to ~/.openclaw/logs/commands.log |
| boot-md | gateway:startup | Runs BOOT.md when gateway starts |

### Webhook Endpoints (External Triggers)

The gateway can expose HTTP endpoints for triggering agent work from outside:

POST /hooks/wake — enqueue system event for main session:
```bash
curl -X POST http://127.0.0.1:18789/hooks/wake \
  -H 'Authorization: Bearer SECRET' \
  -H 'Content-Type: application/json' \
  -d '{"text":"New event detected","mode":"now"}'
```

POST /hooks/agent — run isolated agent turn:
```bash
curl -X POST http://127.0.0.1:18789/hooks/agent \
  -H 'Authorization: Bearer SECRET' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze this","name":"Analysis","model":"opus","timeoutSeconds":300}'
```

POST /hooks/{name} — mapped custom hooks via hooks.mappings config.

Security: keep behind loopback/tailnet, dedicated token, allowedAgentIds, allowedSessionKeyPrefixes.

### Fleet Implications for Hooks

**Agent monitoring/streaming (PO's idea):**
HTTP hooks with async: true can POST to an external monitoring endpoint on every tool call. Pattern:
- Configure PostToolUse HTTP hook per agent
- Hook POSTs tool name, input, output, timestamp to monitoring service
- PO connects to monitoring service to see real-time agent activity
- Non-blocking (async) — doesn't slow agent down

**Trail recording enhancement:**
PostToolUse hooks could record every tool call to the trail system externally, ensuring trail completeness regardless of whether the tool itself records trail events.

**Quality enforcement:**
PreToolUse hooks could enforce additional quality checks beyond the current permission allows — commit message format validation, PR body structure validation, artifact completeness checks before fleet_task_complete.

**Security enhancement:**
Per-role PreToolUse hooks could enforce role-specific security policies beyond what security-guidance provides — DevSecOps gets additional checks, engineer gets dependency audit checks, DevOps gets infrastructure security checks.

---

## 6. Standing Orders — Persistent Autonomous Authority

### What Standing Orders Are

Standing orders grant agents permanent operating authority for defined programs. Instead of individual task instructions, you define programs with clear scope, triggers, approval gates, and escalation rules. They're placed in workspace files (the gateway documentation recommends AGENTS.md) and are auto-injected into every session.

### Anatomy of a Standing Order

Each program specifies:
- **Scope:** What the agent is authorized to do
- **Triggers:** When to act (schedule, event, condition)
- **Approval Gates:** What requires confirmation before acting
- **Escalation Rules:** What to do when uncertain or when something fails
- **Execution Steps:** The procedure to follow
- **What NOT to Do:** Boundaries preventing scope creep

### Standing Orders + CRONs

Standing orders define WHAT the agent is authorized to do. CRONs define WHEN. The CRON message references the standing order rather than duplicating the full procedure:

```bash
openclaw cron add --name daily-inbox-triage \
  --cron "0 8 * * 1-5" --tz America/New_York \
  --timeout-seconds 300 --announce --channel slack --to "channel:C123" \
  --message "Execute daily inbox triage per standing orders."
```

This separation means: changing the procedure changes the standing order file, not every CRON that references it. And multiple CRONs can reference the same standing order.

### Execute-Verify-Report Pattern

Every standing order task follows:
1. Execute — do the work
2. Verify — confirm the result
3. Report — tell the owner what was done

"Done" without verification is not acceptable. 3 attempts max, then escalate.

### Best Practices (from gateway docs)

**Do:**
- Start narrow and expand
- Define explicit approval gates
- Include "What NOT to Do" sections
- Combine with CRONs for time-based execution
- Review logs weekly

**Avoid:**
- Grant broad authority on day one
- Skip escalation rules
- Assume the agent remembers verbal instructions
- Mix concerns in a single program
- Forget to enforce with CRONs

### Fleet Implications

Standing orders are the bridge between the HEARTBEAT.md priority protocol and the CRON system. Currently:
- HEARTBEAT.md defines what agents do on heartbeat (reactive — respond to what's in context)
- CLAUDE.md defines behavioral rules (constraints)
- Neither defines autonomous programs with explicit authority/scope/gates

Standing orders would formalize:
- DevSecOps nightly security scan: scope (what to scan), triggers (CRON at 01:00), approval gates (critical findings escalate to PO), escalation (if scan fails, alert fleet-ops), execution steps (the scan procedure), boundaries (scan only, don't fix)
- PM daily standup: scope (summarize sprint state), triggers (CRON at 09:00), approval gates (none — informational), escalation (if data unavailable, note gaps), execution (generate summary, deliver to channel), boundaries (report only, don't reassign)
- Fleet-ops review sweep: scope (process pending approvals), triggers (CRON every 2h), approval gates (rejections follow review protocol), escalation (uncertain approvals escalate to PO), execution (real review per fleet-elevation/06), boundaries (don't merge PRs, don't override PO decisions)

These need dedicated per-role design sessions. The standing order content IS the PO's decision about what each agent is authorized to do autonomously.

---

## 7. Heartbeat — Extended Reference

### Configuration

```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "30m",
        "model": "anthropic/claude-opus-4-6",
        "includeReasoning": false,
        "lightContext": false,
        "isolatedSession": false,
        "target": "last",
        "ackMaxChars": 300
      }
    }
  }
}
```

### Per-Agent Heartbeats

```json
{
  "agents": {
    "defaults": { "heartbeat": { "every": "30m", "target": "last" } },
    "list": [
      { "id": "main", "default": true },
      {
        "id": "ops",
        "heartbeat": {
          "every": "1h",
          "target": "whatsapp",
          "to": "+15551234567",
          "prompt": "Check ops queue..."
        }
      }
    ]
  }
}
```

### Active Hours

```json
{
  "heartbeat": {
    "activeHours": {
      "start": "09:00",
      "end": "22:00",
      "timezone": "America/New_York"
    }
  }
}
```

Outside the window, heartbeats are skipped.

### HEARTBEAT.md Structured Tasks Block

The gateway supports structured tasks blocks in HEARTBEAT.md for interval-based sub-checks:

```markdown
tasks:

- name: inbox-triage
  interval: 30m
  prompt: "Check for urgent unread items and flag anything time sensitive."
- name: calendar-scan
  interval: 2h
  prompt: "Check for upcoming events that need prep or follow-up."

# Additional instructions
- Keep alerts short.
- If nothing needs attention after all due tasks, reply HEARTBEAT_OK.
```

Only DUE tasks are included in the heartbeat prompt for that tick. If no tasks are due, heartbeat is skipped entirely. Task last-run timestamps stored in session state, survive restarts.

### Cost Optimization

- isolatedSession: true — fresh session each heartbeat (~100K tokens down to ~2-5K)
- lightContext: true — only HEARTBEAT.md from workspace bootstrap
- Cheaper model override
- Small HEARTBEAT.md
- target: "none" for internal-only updates

### Fleet Implications

The fleet's heartbeat system maps directly to the gateway's capabilities. Current fleet heartbeats use the gateway's per-agent heartbeat config. What's not yet leveraged:

- **Structured tasks blocks** — HEARTBEAT.md could use interval-based sub-checks (PM checks inbox every 30m, checks Plane every 2h)
- **isolatedSession** — could dramatically reduce heartbeat cost for idle agents (the brain gate already handles this, but isolated sessions are an alternative approach)
- **Active hours** — agents could be configured to only heartbeat during work hours (reduces overnight cost when PO is not active)
- **Per-agent model override** — heartbeats could use cheaper models (sonnet for routine checks, opus only when wake trigger found)
- **Channel delivery** — heartbeat results could be delivered to IRC channels for PO visibility

---

## 8. Webhook Integration Points

The gateway provides HTTP webhook endpoints for external systems to trigger agent work:

### POST /hooks/wake
Enqueue a system event for the main session. The agent processes it on next heartbeat or immediately with mode: "now".

Use cases for fleet:
- External monitoring detects an issue -> wake DevSecOps
- CI/CD pipeline completes -> wake fleet-ops for review
- PO posts in external channel -> wake PM
- Plane webhook detects new issue -> wake PM

### POST /hooks/agent
Run an isolated agent turn with specific message, model, and thinking level.

Use cases for fleet:
- Fleet orchestrator triggers specific agent work without going through the heartbeat cycle
- External system requests specific analysis from a specific agent
- PO triggers a specific agent's CRON manually

### Authentication
Every request requires a hook token via Authorization: Bearer header. Keep hooks behind loopback, tailnet, or trusted reverse proxy. Use dedicated hook token (not gateway auth token).

### Fleet Integration Pattern

The fleet orchestrator could use webhooks instead of or alongside the current gateway WebSocket RPC for certain operations:
- Current: orchestrator calls inject_content(session_key, message) via WebSocket
- Alternative: orchestrator calls POST /hooks/agent with message + model + agent targeting
- Advantage: webhook creates a background task record (auditable), supports model override, has retry semantics

This is NOT a replacement for the current approach — it's an additional capability. The fleet needs to evaluate which operations benefit from webhook-based triggering vs WebSocket injection.

---

## 9. How These Mechanisms Interact

```
STANDING ORDERS (define WHAT)
  |
  v
CRONs (define WHEN)           HEARTBEATS (define FREQUENCY)
  |                              |
  v                              v
ISOLATED SESSIONS              MAIN SESSION
  |                              |
  v                              v
BACKGROUND TASKS (track)       (no task record)
  |
  v
TASK FLOW (orchestrate multi-step)
  |
  v
HOOKS (react to events within any session)
  |
  v
WEBHOOKS (trigger from external)
```

Each mechanism has a distinct role. They COMPOSE, not replace:
- Standing order defines the DevSecOps nightly scan procedure
- CRON fires at 01:00 in isolated session with opus model
- Background task tracks the execution
- If the scan is multi-step (scan -> analyze -> report), Task Flow orchestrates
- Hooks within the session enforce security patterns during scanning
- If the scan finds critical issues, webhook could wake the PO's notification endpoint

---

## 10. Known Issues and Considerations

### Security Hook Content Detection (Observed 2026-04-07)

The security-guidance plugin's PreToolUse hooks trigger on content that MENTIONS security patterns (like a document describing what the security plugin detects). This causes false positives when writing documentation about security patterns.

Potential solutions:
- Detect when content is documentation/markdown (not code) and reduce sensitivity
- Use a whitelist for known documentation paths
- Transform flagged content to pass hooks while remaining readable (the PO's suggestion)
- Configure per-agent hook sensitivity

### CRON + Fleet State Coordination

CRONs run inside the gateway process. The fleet orchestrator runs as a separate Python daemon. For CRONs to respect fleet state (paused, over budget), one of:
- CRONs check fleet state at execution time (read fleet control state file)
- Fleet orchestrator manages CRONs (create/delete via CLI based on fleet state)
- Standing orders include fleet state awareness (the CRON message tells the agent to check fleet state first)

The simplest approach: standing orders include "If fleet is paused or over budget, skip and report."

### Model/Effort for CRONs vs Heartbeats vs Dispatched Tasks

Three separate configuration surfaces for model/effort:
- CRONs: per-job --model and --thinking flags
- Heartbeats: per-agent heartbeat.model in gateway config
- Dispatched tasks: brain's model_selection.py + backend_router.py

These are currently INDEPENDENT. A unified configuration where the brain manages all three would reduce inconsistency. But that's a brain evolution task, not a gateway configuration task.
