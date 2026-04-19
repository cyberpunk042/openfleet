---
title: "Signatures & Transparency"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [signatures, labor-stamps, transparency, provenance, identity, trainee, metrics]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Signatures & Transparency

## Summary

Agent signatures at every level — individual tools, tool chains, and group calls. Use agent identity + metrics + settings to generate transparency. Trainee/model flagging so artifacts show what produced them. Extend labor stamps from task-level to operation-level.

> "its important they do signatures too, a bit like the idea of saying all the detail about the effort, context size, consumed and etc.... this way we use the agent identity and all his metrics and settings to actually generate transparency. and obviously it needs to be done well and that plays at multiple level, from individual tools and tools chains and group calls."

> "I think the LocalAI work will also need to be flagged as trainee's work like any other variant in what was used to generate the artifacts. making sure that when the agents leave their marks we know what produced it."

## Goals

- Signatures on tool calls: agent identity, model, effort, context size at call time
- Signatures on chains: aggregate stamp for multi-surface operations
- Signatures on group calls: composite stamp covering all operations in the tree
- Trainee flagging: LocalAI, MiMo, Qwen, free model output marked in labor stamps
- PR body, completion comments, board memory, Plane comments all carry provenance
- Fleet-ops can see at review time: what model produced this, at what effort, how much context was used

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Signatures on tool calls: agent identity, model, effort, context size at call time
- [ ] Signatures on chains: aggregate stamp for multi-surface operations
- [ ] Signatures on group calls: composite stamp covering all operations in the tree
- [ ] Trainee flagging: LocalAI, MiMo, Qwen, free model output marked in labor stamps
- [ ] PR body, completion comments, board memory, Plane comments all carry provenance
- [ ] Fleet-ops can see at review time: what model produced this, at what effort, how much context was used

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- fleet/core/labor_stamp.py — DispatchRecord, assemble_stamp(), LaborStamp dataclass
- fleet/core/labor_analytics.py — per-agent, per-model analytics
- fleet/core/tier_progression.py — trainee/standard/expert/community tiers
- fleet/templates/ — PR body, completion comment, IRC templates (already reference labor stamp)
- TaskCustomFields: labor_backend, labor_model, labor_effort, labor_confidence, labor_cost_usd, labor_duration_s

## Phases

### Phase 0: Document & Research

- [ ] Audit current labor stamp coverage — what operations have stamps, what don't
- [ ] Audit what appears in PR bodies and completion comments today
- [ ] Document the identity fields available per agent (from agent.yaml, fleet identity)
- [ ] Map which operations should carry signatures (tools, chains, group calls)

### Phase 1: Design

- [ ] Design per-operation signature format (compact, parseable, human-readable)
- [ ] Design chain-level aggregate signature
- [ ] Design trainee/model flagging extension to labor stamps
- [ ] Design how signatures appear in each surface (PR, IRC, Plane, board memory)
- [ ] Design settings transparency (effort, model, context size, budget mode at time of work)

### Phase 2: Implement

- [ ] Extend labor stamp with per-operation signatures
- [ ] Add trainee flagging to all model sources
- [ ] Wire signatures into PR template, completion comment template, IRC templates
- [ ] Wire signatures into Plane comments
- [ ] Update fleet_task_complete chain to include enhanced labor stamp

### Phase 3: Test & Validate

- [ ] Verify PR bodies show model provenance
- [ ] Verify trainee-produced work is flagged
- [ ] Verify fleet-ops review context includes provenance data
- [ ] Verify analytics track per-model quality metrics

## Relationships

- BUILDS ON: [[Chain/Bus Architecture]] (chains produce the events signatures attach to)
- RELATES TO: [[Multi-Model Strategy]] (model provenance feeds into signatures)
- RELATES TO: [[Brain Evolution]] (brain decides model/effort → captured in signature)
- RELATES TO: [[Full Autonomous Mode]] (autonomous operation needs transparent provenance)
- RELATES TO: [[Federation & Multi-Fleet]] (signatures carry fleet identity across federation)
- RELATES TO: [[Effort Escalation Design — E003]] (effort level captured in labor stamp)
