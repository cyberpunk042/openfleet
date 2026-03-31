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

### 3.4 LocalAI Capabilities (Research pending)

*Awaiting research agent results.*

### 3.5 OpenClaw / Claude Plugins (Research pending)

*Awaiting research agent results.*

---

## 4. Proposed Extension Milestones

### Wave 6: AGENT INTELLIGENCE (Critical)

> PO: "making it instinctive and natural for the AI"
> PO: "everything has to be so well thought, things has to be so clear to the agent"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-AI01 | **Agent Identity System** | Fill IDENTITY.md + CLAUDE.md for all 11 agents. Each gets personality, voice, working philosophy, IRC presence. Not templates — real characters. |
| M-AI02 | **Agent Self-Knowledge** | Each agent gets populated USER.md (who they serve), TOOLS.md (their environment), and initial MEMORY.md. Agents know their context. |
| M-AI03 | **Agent Communication Protocol** | Define how agents request help, escalate, coordinate. Structured `request_collaboration()` protocol. Driver boundaries (PM vs fleet-ops). |
| M-AI04 | **Agent Research Capability** | Agents can research online (web search) and in code (grep, read, explore). Define which agents get which research tools. |
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
| M-KB01 | **Connect AICP RAG to Fleet** | Wire `aicp/core/kb.py` into fleet agent context. Agents can query project knowledge before starting work. |
| M-KB02 | **Domain Knowledge Bases** | Create per-project KBs: fleet KB, AICP KB, DSPD KB, NNRT KB. Ingest docs, code comments, design docs. |
| M-KB03 | **Knowledge Persistence IaC** | SQLite RAG DBs backed up to host filesystem. `make setup` restores. Survives docker purge. IaC for backup/restore. |
| M-KB04 | **Agent Pre-Embedding** | Before each task, embed relevant context (task description, related docs, recent changes) and inject top-K chunks into agent prompt. |
| M-KB05 | **Cross-Agent Knowledge Sharing** | When one agent learns something (challenge finding, bug pattern, architecture decision), it gets ingested into shared KB for all agents. |

### Wave 9: TOOLS & SPECIALIZATIONS (High)

> PO: "AIs agents also need to know their Tools, Stacks and Skills"
> PO: "make them available to them with the project + config + IaC + setups"

| ID | Milestone | Description |
|----|-----------|-------------|
| M-TS01 | **Tool Registry** | Formalize tool definitions per agent. Map capabilities to actual tools (MCP servers, CLI commands, API endpoints). |
| M-TS02 | **Skill Assignment Enforcement** | Move from documentary to enforced skill routing. Agent can only use skills assigned to it. Marketplace discovery for new skills. |
| M-TS03 | **Stack Configuration** | Each agent's TOOLS.md populated with real stack: languages, frameworks, infra access, credentials (via env vars). |
| M-TS04 | **Agent IaC** | `make agent-setup <name>` provisions an agent with all tools, skills, context, KB access. Reproducible from scratch. |

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
| Wave 11: Integration & Plane | 4 | Medium |
| **Total** | **29** | |

Combined with the original 47: **76 total milestones** across 11 waves.

---

## 7. Research Still Pending

- [ ] LocalAI full capability audit (RAG, stores, embeddings, function calling, multimodal)
- [ ] OpenClaw / Claude plugin ecosystem (MCP servers, Agent SDK, knowledge sharing)
- [ ] Verify model landscape (Qwen3, Gemma 3, Phi-4-mini, BFCL standings)
- [ ] LocalAI memory/collection persistence mechanisms

These findings will refine Waves 8-10 when complete.

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
