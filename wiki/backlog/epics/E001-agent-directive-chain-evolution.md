---
title: "Agent Directive Chain Evolution"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [agents, directive-chain, autocomplete, templating, injection, tools-md, heartbeat, identity]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
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

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Revise every agent file across all 10 agents for quality, consistency, and completeness
- [ ] Address TOOLS.md 4000-char truncation in gateway executor (311-363 lines won't fit)
- [ ] Design file split strategy: main + extended, domain folders, per-role files
- [ ] Ensure the autocomplete chain naturally leads agents to the correct tool/bus/chain
- [ ] Make artifact creation easy and natural at every methodology stage
- [ ] Respect operational modes, events, notifications, sub-tasks, comments, relations, cowork, stages, gates, states, transfers, trails, mentions
- [ ] Apply SRP, Domain, Onion standards to agent file structure

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Phases

### Phase 0: Document & Audit — COMPLETE

- [x] Audit gateway executor `_build_agent_context` — truncation per file
- [x] Measure actual char counts for all agent files across 10 agents
- [x] Research how REAL gateway (OpenArms/OpenClaw) handles file injection
- [x] Fix local executor to match real gateway (20K/file, 150K total, .env configurable)
- [x] Document gateway findings → [wiki/domains/architecture/gateway-file-injection.md](../../../wiki/domains/architecture/gateway-file-injection.md)
- [x] Map the full skill/plugin/pack ecosystem (1,100+ skills, 580+ plugins across sources)
- [x] Document per-agent ecosystem allocation → [wiki/domains/architecture/agent-ecosystem-allocation.md](../../../wiki/domains/architecture/agent-ecosystem-allocation.md)
- [x] Audit Navigator intent-map coverage (33/80 = 41%, 19 gaps) → [wiki/domains/architecture/navigator-intent-gap-analysis.md](../../../wiki/domains/architecture/navigator-intent-gap-analysis.md)

**KEY FINDINGS:**

1. **TOOLS.md bloat:** 15-18K per agent. 26 generic tools (6K identical across all) + skills/plugins/hooks/CRONs (~10K). Agents don't need most of it.

2. **Real gateway:** 20K/file, 150K total. Local executor fixed to match. But the PO directive is NOT "raise the limit" — it's "don't flood the agent."

3. **Ecosystem scale:** 1,100+ skills available across superpowers (30+), LerianStudio/ring (89), trailofbits (28 security), NeoLabHQ (14), borghei (225+), marketplace. 78 fleet-* skills are just our custom layer.

4. **Navigator gap:** Only 41% of role×stage intents defined. 8 P1 gaps (engineer heartbeat/conversation/analysis, devsecops heartbeat/work, devops heartbeat/reasoning/contribution). Zero pack skills in any intent. Zero sub-agent recommendations.

5. **Design principle confirmed:** Focused desk (TOOLS.md 2-4K) + dynamic room (Navigator per stage) + filing cabinet (skills on invoke). The desk stays the same size regardless of ecosystem expansion.

### Phase 1: Design — COMPLETE

**Core design:** [wiki/domains/architecture/tools-md-redesign.md](../../domains/architecture/tools-md-redesign.md)

- [x] Design the three-layer model (desk/room/cabinet) with clear ownership
- [x] Design per-role tool sets from tool-roles.yaml (what goes ON the desk)
- [x] Calculate per-role TOOLS.md size targets (2-5K, 77% avg reduction)
- [x] Design what moves from TOOLS.md to Navigator (skills, sub-agents, plugins → room)
- [x] Design what gets removed entirely (CRONs, hooks detail)
- [x] Design generation pipeline changes (9 sections → 5 sections) → [generate-tools-md-redesign.md](../../domains/architecture/generate-tools-md-redesign.md)
- [x] Design validation strategy (coverage checks, resilience)
- [x] Design concern separation verification (no mixing with CLAUDE.md/HEARTBEAT.md)
- [x] Design Navigator intent-map expansion → [navigator-intent-expansion.md](../../domains/architecture/navigator-intent-expansion.md)
- [x] Design generate-tools-md.py algorithm → concrete code spec
- [x] Verify tool-roles.yaml completeness — all 10 roles verified
- [ ] Design skill-stage-mapping.yaml expansion (pack skills in stage recommendations — tied to E007 Phase 1)
- [ ] PO review of three-layer model and per-role allocations

### Phase 2: Scaffold & Implement — IN PROGRESS

**TOOLS.md pipeline (DONE):**
- [x] Rewrite generate-tools-md.py — 5 focused sections, tool-roles.yaml filter
- [x] Regenerate TOOLS.md for all 10 agents (77% reduction: 167K → 38K total)
- [x] Update tests: focused size (1K-8K), required sections, chain awareness, no-bloat checks
- [x] Full test suite green: 2,347 passed

**Navigator intent-map (DONE):**
- [x] Expand intent-map.yaml: 33 → 45 intents
- [x] All 10 roles have heartbeat intents (was 3/10)
- [x] Pack skills in 29 intents (superpowers, ring, trailofbits, neolabhq, borghei)
- [x] Sub-agent recommendations in 29 intents
- [x] Full test suite green

**Gateway executor (DONE — previous session):**
- [x] Fix local executor to 20K/file, 150K total (.env configurable)
- [x] Bloat warnings at 8K per file

**CLAUDE.md templates (DONE):**
- [x] Rewrite all 10 CLAUDE.md templates — 8 sections per standard, all <4000 chars
- [x] Role-specific rules from fleet-elevation specs
- [x] Stage protocol, tool chains, contribution model, boundaries, anti-corruption

**HEARTBEAT.md templates (DONE):**
- [x] Rewrite all 11 heartbeat templates — universal priority order (PO→Messages→Core→Proactive→Health→OK)
- [x] 5 types: PM, Fleet-ops, Architect, DevSecOps, Worker (+ 6 per-role worker variants)
- [x] Role-specific core job sections with group call references

**AGENTS.md generation (VERIFIED):**
- [x] generate-agents-md.py already aligned — synergy matrix driven, focused output
- [x] All 10 AGENTS.md at 3.4K-4.5K — contribution relationships + colleague awareness

**Remaining:**
- [ ] Rewrite/enhance IDENTITY.md templates for all 10 agents (already good, may need minor updates)
- [ ] Rewrite/enhance SOUL.md templates for all 10 agents (already good, may need minor updates)
- [ ] Verify push-agent-framework.sh copies all files correctly on setup

### Phase 3: Test & Validate

- [ ] Simulate what each agent sees at each injection position
- [ ] Verify focused TOOLS.md + Navigator context covers all capabilities
- [ ] Verify autocomplete chain flows naturally (task-context.md 10 sections)
- [ ] Diagram the injection flow for PO review
- [ ] Test with actual gateway (when available)

## Existing Foundation

- 10 role-specific IDENTITY.md, SOUL.md, CLAUDE.md templates in agents/_template/
- 10 HEARTBEAT.md templates in agents/_template/heartbeats/
- Generation pipeline: generate-tools-md.py (7 layers), generate-agents-md.py (synergy)
- Gateway executor: gateway/executor.py `_build_agent_context` (8-position injection)
- 78 workspace skills, 66 chain docs, 13 hooks already built

## Relationships

- ENABLES: [[Chain/Bus Architecture]] (agents need to know the chains)
- ENABLES: [[Full Autonomous Mode]] (agents need complete directives)
- RELATES TO: [[Brain Evolution]] (brain decides what to inject)
- RELATES TO: [[Autocomplete Web / Map Net]] (the map feeds into directive content)
- BUILDS ON: [[Plugin/Skill/Command Ecosystem]] (agents need to know their tools)
- RELATES TO: [[Agent Ecosystem Allocation — Skills, Plugins, Packs Per Role]]
- RELATES TO: [[TOOLS.md Redesign — Focused Desk, Detail On-Demand]]
