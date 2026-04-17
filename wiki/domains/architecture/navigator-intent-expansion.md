---
title: "Navigator Intent-Map Expansion — 19 Missing Intents + Pack Skills"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, E014, navigator, intent-map, pack-skills, sub-agents, expansion]
sources:
  - id: intent-map
    type: documentation
    file: docs/knowledge-map/intent-map.yaml
  - id: skill-stage-mapping
    type: documentation
    file: config/skill-stage-mapping.yaml
  - id: agent-tooling
    type: documentation
    file: config/agent-tooling.yaml
epic: [E001, E014]
phase: "1 — Design"
---

# Navigator Intent-Map Expansion

## Summary

Scope and proposed expansion for Navigator's intent map — adding the 19 intents identified as missing in the gap analysis, plus new pack-skills wiring. Defines the intent keys, role×mode activation, and which skills/commands/tools each intent should surface when Navigator assembles role context.

## Scope

1. **19 missing intents** identified in navigator-intent-gap-analysis.md
2. **Pack skills** injected into ALL intents (existing 33 + new 19)
3. **Sub-agent recommendations** added to work/analysis/review intents
4. **Result:** Navigator covers all role×stage combinations agents actually use

## P1 Intents (8 — must have for TOOLS.md redesign)

### engineer-heartbeat

```yaml
engineer-heartbeat:
  inject:
    - fleet_state: [work_mode, backend_mode]
    - role_data: [assigned_tasks, artifact_state, contributions_received]
    - directives: all
    - messages: mentions
    - tasks: assigned with stage and readiness
    - sub_agents: [test-runner, code-explorer]
```

### engineer-conversation

```yaml
engineer-conversation:
  inject:
    - agent_manual: engineer
    - methodology: conversation (MUST/MUST NOT)
    - skills: [fleet-communicate, brainstorming]
    - pack_skills: [superpowers:brainstorming]
    - note: "Clarify requirements. Ask specific questions. NO code."
```

### engineer-analysis

```yaml
engineer-analysis:
  inject:
    - agent_manual: engineer
    - methodology: analysis
    - skills: [fleet-code-exploration, fleet-gap]
    - pack_skills: [superpowers:systematic-debugging, superpowers:brainstorming]
    - sub_agents: [code-explorer]
    - tools: [fleet_artifact_create (analysis_document)]
    - mcp: [filesystem, github, context7]
    - note: "Examine codebase. Reference specific files. NO solutions."
```

### devsecops-heartbeat

```yaml
devsecops-heartbeat:
  inject:
    - fleet_state: [work_mode, storm_status]
    - role_data: [security_alerts, prs_needing_review, infra_health]
    - directives: all
    - messages: mentions
    - tasks: assigned
    - sub_agents: [dependency-scanner, secret-detector, security-auditor]
```

### devsecops-work

```yaml
devsecops-work:
  inject:
    - agent_manual: devsecops (full)
    - methodology: work
    - skills: [fleet-incident-response, fleet-secret-scanning, fleet-dependency-audit]
    - pack_skills: [superpowers:systematic-debugging, superpowers:verification-before-completion, superpowers:test-driven-development]
    - trailofbits: [security-awareness, openai-security-best-practices]
    - tools: [fleet_commit, fleet_task_complete, fleet_alert]
    - mcp: [filesystem, docker, semgrep]
    - sub_agents: [dependency-scanner, secret-detector, security-auditor]
```

### devops-heartbeat

```yaml
devops-heartbeat:
  inject:
    - fleet_state: [work_mode, backend_mode]
    - role_data: [infra_tasks, service_health, deployment_state]
    - directives: all
    - messages: mentions
    - tasks: assigned
    - sub_agents: [container-inspector]
```

### devops-reasoning

```yaml
devops-reasoning:
  inject:
    - agent_manual: devops
    - methodology: reasoning
    - skills: [fleet-deployment-strategy, fleet-monitoring-setup, fleet-devops-iac]
    - pack_skills: [superpowers:writing-plans, superpowers:brainstorming]
    - ring_skills: [dev-docker-security, dev-helm]
    - tools: [fleet_task_accept]
    - note: "Plan IaC changes. Everything scriptable. Everything reproducible."
```

### devops-contribution

```yaml
devops-contribution:
  inject:
    - agent_manual: devops (deployment role)
    - tools: [fleet_contribute (deployment_manifest)]
    - target_task: full context
    - skills: [fleet-deployment-strategy, fleet-phase-infrastructure-maturity]
    - note: "Environment, config, deploy strategy, monitoring, rollback plan"
```

## P2 Intents (7)

### architect-heartbeat

```yaml
architect-heartbeat:
  inject:
    - fleet_state: [work_mode]
    - role_data: [tasks_needing_design, complexity_flags, architecture_decisions]
    - directives: all
    - messages: mentions
    - tasks: assigned
    - sub_agents: [pattern-analyzer, dependency-mapper, code-explorer]
```

### qa-heartbeat

```yaml
qa-heartbeat:
  inject:
    - fleet_state: [work_mode]
    - role_data: [contribution_tasks, review_tasks, coverage_metrics]
    - directives: all
    - messages: mentions
    - tasks: assigned
    - sub_agents: [test-runner, regression-checker, coverage-analyzer]
```

### writer-heartbeat

```yaml
writer-heartbeat:
  inject:
    - fleet_state: [work_mode]
    - role_data: [doc_tasks, completed_features_without_docs, stale_pages]
    - directives: all
    - messages: mentions
    - tasks: assigned
```

### ux-heartbeat

```yaml
ux-heartbeat:
  inject:
    - fleet_state: [work_mode]
    - role_data: [contribution_tasks, ux_review_tasks]
    - directives: all
    - messages: mentions
    - tasks: assigned
```

### devsecops-analysis

```yaml
devsecops-analysis:
  inject:
    - agent_manual: devsecops
    - methodology: analysis
    - skills: [fleet-vulnerability-assessment, fleet-threat-modeling]
    - pack_skills: [superpowers:systematic-debugging]
    - trailofbits: [openai-security-threat-model, openai-security-ownership-map]
    - tools: [fleet_artifact_create (security_assessment)]
    - mcp: [filesystem, docker, semgrep]
    - sub_agents: [dependency-scanner, security-auditor]
```

### devsecops-reasoning

```yaml
devsecops-reasoning:
  inject:
    - agent_manual: devsecops
    - methodology: reasoning
    - skills: [fleet-incident-response, fleet-security-contribution]
    - pack_skills: [superpowers:writing-plans]
    - tools: [fleet_task_accept]
    - note: "Plan security fix. Phase-appropriate: POC basic, production hardened."
```

### devops-analysis

```yaml
devops-analysis:
  inject:
    - agent_manual: devops
    - methodology: analysis
    - skills: [fleet-fleet-infrastructure, fleet-docker-management]
    - pack_skills: [superpowers:systematic-debugging]
    - ring_skills: [dev-sre]
    - tools: [fleet_artifact_create (infrastructure_assessment)]
    - mcp: [filesystem, docker, github-actions]
    - sub_agents: [container-inspector]
```

## P3 Intents (4)

### accountability-work

```yaml
accountability-work:
  inject:
    - agent_manual: accountability
    - methodology: work
    - skills: [fleet-compliance-reporting, fleet-compliance-verification]
    - pack_skills: [superpowers:verification-before-completion]
    - borghei_skills: [soc2-compliance-expert, nist-csf-specialist]
    - tools: [fleet_artifact_create (compliance_report), fleet_alert]
```

### architect-conversation

```yaml
architect-conversation:
  inject:
    - agent_manual: architect
    - methodology: conversation
    - skills: [fleet-communicate]
    - pack_skills: [superpowers:brainstorming, superpowers:preserving-productive-tensions]
    - note: "Clarify design requirements. Understand constraints. NO design yet."
```

### engineer-investigation

```yaml
engineer-investigation:
  inject:
    - agent_manual: engineer
    - methodology: investigation
    - skills: [fleet-option-exploration, fleet-code-exploration]
    - pack_skills: [superpowers:brainstorming, superpowers:dispatching-parallel-agents]
    - sub_agents: [code-explorer]
    - tools: [fleet_artifact_create (investigation_document)]
    - mcp: [filesystem, github, context7]
    - note: "Research multiple approaches. Not just the first one."
```

### ux-analysis

```yaml
ux-analysis:
  inject:
    - agent_manual: ux
    - methodology: analysis
    - skills: [fleet-ux-every-level, fleet-accessibility-audit]
    - pack_skills: [superpowers:brainstorming]
    - tools: [fleet_artifact_create (ux_assessment)]
    - mcp: [filesystem, playwright]
    - note: "Analyze UX at ALL levels — CLI, API, errors, config, not just UI."
```

## Pack Skills Injection Into EXISTING Intents (33)

Every existing intent also needs pack skill references. Pattern:

| Stage | Universal Pack Skills to Add |
|-------|------------------------------|
| conversation | superpowers:brainstorming |
| analysis | superpowers:systematic-debugging, superpowers:brainstorming |
| investigation | superpowers:brainstorming, superpowers:dispatching-parallel-agents |
| reasoning | superpowers:writing-plans, superpowers:brainstorming |
| work | superpowers:test-driven-development, superpowers:verification-before-completion, superpowers:systematic-debugging |
| review | superpowers:verification-before-completion |
| contribution | (stage-appropriate from above) |
| heartbeat | (none — heartbeat is brief) |

Plus role-specific pack skills:

| Role | Additional Pack Skills |
|------|----------------------|
| architect | NeoLabHQ:ddd, NeoLabHQ:sadd, NeoLabHQ:sdd (reasoning) |
| devsecops | trailofbits:security-awareness, trailofbits:threat-model (analysis, investigation) |
| fleet-ops | ring:code-reviewer, ring:security-reviewer, ring:test-reviewer (review) |
| PM | ring:pre-dev-task-breakdown, ring:pre-dev-delivery-planning (reasoning) |
| writer | ring:writing-api-docs, ring:documentation-structure (work) |
| accountability | borghei:soc2-compliance-expert, borghei:nist-csf-specialist (analysis, work) |

## Sub-Agent Injection Into Relevant Intents

| Role | Sub-Agents | Added To Intents |
|------|-----------|-----------------|
| engineer | test-runner, code-explorer | engineer-work, engineer-analysis, engineer-investigation, engineer-heartbeat |
| architect | pattern-analyzer, dependency-mapper, code-explorer | architect-analysis, architect-investigation, architect-heartbeat |
| QA | test-runner, regression-checker, coverage-analyzer | qa-work, qa-review, qa-heartbeat |
| devops | container-inspector | devops-work, devops-analysis, devops-heartbeat |
| devsecops | dependency-scanner, secret-detector, security-auditor | devsecops-work, devsecops-investigation, devsecops-analysis, devsecops-heartbeat |
| fleet-ops | trail-reconstructor | fleet-ops-review |
| PM | sprint-analyzer | pm-heartbeat |

## Result After Expansion

| Metric | Before | After |
|--------|--------|-------|
| Total intents | 33 | 52 |
| Coverage | 41% | 65% |
| Pack skills in intents | 0 | ~80 references |
| Sub-agent recommendations | 0 | ~25 references |
| Roles with heartbeat | 3/10 | 10/10 |

65% coverage is pragmatic — the remaining 35% are stages that roles rarely enter (PM-analysis, writer-investigation, etc.). Adding those is low priority and can be done incrementally.

## Implementation

1. Add 19 new intent entries to intent-map.yaml
2. Add pack_skills field to all 52 intents (new + existing)
3. Add sub_agents field to relevant intents
4. Update Navigator._find_intent() if needed to handle new fields
5. Update Navigator._assemble_from_intent() to render pack skills and sub-agents
6. Test Navigator.assemble() for all 52 intents
7. Verify knowledge-context.md output is coherent and within 7500 char limit

## Relationships

- PART_OF: E001 Phase 2 (Scaffold) + E014 (Autocomplete Web)
- DEPENDS_ON: E007 (pack skills must be identified and mapped)
- FEEDS_INTO: TOOLS.md redesign (Navigator must deliver what TOOLS.md drops)
- VALIDATED_BY: Navigator output tests per role×stage
