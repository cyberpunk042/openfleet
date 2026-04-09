---
title: "Plugin/Skill/Command Ecosystem"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-08
tags: [plugins, skills, commands, packs, superpowers, reverse-hooks, marketplace]
---

# Plugin/Skill/Command Ecosystem

## Summary

Full evaluation and deployment of the plugin/skill/command ecosystem. Install superpowers and marketplace packs. Create custom /commands per role. Explore reverse hooks. Pair commands + skills + plugins into coherent tooling per agent.

> "we will also make sure that we use all the superpower and main skills from high quality repositories marketplaces packs"

> "we might need to use the hooks and the notions of reverse hooks more too"

> "we might also need to do our own custom /commands generic and per role, a bit like for the skills"

> "we also now start to use a LLM wiki pattern with a notes / messages log and a backlog that can have the desired format per project such as Epic, Module, Task / Issue and we structure claude to continuously and naturally work with that and have the appropriate skill to do good work inside like with anything and like we want to pair commands (proper 'https://github.com/artemgetmann/claude-slash-commands') and skills (PROPER ONES too) and plugin. like 'https://github.com/backnotprop/plannotator' which will be key (especially with the PM)"

> "The AIs agents also need to know their Tools, Stacks and Skills. Everyone has tool specialisations and domain specializations. This also mean that we have to make sure we make them available to them with the project + config + IaC + setups"

> "Lets also not forget that we are not done, what you added in the kB is mostly what we have but this is far from what we aim to have. much more skills and plugins depending on the agents and so on."

## Research Findings

- claude-slash-commands (artemgetmann) — custom commands, now merged into skills pattern
- plannotator (backnotprop) — visual plan annotation, key for PM
- codex-plugin-cc — adversarial reviews (covered in E005)
- Claude Code skills are the recommended approach over commands
- Superpowers: 14 skills + code-reviewer sub-agent
- pr-review-toolkit: 6 parallel review agents

## Goals

- Install and deploy all 4 INSTALL-decision plugins (skill-creator, claude-code-setup, claude-md-management, elements-of-style)
- Evaluate and install high-priority plugins (feature-dev, code-review, episodic-memory)
- Create custom /commands per role where skills don't fit
- Explore and document reverse hooks concept
- Deploy marketplace skill packs to appropriate agents
- Ensure all plugins/skills/commands available via IaC (scripts install them)

## Phases

### Phase 0: Research

- [ ] Audit what plugins are currently INSTALLED (vs configured but not installed)
- [ ] Research reverse hooks — what they are, how they work
- [ ] Evaluate artemgetmann/claude-slash-commands for fleet use
- [ ] Evaluate each DEFER-decision plugin with fresh eyes
- [ ] Inventory marketplace packs relevant per role

### Phase 1: Design

- [ ] Design per-role plugin/skill/command assignment matrix
- [ ] Design custom command structure (generic + per-role)
- [ ] Design reverse hook patterns for fleet use cases
- [ ] Design IaC deployment for plugins (scripts/install-plugins.sh)

### Phase 2: Scaffold & Implement

- [ ] Install 4 INSTALL-decision plugins via gateway
- [ ] Create custom /commands for each role
- [ ] Deploy marketplace skill packs
- [ ] Implement reverse hooks where identified
- [ ] Update agent-tooling.yaml with full plugin assignments
- [ ] Update IaC scripts

### Phase 3: Test & Validate

- [ ] Test each plugin works in agent workspace
- [ ] Test custom commands per role
- [ ] Test IaC deployment reproduces plugin state
- [ ] Evaluate skill quality with agents doing real tasks

## Existing Foundation

- config/agent-tooling.yaml — per-role plugin/skill assignments
- config/plugin-evaluation.yaml — 4 INSTALL, 5 DEFER, 3 SKIP
- 78 workspace skills already built
- 13 hooks across 9 roles

## Relationships

- ENABLES: E001 (Agent Directive Chain — agents need to know their tools)
- RELATES_TO: E005 (Multi-Model — Codex plugin is part of this)
- RELATES_TO: E014 (Autocomplete Web — plugins feed capability)
- DEPENDS_ON: Gateway running (plugin install requires gateway CLI)
