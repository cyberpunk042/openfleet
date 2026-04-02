# Research Group 04 — Skills Classification (Internal + Ecosystem)

**Date:** 2026-04-02
**Status:** INTERNAL COMPLETE, ECOSYSTEM PENDING
**Workflow step:** 1/4 (Research → Classify → Document → Build)

---

## Part 1: Internal Skills Inventory (85 skills)

### Summary

| Category | Count | Substantive Content | Template Boilerplate |
|----------|-------|--------------------|--------------------|
| AICP skills | 78 | 30 | 48 |
| Fleet skills | 7 | 7 | 0 |
| **Total** | **85** | **37** | **48** |

**Critical finding:** 48 of 78 AICP skills use an identical 4-step generic template.
Their names convey intent but the body is the same boilerplate. Only 37 skills
(30 AICP + 7 fleet) have differentiated, substantive content.

### Skills with Real Content (37)

**Idea phase (2):** idea-capture, idea-refine
**Architecture (2):** architecture-propose, architecture-review
**Scaffold (3):** scaffold, scaffold-monorepo, scaffold-subagent
**Foundation (8):** deps, config, ci, docker, database, auth, logging, testing
**Ops (6):** deploy, rollback, incident, backup, scale, maintenance
**PM (6):** assess, plan, retrospective, handoff, changelog, status-report
**MVP composites (4):** mvp-full, mvp-api, mvp-frontend, mvp-agent
**Cycle composites (5):** full-feature-cycle, full-refactor-cycle, release-cycle, incident-cycle, onboarding-cycle
**OpenClaw (5):** setup, add-agent, configure-mc, health, fleet-status
**Fleet (7):** review, plan, test, security-audit, sprint, communicate, plane

### Skills with Generic Template (48 — need content differentiation)

**Feature (6):** plan, implement, test, review, document, iterate
**Infra (7):** search, api, networking, storage, monitoring, cache, queue
**Refactor (6):** split, rename, architecture, dependencies, extract, patterns
**Quality (6):** accessibility, audit, performance, lint, debt, coverage
**Config (5):** secrets, env, deploy, feature-flags, migrations
**Evolve (6):** api-version, internationalize, migrate, scale, plugin-system, integrate
**Infra-security (1):** infra-security (has some content but shares template structure)

---

## Part 2: Current Assignments vs Recommended

### agent-tooling.yaml Gap Analysis

| Role | Currently Assigned | MISSING — Should Add |
|------|-------------------|---------------------|
| **architect** | architecture-propose, architecture-review, scaffold | feature-plan, refactor-architecture, evolve-api-version |
| **software-engineer** | feature-implement, refactor-extract | feature-plan, feature-test, foundation-deps, refactor-split, quality-lint |
| **qa-engineer** | quality-coverage, quality-audit, foundation-testing | feature-test, feature-review, quality-lint, quality-debt, **fleet-test** |
| **devops** | foundation-docker, foundation-ci, ops-deploy, ops-maintenance | ops-rollback, ops-incident, ops-backup, config-deploy, infra-monitoring |
| **devsecops-expert** | infra-security, quality-audit | config-secrets, foundation-auth, **fleet-security-audit** |
| **fleet-ops** | pm-assess, quality-audit | **openclaw-health, openclaw-fleet-status, openclaw-setup, openclaw-add-agent, fleet-review, fleet-communicate, scaffold-subagent** |
| **project-manager** | pm-plan, pm-status-report, pm-retrospective, pm-changelog | pm-assess, pm-handoff, idea-capture, feature-plan, **fleet-plan, fleet-sprint, fleet-plane** |
| **technical-writer** | feature-document, pm-changelog, pm-handoff | onboarding-cycle, quality-debt |
| **ux-designer** | quality-accessibility | quality-performance, evolve-internationalize |
| **accountability** | quality-audit | quality-debt, quality-coverage, pm-status-report |

### Critical Gaps

1. **Fleet skills (7) not in agent-tooling.yaml at all.** They exist in the fleet repo but aren't assigned to any role. fleet-review → fleet-ops, fleet-plan → PM, fleet-test → QA, fleet-security-audit → devsecops, fleet-sprint → PM, fleet-communicate → ALL, fleet-plane → PM.

2. **fleet-ops massively under-equipped.** Primary OpenClaw operator has 2 skills. Needs 7+ more (5 openclaw + 2 fleet skills).

3. **PM missing fleet orchestration.** Has PM skills but lacks fleet-plan, fleet-sprint, fleet-plane — the core sprint management skills.

4. **devops missing reactive ops.** Has deploy + maintenance but not rollback, incident, backup.

5. **fleet-communicate should be ALL agents.** Every agent needs communication surface guidance.

6. **Composite skills (9) unassigned.** MVP and cycle skills chain multiple atomics together. Should be available to senior roles.

### Per-Stage Skill Recommendations

| Stage | Recommended Skills |
|-------|-------------------|
| **conversation** | idea-capture, fleet-communicate |
| **analysis** | pm-assess, quality-audit, quality-debt, architecture-review, openclaw-health |
| **investigation** | infra-search, quality-performance, fleet-security-audit, infra-security |
| **reasoning** | architecture-propose, feature-plan, pm-plan, fleet-plan |
| **work** | feature-implement, feature-test, scaffold, foundation-*, ops-*, fleet-sprint, fleet-review |

---

## Part 3: Ecosystem Skills Research (pending)

*Waiting for ecosystem research agent to complete. Will add:*
- Superpowers (132K stars) — 20+ TDD methodology skills
- claude-skills (9K stars) — 220+ skills for 10+ roles
- plugins-plus-skills (2K stars) — 1,367 skills
- Other collections

---

## Part 4: Recommendations

### Immediate Actions (Foundation)

1. **Update agent-tooling.yaml** — add all fleet skills to their roles
2. **Add fleet-communicate to ALL agents** — communication surface guidance
3. **Equip fleet-ops properly** — add 7 missing skills
4. **Equip PM properly** — add fleet-plan, fleet-sprint, fleet-plane
5. **Add reactive ops to devops** — rollback, incident, backup

### Short-Term Actions (Infrastructure)

6. **Differentiate 48 template skills** — add real content per skill
7. **Add per-stage recommendations** to agent CLAUDE.md
8. **Evaluate Superpowers plugin** — may replace some of our template skills
9. **Deploy skills to agent workspaces** — .claude/skills/ per agent

### Knowledge Map Integration

10. **Each skill gets a _map.yaml** — role, stage, priority, dependencies
11. **Skills manual** as part of the fleet knowledge map tree
12. **Injection profiles** — which skills to mention per context size

---

## Open Questions for PO

1. **48 template skills:** Differentiate all 48, or focus on the ~15 most used? Or adopt Superpowers/ecosystem skills to replace them?
2. **Composite skills (9):** Assign to all agents, or only PM/architect/fleet-ops who orchestrate?
3. **fleet-communicate:** Confirm it goes to ALL agents?
4. **Superpowers adoption:** 132K stars, TDD methodology — integrate alongside our skills or evaluate as replacement for some?
5. **Skill deployment method:** Symlink from AICP repo? Copy? Or build a skill distribution IaC script?
