# Analysis 05 — Hooks Branch of the Knowledge Map

**Date:** 2026-04-02
**Status:** ANALYSIS — mapping all hooks into the knowledge tree
**Purpose:** 26 hook types available, 0 currently used. Which hooks
enhance each role, how they connect to fleet systems.

---

## The Hooks Landscape

Claude Code provides 26 hook event types. Hooks are DETERMINISTIC —
they fire every time, 100% reliable. Unlike skills (which Claude
decides to use) or commands (which the agent invokes), hooks are
AUTOMATIC enforcement. This makes them the foundation of
Line 1 anti-corruption: structural prevention.

**Four handler types:**
- `command` — shell script (fastest, most reliable)
- `http` — POST to URL
- `prompt` — single-turn LLM call
- `agent` — subagent with tools

---

## All 26 Hooks Mapped to Fleet Use Cases

### Pre-Action Hooks (can block/modify)

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `UserPromptSubmit` | Before Claude processes prompt | Inject fleet context, validate task scope, add methodology reminders | ALL | HIGH |
| `PreToolUse` | Before ANY tool executes | **safety-net pattern**: catch destructive commands (rm -rf, git reset --hard, DROP TABLE). Validate tool matches current stage. Enforce contribution requirements before dispatch. | ALL | CRITICAL |
| `PermissionRequest` | Permission dialog appears | Auto-approve known-safe patterns. Block known-dangerous patterns. Custom approval logic per role. | ALL | MEDIUM |

### Post-Action Hooks (observe/react)

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `PostToolUse` | After tool succeeds | **Trail recording**: every tool call → trail event. Code quality checks after edits. Plane sync after commits. | ALL | HIGH |
| `PostToolUseFailure` | After tool fails | Error classification. Repeated failures → alert. Dead MCP server detection. | ALL | MEDIUM |
| `PermissionDenied` | Auto mode denies tool | Log denied operations for audit trail. Detect permission misconfigurations. | ALL | LOW |
| `Stop` | Claude finishes responding | **Review gate pattern** (from codex concept): run independent quality check before completion. Save session state. Trail "turn completed" event. | ALL | HIGH |
| `StopFailure` | Turn ends from API error | Rate limit detection → notify brain. Auth failure → alert. Trigger fallback model. | ALL | HIGH |

### Session Lifecycle Hooks

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `SessionStart` | Session begins/resumes | **Knowledge map injection**: load fleet context, inject role-specific map data, restore memory from claude-mem, set environment variables. | ALL | CRITICAL |
| `SessionEnd` | Session closes | Save session state. Record trail "session ended." Persist memory. Notify orchestrator. | ALL | HIGH |
| `PreCompact` | Before compaction | **Save state before context loss**: write key decisions to memory, save artifact progress, record what to preserve. | ALL | HIGH |
| `PostCompact` | After compaction | Verify preserved state. Re-inject critical context. Confirm context recovery. | ALL | MEDIUM |

### Agent Team Hooks

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `SubagentStart` | Subagent spawns | Log subagent creation. Inject subagent-specific context from map. | ALL | MEDIUM |
| `SubagentStop` | Subagent finishes | Collect subagent results. Validate output quality. Trail event. | ALL | MEDIUM |
| `TeammateIdle` | Teammate about to idle | Load balancing across team members. Assign next task from queue. | FLEET-OPS | LOW |
| `TaskCreated` | Task created | Trail event. Validate task fields. Auto-assign based on role. | PM, FLEET-OPS | MEDIUM |
| `TaskCompleted` | Task completed | Trail event. Trigger review chain. Notify fleet-ops. Update sprint progress. | ALL | HIGH |

### Configuration Hooks

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `InstructionsLoaded` | CLAUDE.md parsed | Inject additional context from knowledge map. Add role-specific rules. Add stage-specific instructions. | ALL | HIGH |
| `ConfigChange` | Settings change | React to PO setting changes. Propagate budget_mode changes. Hot-reload agent configuration. | FLEET-OPS | MEDIUM |

### Workspace Hooks

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `CwdChanged` | Working directory changes | Update project context. Load project-specific rules. Switch knowledge map scope. | ALL | LOW |
| `FileChanged` | Watched file changes | Config hot-reload. CLAUDE.md change detection. agent.yaml change propagation. | FLEET-OPS | MEDIUM |
| `WorktreeCreate` | Worktree created | Trail event. Setup worktree environment. Copy agent config. | ENG, DEVOPS | MEDIUM |
| `WorktreeRemove` | Worktree removed | Cleanup. Trail event. | ENG, DEVOPS | LOW |

### MCP Hooks

| Hook | When | Fleet Use Case | Roles | Priority |
|------|------|---------------|-------|----------|
| `Elicitation` | MCP requests user input | Custom approval flow. Route MCP questions to PO. | ALL | LOW |
| `ElicitationResult` | User responds to MCP | Process response. Route to requesting agent. | ALL | LOW |
| `Notification` | Claude sends notification | Custom notification routing. Fleet-specific notification channels. | ALL | MEDIUM |

---

## Hook Implementation Priorities

### Tier 1: Implement First (structural prevention + trail)

| Hook | Implementation | Why First |
|------|---------------|-----------|
| `PreToolUse` | Command handler: check tool against stage gating, check for destructive patterns (safety-net), validate contribution requirements | **Line 1 anti-corruption.** Structural prevention. Every tool call passes through this gate. |
| `PostToolUse` | Command handler: record trail event with agent+model+tool+result | **Trail system foundation.** Every successful tool call becomes an audit trail entry. |
| `SessionStart` | Command handler: inject knowledge map context, load claude-mem state, set FLEET_AGENT env var | **Context injection.** Without this, agents start blind. |
| `Stop` | Command handler: save session state, record trail "turn completed" | **State preservation.** Prevents context loss between turns. |
| `StopFailure` | Command handler: detect rate_limit → notify brain, detect auth_failed → alert | **Error handling.** Fleet must know when agents hit limits. |

### Tier 2: Implement Next (session management + quality)

| Hook | Implementation | Why Next |
|------|---------------|----------|
| `PreCompact` | Command handler: save key decisions to memory, record artifact progress | **Context survival.** Prevents knowledge loss during compaction. |
| `PostCompact` | Command handler: verify critical context preserved, re-inject if needed | **Context recovery.** Ensures agent doesn't lose its bearings. |
| `SessionEnd` | Command handler: persist final state, notify orchestrator | **Clean shutdown.** Orchestrator knows agent session ended. |
| `InstructionsLoaded` | Command handler: inject role-specific map data, add stage instructions | **Dynamic rules.** Augment CLAUDE.md with map-driven context. |
| `TaskCompleted` | Command handler: trail event, trigger review chain | **Workflow automation.** Task completion triggers downstream actions. |

### Tier 3: Implement Later (advanced features)

| Hook | Implementation | Why Later |
|------|---------------|----------|
| `UserPromptSubmit` | Inject methodology reminders, validate task scope | Enhances quality but not blocking |
| `ConfigChange` | Hot-reload settings, propagate changes | Convenience, not critical path |
| `FileChanged` | Watch for config changes | Operational improvement |
| `SubagentStart/Stop` | Log + validate subagent operations | Agent Teams integration |
| `Notification` | Custom fleet notification routing | Enhances but not required |

---

## Hooks Manual Structure in the Map

```
Hooks Manual/
├── structural-prevention/
│   ├── PreToolUse — safety gate (destructive commands, stage enforcement)
│   │   Connects to: safety-net plugin, Line 1 anti-corruption, trail system
│   ├── PostToolUse — trail recording (every tool call → audit event)
│   │   Connects to: trail_recorder.py, LaborStamp mini-signatures
│   └── Stop — review gate + state save
│       Connects to: codex review gate pattern, session persistence
│
├── context-management/
│   ├── SessionStart — knowledge map injection
│   │   Connects to: knowledge map navigator, claude-mem, intent-map
│   ├── PreCompact — state preservation before context loss
│   │   Connects to: session_manager.py, smart artifacts dumping
│   ├── PostCompact — context recovery verification
│   │   Connects to: CW-04 efficient regathering
│   ├── InstructionsLoaded — augment CLAUDE.md with map data
│   │   Connects to: autocomplete chain, per-stage instructions
│   └── SessionEnd — clean shutdown, state persistence
│       Connects to: orchestrator, trail system
│
├── error-handling/
│   ├── StopFailure — rate limit detection, auth failures
│   │   Connects to: budget system, storm monitor, circuit breakers
│   └── PostToolUseFailure — repeated failure detection
│       Connects to: doctor (stuck detection), MCP health
│
├── workflow/
│   ├── TaskCreated — validate fields, auto-assign
│   │   Connects to: PM workflow, contribution subtask creation
│   ├── TaskCompleted — trigger review chain
│   │   Connects to: fleet-ops review, event chains
│   └── TeammateIdle — load balancing
│       Connects to: Agent Teams, dispatch
│
└── workspace/
    ├── ConfigChange — hot-reload propagation
    ├── FileChanged — config watching
    ├── WorktreeCreate — setup environment
    └── WorktreeRemove — cleanup
```

---

## How Hooks Connect to Other Branches

| Hook | Connects To |
|------|------------|
| PreToolUse | → Anti-corruption Line 1, → Stage gating (methodology), → safety-net plugin, → Contribution dispatch gate |
| PostToolUse | → Trail system (33 event types), → LaborStamp signatures, → Plane sync |
| SessionStart | → Knowledge map (intent-map → injection profile), → claude-mem, → Memory system |
| PreCompact | → Session manager (brain Step 10), → CW-03/CW-04, → Smart artifacts |
| Stop | → Codex review gate pattern, → fleet_task_complete chain |
| StopFailure | → Budget system, → Storm monitor (rate_limit indicator), → Circuit breakers |
| InstructionsLoaded | → CLAUDE.md + knowledge map augmentation, → Stage instructions |
| TaskCompleted | → Event chain (build_task_complete_chain), → Sprint progress |

---

## The Key Insight

Hooks are the ENFORCEMENT LAYER of the knowledge map. The map defines
WHAT knowledge exists and WHERE it goes. Hooks ensure it ACTUALLY GETS
THERE — reliably, every time, without the agent choosing to skip it.

- Map says "architect in reasoning gets brainstorming + writing-plans"
- SessionStart hook INJECTS that content at session start
- Map says "every tool call recorded in trail"
- PostToolUse hook RECORDS it automatically
- Map says "no destructive commands"
- PreToolUse hook BLOCKS them before execution

Skills can be ignored. Commands can be forgotten. Rules can be violated.
Hooks CANNOT be bypassed — they are deterministic automation.

This is why hooks are the structural foundation (Line 1) of anti-corruption.
