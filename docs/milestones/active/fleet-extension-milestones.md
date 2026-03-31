# Fleet Extension Milestones — Beyond the 47

**Date:** 2026-03-31
**Status:** PLANNING — research in progress, PO requirements quoted
**Predecessor:** 47 strategic milestones (COMPLETE), 8 integration wires (COMPLETE)

---

## 1. Origin — Product Owner Requirements

> "I do not believe we achieved everything we said we would about the multiple options and their validation and the full extent of the capabilities we had discussed to put in place like the right model with the right latest compression and such."

> "we need to be sure that we are honest and Identify the real gap and build the right bulletproof solution."

> "This was never meant to be over I am extending the milestones again"

> "Cutting edge development can mean a lot sometimes, forgetting those research and/or the requirements is dangerous to lose potential."

> "Do not minimize what I said. This is a long task, multiple milestones, treat it as such."

---

## 2. Honest Gap Assessment

### What We Built (47 milestones)
Decision logic — routing, budgets, challenges, storms, model management, labor attribution. All unit-tested, integration-tested, committed. But this is the **decision layer**. It decides WHAT to route WHERE. The intelligence, tooling, and runtime are not there yet.

### What's Missing (13 areas identified)

| # | Area | Status | Gap |
|---|------|--------|-----|
| 1 | Agent identity & personality | 1/11 agents have personality | **Critical** |
| 2 | Agent autonomy tuning | Heartbeat exists, not tuned | **Critical** |
| 3 | Context-aware agent behavior | Session telemetry built, agents don't use it | **High** |
| 4 | Escalation logic | Budget constrains, no dynamic escalation | **High** |
| 5 | Agent online research | Not addressed | **Missing** |
| 6 | Agent code/docs research | Not addressed | **Missing** |
| 7 | RAG / Knowledge bases | AICP has full RAG pipeline, not connected to fleet | **High** |
| 8 | LocalAI memory persistence | Stores API is ephemeral, SQLite RAG persists | **Medium** |
| 9 | Plane integration | Not addressed | **Missing** |
| 10 | Agent tools & specializations | skill-assignments.yaml documentary only | **High** |
| 11 | Brain integration | FleetContext exists, intelligence missing | **High** |
| 12 | Agent file review & structure | Skeleton right, content empty | **Critical** |
| 13 | Model compression/validation | Schemas only, no real benchmarks run | **High** |

---

## 3. Research Findings

### 3.1 Agent File Audit (Completed)

**11 agents audited. Naturalness score: 6.5/10.**

Structure per agent: SOUL.md, IDENTITY.md, AGENTS.md, CLAUDE.md, HEARTBEAT.md, USER.md, TOOLS.md, agent.yaml, context/

**What works:**
- SOUL.md as ethical foundation
- Heartbeat polling pattern
- Capability lists per agent
- Delivery phases with gates
- Labor attribution
- Constraint system (max_turns, approval_required)

**What's empty/missing:**
- 9/11 agents have blank IDENTITY.md (no personality)
- 9/11 agents have no CLAUDE.md (no character)
- All USER.md are empty templates
- All TOOLS.md are empty templates
- No agent-to-agent communication protocol
- No escalation rules defined
- Memory system defined but never populated
- Driver coordination (project-manager vs fleet-ops) boundaries unclear
- Context injection ad-hoc, not standardized

**Key agents with real configuration:**
- **devsecops-expert (Cyberpunk-Zero)**: Full personality, structured heartbeat, security workflow
- **project-manager**: Role clarity, SCRUM methodology, agent assignment matrix
- **fleet-ops**: Board monitoring, quality enforcement

### 3.2 Model Compression (Completed)

**Immediate wins (not being used):**
- KV cache quantization (`--cache-type-k q4_0 --cache-type-v q4_0`) — 4x KV savings
- Flash Attention (`--flash-attn`) — further memory reduction + speed
- Combined with Q4_K_M weights: 16-24K context on 8GB VRAM

**Best 8B models by task:**

| Task | Best Model | Why |
|------|-----------|-----|
| Function calling | Hermes 2 Pro (current) | Purpose-built, `<tool_call>` format |
| General instruction | Qwen 2.5 7B | Stronger than Hermes for general tasks |
| Code | Qwen 2.5 Coder 7B | Competitive with much larger models |
| Reasoning | DeepSeek R1 Distill 8B | Chain-of-thought, but verbose |
| Structured output | Hermes 2 Pro / Qwen 2.5 7B | Both strong |

**Dual GPU (8GB + 11GB = 19GB) enables:**
- 14B models at Q5_K_M — massive quality jump
- Qwen 2.5 14B or DeepSeek R1 14B become viable
- 8B models at FP16 — zero quantization loss

**BitNet**: Not production ready. Standard GGUF quantization remains the practical choice.

**Models to verify (may be stale):**
- Qwen3-8B release status
- Gemma 3 variants
- Phi-4-mini existence
- BFCL leaderboard current standings

### 3.3 AICP Existing Infrastructure (Discovered)

AICP already has significant infrastructure that fleet milestones didn't connect to:

| Module | What It Does | Fleet Connection |
|--------|-------------|------------------|
| `aicp/core/rag.py` | SQLite-backed vector store, cosine similarity, embedding via LocalAI | **Not connected** |
| `aicp/core/kb.py` | Knowledge base with file/dir ingestion, BGE reranker | **Not connected** |
| `aicp/core/stores.py` | LocalAI `/stores/` API client (ephemeral) | **Not connected** |
| `aicp/core/chunking.py` | Text chunking for embeddings | Used by rag.py |
| `aicp/core/skills.py` | 3-layer skill system (global, project, Claude commands) | **Not connected** |
| `aicp/core/tools.py` | Function calling with LocalAI | **Not connected** |
| `aicp/core/context.py` | Project context builder for AI backends | **Not connected** |
| `aicp/core/cluster.py` | Multi-node coordination | **Not connected** |
| `aicp/core/gpu.py` | GPU detection and auto-config | **Not connected** |

**Critical insight**: The RAG pipeline in AICP (`rag.py` + `kb.py`) uses SQLite for persistence — it survives docker purges because the DB is on the host filesystem. The LocalAI stores API (`stores.py`) is ephemeral. The solution to the PO's persistence requirement is to use the SQLite-backed RAG, not LocalAI stores.

### 3.4 LocalAI Capabilities (Completed)

**Full local RAG stack already available — not being used.**

| Feature | Endpoint | Model | Runs On | Status |
|---------|----------|-------|---------|--------|
| Embeddings | `/v1/embeddings` | nomic-embed-text-v1.5 | CPU | Configured, not used by fleet |
| Stores (vector DB) | `/stores/set`, `/stores/find` | N/A | CPU | Available, not used |
| Reranking | `/v1/rerank` | bge-reranker-v2-m3 | CPU | Configured, not used by fleet |
| Function calling | `/v1/chat/completions` (tools) | hermes models | GPU | Grammar config MISSING |
| Vision | `/v1/chat/completions` (image) | LLaVA | GPU | Configured |
| Speech-to-text | `/v1/audio/transcriptions` | Whisper | CPU | Configured |
| Text-to-speech | `/v1/audio/speech` | Piper | CPU | Configured |
| Image generation | `/v1/images/generations` | Stable Diffusion | GPU | Configured |

**Critical: Embedding + Reranker run on CPU simultaneously with GPU LLM.** No model swapping needed for RAG operations. This is a huge advantage — RAG queries cost zero GPU time.

**Critical persistence bug:** Docker-compose does NOT mount `/data` volume. All stores, agent state, and KB collections are lost on container recreate. Fix:
```yaml
volumes:
  - ./data:/data
environment:
  - LOCALAI_DATA_PATH=/data
```

**LocalAI v4.0 new capabilities (may not be in current install):**
- Built-in agent system with per-agent knowledge bases
- MCP tool support in model YAML configs
- Video generation, sound generation, voice activity detection, object detection
- Realtime API (WebSocket for live audio)

**Function calling grammar config (missing from hermes YAMLs):**
```yaml
function:
  parallel_calls: true
  mixed_mode: false
```
This enables grammar-constrained decoding for reliable tool use on small models.

**Prompt caching (missing from hermes-3b):**
```yaml
prompt_cache_path: hermes-3b-cache
prompt_cache_all: true
```

### 3.5 OpenClaw / Claude Ecosystem (Completed)

**Scale of available tooling is massive — we're using almost none of it.**

| Ecosystem | Scale | What It Offers |
|-----------|-------|----------------|
| OpenClaw Skills Registry | **5,400+ skills** | Ready-made capabilities via mcporter CLI |
| Claude Code Plugins | **9,000+ plugins** | Packaged skills, agents, hooks, MCP servers |
| MCP Server Registry | **1,000+ servers** | GitHub, Slack, Postgres, browsers, filesystems |
| Agent Skills Standard | Open spec | SKILL.md with frontmatter, progressive disclosure |

**Claude Agent SDK — Agent Teams (Swarm Mode):**
- Lead agent + 2-5 teammates, each in own context window + git worktree
- Shared task list with dependency tracking and file-locking
- **Mailbox-based direct messaging** between teammates
- Quality gates: `TeammateIdle`, `TaskCreated`, `TaskCompleted` hooks
- Plan approval: teammates can be required to plan before implementing
- Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`

**This is critical**: Agent Teams provides the inter-agent communication protocol we identified as missing in the agent file review. Instead of building our own, we should evaluate whether Agent Teams fits our fleet orchestration model.

**Claude Code Skills Architecture:**
- SKILL.md with YAML frontmatter (description, model override, effort override, allowed-tools, context fork)
- Progressive disclosure: descriptions load at ~100 tokens, full instructions only on invocation
- Scopes: enterprise → personal → project → plugin (priority order)
- Agent-specific skills via project directories, plugins, or subagent definitions
- Dynamic: `$ARGUMENTS`, shell injection, supporting files

**Cost Optimization:**
- Prompt caching: **90% discount** on cached input tokens
- Batch API: **50% discount** for async processing
- Both directly relevant to fleet operations at scale

**Knowledge Sharing Mechanisms:**
- CLAUDE.md + auto memory (file-based, deterministic)
- MCP servers (custom RAG endpoint)
- Claude-Mem plugin (session capture + semantic retrieval)
- `@imports` syntax in CLAUDE.md for shared docs
- `--add-dir` for cross-project context
- Agent SDK: session resume/fork for continuity

**Key insight**: Claude Code's context system is file-based and deterministic, NOT embedding-based. For true semantic RAG, we need either our AICP RAG pipeline (SQLite + LocalAI embeddings) or a custom MCP server wrapping a vector DB. Both options are already partially built.

---

## 4. Proposed Extension Milestones

### Wave 6: AGENT INTELLIGENCE (Critical)

> PO: "making it instinctive and natural for the AI"
> PO: "everything has to be so well thought, things has to be so clear to the agent"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-AI01 | **Agent Identity System** | Fill IDENTITY.md + CLAUDE.md for all 11 agents. Each gets personality, voice, working philosophy, IRC presence. Not templates — real characters. |
| M-AI02 | **Agent Self-Knowledge** | Each agent gets populated USER.md (who they serve), TOOLS.md (their environment), and initial MEMORY.md. Agents know their context. |
| M-AI03 | **Agent Communication Protocol** | Evaluate Agent Teams (swarm mode) vs custom protocol. If Agent Teams fits: enable `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, configure mailbox messaging, shared task lists, quality gates. If not: build structured `request_collaboration()`. Define driver boundaries (PM vs fleet-ops). |
| M-AI04 | **Agent Research Capability** | Agents can research online (WebSearch, WebFetch) and in code (Grep, Read, Glob, Explore agent). Define which agents get which research tools via `allowed-tools` in SKILL.md. |
| M-AI05 | **Agent Memory Lifecycle** | Populate memory system: daily logs (memory/YYYY-MM-DD.md), curated wisdom (MEMORY.md). Define archival, retention, cross-session persistence. |
| M-AI06 | **Context Injection Standard** | Standardize FleetContext fields, validation, guaranteed structure. Every agent gets consistent, complete context on every cycle. |

### Wave 7: AUTONOMY TUNING (Critical)

> PO: "fine tune the timing for the sleep and offline and silent heartbeat"
> PO: "very responsive and prompt to work... do not waste breath"
> PO: "a lot does not require agent"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-AT01 | **Heartbeat Calibration** | Tune heartbeat intervals per agent role. Drivers: fast (60s). Workers: adaptive (idle=300s, active=30s). Sleep/wake thresholds. |
| M-AT02 | **No-Agent Decision Layer** | Define what doesn't need an agent: direct HTTP, MCP tool calls, template responses. Route to `direct` backend. Saves 100% agent cost. |
| M-AT03 | **Context-Aware Agent Lifecycle** | Agents monitor their own context usage (via session telemetry). Trigger strategic compaction, extract artifacts to memory, recchain with fresh context. |
| M-AT04 | **Escalation Engine** | Dynamic escalation: effort level, model tier, backend source — all adaptive based on task complexity, confidence tier, and budget mode. |
| M-AT05 | **Silent Heartbeat Protocol** | Heartbeats that cost zero when idle: no LLM call, just API checks. LLM only when work is found. Budget-aware heartbeat frequency. |

### Wave 8: KNOWLEDGE & RAG (High)

> PO: "RAG of knowledge bases, where global and project specific or domain specific informations can be shared and updated"
> PO: "Memories / Knowledge Base Collections would persist as I purge all the docker"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-KB01 | **Connect AICP RAG to Fleet** | Wire `aicp/core/kb.py` into fleet agent context via custom MCP server. Agents query project knowledge using standard MCP tool calls. Alternatively: direct LocalAI stores API integration. |
| M-KB02 | **Domain Knowledge Bases** | Create per-project KBs: fleet KB, AICP KB, DSPD KB, NNRT KB. Ingest docs, code comments, design docs. |
| M-KB03 | **Knowledge Persistence IaC** | SQLite RAG DBs backed up to host filesystem. `make setup` restores. Survives docker purge. IaC for backup/restore. |
| M-KB04 | **Agent Pre-Embedding** | Before each task, embed relevant context (task description, related docs, recent changes) and inject top-K chunks into agent prompt. |
| M-KB05 | **Cross-Agent Knowledge Sharing** | When one agent learns something (challenge finding, bug pattern, architecture decision), it gets ingested into shared KB for all agents. |

### Wave 9: TOOLS & SPECIALIZATIONS (High)

> PO: "AIs agents also need to know their Tools, Stacks and Skills"
> PO: "make them available to them with the project + config + IaC + setups"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-TS01 | **Tool Registry via MCP** | Map agent capabilities to MCP servers (1,000+ available). Each agent gets configured MCP servers in `.mcp.json`. GitHub, Slack, Postgres, filesystem, browser automation. |
| M-TS02 | **Skill Assignment via SKILL.md** | Convert documentary skill-assignments.yaml to real SKILL.md files per agent. Use `allowed-tools`, `model` overrides, `context: fork` for isolation. Leverage 5,400+ OpenClaw skills registry. |
| M-TS03 | **Stack Configuration** | Each agent's TOOLS.md populated with real stack: languages, frameworks, infra access, credentials (via env vars). Plugin packaging for shareable agent configs. |
| M-TS04 | **Agent IaC** | `make agent-setup <name>` provisions an agent with all tools, skills, MCP servers, context, KB access. Plugin structure for reproducibility. |

### Wave 10: MODEL OPTIMIZATION (High)

> PO: "the right model with the right latest compression"
> PO: "the multiple options and their validation"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-MO01 | **Enable KV Cache Quantization** | Add `--cache-type-k q4_0 --cache-type-v q4_0 --flash-attn` to all model YAML configs. Immediate VRAM savings. |
| M-MO02 | **Add Qwen 2.5 Models** | Add Qwen 2.5 7B Instruct + Qwen 2.5 Coder 7B to model registry. GGUF configs, benchmarks against Hermes. |
| M-MO03 | **Run Real Benchmarks** | Execute `model_benchmark.py` against actual LocalAI. Record real latency, quality, function calling accuracy. Not schemas — real numbers. |
| M-MO04 | **Multi-Model Strategy** | Configure model swap for task type: Hermes for function calling, Qwen for general, Qwen Coder for code. Router-driven. |
| M-MO05 | **Dual GPU Preparation** | When second GPU arrives: tensor split config, 14B model configs (Qwen 14B, DeepSeek R1 14B), updated VRAM calculations. |

### Wave 11: INTEGRATION & PLANE (Medium)

> PO: "automatically write / update Plane pages based on the progresses"
> PO: "inform the Writer to let him know he can add his level of detail"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-IP01 | **Plane Auto-Update** | When milestones complete, auto-update Plane pages via API. Progress tracking in real-time. |
| M-IP02 | **Writer Notification** | When content changes, notify technical-writer agent to review and enhance. Multi-block artifact compatibility. |
| M-IP03 | **AICP ↔ Fleet Bridge** | Connect `router_unification.py` to AICP controller. Fleet routing decisions flow through AICP to actual backends. |
| M-IP04 | **Fleet Runtime Deployment** | Actually run the orchestrator with agents. Operational readiness milestones (#17-21). |
| M-IP05 | **Cost Optimization** | Enable prompt caching (90% discount), Batch API (50% discount) for non-latency-critical work. Claude-Mem plugin for cross-session knowledge. Track savings in budget analytics. |

---

## 5. Dependency Map

```
Wave 6: AGENT INTELLIGENCE ← must come first (agents need to know who they are)
  ↓
Wave 7: AUTONOMY TUNING ← agents need identity before tuning behavior
  ↓
Wave 8: KNOWLEDGE & RAG ← agents need to be autonomous before querying KB
  ↓
Wave 9: TOOLS & SPECIALIZATIONS ← KB informs what tools each agent needs
  ↓
Wave 10: MODEL OPTIMIZATION ← can run in parallel with Wave 8-9
  ↓
Wave 11: INTEGRATION & PLANE ← brings everything together
```

**Wave 10 (Model Optimization)** can start immediately — M-MO01 (KV cache) is a config change, not code.

---

## 6. Milestone Count

| Wave | Milestones | Priority |
|------|-----------|----------|
| Wave 6: Agent Intelligence | 6 | Critical |
| Wave 7: Autonomy Tuning | 5 | Critical |
| Wave 8: Knowledge & RAG | 5 | High |
| Wave 9: Tools & Specializations | 4 | High |
| Wave 10: Model Optimization | 5 | High |
| Wave 11: Integration & Plane | 5 | Medium |
| **Total** | **30** | |

Combined with the original 47: **77 total milestones** across 11 waves.

---

## 7. Research — ALL COMPLETE

- [x] Agent file audit — 11 agents, 10 critical gaps, 6.5/10 naturalness
- [x] Model compression — KV cache quant available now, Qwen 2.5 > Hermes for general, dual GPU enables 14B
- [x] LocalAI capabilities — full RAG stack on CPU, persistence bug found, v4 agents, function calling grammar
- [x] OpenClaw/Claude ecosystem — 5,400+ skills, 9,000+ plugins, 1,000+ MCP servers, Agent Teams swarm mode, prompt caching 90% off

### Items to verify (research agent knowledge may be stale):
- Qwen3-8B release status and benchmarks
- Gemma 3 variants
- Phi-4-mini existence
- BFCL leaderboard current standings for function calling
- LocalAI v4.0 availability in our Docker image version

---

## 8. Principles

From the PO:

> "everything has to be so well thought, things has to be so clear to the agent and its model of execution and intelligent choices obviously and adaptive choices and based on the settings too obviously"

This means:
1. **No skeleton implementations** — every milestone must be real, tested, and connected
2. **Research before building** — verify capabilities exist before designing
3. **Quote requirements** — trace every milestone to a PO statement
4. **IaC everything** — `make setup` reproduces the entire stack
5. **Persist everything** — nothing lost on docker purge, session end, or context compact
