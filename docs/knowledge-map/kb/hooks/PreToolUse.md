# PreToolUse

**Type:** Claude Code Hook (lifecycle event)
**Category:** Pre-Action (can BLOCK or MODIFY tool calls)
**Handler types:** command (shell), http, prompt (LLM), agent (subagent)
**Can block:** YES — return deny to prevent tool execution

## What It Actually Does

Fires BEFORE any tool executes. Receives the tool name and input parameters as JSON on stdin. Can: allow (tool proceeds), deny (tool blocked with feedback message), ask (prompt user for permission), defer (let other handlers decide), or modify the input parameters before the tool runs.

This is the MOST POWERFUL enforcement hook — it sits between the agent's intent and the action. Everything the agent does passes through PreToolUse first.

## Matcher

Matches by tool name. Can target specific tools or use wildcards:
- `"match": ["Bash"]` — only fires for Bash commands
- `"match": ["Write", "Edit"]` — fires for file modifications
- `"match": ["*"]` — fires for ALL tool calls (expensive — use sparingly)

## Handler Input (JSON on stdin)

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "git reset --hard"
  },
  "session_id": "...",
  "agent_name": "software-engineer"
}
```

## Handler Output

```json
// Allow (tool proceeds normally):
{"allow": true}

// Deny (tool blocked, agent sees message):
{"deny": true, "message": "Destructive command blocked: git reset --hard"}

// Allow with modified input:
{"allow": true, "input": {"command": "git status"}}

// Inject additional context (agent sees this):
{"allow": true, "additionalContext": "Warning: this file is in a protected directory"}
```

Exit code 0 = success (parse JSON). Exit code 2 = blocking error (stderr as feedback). Other = non-blocking, tool proceeds.

## Fleet Use Cases (3 layers)

### Layer 1: Destructive Command Protection (safety-net plugin)

```
PreToolUse fires for Bash("rm -rf /project")
├── safety-net pattern match: "rm -rf" → DESTRUCTIVE
├── Return: {deny: true, message: "⚠️ Blocked: rm -rf"}
└── Agent sees warning, reconsiders
```

This is the safety-net plugin's implementation — a PreToolUse handler that pattern-matches destructive commands.

### Layer 2: Methodology Stage Enforcement

```
PreToolUse fires for Write("fleet/core/new_module.py")
├── Custom handler reads agent's current stage from context
├── Stage = "conversation" → file writing not allowed
├── Return: {deny: true, message: "Cannot write files in conversation stage. Complete the conversation protocol first."}
└── Agent must advance to analysis+ stage before producing files
```

Currently, stage enforcement is in MCP tools.py (_check_stage_allowed) but only covers fleet_commit and fleet_task_complete. A PreToolUse hook would enforce on ALL file operations — Write, Edit, Bash file operations.

### Layer 3: Contribution Gate

```
PreToolUse fires for fleet_task_complete
├── Custom handler checks: are all required contributions received?
├── contributions.check_contribution_completeness() → missing: [qa_test_definition]
├── Return: {deny: true, message: "Missing required contributions: qa_test_definition from QA. Use fleet_request_input to request it."}
└── Agent cannot complete until all contributions arrive
```

## Configuration

```json
// In hooks.json or .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python -m fleet.hooks.pre_tool_gate",
        "match": ["Bash", "Write", "Edit"],
        "timeout": 5000
      }
    ]
  }
}
```

Multiple handlers can be registered — they run in order. First deny wins.

## Relationships

- FIRES BEFORE: every matched tool execution
- IMPLEMENTED BY: safety-net plugin (destructive command patterns)
- IMPLEMENTS: anti-corruption Line 1 (structural prevention — physically blocks wrong actions)
- CONNECTS TO: methodology.py (stage checking for file operations)
- CONNECTS TO: contributions.py (contribution gate for fleet_task_complete)
- CONNECTS TO: _check_stage_allowed in tools.py (current stage enforcement — hook would be broader)
- CONNECTS TO: agent_lifecycle.py (hook could check agent health before tool execution)
- CONNECTS TO: trail system (blocked operations should be recorded as trail events)
- CONNECTS TO: doctor.py (repeated blocks → pattern detection)
- CONNECTS TO: security-guidance plugin (separate hook for insecure CODE patterns)
- ENFORCEMENT HIERARCHY: PreToolUse hook (structural, can't bypass) > _check_stage_allowed in MCP (tool-level) > CLAUDE.md rules (can be ignored)
- PERFORMANCE: command handlers should complete in <100ms. Prompt/agent handlers are slower.
- CRITICAL INSIGHT: hooks are DETERMINISTIC. Unlike skills or rules that Claude might ignore, hooks fire EVERY TIME and their deny response CANNOT be overridden by the agent.
