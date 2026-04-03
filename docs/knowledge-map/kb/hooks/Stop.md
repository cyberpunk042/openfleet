# Stop

**Type:** Claude Code Hook (lifecycle event)
**Category:** Post-Action (fires when Claude finishes responding)
**Handler types:** command, http, prompt, agent
**Can block:** YES — can prevent Claude from stopping (forces continuation)

## What It Actually Does

Fires when Claude finishes a response — before the turn ends and control returns to the user (or the session idles). The handler can: observe (save state, record trail), react (trigger notifications), or BLOCK the stop (force Claude to continue — this is the review gate pattern).

Blocking a Stop is powerful and dangerous: it forces Claude to keep working, potentially entering a loop. The codex-plugin-cc review gate uses this to block completion until an independent review passes.

## Handler Input

```json
{
  "hook_event_name": "Stop",
  "session_id": "...",
  "agent_name": "software-engineer"
}
```

## Handler Output

```json
// Observed, no intervention:
{}

// Block the stop (force continuation):
// exit code 2, stderr = feedback
// "Independent review found 3 issues. Address them before completing."
```

## Fleet Use Cases

### Primary: Session State Save

```
Stop fires (Claude finished responding)
├── Save key decisions made this turn to persistent storage
│   ├── Write to .claude/memory/ if significant decisions
│   ├── Update trail: "turn completed" event
│   └── Record what agent was working on (for context recovery)
├── Return: {} (don't block — just observe)
└── State saved for recovery after compact/clear/prune
```

This ensures every turn leaves a recoverable state. Even if the session is pruned by the doctor or compacted by the brain, the Stop hook saved the critical state first.

### Secondary: Review Gate Pattern (from codex concept)

```
Stop fires (Claude finished responding after fleet_task_complete)
├── Independent quality check:
│   ├── Run automated pattern checks on the diff
│   ├── Or query a different model for review (LocalAI as independent reviewer)
│   ├── Or run /security-review automatically
├── Issues found?
│   ├── YES → exit code 2, stderr: "3 issues found. Address before completing."
│   │   └── Claude receives feedback, must address issues, tries to stop again
│   └── NO → {} (stop allowed, work is approved)
```

This is the codex-plugin-cc review gate concept implemented natively. Instead of using OpenAI's Codex, we use our own infrastructure:
- LocalAI hermes/qwen as the independent reviewer (free)
- Automated pattern checks from challenge_automated.py (free)
- /security-review for security-sensitive changes

### Caution: Stop Loops

Blocking Stop creates a LOOP: Claude responds → Stop hook blocks → Claude addresses issues → responds again → Stop hook checks again → blocks again (if issues remain). This can:
- Drain tokens rapidly (each cycle = full context re-sent)
- Create infinite loops if the check is too strict or the fix introduces new issues
- The codex review gate has this exact problem (documented in codex-plugin-cc KB entry)

**Mitigation:** Include a max iteration count. After 3 blocked stops, allow the stop and flag for human review instead.

## Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "python -m fleet.hooks.stop_save_state",
        "timeout": 5000
      }
    ]
  }
}
```

## Relationships

- FIRES: when Claude finishes responding (every turn)
- CAN BLOCK: yes — forces Claude to continue (review gate pattern)
- IMPLEMENTS: session state save (every turn → recoverable state)
- IMPLEMENTS: review gate pattern (independent quality check before completion)
- CONNECTS TO: codex-plugin-cc (codex review gate uses Stop hook internally)
- CONNECTS TO: PreCompact hook (Stop saves state, PreCompact saves before compact specifically)
- CONNECTS TO: trail system (trail.turn.completed event)
- CONNECTS TO: claude-mem (claude-mem's Summary hook fires nearby — captures session summaries)
- CONNECTS TO: challenge_automated.py (automated checks could run at Stop)
- CONNECTS TO: session_manager.py (stop is where context size is evaluated for dump decisions)
- CONNECTS TO: agent_lifecycle.py (stop with no work → HEARTBEAT_OK → idle tracking)
- CONNECTS TO: fleet_task_complete (if agent completed task, Stop hook is the last gate before done)
- DANGER: blocking Stop can create runaway loops. Always include max iterations.
