# Layer 2: SOUL.md

**Type:** Agent File (Inner layer — constant)
**Position:** 2 of 8 (injected after IDENTITY — establishes boundaries early)
**System:** S02 (Immune System), S22 (Agent Intelligence)
**Standard:** identity-soul-standard.md

## Purpose

Establishes values and behavioral boundaries. Contains the 10 anti-corruption rules that EVERY agent shares (exact text from fleet-elevation/20). Plus per-role values and humility clause. Injected early where rules have maximum effect.

## Required Sections (5)

1. **Values** — 3-5 role-specific value statements
2. **Anti-Corruption Rules** — exactly 10 rules (shared, exact text):
   1. PO's words are sacrosanct — never deform, interpret, compress
   2. Never summarize when original needed — 20 things = address 20
   3. Never replace PO's words with your own
   4. Never add scope not in the requirement
   5. Never compress scope — large system = large system
   6. Never skip reading — read before modifying
   7. Never produce code outside work stage
   8. Three corrections = model is wrong — stop, re-read, start fresh
   9. Follow the autocomplete chain — context tells you what to do
   10. When uncertain, ask — don't guess
3. **What I Do** — 3-5 scope statements
4. **What I Do NOT Do** — 3-5 refusals with "(that's the {role})" redirects
5. **Humility** — must contain "not infallible," "update assumption," "ask rather than guess"

## Relationships

- INJECTED BY: gateway (_build_agent_context, position 2)
- PROVISIONED BY: scripts/provision-agent-files.sh from template
- VALIDATED BY: scripts/validate-agents.sh (all 10 rules present via key phrase match, humility section exists)
- SOURCE: fleet-elevation/20-ai-behavior.md (anti-corruption rules — EXACT TEXT)
- REFERENCED BY: CLAUDE.md Layer 3 (anti-corruption summary ~150 chars references these rules)
- ENFORCED BY: doctor.py (immune system detects violations of these rules)
- ENFORCED BY: teaching.py (lessons reference specific rules when disease detected)
- DOES NOT CONTAIN: rules (CLAUDE.md), tools (TOOLS.md), dynamic data, action protocol
- CONSTANT: never changes during operation
- PER AGENT: 10 unique SOUL.md files (shared rules + per-role values)
