---
title: "Navigator Intent-Map Gap Analysis"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, E014, navigator, intent-map, autocomplete, knowledge-map, gaps]
sources:
  - id: intent-map
    type: documentation
    file: docs/knowledge-map/intent-map.yaml
  - id: methodology
    type: documentation
    file: config/methodology.yaml
  - id: agent-tooling
    type: documentation
    file: config/agent-tooling.yaml
epic: [E001, E014]
phase: "0 — Research"
---

# Navigator Intent-Map Gap Analysis

## Summary

Gap analysis of Navigator's current intent map. Measures coverage (33 intents across 10 roles = 41% of the theoretical 80-intent matrix), identifies the 19 missing intents, and names the operational modes where role×mode cells produce empty or wrong context for fleet agents.

## Current State

33 intents defined in intent-map.yaml across 10 roles. Coverage: **41%** of theoretical maximum (80 = 10 roles × 8 modes).

But not all intents are needed. Some roles don't traverse all stages. Some stages are so brief they don't need Navigator enrichment.

## Required vs Defined Per Role

### Drivers (PM, Fleet-Ops)

**Project Manager** — the conductor. PM goes through stages on their OWN tasks (epic breakdown, sprint planning) but primarily manages OTHER agents' stages.

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | YES | YES | PM talks to PO to understand requirements |
| analysis | LOW | NO | PM rarely does deep analysis — usually delegates |
| investigation | LOW | NO | PM rarely researches — usually delegates |
| reasoning | YES | YES | PM plans epics, sprints, assigns work |
| work | YES | YES | PM creates tasks, manages sprint, bridges Plane |
| heartbeat | YES | YES | PM monitors fleet state, unassigned tasks |

**Needed intents: 4.** Have 4. **PM is complete** for practical purposes.

**Fleet-Ops** — the quality guardian. Fleet-ops doesn't go through methodology stages on own tasks. Primary mode is REVIEW.

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| review | YES — PRIMARY | YES | 7-step real review — core job |
| heartbeat | YES | YES | Monitor pending approvals, board health |
| work | LOW | NO | Rarely — fleet-ops occasionally has infrastructure tasks |

**Needed intents: 2.** Have 2. **Fleet-ops is complete.**

### Contributors (Architect, DevSecOps, QA, Writer, UX)

These agents primarily contribute to other agents' tasks. They have their OWN methodology stages when assigned direct tasks, PLUS a contribution mode.

**Architect**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | MEDIUM | NO | Architect clarifies design requirements with PO |
| analysis | YES | YES | Examine codebase for design |
| investigation | YES | YES | Research options (minimum 3) |
| reasoning | YES | YES | Produce plan, design decisions |
| work | LOW | NO | Architect rarely implements — usually transfers |
| contribution | YES — PRIMARY | YES | design_input contributions to other agents |
| heartbeat | YES | NO | Needs: tasks needing design, complexity flags |

**Needed: 6.** Have 4. **Missing: heartbeat, conversation.**

**DevSecOps — Cyberpunk-Zero**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | LOW | NO | Security tasks rarely need PO conversation |
| analysis | YES | NO | Examine code/infra for vulnerabilities |
| investigation | YES | YES | Research CVEs, threat patterns |
| reasoning | YES | NO | Plan security fixes, threat model |
| work | YES | NO | Implement security fixes, patches |
| contribution | YES — PRIMARY | YES | security_requirement contributions |
| review | YES | YES | PR security review |
| heartbeat | YES | NO | Needs: security alerts, PRs to review |

**Needed: 7.** Have 3. **Missing: analysis, reasoning, work, heartbeat.** Significant gap — devsecops has one of the broadest action profiles.

**QA Engineer**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | LOW | NO | QA tasks rarely need PO conversation |
| analysis | MEDIUM | NO | Analyze test coverage gaps |
| investigation | LOW | NO | QA rarely researches |
| reasoning | MEDIUM | NO | Plan test approach |
| work | YES | YES | Write tests |
| contribution | YES — PRIMARY | YES | qa_test_definition (TC-XXX) |
| review | YES | YES | Validate against predefined criteria |
| heartbeat | YES | NO | Needs: contribution tasks, review tasks |

**Needed: 5.** Have 3. **Missing: heartbeat, analysis.**

**Technical Writer**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | LOW | NO | Doc tasks rarely need PO conversation |
| analysis | MEDIUM | NO | Analyze existing docs for gaps |
| reasoning | MEDIUM | NO | Plan doc structure |
| work | YES | YES | Write documentation |
| contribution | YES | YES | documentation_outline |
| heartbeat | YES | NO | Needs: completed features without docs, stale pages |
| heartbeat-autonomous | YES | YES | Proactive page maintenance when Plane connected |

**Needed: 4.** Have 3. **Missing: heartbeat.**

**UX Designer**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | MEDIUM | NO | Discuss UX requirements with PO |
| analysis | MEDIUM | NO | Analyze existing UX for gaps |
| reasoning | YES | YES | Design component specs |
| work | LOW | NO | UX rarely implements directly |
| contribution | YES — PRIMARY | YES | ux_spec contributions |
| heartbeat | YES | NO | Needs: contribution tasks, UX review tasks |

**Needed: 4.** Have 2. **Missing: heartbeat, analysis.**

**Accountability Generator**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | LOW | NO | Compliance tasks rarely need PO conversation |
| analysis | YES | YES | Analyze trails, verify compliance |
| reasoning | MEDIUM | NO | Plan compliance report structure |
| work | MEDIUM | NO | Produce compliance reports |
| heartbeat | YES | YES | Check completed tasks for trail completeness |

**Needed: 3.** Have 2. **Missing: work (for producing reports).**

### Workers (Engineer, DevOps)

These agents do their work through full methodology stages.

**Software Engineer**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | YES | NO | Clarify requirements with PO |
| analysis | YES | NO | Examine codebase |
| investigation | MEDIUM | NO | Research approaches |
| reasoning | YES | YES | Plan implementation |
| work | YES — PRIMARY | YES | Implement + commit + complete |
| heartbeat | YES | NO | Needs: assigned tasks, stage, contributions |

**Needed: 5.** Have 2. **Missing: conversation, analysis, heartbeat.** Engineer is the most active agent but has the least intent coverage proportionally.

**DevOps**

| Mode | Required? | Defined? | Why |
|------|-----------|----------|-----|
| conversation | MEDIUM | NO | Discuss infra requirements |
| analysis | YES | NO | Analyze current infrastructure |
| investigation | MEDIUM | NO | Research infra options |
| reasoning | YES | NO | Plan IaC changes |
| work | YES — PRIMARY | YES | Implement IaC |
| contribution | YES | NO | deployment_manifest contributions |
| heartbeat | YES | NO | Needs: infra tasks, health alerts |

**Needed: 5.** Have 1. **Missing: reasoning, contribution, heartbeat, analysis.** DevOps has the worst coverage.

## Priority-Ranked Intent Gaps

| Priority | Intent | Why Critical |
|----------|--------|-------------|
| **P1** | engineer-heartbeat | Most active agent has no heartbeat intent |
| **P1** | engineer-conversation | Engineer needs to clarify requirements |
| **P1** | engineer-analysis | Engineer needs to examine codebase |
| **P1** | devsecops-heartbeat | Security agent needs to see alerts, PRs |
| **P1** | devsecops-work | Security agent needs to implement fixes |
| **P1** | devops-heartbeat | Infra agent needs to see health alerts |
| **P1** | devops-reasoning | Infra agent needs to plan IaC |
| **P1** | devops-contribution | DevOps provides deployment_manifest |
| **P2** | architect-heartbeat | Design agent needs to see design request tasks |
| **P2** | qa-heartbeat | QA needs to see contribution and review tasks |
| **P2** | writer-heartbeat | Writer needs to see completed features needing docs |
| **P2** | ux-heartbeat | UX needs to see contribution tasks |
| **P2** | devsecops-analysis | Security analysis (vulnerability assessment) |
| **P2** | devsecops-reasoning | Security fix planning |
| **P2** | devops-analysis | Infrastructure assessment |
| **P3** | accountability-work | Produce compliance reports |
| **P3** | architect-conversation | Clarify design requirements |
| **P3** | engineer-investigation | Research approaches |
| **P3** | ux-analysis | Analyze existing UX |

**Total gaps: 19 intents (P1: 8, P2: 7, P3: 4)**

## Pack Skills Missing From All Intents

Current intents reference fleet-* skills, Anthropic marketplace skills, and a few superpowers skills. Missing entirely:

| Pack | Skills That Should Appear | In Which Intents |
|------|--------------------------|-----------------|
| **superpowers** | brainstorming (all conversation/analysis), TDD (all work), systematic-debugging (all analysis/investigation), verification-before-completion (all work), subagent-driven-development (engineer/QA work), writing-plans (all reasoning) | Every intent for applicable stages |
| **ring dev-team** | dev-implementation, dev-unit-testing, dev-refactor | engineer-work, devops-work |
| **ring pm-team** | pre-dev-task-breakdown, pre-dev-delivery-planning | pm-reasoning, pm-work |
| **ring tw-team** | writing-api-docs, documentation-structure | writer-work |
| **ring default** | code-reviewer, security-reviewer, test-reviewer | fleet-ops-review, qa-review |
| **trailofbits** | openai-security-threat-model, security-awareness | devsecops-investigation, devsecops-contribution |
| **NeoLabHQ** | ddd, sadd, sdd | architect-reasoning |
| **borghei compliance** | soc2-compliance-expert, nist-csf-specialist | accountability-analysis |

## Sub-Agent Recommendations Missing From All Intents

No intent currently includes sub-agent recommendations. Each role has assigned sub-agents (from agent-tooling.yaml) that should appear at the right moment:

| Role | Sub-Agents | Which Intents |
|------|-----------|---------------|
| engineer | test-runner, code-explorer | engineer-work, engineer-analysis |
| architect | pattern-analyzer, dependency-mapper, code-explorer | architect-analysis, architect-investigation |
| QA | test-runner, regression-checker, coverage-analyzer | qa-work, qa-review |
| devops | container-inspector | devops-work, devops-analysis |
| devsecops | dependency-scanner, secret-detector, security-auditor | devsecops-investigation, devsecops-review |
| fleet-ops | trail-reconstructor | fleet-ops-review |
| PM | sprint-analyzer | pm-heartbeat |

## What Filling These Gaps Means

Filling the 19 missing intents + adding pack skills + adding sub-agents to existing intents = the Navigator can deliver stage-appropriate recommendations for ALL roles at ALL stages they actually use. This is what allows TOOLS.md to stay focused — the Navigator handles the "what skills/sub-agents should I consider right now" question.

Without these intents, agents in certain stages get NO Navigator enrichment, which means:
- Engineer in analysis stage gets nothing from knowledge-context.md
- DevOps in reasoning stage gets nothing
- Every heartbeat for 7/10 agents gets nothing from Navigator

The TOOLS.md redesign assumes Navigator delivery works. These gaps must be filled for that assumption to hold.

## Implementation

This work belongs to E001 Phase 2 (Scaffold) and E014 (Autocomplete Web). The intent-map.yaml updates should:

1. Create the 19 missing intents following the existing format
2. Add pack skills to ALL intents (existing + new) where applicable
3. Add sub-agent recommendations to work/analysis/review intents
4. Verify each intent's content against the agent-ecosystem-allocation.md per-role tables
5. Test with Navigator.assemble() for all role×stage combinations

## Relationships

- FEEDS_INTO: E001 (TOOLS.md redesign depends on Navigator coverage)
- PART_OF: E014 (Autocomplete Web — intent-map IS the web's routing table)
- RELATES_TO: E007 (Ecosystem — pack skills feed into intents)
- RELATES_TO: E003 (Brain Evolution — orchestrator drives Navigator refresh)
