---
title: "Deterministic Bypass Design — E003"
type: reference
domain: architecture
status: draft
created: 2026-04-09
updated: 2026-04-09
tags: [E003, brain, deterministic, bypass, cost, intelligence]
sources: [fleet/cli/orchestrator.py, fleet/core/brain_writer.py]
epic: E003
phase: "1 — Design"
---

# Deterministic Bypass Design

## PO Directive

> "we need to be smart and fine tune the brain we know that a lot does not require agent."

## Principle

Every operation that can be decided in Python ($0) should be decided in Python. Claude calls are reserved for work that actually needs reasoning. The brain intercepts operations and handles them deterministically when the outcome is predictable.

## What Already Bypasses Claude

| Operation | How | Cost |
|-----------|-----|------|
| Brain-evaluated heartbeats | write_brain_decisions() checks mentions/tasks/directives → silent if nothing | $0 for idle agents |
| Stage auto-set | get_initial_stage() maps readiness → stage from methodology.yaml | $0 per dispatch |
| Contribution auto-creation | detect_contribution_opportunities() from synergy matrix | $0 per reasoning task |
| Contribution completeness gate | check_contribution_completeness() | $0 per dispatch |
| Phase gate check | is_phase_gate() from phases.yaml | $0 per dispatch |
| Storm severity evaluation | StormMonitor.evaluate() counts indicators | $0 per cycle |
| Budget quota check | BudgetMonitor.check_quota() reads OAuth API (cached 5min) | $0 per cycle |
| Parent evaluation | All children done → parent to review | $0 per cycle |
| Trail recording | TrailRecorder writes to board memory | $0 (MC API, not Claude) |
| Context strategy | ContextStrategy.evaluate() checks thresholds | $0 per cycle |

## What STILL Uses Claude Unnecessarily

| Operation | Current | Could Be Deterministic |
|-----------|---------|----------------------|
| Simple task assignments | PM heartbeats, reads context, assigns via fleet_task_create | Brain could auto-assign based on task_type → agent mapping from agent-tooling.yaml |
| Status-only heartbeats | Agent heartbeats just to report "no work" | Already handled by brain_evaluated heartbeats → silent |
| Approval routing | Orchestrator wakes fleet-ops for every review task | Could auto-approve tasks that meet ALL structural checks (trail complete, tests pass, criteria met) — PO would need to opt in |
| Gate response processing | PM heartbeats to check if PO responded to gates | Brain could read board memory for PO gate responses and advance automatically |
| Contribution task creation | Currently in orchestrator Step 2.5 | Already deterministic ✓ |
| Stale task detection | Fleet-ops heartbeats to check board health | Brain already has health_check step — could post alerts directly |

## Proposed New Bypasses

### 1. Auto-assign from task_type

When a task enters inbox with task_type set but no agent_name:

```python
TYPE_TO_AGENT = {
    "epic": "architect",          # Architect breaks down epics
    "story": "project-manager",   # PM triages stories
    "bug": "software-engineer",   # Engineer fixes bugs
    "security": "devsecops-expert",
    "docs": "technical-writer",
    "infra": "devops",
}
```

This saves a PM heartbeat cycle (Claude call) for obvious assignments. PM still reviews and can reassign.

### 2. Auto-process PO gate responses

When PO posts to board memory with tags [gate, approved]:
- Brain reads the gate response
- Advances readiness to 99
- Task becomes dispatchable
- No PM heartbeat needed to notice and process

### 3. Auto-alert for stale conditions

Instead of fleet-ops heartbeating to discover stale tasks:
- Brain checks in health step (already exists)
- Posts alert to board memory directly
- Notifies IRC
- Fleet-ops only wakes for actual reviews

### 4. Auto-acknowledge simple messages

When an agent receives a status question (@mention "what's your status?"):
- Brain reads the agent's current task state
- Posts a formatted status update from pre-embed data
- No Claude call needed for "my task is X, stage Y, readiness Z"

## Implementation Priority

1. **Auto-process gate responses** — high value, saves PM cycles, straightforward
2. **Auto-alert stale conditions** — already partially in health_check step, enhance
3. **Auto-assign from task_type** — medium value, obvious cases only
4. **Auto-acknowledge status** — lower priority, nice to have

## Relationships

- PART_OF: E003 (Brain Evolution — intelligence)
- RELATES_TO: E008 (Lifecycle — fewer Claude calls = lower cost)
- RELATES_TO: E006 (Budget — deterministic bypass is the ultimate economy)
- RELATES_TO: E012 (Autonomous — brain handles routine, agents handle complex)
