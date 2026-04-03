# /compact

**Type:** Claude Code Built-In Command
**Category:** Session Management
**Available to:** ALL agents

## What It Actually Does

Compresses the conversation context while preserving specified content. Takes an optional focus instruction that tells Claude what to prioritize keeping. Claude reads the full conversation, generates a summary that preserves the specified focus, and replaces the conversation history with that summary. Context usage drops significantly — from 70%+ down to 10-20%.

The instruction matters. `/compact retain task context and contributions` produces a very different summary than `/compact` alone. Without instruction, Claude decides what's important. With instruction, you control what survives.

CLAUDE.md files survive compaction automatically — they're re-read from disk after compact, not from conversation memory. This is why agent identity (IDENTITY.md, SOUL.md, CLAUDE.md) persists even through aggressive compaction.

## When Fleet Agents Should Use It

**Context approaching 70%:** The organic tipping point. Agent should start thinking about what to preserve. Not forced — natural transition.

**Between logical tasks:** After fleet_task_complete, before starting new work. Clean context for fresh task.

**Before rate limit rollover:** PO discovered that high-context sessions cause a 20% quota spike on the first message in a new rate limit window. Compacting before rollover prevents this. Session manager (brain Step 10) may force-compact agents near rollover.

**After long investigation/analysis:** These stages read lots of code, filling context with file contents. Compact before transitioning to reasoning/work — keep findings, drop the raw file reads.

**When context feels sluggish:** Large context means more tokens per API call (8-12 calls per command, each carrying full context). Compaction directly reduces cost per operation.

## What to Preserve (per role)

| Role | Focus Instruction |
|------|------------------|
| Engineer in WORK | "retain task requirement, accepted plan, contributions from colleagues, commit history" |
| Architect in REASONING | "retain design options explored, decision rationale, architecture constraints" |
| Fleet-ops in REVIEW | "retain task requirement, acceptance criteria, review progress, findings" |
| PM in SPRINT | "retain sprint plan, task assignments, blockers, pending gates" |
| Any agent | "retain current task context, stage, readiness, what I was doing" |

## What NOT to Do

- Don't compact in the middle of a complex reasoning chain — you'll lose the reasoning
- Don't compact without specifying what to retain — you may lose critical context
- Don't compact just because context is at 50% — only when it's actually needed
- Don't compact repeatedly in quick succession — each compact costs tokens itself

## Relationships

- TRIGGERED BY: session_manager.py (brain Step 10 — force compact near rollover)
- PRESERVED THROUGH: CLAUDE.md, IDENTITY.md, SOUL.md (re-read from disk)
- PRESERVED THROUGH: claude-mem observations (searchable after compact)
- HOOKS: PreCompact (save state before), PostCompact (verify after)
- CONNECTS TO: CW-03 (strategic compaction protocol per role)
- CONNECTS TO: CW-08 (pre-rollover preparation — compact at 85% rate limit)
- CONNECTS TO: /context command (inspect context before deciding to compact)
- CONNECTS TO: smart artifacts dumping (§35.7 — dump heavy context to artifacts instead of compacting)
- CONNECTS TO: agent_lifecycle.py — consecutive HEARTBEAT_OK after compact may trigger IDLE state
- COST: compaction itself costs tokens (summary generation). Allow >90% budget specifically for compaction cost — it saves more than it spends.

## Context Awareness Integration

The two parallel countdowns affect when to compact:
1. **Context remaining** — 7% = prepare (think about preserving), 5% = force (save + compact now)
2. **Rate limit remaining** — 85% = no new heavy dispatches, 90% = force compact heavy contexts

Aggregate fleet math: 5 agents × 200K context near rollover = 1M token spike risk. Brain staggers compactions — doesn't compact all 10 agents simultaneously (compaction itself costs tokens).
