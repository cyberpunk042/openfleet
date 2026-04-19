---
title: "Plugin/Skill/Command Ecosystem"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [plugins, skills, commands, packs, superpowers, reverse-hooks, marketplace, ring, trailofbits, ecosystem]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: directive
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Plugin/Skill/Command Ecosystem

## Summary

Full evaluation and deployment of the plugin/skill/command ecosystem. Register major packs (superpowers, ring, trailofbits, NeoLabHQ, borghei). Install per-role skill groups through the setup pipeline. Create custom /commands per role. Explore reverse hooks. Pair commands + skills + plugins into coherent per-agent tooling that flows through IaC provisioning.

> "we will also make sure that we use all the superpower and main skills from high quality repositories marketplaces packs"

> "we might need to use the hooks and the notions of reverse hooks more too"

> "we might also need to do our own custom /commands generic and per role, a bit like for the skills"

> "we also now start to use a LLM wiki pattern with a notes / messages log and a backlog that can have the desired format per project such as Epic, Module, Task / Issue and we structure claude to continuously and naturally work with that and have the appropriate skill to do good work inside like with anything and like we want to pair commands (proper 'https://github.com/artemgetmann/claude-slash-commands') and skills (PROPER ONES too) and plugin. like 'https://github.com/backnotprop/plannotator' which will be key (especially with the PM)"

> "The AIs agents also need to know their Tools, Stacks and Skills. Everyone has tool specialisations and domain specializations. This also mean that we have to make sure we make them available to them with the project + config + IaC + setups"

> "Lets also not forget that we are not done, what you added in the kB is mostly what we have but this is far from what we aim to have. much more skills and plugins depending on the agents and so on."

> "This also need to properly integrate into the brain and structure and pre-embedding and instructions and the way to decide. everything has to be so well thought, things has to be clear to the agent and its model of execution and intelligent choices obviously and adaptive choices and based on the settings too obviously"

## Ecosystem Scale (Research 2026-04-09)

| Source | Scale | Quality | Status |
|--------|-------|---------|--------|
| Anthropic Official Marketplace | 126 plugins | Curated | 10 configured in agent-tooling.yaml |
| obra/superpowers | 30+ skills, 9 marketplace plugins | Battle-tested, de facto standard | Configured, 0 installed |
| LerianStudio/ring | 89 skills, 38 agents, 10 review agents | Team-structured, mirrors fleet | Not evaluated |
| trailofbits/skills-curated | 28 security plugins | Security researchers, vetted | Not evaluated |
| NeoLabHQ/context-engineering-kit | 14 plugins (DDD, SADD, TDD) | Engineering methodology | Not evaluated |
| borghei/Claude-Skills | 225+ skills, 23 compliance | Regulatory/governance | Not evaluated |
| alirezarezvani/tresor | 8 agents, 20+ commands | Practical workflows | Not evaluated |
| Total ecosystem | ~1,100+ skills, 580+ plugins | Variable | ~10% configured, 0% deployed |

See: [wiki/domains/architecture/agent-ecosystem-allocation.md](../../domains/architecture/agent-ecosystem-allocation.md)

## Current State

| Layer | Configured | Deployed | Gap |
|-------|-----------|----------|-----|
| Plugins (agent-tooling.yaml) | 18 unique across roles | 0 installed | Need gateway running + install-plugins.sh |
| Plugin skills (come with plugins) | ~37 (superpowers 14, pr-review-toolkit 6, etc.) | 0 | Blocked on plugin installation |
| Fleet workspace skills | 78 fleet-* in .claude/skills/ | 78 | Done |
| Gateway skills | 13 in .agents/skills/ | 13 | Done |
| Marketplace skills (skill-assignments.yaml) | 9 install=true | 0 | Need gateway + marketplace sync |
| Sub-agents (.claude/agents/) | 12 defined | 12 .md files | Done |
| Skill packs (skill-packs.yaml) | 1 (Anthropic Official) | 0 synced | Need 5+ more packs registered |

## Goals

- Register 5+ major packs in skill-packs.yaml (superpowers, ring, trailofbits, NeoLabHQ, borghei)
- Evaluate and quality-filter each pack for fleet-relevant skills per role
- Map pack skills to agents via skill-assignments.yaml with metadata
- Deploy all configured plugins to agent workspaces via IaC
- Create custom /commands per role where skills don't fit
- Explore reverse hooks concept and implement where valuable
- Ensure skill-stage-mapping.yaml includes pack skills in stage recommendations
- Ensure Navigator intent-map.yaml recommends pack skills at right stages
- All installation flows through setup pipeline — zero manual steps

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Register 5+ major packs in skill-packs.yaml (superpowers, ring, trailofbits, NeoLabHQ, borghei)
- [ ] Evaluate and quality-filter each pack for fleet-relevant skills per role
- [ ] Map pack skills to agents via skill-assignments.yaml with metadata
- [ ] Deploy all configured plugins to agent workspaces via IaC
- [ ] Create custom /commands per role where skills don't fit
- [ ] Explore reverse hooks concept and implement where valuable
- [ ] Ensure skill-stage-mapping.yaml includes pack skills in stage recommendations
- [ ] Ensure Navigator intent-map.yaml recommends pack skills at right stages
- [ ] All installation flows through setup pipeline — zero manual steps

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Per-Role Skill Groups (Target)

| Agent | Plugins | Pack Skills | Fleet Skills | Total |
|-------|---------|-------------|-------------|-------|
| project-manager | claude-mem, safety-net, plannotator | superpowers planning (5), ring pm-team (17), ring pmo-team (10) | 8 fleet-* PM | ~42 |
| fleet-ops | claude-mem, safety-net, pr-review-toolkit, claude-md-management | superpowers review (3), ring review agents (10) | 6 fleet-* ops | ~22 |
| architect | claude-mem, safety-net, context7, superpowers, adversarial-spec, skill-creator, claude-code-setup | NeoLabHQ (4), ring pm-team design (2) | 8 fleet-* arch | ~18+ superpowers 30 |
| devsecops | claude-mem, safety-net, security-guidance, sage, semgrep | trailofbits security (6-10), superpowers debugging (4), borghei compliance (3) | 7 fleet-* sec | ~27 |
| software-engineer | claude-mem, safety-net, context7, superpowers, pyright-lsp, skill-creator | ring dev-team (4), trailofbits simplifier (1) | 8 fleet-* eng | ~17+ superpowers 30 |
| devops | claude-mem, safety-net, hookify, commit-commands, claude-code-setup | superpowers infra (4), ring dev-team infra (3), ring finops (1) | 8 fleet-* devops | ~19 |
| qa-engineer | claude-mem, safety-net, superpowers | ring test-reviewer (1) | 8 fleet-* QA | ~13+ superpowers 30 |
| technical-writer | claude-mem, safety-net, context7, ars-contexta, elements-of-style | superpowers writing (3), ring tw-team (8) | 6 fleet-* writer | ~22 |
| ux-designer | claude-mem, safety-net | superpowers creative (3) | 5 fleet-* UX | ~11 |
| accountability | claude-mem, safety-net, claude-md-management | superpowers verification (1), ring pmo-team (2), borghei compliance (3) | 5 fleet-* acct | ~14 |

## Phases

### Phase 0: Research & Evaluate

- [x] Inventory full ecosystem (1,100+ skills, 580+ plugins) — done 2026-04-09
- [x] Identify 3 major packs (superpowers, ring, trailofbits) + 3 secondary (NeoLabHQ, borghei, tresor)
- [x] Map per-agent allocation → agent-ecosystem-allocation.md
- [x] Evaluate plugin decisions (4 INSTALL, 5 DEFER, 3 SKIP) → plugin-evaluation.yaml
- [ ] Hands-on test superpowers pack — install in test workspace, verify all 30 skills work
- [ ] Hands-on test LerianStudio/ring — install, evaluate team skill quality
- [ ] Hands-on test trailofbits curated — install, evaluate security skill depth
- [ ] Evaluate NeoLabHQ context-engineering-kit for architect
- [ ] Evaluate borghei compliance skills for accountability
- [ ] Research reverse hooks — what they are, how OpenClaw/OC implements them
- [ ] Research custom /commands pattern — what doesn't fit as skills, needs commands

### Phase 1: Design

- [ ] Design skill-packs.yaml expansion (5+ pack registrations with metadata)
- [ ] Design skill-assignments.yaml expansion (pack skills → agents with quality filter)
- [ ] Design skill-stage-mapping.yaml expansion (pack skills in stage recommendations)
- [ ] Design custom /command structure (generic + per-role)
- [ ] Design reverse hook patterns for fleet use cases
- [ ] Design IaC deployment sequence (packs → marketplace → agents → validate)
- [ ] Design quality filtering criteria (how to triage mega-packs with template skills)

### Phase 2: Scaffold & Implement

- [ ] Update skill-packs.yaml with 5+ pack registrations
- [ ] Update skill-assignments.yaml with filtered pack skills per agent
- [ ] Update skill-stage-mapping.yaml with pack skills per stage
- [ ] Update agent-tooling.yaml if new plugins identified from evaluation
- [ ] Build/update scripts/install-plugins.sh for full plugin deployment
- [ ] Build scripts/sync-skill-packs.sh for pack sync to marketplace
- [ ] Create custom /commands per role
- [ ] Implement reverse hooks where identified
- [ ] Update Navigator intent-map.yaml with pack skill references

### Phase 3: Test & Validate

- [ ] Test each plugin installs correctly in agent workspace
- [ ] Test pack skill sync to OCMC marketplace
- [ ] Test skill-to-agent assignment via marketplace
- [ ] Test custom commands per role
- [ ] Test IaC deployment reproduces full skill state (make setup → all skills available)
- [ ] Verify Navigator recommends pack skills at correct stages
- [ ] Verify TOOLS.md generation references are accurate

## Existing Foundation

- config/agent-tooling.yaml — per-role plugin/skill assignments (18 plugins configured)
- config/plugin-evaluation.yaml — 4 INSTALL, 5 DEFER, 3 SKIP decisions
- config/skill-packs.yaml — 1 pack registered (Anthropic Official)
- config/skill-assignments.yaml — 9 marketplace skills with install decisions
- config/skill-stage-mapping.yaml — stage-aware recommendations (fleet-* + some superpowers)
- 78 fleet-* workspace skills in .claude/skills/
- 13 gateway skills in .agents/skills/
- 12 sub-agents defined in .claude/agents/
- scripts/install-plugins.sh referenced but needs verification
- gateway skill scanner discovers SKILL.md files automatically

## Relationships

- ENABLES: [[Agent Directive Chain Evolution]] (agents need their tools available to reference)
- RELATES TO: [[Autocomplete Web / Map Net]] (Navigator recommends skills per stage)
- RELATES TO: [[Multi-Model Strategy]] (Codex plugin is part of this ecosystem)
- RELATES TO: [[Brain Evolution]] (brain reads skill-stage-mapping for pre-embed)
- CONSTRAINED BY: Gateway running (plugin install, marketplace sync)
