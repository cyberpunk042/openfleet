# System 2: Immune System

**Source:** `fleet/core/doctor.py` (250+ lines), `fleet/core/behavioral_security.py` (60+ lines), `fleet/core/self_healing.py`
**Status:** ✅ Live verified (VERIFICATION-MATRIX.md)
**Design docs:** `immune-system/01-07`, `fleet-elevation/20`

---

## Purpose

Detects AI diseases (deviation, laziness, protocol violations) and responds with teaching, compaction, or pruning. The doctor is hidden from agents — they experience consequences but don't see the detection. Runs as Step 2 in every orchestrator cycle.

## Key Concepts

### Disease Categories (teaching.py:28-39)

11 diseases defined:
1. `deviation` — work doesn't match verbatim requirement
2. `laziness` — partial work, fast completion, criteria not met
3. `confident_but_wrong` — 3+ corrections, model is wrong
4. `protocol_violation` — work tools called in wrong stage
5. `abstraction` — PO's words replaced with generic terms
6. `code_without_reading` — modifies without reading first
7. `scope_creep` — unrequested additions
8. `cascading_fix` — fix causes new break
9. `context_contamination` — stale context causes drift
10. `not_listening` — ignores corrections
11. `compression` — large scope minimized

### Detection Functions (doctor.py:114-250)

4 implemented:
- `detect_protocol_violation()` — fleet_commit in non-work stage → TRIGGER_TEACHING
- `detect_laziness()` — fast completion (< 2min/SP for SP≥3), partial acceptance criteria → TRIGGER_TEACHING
- `detect_stuck()` — no activity for threshold minutes → FORCE_COMPACT
- `detect_correction_threshold()` — 3+ corrections → PRUNE

6 NOT yet implemented:
- `detect_deviation`, `detect_scope_creep`, `detect_compression`, `detect_abstraction`, `detect_contribution_avoidance`, `detect_synergy_bypass`

### Response Actions (doctor.py:47-54)

- `NONE` — healthy
- `MONITOR` — increased monitoring
- `FORCE_COMPACT` — reduce context
- `TRIGGER_TEACHING` — deliver adapted lesson
- `PRUNE` — kill session, regrow fresh
- `ESCALATE_TO_PO` — human attention needed

### Agent Health Profile (doctor.py:81-91)

Per-agent tracking: correction_count, total_lessons, total_prunes, last_disease, is_in_lesson, is_pruned.

### DoctorReport (doctor.py:94-109)

Output consumed by orchestrator: detections, interventions, agents_to_skip (don't dispatch), tasks_to_block.

### Behavioral Security (behavioral_security.py)

Cyberpunk-Zero's layer. Scans for: credential exfiltration, DB destruction, security disabling. Can set `security_hold` on tasks (blocks approval). Even human requests get flagged if suspicious.

Runs as orchestrator Step 1 (`_security_scan`).

## Three Lines of Defense (fleet-elevation/20)

```
LINE 1: STRUCTURAL PREVENTION (before disease)
  - Autocomplete chain engineering
  - Stage-gated tool access (fleet_commit blocked outside work)
  - Contribution requirements as gates
  - Verbatim anchoring in context

LINE 2: DETECTION (when disease appears)
  - Doctor detection patterns (4 implemented, 6 pending)
  - Behavioral security scan (orchestrator Step 1)
  - Standards library checks

LINE 3: CORRECTION (after detection)
  - Teaching lessons (adapted to disease + context + agent)
  - Force compact (strip bloated context)
  - Prune and regrow (kill session, fresh start)
  - Readiness regression (task back to earlier stage)
```

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Doctor runs as Step 2 every cycle | Orchestrator → Doctor |
| **Teaching** | Doctor triggers teaching lessons | Doctor → Teaching |
| **Gateway** | Doctor prunes/compacts via gateway client | Doctor → Gateway |
| **Methodology** | Doctor knows stage rules | Methodology → Doctor |
| **Standards** | Standards check feeds detection | Standards → Doctor |
| **Events** | Protocol violations emit events | Doctor → Events |
| **Agent Lifecycle** | Pruned agents get is_pruned flag | Doctor → Lifecycle |
| **MCP Tools** | Stage-gated access IS structural prevention | MCP → Prevention |

## What's Needed

- [ ] Implement 6 remaining detection functions
- [ ] Wire standards compliance into detection
- [ ] Contribution avoidance detection (requires contribution flow first)
- [ ] Synergy bypass detection (requires contribution flow first)
