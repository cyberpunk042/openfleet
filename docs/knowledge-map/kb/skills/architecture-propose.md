# architecture-propose

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/architecture-propose/SKILL.md
**Invocation:** /architecture-propose [path to idea doc]
**Effort:** high
**Allowed tools:** Read, Write, Edit, Glob, Grep

## Purpose

Analyze an idea document and propose a concrete, buildable system architecture. Takes a raw idea doc (default: `docs/idea.md`) and produces a complete architecture document covering components, layers, data flows, technology stack, deployment model, security, scalability, and the first 5 buildable milestones.

## Input

Reads the idea document at the path provided as argument (default: `docs/idea.md`). Also reads README.md and CLAUDE.md if they exist for additional project context.

## Process

1. Understand core requirements from the idea doc
2. Identify system boundaries and components
3. Choose appropriate technologies
4. Design the layer/component structure
5. Map data flows between components
6. Identify external dependencies and integrations
7. Consider deployment model

## Output

Writes `docs/architecture.md` with 10 required sections:
- **Overview** — one paragraph system description
- **Components** — each with name, responsibility (SRP), interfaces, technology + rationale
- **Layer Structure** — organization (layers, services, modules) + directory structure proposal
- **Data Flow** — how data moves through the system, key pathways
- **Technology Stack** — table: layer, technology, rationale
- **External Dependencies** — what the system depends on and why
- **Deployment Model** — containers, serverless, bare metal, etc.
- **Security Considerations** — auth, data protection, access control
- **Scalability Path** — how it grows from MVP to production
- **First 5 Milestones** — ordered steps to build, each producing something testable

Presents to user for review. Incorporates feedback before finalizing.

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| Architect | ESSENTIAL | Core skill — design authority produces architecture |
| PM | RECOMMENDED | PM may use to understand architecture during planning |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| reasoning | Primary — produce architecture from analyzed requirements |
| work | When architect has own design task |

## Relationships

- DEPENDS ON: idea-capture or idea-refine (idea doc must exist first)
- FOLLOWED BY: architecture-review (validate the proposed architecture)
- FOLLOWED BY: scaffold (create project structure from the architecture)
- PRODUCES: docs/architecture.md (consumed by engineer, devops, QA for implementation)
- CONNECTS TO: fleet_artifact_create (architecture = plan artifact type)
- CONNECTS TO: fleet_contribute (architect delivers design_input based on this architecture)
- CONNECTS TO: methodology — REASONING stage (plan the approach before building)
- CONNECTS TO: standards.py — plan artifact requires: title, requirement_reference, approach, target_files, steps, acceptance_criteria_mapping
- PAIRED WITH: architecture-review (propose then review — different perspectives)
- FEEDS: engineer's implementation plan (architect's design → engineer's plan → engineer's code)
