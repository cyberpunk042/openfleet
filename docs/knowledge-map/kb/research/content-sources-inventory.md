# Content Sources Inventory — What Feeds the Autocomplete Web

**Type:** Research Finding
**Date:** 2026-04-03
**Sources:** Fleet repo survey, map-to-RAG optimization research

## Two Indexing Paths

### Path 1: KB Sync (graph API, zero LLM)

For content with explicit `## Relationships` sections. Direct entity + relationship insertion via LightRAG /graph/entity/create and /graph/relation/create. Populates both graph AND vector stores.

**Content:** 220 KB entries across 12 branches

### Path 2: Text Insertion (LLM extraction for prose/code)

For content without structured relationships. LightRAG chunks the text, embeds chunks, and uses the LLM to extract entities/relationships. Feeds chunks_vdb for naive/mix queries AND the graph.

**Content:** ~100 additional files

## Content Estate

### Already Indexed (KB Sync)

| Branch | Files | Entities | Relationships |
|--------|-------|----------|---------------|
| systems | 22 | 22 + refs | ~200 |
| tools | 29 | 29 + refs | ~150 |
| skills | 60 | 60 + refs | ~300 |
| commands | 34 | 34 + refs | ~200 |
| hooks | 26 | 26 + refs | ~200 |
| plugins | 14 | 14 + refs | ~100 |
| agents | 10 | 10 + refs | ~100 |
| mcp | 9 | 9 + refs | ~50 |
| layers | 9 | 9 + refs | ~100 |
| infrastructure | 4 | 4 + refs | ~50 |
| research | 5 | 5 + refs | ~30 |
| **Total** | **222** | **~1,545** | **~2,295** |

### To Index (Text Insertion)

| Source | Files | Lines | Why |
|--------|-------|-------|-----|
| Manuals | 6 | 2,500 | Prose context — methodology reasoning, agent details |
| System docs (full) | 23 | 10,276 | Deep system knowledge beyond KB summaries |
| Research docs | 10 | 4,063 | Decision rationale, analysis findings |
| Cross-references.yaml | 1 | 327 | Role-system-tool mappings |
| Fleet core Python | 22 | ~12,000 | Actual code relationships, imports, functions |
| MCP tools.py | 1 | 2,787 | 29 tool implementations |
| Gateway | 4 | 1,437 | Context injection code |
| Config YAMLs | 8 | 1,289 | Agent-tooling, synergy-matrix, phases |
| Design docs (key) | 6 | ~15,000 | Architecture decisions, roadmap |
| Fleet-elevation | 31 | 14,715 | Agent design, onion layers, tool chains |
| Agent CLAUDE.md | 13 | 2,136 | Per-role instructions (what agents see) |
| **Total** | **~125** | **~66,000** | |

### Not Worth Indexing

- Scripts (57 bash files) — IaC, not knowledge
- Test files — validation, not knowledge
- `__init__.py`, `__pycache__` — boilerplate
- .env, .gitignore — configuration, not knowledge
- Completed/archived milestones — historical

## Indexing Strategy

1. **First:** KB sync (graph API) — structured relationships, zero LLM
2. **Second:** Entity deduplication — merge duplicate entities from KB sync
3. **Third:** Text insertion of manuals + system docs — prose chunks for naive/mix
4. **Fourth:** Text insertion of code files — actual relationships
5. **Fifth:** Text insertion of design docs + config — architecture decisions
6. **Ongoing:** Incremental KB sync when KB entries change

## Map-to-RAG Connections

The knowledge map metadata HELPS the RAG:
- **intent-map.yaml** → navigator selects graph query mode per role/stage
- **injection-profiles.yaml** → navigator budgets graph context per model tier
- **cross-references.yaml** → navigator enriches with tool→system connections
- **Navigator** → pre-extracts keywords (zero LLM queries)
- **KB entries** → graph entities with hand-written relationships (highest quality)

NOT indexed in RAG (used by navigator directly):
- intent-map.yaml — deterministic lookup, not search
- injection-profiles.yaml — configuration, not knowledge

## Relationships

- DEFINES: what content feeds LightRAG
- CONNECTS TO: kb/infrastructure/kb-sync.md (Path 1)
- CONNECTS TO: kb/infrastructure/lightrag.md (Path 2)
- CONNECTS TO: scripts/lightrag-index.sh (text insertion implementation)
- CONNECTS TO: scripts/setup-lightrag.sh (setup orchestration)
- CONNECTS TO: fleet/core/graph_enrichment.py (post-sync dedup)
- CONNECTS TO: fleet/core/navigator.py (query-time map usage)
