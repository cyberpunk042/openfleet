# Task × Pre-Embedded Data

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 3 of 8)

---

## What This Is

Before the agent even makes an MCP call, task data is already in its
session context. The gateway injects it when the agent is dispatched
for task work. The agent sees the task bundle in its system prompt.

This is different from MCP calls — the data is THERE before the agent
starts thinking. No tool call needed. Pre-embedded.

---

## How It Works

The orchestrator dispatches a task to an agent. The dispatch mechanism
sends a message to the gateway. The gateway starts (or resumes) the
agent's session. The agent's context includes:

1. **Agent identity** — from agent.yaml (already exists)
2. **CLAUDE.md** — project rules (already exists)
3. **context/ files** — persistent context files (already exists)
4. **Task pre-embed** — NEW: the task bundle, pre-assembled

The task pre-embed is built by the orchestrator at dispatch time and
injected into the agent's session via the gateway. The agent reads it
as part of its initial context without calling any tool.

---

## What Gets Pre-Embedded

A subset of the full task bundle — the essential data the agent needs
immediately:

- Task ID, title, status
- Verbatim requirement
- Current stage + stage instructions
- Readiness percentage
- Artifact completeness summary (not the full object — just what's
  missing and what to work on next)
- Last few comments (recent conversation with PO or reviewers)
- Any directives targeting this agent

NOT pre-embedded (too large, fetched via MCP if needed):
- Full artifact object
- Full comment history
- Full activity log
- Plane state details

---

## Foundation Milestones

### TP-F01: Task pre-embed data model
- Define what's included vs excluded
- Size budget (context/ files are max 1000 chars each in gateway)
- Format: structured text or JSON

### TP-F02: Pre-embed assembly function
- Build the pre-embed from task + methodology + recent comments
- Compact format within size budget
- Include actionable summary (what to do next)

---

## Infrastructure Milestones

### TP-I01: Gateway injection mechanism
- How does the pre-embed get into the agent's session?
- Option A: Write to agent's context/ directory before dispatch
- Option B: Include in dispatch message via chat.send
- Option C: Gateway API for session context injection
- Need to evaluate which mechanism the gateway supports

### TP-I02: Dispatch-time assembly
- Orchestrator builds pre-embed at dispatch time
- Passed to gateway as part of dispatch flow
- Fresh for each dispatch (not stale from previous cycle)

---

## Integration Milestones

### TP-G01: Wire to orchestrator dispatch
- _dispatch_ready_tasks builds pre-embed for each dispatched task
- Pre-embed included in dispatch payload

### TP-G02: Wire to gateway
- Gateway receives pre-embed and injects into session context
- Agent sees it on first context load

---

## Testing Milestones

### TP-T01: Pre-embed content verification
- Verify pre-embed contains correct task data
- Verify size within budget
- Verify format is agent-readable