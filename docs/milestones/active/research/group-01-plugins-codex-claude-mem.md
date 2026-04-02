# Research Group 01 — Codex Plugin + Claude-Mem

**Date:** 2026-04-02
**Status:** RESEARCHED — findings ready for PO review
**Workflow step:** 1/4 (Research → Classify → Document → Build)

---

## codex-plugin-cc (openai/codex-plugin-cc)

**Source:** https://github.com/openai/codex-plugin-cc
**Released:** 2026-03-30 by OpenAI
**Stars:** ~2.2K
**Type:** Claude Code plugin (NOT MCP server)

### What It Does

Cross-provider bridge: call OpenAI's Codex engine from within Claude Code.

**6 slash commands:**

| Command | Purpose |
|---------|---------|
| `/codex:setup` | Verify/install/configure Codex CLI. Enable/disable review gate. |
| `/codex:review` | Standard code review against uncommitted changes or branch diffs. Read-only. NOT steerable (no custom focus). |
| `/codex:adversarial-review` | Devil's advocate — challenges design trade-offs, assumptions, failure modes. Customizable focus. |
| `/codex:rescue` | Delegate a task to Codex as a subagent. Foreground or background. |
| `/codex:status` | Check background job progress. |
| `/codex:result` | Get completed job output. Includes session ID for resume. |

**Review Gate (optional):** Stop hook that runs independent Codex review before Claude can complete. If issues found, stop is blocked. WARNING: can create long-running loops that drain both Claude and Codex limits rapidly.

### Installation

```
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/codex:setup
```

**Prerequisites:** Node.js 18.18+, Codex CLI (auto-installs if npm available)

### Authentication

Two paths:
- **ChatGPT subscription (OAuth):** `codex login` → browser flow. Works with Plus ($20/mo), Pro ($200/mo), Business, Enterprise. Free/Go plans temporarily include Codex.
- **OpenAI API key:** `codex login --api-key`. Billed at API rates.

No standalone Codex subscription exists.

### Can It Use LocalAI?

**Yes, in theory.** Codex CLI supports custom providers:

```toml
# .codex/config.toml
[model_providers.localai]
name = "LocalAI"
base_url = "http://localhost:8090/v1"
env_key = "LOCALAI_API_KEY"

model = "hermes"
model_provider = "localai"
```

**Caveats:**
- Designed for OpenAI's Codex models (gpt-5.x). Small models (3B/7B) unlikely to produce useful adversarial reviews.
- `/codex:rescue` delegation requires multi-step reasoning beyond small model capability.
- Qwen3.5-9B might handle basic structured reviews.
- Untested territory.

### Known Issues

- **Issue #18:** Sandbox restriction — `bwrap: loopback: Failed RTM_NEWADDR` in restricted environments
- **Issue #59:** Review gate state mismatch — setup writes to temp dir but hook reads from persistent dir
- `/codex:review` not steerable (must use adversarial-review for custom focus)
- Review gate can create runaway loops draining both providers' limits

### Fleet Relevance

| Aspect | Assessment |
|--------|-----------|
| Cross-model quality gate | HIGH VALUE — independent AI validates work |
| Adversarial review for security-critical | HIGH VALUE — design challenge from different perspective |
| Task delegation | MEDIUM — useful for complex subtasks |
| Review gate pattern | HIGH VALUE as CONCEPT — implement natively with LocalAI |
| Cost impact | NEGATIVE — adds OpenAI costs on top of Claude |
| LocalAI independence mission | CONFLICTS — adds cloud dependency |

**Key takeaway:** The **review gate architectural pattern** (Stop hook → independent review → block if issues) is the most valuable concept. Can be implemented natively without the OpenAI dependency. The plugin itself is useful for cross-provider validation when budget allows.

---

## claude-mem (thedotmack/claude-mem)

**Source:** https://github.com/thedotmack/claude-mem
**Stars:** 44,666 | **Forks:** 3,366
**License:** AGPL-3.0
**Type:** Claude Code plugin (with internal MCP server)
**Docs:** https://docs.claude-mem.ai

### What It Does

Persistent cross-session memory for Claude Code:
- **Captures** every tool execution via lifecycle hooks
- **Compresses** observations using Claude Agent SDK (background worker)
- **Stores** in SQLite + ChromaDB vector store
- **Injects** relevant context at session start
- **Provides** 4 MCP search tools for semantic/full-text retrieval

### 4 MCP Tools

| Tool | Purpose |
|------|---------|
| `search` | Full-text search (AND/OR/NOT/phrase). Returns compact index (~50-100 tokens/result). |
| `timeline` | Chronological view around a specific observation. |
| `get_observations` | Fetch full details for specific IDs (after search narrows results). |
| `__IMPORTANT` | Context/instruction tool (injected awareness). |

**3-layer progressive disclosure:** search (2K tokens) → identify relevant IDs → get_observations (3K tokens) = ~5K total vs ~50K for naive RAG. **10x token savings.**

### Installation

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
# Restart Claude Code
```

**OpenClaw gateway installer:**
```bash
curl -fsSL https://install.cmem.ai/openclaw.sh | bash
```

**Auto-installs:** Bun, uv (Python for ChromaDB), Node.js

### Architecture

- **Worker service:** Express.js on port 37777 (Bun daemon)
- **Storage:** `~/.claude-mem/` — SQLite (source of truth, ACID) + ChromaDB (vector embeddings)
- **5 lifecycle hooks:** SessionStart, UserPromptSubmit, PostToolUse, Summary, SessionEnd
- **Context injection:** At SessionStart, queries recent summaries (10) + observations (50), injects via `hookSpecificOutput.additionalContext`
- **Requires:** `ANTHROPIC_API_KEY` for observation compression (calls Claude API in background)
- **Web UI:** http://localhost:37777 for settings, real-time memory stream

### OpenClaw Integration

**Explicit support exists:**
- OpenClaw-specific installer script
- Plugin exports `claudeMemPlugin()` for OpenClaw gateway
- Subscribes to 7 OpenClaw lifecycle events
- Provides `/claude-mem-status` and `/claude-mem-feed` commands

**Known bugs:**
- Issue #1106: OpenClaw installer missing `openclaw.extensions` field in package.json
- Issue #1471: MCP server not registered properly (marketplace root `.mcp.json` empty)

### CRITICAL Known Issues for Fleet

| Issue | Severity | Impact on Fleet |
|-------|----------|----------------|
| **ChromaDB OOM (#1077)** | CRITICAL | chroma-mcp processes never cleaned up — 146 orphans consumed 5.6GB on 32GB machine |
| **35GB RAM (#707)** | CRITICAL | ChromaDB can consume 35GB+ loading vector DB on macOS |
| **Spawn storm (#1063)** | CRITICAL | Killing worker with 6+ sessions → 641 chroma-mcp processes, 75%+ CPU, ~64GB virtual, nearly crashed WSL2 |
| **No connection mutex** | HIGH | Concurrent sessions race through ChromaDB connection, each spawning subprocess |
| **WSL2 specific** | HIGH | Spawn storm issue specifically documented in WSL2 — our exact environment |

**CRITICAL FOR US:** The spawn storm issue (#1063) was reported on WSL2 specifically. With 10 concurrent agents, this could be catastrophic.

**Mitigation:** SQLite-only mode available (loses semantic search, keeps full-text search). This avoids ChromaDB entirely.

### Comparison: claude-mem vs Built-in .claude/memory/

| Feature | Built-in Memory | claude-mem |
|---------|----------------|------------|
| Storage | Git-tracked .md files | SQLite + ChromaDB database |
| Search | None (Claude reads index) | FTS5 + vector semantic search |
| Auto-capture | Corrections only | ALL tool executions |
| Token cost | Free (files in context) | Background API calls for compression |
| Complexity | Zero | Significant (worker, ChromaDB, Bun) |
| Reliability | Rock solid | Known OOM/spawn issues |
| Scalability | 200-line index cap | Thousands of observations |
| Portability | Git-tracked, shareable | Local database only |

**They are complementary, not competing.** Built-in memory = lightweight reliable preferences. claude-mem = large-scale recall with search.

### Fleet Relevance

| Aspect | Assessment |
|--------|-----------|
| Cross-session memory | HIGH VALUE — agents retain context across restarts |
| Shared memory across agents | POSSIBLE — shared ~/.claude-mem/ database |
| Token savings (3-layer search) | HIGH VALUE — 10x reduction vs naive RAG |
| Heartbeat context (local search) | HIGH VALUE — recall without Claude costs |
| WSL2 stability (ChromaDB) | CRITICAL RISK — spawn storms documented |
| Concurrent agents (10) | HIGH RISK — no connection mutex |
| SQLite-only mode | VIABLE WORKAROUND — loses semantic search, keeps FTS |

**Key takeaway:** claude-mem is valuable BUT must use **SQLite-only mode** for fleet deployment to avoid ChromaDB spawn storms on WSL2. FTS5 search is sufficient for most agent recall needs. Semantic search can be added later via LightRAG (which we're already planning).

---

## Classification Per Agent Role

### codex-plugin-cc

| Role | Relevance | Use Case |
|------|-----------|----------|
| fleet-ops | HIGH | Adversarial review during 7-step review protocol |
| devsecops-expert | HIGH | Security-focused adversarial review on PRs |
| architect | MEDIUM | Design decision challenge via adversarial review |
| software-engineer | MEDIUM | Code review second opinion |
| qa-engineer | LOW | QA has own challenge mechanisms |
| devops | LOW | Infrastructure code review |
| PM / writer / UX / accountability | NONE | Not code-producing roles |

### claude-mem

| Role | Relevance | Use Case |
|------|-----------|----------|
| ALL agents | HIGH | Cross-session memory, context recovery after prune/compact |
| PM | HIGH | Sprint history, past decisions, assignment patterns |
| fleet-ops | HIGH | Review history, approval patterns, methodology violations seen |
| architect | HIGH | Design decisions, architecture patterns discovered |
| software-engineer | HIGH | Codebase knowledge, implementation patterns |
| devsecops-expert | HIGH | Security findings, vulnerability patterns |
| QA | MEDIUM | Test patterns, failure categories |
| devops / writer / UX / accountability | MEDIUM | Role-specific recall |

---

## Open Questions for PO

### codex-plugin-cc

1. **Budget:** Do we want to spend OpenAI API credits alongside Claude? Or implement the review gate pattern natively?
2. **Which agents get it?** All code-producing agents, or just fleet-ops + devsecops for review?
3. **LocalAI alternative:** Implement the same review gate concept using LocalAI hermes/Qwen as the independent reviewer?
4. **Review gate:** Enable the Stop hook on specific agents? Risk of runaway loops vs quality benefit?

### claude-mem

1. **SQLite-only mode:** Accept losing semantic search to avoid ChromaDB spawn storms on WSL2?
2. **Shared vs per-agent:** One shared database for all agents, or per-agent databases?
3. **OpenClaw installer:** Use the OpenClaw-specific installer (has known bugs) or install via plugin system?
4. **ANTHROPIC_API_KEY:** Observation compression costs Claude tokens in background — acceptable?
5. **LightRAG relationship:** Use claude-mem for agent memory + LightRAG for project knowledge graph, or consolidate?

---

## Next Steps (awaiting PO direction)

1. PO reviews findings and answers open questions
2. Decide: install codex-plugin-cc or implement pattern natively
3. Decide: claude-mem SQLite-only mode for fleet
4. Update config/agent-tooling.yaml with real plugin data
5. Update complete-roadmap.md with researched milestones
6. Move to next research group: 1000+ skills/commands/plugins classification
