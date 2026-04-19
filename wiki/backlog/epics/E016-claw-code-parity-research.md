---
title: "Claw Code Parity Research"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-19
tags: [claw-code, aicp, parity, rust, features, localai, independence]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Claw Code Parity Research

## Summary

Research ultraworkers/claw-code-parity for AICP features the fleet needs. Understand what Claude Code provides that AICP lacks. The AICP mission is LocalAI independence — running fleet operations on local hardware when Claude is unavailable or for cost reduction. Claw-code-parity is a Rust reimplementation that shows what's possible.

> "This is going to require ourself to master our full product. This will also require us to understand all the proper plugins and tools and skills and commands. It all come together to so many different level and for the lacking feature in aicp we will look at how it was done here: https://github.com/ultraworkers/claw-code-parity"

## Research Findings

| Feature | Claude Code | Claw Code Parity | AICP Status |
|---------|------------|------------------|-------------|
| /agents | Yes — sub-agent spawning | 177K stars Rust reimpl | Not implemented |
| /hooks | Yes — PreToolUse, PostToolUse, etc. | Reimplemented | Not implemented |
| /mcp | Yes — MCP server integration | Reimplemented | Not implemented |
| /skills | Yes — SKILL.md discovery | Reimplemented | Not implemented |
| /plan | Yes — implementation planning | Reimplemented | Not implemented |
| /review | Yes — code review | Reimplemented | Not implemented |
| /tasks | Yes — task tracking | Reimplemented | Not implemented |

## Goals

- Understand which Claude Code features the fleet depends on
- Identify which features AICP needs to implement for LocalAI independence
- Research claw-code-parity's architecture for implementation guidance
- Prioritize AICP features by fleet dependency (what breaks without Claude?)

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Understand which Claude Code features the fleet depends on
- [ ] Identify which features AICP needs to implement for LocalAI independence
- [ ] Research claw-code-parity's architecture for implementation guidance
- [ ] Prioritize AICP features by fleet dependency (what breaks without Claude?)

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- devops-expert-local-ai (AICP repo) — LocalAI inference, basic agent capabilities
- fleet/core/backend_router.py — routes tasks to claude-code or localai backend
- fleet/core/model_selection.py — model selection per task complexity
- fleet/gateway/executor.py — execute_via_openai_compat() for LocalAI calls
- docs/milestones/active/strategic-vision-localai-independence.md — AICP vision

## Phases

### Phase 0: Research

- [ ] Deep-dive claw-code-parity architecture (how they reimplemented each feature)
- [ ] Map fleet's Claude Code dependencies (which features are critical vs nice-to-have)
- [ ] Evaluate AICP's current capability gaps against fleet requirements
- [ ] Research LocalAI v4.0 agent features (knowledge bases, agent mode)

### Phase 1: Design

- [ ] Design AICP feature roadmap aligned with fleet needs
- [ ] Design the bridge between fleet and AICP (router_unification.py is schema only)
- [ ] Design graceful degradation (what happens when Claude is unavailable)

### Phase 2: Implement (in AICP repo)

- [ ] Implement priority features in AICP
- [ ] Wire fleet router to AICP for LocalAI tasks
- [ ] Test fleet operation with mixed Claude + LocalAI backend

## Relationships

- RELATES TO: [[Multi-Model Strategy]] (LocalAI is one of the models)
- RELATES TO: [[RAG/Knowledge System (LightRAG)]] (LocalAI provides embeddings for LightRAG)
- RELATES TO: [[Budget & Tempo Modes]] (LocalAI enables economic budget mode)
