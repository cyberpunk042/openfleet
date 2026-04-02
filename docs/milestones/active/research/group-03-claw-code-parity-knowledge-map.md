# Research Group 03 — Claw Code Parity + Fleet Knowledge Map Architecture

**Date:** 2026-04-02
**Status:** RESEARCHED — architectural vision captured, parity inventory obtained
**Workflow step:** 1/4 (Research → Classify → Document → Build)

---

## Part 1: claw-code-parity (ultraworkers/claw-code-parity)

**Source:** https://github.com/ultraworkers/claw-code-parity
**Parent:** ultraworkers/claw-code — 148K stars, 101K forks
**Type:** Rust reimplementation of Claude Code agent harness

### What It Is

Clean-room Rust port of Claude Code's agent harness. Created from the
TypeScript source surface that was briefly exposed. The project catalogs
the COMPLETE internal structure of Claude Code.

### Why It Matters for AICP

**Not for copying** — for understanding what Claude Code does internally
so AICP's router can make intelligent decisions about what needs Claude
vs what can go to LocalAI.

### Complete Claude Code Internal Inventory

From the archived surface snapshots:

- **184 tools** cataloged (vs our 33 built-in + 29 fleet MCP)
- **207 commands** cataloged (vs our 50+ known slash commands)
- **1,902 TypeScript files** mapped with full file tree

### PARITY.md Gap Analysis (7 areas)

What the Rust port is missing vs Claude Code — useful as a
checklist of Claude Code capabilities:

1. **Tools surface:** 19 implemented vs 184 upstream
2. **Hook execution:** Config loads but hooks don't fire
3. **Plugins:** Entirely absent
4. **Skills:** Partial (SKILL.md loading, no registry/discovery)
5. **CLI breadth:** 15 commands vs 207 upstream
6. **Assistant orchestration:** No streaming concurrency, no hook integration
7. **Services:** Missing analytics, LSP, team memory sync, prompt suggestions

### What AICP Can Learn

| Concept | Claw Code Approach | AICP Approach | Gap |
|---------|-------------------|---------------|-----|
| Backend | Anthropic API only | Multi-backend (Claude + LocalAI + OpenRouter) | AICP is MORE ambitious |
| Permissions | 3 modes | Think/Edit/Act with path protection | AICP is richer |
| Tools | 184 in upstream | 29 fleet + 33 built-in | Need to understand what the other 122 do |
| Hooks | PreToolUse/PostToolUse | 26 hook types available | AICP has access to more hooks |
| MCP | Client implementation | Fleet MCP server (29 tools) + per-agent MCP | AICP has custom MCP |
| Session | JSONL persistence | Gateway-managed sessions | Different model |
| Compaction | ILM-style | Brain-managed (session_manager.py) | AICP adds fleet-wide coordination |
| Skills | SKILL.md loading | 85 skills + ecosystem | AICP has more |
| Cost | None (25B tokens/year) | Budget modes, LocalAI offload, cost tracking | AICP core mission |

### 122 "Missing" Tools to Investigate

The gap between 184 upstream tools and our 62 (33 built-in + 29 fleet)
means there are ~122 tools in Claude Code we haven't accounted for.
Many are likely internal/UI tools, but some may be capabilities our
agents should know about or that AICP's router should handle.

**Next step:** Extract the full 184-tool list from the surface snapshot
and classify which are relevant to fleet agents.

---

## Part 2: Fleet Knowledge Map Architecture

### PO Vision (Verbatim)

> "Imagine all the notions about the systems, the knowledges, the
> functioning of the fleet and the agents and brought together and
> then cross-referenced and associated with a map file, like for
> javascript or similar language in order to create a virtual map
> of this / those said trees"

> "there is also a RAG Map that is like a manual / a magic book
> that unlock the knowledge about the self and the system(s) in
> all its layer, and the modules and everything shrinked down so
> that we can adapt the injections"

> "things you could never inject into a cheap model for example but
> could still be strategically integrated into the feed as per still
> what is present and the map act as a facilitator with clear intents"

> "it also help any conversation / agent feed in general but this
> goes in pair with the memory idea and then the RAG idea and the
> lightRAG and the dynamic files and pre-embedding and injections"

> "For the map think about AI in general, its all about proper
> relations and metadata and data patterns and autocomplete"

> "The fleet system manual. containing multiple system manuals and
> individual modules and layers and agents manuals and tools manuals"

> "Research and conclusions are the driver that will define multiple
> foundational pieces and infrastructure and workflow and logics"

### What This Is

A metadata/map system that acts as the ROOT of all fleet knowledge.
Like a JavaScript source map connects minified code to original source,
the Fleet Knowledge Map connects compact metadata references to full
knowledge content.

### The Tree Structure

```
Fleet Knowledge Map (root)
│
├── SYSTEM MANUALS (22 systems)
│   ├── 01-methodology/
│   │   ├── _map.yaml (metadata: what, connects-to, depends-on)
│   │   ├── full.md (complete system doc — 400+ lines)
│   │   ├── condensed.md (key concepts — 50 lines)
│   │   └── minimal.md (one-paragraph essence — 5 lines)
│   ├── 02-immune-system/
│   │   ├── _map.yaml
│   │   ├── full.md
│   │   ├── condensed.md
│   │   └── minimal.md
│   └── ... (22 systems)
│
├── AGENT MANUALS (10 agents)
│   ├── architect/
│   │   ├── _map.yaml (role, tools, skills, plugins, commands, contributes-to)
│   │   ├── full.md (complete agent spec from fleet-elevation)
│   │   ├── condensed.md (key behaviors + tool chains)
│   │   └── minimal.md (identity + core responsibility)
│   └── ... (10 agents)
│
├── MODULE MANUALS (94 core modules)
│   ├── orchestrator/
│   │   ├── _map.yaml (imports, exports, called-by, calls)
│   │   ├── full.md (complete module doc)
│   │   └── minimal.md (signature + purpose)
│   └── ... (94 modules)
│
├── TOOL MANUALS (29 fleet + 33 built-in + ecosystem)
│   ├── fleet_task_complete/
│   │   ├── _map.yaml (chain operations, surfaces, who-uses, stage-gating)
│   │   ├── full.md (complete call tree from fleet-elevation/24)
│   │   └── minimal.md (purpose + key params)
│   └── ... (all tools)
│
├── SKILL MANUALS (85+ skills)
│   ├── architecture-propose/
│   │   ├── _map.yaml (roles, stages, invocation, dependencies)
│   │   └── content.md (skill content)
│   └── ... (all skills)
│
├── PLUGIN MANUALS (evaluated plugins)
│   ├── claude-mem/
│   │   ├── _map.yaml (capabilities, hooks, MCP tools, risks)
│   │   └── condensed.md (what it provides)
│   └── ... (evaluated plugins)
│
├── COMMAND MANUALS (50+ commands)
│   ├── _map.yaml (all commands with per-role, per-stage recommendations)
│   └── per-command details
│
├── STANDARDS MANUAL (8 standards + 13 artifact types)
│   ├── per-standard _map.yaml
│   └── per-artifact-type schema
│
├── METHODOLOGY MANUAL
│   ├── per-stage instructions (from stage_context.py)
│   ├── per-stage tool recommendations
│   ├── per-stage skill recommendations
│   └── per-stage command recommendations
│
└── RAG INDEX (the navigator)
    ├── cross-references.yaml (system→module→tool→agent relationships)
    ├── intent-map.yaml (situation → what to inject)
    └── injection-profiles/
        ├── opus-1m.yaml (full detail for powerful models)
        ├── sonnet-200k.yaml (condensed for standard)
        ├── localai-8k.yaml (minimal for cheap models)
        └── heartbeat.yaml (just enough for idle check)
```

### How It Works

1. **Brain determines context:** Agent role, task stage, model, context window
2. **Brain reads intent-map:** "architect in reasoning stage on Opus 1M"
3. **Intent-map returns injection profile:** load architect/condensed + methodology/reasoning/full + relevant-tools/condensed + contributions/full
4. **Brain assembles autocomplete chain** from the selected content
5. **Agent gets exactly the right knowledge** — not too much, not too little

### Adaptive Injection (the key innovation)

Same agent, same task, different model = different injection:

**Opus 1M context:**
- Full system manual for relevant systems
- Full tool chain documentation
- Full contribution matrix
- Full methodology instructions
- Full standards for artifact type
- All skills with descriptions

**Sonnet 200K context:**
- Condensed system overview
- Tool chains (condensed — name + purpose + key params)
- Contribution matrix (who gives what)
- Methodology instructions (full — these are critical)
- Standards (required fields only)

**LocalAI 8K context:**
- Minimal identity (1 line)
- Current task verbatim + criteria
- Stage instruction (which stage, what to do)
- Tool names only (no chains)
- "Call fleet_read_context for more detail"

### Relationship to Other Systems

| System | Relationship to Knowledge Map |
|--------|------------------------------|
| **autocomplete.py** | READS from map to assemble chains |
| **preembed.py** | READS from map for pre-embed content |
| **context_writer.py** | USES map injection profiles |
| **LightRAG** | INDEXES the full content from manuals |
| **claude-mem** | STORES agent discoveries, MAP indexes them |
| **session_manager.py** | USES map to decide what to dump vs keep |
| **heartbeat_gate.py** | USES minimal map for free evaluation |
| **.claude/memory/** | Agent memory, MAP cross-references it |
| **standards.py** | MAP indexes standards per artifact type |
| **contributions.py** | MAP indexes synergy matrix per role |

### What Needs to Happen

1. **Complete the research** — groups 01-03 (mostly done), then skills classification
2. **Build the manual content** — system manuals exist (22 docs), need agent/tool/skill/command manuals
3. **Build the map metadata** — _map.yaml files with cross-references
4. **Build the injection profiles** — opus/sonnet/localai/heartbeat
5. **Build the intent-map** — situation → injection rules
6. **Build the navigator** — brain reads map, selects content, assembles chain
7. **Integrate with LightRAG** — map becomes the structured index, LightRAG handles semantic search
8. **Test with real agents** — verify the right content reaches agents at the right time

### Impact on Roadmap

This is NOT a single milestone. This is a **foundational architecture** that:
- Adds ~50+ milestones to the roadmap (manual creation, map building, integration)
- Changes how autocomplete.py works (reads from map, not hardcoded)
- Changes how preembed.py works (map-driven injection)
- Changes how context_writer.py works (profile-based assembly)
- Enables intelligent LocalAI usage (minimal injection for 8K context)
- Enables LightRAG integration (map = structured index)
- Enables cross-session knowledge (map + claude-mem + memory)

---

## Open Questions for PO

1. **Map format:** YAML metadata files + markdown content? Or a database (SQLite)?
2. **Manual granularity:** How deep? Per-function level? Or per-module?
3. **Injection profile count:** 4 profiles (opus/sonnet/localai/heartbeat) enough? Or per-agent profiles?
4. **Intent-map rules:** Hardcoded in YAML? Or configurable by PO?
5. **Build order:** Manuals first (content), then map (metadata), then navigator (code)?
6. **LightRAG integration:** Map as the structured index for LightRAG, or separate systems?
7. **claw-code-parity:** Extract the 184-tool list to understand what we're missing?

---

## Next Steps

1. Complete skills classification (group 03 research)
2. PO reviews knowledge map architecture
3. Start building system manuals (22 already exist, need condensed + minimal versions)
4. Build map metadata (_map.yaml cross-references)
5. Build injection profiles (adaptive context assembly)
6. Update complete-roadmap.md with ~50+ new knowledge map milestones
