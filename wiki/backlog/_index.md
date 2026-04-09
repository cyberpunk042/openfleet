---
title: "Backlog"
type: index
domain: backlog
status: active
created: 2026-04-08
updated: 2026-04-08
tags: [backlog, planning, epics, roadmap]
---

# Backlog

All planned work for OpenFleet evolution, organized by epics, modules, and tasks.
Source of truth: [wiki/log/2026-04-08-fleet-evolution-vision.md](../log/2026-04-08-fleet-evolution-vision.md)

## Epics

| ID | Epic | Priority | Status | Depends On |
|----|------|----------|--------|------------|
| E001 | [Agent Directive Chain Evolution](epics/E001-agent-directive-chain-evolution.md) | P1 | draft | E007 |
| E002 | [Chain/Bus Architecture](epics/E002-chain-bus-architecture.md) | P1 | draft | E001 |
| E003 | [Brain Evolution](epics/E003-brain-evolution.md) | P1 | draft | E001, E002 |
| E004 | [RAG/Knowledge System (LightRAG)](epics/E004-rag-knowledge-system.md) | P1 | draft | E013 |
| E005 | [Multi-Model Strategy](epics/E005-multi-model-strategy.md) | P1 | draft | E003 |
| E006 | [Budget & Tempo Modes](epics/E006-budget-tempo-modes.md) | P1 | draft | E003, E005 |
| E007 | [Plugin/Skill/Command Ecosystem](epics/E007-plugin-skill-command-ecosystem.md) | P1 | draft | gateway |
| E008 | [Agent Lifecycle Fine-Tuning](epics/E008-agent-lifecycle-fine-tuning.md) | P2 | draft | E003 |
| E009 | [Signatures & Transparency](epics/E009-signatures--transparency.md) | P2 | draft | E002 |
| E010 | [Config Evolution](epics/E010-config-evolution.md) | P2 | draft | — |
| E011 | [Simulation & Validation](epics/E011-simulation--validation.md) | P2 | draft | E001-E003 |
| E012 | [Full Autonomous Mode](epics/E012-full-autonomous-mode.md) | P1 | draft | E001, E003, E007 |
| E013 | [IaC & Persistence](epics/E013-iac--persistence.md) | P2 | draft | — |
| E014 | [Autocomplete Web / Map Net](epics/E014-autocomplete-web--map-net.md) | P1 | draft | E004 |
| E015 | [Scaffold→Foundation→Infra→Features](epics/E015-scaffold-foundation-infra-features-pattern.md) | P2 | draft | — |
| E016 | [Claw Code Parity Research](epics/E016-claw-code-parity-research.md) | P2 | draft | — |
| E017 | [Federation & Multi-Fleet](epics/E017-federation--multi-fleet.md) | P2 | draft | E001 |

## Priority Groups

**P1 — Foundation (must build first):**
E001 (Directive Chain) → E002 (Chains/Buses) → E003 (Brain) → E007 (Plugins) → E012 (Autonomous)
E004 (LightRAG) → E014 (Autocomplete Web)
E005 (Multi-Model) → E006 (Budget)

**P2 — Evolution (builds on foundation):**
E008 (Lifecycle) → E009 (Signatures) → E010 (Config) → E011 (Validation)
E013 (IaC) → E015 (Pattern) → E016 (Parity) → E017 (Federation)

## Modules

See [modules/_index.md](modules/_index.md)

## Tasks

See [tasks/_index.md](tasks/_index.md)
