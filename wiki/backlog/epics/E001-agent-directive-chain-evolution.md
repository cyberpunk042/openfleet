---
title: "Agent Directive Chain Evolution"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-08
tags: [agents, directive-chain, autocomplete, templating, injection, tools-md, heartbeat, identity]
---

# Agent Directive Chain Evolution

## Summary

Full revision of all agent files — not just one file, but the complete templating, injection, structure, pattern explanation, and autocomplete chain. Elevate every position of the 7-position directive chain (IDENTITY → SOUL → CLAUDE.md → TOOLS.md → AGENTS.md → context/ → HEARTBEAT.md) to gold standard quality. Address TOOLS.md size limitations. Consider domain-split files, extended files, per-role files.

> "I feel like we need to revise everything about all agents, not just one of their files, the whole things and the templating and the injection and the structure and pattern explanation before autocomplete and so on... we need to do a gold job, we need to elevate the quality and the standard."

> "I think It fits perfectly with the tools.md limitations (more focus). Not that we cannot have other .md files for example per domains or with a folder or a main and extended one or a main and per role one and things like this."

> "we need to do the right directive so the AI know if it need to use this bus or this bus and know that it will do this chain naturally and do this and that and so on.... we need to give everything and give even the method for the current stage and so on... its all about focusing on the current task for heartbeat and following a logical pattern with the injected data making sure we interconnect the idea and set a proper autocomplete chain and make sure that the moment to create the artifact(s) its easy and natural and intelligent."

## Goals

- Revise every agent file across all 10 agents for quality, consistency, and completeness
- Address TOOLS.md 4000-char truncation in gateway executor (311-363 lines won't fit)
- Design file split strategy: main + extended, domain folders, per-role files
- Ensure the autocomplete chain naturally leads agents to the correct tool/bus/chain
- Make artifact creation easy and natural at every methodology stage
- Respect operational modes, events, notifications, sub-tasks, comments, relations, cowork, stages, gates, states, transfers, trails, mentions
- Apply SRP, Domain, Onion standards to agent file structure

## Phases

### Phase 0: Document & Audit

- [x] Audit gateway executor `_build_agent_context` — **4000-char truncation per file** (8000 for context/)
- [x] Measure actual char counts for all agent files across 10 agents

**CRITICAL FINDING:** TOOLS.md is 15,000-18,000 chars. Truncated to 4,000. Agents see ~22%. NEVER see: role group calls, skills, sub-agents, CRONs, standing orders, hooks. All 78 skills INVISIBLE through local gateway.

| File | Typical Size | Limit | Lost |
|------|-------------|-------|------|
| TOOLS.md | 15-18K | 4,000 | 11-14K (78%) |
| AGENTS.md | 3.5-4.5K | 4,000 | 0-500 |
| HEARTBEAT.md | 1.4-6.2K | 4,000 | 0-2.2K (PM worst) |
| CLAUDE.md | 3.0-3.9K | 4,000 | OK |
| SOUL.md | 2.6-3.6K | 4,000 | OK |
| IDENTITY.md | 1.5-2.7K | 4,000 | OK |
| context/*.md | varies | 8,000 each | Multiple files OK |

**Design options identified:**
1. Increase truncation limit (may hit LLM system prompt ceiling)
2. Split TOOLS.md into multiple files under 4000 each
3. Move role-specific content to context/ (8000 limit, multiple files)
4. Real gateway (OpenArms) may not have this limit — MUST RESEARCH
5. Compress: shorter descriptions per tool
6. Hybrid: critical summary in TOOLS.md, full reference in context/

- [ ] **Research how REAL gateway (OpenArms/OpenClaw) handles file injection**
- [ ] Map operational modes, event types, notification paths agents need
- [ ] Document what first 4000 chars of TOOLS.md actually contains per agent

### Phase 1: Design

- [ ] Design file split strategy for TOOLS.md (main + extended? domain folders? per-stage files?)
- [ ] Design how the gateway should handle extended files (modify executor? new injection mechanism?)
- [ ] Design the autocomplete chain engineering — how each position flows into the next
- [ ] Design per-stage method sections that tell agents exactly what to do at each stage
- [ ] Design the artifact creation flow — what makes it "easy and natural"
- [ ] Design the chain/bus selection directive — how agents know which propagation bus to use
- [ ] Design the agent identity structure for multi-fleet support (fleet number, unique names)
- [ ] Document all design decisions in wiki/domains/architecture/

### Phase 2: Scaffold

- [ ] Create new file templates for the split strategy
- [ ] Create per-role file structure if needed
- [ ] Scaffold the modified gateway executor if needed
- [ ] Create validation tests for the new structure

### Phase 3: Implement

- [ ] Rewrite/enhance IDENTITY.md templates for all 10 agents
- [ ] Rewrite/enhance SOUL.md templates for all 10 agents
- [ ] Rewrite/enhance CLAUDE.md templates for all 10 agents (within 4000 chars)
- [ ] Split/restructure TOOLS.md for all 10 agents
- [ ] Rewrite/enhance AGENTS.md for all 10 agents
- [ ] Rewrite/enhance HEARTBEAT.md templates for all 10 agents
- [ ] Update generation pipeline (generate-tools-md.py, generate-agents-md.py) for new structure
- [ ] Update provision-agent-files.sh for new file structure
- [ ] Update push-agent-framework.sh for new file structure

### Phase 4: Test & Validate

- [ ] Simulate what each agent sees at each position
- [ ] Verify truncation doesn't cut critical information
- [ ] Verify autocomplete chain flows naturally
- [ ] Diagram the injection flow for PO review
- [ ] Test with actual gateway (when available)

## Existing Foundation

- 10 role-specific IDENTITY.md, SOUL.md, CLAUDE.md templates in agents/_template/
- 10 HEARTBEAT.md templates in agents/_template/heartbeats/
- Generation pipeline: generate-tools-md.py (7 layers), generate-agents-md.py (synergy)
- Gateway executor: gateway/executor.py `_build_agent_context` (8-position injection)
- 78 workspace skills, 66 chain docs, 13 hooks already built

## Relationships

- ENABLES: E002 (Chain/Bus Architecture — agents need to know the chains)
- ENABLES: E012 (Full Autonomous Mode — agents need complete directives)
- RELATES_TO: E003 (Brain Evolution — brain decides what to inject)
- RELATES_TO: E014 (Autocomplete Web — the map feeds into directive content)
- DEPENDS_ON: E007 (Plugin/Skill Ecosystem — agents need to know their tools)
