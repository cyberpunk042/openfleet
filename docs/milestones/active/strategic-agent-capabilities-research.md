# Strategic Agent Capabilities — Sub-Agents, Agent Teams, Extended Thinking, Monitoring

**Date:** 2026-04-07
**Status:** Research — technical capabilities for advanced agent operations
**Scope:** Sub-agent strategies, Agent Teams, extended thinking integration, hook-based monitoring, session management
**Sources:** Claude Code documentation, OpenClaw/OpenArms gateway docs, fleet-elevation/23 (strategic calls), fleet-elevation/20 (anti-corruption), context-window-awareness-and-control.md

---

## Why This Document Exists

Top-tier experts don't just use tools — they delegate, collaborate, think deeply when appropriate, and are observable. The fleet agents have access to sub-agent spawning, Agent Teams for parallel work, adaptive extended thinking, and hook-based monitoring — but none of these are configured or leveraged beyond what plugins provide by default.

This document captures the full technical capabilities and how they map to fleet needs.

---

## 1. Sub-Agents — Delegation Within a Session

### How Sub-Agents Work

Sub-agents are specialized Claude instances running in separate context windows within a single session. Each sub-agent:
- Has its own isolated context window (preserves main agent's context space)
- Runs with a custom system prompt focused on its specialty
- Has restricted tool access (principle of least privilege)
- Can operate with different model and permissions than the main agent
- Works independently and returns results back to the main agent only
- Does NOT run in true parallel — executes sequentially within the session

### Defining Sub-Agents

Location and scope:

| Scope | Location | Shared? |
|-------|----------|---------|
| Project | .claude/agents/{name}.md | Yes, with team via git |
| User | ~/.claude/agents/{name}.md | Only on this machine |
| Plugin | agents/{name}.md in plugin | Via plugin |

Configuration via YAML frontmatter in the .md file:

```yaml
---
name: agent-name
description: >
  When to use this agent — drives auto-delegation decisions.
model: claude-sonnet-4-6  # or opus, haiku, inherit from parent
tools:
  - Bash
  - Read
  - Grep
  - Glob
tools_deny:
  - WebFetch
permissions:
  defaultMode: plan
isolation: worktree   # or none
disabled: false
skills:
  - relevant-skill-name
mcpServers:
  - relevant-mcp-server
persistentMemory: true
---

[System prompt instructions for this sub-agent]
```

Key fields:
- **description** — controls WHEN the main agent auto-delegates to this sub-agent. The main agent reads descriptions and matches tasks to specialists.
- **model** — cost control. Use sonnet for routine, haiku for simple, opus for complex. Inherit from parent if the main agent's model is appropriate.
- **tools** — allowlist restricts what the sub-agent can do. A code-explorer sub-agent should NOT have Write/Edit.
- **tools_deny** — alternatively, block specific tools.
- **isolation: worktree** — gives the sub-agent its own git worktree. Automatically cleaned up if no changes.
- **skills** — preload specific skills for the sub-agent's focus area.
- **mcpServers** — expose specific MCP servers.

### Sub-Agent Strategies

**Strategy 1: Focused Delegation**
Spawn a sub-agent for a specific subtask. Main agent continues while waiting for results.
- Architect spawns code-explorer to map a codebase area
- Engineer spawns test-runner to execute and report test results
- QA spawns coverage-analyzer to check test coverage metrics

**Strategy 2: Parallel Research (Simulated)**
Sub-agents execute sequentially within a session but can batch multiple research tasks:
- Spawn research sub-agent with multiple questions
- Sub-agent investigates all questions in its isolated context
- Returns aggregated findings to main agent
- Main agent synthesizes across findings

**Strategy 3: Two-Stage Review (from superpowers)**
The subagent-driven-development skill:
1. Stage 1: Check spec compliance (does the work match the plan?)
2. Stage 2: Check code quality (is the code well-written?)
Both stages in the current session, each with focused analysis.

**Strategy 4: Context Protection**
Spawn sub-agent for work that would bloat the main context:
- Large codebase exploration (reading many files)
- Log analysis (processing large output)
- Dependency audit (checking many packages)
The sub-agent's context is isolated — the main agent only sees the summary.

### Sub-Agents Already Available via Plugins

**superpowers code-reviewer:**
- Reviews completed project steps against original plans
- Covers: plan alignment, code quality, architecture/design, documentation/standards
- Issue categorization: Critical / Important / Suggestion

**pr-review-toolkit (6 agents):**
- code-reviewer (opus): CLAUDE.md compliance, style, bugs
- code-simplifier: simplification preserving functionality
- comment-analyzer: comment accuracy, documentation completeness
- pr-test-analyzer: behavioral coverage, test gaps, edge cases
- silent-failure-hunter: error handling audit
- type-design-analyzer: type encapsulation, invariant expression

**feature-dev (3 agents, NOT yet assigned to any fleet agent):**
- code-explorer (sonnet): trace execution paths, map architecture
- code-architect (sonnet): design features, provide implementation blueprints
- code-reviewer (sonnet): confidence-based code review

### Fleet Sub-Agent Needs (To Be Designed)

Each role may benefit from custom sub-agent definitions. These are NOT specifications — they need per-role design work. Examples of TYPES that could be useful:

**For Architect:**
- Codebase navigator (read-only, filesystem + grep, sonnet) — explore code structure without bloating main context
- Pattern analyzer (read-only, filesystem + grep, haiku) — identify patterns in existing code

**For Engineer:**
- Test executor (filesystem + pytest-mcp, sonnet) — run tests and report results
- Parallel explorer (web search + web fetch, sonnet, worktree) — research while main agent works

**For DevSecOps:**
- Dependency scanner (filesystem + bash, sonnet) — scan dependencies for vulnerabilities
- Secret detector (filesystem + grep, haiku) — scan files for exposed secrets

**For QA:**
- Coverage reporter (filesystem + bash, sonnet) — generate coverage reports
- Regression checker (filesystem + pytest-mcp, sonnet) — run specific regression test suites

**For Fleet-Ops:**
- Trail reconstructor (filesystem + grep, sonnet) — reconstruct task trail from board memory events
- Compliance checker (filesystem + grep, haiku) — verify methodology compliance

These need proper design: exact tools allowed, model choice, isolation mode, what the description says (for auto-delegation), what the system prompt teaches.

---

## 2. Agent Teams — True Parallel Collaboration

### What Agent Teams Are

Agent Teams enable multiple independent Claude Code instances working simultaneously on the same project. Unlike sub-agents (sequential, results return to parent), teammates work in parallel with direct peer-to-peer messaging and shared task lists.

**Enable:** CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 in settings or environment.
**Requires:** Claude Code v2.1.32 or later.

### Architecture

| Component | Role |
|-----------|------|
| Lead | Main session that creates, spawns, and coordinates teammates |
| Teammates | Separate independent sessions with own context windows |
| Task List | Shared .claude/tasks/{team-name}/ with pending/in-progress/completed |
| Mailbox | Direct messaging system between agents |

### Communication

- Direct message: teammate send-message to "Alice" "question here"
- Broadcast: send to all teammates at once
- Automatic delivery: messages arrive without lead polling
- Lead receives all teammate messages automatically

### Task Lists

- Stored in ~/.claude/tasks/{team-name}/
- Three states: pending -> in-progress -> completed
- Tasks can have dependencies (blocked tasks auto-unblock when dependency completes)
- File locking prevents race conditions

### Permissions

- Teammates inherit lead's permission mode at spawn
- Can change individual teammate modes after spawning
- If lead runs with bypass permissions, all teammates do too
- Sub-agent definitions can be used as teammate templates

### Display Modes

- **In-process** (default): all teammates run in your terminal, cycle with Shift+Down
- **Split-pane** (tmux/iTerm2): each teammate gets own pane, see all simultaneously

### Quality Gates via Hooks

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "type": "command",
        "command": "/path/to/quality-check.sh"
      }
    ],
    "TaskCompleted": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/verify-tests.sh"
          }
        ]
      }
    ]
  }
}
```

Exit code 2 from hook blocks completion and sends feedback to teammate.

### Known Limitations (Experimental)

- No session resumption (/resume and /rewind don't restore in-process teammates)
- Task status lag (teammates sometimes fail to mark tasks complete)
- One team per session (lead manages one team at a time)
- No nested teams
- Lead is fixed (cannot promote teammate mid-session)

### Fleet Implications

Agent Teams could COMPLEMENT the fleet orchestrator:
- **Orchestrator** handles fleet-wide coordination (10 agents, task dispatch, budget, health)
- **Agent Teams** handles within-task collaboration (architect + engineer on same epic)

Potential use cases:
- **Epic breakdown:** PM leads a team of architect + engineer to explore, design, and plan simultaneously
- **Parallel review:** Fleet-ops leads a team of 3 reviewers checking different aspects in parallel
- **Investigation:** Architect leads a team exploring multiple approaches simultaneously, debating via mailbox
- **Implementation:** Engineer leads teammates working on different modules, coordinating via shared task list

This is EXPERIMENTAL and needs evaluation against the fleet's current orchestrator. The key question: does Agent Teams' built-in coordination complement or conflict with the fleet's orchestrator-driven coordination? Likely complement — Agent Teams for micro-coordination within a single task session, orchestrator for macro-coordination across the fleet.

---

## 3. Extended Thinking — Adaptive Reasoning Depth

### How Extended Thinking Works

On Opus 4.6 and Sonnet 4.6, extended thinking is always active with adaptive reasoning. The model dynamically allocates thinking tokens based on effort level:
- Higher effort = more thinking tokens available = better output = more cost
- Lower effort = fewer thinking tokens = faster output = less cost
- The model decides how many tokens to actually use per turn based on complexity

### Configuration Options

| Scope | Method | Control |
|-------|--------|---------|
| Per-session effort | /effort command or /model | Sets thinking depth (low/medium/high) |
| Environment default | CLAUDE_CODE_EFFORT_LEVEL=high | Global default |
| Toggle | Option+T / Alt+T | Toggle on/off for current session |
| Per-project | /config -> toggle thinking | Default across sessions |
| Token limit | MAX_THINKING_TOKENS=N | Cap thinking tokens (Opus 4.6 / Sonnet 4.6) |
| Force high | "ultrathink" keyword in prompt | Forces high effort for single turn |

### Fleet's Current State

configure-agent-settings.sh sets per-role effort levels:

| Agent | Effort | Rationale |
|-------|--------|-----------|
| Architect | high | Deep design reasoning |
| DevSecOps | high | Thorough security analysis |
| PM | high | Strategic planning |
| Accountability | high | Thorough compliance analysis |
| Software Engineer | medium | Implementation work |
| QA Engineer | medium | Test analysis |
| DevOps | medium | Infrastructure work |
| Fleet-Ops | medium | Review processing |
| UX Designer | medium | Design work |
| Technical Writer | low | Documentation (routine) |

These are STATIC — same effort regardless of methodology stage, task complexity, or situation.

### What Stage-Aware Effort Would Look Like

The PO described strategic calls: "we dont do claude call just for fun... we do them strategically with the right configurations appropriate to the case, this include everything including the effort setting."

Stage-aware effort means:

| Situation | Suggested Effort | Why |
|-----------|-----------------|-----|
| Conversation stage (understanding requirements) | high | Deep reasoning needed to extract meaning |
| Analysis stage (examining codebase) | high | Thoroughness needed for accurate assessment |
| Investigation stage (exploring options) | high | Breadth needed for comprehensive exploration |
| Reasoning stage (planning approach) | high | Precision needed for correct plan |
| Work stage (executing confirmed plan) | medium | Plan is confirmed, execution is more mechanical |
| Heartbeat with no work | low | Status check doesn't need deep reasoning |
| CRON: security scan | high | Thoroughness critical for security |
| CRON: daily summary | low | Routine data aggregation |
| Review processing | medium-high | Reading work carefully but following established protocol |

### Three Configuration Surfaces (Currently Independent)

1. **Dispatched tasks:** brain's model_selection.py + backend_router.py decide model and effort at dispatch time
2. **Heartbeats:** static effortLevel in settings.json per agent
3. **CRONs:** per-job --model and --thinking flags

These are NOT connected. A unified system where the brain manages all three would:
- Use the same decision dimensions (fleet-elevation/23: model, effort, context, max_turns, mode, budget, role, task, fleet state)
- Adapt based on current situation, not static config
- Respect budget constraints across all three surfaces

This is a brain evolution task, not a configuration task. The infrastructure supports it (model override per heartbeat, per CRON, per dispatch). The decision logic needs to be built.

### The "ultrathink" Keyword

Including "ultrathink" anywhere in a prompt forces high effort for that single turn. The fleet could use this strategically:
- In CRON messages for critical operations: "ultrathink: Execute thorough security scan..."
- In dispatch messages for complex tasks: "ultrathink: This is an L5 epic requiring deep analysis..."
- In heartbeat wake messages for urgent situations: "ultrathink: Critical security alert requires deep analysis..."

This is a tactical tool, not a strategic system. The strategic system is the unified effort management from the brain.

---

## 4. Hook-Based Monitoring — PO Observation

### The PO's Idea

The PO described connecting via a stream to a selected agent to see their current feed — observing what the agent is doing in real-time.

### Technical Implementation Path

Claude Code hooks can POST data to external endpoints on every lifecycle event. The pattern:

**Configure PostToolUse HTTP hook per agent:**
- Fires after every tool call
- POSTs JSON payload to monitoring endpoint
- Async (non-blocking — doesn't slow agent)
- Payload includes: tool_name, tool_input (parameters), tool_output (result), timestamp, agent_name, session_id

**Monitoring service receives and displays:**
- Real-time feed of agent activity
- Filterable by agent, by tool type, by time
- Searchable for specific operations
- PO connects via web browser to see live feed

**Configuration pattern:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:XXXX/agent-feed",
            "async": true
          }
        ]
      }
    ]
  }
}
```

### What Data Is Available at Each Event

| Event | Available Data |
|-------|---------------|
| PreToolUse | tool_name, tool_input, tool_arguments |
| PostToolUse | tool_name, tool_input, tool_output, success/failure |
| SessionStart | session_source (startup/resume/clear/compact) |
| SubagentStart | sub-agent name, model, tools |
| FileChanged | file_path, change_type |
| PermissionRequest | permission_type, tool_name |

### Additional Monitoring Capabilities

**Trail enhancement:** PostToolUse hooks could record every tool call to the fleet trail system (board memory tagged trail + task:{id}), ensuring trail completeness regardless of whether individual tools record trail events.

**Cost tracking:** PostToolUse hooks could aggregate token usage per agent per session, feeding the budget monitor with real-time cost data instead of periodic API queries.

**Quality metrics:** PostToolUse hooks could track tool call patterns — how many commits before completion, how many retries on failures, which tools each agent uses most — feeding the immune system's disease detection.

**Behavioral analysis:** PreToolUse hooks could detect suspicious patterns in real-time — agent trying to call fleet_commit during analysis stage (before the MCP stage gate catches it), agent making unusually many API calls, agent accessing files outside its task scope.

---

## 5. Session Management — Context Awareness and Control

### The PO's Requirements (from context-window-awareness-and-control.md)

| ID | Requirement |
|----|-------------|
| CW-01 | Know the context window size — validate 1M or 200K |
| CW-02 | Awareness of cost dynamics — 1M context = faster quota drain |
| CW-03 | Strategic compaction — not premature, not too late |
| CW-04 | Efficient context regathering — recover from memory not full re-reads |
| CW-05 | Prevent context bloat — shouldn't fill with "just a few thousand lines" |
| CW-06 | Control and prove it — document settings, configurations, awareness |

### Context Visibility

The IDE and Claude Code expose context usage per turn:
- context_window.context_window_size — total capacity (200K or 1M)
- context_window.used_percentage — how full
- context_window.remaining_percentage — how much left
- context_window.current_usage.input_tokens — this turn's input
- context_window.total_input_tokens — cumulative session input

The model receives awareness via system blocks:
```xml
<budget:token_budget>1000000</budget:token_budget>
<system_warning>Token usage: 35000/1000000; 965000 remaining</system_warning>
```

### Context as Cost Multiplier

Claude Code sends FULL conversation history as input tokens on every API call:
- Turn 1: context = 10K tokens x 1 API call = 10K input tokens
- Turn 5: context = 80K tokens x 3 API calls = 240K input tokens
- Turn 10: context = 200K tokens x 5 API calls = 1M input tokens
- Turn 15: context = 500K tokens x 8 API calls = 4M input tokens

Each "edit this file" command can consume 50K-150K tokens from context multiplication.

### Strategic Compaction (Brain Step 10 Design)

From fleet-elevation/23:

The brain manages two parallel countdowns:
1. **Context remaining per agent** — organic awareness at 7% and 5%
2. **Rate limit session usage fleet-wide** — awareness at 85% and 90%

Session management logic:
- DO NOT dispatch 1M context tasks near rate limit rollover
- Near rollover, evaluate each agent's context:
  - Does agent have upcoming work needing this context? Keep if yes.
  - Is context over ~40-80K tokens (threshold to tune)? Consider compacting.
  - If no predicted need: dump as smart artifacts, fresh session
  - If related work coming: synthesized re-injection later
  - If unrelated work: simply new task, no re-injection needed
- Force compact IS appropriate near rollover for heavy contexts
  - Allow going over 90% rate limit budget for compacting itself
  - The compaction cost saves more than it spends
- After rollover, properly put agents back on track
  - Fresh sessions where needed
  - Re-inject synthesized context where work continues

Aggregate context math:
- 5 x 200K = 1M tokens re-sent on rollover (significant on 5x Pro)
- 2 x 1M = 2M tokens re-sent (exceeds 5x Pro window)
- Brain must calculate total fleet context cost vs remaining quota

### Connection to Skills and Tools

The context budget affects how many skills can be loaded (max 150 skills, max 30K chars for skills prompt). If an agent has 100+ skills plus large TOOLS.md plus dynamic context, the total system prompt becomes very large. The brain needs to be aware of:
- Skill injection size per agent
- TOOLS.md injection size per agent
- Dynamic context size per agent
- Total system prompt size
- Remaining context window for actual work

This feeds back into the skill curation decision: each skill must earn its place in the agent's context. Quality over quantity.

### Statusline for Agent Monitoring

Claude Code's /statusline generates a shell script for persistent status display:

```bash
#!/bin/bash
input=$(cat)
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
MODEL=$(echo "$input" | jq -r '.model.display_name')
FILLED=$((PCT * 10 / 100))
BAR=$(printf '%*s' "$FILLED" | tr ' ' '#')$(printf '%*s' $((10-FILLED)) | tr ' ' '-')
echo "[$MODEL] $BAR $PCT%"
```

This gives real-time context awareness — directly addressing CW-01 and CW-06. The fleet could configure per-agent statuslines that include context %, cost, rate limit position.

---

## 6. How These Capabilities Connect to the Fleet

### The Strategic Call Decision (9 Dimensions from fleet-elevation/23)

Every Claude call has 9 configuration axes the brain weighs:

1. **Model selection** — opus for deep reasoning, sonnet for standard, haiku/LocalAI for simple
2. **Effort level** — affects thinking depth and token usage
3. **Context size/strategy** — 1M vs 200K, continue vs fresh vs compact
4. **Max turns** — tool-call cycles before stopping
5. **Mode** — think (read-only), edit (modifications), act (commands)
6. **Budget constraints** — current mode, rate limit position
7. **Agent role** — PM/fleet-ops default opus, workers default sonnet
8. **Task properties** — type, stage, phase, story points
9. **Fleet state** — storm severity, aggregate context pressure

These dimensions apply to ALL Claude calls — dispatch, heartbeat, CRON, sub-agent spawn, Agent Team teammate creation. Today they're independently configured across different surfaces. The elevation path is unifying them under the brain's strategic decision logic.

### The Autocomplete Chain Enhancement

Sub-agents, Agent Teams, extended thinking, and monitoring all strengthen the autocomplete chain:

- **Sub-agents** — agent naturally delegates when the description matches (structural prevention of context bloat)
- **Agent Teams** — complex tasks naturally split across teammates (structural prevention of serial bottlenecks)
- **Extended thinking** — right effort level means agent thinks deeply when needed, quickly when routine (structural matching of reasoning to need)
- **Monitoring hooks** — every operation observable (structural visibility for PO and immune system)

### The Anti-Corruption Enhancement

These capabilities also strengthen anti-corruption Line 1 (structural prevention):

- Sub-agent isolation prevents context contamination between tasks
- Agent Team task lists prevent scope creep (tasks are defined, not open-ended)
- Extended thinking at high effort for planning stages reduces lazy/shallow plans
- Monitoring hooks catch deviations in real-time (not just at review stage)

---

## 7. Implementation Considerations

### Sub-Agent Definitions Need Per-Role Design

Each role's sub-agents need:
- What the role actually needs to delegate (observed from real usage)
- What model is cost-appropriate for each delegation type
- What tools are necessary and sufficient (principle of least privilege)
- What isolation mode protects against context contamination
- What the description says (drives auto-delegation accuracy)

This is NOT a one-time configuration — it evolves as agents work and patterns emerge. Start with the most obvious delegations (code-explorer for architect, test-runner for QA) and expand based on observed needs.

### Agent Teams Needs Architecture Review

Before deploying Agent Teams fleet-wide:
- How does it interact with the fleet orchestrator? (complementary or conflicting?)
- What permissions do teammates get? (inherit lead's — is this appropriate?)
- How does it interact with the fleet's heartbeat system? (separate sessions)
- What happens when a team session ends? (teammates orphaned?)
- Cost implications? (each teammate is a full Claude instance)

This is a strategic evaluation, not a configuration task.

### Extended Thinking Unification Needs Brain Evolution

Three independent effort configuration surfaces (dispatch, heartbeat, CRON) need a unified system. This is part of brain evolution (fleet-elevation/04, fleet-elevation/23) — not a standalone task. The infrastructure supports per-call model/effort override. The decision logic needs to be built.

### Monitoring Endpoint Needs Building

The PO's agent observation idea requires:
- A monitoring service that receives HTTP hook payloads
- A web interface for real-time agent feed display
- Per-agent filtering and search
- Authentication (PO access only)
- Storage for historical activity (how long to keep?)

This could be a simple Flask/FastAPI service with WebSocket feed to a browser, or it could leverage existing infrastructure (IRC channels already show agent activity, The Lounge provides web access). The monitoring service is additional tooling, not a fleet core system.
