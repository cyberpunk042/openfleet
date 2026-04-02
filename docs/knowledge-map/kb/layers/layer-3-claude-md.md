# Layer 3: CLAUDE.md

**Type:** Agent File (Middle layer — stable)
**Position:** 3 of 8 (role-specific rules — high influence zone)
**System:** S22 (Agent Intelligence)
**Standard:** claude-md-standard.md
**Constraint:** MAX 4000 characters (gateway-enforced)

## Purpose

Role-specific behavioral constraints. Each agent's CLAUDE.md is UNIQUE — contains only rules that change behavior specific to their role. No generic advice. Every line should be role-specific. Dense and precise — 4000 chars is tight.

## Required Sections (8, in order)

1. **Core Responsibility** (~100 chars) — ONE sentence, what the role DOES
2. **Role-Specific Rules** (~2000 chars) — largest section, unique per role
3. **Stage Protocol** (~400 chars) — behavior per methodology stage
4. **Tool Chains** (~500 chars) — 4-8 tools with chain patterns
5. **Contribution Model** (~350 chars) — gives/receives per synergy matrix
6. **Boundaries** (~250 chars) — min 3 refusals with "(that's the {role})"
7. **Context Awareness** (~200 chars) — both countdowns (context 7%/5%, rate limit 85%/90%)
8. **Anti-Corruption** (~150 chars) — brief summary reinforcing SOUL.md rules

## Character Budget

Total: 4000 chars max. Approximate allocation:
- Role rules: 2000 (50%)
- Tool chains: 500 (12.5%)
- Stage protocol: 400 (10%)
- Contribution: 350 (8.75%)
- Boundaries: 250 (6.25%)
- Context: 200 (5%)
- Anti-corruption: 150 (3.75%)
- Title/headers: 150 (3.75%)

## Relationships

- INJECTED BY: gateway (_build_agent_context, position 3, max 4000 chars)
- PROVISIONED FROM: agents/_template/CLAUDE.md/{role}.md
- CONTENT FROM: fleet-elevation/05-14 (per-role specifications)
- VALIDATED BY: scripts/validate-agents.sh (char count, 8 sections, no concern mixing, tool names match tools.py, contributions match synergy matrix)
- REFERENCES: stage_context.py (stage protocol section summarizes MUST/MUST NOT)
- REFERENCES: fleet-elevation/24 (tool chain patterns)
- REFERENCES: fleet-elevation/15 (contribution model)
- REFERENCES: fleet-elevation/20 (anti-corruption summary)
- AUGMENTED BY: InstructionsLoaded hook (can inject additional context from knowledge map at load time)
- DOES NOT CONTAIN: identity (IDENTITY.md), values/full rules (SOUL.md), tool docs with params (TOOLS.md), colleague descriptions (AGENTS.md), dynamic data (context/), action protocol (HEARTBEAT.md)
- STABLE: changes when fleet evolves, not during operation
- PER AGENT: 10 unique CLAUDE.md files

## Per-Role Content Sources

| Role | Fleet-Elevation Doc | Core Focus |
|------|-------------------|-----------|
| PM | /05 | Task assignment, PO routing, sprint, gate management |
| Fleet-ops | /06 | 7-step review, approval processing, methodology compliance |
| Architect | /07 | Design authority, SRP/DDD/Onion, min 3 options |
| DevSecOps | /08 | Security layer, BEFORE/DURING/AFTER, crisis response |
| Engineer | /09 | Implementation, TDD, process respect, stay in scope |
| DevOps | /10 | IaC, CI/CD, deployment, operational maturity |
| QA | /11 | Test PREDEFINITION, pessimistic, phase-appropriate |
| Writer | /12 | Living documentation, stale detection, continuous |
| UX | /13 | UX everywhere (CLI, API, errors, config, not just UI) |
| Accountability | /14 | Trail verification, compliance, process adherence |
