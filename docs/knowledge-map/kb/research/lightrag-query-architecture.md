# LightRAG Query Architecture — Zero-LLM Path

**Type:** Research Finding
**Date:** 2026-04-03
**Sources:** LightRAG source code analysis (operate.py, lightrag.py)

## Query Pipeline — Where the LLM Is Used

Two LLM calls during a query:

1. **Keyword Extraction** (mandatory for KG modes): LLM extracts high-level and low-level keywords from the query as JSON. ~500 token prompt.
2. **Response Generation** (final step): LLM synthesizes a natural language answer from retrieved context.

## Zero-LLM Query Paths

### Path A: KG modes + pre-supply keywords + only_need_context

```
Pre-supply hl_keywords + ll_keywords in QueryParam
+ only_need_context = true
→ Keyword extraction: SKIPPED (pre-supplied)
→ Vector/graph search: embedding-only (no LLM)
→ Response generation: SKIPPED
→ Result: raw context (entities + relationships + chunks)
→ LLM calls: 0
```

### Path B: Naive mode + only_need_context

```
mode = "naive"
+ only_need_context = true
→ No keyword extraction (naive mode never uses keywords)
→ Pure vector search on chunks_vdb
→ Response generation: SKIPPED
→ LLM calls: 0
```

## Our Implementation

The navigator uses Path A:
- `_extract_keywords()` pre-extracts from task context (regex, no LLM)
- Passes `hl_keywords` + `ll_keywords` + `only_need_context=true` to LightRAG
- LightRAG returns raw graph context
- Navigator truncates to budget and assembles into knowledge-context.md

This means the entire autocomplete web — from KB sync to graph query to navigator assembly to gateway injection — runs with zero LLM cost at query time.

## When LLM IS Needed

1. **Non-KB document indexing** — LightRAG's text insertion path uses the LLM for entity extraction. This is for manuals, code, design docs (content without ## Relationships sections).
2. **Full response generation** — if an agent queries LightRAG directly (not via navigator) without `only_need_context=true`, the LLM generates a prose answer.
3. **Entity merging summaries** — when `FORCE_LLM_SUMMARY_ON_MERGE >= 8` accumulated descriptions, LLM summarizes. Only during indexing, not queries.

## Model Requirements per Task

| Task | Model Needed | Can Use 3B? |
|------|-------------|-------------|
| KB sync (graph API) | None | N/A |
| Navigator graph query | None (pre-supplied keywords) | N/A |
| Text insertion (manuals/code) | 7B+ for extraction | Mediocre quality |
| Direct query with response | Any (keyword extract + respond) | Yes for simple lookups |

## Relationships

- IMPLEMENTED IN: fleet/core/navigator.py (_extract_keywords, _query_graph)
- CONNECTS TO: LightRAG API (/query endpoint)
- CONNECTS TO: kb/infrastructure/navigator.md (navigator documentation)
- CONNECTS TO: kb/infrastructure/lightrag.md (LightRAG system)
- CONNECTS TO: kb/research/localai-optimization.md (model settings for extraction)
- ENABLES: LocalAI independence (zero Claude tokens for graph queries)
