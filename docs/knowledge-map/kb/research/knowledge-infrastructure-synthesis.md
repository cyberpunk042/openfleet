# Knowledge Infrastructure Synthesis — Three Systems, One Web

**Type:** Research Conclusion
**Date:** 2026-04-02
**Inputs:** claw-code-parity research, LightRAG research, claude-mem research, existing knowledge map metadata
**Status:** CONCLUSION — defines foundational architecture decisions

## The Problem

We have 178+ KB entries across 10 branches, 7 manuals, 3 metadata files. But this is static content on disk. Nothing indexes it, nothing navigates it, nothing injects the RIGHT content at the RIGHT time. The intent-map.yaml defines WHAT to inject, injection-profiles.yaml defines HOW MUCH — but no system reads these files and acts on them.

Meanwhile, agents restart every session with amnesia. No cross-session learning. No cross-agent knowledge sharing. No graph traversal to find "what relates to what." The autocomplete web doesn't exist yet — we have the leaves but no nervous system.

## The Three-System Architecture

### System 1: LightRAG — The Graph (Cross-Agent Knowledge)

**What it does:** Indexes all KB entries, extracts entities and relationships, builds a navigable knowledge graph. Custom entity types match our domain: `system, agent, command, hook, skill, plugin, layer, tool, module, workflow`.

**What it enables:**
- Graph queries: "What connects to system X?" → traverses entity-relationship edges
- Thematic queries: "How do hooks enforce methodology?" → global mode, relationship embeddings
- Focused retrieval: "What tools does fleet-ops use during review?" → local mode, entity embeddings
- Cross-branch navigation: A query about an agent finds its tools, skills, systems, hooks — through graph edges, not file paths

**Storage:** NetworkX (single-machine default) → Neo4j/PostgreSQL when scaling to Fleet Bravo

**Integration:** Docker container on port 9621, alongside LocalAI on port 8090. LLM via OpenAI-compatible API. Embeddings via bge-m3. Reranking via bge-reranker-v2-m3 (already configured).

**MCP bridge:** daniel-lightrag-mcp provides 22 tools. Agents query the graph via MCP tool calls.

### System 2: Claude-Mem — The Memory (Per-Agent Learning)

**What it does:** Captures tool usage during sessions, compresses via AI into structured observations (97% token reduction), stores in SQLite, injects relevant history into future sessions.

**What it enables:**
- Per-agent learning: "Last time I reviewed architect's work, I found 3 missing acceptance criteria" → observation persists, injected next review session
- Progressive disclosure: search (titles) → timeline (context) → full observations (~3K tokens vs ~20K for bulk RAG)
- Cross-session continuity: agent picks up WHERE it left off, not from scratch

**Storage:** SQLite per-agent instance (port 37771-37780), ChromaDB optional (disabled for RAM savings)

**Integration:** Installed as Claude Code plugin via IaC. SessionStart hook injects MEMORY.md. PostToolUse hook captures observations asynchronously.

### System 3: Knowledge Map + Navigator — The Brain (Intent-Based Injection)

**What it does:** The static knowledge tree (KB entries, manuals, metadata) plus a navigator module that reads intent-map.yaml and injection-profiles.yaml to assemble context per role, per stage, per model.

**What it enables:**
- Intent-based injection: "architect in reasoning stage" → inject architecture-propose skill, /plan command, design input contribution requirements
- Adaptive depth: Opus gets full system manuals, Sonnet gets condensed, LocalAI gets minimal
- Autocomplete chain: structured data where AI's natural continuation IS correct behavior

**Storage:** Markdown files on disk (KB entries), YAML metadata (intent-map, injection-profiles, cross-references)

**Integration:** Navigator module reads metadata → assembles context → InstructionsLoaded hook or gateway injects into agent session.

## How The Three Systems Interconnect

```
                    ┌──────────────────────────────┐
                    │   Knowledge Map (Static)      │
                    │   178+ KB entries              │
                    │   7 manuals, 3 metadata files  │
                    │   Intent map + profiles        │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   LightRAG (Graph Index)      │
                    │   Entity extraction            │
                    │   Relationship extraction      │
                    │   Graph traversal queries      │
                    │   MCP: 22 tools                │
                    └──────────┬───────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
    │ Agent 1        │ │ Agent 2      │ │ Agent N      │
    │ claude-mem     │ │ claude-mem   │ │ claude-mem   │
    │ (port 37771)   │ │ (port 37772) │ │ (port 3777N) │
    │ observations   │ │ observations │ │ observations │
    └─────────┬──────┘ └──────┬───────┘ └──────┬───────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   Navigator Module             │
                    │   Reads intent-map.yaml        │
                    │   Reads injection-profiles.yaml│
                    │   Queries LightRAG graph       │
                    │   Assembles per-agent context   │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   Gateway Injection            │
                    │   8-layer onion                │
                    │   + InstructionsLoaded hook     │
                    │   + SessionStart hook           │
                    │   → Agent session context       │
                    └──────────────────────────────┘
```

## The Multi-Map Overlap

Multiple maps exist simultaneously. They are not redundant — they serve different TRAVERSAL needs:

### Map 1: The Static Tree (Knowledge Map)

**Structure:** Hierarchical branches (systems/tools/commands/hooks/agents/skills/plugins/layers/workflows/infrastructure/research)
**Traversal:** File path navigation, grep for relationships
**Best for:** Human reading, documentation, reference lookup
**Format:** Markdown files with Relationships sections

### Map 2: The Graph (LightRAG)

**Structure:** Entities + relationships (non-hierarchical, web-shaped)
**Traversal:** Graph queries — local (entity-focused), global (relationship-focused), hybrid, mix
**Best for:** "What connects to X?" queries, discovering non-obvious relationships, cross-branch navigation
**Format:** Graph database (NetworkX/Neo4j) + vector embeddings

### Map 3: The Intent Map (YAML metadata)

**Structure:** Role × Stage → injection content mapping
**Traversal:** Lookup by (role, stage, model) → get injection recipe
**Best for:** Navigator module — deterministic context assembly
**Format:** YAML (intent-map.yaml, injection-profiles.yaml, cross-references.yaml)

### Map 4: The Memory Map (claude-mem per agent)

**Structure:** Chronological observations with type/concept tags
**Traversal:** FTS5 search, vector similarity, timeline navigation
**Best for:** "What did THIS agent learn?" — per-agent session history
**Format:** SQLite + ChromaDB per agent instance

### How Maps Overlap

A single concept like "fleet-ops review protocol" exists in:
- **Static tree:** kb/agents/fleet-ops.md (7-step protocol), kb/tools/fleet_approve.md, kb/commands/diff.md
- **Graph:** entity "fleet-ops" connected to entities "fleet_approve", "/diff", "/pr-comments", "quality-audit" through relationship edges
- **Intent map:** `fleet-ops-review` intent → inject agent_manual, standards, skills, commands, tools, trail, contributions
- **Memory:** fleet-ops agent's observations from past reviews — patterns, gotchas, corrections

Navigator combines ALL four: static content shaped by intent map, enriched by graph traversal, personalized by agent memory.

## The Paths and Travels

An **entry point** is any query, intent, or context requirement. A **travel** is the path through the web that finds the right content.

### Example Travel: "Engineer dispatched to implement auth middleware"

```
Entry: role=engineer, stage=work, task="implement auth middleware"
  │
  ├─ Intent map lookup: engineer-work
  │   → inject: agent_manual, methodology, skills, commands, tools, mcp, plugins, contributions, standards, context_awareness
  │
  ├─ Profile selection: opus-1m (full detail)
  │   → skills: full_descriptions
  │   → commands: full_guidance
  │   → tools: full_chains
  │   → contributions: full
  │
  ├─ Graph query (LightRAG): "auth middleware" entities
  │   → finds: S04-authentication system, authMiddleware module, JWT token patterns
  │   → relationships: connects to S01-methodology (security review needed), S08-contributions (devsecops input required)
  │   → injects: relevant system manual sections, security contribution requirements
  │
  ├─ Memory query (claude-mem): engineer's past auth work
  │   → observations: "gotcha: JWT refresh token race condition in middleware chain"
  │   → observations: "pattern: always validate token before extracting claims"
  │   → injects: relevant past learnings
  │
  └─ Assembled context: ~50K tokens
      Agent manual (full) + methodology WORK stage + feature-implement skill +
      /debug, /diff, /fast commands + fleet_commit tool chain +
      filesystem/github/playwright MCP + architect design_input received +
      QA test definitions received + devsecops security requirements +
      auth system manual section + past auth learnings from memory
```

### Example Travel: "Heartbeat — is there work?"

```
Entry: role=any, stage=heartbeat
  │
  ├─ Heartbeat gate (deterministic, $0): evaluate_agent_heartbeat()
  │   → checks: assigned tasks? messages? directives? alerts?
  │   → decision: WAKE (has work) | SILENT (no work) | STRATEGIC (long running)
  │
  ├─ If SILENT: no LLM call, no injection, $0 cost
  │
  ├─ If WAKE:
  │   ├─ Intent map: {role}-heartbeat
  │   ├─ Profile: heartbeat (1K tokens)
  │   ├─ No graph query (too expensive for heartbeat)
  │   ├─ No memory query (not relevant for idle check)
  │   └─ Content: fleet state + directives + messages + tasks + role data
  │
  └─ Cost: $0 (70% of heartbeats) or ~1K tokens (30% with work)
```

## What Needs to Be Built

### Phase 1: LightRAG Infrastructure

1. Add LightRAG to docker-compose.yaml (port 9621, depends on LocalAI)
2. Configure custom entity types for fleet domain
3. Create indexing script: sync KB entries → LightRAG /documents/upload
4. Test entity extraction quality with hermes-3b vs Claude
5. Verify graph captures real relationships (system→tool→agent edges)
6. Install daniel-lightrag-mcp for Claude Code agent access

### Phase 2: Claude-Mem Fleet Deployment

1. IaC script: provision claude-mem per agent (unique port, unique data dir)
2. Configure compression provider (OpenRouter free tier for cost savings)
3. Disable ChromaDB (SQLite-only mode for RAM savings)
4. Add to agent-tooling.yaml (already listed as default plugin)
5. Test: agent session creates observations, next session sees them

### Phase 3: Navigator Module

1. Build navigator that reads intent-map.yaml + injection-profiles.yaml
2. Navigator queries LightRAG for task-relevant graph entities
3. Navigator queries claude-mem for agent-specific memory
4. Assembles context per (role, stage, model, task)
5. Injects via InstructionsLoaded hook or gateway context assembly
6. Test: different roles get different content, different models get different depth

### Phase 4: Cross-Agent Knowledge Sync

1. Periodic indexer: read each agent's claude-mem observations → feed to LightRAG
2. Agent observations become graph entities (new relationships discovered)
3. Test: agent A learns something → agent B can find it via graph query

### Phase 5: Test and Iterate

1. Run agents with full pipeline
2. Measure: does the right content reach the right agent?
3. Measure: does graph traversal find non-obvious connections?
4. Measure: does agent memory improve across sessions?
5. Iterate: adjust entity types, query modes, injection profiles

## Decisions Needed (PO)

| # | Decision | Options | Impact |
|---|----------|---------|--------|
| D-KI-01 | LightRAG graph backend | NetworkX (default, simple) vs PostgreSQL+AGE (scalable) | Single machine = NetworkX. Multi-machine = PostgreSQL |
| D-KI-02 | LightRAG indexing LLM | Claude (quality) vs hermes-3b (free) vs hybrid | Entity extraction quality vs cost |
| D-KI-03 | Claude-mem compression provider | Claude (expensive) vs OpenRouter free vs Gemini Flash Lite | Per-tool-call cost for 10 agents |
| D-KI-04 | ChromaDB enable/disable for claude-mem | Enable (semantic search) vs disable (RAM savings) | 35GB RAM risk vs search quality |
| D-KI-05 | Navigator module location | AICP (aicp/core/) vs fleet (fleet/core/) vs standalone | Where does the map reading code live? |
| D-KI-06 | Cross-agent knowledge sync frequency | Real-time vs periodic (5min/15min/30min) | Freshness vs resource usage |
| D-KI-07 | LightRAG MCP: which agents get it? | All agents vs PM + architect + fleet-ops | Graph queries cost tokens |

## Relationships

- SYNTHESIZES: kb/research/claw-code-parity.md (AICP feature gaps → informs Navigator design)
- SYNTHESIZES: kb/infrastructure/lightrag.md (graph RAG → System 1)
- SYNTHESIZES: kb/infrastructure/claude-mem.md (per-agent memory → System 2)
- DEFINES: three-system architecture (graph + memory + navigator)
- DEFINES: four-map overlap model (static + graph + intent + memory)
- DEFINES: paths and travels concept (entry point → traversal → focused output)
- CONNECTS TO: intent-map.yaml (Map 3 — navigator reads this)
- CONNECTS TO: injection-profiles.yaml (depth control per model)
- CONNECTS TO: cross-references.yaml (system → module → tool → agent mappings)
- CONNECTS TO: 8-layer onion (gateway injection order)
- CONNECTS TO: InstructionsLoaded hook (navigator injection point)
- CONNECTS TO: SessionStart hook (claude-mem injection point)
- CONNECTS TO: heartbeat_gate.py (deterministic pre-check before injection)
- CONNECTS TO: preembed.py (current context writer — navigator replaces/augments)
- CONNECTS TO: autocomplete chain (the ultimate goal — structure prevents deviation)
- INFORMS: Phase 1-5 build plan (what to build, in what order)
- GATES: D-KI-01 through D-KI-07 (PO decisions needed before building)
