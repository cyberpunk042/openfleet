# InstructionsLoaded

**Type:** Claude Code Hook (lifecycle event)
**Category:** Configuration (fires when CLAUDE.md / rules are parsed)
**Handler types:** command, http, prompt, agent
**Can block:** NO
**Matcher:** `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`

## What It Actually Does

Fires when Claude Code parses CLAUDE.md and other instruction files (.claude/rules/, imported @files). The handler can AUGMENT the loaded instructions with additional context — effectively adding dynamic content to what are normally static instruction files.

This is the mechanism for making CLAUDE.md DYNAMIC without changing the file on disk. The knowledge map navigator can inject role-specific, stage-specific content through this hook, making each agent's instructions context-aware.

## Handler Input

```json
{
  "hook_event_name": "InstructionsLoaded",
  "session_id": "...",
  "trigger": "session_start",
  "instructions_sources": ["CLAUDE.md", ".claude/rules/fleet-rules.md"]
}
```

## Handler Output

```json
{
  "additionalContext": "## Per-Stage Recommendations\n\nYou are in REASONING stage. Recommended:\n- Skills: /architecture-propose, /writing-plans\n- Commands: /plan, /branch\n- Focus: produce plan referencing verbatim requirement"
}
```

## Fleet Use Case: Dynamic CLAUDE.md Augmentation

```
InstructionsLoaded fires (CLAUDE.md parsed)
├── Read agent name + current task stage
├── Look up methodology-manual.md for this stage:
│   ├── Recommended skills for this stage
│   ├── Recommended commands for this stage
│   ├── Relevant MCP servers for this stage
│   └── Stage-specific reminders
├── Assemble augmentation:
│   "## Stage: REASONING
│    Skills: /architecture-propose, /writing-plans, /brainstorming
│    Commands: /plan, /branch, /effort high
│    Remember: produce plan referencing verbatim. Do NOT implement yet."
├── Return: {additionalContext: augmentation}
└── Agent sees CLAUDE.md + augmented stage-specific content
```

The CLAUDE.md file stays at 4000 chars (gateway limit). The InstructionsLoaded hook adds MORE context AFTER the gateway limit is applied — effectively extending what the agent knows beyond the 4000 char constraint.

## Why This Matters

CLAUDE.md has a hard 4000 char limit. It must fit: core responsibility, role rules, stage protocol, tool chains, contribution model, boundaries, context awareness, anti-corruption — all in 4000 chars. There's no room for per-stage skill/command recommendations.

InstructionsLoaded hook EXTENDS the effective CLAUDE.md by injecting additional role+stage content after the gateway limit is applied. The agent sees CLAUDE.md (static, 4000 chars) + augmented content (dynamic, from knowledge map).

## Relationships

- FIRES AFTER: CLAUDE.md and .claude/rules/ files are parsed
- CANNOT BLOCK: instructions load regardless — but augmentation shapes behavior
- AUGMENTS: CLAUDE.md content with dynamic knowledge map data
- CONNECTS TO: methodology-manual.md (per-stage tool/skill/command recommendations)
- CONNECTS TO: knowledge map navigator (selects what to augment based on role + stage)
- CONNECTS TO: SessionStart hook (SessionStart fires first, InstructionsLoaded fires after)
- CONNECTS TO: agent-tooling.yaml (which skills/commands to recommend per role)
- CONNECTS TO: injection-profiles.yaml (how much augmentation per context size)
- CONNECTS TO: CLAUDE.md Layer 3 (the 4000-char static base that this augments)
- CONNECTS TO: .claude/rules/ (modular rules files — augmentation can add rule-like content)
- KEY INSIGHT: this hook SOLVES the 4000-char CLAUDE.md constraint. Static rules in the file + dynamic context from the hook = comprehensive agent guidance without hitting the gateway limit.
