---
title: "OpenFleet doctor.py Rules Mapped to Agent Failure Taxonomy"
type: concept
domain: architecture
status: synthesized
confidence: high
maturity: seed
created: 2026-04-18
updated: 2026-04-18
tags: [doctor, immune-system, agent-failure-taxonomy, coverage, gaps, openfleet, detection]
sources:
  - id: openfleet-doctor
    type: documentation
    file: fleet/core/doctor.py
    title: "OpenFleet doctor.py (679 lines, 10 detection functions + intervention decisions)"
  - id: brain-taxonomy
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/lessons/03_validated/enforcement-compliance/agent-failure-taxonomy-seven-classes-of-behavioral-failure.md
    title: "Agent Failure Taxonomy — Seven Classes of Behavioral Failure"
  - id: brain-three-lines
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/patterns
    title: "Three Lines of Defense — Immune System for Agent Quality"
---

# OpenFleet doctor.py Rules Mapped to Agent Failure Taxonomy

## Summary

OpenFleet's `fleet/core/doctor.py` (679 lines) implements 10 detection functions — the Line 2 detection layer of the three-lines-of-defense immune-system pattern. The brain's agent-failure-taxonomy defines 8 behavioral failure classes observed across OpenArms production runs (clean-completion rate 20%: 4 of 5 runs needed manual fixes). This page cross-references the two: which taxonomy classes our doctor DETECTS, which classes it MISSES, and which of our rules are NOVEL to OpenFleet (not yet represented in the brain taxonomy). Direct adherence to brain's "Three Lines of Defense" pattern at the instance-mapping layer.

## Key Insights

1. **Our doctor covers 2-3 of the 8 taxonomy classes directly.** The remaining 5-6 classes are largely uncovered at the doctor level — they require different mitigation mechanisms (budget caps, pre-flight gates, dispatch-time generation, policy rules).

2. **OpenFleet has 5 NOVEL detection rules that the brain taxonomy doesn't explicitly name.** These are candidate contributions to the brain: detect_correction_threshold, detect_code_without_reading, detect_cascading_fix, detect_abstraction, detect_not_listening.

3. **The fleet-scale context surfaces failure patterns solo agents don't produce.** detect_not_listening (PO interaction) and detect_correction_threshold (multi-iteration rework) are natural fleet concerns. A solo agent doesn't have enough interaction surface area to exhibit them.

4. **Line-2 detection is the natural home for behavioral signals, but some classes need Line-1 prevention or Line-3 correction.** Class 4 fatigue (prevent via budget cap, Line 1) and Class 5 sub-agent non-compliance (correct via trustless verification, Line 3) can't be addressed by Line-2 doctor rules alone.

5. **Infrastructure-vs-behavior split applies to our rules too.** detect_protocol_violation (tool-call-level check) is actually Line-1 INFRASTRUCTURE disguised as Line-2 detection — it's machine-checkable. The 9 other rules are genuine Line-2 BEHAVIORAL checks needing judgment heuristics.

## Deep Analysis

### Coverage Map — 8 Taxonomy Classes × 10 Doctor Rules

| # | Brain Class | OpenFleet Rule(s) | Coverage |
|---|-------------|-------------------|----------|
| 1 | **Artifact pollution** (reverted files stay in artifacts list) | — | ❌ NOT COVERED. Need artifact-path-filter at commit time, not doctor-level detection. Brain-recommended fix: Option B (filter in `commitAndAdvance` against existing-files.json). |
| 2 | **Weakest-checker optimization** (code shaped by target checker) | — | ❌ NOT COVERED. Need gate-strictness policy (ALL gates always run), not detection. Brain-recommended fix: Option 1 (all gates mandatory per stage). |
| 3 | **Environment patching without escalation** (polyfill chains, $12-15 overhead) | `detect_cascading_fix` (partial), `detect_stuck` (partial) | ⚠️ PARTIAL. Our cascading_fix catches fix-on-fix pattern but isn't environment-specific. Brain fix is Line-1 pre-flight + retry cap, not Line-2. |
| 4 | **Fatigue cliff** (quality drops at tasks 4-5) | — | ❌ NOT COVERED at doctor level. Brain fix is budget cap + methodology re-read every 3 tasks. OpenFleet orchestrator controls task flow, so this is orchestrator-layer concern, not doctor-layer. |
| 5 | **Sub-agent non-compliance** (~67% violation even with rules in prompt) | — | ❌ NOT COVERED. Brain fix is Option 3 trustless verification of sub-agent OUTPUT. Doctor watches main-agent behavior; sub-agent output verification would need a different hook. |
| 6 | **Silent conflict resolution** (agent accommodates instead of escalating) | `detect_compression` (direct), `detect_not_listening` (partial) | ✅ COVERED. detect_compression catches vision-shrinking; detect_not_listening catches response-before-processing. Brain's richer fix (dispatch-time Done When generation) is complementary. |
| 7 | **Memory/Wiki conflation** (knowledge in Claude memory not wiki) | — | ❌ NOT COVERED. Brain fix is a behavioral rule, not infrastructure: "if anyone beyond current session needs to read it → wiki." |
| 8 | **Clean-win scope expansion** (clean-but-unauthorized refactor) | `detect_scope_creep` | ✅ COVERED. Our scope_creep rule targets files-outside-plan, which captures Class-A refactor. Classes B (internal design of new files) and C (additive re-exports) may slip through — need design-implementation drift detection for full coverage. |

### Novel OpenFleet Rules (Not Explicitly Named in Brain's 8 Classes)

OpenFleet's doctor has 5 detection rules that don't map cleanly to brain's 8 classes. They may be fleet-scale-specific patterns, or they may be gaps in brain's taxonomy that our observations could fill:

| Rule | Signal | Why It Matters | Candidate for Brain Taxonomy? |
|------|--------|----------------|------------------------------|
| `detect_correction_threshold` | Agent corrected too many times on same task | Multi-iteration rework without root-cause fix. Different from Class 3 environment patching — this is any cause, not just env. | Yes — "correction-loop without root-cause" could be Class 9. Fleet-specific because fleet-ops reviews multiple iterations. |
| `detect_code_without_reading` | Produced code without reading existing code first | Fleet-scale: agents inherit a large codebase. Not reading before writing produces drift. This overlaps brain's "Never Synthesize from Descriptions Alone" lesson but at a different operational layer. | Yes — could be promoted to a behavioral class. |
| `detect_cascading_fix` | Fix-on-fix chain | Partial overlap with Class 3 env patching, but cascading_fix is general — any fix-on-fix. Broader class. | Merge candidate — extend Class 3 to general cascading-fix, not just env-specific. |
| `detect_abstraction` | Replaced literal requirements with abstractions | "Hardcoded instances fail" in reverse — agent abstracts too early. Fleet-scale: specialist agents prefer their abstractions. | Yes — mirror of "hardcoded instances fail" lesson but for premature abstraction. |
| `detect_not_listening` | Produces output instead of processing input | PO interaction-specific. Solo agents have tighter operator feedback loops; fleet agents interact asynchronously and may skip input processing. | Maybe — fleet-specific may not generalize to solo. |

### Our Infrastructure-Layer Rule Hiding in Line 2

`detect_protocol_violation` is listed as a doctor (Line 2) rule but is actually an INFRASTRUCTURE (Line 1) check — it's mechanically determinable whether a tool call was allowed for the agent's current stage (the `tools_blocked` check from `methodology.yaml`). Per brain's Infrastructure > Instructions principle, this should live in the MCP-server tool-blocking layer, not in reactive detection. It's currently in doctor as a detection-layer fallback when MCP blocking is bypassed or when async detection is needed — legitimate but conceptually Line 1.

### Gaps Relative to Brain's Line-2 Detection Requirements

Brain's three-lines-of-defense pattern specifies 4 detection functions running every 30s. Our doctor runs 10 detection functions on agent events. The overlap is partial:

| Brain's Line-2 Detection Dimension | OpenFleet Coverage |
|-----------------------------------|-------------------|
| Protocol violation | ✅ detect_protocol_violation |
| Stage boundary drift | ✅ detect_scope_creep (files) + detect_compression (scope) |
| Contribution gate violation | ❌ (would need separate hook) |
| Quality signal degradation | ⚠️ detect_laziness (partial — rough time-vs-points heuristic) |

Not covered: contribution-gate violations (agent advances without consuming required contribution), quality-trend degradation across multi-task sequences (fatigue-cliff indicator).

### Implications for Our Immune System Evolution

**Quick wins (Line 1 additions):**
- Artifact-path-filter at commit time (closes Class 1) — small PR, high impact
- Gate-strictness policy: all gates always for src-touching stages (closes Class 2)
- Pre-flight environment validation before agent run starts (closes Class 3 at prevention layer)

**Line 2 additions:**
- Contribution-gate-violation detector (agent advances without consuming contributions)
- Quality-trend detector over multi-task windows (fatigue-cliff early warning)

**Line 3 additions:**
- Trustless sub-agent output verification (closes Class 5)
- Design-implementation drift detector (closes Class 8 classes B and C)

**Policy / behavioral:**
- Memory-vs-wiki routing rule for class 7 (advisory enforcement; not infrastructure-enforceable without runtime-memory access which we don't have)

### Relationship to Brain's Three Lines of Defense Pattern

Our doctor.py is Line 2. Line 1 (prevention) lives in `fleet/mcp/tools.py` (tool blocking per stage). Line 3 (correction) lives in the orchestrator's intervention logic (`decide_response`, `build_intervention` in doctor.py lines 436-475). The pattern is present but not complete — the gaps above are opportunities for each line.

## Open Questions

> [!question] Should `detect_protocol_violation` move from Line 2 to Line 1?
> Mechanically checkable → infrastructure principle says this should prevent at tool-call level, not detect after. The MCP tool-blocking already does this; the doctor rule may be redundant with defense-in-depth value. Requires checking whether both fire in practice or whether one silently shadows the other.

> [!question] Are our 5 novel rules worth contributing to brain taxonomy?
> detect_correction_threshold, detect_code_without_reading, detect_cascading_fix (general form), detect_abstraction, detect_not_listening. Each needs ≥3 independent evidence items (brain's lesson-page-standard) to promote. OpenFleet has operational data for some; we'd need to audit our agent run logs for evidence.

> [!question] What's the right Line-1/Line-2/Line-3 split for Class 4 (fatigue cliff)?
> Brain recommends budget cap (Line 1). We could add quality-trend detection (Line 2) as early warning. Line 3 correction would be forced session-end. Likely a layered approach, not single-line.

## Relationships

- BUILDS ON: [[Agent Failure Taxonomy — Seven Classes of Behavioral Failure]] (brain's 8-class taxonomy)
- BUILDS ON: brain's Three Lines of Defense pattern
- IMPLEMENTS: `fleet/core/doctor.py` (the 10 detection functions being mapped)
- FEEDS INTO: [[Brain Evolution]] (doctor is a brain-layer component; gaps become epics)
- FEEDS INTO: [[Chain/Bus Architecture]] (detector outputs are events; they flow through chains)
- RELATES TO: [[Methodology Models Rationale]] (detection rules reference model stages and protocols)
- RELATES TO: [[Operational Depth Gaps — What Structural Compliance Doesn't Measure]] (the gaps listed here are candidates for that register)
- RELATES TO: [[Verify Before Contributing to External Knowledge Systems]] (detect_code_without_reading shares its DNA)
- CONSTRAINS: any new immune-system rules — must declare Line-1/2/3 and map to taxonomy class
