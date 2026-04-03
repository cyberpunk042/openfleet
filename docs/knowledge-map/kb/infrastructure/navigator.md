# Navigator — The Autocomplete Web Core

**Type:** Infrastructure Component (Fleet Module)
**Source:** fleet/core/navigator.py
**Status:** Initial implementation

## What the Navigator Is

The navigator is the brain of the autocomplete web. It reads the knowledge map metadata (intent-map.yaml, injection-profiles.yaml) and assembles focused context for each agent based on their role, current stage, task, and model capacity.

It answers one question: **"What does THIS agent need to know RIGHT NOW?"**

## How It Works

```
Navigator.assemble(role, stage, task, model)
│
├── 1. Select injection profile (model → depth tier)
│   opus-1m: full (50K tokens)
│   sonnet-200k: condensed (15K tokens)
│   localai-8k: minimal (2K tokens)
│   heartbeat: none (1K tokens, from fleet-context.md)
│
├── 2. Find intent (role × stage → injection recipe)
│   intent-map.yaml: "architect-reasoning" →
│     inject: agent_manual, methodology, skills, commands, tools, mcp
│
├── 3. Load content per branch at profile depth
│   full: read KB entries, complete manual sections
│   condensed: key concepts, first paragraphs
│   minimal: names only, one-line summaries
│   none: skip
│
├── 4. Query LightRAG graph (if task context provided)
│   hybrid mode: entities + relationships relevant to task
│   budget: ~25% of profile's total budget
│
└── Output: NavigatorContext → render() → context string
    Written to: agents/{name}/context/knowledge-context.md
    Gateway reads it alongside fleet-context.md and task-context.md
```

## Three Context Files (After Navigator)

| File | Written By | Contains |
|------|-----------|----------|
| fleet-context.md | orchestrator (Step 0) | Fleet state, messages, role data, events |
| task-context.md | orchestrator (dispatch) | Task details, stage, requirement, contributions |
| knowledge-context.md | navigator | Knowledge map content, graph context, skill/command guidance |

## The Autocomplete Effect

The navigator structures context so the agent's natural continuation IS correct behavior:

- Architect in REASONING stage → sees architecture-propose skill, /plan command, brainstorming skill, "do NOT implement yet" note
- Engineer in WORK stage → sees feature-implement skill, /debug command, contribution inputs from architect/QA/devsecops, test requirements
- Fleet-ops in REVIEW → sees 7-step review protocol, /diff and /pr-comments commands, trail verification instructions

The agent doesn't choose to follow the methodology — the methodology IS the context. The right answer is the obvious continuation.

## Relationships

- READS: intent-map.yaml (role × stage → injection recipe)
- READS: injection-profiles.yaml (model → depth tier)
- READS: cross-references.yaml (system → module → tool → agent mappings)
- READS: KB entries (docs/knowledge-map/kb/ — all branches)
- READS: manuals (agent-manuals.md, methodology-manual.md, standards-manual.md, module-manuals.md)
- QUERIES: LightRAG (port 9621 — hybrid graph queries for task context)
- WRITES TO: context_writer.py → knowledge-context.md
- CALLED BY: orchestrator Step 0 (context refresh cycle)
- CONNECTS TO: preembed.py (navigator augments pre-embed with knowledge content)
- CONNECTS TO: InstructionsLoaded hook (future — navigator could inject via hook)
- CONNECTS TO: gateway (reads context files → injects into agent session)
- CONNECTS TO: 8-layer onion (knowledge-context.md adds to fleet-context layer)
- IS: the autocomplete web — the module that turns static knowledge into dynamic context
