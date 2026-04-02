# Layer 1: IDENTITY.md

**Type:** Agent File (Inner layer — constant)
**Position:** 1 of 8 (injected FIRST — maximum influence)
**System:** S06 (Agent Lifecycle), S22 (Agent Intelligence)
**Standard:** identity-soul-standard.md

## Purpose

Grounds the AI's identity. Every subsequent token is generated FROM this identity. "You are Architect Alpha, a top-tier expert." Not "you are an agent" — the words matter. Top-tier experts don't need overconfidence, self-confirmed bias, cheating, or getting lost.

## Required Sections (4)

1. **Who You Are** — name, display_name, fleet, fleet_number, username, role + one-line definition
2. **Your Specialty** — 3-5 sentences of deep domain expertise (must include role-specific knowledge items)
3. **Your Personality** — 2-3 sentences, role-specific communication style
4. **Your Place in the Fleet** — 3-5 sentences referencing at least 3 other agents by role, matching synergy map

## Relationships

- INJECTED BY: gateway (_build_agent_context, position 1)
- PROVISIONED BY: scripts/provision-agent-files.sh from template + agent-identities.yaml
- VALIDATED BY: scripts/validate-agents.sh (fleet identity fields, top-tier language, specialty specificity, synergy consistency)
- REFERENCES: agent.yaml (name, display_name, fleet_id must match exactly)
- REFERENCED BY: fleet-context.md (Layer 6 — identity grounding line)
- DOES NOT CONTAIN: rules (CLAUDE.md), values (SOUL.md), tools (TOOLS.md), dynamic data (context/), action protocol (HEARTBEAT.md)
- CONSTANT: never changes during operation
- PER AGENT: 10 unique IDENTITY.md files (one per role)
