# Analysis 02 — Plugins Branch of the Knowledge Map

**Date:** 2026-04-02
**Status:** ANALYSIS — conclusions from research groups 01-04
**Purpose:** Define exactly which plugins populate the Plugins Manual branch

---

## Current State

agent-tooling.yaml defaults:
- claude-mem (ALL agents) — cross-session memory
Per-role:
- context7 (architect, engineer) — library docs

Research cataloged 40+ plugins. Analysis: which to adopt, per role, priority.

---

## Analysis by Tier

### ADOPT — High confidence, clear value

| Plugin | Stars | What It Does | Roles | Priority | Risk |
|--------|-------|-------------|-------|----------|------|
| **claude-mem** | 45K | Cross-session memory, 4 MCP search tools, 10x token savings | ALL | CRITICAL | ChromaDB spawn storms on WSL2. **USE SQLITE-ONLY MODE.** |
| **context7** | 47K | Library/framework docs, prevents hallucinated APIs | ENG, ARCH, WRITER | HIGH | None — already verified working |
| **safety-net** | 1K | Hook catches destructive git/fs commands before execution | ALL | HIGH | None — passive protection hook |
| **pyright-lsp** | official | Python type checking, automatic diagnostics after edits | ALL Python agents | HIGH | Needs pyright binary installed |

### EVALUATE — Potentially high value, needs deeper assessment

| Plugin | Stars | What It Does | Roles | Consideration |
|--------|-------|-------------|-------|--------------|
| **Superpowers** | 132K | TDD methodology enforcement, 14 deep skills | ALL dev | Conflict: assumes autonomous execution vs our "wait for approval" model. Need to adapt autonomy level. Methodology is SOUND — TDD, brainstorming, subagent dispatch. But can't install as-is. |
| **codex-plugin-cc** | 11K | Cross-provider adversarial review from OpenAI Codex | FLEET-OPS, DEVSEC | Adds OpenAI cost. But review gate PATTERN is valuable. Option: install for fleet-ops only, or implement pattern natively. |
| **pr-review-toolkit** | official | 5 parallel Sonnet agents review every PR | FLEET-OPS, QA | 5x token cost per review. High quality but expensive. May conflict with fleet-ops 7-step review protocol. |
| **claude-octopus** | 2K | Multi-model review (up to 8 AIs) | FLEET-OPS | Interesting for cross-model validation. But: do we have 8 models? With LocalAI we have 2-3. Future consideration. |
| **adversarial-spec** | 518 | Multi-LLM debate for spec refinement | ARCH | Design decision challenge via debate. Useful during REASONING stage. But: requires multiple LLM backends. |
| **harness** | 2K | Meta-skill that designs agent teams | ARCH, FLEET-OPS | Designs domain-specific agent teams. Could inform our fleet architecture. Evaluate if concepts apply. |

### DEFER — Not needed now, revisit when relevant

| Plugin | Stars | Why Defer |
|--------|-------|----------|
| **Ruflo** | 29K | Swarm orchestration. We have our own orchestrator. Different architecture. |
| **Agents (wshobson)** | 33K | Multi-agent orchestration. We have our own. |
| **plannotator** | 4K | Visual plan annotation. Value unclear without team UI. |
| **pro-workflow** | 2K | Self-correcting memory over 50+ sessions. claude-mem covers this. |
| **memsearch** | 1K | Markdown memory. claude-mem is more comprehensive. |
| **total-recall** | 189 | Tiered memory. claude-mem covers this. |
| **ars contexta** | 3K | Knowledge systems. LightRAG will cover this. |
| **hooks-mastery** | 3K | Educational — not a runtime plugin. Reference for learning hooks. |

### SKIP — Not relevant

| Plugin | Why Skip |
|--------|---------|
| **ralph-wiggum** | Autonomous loops — conflicts with fleet guardrails |
| **smart-ralph** | Same — autonomous development |
| **feature-dev** | Our methodology is richer (5 stages vs guided workflow) |
| **plugin-dev** | For building plugins, not for agents |
| **explanatory/learning output** | Educational style — agents are professionals, not students |
| **All domain-specific** (iOS, Elixir, equity research, etc.) | Not our stack |

---

## Conclusions: Plugins Manual Content

### Definite Installs (4 plugins)

| Plugin | Scope | Install Method | Config Notes |
|--------|-------|---------------|-------------|
| **claude-mem** | ALL agents | `/plugin install claude-mem` or OpenClaw installer | **SQLite-only mode** to avoid ChromaDB WSL2 spawn storms. Set in ~/.claude-mem/settings.json |
| **context7** | ARCH, ENG, WRITER | `/plugin install context7` | Already verified working |
| **safety-net** | ALL agents | `/plugin install safety-net` | Passive PreToolUse hook — catches rm -rf, git reset --hard, etc. |
| **pyright-lsp** | ALL Python agents | `/plugin install pyright-lsp` | Needs pyright binary: `npm i -g pyright` |

### Conditional Installs (pending PO decisions)

| Plugin | Condition | Decision Needed |
|--------|-----------|----------------|
| **Superpowers** | Adapt autonomy model for fleet | How to throttle autonomous execution? Which skills to cherry-pick vs install whole plugin? |
| **codex-plugin-cc** | Budget for OpenAI API | Install for fleet-ops only? Or implement review gate natively? |
| **pr-review-toolkit** | Token budget for 5x review cost | Worth the quality increase? Or fleet-ops 7-step review sufficient? |

### What This Means for the Map

```
Plugin Manuals/
├── claude-mem/
│   ├── _map.yaml (ALL agents, session memory, 4 MCP tools)
│   ├── full.md (installation, SQLite-only config, search tools, hooks)
│   ├── condensed.md (what it provides, how to search)
│   └── minimal.md (memory persists across sessions, use search tools)
├── context7/
│   ├── _map.yaml (ENG+ARCH+WRITER, investigation+work stages)
│   └── full.md (resolve-library-id → query-docs workflow)
├── safety-net/
│   ├── _map.yaml (ALL agents, PreToolUse hook)
│   └── full.md (what it catches, when it blocks)
├── pyright-lsp/
│   ├── _map.yaml (ALL Python agents, continuous)
│   └── full.md (type diagnostics, navigation)
└── [conditional]/
    ├── superpowers/ (if adopted)
    ├── codex/ (if adopted)
    └── pr-review-toolkit/ (if adopted)
```

---

## PO Decision Points

1. **safety-net:** Confirm install on ALL agents? (catches destructive commands)
2. **pyright-lsp:** Install on all agents since our codebase is Python?
3. **Superpowers:** Adapt for fleet (cherry-pick TDD + brainstorming + systematic-debugging) or evaluate as-is?
4. **codex-plugin-cc:** Budget for OpenAI alongside Claude? Or native review gate?
5. **pr-review-toolkit:** 5 Sonnet agents per review — worth the token cost?
