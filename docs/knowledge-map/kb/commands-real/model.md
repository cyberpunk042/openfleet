# /model

**Type:** Claude Code Built-In Command
**Category:** Model & Effort
**Available to:** ALL agents

## What It Actually Does

Select or change the AI model for the current session. Left/right arrows adjust the effort slider (low → medium → high → max). Displays available models and current selection.

Models available:
- `claude-opus-4-6` — strongest reasoning, highest cost. Default for fleet agents.
- `claude-opus-4-6[1m]` — Opus with 1M context window (Max/Team/Enterprise plans)
- `claude-sonnet-4-6` — fast, good for standard implementation work
- `claude-sonnet-4-6[1m]` — Sonnet with 1M context
- `claude-haiku-4-5` — fastest, cheapest, for simple tasks

## When Fleet Agents Should Use It

**Most agents won't use this directly.** The orchestrator's model_selection.py chooses the model at dispatch time based on task complexity, story points, and agent role:
- Complex/critical tasks → opus
- Security/architecture → opus (always)
- Standard implementation → sonnet
- Simple structured → hermes-3b (when LocalAI routing is live)

**When an agent SHOULD use /model:**
- Switching to opus for a difficult subtask within a session (override dispatch selection)
- Switching to sonnet for routine work after a complex section
- Checking which model they're currently running

## Effort Levels

| Level | Persistence | When to Use |
|-------|-------------|-------------|
| low | Across sessions | Simple updates, doc changes |
| medium | Across sessions (default) | Standard implementation |
| high | Across sessions | Architecture decisions, complex debugging |
| max | Current session ONLY | Critical security analysis, complex architecture (Opus only) |
| auto | Reset to default | Return to default after override |

**Keyword trigger:** Include "ultrathink" in a prompt for one-turn high effort without changing the persistent setting.

## Relationships

- SET BY: orchestrator dispatch (model_selection.py chooses per task)
- OVERRIDES: agent can change within session (dispatch chose sonnet, agent switches to opus for a complex part)
- CONNECTS TO: model_selection.py (select_model_for_task — SP + type + role → model)
- CONNECTS TO: injection-profiles.yaml (model determines injection profile: opus-1m → full, sonnet → condensed, localai → minimal)
- CONNECTS TO: LaborStamp (model field records which model produced the work)
- CONNECTS TO: confidence_tier (auto-derived: opus=expert, sonnet=standard, localai=trainee)
- CONNECTS TO: review_gates.py (trainee tier → deeper review pipeline)
- CONNECTS TO: challenge system (trainee/community tier → mandatory challenges)
- CONNECTS TO: /effort command (effort slider adjusts thinking depth)
- CONNECTS TO: /fast command (fast mode = same Opus with speed-optimized API)
- CONNECTS TO: ANTHROPIC_MODEL env var (gateway sets initial model)
- CONNECTS TO: CLAUDE_CODE_EFFORT_LEVEL env var (persistent effort setting)
