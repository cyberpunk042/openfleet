# /context

**Type:** Claude Code Built-In Command
**Category:** Context & Cost
**Available to:** ALL agents

## What It Actually Does

Visualizes context window usage as a colored grid with optimization suggestions. Shows what's consuming context: system prompt (CLAUDE.md, IDENTITY.md, etc.), conversation history, tool results, file reads. Colors indicate usage levels: green (<70%), yellow (70-89%), red (90%+).

This is the agent's AWARENESS tool — it answers "how much room do I have?" and "what's using all my context?"

## When Fleet Agents Should Use It

**Before heavy codebase reads:** About to read a 500-line module? /context first. If already at 60%, that read will push to 70%+. Maybe compact first, or read selectively.

**When context feels sluggish:** Large context = more tokens per API call (Claude makes 8-12 API calls per user command, each carrying FULL context). If responses feel slow, /context shows why.

**After compaction:** Verify what was preserved. Did the compact retain what you need? /context shows the new context composition.

**Before fleet_task_complete:** About to trigger the 12+ operation chain? Check if you have enough context headroom. The chain involves multiple tool calls, each consuming context.

**At 70% context (organic tipping point):** PO's context endgame model: 100-30% = normal work, 30-7% = progressive mindfulness, 7% = prepare extraction, 5% = final extraction. /context tells you where you are.

## What It Shows

```
Context usage: 45% ████████████░░░░░░░░░░░░ 450K / 1M

Breakdown:
  System prompt (CLAUDE.md + agent files): 12%
  Conversation history: 28%
  Tool results (file reads, search): 42%
  Other: 18%

Suggestions:
  - Consider /compact to reduce tool result history
  - Large file reads at turns 3, 7, 12 could be trimmed
```

## Per-Role Awareness

| Role | Context Concern | Why |
|------|----------------|-----|
| Architect | Investigation fills context with file reads | Reading many files to explore options |
| Engineer | Implementation fills with code reads + edits | Progressive file operations |
| PM | Sprint planning reads many task states | Board-wide task scanning |
| Fleet-ops | Review reads PR diff + trail + requirement | Multiple data sources per review |

## Relationships

- CONNECTS TO: /compact (context too high → compact)
- CONNECTS TO: /cost (context size affects token cost per operation)
- CONNECTS TO: /usage (rate limit usage is the OTHER countdown)
- CONNECTS TO: session_manager.py (brain Step 10 — aggregate fleet context math)
- CONNECTS TO: CW-01 (know context window size — 200K or 1M)
- CONNECTS TO: CW-05 (prevent context bloat — .claudeignore)
- CONNECTS TO: CW-09 (1M context managed more aggressively than 200K)
- CONNECTS TO: injection-profiles.yaml (profile selected based on model + context window)
- CONNECTS TO: CLAUDE.md Section 7 (context awareness — both countdowns)
- CONNECTS TO: statusline (context % always visible in statusline bar)
- THE TWO COUNTDOWNS: /context shows context remaining. /usage shows rate limit remaining. Both matter. Heavy context near rate limit rollover = 20% spike.
