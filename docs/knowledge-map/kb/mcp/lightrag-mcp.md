# LightRAG MCP Server

**Type:** External MCP Server
**Package:** daniel-lightrag-mcp (pip)
**Transport:** command (python -m daniel_lightrag_mcp)
**Tools:** 22 (documents, queries, knowledge graph, system)
**Auth:** Optional LIGHTRAG_API_KEY
**Installed for:** ALL agents (default)

## What It Does

Full MCP interface to the LightRAG knowledge graph. 22 tools across 4 categories:

**Document Management (8):** insert_text, insert_texts, upload_document, scan_documents, get_documents, get_documents_paginated, delete_document, clear_documents

**Query Operations (2):** query_text (6 modes: naive/local/global/hybrid/mix/bypass), query_text_stream (streaming)

**Knowledge Graph Operations (6):** get_knowledge_graph, get_graph_labels, check_entity_exists, update_entity, update_relation, delete_entity, delete_relation

**System Management (5):** get_pipeline_status, get_track_status, get_document_status_counts, clear_cache, get_health

## Fleet Use Case

Every agent can query the fleet knowledge graph. Example queries:
- "What systems connect to the orchestrator?" → global mode, relationship traversal
- "What tools does fleet-ops use?" → local mode, entity-focused
- "How does the heartbeat gate work?" → mix mode, all sources
- "What's related to security?" → hybrid mode, entities + relationships

This IS the autocomplete web made accessible. The graph contains every entity and relationship from 190+ KB entries.

## Relationships

- INSTALLED FOR: ALL agents (default MCP server)
- INSTALLED VIA: pip install daniel-lightrag-mcp (setup-mcp-deps.sh)
- CONNECTS TO: LightRAG container (port 9621 — LIGHTRAG_BASE_URL)
- CONNECTS TO: knowledge map (KB entries → indexed → graph → queried via MCP)
- CONNECTS TO: intent-map.yaml (navigator could use MCP queries to enrich injection)
- CONNECTS TO: injection-profiles.yaml (query results adapted per context tier)
- CONNECTS TO: navigator module (future — reads graph to assemble context)
- CONNECTS TO: InstructionsLoaded hook (future — inject graph query results)
