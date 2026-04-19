---
title: "Multi-Model Strategy"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [codex, mimo, qwen, turboquant, localai, routing, free-models, trainee]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Multi-Model Strategy

## Summary

Evolve beyond Claude-only to a use-case-based multi-model strategy. Codex for adversarial reviews. MiMo-V2-Pro for free reasoning. Qwen3.5-Omni for multi-modal. TurboQuant enabling LocalAI with smaller hardware. Free model load balancing via ClawRouters/LiteLLM. All with provenance tracking — agents mark what model produced each artifact.

> "New reality. I think we need to use Codex for certain task like adversarial reviews. (clearly not codex for everything, its bad at some things) I think there are plugins and you can plug it in easily we dont even need to pay I think? also needed a way to determine which one to use / which way to go."

> "then there is MiMo-V2-Pro and stuff like that that are free for appropriate task when available. Just like we want to use methodologies and skills. Not an always in, more like a use case strategy logic decision."

> "We also need to look more deeply into TurboQuant and Qwen models like Qwen3.5-Omni and use the full anatomy of the claude anatomy; commands, rules, skills, etc..."

> "I think the LocalAI work will also need to be flagged as trainee's work like any other variant in what was used to generate the artifacts. making sure that when the agents leave their marks we know what produced it."

## Research Findings

| Model/Tool | What | Cost | Integration |
|------------|------|------|-------------|
| Codex (OpenAI) | Adversarial reviews, task delegation | Free with API key | codex-plugin-cc for Claude Code |
| MiMo-V2-Pro (Xiaomi) | 1T reasoning model, 1M context | $1/M input, free API periods | OpenRouter, OpenClaw partner |
| Qwen3.5-Omni (Alibaba) | Omni-modal, 256k context, 113 languages | TBD | API available |
| TurboQuant (Google) | 6x memory compression, zero accuracy loss | Free (algorithm) | Enables smaller hardware for LLMs |
| ClawRouters | 50+ model routing, 60-90% savings | Free BYOK tier | OpenAI-compatible API |
| LiteLLM | 100+ model routing, auto-failover | Open source | Proxy/gateway |

## Goals

- Install Codex plugin for Claude Code agents (adversarial reviews)
- Evaluate MiMo-V2-Pro for reasoning tasks via OpenRouter
- Research TurboQuant impact on LocalAI viability (8GB+11GB setup)
- Design use-case routing logic (which model for which task type)
- Implement trainee/provenance flagging in labor stamps
- Evaluate free model load balancers (ClawRouters, LiteLLM)

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Install Codex plugin for Claude Code agents (adversarial reviews)
- [ ] Evaluate MiMo-V2-Pro for reasoning tasks via OpenRouter
- [ ] Research TurboQuant impact on LocalAI viability (8GB+11GB setup)
- [ ] Design use-case routing logic (which model for which task type)
- [ ] Implement trainee/provenance flagging in labor stamps
- [ ] Evaluate free model load balancers (ClawRouters, LiteLLM)

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Research

- [ ] Install and test codex-plugin-cc in a test workspace
- [ ] Test MiMo-V2-Pro via OpenRouter for a reasoning task
- [ ] Research TurboQuant availability for LocalAI models
- [ ] Evaluate ClawRouters vs LiteLLM for fleet routing
- [ ] Document Qwen3.5-Omni capabilities relevant to fleet tasks

### Phase 1: Design

- [ ] Design the use-case routing decision tree (task type → model)
- [ ] Design the trainee/provenance flagging system (extend labor stamps)
- [ ] Design the configuration surface for model routing (fleet.yaml or per-agent)
- [ ] Design the fallback chain (preferred model unavailable → next option)

### Phase 2: Scaffold

- [ ] Add codex-plugin-cc to agent-tooling.yaml for applicable agents
- [ ] Configure OpenRouter backend in backend_router.py
- [ ] Scaffold the model routing decision module
- [ ] Extend labor stamp with model_source field

### Phase 3: Implement

- [ ] Deploy codex plugin to fleet-ops and architect agents
- [ ] Wire MiMo-V2-Pro via OpenRouter as an additional backend
- [ ] Implement use-case routing in dispatch
- [ ] Implement trainee flagging in labor stamps
- [ ] Wire free model load balancer (if chosen)

### Phase 4: Test & Validate

- [ ] Test adversarial review with codex plugin
- [ ] Test reasoning task with MiMo-V2-Pro — compare quality to Claude
- [ ] Test trainee flagging appears in PR bodies and completion comments
- [ ] Validate routing logic selects correct model per task type

## Existing Foundation

- Backend router: fleet/core/backend_router.py (route_task, backends_for_mode)
- Model selection: fleet/core/model_selection.py (stage-aware effort)
- Labor stamps: fleet/core/labor_stamp.py (DispatchRecord, assemble_stamp)
- Plugin evaluation: config/plugin-evaluation.yaml (4 INSTALL, 5 DEFER, 3 SKIP)

## Relationships

- RELATES TO: [[Budget & Tempo Modes]] (cheaper models reduce cost)
- RELATES TO: [[Signatures & Transparency]] (model provenance in stamps)
- RELATES TO: [[Brain Evolution]] (brain decides routing)
- RELATES TO: [[Effort Escalation Design — E003]] (model+effort selection ladder)
- RELATES TO: [[Claw Code Parity Research]] (AICP LocalAI is one of the models)
- ENABLES: [[RAG/Knowledge System (LightRAG)]] (LocalAI provides embeddings)
