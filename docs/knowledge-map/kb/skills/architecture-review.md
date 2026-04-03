# architecture-review

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/architecture-review/SKILL.md
**Invocation:** /architecture-review
**Effort:** high
**Allowed tools:** Read, Write, Edit, Glob, Grep

## Purpose

Critically review an existing architecture document against 8 evaluation criteria. Checks completeness against the idea doc, identifies over-engineering and under-engineering, evaluates security, dependencies, testability, deployability, and missing pieces. For each issue found, proposes a specific fix. Rates overall readiness: Ready to build / Needs revision / Major rethink.

## Process

1. Read `docs/architecture.md` AND `docs/idea.md` (reviews architecture against original requirements)
2. Evaluate against 8 criteria:
   - **Completeness** — every requirement from idea doc has a home in architecture?
   - **Over-engineering** — anything more complex than needed for current stage?
   - **Under-engineering** — will anything break at moderate scale?
   - **Security** — exposed attack surfaces?
   - **Dependencies** — risky or unnecessary external dependencies?
   - **Testability** — can each component be tested independently?
   - **Deployability** — can this be deployed incrementally?
   - **Missing pieces** — what's not addressed?
3. For each issue: propose a specific fix (not vague — actionable)
4. Rate overall readiness

## Output

Review comments inline in the architecture doc, or separate `docs/architecture-review.md` if preferred. Each issue includes: what's wrong, why it matters, specific proposed fix.

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| Architect | ESSENTIAL | Review own or others' architecture for quality |
| DevSecOps | RECOMMENDED | Security evaluation of architecture |
| Fleet-ops | OPTIONAL | Architecture alignment check during review |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| analysis | Review existing architecture for gaps |
| reasoning | Validate proposed design before implementation |

## Relationships

- FOLLOWS: architecture-propose (review what was proposed)
- PRECEDES: scaffold (only scaffold after architecture passes review)
- READS: docs/architecture.md (the architecture) + docs/idea.md (the requirements)
- PRODUCES: review findings with specific fixes + readiness rating
- CONNECTS TO: fleet_contribute (architect reviews engineer's proposed architecture as design_input)
- CONNECTS TO: fleet_approve (architecture alignment is part of fleet-ops 7-step review)
- CONNECTS TO: quality-audit skill (broader quality check includes architecture alignment)
- CONNECTS TO: standards.py — plan artifact quality criteria include "approach specifies target files"
- CONNECTS TO: anti-corruption — "do not over-architect for current phase" aligns with phase-appropriate standards
- KEY PRINCIPLE: review checks AGAINST the idea doc requirements — deviation from requirements is a finding
