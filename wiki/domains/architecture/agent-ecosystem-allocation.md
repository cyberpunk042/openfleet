---
title: "Agent Ecosystem Allocation — Skills, Plugins, Packs Per Role"
type: reference
domain: architecture
status: draft
confidence: high
created: 2026-04-09
updated: 2026-04-09
tags: [E001, E007, skills, plugins, packs, ecosystem, per-role, allocation]
sources:
  - id: agent-tooling
    type: documentation
    file: config/agent-tooling.yaml
  - id: skill-packs
    type: documentation
    file: config/skill-packs.yaml
  - id: skill-assignments
    type: documentation
    file: config/skill-assignments.yaml
  - id: skill-stage-mapping
    type: documentation
    file: config/skill-stage-mapping.yaml
  - id: ecosystem-research
    type: documentation
    file: ecosystem research
epic: [E001, E007]
phase: "0 — Research"
---

# Agent Ecosystem Allocation — Skills, Plugins, Packs Per Role

## Summary

Cross-ecosystem inventory of skills, plugins, and skill-packs available to fleet agents — mapping what Anthropic ships by default, what OpenArms contributes, what ClawHub offers, and what we allocate per role. Acts as the input register for skill-stage-mapping.yaml and agent-tooling.yaml so each of the 10 roles receives a calibrated, non-overlapping tooling envelope.

## PO Directive

> "we will also make sure that we use all the superpower and main skills from high quality repositories marketplaces packs"

> "The AIs agents also need to know their Tools, Stacks and Skills. Everyone has tool specialisations and domain specializations."

> "Lets also not forget that we are not done, what you added in the kB is mostly what we have but this is far from what we aim to have. much more skills and plugins depending on the agents and so on."

## Ecosystem Scale

| Source | Count | Quality | Status |
|--------|-------|---------|--------|
| Anthropic Official Marketplace | 126 plugins | Curated, vendor partnerships | 10 configured in agent-tooling.yaml |
| obra/superpowers ecosystem | 30+ skills, 9 plugins | Battle-tested (v5.0.7), de facto standard | Configured, not installed |
| LerianStudio/ring | 89 skills, 38 agents | Team-structured, mirrors fleet | Not evaluated |
| trailofbits/skills-curated | 28 security plugins | Security researchers, vetted | Not evaluated |
| NeoLabHQ/context-engineering-kit | 14 plugins | Engineering methodology (DDD, SADD, TDD) | Not evaluated |
| borghei/Claude-Skills | 225+ skills, 23 compliance | Business-domain, regulatory | Not evaluated |
| alirezarezvani/tresor + skill-factory | 8 agents, 20+ commands | Practical workflows | Not evaluated |
| davepoon/buildwithclaude | 125+ skills, 115+ agents | Aggregator, variable quality | Not evaluated |
| jeremylongshore/plugins-plus-skills | 500+ skills | Quantity-oriented, template-based | Not evaluated |

**Total available ecosystem: ~1,100+ skills, 580+ plugins, 215+ agents.**

## The Three Packs That Matter Most

### Pack 1: superpowers (obra)

The de facto standard. Ported to 7+ platforms. Every fleet agent benefits.

| Skill Category | Skills | Fleet Roles |
|---------------|--------|-------------|
| Collaboration | brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, receiving-code-review, requesting-code-review, subagent-driven-development, using-git-worktrees, writing-plans, remembering-conversations | ALL |
| Debugging | systematic-debugging, verification-before-completion, root-cause-tracing, defense-in-depth | engineer, QA, devops, devsecops |
| Architecture | preserving-productive-tensions | architect |
| Problem-Solving | collision-zone-thinking, inversion-exercise, meta-pattern-recognition, scale-game, simplification-cascades, when-stuck | architect, engineer, PM |
| Testing | test-driven-development, testing-anti-patterns, condition-based-waiting | engineer, QA |
| Research | tracing-knowledge-lineages | architect, writer |
| Meta | writing-skills, testing-skills-with-subagents, gardening-skills-wiki | architect (skill creation) |

**Decision:** Install for ALL agents (default). Already in agent-tooling.yaml for architect, engineer, QA. Expand to all.

### Pack 2: LerianStudio/ring

Team-structured — mirrors fleet. 89 skills organized by team function.

| ring Team | Skills | Fleet Agent |
|-----------|--------|-------------|
| dev-team (33 skills) | dev-implementation, dev-unit-testing, dev-integration-testing, dev-fuzz-testing, dev-docker-security, dev-helm, dev-sre, dev-refactor, dev-frontend-accessibility, dev-frontend-e2e, dev-frontend-performance... | software-engineer, devops, QA |
| pm-team (17 skills) | pre-dev-prd-creation, pre-dev-task-breakdown, pre-dev-feature-map, pre-dev-dependency-map, pre-dev-delivery-planning, pre-dev-api-design, pre-dev-data-model... | project-manager, architect |
| pmo-team (10 skills) | portfolio-planning, executive-reporting, risk-management, resource-allocation, project-health-check, pmo-retrospective, delivery-reporting, dependency-mapping... | project-manager, accountability |
| tw-team (8 skills) | writing-api-docs, writing-functional-docs, documentation-review, documentation-structure, voice-and-tone, api-field-descriptions... | technical-writer |
| finops-team (8 skills) | infrastructure-cost-estimation, regulatory-templates-gate1/2/3... | devops, accountability |
| default (23 skills) | brainstorming, systematic-debugging, TDD, executing-plans, writing-plans, production-readiness-audit, release-guide-info... + 10 review agents (code-reviewer, security-reviewer, test-reviewer, dead-code-reviewer, nil-safety-reviewer, consequences-reviewer, codebase-explorer, business-logic-reviewer, review-slicer) | ALL |

**Decision:** Evaluate. Team structure aligns perfectly. Review agents (10) complement our fleet-ops review protocol. PM pre-dev skills fill our contribution design gap.

### Pack 3: trailofbits/skills-curated

28 security plugins from security researchers. Depth we don't have.

| Plugin | Purpose | Fleet Use |
|--------|---------|-----------|
| ffuf-web-fuzzing | Web application fuzzing | devsecops — active testing |
| ghidra-headless | Binary reverse engineering | devsecops — deep analysis |
| openai-security-best-practices | Security patterns reference | devsecops, engineer |
| openai-security-ownership-map | Security ownership per codebase area | devsecops, architect |
| openai-security-threat-model | Structured threat modeling | devsecops |
| planning-with-files | File-based planning (complements our methodology) | architect, PM |
| python-code-simplifier | Complexity reduction | engineer, QA |
| scv-scan | Supply chain vulnerability scanning | devsecops |
| security-awareness | General security patterns | ALL |

**Decision:** Install security-relevant ones for devsecops. Select cross-cutting ones (security-awareness, python-code-simplifier) for engineer/QA.

## Per-Agent Complete Allocation

### Project Manager

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, plannotator |
| **superpowers** | brainstorming, writing-plans, executing-plans, dispatching-parallel-agents, when-stuck |
| **ring pm-team** | pre-dev-prd-creation, pre-dev-task-breakdown, pre-dev-feature-map, pre-dev-dependency-map, pre-dev-delivery-planning |
| **ring pmo-team** | portfolio-planning, project-health-check, delivery-reporting |
| **Fleet skills** | fleet-task-triage, fleet-sprint-planning, fleet-backlog-grooming, fleet-blocker-resolution, fleet-po-communication, fleet-epic-breakdown, fleet-stage-progression, fleet-pm-orchestration |
| **Gateway skills** | fleet-plan, fleet-sprint, fleet-plane, fleet-task-create, fleet-task-update, fleet-comment, fleet-memory |
| **Marketplace** | pm-plan, pm-assess, pm-status-report, pm-retrospective, pm-changelog, pm-handoff, idea-capture, feature-plan |
| **MCP servers** | fleet, github, plane |
| **Sub-agents** | sprint-analyzer, code-explorer |

### Fleet-Ops (Board Lead)

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, pr-review-toolkit, claude-md-management |
| **superpowers** | verification-before-completion, receiving-code-review, systematic-debugging |
| **ring default** | code-reviewer, security-reviewer, test-reviewer, dead-code-reviewer, consequences-reviewer, review-slicer |
| **Fleet skills** | fleet-ops-review-protocol, fleet-methodology-compliance, fleet-quality-enforcement, fleet-budget-awareness, fleet-board-health-assessment, fleet-trail-verification |
| **Gateway skills** | fleet-review, fleet-alert, fleet-comment, fleet-memory |
| **Marketplace** | pm-assess, quality-audit, openclaw-health, openclaw-fleet-status |
| **MCP servers** | fleet, github |
| **Sub-agents** | trail-reconstructor, code-explorer |

### Architect

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, context7, superpowers, adversarial-spec, skill-creator, claude-code-setup |
| **superpowers** | brainstorming, writing-plans, preserving-productive-tensions, meta-pattern-recognition, simplification-cascades, tracing-knowledge-lineages |
| **NeoLabHQ** | ddd (Domain-Driven Design), sadd (Software Architecture Design Doc), sdd (Software Design Doc), tech-stack |
| **ring pm-team** | pre-dev-api-design, pre-dev-data-model |
| **Fleet skills** | fleet-architecture-health, fleet-design-contribution, fleet-design-pattern-selection, fleet-srp-verification, fleet-domain-boundary-enforcement, fleet-option-exploration, fleet-adr-creation, fleet-architecture-cron-operations |
| **Gateway skills** | fleet-plan, fleet-report, fleet-gap, fleet-comment |
| **Marketplace** | architecture-propose, architecture-review, scaffold, feature-plan, refactor-architecture |
| **MCP servers** | fleet, filesystem, github |
| **Sub-agents** | pattern-analyzer, dependency-mapper, code-explorer |

### DevSecOps — Cyberpunk-Zero

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, security-guidance, sage, semgrep |
| **superpowers** | systematic-debugging, defense-in-depth, root-cause-tracing, verification-before-completion |
| **trailofbits** | openai-security-threat-model, openai-security-ownership-map, openai-security-best-practices, scv-scan, ffuf-web-fuzzing, security-awareness |
| **borghei compliance** | gdpr-dsgvo-expert, soc2-compliance-expert, nist-csf-specialist (selected — for when compliance scope expands) |
| **Fleet skills** | fleet-vulnerability-assessment, fleet-dependency-audit, fleet-secret-scanning, fleet-incident-response, fleet-threat-modeling, fleet-security-compliance, fleet-security-contribution |
| **Gateway skills** | fleet-alert, fleet-report, fleet-comment |
| **Marketplace** | infra-security, quality-audit, config-secrets, foundation-auth, fleet-security-audit |
| **MCP servers** | fleet, filesystem, docker, semgrep |
| **Sub-agents** | dependency-scanner, secret-detector, security-auditor, code-explorer |

### Software Engineer

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, context7, superpowers, pyright-lsp, skill-creator |
| **superpowers** | test-driven-development, systematic-debugging, verification-before-completion, subagent-driven-development, requesting-code-review, receiving-code-review, using-git-worktrees, finishing-a-development-branch, brainstorming, writing-plans, executing-plans, testing-anti-patterns |
| **ring dev-team** | dev-implementation, dev-unit-testing, dev-integration-testing, dev-refactor |
| **trailofbits** | python-code-simplifier |
| **Fleet skills** | fleet-engineer-workflow, fleet-contribution-consumption, fleet-conventional-commits, fleet-implementation-planning, fleet-subtask-creation, fleet-design-pattern-application, fleet-code-exploration, fleet-fix-task-handling |
| **Gateway skills** | fleet-commit, fleet-pr, fleet-comment, fleet-urls, fleet-alert, fleet-task-create |
| **Marketplace** | feature-implement, feature-plan, feature-test, refactor-extract, refactor-split, foundation-deps, quality-lint |
| **MCP servers** | fleet, filesystem, github, playwright |
| **Sub-agents** | test-runner, code-explorer |

### DevOps

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, hookify, commit-commands, claude-code-setup |
| **superpowers** | systematic-debugging, verification-before-completion, writing-plans, executing-plans |
| **ring dev-team** | dev-docker-security, dev-helm, dev-sre |
| **ring finops-team** | infrastructure-cost-estimation |
| **Fleet skills** | fleet-devops-iac, fleet-docker-management, fleet-cicd-pipeline, fleet-deployment-strategy, fleet-monitoring-setup, fleet-rollback-procedures, fleet-fleet-infrastructure, fleet-phase-infrastructure-maturity |
| **Gateway skills** | fleet-commit, fleet-pr, fleet-alert, fleet-comment |
| **Marketplace** | foundation-docker, foundation-ci, foundation-config, ops-deploy, ops-rollback, ops-incident, ops-backup, ops-maintenance, config-deploy, infra-monitoring |
| **MCP servers** | fleet, filesystem, github, docker, github-actions |
| **Sub-agents** | container-inspector, code-explorer |

### QA Engineer

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, superpowers |
| **superpowers** | test-driven-development, testing-anti-patterns, condition-based-waiting, systematic-debugging, verification-before-completion, subagent-driven-development |
| **ring default** | test-reviewer |
| **Fleet skills** | fleet-qa-predefinition, fleet-test-validation, fleet-test-contribution-protocol, fleet-acceptance-criteria-quality, fleet-regression-testing, fleet-boundary-value-analysis, fleet-phase-testing, fleet-integration-testing |
| **Gateway skills** | fleet-test, fleet-comment, fleet-alert |
| **Marketplace** | quality-coverage, quality-audit, quality-lint, quality-debt, foundation-testing, feature-test, feature-review |
| **MCP servers** | fleet, filesystem, playwright |
| **Sub-agents** | test-runner, regression-checker, coverage-analyzer, code-explorer |

### Technical Writer

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, context7, ars-contexta, elements-of-style |
| **superpowers** | writing-plans, brainstorming, tracing-knowledge-lineages |
| **ring tw-team** | writing-api-docs, writing-functional-docs, documentation-review, documentation-structure, voice-and-tone, api-field-descriptions |
| **Fleet skills** | fleet-doc-contribution-protocol, fleet-documentation-structure, fleet-doc-lifecycle, fleet-terminology-consistency, fleet-changelog-generation, fleet-api-documentation |
| **Gateway skills** | fleet-comment, fleet-report, fleet-urls |
| **Marketplace** | feature-document, pm-changelog, pm-handoff, quality-debt |
| **MCP servers** | fleet, filesystem, github |
| **Sub-agents** | code-explorer |

### UX Designer

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net |
| **superpowers** | brainstorming, collision-zone-thinking, simplification-cascades |
| **Fleet skills** | fleet-ux-contribution-protocol, fleet-ux-every-level, fleet-interaction-design, fleet-component-patterns, fleet-accessibility-audit |
| **Gateway skills** | fleet-comment, fleet-report |
| **Marketplace** | quality-accessibility |
| **MCP servers** | fleet, filesystem, playwright |
| **Sub-agents** | code-explorer |

### Accountability Generator

| Source | What They Get |
|--------|--------------|
| **Plugins** | claude-mem, safety-net, claude-md-management |
| **superpowers** | verification-before-completion |
| **ring pmo-team** | risk-management, governance-specialist patterns |
| **borghei compliance** | soc2-compliance-expert, nist-csf-specialist, risk-management-specialist (selected) |
| **Fleet skills** | fleet-accountability-trail, fleet-compliance-verification, fleet-compliance-reporting, fleet-pattern-detection, fleet-trail-verification |
| **Gateway skills** | fleet-alert, fleet-report, fleet-comment |
| **Marketplace** | quality-audit, quality-debt, quality-coverage, pm-status-report |
| **MCP servers** | fleet, filesystem |
| **Sub-agents** | trail-reconstructor, code-explorer |

## How This Flows Through the System

### 1. Registration (skill-packs.yaml)

```yaml
packs:
  - name: Anthropic Official
    source_url: https://github.com/anthropics/skills
  - name: Superpowers
    source_url: https://github.com/obra/superpowers
  - name: Superpowers Marketplace
    source_url: https://github.com/obra/superpowers-marketplace
  - name: LerianStudio Ring
    source_url: https://github.com/LerianStudio/ring
  - name: Trail of Bits Security
    source_url: https://github.com/trailofbits/skills-curated
  - name: NeoLabHQ Context Engineering
    source_url: https://github.com/NeoLabHQ/context-engineering-kit
```

### 2. Assignment (skill-assignments.yaml + agent-tooling.yaml)

Each pack skill gets mapped to agents with metadata (category, risk, install=true/false). The setup pipeline reads these and installs during provisioning.

### 3. Provisioning (setup pipeline)

```
setup.sh
  → install-plugins.sh (per agent from agent-tooling.yaml)
  → sync skill packs (from skill-packs.yaml → OCMC marketplace)
  → install skills to agents (from skill-assignments.yaml)
  → push-agent-framework.sh (copies TOOLS.md, AGENTS.md to workspaces)
```

### 4. Discovery (gateway)

Gateway skill scanner discovers all SKILL.md files in:
- .claude/skills/ (workspace — our 78 fleet-* skills)
- .agents/skills/ (gateway — 13 operational skills)
- Plugin skill directories (from installed plugins)
- Marketplace-installed skills

Agent sees ALL discovered skills. They don't need to be listed in TOOLS.md — they're discoverable.

### 5. Recommendation (Navigator)

Navigator intent-map.yaml recommends the RIGHT skills for the RIGHT stage. The agent doesn't browse 200 skills — Navigator says "at THIS stage, consider THESE 3-5 skills."

### 6. Reference (TOOLS.md)

TOOLS.md stays focused: tools + chains + boundaries. Does NOT list all skills. Skills are discoverable (gateway) and recommended (Navigator). TOOLS.md trusts those systems.

## Impact on TOOLS.md Redesign

**The desk stays the same size.** Adding 200 more skills to the ecosystem doesn't add lines to TOOLS.md. The desk is tools + chains + boundaries. Period.

**The room gets richer.** Navigator has more skills to recommend per stage. skill-stage-mapping.yaml expands with pack skills alongside our fleet-* skills.

**The filing cabinet grows.** More SKILL.md files available for per-case invocation. This is transparent to the agent — gateway discovers them.

**The agent-tooling.yaml grows.** Each agent's plugin and skill list expands. But this config drives the setup pipeline, not TOOLS.md content.

## Gaps to Fill

| Gap | What's Missing | Epic |
|-----|---------------|------|
| skill-packs.yaml | Only has Anthropic Official. Need superpowers, ring, trailofbits, NeoLabHQ | E007 |
| skill-assignments.yaml | Only has Anthropic marketplace skills. Need pack skills mapped to agents | E007 |
| skill-stage-mapping.yaml | Only has fleet-* and superpowers skills. Need ring, trailofbits skills per stage | E007 |
| install-plugins.sh | Script exists in config but may not handle pack installation | E007 |
| Navigator intent-map.yaml | Needs pack skill names in role×stage intents | E001 |
| Pack evaluation | ring, trailofbits, borghei compliance need hands-on testing | E007 Phase 0 |
| Pack quality filtering | Mega-packs (jeremylongshore, davepoon) need quality triage — most are templates | E007 Phase 0 |

## Relationships

- FEEDS_INTO: E001 (TOOLS.md redesign trusts Navigator to recommend pack skills)
- PART_OF: E007 (Plugin/Skill/Command Ecosystem)
- RELATES_TO: E014 (Autocomplete Web — Navigator delivers skill recommendations)
- RELATES_TO: E003 (Brain — brain's context refresh drives Navigator)
