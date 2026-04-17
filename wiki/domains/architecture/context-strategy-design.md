---
title: "Context Strategy Design — E003"
type: reference
domain: architecture
status: draft
created: 2026-04-09
updated: 2026-04-09
tags: [E003, E008, context, compaction, strategy, session, rate-limit]
sources:
  - id: context-window-awareness-and-control
    type: documentation
    file: docs/milestones/active/context-window-awareness-and-control.md
  - id: 04-the-brain
    type: documentation
    file: fleet-elevation/04-the-brain.md
epic: E003
phase: "1 — Design"
confidence: medium
---

# Context Strategy Design

## Summary

E003 design of context strategy — how the orchestrator decides what to inject, at what depth, for which consumer, in a way that honors the two countdowns (session context budget + task budget). Ties tier-aware rendering, effort profiles, bypass heuristics, and Goldilocks identity into one coherent strategy.

## PO Directive

> "strategical in context switching and mindful of the current context size relative to the next forced compact that require adapting preparing and potentially even triggering it ourself before rechaining to regather the context to continue working if necessary"

## Problem

Two countdowns shape agent work:
1. **Context remaining** — Claude forces compaction when context fills. The agent loses context abruptly.
2. **Rate limit session** — 5-hour window with usage cap. Agents near the limit face rejection.

Without a strategy: agent works until forced compaction → loses context mid-task → regathers poorly → quality degrades. Or: agent hits rate limit → session killed → trail gap → review fails.

## Design: Progressive Response

### Context Percentage Thresholds

| Context Used | Action | Who Acts |
|-------------|--------|----------|
| < 70% | Normal operation | Agent works freely |
| 70% | **AWARE** — agent told "context at 70%" in pre-embed | Brain writes to context/ |
| 80% | **PREPARE** — agent should extract key state to artifacts | Brain warns, agent saves |
| 90% | **EXTRACT** — agent must dump working state to artifacts NOW | Brain forces extraction |
| 95% | **COMPACT** — brain triggers compaction proactively | Brain initiates, NOT forced |
| 100% | Claude forces compaction (AVOID — lost context) | System (uncontrolled) |

### How the Brain Knows

Session telemetry (session_telemetry.py) provides:
- `context_used_pct` — from Claude session JSON
- `context_window_size` — 200K or 1M
- `five_hour_used_pct` — rate limit window

The orchestrator reads this every 30s cycle and writes thresholds to context/.

### What "Extract" Means

At 80-90%, the agent needs to save working state externally:
1. Current task progress → `fleet_task_progress(summary)` — persists to MC
2. Current analysis/plan → `fleet_artifact_update()` — persists to Plane HTML
3. Key decisions → `fleet_chat()` → board memory — persists across sessions
4. Implementation state → `fleet_commit()` — persists to git

After extraction, a fresh session can regather from: task comments + artifact state + board memory + git log. Nothing critical lives only in context.

### What "Proactive Compact" Means

At 95%, instead of waiting for Claude's forced compaction (which is abrupt and loses nuance), the brain:
1. Triggers a session compact via gateway API (`sessions.compact`)
2. The compact preserves a synthesis of the conversation
3. The agent continues from the compacted state with full pre-embedded context

This is better than forced compaction because:
- Pre-embedded context (from fleet-context.md, task-context.md, knowledge-context.md) is refreshed by the orchestrator BEFORE the compacted session resumes
- The agent starts with fresh, complete pre-embed rather than a truncated conversation

### Rate Limit Strategy

| 5h Used | Action |
|---------|--------|
| < 70% | Normal |
| 70% | Inform agent — "rate limit at 70%, conserve when possible" |
| 85% | **CONSERVE** — brain lowers effort to "medium" for remaining work |
| 90% | **CRITICAL** — brain finishes current operation, no new dispatch |
| 95% | **STOP** — brain holds all dispatch, waits for rollover |

### Aggregate Fleet Math

10 agents × 200K context = 2M potential context pressure.
If 5 agents are near 80% simultaneously → aggregate rate limit risk.

The brain should stagger: don't compact all agents at once. Compact the least-active agent first. Space compactions by at least 2 minutes.

## Implementation Plan

### Module: fleet/core/context_strategy.py

```python
class ContextStrategy:
    """Evaluate and respond to context pressure per agent."""
    
    def evaluate(self, agent_name, context_pct, rate_limit_pct) -> ContextAction:
        """Returns: NORMAL, AWARE, PREPARE, EXTRACT, COMPACT, STOP"""
    
    def should_compact(self, agent_name, context_pct) -> bool:
        """Proactive compaction decision."""
    
    def should_dispatch(self, rate_limit_pct) -> bool:
        """Rate limit allows dispatch?"""
    
    def stagger_compactions(self, agents_near_limit) -> list:
        """Order agents for compaction to avoid simultaneous pressure."""
```

### Integration Points

1. **Orchestrator Step 0** (context refresh) — evaluate context strategy per agent, write warnings to context/
2. **Orchestrator Step 5** (dispatch) — check rate limit before dispatching
3. **Agent pre-embed** (task-context.md §7 Context Awareness) — already has the section, needs real data
4. **Gateway** — compact API call for proactive compaction

### What Agents See

In task-context.md (already designed in autocomplete chain §9 WHAT TO DO NOW):
```
Context: 82% used. PREPARE — save working state to artifacts before continuing.
Rate limit: 68%. Normal.
```

This appears in the agent's pre-embedded context every 30s. The agent doesn't need to poll — it's structural awareness.

## Depends On

- session_telemetry.py wired to orchestrator (Step 14 in path-to-live)
- Gateway compact API accessible from orchestrator
- Rate limit data from Claude OAuth API (budget_monitor.py already reads this)

## Relationships

- PART_OF: E003 (Brain Evolution)
- RELATES_TO: E008 (Lifecycle — compaction timing)
- RELATES_TO: E001 (Context Awareness section in CLAUDE.md and task-context.md)
