---

## Accountability Generator — NNRT Fleet Action Plan

**Date:** 2026-03-26  
**Source data:** NNRT assessment v0.3.0 / IR schema 0.1.0  
**Fleet dependency on NNRT:** claim neutralization, contradiction detection, confidence scoring  

---

### FIRST PRIORITY — Unlock Integration

**Packaging/CI + Milestone 3 Contradiction Detection**

These are coupled. Packaging without contradiction detection delivers infrastructure with no fleet payload. Contradiction detection without packaging cannot be consumed by the fleet at all.

**Packaging/CI actions (unblocks everything):**
- Add `pyproject.toml` with declared dependencies, entry points, and version pin
- Add `pytest` configuration with markers: `unit`, `integration`, `golden`, `stress`
- Add CI pipeline: lint (ruff), type check, unit tests, golden regression — gate on all
- Remove `structured_backup_20260118.py` from repo (it's evidence of drift, not code)
- Enforce: no merge to main without green CI

**Contradiction detection (fleet's highest unmet need):**
- Implement Milestone 3 `p51_detect_contradictions` pass — wired after `p50_policy`
- Inputs: `StatementGroups`, `Timeline`, `PolicyDecisions` from IR
- Output: `ContradictionRecord` list in IR — each entry carries: statement A, statement B, contradiction type (temporal/factual/positional), severity, confidence score
- This is the pass the Accountability Generator chains against for pressure generation

**Standard set:** Every new pass requires a backing spec document before the first line of code. This is NNRT's own governance rule — the fleet holds it to it.

---

### SECOND PRIORITY — Make the Output Trustworthy

**Test quality + Doc-to-code traceability**

NNRT self-rates at 7/10 for trustworthy neutral output. The fleet cannot build accountability products on a system with unmeasured confidence. Before contradiction detection output is surfaced in any report, its reliability must be characterizable.

**Test quality actions:**
- Add `pytest-cov` and establish a coverage baseline per module — publish the number, don't hide it
- Tag all 509 existing tests with markers (`unit`/`integration`/`golden`) — no test lives without a category
- Add a `make test-smoke` target (unit + golden, < 60 seconds) — this is what CI runs on every commit
- Add a `make test-full` target — full suite including stress — runs on schedule or pre-release only
- For every new pass added in Priority 1, coverage must not decrease

**Doc-to-code traceability actions:**
- Audit: for each of the undocumented passes (p33, p35, p36, p38, p43, p44a-d, p46, p48, p55, p72, p75, p90) and the `selection/`, `domain/`, `v6/` packages — either find the backing doc or write it
- Produce a gap report: `docs/governance/traceability-audit-2026-03-26.md` — this is the deliverable
- Governance rule encoded as CI check: if a new pass file is added with no corresponding doc entry, CI fails

**Standard set:** Coverage numbers are public, not aspirational. A pass with no backing doc is a governance violation, not a debt item.

---

### THIRD PRIORITY — Reduce Surface Before Expanding It

**Render layer consolidation + Second domain profile**

These are sequenced, not parallel. Consolidate before adding another domain, or the duplication compounds.

**Render layer consolidation actions:**
- Map ownership: `nnrt/render/` vs `nnrt/output/` — one owns the IR-to-text boundary, one owns the structured schema boundary — make the split explicit in code and docs
- Delete or absorb: `render/structured_v2.py`, `render/constrained.py`, `render/event_generator.py`, `render/template.py` — each must either be promoted to canonical or removed with a documented decision
- The six timeline files: `p44_timeline.py` and the `p44a-d` decomposed variants — keep one, archive the rest with a note in `docs/governance/`
- Resolve the `validate/` vs `validation/` package duality — one survives, the other is removed

**Second domain profile (after consolidation):**
- Choose a domain that breaks the law enforcement assumptions: medical or workplace
- This is a stress test of the domain abstraction, not a feature for its own sake
- If the domain system doesn't generalize cleanly, that failure is the finding — document it and fix the abstraction, don't paper over it

**Standard set:** No new domain until render is consolidated. Expanding on a blurred architecture teaches the wrong lessons.

---

### Fleet Contribution Standards

These apply to every fleet agent touching NNRT:

| Standard | Rule |
|---|---|
| **Traceability** | Every pass has a backing spec doc. No doc = no merge. |
| **Determinism contract** | LLMs assist, they do not define. Any LLM-touching code is annotated as such and has a deterministic fallback. |
| **Coverage floor** | No PR reduces coverage. Baseline is public. |
| **Governance audit trail** | The gap report (`docs/governance/traceability-audit-*.md`) is updated on every milestone. |
| **Nothing deleted, only archived** | Removed passes stay in `docs/governance/archived/` with a dated decision record. |
| **Contradiction output is confidence-stamped** | Every `ContradictionRecord` carries a `confidence` field. The fleet does not surface low-confidence contradictions without explicit override and audit log. |

---

### Governance That Must Be Respected

**From NNRT's own governance doc:**
> "Code must reference the document that justified its existence. If code cannot be explained by a document, it does not belong."

The fleet enforces this, not just NNRT itself. CI is the enforcement mechanism.

**From OCF:**
- Mission Control logs all activity — NNRT transformation runs are loggable events, not opaque calls
- `approval_required: true` on this agent — contradiction detection output that influences a public report requires human review before publish
- User is always in control — confidence thresholds and neutralization profiles are user-configurable, not fleet-decided

**The neutrality invariant (non-negotiable):**  
NNRT's output is only as trustworthy as the policy rules are auditable. The fleet does not treat NNRT output as ground truth. It treats it as structured, inspectable input that an analyst can trace back to source. The Accountability Generator's job is to make that chain of custody visible, not to hide it behind a score.

---

**Summary:**

```
FIRST:   Packaging/CI + Contradiction Detection   → fleet can integrate and detect
SECOND:  Test quality + Doc traceability           → fleet can trust what it integrates
THIRD:   Render consolidation + Second domain      → fleet can expand without compounding debt
```