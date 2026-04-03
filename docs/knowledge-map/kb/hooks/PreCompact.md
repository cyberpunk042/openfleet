# PreCompact

**Type:** Claude Code Hook (lifecycle event)
**Category:** Session Lifecycle (fires before context compaction)
**Handler types:** command, http, prompt, agent
**Can block:** NO — compaction proceeds regardless
**Matcher:** `manual` (user triggered /compact), `auto` (automatic at ~95% capacity)

## What It Actually Does

Fires BEFORE context compaction — the moment between "full context" and "compressed context." This is the LAST CHANCE to save critical state before it's potentially lost in compression. Claude will summarize the conversation, and details not included in the summary are gone.

The handler can extract key information and persist it to durable storage (claude-mem, .claude/memory/, files on disk) before the compression happens.

## Handler Input

```json
{
  "hook_event_name": "PreCompact",
  "session_id": "...",
  "trigger": "manual",  // or "auto"
  "agent_name": "software-engineer"
}
```

## Handler Output

```json
// Acknowledged (state saved externally):
{}
```

The handler saves state to EXTERNAL storage (not conversation memory, which is about to be compressed):
- Write key decisions to .claude/memory/ files
- Write artifact progress to disk
- Post to board memory (persists outside session)
- Record in claude-mem SQLite (survives compaction)

## Fleet Use Case: Context Survival

```
PreCompact fires (user called /compact or auto at 95%)
├── Save critical state:
│   ├── Current task ID + stage + readiness + progress
│   ├── Key decisions made this session (rationale, not just outcome)
│   ├── Artifact fields filled since last save
│   ├── Contributions received and referenced
│   ├── Plan steps completed vs remaining
│   └── What the agent was working on (for recovery)
├── Write to .claude/memory/:
│   ├── "Working on task abc123, stage: work, progress: 50%"
│   ├── "Decided to use observer pattern because..."
│   └── "Received design_input from architect: ..."
├── Post to board memory:
│   ├── tags: [trail, task:{id}, pre_compact]
│   └── content: "Pre-compact snapshot: stage=work, progress=50%, 3 commits"
└── Agent recovers from memory at next SessionStart
    (or reads from claude-mem search)
```

## Auto vs Manual Trigger

| Trigger | When | Agent Should |
|---------|------|-------------|
| `manual` | Agent called /compact | Agent chose to compact — they know what to preserve. Hook saves system state (task ID, stage). Agent handles content preservation via /compact instruction. |
| `auto` | Context hit ~95% capacity | Automatic — agent may not have prepared. Hook saves EVERYTHING critical. This is why PreCompact is essential: auto-compact happens without warning. |

## What to Save vs What CLAUDE.md Already Provides

After compaction, Claude re-reads CLAUDE.md and other agent files from disk. So:

**DON'T need to save (survives via disk re-read):**
- Agent identity (IDENTITY.md)
- Agent rules (CLAUDE.md)
- Agent values (SOUL.md)
- Tool reference (TOOLS.md)
- Colleague knowledge (AGENTS.md)
- Fleet state (fleet-context.md — brain refreshes every 30s)

**DO need to save (lost in compaction):**
- Current task context (what am I working on, what have I done)
- Decisions made (why I chose approach X over Y)
- Contributions received (what colleagues provided)
- Progress within plan (steps 1-3 done, step 4 in progress)
- What to tell /compact to preserve (if agent can influence the summary)

## Relationships

- FIRES BEFORE: /compact or auto-compact at ~95% (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE)
- CANNOT BLOCK: compaction proceeds regardless
- PAIRED WITH: PostCompact (verify state after compaction)
- PAIRED WITH: Stop hook (Stop saves per-turn, PreCompact saves pre-compression)
- CONNECTS TO: claude-mem (save observations that survive compaction)
- CONNECTS TO: .claude/memory/ (file-based state that survives compaction)
- CONNECTS TO: board memory (post trail event that persists outside session)
- CONNECTS TO: CW-03 (strategic compaction protocol per role)
- CONNECTS TO: CW-04 (efficient regathering after compaction)
- CONNECTS TO: session_manager.py (brain may force-compact — hook saves state first)
- CONNECTS TO: SessionStart hook (trigger="compact" — re-injects after compaction)
- CONNECTS TO: smart artifacts dumping (§35.7 — dump heavy context to artifacts before compact)
- KEY INSIGHT: PreCompact is the INSURANCE POLICY. Auto-compact can happen anytime at 95%. Without this hook, critical task state is lost. With it, state is saved to durable storage and recovered via SessionStart + claude-mem search.
