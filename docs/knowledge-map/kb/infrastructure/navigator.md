# Navigator — The Autocomplete Web Core

**Type:** Infrastructure Component (Fleet Module)
**Source:** fleet/core/navigator.py
**Tests:** 22 passing (tests/test_navigator.py)
**Status:** Production-ready — wired into orchestrator, all 26 intents working

## What the Navigator Is

The brain of the autocomplete web. Reads the knowledge map metadata (intent-map.yaml, injection-profiles.yaml), selects content at the right depth for the model, queries the LightRAG graph for task-relevant context, and assembles focused output that fits within the gateway's 8000 char limit.

It answers one question: **"What does THIS agent need to know RIGHT NOW?"**

## How It Works

```
Navigator.assemble(role, stage, model, task_context)
│
├── 1. Select injection profile (model → depth tier)
│   opus-1m:    full (50K budget, ~7.5K actual)
│   sonnet-200k: condensed (15K budget, ~3K actual)
│   localai-8k:  minimal (2K budget, ~500 actual)
│   heartbeat:   none (content from fleet-context.md only)
│
├── 2. Find intent (role × stage → injection recipe)
│   26 intents defined in intent-map.yaml
│   e.g. "architect-reasoning" → agent_manual, methodology,
│        skills [architecture-propose, writing-plans, brainstorming],
│        commands [/plan, /branch, /effort], tools [fleet_task_accept]
│
├── 3. Load content per branch at profile depth
│   agent_manual:     full section / 10 lines / 1 line
│   methodology:      full stage (ALWAYS full — never compressed)
│   skills:           purpose descriptions / names only
│   commands:         what-it-does + guidance / key list
│   tools:            purpose line / names
│   standards:        specific standards only (not entire manual)
│   contributions:    status pointer
│   trail:            verification reminder
│   context_awareness: compact/usage guidance
│   mcp:              server descriptions
│
├── 4. Query LightRAG graph (if task context provided)
│   Mode selection per context:
│     review/audit → mix (comprehensive, all sources)
│     security → mix
│     design/architecture → global (relationship-focused)
│     specific systems/tools → local (entity-focused)
│     default → hybrid (entities + relationships)
│   Budget: ~25% of profile total
│
├── 5. Enforce gateway limit (7500 chars → fits in 8000 per file)
│   Trims from end (lowest priority) preserving:
│     agent manual + methodology (highest) over
│     graph context + notes (lowest)
│
└── Output: NavigatorContext → render() → knowledge-context.md
    Written via context_writer.write_knowledge_context()
    Gateway reads alongside fleet-context.md and task-context.md
```

## Performance

- **File caching:** _read_file() caches all KB/manual reads across cycles
- **Singleton:** One Navigator instance per orchestrator lifetime
- **reload():** Clears cache on demand (e.g., after KB update)
- **26 intents tested:** All produce correct content at all depth tiers

## Verified Output

| Role / Stage | Opus | Sonnet | LocalAI |
|-------------|------|--------|---------|
| architect / reasoning | 5,615 chars (5 sections) | 3,069 chars (5 sections) | ~500 chars |
| engineer / work | 7,521 chars (4 sections) | ~3,500 chars | 514 chars |
| fleet-ops / review | 3,484 chars (6 sections) | ~2,000 chars | ~50 chars |
| PM / reasoning | 5,942 chars (5 sections) | ~3,000 chars | ~500 chars |
| devsecops / investigation | 5,252 chars (4 sections) | ~2,500 chars | ~50 chars |

## Three Context Files

| File | Written By | Contains | Limit |
|------|-----------|----------|-------|
| fleet-context.md | orchestrator Step 0 | Fleet state, messages, role data, events | 8000 chars |
| knowledge-context.md | navigator | Knowledge map, skills, commands, methodology, graph | 8000 chars |
| task-context.md | orchestrator dispatch | Task details, stage, requirement, contributions | 8000 chars |

Gateway reads ALL three in sorted order, injected into agent's system prompt as layers 6-7 of the 8-layer onion.

## The Autocomplete Effect

The navigator structures context so the agent's natural continuation IS correct behavior:

- Architect in REASONING → sees /plan command, brainstorming skill, "do NOT implement yet"
- Engineer in WORK → sees /debug command, TDD skill, contribution inputs, test requirements
- Fleet-ops in REVIEW → sees 7-step protocol, trail verification, contribution checking
- DevOps in WORK → sees IaC note, /loop command, Docker foundation skill
- Writer in WORK → sees "documentation is a LIVING SYSTEM" note

The agent doesn't choose to follow the methodology — the methodology IS the context.

## Relationships

- READS: intent-map.yaml (26 intents: role × stage → injection recipe)
- READS: injection-profiles.yaml (4 tiers: opus-1m, sonnet-200k, localai-8k, heartbeat)
- READS: KB entries (198 entries across 11 branches)
- READS: manuals (agent-manuals.md, methodology-manual.md, standards-manual.md)
- QUERIES: LightRAG (port 9621 — context-aware mode selection)
- WRITES: knowledge-context.md via context_writer.write_knowledge_context()
- CALLED BY: orchestrator Step 0 (_refresh_agent_contexts, every cycle)
- ENFORCES: 8000 char gateway limit (trims from lowest priority)
- CACHES: all file reads across orchestrator cycles
- CONNECTS TO: gateway executor.py + ws_server.py (reads context/ files)
- CONNECTS TO: 8-layer onion (knowledge-context.md is part of layer 6-7)
- CONNECTS TO: preembed.py (navigator augments pre-embed with knowledge)
- IS: the autocomplete web — static knowledge → dynamic, focused, adaptive context
