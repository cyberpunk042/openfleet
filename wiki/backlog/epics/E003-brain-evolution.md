---
title: "Brain Evolution"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-08
tags: [brain, orchestrator, context, effort, lifecycle, dispatch, intelligence]
---

# Brain Evolution

## Summary

Evolve the orchestrator brain to avoid giving needless work to AI, manage context intelligently, escalate effort and model adaptively, coordinate chain execution, and make the fleet a proficient autonomous unit that doesn't waste breath yet is responsive and prompt.

> "Its important to consider the brain too. the orchestration and logic layers play an important part in avoiding to give needless work to the AI or even things that are not even logical to give to AI, especially in a fine-tuned fleet. The Brain is not called brain for nothing it is a critical part for the cortexes / agents to do their part."

> "we are going to need to fine tune the timing for the sleep and offline and silent heartbeat and all the reasoning and real logical settings for a proficient autonomous fleet. that do not waste breath and yet is very responsive and prompt to work. very strategical in context switching and mindful of the current context size relative to the next forced compact that require adapting preparing and potentially even triggering it ourself before rechaining to regather the context to continue working if necessary"

> "we need to be smart and fine tune the brain we know that a lot does not require agent."

> "There is a logic of escalation of effort and model and source that is also necessary also adaptive based on the settings."

## Goals

- Brain avoids dispatching work that can be handled deterministically
- Context-aware compaction strategy (detect approaching limits, prepare, trigger if needed)
- Adaptive effort escalation (stage → effort → model → source)
- Fine-tuned heartbeat timing (responsive but not wasteful)
- Automatic contribution subtask creation from synergy matrix
- IDLE/SLEEPING/OFFLINE evaluation without wasting Claude calls
- Session management across context compactions

## Phases

### Phase 0: Document

- [ ] Audit current orchestrator 13-step cycle — what's intelligent, what's dumb
- [ ] Document every decision point that currently wastes agent calls
- [ ] Document the context compaction problem and current handling
- [ ] Map the effort escalation logic (current vs desired)
- [ ] Document the heartbeat gate evaluation logic

### Phase 1: Design

- [ ] Design deterministic operations that bypass Claude entirely
- [ ] Design the context strategy module (when compact, when fresh, when continue)
- [ ] Design unified effort decision logic across dispatch/heartbeat/CRON
- [ ] Design the automatic contribution subtask creation from synergy matrix
- [ ] Design heartbeat timing optimization (responsive but economical)

### Phase 2: Scaffold

- [ ] Scaffold context strategy module in fleet/core/
- [ ] Scaffold unified effort decision module
- [ ] Scaffold contribution auto-creation module
- [ ] Define configuration surface for brain tuning

### Phase 3: Implement

- [ ] Implement deterministic bypass for simple operations
- [ ] Implement context strategy (compact detection, preparation, self-triggered compaction)
- [ ] Implement unified effort escalation
- [ ] Implement automatic contribution subtask creation
- [ ] Implement optimized heartbeat timing
- [ ] Wire to existing orchestrator cycle

### Phase 4: Test & Validate

- [ ] Simulate full cycle with deterministic bypass — verify no unnecessary agent calls
- [ ] Test context strategy under various context sizes
- [ ] Test effort escalation produces correct model/effort per situation
- [ ] Test contribution auto-creation from synergy matrix
- [ ] Measure heartbeat cost reduction vs responsiveness

## Existing Foundation

- Orchestrator: fleet/cli/orchestrator.py (13-step, 30s cycle)
- HeartbeatGate: deterministic evaluation for IDLE+ agents
- Budget Monitor: real quota tracking
- Storm Monitor: severity-based dispatch limiting
- Model Selection: stage-aware effort floors (built this session)
- Agent Lifecycle: ACTIVE → IDLE → SLEEPING → OFFLINE

## Relationships

- DEPENDS_ON: E001 (Agent Directive Chain — brain injects context)
- DEPENDS_ON: E002 (Chain/Bus Architecture — brain coordinates chains)
- ENABLES: E008 (Agent Lifecycle Fine-Tuning — brain controls timing)
- ENABLES: E012 (Full Autonomous Mode — brain drives autonomous operation)
- RELATES_TO: E006 (Budget & Tempo — brain respects budget modes)
