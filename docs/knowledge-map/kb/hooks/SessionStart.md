# SessionStart

**Type:** Claude Code Hook (lifecycle event)
**Category:** Session Lifecycle
**Handler types:** command, http, prompt, agent
**Can block:** NO — session starts regardless, but handler output is injected
**Matcher:** `startup`, `resume`, `clear`, `compact` (fires on all session start types)

## What It Actually Does

Fires when a Claude Code session begins or resumes. This includes: fresh session start (`startup`), resuming a previous session (`resume`), after /clear (`clear`), and after /compact (`compact`). The handler can inject additional context into the session via `additionalContext` in the output.

This is WHERE the knowledge map becomes ACTIVE. The SessionStart hook reads the agent's role, determines what knowledge to inject from the map, selects the appropriate injection profile (opus/sonnet/localai), and injects the assembled content into the session. The agent wakes up already knowing what it needs to know.

## Handler Input

```json
{
  "hook_event_name": "SessionStart",
  "session_id": "...",
  "agent_name": "software-engineer",
  "trigger": "startup",  // or "resume", "clear", "compact"
  "cwd": "/home/jfortin/openclaw-fleet"
}
```

## Handler Output

```json
{
  "additionalContext": "## Fleet Context\nYou are Software Engineer in Fleet Alpha.\n\nYour current task: ...\n\nYour skills: /feature-implement, /feature-test, ...\n\n..."
}
```

The `additionalContext` string is injected into the session's system prompt. The agent sees this content as part of their starting context — they don't know it came from a hook.

## Fleet Use Cases

### Primary: Knowledge Map Context Injection

```
SessionStart fires (agent session begins)
├── Read agent_name from hook input
├── Determine agent role from agent-tooling.yaml
├── Determine model + context window → select injection profile
│   ├── opus-1m → full detail from map
│   ├── sonnet-200k → condensed
│   ├── localai-8k → minimal
│   └── heartbeat → none (fleet-context.md handles it)
├── Read intent-map.yaml → what to inject for this role
├── Assemble content from knowledge map branches:
│   ├── Agent manual (mission, tools, key rules)
│   ├── Methodology (current stage instructions)
│   ├── Skills (available per-stage recommendations)
│   ├── Commands (relevant per-stage)
│   └── Context awareness (countdowns if applicable)
├── Return: {additionalContext: assembled_content}
└── Agent starts with map-driven knowledge injected
```

This is the mechanism that makes the knowledge map LIVE. Without this hook, the map is just files. With it, the right knowledge reaches the right agent at the right time.

### Secondary: claude-mem Context Recovery

claude-mem's SessionStart hook also fires (separate handler):
```
├── Query SQLite for recent summaries (10) + observations (50)
├── Inject previous session knowledge
└── Agent recovers cross-session memory
```

Both hooks fire — knowledge map injection AND claude-mem recovery. The agent gets fleet knowledge + personal memory.

### Tertiary: Environment Setup

```
├── Set FLEET_AGENT environment variable
├── Set FLEET_DIR path
├── Initialize fleet MCP server connection
└── Load agent-specific settings
```

## Trigger Types

| Trigger | When | Implications |
|---------|------|-------------|
| `startup` | Fresh session start | Full injection — agent knows nothing |
| `resume` | Resuming previous session | Lighter injection — agent has prior context |
| `clear` | After /clear command | Full injection — conversation history cleared |
| `compact` | After /compact | Targeted injection — verify critical context survived |

## Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python -m fleet.hooks.session_start_inject",
        "timeout": 10000
      }
    ]
  }
}
```

Timeout is generous (10s) because map assembly may involve reading multiple files.

## Relationships

- FIRES ON: every session start (startup, resume, clear, compact)
- CANNOT BLOCK: session starts regardless — but injected context shapes behavior
- IMPLEMENTS: knowledge map activation (map content → agent context)
- IMPLEMENTS: claude-mem recovery (cross-session memory injection)
- CONNECTS TO: map_navigator.py (reads intent-map, selects profile, assembles content)
- CONNECTS TO: injection-profiles.yaml (profile determines depth of injection)
- CONNECTS TO: intent-map.yaml (role + stage → what to inject)
- CONNECTS TO: claude-mem plugin (separate SessionStart handler for memory recovery)
- CONNECTS TO: agent_lifecycle.py (session start = agent potentially waking from IDLE/SLEEPING)
- CONNECTS TO: heartbeat_gate.py (brain evaluates BEFORE session starts — if silent, no session created)
- CONNECTS TO: InstructionsLoaded hook (fires after SessionStart — can augment CLAUDE.md with map data)
- CONNECTS TO: PostCompact hook (after compact trigger, SessionStart fires with trigger="compact")
- CONNECTS TO: /clear command (fires with trigger="clear" — full re-injection)
- KEY INSIGHT: this is the BRIDGE between static knowledge (map files on disk) and dynamic context (what the agent actually sees). Everything in the knowledge map tree ultimately flows through this hook to reach agents.
