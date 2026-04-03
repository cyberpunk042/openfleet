# /clear

**Type:** Claude Code Built-In Command
**Category:** Session Management
**Available to:** ALL agents
**Aliases:** /reset, /new

## What It Actually Does

Clears conversation history completely and frees context. The session restarts fresh — no conversation history, no tool results, no file reads from previous turns. CLAUDE.md and agent files are re-read from disk (they always survive clears). claude-mem observations persist (they're in SQLite, not session memory).

This is MORE aggressive than /compact. Compact summarizes and keeps a compressed version. Clear DELETES everything and starts over.

## When Fleet Agents Should Use It

**Between completely unrelated tasks:** After fleet_task_complete on task A, before starting task B in a different project/domain. No context from task A is useful for task B — clear is faster than compact.

**After session contamination:** If context is corrupted with wrong assumptions, failed approaches, or stale data that /compact would preserve in summary form. Clear gives a genuinely fresh start.

**After gateway prune:** When the orchestrator prunes an agent (doctor response to 3+ corrections), the agent gets a fresh session. The agent should /clear if any previous context leaked through.

**Sprint boundary:** PM starting a new sprint — clear old sprint context, fresh start for new sprint planning.

## What Survives vs What's Lost

| Survives /clear | Lost on /clear |
|----------------|---------------|
| IDENTITY.md (re-read from disk) | Conversation history |
| SOUL.md (re-read) | Tool results (file reads, searches) |
| CLAUDE.md (re-read) | Reasoning chains |
| TOOLS.md, AGENTS.md (re-read) | Decisions made in conversation |
| HEARTBEAT.md (re-read) | Context built up over turns |
| fleet-context.md (re-read, fresh from brain) | |
| task-context.md (re-read, fresh from brain) | |
| claude-mem observations (in SQLite) | |
| .claude/memory/ files (on disk) | |
| Git state (commits, branches) | |

## When NOT to Use It

- Don't /clear in the middle of a task — you'll lose your working context
- Don't /clear when /compact would suffice — compact preserves key knowledge
- Don't /clear reflexively — only when fresh start is genuinely needed

## Relationships

- MORE AGGRESSIVE THAN: /compact (compact preserves summary, clear deletes all)
- CONNECTS TO: SessionEnd hook (fires on clear)
- CONNECTS TO: SessionStart hook (fires after clear — re-injects context)
- CONNECTS TO: agent_lifecycle.py (clear may reset agent state)
- CONNECTS TO: claude-mem (observations survive — searchable after clear)
- CONNECTS TO: .claude/memory/ (files survive — re-loaded at session start)
- CONNECTS TO: orchestrator prune (doctor prunes → fresh session → similar to clear)
- CONNECTS TO: CW-04 (efficient regathering — after clear, agent uses memory to recover)
- WHAT RECOVERS CONTEXT AFTER CLEAR: agent files (layers 1-8), claude-mem search, .claude/memory/ files, fleet-context.md (brain-written), task-context.md (brain-written)
