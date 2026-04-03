# System 22: Agent Intelligence — Autonomy, Escalation, Context, Autocomplete

**Type:** Fleet System (CROSS-CUTTING SPECIFICATION — touches many modules)
**ID:** S22
**Files:** autocomplete.py, context_assembly.py, heartbeat_context.py, preembed.py, context_writer.py, role_providers.py, smart_chains.py
**Total:** ~1,200 lines (overlaps with S19)

## What This System Does

The INTELLIGENCE layer that makes agents smart, adaptive, and responsive. Four domains:

### 1. Autonomy Tuning
Per-role adaptive thresholds (wake timing, sleep timing). Silent heartbeat protocol: brain evaluates sleeping agents deterministically ($0). 10 agents, 7 sleeping = 70% cost reduction. Currently hardcoded thresholds — needs config/agent-autonomy.yaml.

### 2. Escalation Logic
5 dimensions: effort (low→max), model (hermes-3b→opus), backend (localai→claude), session (compact→fresh), turns (5→30). Triggered by: task complexity (SP), agent confidence tier, outcome signals (rejection→escalate, challenge failed→escalate model, 3 corrections→prune).

### 3. Three-Tier Decision Model
- Tier 1 BRAIN: deterministic Python, FREE ($0). Operational decisions.
- Tier 2 LOCAL AI: free, fast. Simple evaluations (hermes-3b).
- Tier 3 CLAUDE: paid. Real work, complex reasoning.

Route to cheapest tier that can handle each decision.

### 4. Context Endgame (PO's Organic Model)
NOT rigid zones. Organic flow:
- 100-30% remaining: normal work
- 30-7%: progressive natural mindfulness
- 7% (safe tipping point): prepare extraction, keep working
- 5% (real tipping point): final extraction, commit, memory write
- 0%: still alive, engage regather protocol from memory (200-500 tokens vs 50K+ re-reads)

PO observed this pattern work naturally. Force compact BEFORE rollover = no 20% spike.

### 5. Autocomplete Chain
8-layer onion: IDENTITY → SOUL → CLAUDE.md → TOOLS.md → AGENTS.md → fleet-context → task-context → HEARTBEAT. Data arranged so AI's natural continuation IS correct professional action. Structure prevents deviation more reliably than rules.

## Relationships

- DRIVES: how agents behave, adapt, and manage resources
- CONNECTS TO: S06 agent lifecycle (autonomy thresholds, silent heartbeats)
- CONNECTS TO: S07 orchestrator (context refresh, dispatch decisions)
- CONNECTS TO: S12 budget (escalation constrained by budget)
- CONNECTS TO: S14 router (escalation uses model/backend selection)
- CONNECTS TO: S19 session (context management, telemetry)
- CONNECTS TO: knowledge map (autocomplete chain = map-driven injection)
- CONNECTS TO: claude-mem (4-layer context recovery: pre-embed → auto-memory → claude-mem → fleet RAG)
- ENTIRELY SPECIFICATION: adaptive thresholds, brain evaluation logic, escalation engine, per-role agent files NOT YET BUILT
