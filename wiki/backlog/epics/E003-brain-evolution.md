---
title: "Brain Evolution"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [brain, orchestrator, context, effort, lifecycle, dispatch, intelligence]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
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

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Brain avoids dispatching work that can be handled deterministically
- [ ] Context-aware compaction strategy (detect approaching limits, prepare, trigger if needed)
- [ ] Adaptive effort escalation (stage → effort → model → source)
- [ ] Fine-tuned heartbeat timing (responsive but not wasteful)
- [ ] Automatic contribution subtask creation from synergy matrix
- [ ] IDLE/SLEEPING/OFFLINE evaluation without wasting Claude calls
- [ ] Session management across context compactions

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Document — COMPLETE

- [x] Audit current orchestrator 13-step cycle → [brain-audit.md](../../domains/architecture/brain-audit.md)
- [x] Document what's intelligent (brain-evaluated heartbeats, storm response, Navigator integration)
- [x] Document what's missing (contribution wiring, gate processing, cross-task propagation, context strategy)
- [x] Map effort escalation (model_selection.py has stage-aware effort floors, needs adaptive logic)
- [x] Document heartbeat gate (heartbeat_gate.py works, brain_writer.py writes decisions)

**Key finding:** Brain doesn't need a rewrite — it needs **wiring.** The modules exist (contributions.py, heartbeat_gate.py, phases.py, event_chain.py). The orchestrator cycle needs new steps that CALL them. Layer 1 (poll cycle) is solid. Layers 2 (chain registry) and 3 (logic engine) are spec-only. Layer 2 can wait — polling at 30s is adequate. Layer 3 can wait — hardcoded logic works for MVP. The critical gap is contribution auto-creation from synergy matrix.

### Phase 1-2: Design & Implement — PARTIALLY DONE

**Contribution wiring (DONE — 2026-04-09):**
- [x] Contribution auto-creation: Step 2.5 in orchestrator creates subtasks from synergy matrix when tasks enter REASONING
- [x] Contribution completeness gate: dispatch blocks WORK stage until required contributions received
- [x] Idempotent: skips if contribution children already exist
- [x] IRC notification when contributions created
- [x] Full test suite green (2,347 tests)

**Remaining:**
- [ ] Design deterministic operations that bypass Claude entirely
- [ ] Design the context strategy module (when compact, when fresh, when continue)
- [ ] Design unified effort decision logic across dispatch/heartbeat/CRON
- [ ] Design heartbeat timing optimization (responsive but economical)
- [ ] Scaffold context strategy module in fleet/core/

### Phase 3: Continue Implementation

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

- BUILDS ON: [[Agent Directive Chain Evolution]] (brain injects context)
- BUILDS ON: [[Chain/Bus Architecture]] (brain coordinates chains)
- ENABLES: [[Agent Lifecycle Fine-Tuning]] (brain controls timing)
- ENABLES: [[Full Autonomous Mode]] (brain drives autonomous operation)
- RELATES TO: [[Budget & Tempo Modes]] (brain respects budget modes)
- RELATES TO: [[Brain (Orchestrator) Audit — E003 Phase 0]]
- RELATES TO: [[Context Strategy Design — E003]]
- RELATES TO: [[Deterministic Bypass Design — E003]]
- RELATES TO: [[Effort Escalation Design — E003]]
