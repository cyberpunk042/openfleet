---
title: "Operational Modes — Heartbeat vs Task, Injection Levels"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, E003, E008, operational-modes, heartbeat, task, injection, context]
sources:
  - id: po-feedback-2026-04-09
    type: documentation
    file: PO feedback 2026-04-09
epic: [E001, E003]
phase: "1 — Design"
---

# Operational Modes — Heartbeat vs Task

## Summary

Design for separating OpenFleet's operational modes — heartbeat vs task — that current agent files (CLAUDE.md, HEARTBEAT.md, TOOLS.md) conflate. Specifies per-mode injection depth, per-mode file ownership, and how Navigator assembles mode-appropriate context rather than one-size-fits-all content.

## PO Observation

> "isn't fleet_read_context() only for when you want to consult another task that you might not already have in your context? it's as if you were in mode no pre-injected context..."

> "Heartbeat is what the worker does when he is not working on a task. A task is what he does when he has something assigned to him. The way of working and what to do is completely different."

> "I see maybe two new config / parameters with multiple possible options."

## The Problem

Current agent files (CLAUDE.md, HEARTBEAT.md, TOOLS.md) conflate two completely different operational modes:

1. **Heartbeat mode** — agent wakes on CRON, checks for work, processes messages, does standing orders. Context is FULLY PRE-EMBEDDED. Agent doesn't need to call fleet_read_context() — the data is already in its system prompt.

2. **Task mode** — agent has been dispatched to work on a specific task. Context is FULLY PRE-EMBEDDED via task-context.md (autocomplete chain). Agent follows methodology stages. fleet_read_context() is only needed if pre-embed is stale or agent needs data about a DIFFERENT task.

The current CLAUDE.md says "fleet_read_context() FIRST — before any work." This is WRONG when pre-injection is active. The agent already has the data. Calling fleet_read_context() wastes a tool call and adds noise to context.

## What Already Exists (Infrastructure)

The two-path architecture is already built:

**Path A — Heartbeat:** CRON fires → brain_writer evaluates (wake/silent/strategic via .brain-decision.json) → if wake → gateway reads agent files + context/ → Claude session → agent follows HEARTBEAT.md
- AgentStatus: IDLE/SLEEPING/OFFLINE
- Context pre-embedded: fleet-context.md, knowledge-context.md, task-context.md (if in-progress)
- fleet_read_context() NOT needed — data already injected

**Path B — Task dispatch:** orchestrator Step 5 → writes task-context.md (autocomplete chain) + inject_content() into session → agent follows CLAUDE.md stage protocol
- AgentStatus: ACTIVE
- Context pre-embedded: task-context.md (10-section autocomplete chain), fleet-context.md
- fleet_read_context() NOT needed — data already injected

**Path C — Direct CLI (no brain, no gateway):** Manual testing
- No pre-embedded context at all
- fleet_read_context() REQUIRED — only way to get task data

The gateway, brain_writer, and orchestrator ALREADY differentiate Paths A and B. We don't need new infrastructure. We need the AGENT FILES to acknowledge which path they're on.

## Two Parameters (agent-visible, not new infrastructure)

### 1. `operational_mode`: heartbeat | task

Controls WHAT the agent does and WHICH directives apply. Already implicit in which context files are present — making it explicit.

**heartbeat:**
- Agent follows HEARTBEAT.md protocol (priority order: PO→messages→core job→proactive→health→OK)
- Context comes from fleet-context.md (fleet state, messages, directives, tasks, role data)
- Context comes from knowledge-context.md (Navigator: skills, sub-agents for current stage)
- If agent has an in-progress task → task-context.md also present
- fleet_read_context() NOT needed — data is pre-embedded
- Agent does NOT follow methodology stages on its own work — it processes the queue

**task:**
- Agent follows CLAUDE.md stage protocol (conversation→analysis→investigation→reasoning→work)
- Context comes from task-context.md (10-section autocomplete chain: identity→task→stage→verbatim→protocol→contributions→phase→action→chain)
- Context comes from fleet-context.md (fleet state, minimal)
- Context comes from knowledge-context.md (stage-specific skills)
- fleet_read_context() only if: pre-embed is stale, or need different task's data, or injection_level is none
- Agent follows the verbatim requirement and methodology protocol

### 2. `injection_level`: full | partial | none

Controls HOW MUCH context is pre-embedded before the agent starts.

**full (default):**
- All 8 injection positions filled (IDENTITY→SOUL→CLAUDE→TOOLS→AGENTS→context/→HEARTBEAT)
- fleet-context.md written every 30s by brain
- task-context.md written at dispatch with autocomplete chain
- knowledge-context.md written by Navigator with stage-specific content
- fleet_read_context() is OPTIONAL — only for refresh or different task data
- This is the normal operating mode

**partial:**
- Static files injected (IDENTITY, SOUL, CLAUDE, TOOLS, AGENTS, HEARTBEAT)
- fleet-context.md may be stale or minimal
- task-context.md may not have full autocomplete chain
- fleet_read_context() RECOMMENDED — supplement pre-embed with fresh data
- Used when: brain can't refresh context (MC down, orchestrator delayed)

**none:**
- Only CLAUDE.md injected (via gateway native read)
- No fleet-context.md, no task-context.md, no knowledge-context.md
- fleet_read_context() REQUIRED — agent must load all context from MCP
- Used when: lightweight session, testing, fallback, direct CLI dispatch
- This is the mode current CLAUDE.md implicitly assumes

## Impact on Agent Files

### CLAUDE.md — Stage Protocol Changes

Current (wrong for full injection):
```
1. fleet_read_context() — FIRST call
2. Read contributions...
3. fleet_task_accept(plan)
```

Correct for full injection:
```
Your task context is pre-embedded (see YOUR TASK, VERBATIM REQUIREMENT, 
STAGE PROTOCOL, INPUTS FROM COLLEAGUES sections above). 
If you need fresh data or a different task's context → fleet_read_context().
Otherwise, follow the stage protocol from your pre-embedded context.
```

Correct for no injection:
```
1. fleet_read_context() — load task data (required — no pre-injection)
2. Read contributions from context...
3. fleet_task_accept(plan)
```

### HEARTBEAT.md — Already Correct

HEARTBEAT.md already says "Your full context is pre-embedded... Read it FIRST. No tool calls needed for awareness." This is correct for heartbeat mode with full injection.

### TOOLS.md — fleet_read_context Description

Current:
```
### fleet_read_context
Load task data + colleague contributions
**When:** FIRST call — before any work
```

Should be:
```
### fleet_read_context
Load or refresh task data + colleague contributions
**When:** injection_level=none (required) | injection_level=full (only if need fresh data or different task)
```

## How the Brain Sets These

The orchestrator knows which mode the agent is in:

**Heartbeat trigger (CRON fires):**
```python
operational_mode = "heartbeat"
injection_level = "full"  # brain refreshed context this cycle
```

**Task dispatch:**
```python
operational_mode = "task"
injection_level = "full"  # brain wrote task-context.md with autocomplete chain
```

**Direct CLI dispatch (testing):**
```python
operational_mode = "task"
injection_level = "none"  # no brain, no pre-embed
```

**Gateway lightweight session:**
```python
operational_mode = "heartbeat"
injection_level = "partial"  # only HEARTBEAT.md injected, minimal context
```

These parameters get written to the agent's context/ files so the agent's CLAUDE.md/HEARTBEAT.md can branch on them.

## Implementation

### Config: agent.yaml addition

```yaml
operational_modes:
  heartbeat:
    injection_level: full        # brain pre-embeds everything
    directives: HEARTBEAT.md     # follow heartbeat priority protocol
    fleet_read_context: optional # data already pre-embedded
  task:
    injection_level: full        # brain pre-embeds autocomplete chain
    directives: CLAUDE.md        # follow stage protocol
    fleet_read_context: optional # data already pre-embedded
  task_no_inject:
    injection_level: none        # direct dispatch, no brain
    directives: CLAUDE.md        # follow stage protocol
    fleet_read_context: required # must load context via MCP
```

### Context file: mode indicator

Brain writes to fleet-context.md:
```
## OPERATIONAL MODE
mode: task
injection: full
fleet_read_context: optional — your task data is already pre-embedded above
```

Or for no injection:
```
## OPERATIONAL MODE
mode: task
injection: none
fleet_read_context: REQUIRED — call fleet_read_context() to load your task
```

### CLAUDE.md update

Add mode-awareness at the top of Role-Specific Rules:

```markdown
## Role-Specific Rules

**If your context shows `injection: full`:** Your task data is pre-embedded.
Read VERBATIM REQUIREMENT and STAGE PROTOCOL from your context above.
fleet_read_context() only if you need fresh data or a different task.

**If your context shows `injection: none`:** No pre-embedded data.
Call fleet_read_context() FIRST to load your task before any work.
```

## What This Fixes

1. Agents stop calling fleet_read_context() unnecessarily when data is pre-embedded
2. Heartbeat and task workflows have clear, separate directive chains
3. The "FIRST call" instruction only applies when injection is none
4. Skills and methodology change based on operational mode (heartbeat skills vs task skills)
5. Navigator can inject different content for heartbeat vs task mode (already partially in intent-map.yaml with heartbeat intents)

## Relationships

- PART_OF: E001 (Agent Directive Chain — this is the fix for the conflation)
- RELATES_TO: E003 (Brain — brain sets the mode)
- RELATES_TO: E008 (Lifecycle — heartbeat vs active mode)
- RELATES_TO: E014 (Navigator — different intents per mode)
