---
title: "Gateway File Injection — Research Findings"
type: reference
domain: architecture
status: processing
confidence: medium
created: 2026-04-08
updated: 2026-04-08
tags: [gateway, injection, truncation, tools-md, autocomplete-chain, E001]
sources: [gateway/executor.py, scripts/push-agent-framework.sh, openarms source]
---

# Gateway File Injection — Research Findings

## Summary

Two gateway paths exist. The local executor truncates files to 4000 chars (destroying 78% of TOOLS.md). The real gateway (OpenArms) uses Claude Code workspaces where CLAUDE.md is read natively with no limit. The bootstrap mechanism for other files needs further research.

## Key Findings

### Local Gateway (gateway/executor.py)
- `_build_agent_context()` builds system prompt from 8 files
- Injection order: IDENTITY → SOUL → CLAUDE.md → TOOLS.md → AGENTS.md → context/ → HEARTBEAT
- **Each file truncated to 4000 chars** (except context/ files at 8000)
- TOOLS.md is 15,000-18,000 chars → agents see only first 22%
- Role-specific sections (group calls, skills, hooks, CRONs) are INVISIBLE
- Uses `--append-system-prompt` flag to Claude CLI

### Real Gateway (OpenArms/OpenClaw)
- Runs as systemd service, manages Claude Code sessions in workspaces
- Claude Code reads CLAUDE.md natively — **NO size limit**
- TOOLS.md, AGENTS.md, HEARTBEAT.md placed in workspace by push-agent-framework.sh
- Bootstrap injects files: **20,000 chars per file**, **150,000 total** (from schema.help.ts)
- May use `inject_content()` for dynamic content (heartbeat wake, teaching lessons)

### Code Docs (.md in src/)
- .md files are spread across the codebase in source directories
- These are inner documentation — not injected into agents
- Part of the code docs layer, distinct from wiki (LLM-friendly) and docs (front-facing)

## RESOLVED

**Real gateway: 20,000 chars/file, 150,000 total.** TOOLS.md at 15-18K fits. Local executor at 4,000 is wrong — needs fixing.

**Lightweight mode:** Gateway has option to keep only HEARTBEAT.md for low-cost sessions. Relevant for E008 (lifecycle tuning).

## PO Directive: Don't Flood the Agent

> "we do not want to flood our agent with things it doesn't need to know... bloated files are still sign that there might be something wrong"

> "if there are too much tools its because we forgot that the AI assistant does not need to know every single tools but only a few group calls and then if he need to know more he gets it per-case via skills or other injection"

> "This goes hand to hand into the idea of not overwhelming the agent and doing a proper autocomplete chain and also not flooding it with too many mcps over skills"

**Current TOOLS.md is 15-18K chars — BLOATED.** Agents don't need 30 tool descriptions. They need 5-8 focused group calls.

## Design Principle: Focused Pre-Inject, Detail On-Demand

| Layer | What | Size Target |
|-------|------|------------|
| Pre-injected (TOOLS.md) | Focused group calls, "call THIS it does THAT" | 3-5K |
| Skills (on invoke) | Detailed methodology, step-by-step protocol | loaded per-case |
| Context/ (brain preembed) | Task-specific recommendations, stage method | dynamic |
| Queryable (sub-agent/MCP) | Full reference, all parameters, all chains | on request |

## Local Executor Config

Fixed to match real gateway. Configurable via .env:
- `FLEET_BOOTSTRAP_MAX_PER_FILE` — hard cap (default: 20000)
- `FLEET_BOOTSTRAP_MAX_TOTAL` — hard cap (default: 150000)
- `FLEET_BOOTSTRAP_WARN_PER_FILE` — warning threshold (default: 8000)
- `FLEET_BOOTSTRAP_WARN_TOTAL` — warning threshold (default: 60000)

Warnings log when files exceed threshold — "Bloated files degrade focus."

## Design Implications

E001's real work: redesign TOOLS.md to be FOCUSED (3-5K), push detail into skills/context/queryable layers. The autocomplete chain should naturally lead to the right group call without the agent needing to read a manual.

## Relationships

- FEEDS_INTO: E001 (Agent Directive Chain Evolution)
- RELATES_TO: E014 (Autocomplete Web — injection is how agents access the map)
