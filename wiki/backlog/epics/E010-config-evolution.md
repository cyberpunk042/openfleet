---
title: "Config Evolution"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [readiness, progress, phases, delivery, config, work-readiness, work-progress]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Config Evolution

## Summary

Differentiate work_readiness (ready to start working on) from work_progress (ready to be reviewed). Evolve phase progression configuration. Flexible delivery phases. Make evolving requirements and phases a natural part of the system.

> "i realize we are also going to need a new readiness config, we have work_readiness and it seem to be confused with another needs which would more be more like work_progress, something that differentiate between, its ready to start working on and its ready to reviewed."

> "Things can evolve. The requirements, the things to test, the phases of the task, the various data blob for whatever different type we need + the main one and so on. We do not go small we go big... phases are important too. not to confuse with state and stage that relate to the preparing and processing than the delivery and the phases of this delivery. advancing as the stages advance and a deliverable can pass from ideal, to conceptual, to POC, to MVP, to Staging, to Production ready.... or alpha, beta, rc & etc..... this like the stages are not set in stone and are meant to allow mature delivery with docs defs and code docs and tests and security and logical work and not disconnected unless already planned otherwise need to plan this to continue"

## Goals

- Split task_readiness (0-99, pre-dispatch authorization) from task_progress (0-100, post-dispatch work tracking)
- task_readiness: PO controls, gates dispatch. 0=not started, 50=investigating, 80=reasoning, 99=ready to work
- task_progress: Agent drives, tracks work. 0=accepted, 30=implementing, 70=done, 80=challenged, 90=reviewed, 100=complete
- Make delivery phases (idea→conceptual→poc→mvp→staging→production) configurable and extensible
- Support custom progressions (release: alpha→beta→rc→release)
- Requirements can evolve at any stage — not locked once set

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Split task_readiness (0-99, pre-dispatch authorization) from task_progress (0-100, post-dispatch work tracking)
- [ ] task_readiness: PO controls, gates dispatch. 0=not started, 50=investigating, 80=reasoning, 99=ready to work
- [ ] task_progress: Agent drives, tracks work. 0=accepted, 30=implementing, 70=done, 80=challenged, 90=reviewed, 100=complete
- [ ] Make delivery phases (idea→conceptual→poc→mvp→staging→production) configurable and extensible
- [ ] Support custom progressions (release: alpha→beta→rc→release)
- [ ] Requirements can evolve at any stage — not locked once set

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- TaskCustomFields: task_readiness (int, 0-99), task_progress (int, 0-100) — ALREADY split in models.py
- config/methodology.yaml — stages with readiness_range per stage
- config/phases.yaml — 2 progressions (standard, release) with PO gates
- fleet/core/phases.py — loads phase config
- fleet/core/methodology.py — stage from readiness range

## Phases

### Phase 0: Document & Research

- [ ] Audit how task_readiness and task_progress are used today across all modules
- [ ] Audit how phases.yaml is consumed (is phase gate enforcement in orchestrator?)
- [ ] Document the confusion points — where does readiness get confused with progress?
- [ ] Map what "evolving requirements" means operationally (requirement changes mid-task)

### Phase 1: Design

- [ ] Design clear task_readiness semantics (PO-driven, gates dispatch)
- [ ] Design clear task_progress semantics (agent-driven, tracks work lifecycle)
- [ ] Design phase advancement protocol (who requests, who approves, what gates)
- [ ] Design requirement evolution handling (verbatim changes → what happens to in-progress work?)

### Phase 2: Implement

- [ ] Enforce task_readiness/task_progress separation across all MCP tools
- [ ] Wire phase gate enforcement into orchestrator
- [ ] Wire phase standards injection into agent context
- [ ] Build requirement evolution tracking (history of verbatim changes)

### Phase 3: Test & Validate

- [ ] Test readiness gates dispatch correctly
- [ ] Test progress tracks work lifecycle accurately
- [ ] Test phase advancement with PO gates
- [ ] Test requirement changes propagate to in-progress agents

## Relationships

- RELATES TO: [[Agent Directive Chain Evolution]] (agents need to understand readiness vs progress)
- RELATES TO: [[Brain Evolution]] (brain uses readiness for dispatch, progress for evaluation)
- RELATES TO: [[Full Autonomous Mode]] (autonomous mode depends on clear state semantics)
- RELATES TO: [[Chain/Bus Architecture]] (config changes propagate via chains)
- RELATES TO: [[Simulation & Validation]] (config changes need simulation validation)
- RELATES TO: [[Scaffold→Foundation→Infra→Features Pattern]] (phases are config dimension)
