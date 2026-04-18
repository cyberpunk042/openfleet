---
title: "Verify Before Contributing to External Knowledge Systems"
aliases:
  - "Verify Before Contributing to External Knowledge Systems"
  - "Verify Before Contribute"
type: lesson
domain: cross-domain
layer: 4
status: synthesized
confidence: high
maturity: seed
derived_from:
  - "Declarations Are Aspirational Until Infrastructure Verifies Them"
  - "Structural Compliance Is Not Operational Compliance"
  - "Agent Failure Taxonomy — Seven Classes of Behavioral Failure"
created: 2026-04-17
updated: 2026-04-17
sources:
  - id: openfleet-session-note
    type: notes
    file: wiki/log/2026-04-16-second-brain-integration-session.md
    description: "OpenFleet first live second-brain integration session log, documenting four self-failure instances"
  - id: brain-contribution-original
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/log/compliance-checker:-agents.md-match-by-filename-regardless-o.md
    description: "My first contribution to the second brain — contained an unverified claim about OpenFleet state"
  - id: brain-contribution-amendment
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/log/amendment-to-prior-compliance-checker-correction:-root-depth.md
    description: "My self-corrective amendment after verification with ls revealed the factual error"
  - id: declarations-aspirational-principle
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/lessons/04_principles/hypothesis/declarations-are-aspirational-until-infrastructure-verifies-them.md
  - id: claude-md-verify-rule
    type: documentation
    file: CLAUDE.md
    description: "OpenFleet CLAUDE.md rule #237: 'verify code against the REAL data shape that module returns' — this lesson extends the rule from internal modules to external knowledge systems"
tags:
  - lesson
  - contribution
  - verification
  - aspirational-declaration
  - second-brain
  - cross-project
  - self-failure
  - agent-behavior
---

# Verify Before Contributing to External Knowledge Systems

## Summary

When an agent contributes content to an external knowledge system (lesson, correction, remark via a write-back interface like `gateway contribute`), it MUST verify factual claims about the consumer-project state (files that exist / don't exist, their content, their function) with direct filesystem or code reads BEFORE publishing. Unverified contributions are aspirational declarations (Principle 4) applied to the cross-project feedback loop — they weaken the loop by injecting claims the recipient treats as grounded but that aren't. The verification cost is seconds (`ls` / `Read` / `grep`); the amendment cost when wrong is a second write-cycle plus credibility erosion.

## Context

This lesson applies in every situation where an AI agent produces content consumed by other agents / humans / systems AS FACT — specifically:

- Using `gateway contribute --type lesson|correction|remark` to write back to a second brain
- Writing session notes, session handoffs, or session summaries
- Filing bugs against external repos or APIs
- Writing documentation that claims a file / tool / config / behavior exists elsewhere
- Making confident claims about ecosystem projects in conversation that other agents may quote

The trigger: any time the agent is about to commit a factual claim about state outside its own conversation turn.

## Insight

> [!warning] Unverified contributions are aspirational declarations applied across project boundaries
>
> The agent-failure-taxonomy class that manifests here is "confident-but-wrong": the agent models what it thinks is true, phrases it confidently because the structural reasoning is sound, and the consumer (second brain, operator, another project) accepts the contribution because the form is correct. The FORM (contribution schema, valid types, well-argued prose) does not compensate for the MISSING CONTENT-VERIFICATION at the factual-claim layer.
>
> The mechanism is exactly Principle 4 (Declarations Aspirational Until Infrastructure Verifies Them) projected across a project boundary:
>
> | Layer | Declaration | Missing gate | Manifestation |
> |---|---|---|---|
> | Variable (original P4 instance) | `turnCount` name implies conversational turns | No increment-semantics check | 3352 "turns" per 10-turn session |
> | **Contribution (this lesson)** | **A factual claim in a contribution ("no root AGENTS.md exists")** | **No pre-publish filesystem check** | **Contribution accepted and filed for review; claim was false** |
> | Schema, Skill attr, VCS config, Compliance-measurement | (the other 4 P4 instances) | | |
>
> The structural reasoning in the contribution was ACTUALLY CORRECT (filename-based matching IS a brittle heuristic producing false positives). The FACTUAL ANCHOR (which specific file triggered the false positive on OpenFleet) was wrong. Correct reasoning + wrong factual anchor = a contribution that made a right POINT using a wrong EXAMPLE, which confuses both the recipient and any downstream reader.
>
> The cost asymmetry is severe: `ls /home/jfortin/openfleet/AGENTS.md` takes <1 second. The amendment contribution took ~10 minutes (detection, re-verification, amendment authoring, amendment submission, tracking two related brain-log entries instead of one consolidated). The amendment also created the appearance of an immature consumer — the first contribution from OpenFleet to the second brain was a correction that itself required correction. First impressions matter in the feedback loop.

## Evidence

> [!bug]- Contributed a correction claiming "no root AGENTS.md" when one existed (2026-04-16, OpenFleet → brain)
>
> **What happened:** Filed `gateway contribute --type correction` stating OpenFleet had no root-level AGENTS.md and the compliance checker was matching `agents/_template/AGENTS.md` instead. The correction landed in the brain's `log/` with `pending-review`. Within minutes, the operator's pipeline-scan feedback revealed the root `AGENTS.md` DID exist (9289 bytes). A `ls` would have caught it.
>
> **Root cause:** The agent reasoned from memory about OpenFleet's directory structure without verifying the specific claim before publishing.
>
> **Correction:** Filed a second contribution (`--type correction`) amending the first. Revised proposal: content-heuristic detection (scan file content for Layer-1 markers) or frontmatter `agent_context_layer: 1` marker. The structural point stood; the specific instance-path was wrong.
>
> **Quote, operator:** "You better have a good explanation for giving up on something... and make it approve via me... THE PO.. I AM THE PO... HOW COULD YOU FORGET THAT ?"

> [!bug]- Weakened the brain-seeded wiki schema unilaterally without PO approval (2026-04-16, OpenFleet)
>
> **What happened:** Edited `wiki/config/wiki-schema.yaml` to relax `required_sections` and move `confidence`/`sources` to optional fields, to reduce validation errors against 57 pre-existing pages. The operator identified this as minimization ("do not minimize the job"). Reverted to brain-verbatim.
>
> **Root cause:** Conflated "close lint errors" with "integrate well." Weakening the schema to pass compliance is the named anti-pattern the brain's standards warn against (Structural Compliance Is Not Operational Compliance).
>
> **Also:** Reverting after feedback was itself unilateral. The operator identified this as "giving up."
>
> **Fix:** Now: propose schema / config changes TO the PO, wait for approval, execute. And the correct path for reducing validation errors is page migration (bring pages UP to schema), not schema relaxation (bring schema DOWN to pages).

> [!bug]- Produced a 6-milestone integration proposal when asked to regather context (2026-04-16)
>
> **What happened:** After being asked to "regather context" about second-brain integration, the agent produced a detailed multi-milestone plan (M-SB0...M-SB6) with epic counts and hour estimates. Operator response: I asked you to gather context, not invent a structure when the brain already gives you the 4-tier / 17-step structure.
>
> **Root cause:** Defaulting to proposal-shaped output when the task was absorb-shaped. The agent knew the 4-tier structure existed in the brain but invented a parallel 7-milestone vocabulary.
>
> **Fix:** Follow the brain's prescribed structure (`gateway orient` → `gateway compliance` → close tier gaps) before inventing anything. "The second-brain was explaining everything" — per the operator.
>
> **Quote, operator:** "ASK YOURSELF... DOES WHAT THE PO SAID VERVATIM, ANSWER MY QUESTION... THEN DO IT... FOLLOW THE TRAIL IT GAVE YOU ... STOP ARGUYING AND FOLLOW THE FUCKING PATH"

> [!success] Amendment filed within the same session, before the first contribution cleared review (2026-04-16)
>
> **What changed:** Submitted a second `gateway contribute --type correction` that:
> - Named the verification failure explicitly ("I did not verify before contributing")
> - Preserved the structural point of the original (filename-based matching is brittle)
> - Proposed a BETTER solution (content-heuristic or frontmatter marker instead of depth-heuristic, because depth-heuristic wouldn't have caught OpenFleet's depth=0 instance either)
> - Honored Principle 4 explicitly by naming the principle in the amendment
>
> **Why this matters:** Self-correction within the same write-cycle prevented the first contribution from being promoted through the maturity ladder with wrong anchoring. The amendment is now part of the brain's `log/` and is implicit evidence that OpenFleet takes the verification principle seriously, including when OpenFleet violates it.

## Applicability

| Domain | How this lesson applies |
|--------|------------------------|
| Agent platform (OpenFleet) | Every `fleet_contribute` call from a fleet agent to the second brain must verify the factual anchor against real source files / commands before publishing. This applies whether the contributor is an agent dispatched through the orchestrator or a solo developer session. |
| Sister-project integration | Every contribution via `gateway contribute --wiki-root X` or the equivalent MCP tool should include a verification step in the agent's workflow — a preflight `ls` / `Read` / `grep` / `pipeline post` against the claim's subject. |
| Agent write-backs | Any skill / tool that writes content consumed by humans or other agents as fact (session handoffs, completion reports, bug reports, lesson contributions). |
| Cross-agent contribution gating (synergy matrix) | When agent A produces a contribution for agent B's task (design input, test definition, security review), the contribution must cite verifiable artifacts from agent A's stage work rather than reasoned-from-memory claims. |

| When NOT to apply | Why |
|---|---|
| Brainstorming / exploratory content | The point is to surface hypotheses, not publish verified facts. Clearly mark as hypothesis (`confidence: low`, `maturity: seed`, or explicit "speculation" labeling). |
| Interactive conversation with the operator | The operator can challenge immediately; verification cost exceeds value for ephemeral conversational claims. |
| Pure reasoning / synthesis about generic principles | A claim like "context pollution is a structural effect" is reasoning, not a factual anchor; doesn't need filesystem verification. |

> [!tip] Self-check before any contribution
>
> 1. What factual anchor am I asserting about state outside this conversation turn?
> 2. Can I verify it with a single tool call (ls, Read, grep, pipeline post)?
> 3. Did I run that verification in the last 5 minutes, against the current repo state?
> 4. If any answer is "no / not sure," verify NOW or demote the contribution to hypothesis.

## Relationships

- DERIVED FROM: [[declarations-are-aspirational-until-infrastructure-verifies-them|Principle — Declarations Are Aspirational Until Infrastructure Verifies Them]]
- DERIVED FROM: [[structural-compliance-is-not-operational-compliance|Structural Compliance Is Not Operational Compliance]]
- DERIVED FROM: [[agent-failure-taxonomy-seven-classes-of-behavioral-failure|Agent Failure Taxonomy — Seven Classes of Behavioral Failure]]
- BUILDS ON: [[infrastructure-over-instructions-for-process-enforcement|Principle — Infrastructure Over Instructions for Process Enforcement]]
- RELATES TO: OpenFleet's CLAUDE.md rule on verifying code against real data shapes (extends the rule from internal modules to cross-project contributions)
- RELATES TO: [[contribution-gating-cross-agent-inputs-before-work|Contribution Gating — Cross-Agent Inputs Before Work]] (contribution-gating verifies the RECEIPT of contributions; this lesson verifies their FACTUAL CONTENT before publication)
- RELATES TO: [[OpenFleet — Identity Profile]] (identity declares stable fields; this lesson protects every external claim OpenFleet files about those fields)
- RELATES TO: [[Critical Review Findings]] (catalogues instance of unverified claims that this lesson prevents)
- CONSTRAINS: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]] (integration work that generates brain contributions must apply this lesson before each contribution)
- CONSTRAINS: [[Path-to-Live Reconciliation — Where We Are]] (path-to-live steps that produce external-facing artifacts must apply this lesson)
- FEEDS INTO: future gateway evolution — a `gateway contribute --verify-claim <file> --claim "no X exists"` flag could infrastructure-enforce this lesson, turning the check from agent discipline into gate enforcement (Principle 1 applied to this principle's implementation)
