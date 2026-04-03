# PostToolUse

**Type:** Claude Code Hook (lifecycle event)
**Category:** Post-Action (observe and react after tool succeeds)
**Handler types:** command, http, prompt, agent
**Can block:** YES — can reject the tool result (exit code 2)

## What It Actually Does

Fires AFTER a tool executes SUCCESSFULLY. Receives the tool name, input, AND output as JSON. Can observe (log, record), react (trigger side effects), or reject (exit code 2 = treat as tool failure). Does NOT fire on tool failures (that's PostToolUseFailure).

This is the OBSERVATION hook — it sees what actually happened, not what was planned.

## Matcher

Same as PreToolUse — matches by tool name. `["*"]` matches all tools.

## Handler Input

```json
{
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/home/jfortin/openclaw-fleet/fleet/core/models.py",
    "content": "..."
  },
  "tool_output": {
    "status": "success",
    "bytes_written": 4521
  },
  "session_id": "...",
  "agent_name": "software-engineer"
}
```

## Handler Output

```json
// Observed, no intervention:
{}  // empty = acknowledged

// Inject context for agent to see:
{"additionalContext": "pyright found 2 type errors in this file after your edit"}

// Reject the result (treated as failure):
// (exit code 2, stderr message shown to agent)
```

## Fleet Use Cases

### Primary: Automatic Trail Recording

```
PostToolUse fires for fleet_commit(files, message)
├── trail_record handler:
│   ├── Extract: tool=fleet_commit, agent=software-engineer, sha=abc1234
│   ├── Post to board memory:
│   │   content: "[trail] trail.commit.created: software-engineer sha=abc1234"
│   │   tags: [trail, task:{id}, trail.commit.created, agent:software-engineer]
│   └── Complete in <50ms (non-blocking)
└── Agent doesn't see anything (silent observation)
```

This replaces manual trail recording in each MCP tool. Instead of adding try/except trail code to every tool handler, ONE PostToolUse hook records trail for ALL tool calls automatically. Never missed, never forgotten.

### Secondary: Code Quality Feedback

```
PostToolUse fires for Write("fleet/core/models.py")
├── pyright-lsp detects type errors (automatic, via LSP integration)
├── PostToolUse handler checks for diagnostics
├── If errors found:
│   └── Return: {additionalContext: "⚠ pyright: 2 type errors introduced. Check before committing."}
└── Agent sees the warning in their context
```

### Tertiary: Plane Sync Trigger

```
PostToolUse fires for fleet_commit
├── If task has plane_issue_id:
│   ├── Post commit summary as Plane issue comment
│   └── Update Plane labels (readiness if artifact completeness changed)
```

## Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "python -m fleet.hooks.post_tool_trail",
        "match": ["*"],
        "timeout": 3000
      }
    ]
  }
}
```

## Relationships

- FIRES AFTER: every matched SUCCESSFUL tool execution
- DOES NOT FIRE: on tool failure (that's PostToolUseFailure hook)
- IMPLEMENTS: automatic trail recording (every tool call → audit event)
- CONNECTS TO: trail_recorder.py (33 trail event types recorded via this hook)
- CONNECTS TO: LaborStamp mini-signatures (agent + model + context% per trail event)
- CONNECTS TO: pyright-lsp (type diagnostics after Write/Edit)
- CONNECTS TO: plane_sync.py (sync after fleet_commit, fleet_task_complete)
- CONNECTS TO: fleet-ops review Step 4 (trail verified using data from this hook)
- CONNECTS TO: accountability generator (trail completeness from this hook's data)
- CONNECTS TO: doctor.py (hook data feeds disease detection — tool call patterns reveal laziness, scope creep)
- PERFORMANCE: `["*"]` matcher means this fires for EVERY tool call. Handler MUST be fast (<100ms). Use command type (shell script), not prompt/agent type (LLM call).
- KEY INSIGHT: PostToolUse is the data pipeline for the trail system. Without it, trail recording is manual and unreliable. With it, every tool call is automatically recorded — the foundation for accountability, review, and immune system detection.
