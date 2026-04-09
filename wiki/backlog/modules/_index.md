---
title: "Modules Index"
type: index
domain: backlog
status: active
created: 2026-04-08
updated: 2026-04-09
tags: [modules, backlog]
---

# Modules

Breakdown of epics into implementable modules. Each module maps to a system area and produces concrete deliverables.

## E001 — Agent Directive Chain

| Module | System Area | Status |
|--------|------------|--------|
| M001-tools-md | TOOLS.md generation pipeline | ✅ Done — 77% reduction |
| M002-claude-md | CLAUDE.md per-agent templates | ✅ Done — 10 agents, 8 sections |
| M003-heartbeat-md | HEARTBEAT.md per-role templates | ✅ Done — 11 templates, priority order |
| M004-agent-yaml | agent.yaml provisioning | ✅ Done — 14 fields per standard |
| M005-navigator-intents | Navigator intent-map expansion | ✅ Done — 33→45 intents |
| M006-autocomplete-chain | task-context.md 10-section order | ✅ Done — preembed.py rewritten |
| M007-identity-soul | IDENTITY.md + SOUL.md review | 🔨 Minor updates needed |
| M008-validation | Injection simulation + concern mixing | ✅ Done — 339/340 pass |

## E002 — Chain/Bus Architecture

| Module | System Area | Status |
|--------|------------|--------|
| M009-cross-task | Parent↔child comment propagation | ✅ Done — complete + reject chains |
| M010-chain-docs | ins/outs/middles for all chains | ✅ Done — 11/11 state-modifying tools |
| M011-eventstore | EventStore consistency | ✅ Verified — already wired in ChainRunner |
| M012-chain-layer2 | Event-driven reactions (Layer 2) | ❌ Not needed for MVP |

## E003 — Brain Evolution

| Module | System Area | Status |
|--------|------------|--------|
| M013-contributions | Auto-create contributions + dispatch gate | ✅ Done — orchestrator Step 2.5 |
| M014-trail-wiring | Trail recording in orchestrator | ✅ Done — dispatch + contribution events |
| M015-diseases | 11/11 disease detection functions | ✅ Done — 7 new + 4 existing |
| M016-teaching | 11/11 teaching lesson templates | ✅ Done — 3 new + 8 existing |
| M017-effort-escalation | Budget-adaptive model/effort selection | ✅ Done — 10-factor decision |
| M018-context-strategy | Progressive context/rate limit response | ✅ Done — module + wiring |
| M019-role-providers | Contribution-aware role providers | ✅ Done — registry fixed |
| M020-settings-wiring | backend_mode→router, budget_mode→tempo | ❌ Needs MC running |
| M021-session-telemetry | Wire session_telemetry adapter | ❌ Needs gateway data |
| M022-deterministic-bypass | Simple ops without Claude calls | 🔨 Design done + PO gate auto-processing |

## E007 — Plugin/Skill/Command Ecosystem

| Module | System Area | Status |
|--------|------------|--------|
| M023-ecosystem-research | Full ecosystem inventory + allocation | ✅ Done — 1,100+ skills, 6 packs |
| M024-skill-stage-packs | Pack skills in skill-stage-mapping.yaml | ✅ Done — 5 packs mapped |
| M025-custom-commands | Per-role /commands | ✅ Done — 13 commands covering all 10 roles |
| M026-pack-registration | skill-packs.yaml with 5+ packs | ❌ Needs gateway |
| M027-plugin-install | Deploy plugins to workspaces | ❌ Needs gateway |
| M028-reverse-hooks | Research + implement reverse hooks | 🔨 Researched — inject_content() is the primitive, needs formalization |

## E010 — Config Evolution

| Module | System Area | Status |
|--------|------------|--------|
| M029-readiness-progress | Enforce readiness/progress separation | ✅ Done — events, pre-embed, MCP |
| M030-phase-enforcement | Phase gate enforcement in orchestrator | ✅ Done — blocks at gate phases without PO approval |

## Summary

| Status | Count |
|--------|-------|
| ✅ Done | 22 |
| 🔨 Partial | 3 |
| ❌ Not started / blocked | 5 |
| **Total** | **30** |
