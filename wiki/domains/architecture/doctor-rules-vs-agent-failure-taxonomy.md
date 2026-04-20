---
title: "OpenFleet doctor.py Rules Mapped to Agent Failure Taxonomy"
type: concept
domain: architecture
status: synthesized
confidence: high
maturity: seed
created: 2026-04-18
updated: 2026-04-20
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

2. **OpenFleet has 5 candidate detection rules vs brain's taxonomy — 4 genuinely novel + 1 overlap** (refined 2026-04-19 after full absorption of brain's [three-lines-of-defense pattern](../../../../devops-solutions-research-wiki/wiki/patterns/03_validated/enforcement/three-lines-of-defense-immune-system-for-agent-quality.md)). **`detect_correction_threshold` overlaps** — brain's Line 2 detection explicitly lists `detect_correction_threshold()` as one of its 4 existing functions. Our contribution to brain for this rule is the fleet-scale reviewer-feedback-count angle, not the rule itself. **Genuinely novel contributions**: detect_code_without_reading, detect_cascading_fix (generalization), detect_abstraction, detect_not_listening.

3. **The fleet-scale context surfaces failure patterns solo agents don't produce.** detect_not_listening (PO interaction) and detect_correction_threshold (multi-iteration rework) are natural fleet concerns. A solo agent doesn't have enough interaction surface area to exhibit them.

4. **Line-2 detection is the natural home for behavioral signals, but some classes need Line-1 prevention or Line-3 correction.** Class 4 fatigue (prevent via budget cap, Line 1) and Class 5 sub-agent non-compliance (correct via trustless verification, Line 3) can't be addressed by Line-2 doctor rules alone.

5. **Infrastructure-vs-behavior split applies to our rules too.** detect_protocol_violation (tool-call-level check) is actually Line-1 INFRASTRUCTURE disguised as Line-2 detection — it's machine-checkable. The 9 other rules are genuine Line-2 BEHAVIORAL checks needing judgment heuristics.

6. **Brain 2026-04-19 validates the pattern generalizes across failure domains.** Brain's [[model-quality-failure-prevention|Model — Quality & Failure Prevention]] now tabulates OpenFleet's agent-behavior three-lines against AICP's inference-backend three-lines (per-backend circuit breakers / failover chain / DLQ with retry budget). Cross-scope comparison: Line-1 Prevention = stage-gated tools (ours) ↔ circuit breakers (AICP); Line-2 Detection = doctor.py 30s/10 rules (ours) ↔ failover auto-escalation (AICP); Line-3 Correction = PRUNE/ESCALATE/quarantine (ours) ↔ DLQ persistence (AICP). This is the first ecosystem evidence that three-lines is a domain-agnostic pattern, not an agent-behavior-specific one — our 746-line implementation is explicitly cited alongside AICP's 467-line stack.

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

### Candidate OpenFleet Rules vs Brain's 8 Classes

OpenFleet's doctor has 5 candidate detection rules. **Refined 2026-04-19**: 1 overlaps with brain's existing Line-2 detection (`detect_correction_threshold`); 4 are genuinely novel. They may be fleet-scale-specific patterns, or they may be gaps in brain's taxonomy that our observations could fill:

| Rule | Signal | Why It Matters | Candidate for Brain Taxonomy? |
|------|--------|----------------|------------------------------|
| `detect_correction_threshold` | Agent corrected too many times on same task | Multi-iteration rework without root-cause fix. Different from Class 3 environment patching — this is any cause, not just env. | **Overlap** — brain's [three-lines-of-defense pattern](../../../../devops-solutions-research-wiki/wiki/patterns/03_validated/enforcement/three-lines-of-defense-immune-system-for-agent-quality.md) already lists `detect_correction_threshold()` as one of 4 Line-2 functions. Our contribution is the fleet-scale angle (reviewer-feedback-count, not agent self-repetition) — would be a refinement of existing, not a new Class 9. |
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

### Alternative Lens — Our Rules vs Brain's 5 Named Diseases

Brain's `three-lines-of-defense` pattern names 5 diseases as Line-2 detection targets (complementary lens to the 8-class taxonomy above — diseases are detection categories, classes are failure modes across all lines):

| Brain Disease | Our Rule | Match |
|---------------|----------|-------|
| **Deviation** (output doesn't match verbatim requirement) | `detect_compression` (partial) | ⚠️ partial — compression catches vision-shrinking, not general deviation from verbatim |
| **Laziness** (partial criteria coverage) | `detect_laziness` | ✅ direct |
| **Protocol violation** (wrong tool at wrong stage) | `detect_protocol_violation` | ✅ direct (though conceptually Line-1 per above) |
| **Confident-but-wrong** (same mistake 3+ times) | `detect_correction_threshold` | ✅ direct |
| **Scope creep** (features not in requirement) | `detect_scope_creep` | ✅ direct |

**4 of 5 brain-named diseases covered directly**; Deviation is partial. Consider strengthening `detect_compression` or adding a `detect_deviation` rule that compares output against verbatim-requirement anchors.

Brain also lists Line-2 "behavioral security scanning: credential exfiltration, DB destruction, security disabling, supply chain attacks." Ours has `signal_rejection` but no standalone security scanner rules — this is likely covered elsewhere in the fleet (devsecops agent skills + MCP tool policy), not doctor-level. Worth verifying the location.

### Third Lens — Our Rules vs Brain's 5 Doctor Categories

Brain's `model-quality-failure-prevention` groups immune-system detection into 5 categories (complementary to the 8-class taxonomy and the 5-named-diseases — categories are *what class of signal does the detector respond to*):

| Brain Category | Signal | Our Rule(s) |
|---|---|---|
| **Liveness** | Agents alive in state but dead in practice (heartbeat timeout, stuck execution) | `detect_stuck` |
| **Loop detection** | Runaway cycles, retry storms, dispatch-without-completion | `detect_cascading_fix`, `detect_correction_threshold` |
| **State integrity** | Impossible state combinations (parent complete but children pending) | Not covered at doctor level — orchestrator state machine handles this |
| **Behavioral security** | Permission and scope violations, out-of-scope writes | `detect_protocol_violation` (tool-call-level), `detect_scope_creep` (file-level) |
| **Resource exhaustion** | Degraded conditions (circuit breaker open, memory pressure, cost spikes) | Not covered at doctor level — budget monitor + storm graduation handle this |

Coverage: 3 of 5 brain categories represented in doctor.py. State integrity and resource exhaustion live outside doctor (orchestrator state machine, budget monitor). Our detectors for semantic-quality signals (laziness, compression, code-without-reading, abstraction, not-listening) don't fit neatly into any of the 5 categories — they're a **6th category candidate**: *semantic quality* — not about liveness/loops/state/security/resources, but about the QUALITY of the agent's output.

### 3-Strike Pattern

Brain's three-lines-of-defense pattern notes a 3-strike tolerance: "One violation doesn't trigger action. Three violations within a window trigger quarantine. This tolerates transient anomalies while catching persistent failures." Our `detect_correction_threshold` rule codifies this at the correction-count layer (3+ corrections on same task → intervention). Worth auditing whether our other detectors use the same 3-strike pattern or fire on single violations — inconsistent tolerance thresholds create uneven enforcement.

### Orchestrator Position

Brain documents OpenFleet's doctor as running at **step 6 of a 12-step orchestrator cycle** — after security scan, before dispatch, described as preemptive-immune-response position (detection BEFORE dispatch, so flagged tasks accumulate strikes before being assigned).

Verified 2026-04-18 against `fleet/cli/orchestrator.py`: `_run_doctor` is called from `run_orchestrator_cycle` (line ~395), and line 407's comment confirms "respects doctor report — skips agents flagged by immune system." The doctor → dispatch ordering matches brain's description. The code does NOT explicitly number steps 1-12; brain's "step 6 of 12" is a description of the cycle flow, not an in-code label. Directionally accurate.

### Hidden-from-Agents Principle

Brain pattern: "Immune system is HIDDEN from agents. Agents experience tool blocks, context changes, session restarts — but never see the detection logic. This prevents agents from gaming the enforcement." Our doctor emits events to the orchestrator, which surfaces consequences to agents via interventions (TEACH/COMPACT/PRUNE/ESCALATE) — agents see outcomes, not the detection that produced them. Alignment check: verify no agent-facing logs or context expose the detection rule names or thresholds.

## Open Questions

> [!question] Should `detect_protocol_violation` move from Line 2 to Line 1?
> Mechanically checkable → infrastructure principle says this should prevent at tool-call level, not detect after. The MCP tool-blocking already does this; the doctor rule may be redundant with defense-in-depth value. Requires checking whether both fire in practice or whether one silently shadows the other.

> [!question] Are our 4 novel rules worth contributing to brain taxonomy?
> detect_code_without_reading, detect_cascading_fix (general form), detect_abstraction, detect_not_listening. (`detect_correction_threshold` removed — overlaps with brain's existing Line-2 function per 2026-04-19 absorption of three-lines-of-defense pattern.) Each needs ≥3 independent evidence items (brain's lesson-page-standard) to promote. OpenFleet has operational data for some; we'd need to audit our agent run logs for evidence.

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
