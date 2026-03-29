# Fleet Operations Protocol — Complete System Design

## Principle

The human is the leader. The fleet operates autonomously within boundaries.
The human should never do repetitive work. Every manual step is a bug.

---

## The Complete Task Lifecycle

Every state transition has automation. Nothing sits idle.

```
HUMAN creates task (or lead agent creates subtask)
    ↓
INBOX
    ↓ auto: dispatch to assigned agent via chat.send
IN_PROGRESS
    ↓ agent: works in worktree, commits, pushes branch, creates PR
    ↓ agent: posts progress comments with URLs
    ↓ agent: posts PR URL to task comment + board memory + channel
REVIEW
    ↓ auto: QA agent runs tests on PR branch
    ↓ auto: architect agent reviews if flagged
    ↓ auto: results posted as task comments
    ↓ if all pass: notify human in channel "PR ready: <URL>"
    ↓
HUMAN approves in MC (or merges PR directly on GitHub)
    ↓
DONE
    ↓ auto: detect PR merge → move task to done (if not already)
    ↓ auto: detect task done → merge PR (if not already)
    ↓ auto: cleanup worktree
    ↓ auto: post summary to channel
```

### State Transition Automation

| Transition | Trigger | Action |
|-----------|---------|--------|
| → inbox | Task created | Auto-dispatch if agent assigned |
| inbox → in_progress | Agent accepts | Agent posts acceptance comment |
| in_progress (progress) | Agent working | Agent posts progress comments with refs |
| in_progress → review | Agent completes | Push branch, create PR, post URLs |
| review (checks) | Task enters review | QA agent runs tests, architect reviews |
| review → done | Human approves in MC | Auto-merge PR if not merged |
| review → done | Human merges PR on GitHub | Webhook detects merge, moves task to done |
| done (cleanup) | Task reaches done | Cleanup worktree, post summary |

### What the Human NEVER Does

- Manually push agent branches
- Manually create PRs
- Manually copy PR URLs into task comments
- Manually run tests on agent branches
- Manually move tasks that should auto-transition
- Manually clean up worktrees
- Check multiple places for status (everything flows to one channel)

### What the Human DOES

- Create tasks (or approve lead agent's task proposals)
- Review PRs (code review on GitHub)
- Approve/reject in MC (for gated tasks)
- Merge PRs (click merge on GitHub — or auto-merge if configured)
- Interact with agents via channel (@mention)
- Set priorities and direction

---

## Messaging Protocol

### Three Surfaces, Three Purposes

| Surface | Purpose | Who writes | Who reads |
|---------|---------|-----------|-----------|
| **MC Task Comments** | Task-specific updates, results, PRs | Agents, human | Human (per-task detail) |
| **MC Board Memory** | Cross-task knowledge, decisions, fleet status | Agents, human | All agents, human |
| **Channel (IRC/Discord)** | Real-time alerts, URLs, human↔agent interaction | Agents, human | Human (primary), agents |

### MC Task Comment Rules

Every task comment MUST be one of:
- **Acceptance**: "Starting work: <brief plan>"
- **Progress**: "Progress: <what was done>. Next: <what's next>"
- **Blocker**: "**Blocked**: <reason>. Needed: <what would unblock>"
- **Completion**: "**Completed** PR: <URL> Branch: <ref> Commits: <N> Files: <list> Summary: <what>"
- **Review result**: "**QA**: <pass/fail> <details>" or "**Review**: <approved/changes needed>"

No freeform text dumps. Structured, scannable, with URLs.

### MC Board Memory Rules

Board memory is for PERSISTENT KNOWLEDGE that spans tasks:
- **Decisions**: "DECISION: We use X because Y" — tags: [decision, <project>]
- **Architecture**: "ARCH: Component X connects to Y via Z" — tags: [architecture, <project>]
- **PR notifications**: "PR Ready: <URL> for <project>" — tags: [pr, review, <project>]
- **Blockers**: "BLOCKER: <what> blocks <what>" — tags: [blocker, <project>]
- **Human directives**: human posts instructions — tags: [chat, directive]

NOT for: progress updates (those go in task comments), chatter, duplicate info.

### Channel Message Rules (IRC/Discord)

The channel is the HUMAN'S WINDOW into the fleet. Messages must be:
- **Actionable**: human should know what to do (review PR, unblock agent, etc.)
- **Link-rich**: every reference is a clickable URL
- **Concise**: one line per event, details in links

Message format:
```
[<agent>] <event>: <title> — <URL>
```

Events:
```
[software-engineer] STARTED: Fix test collection errors — http://localhost:3000/tasks/3402f526
[software-engineer] PR READY: Fix test collection — https://github.com/.../pull/3
[qa-engineer] TESTS PASS: fleet/sw-eng/3402f526 — 604/604 passing
[architect] REVIEW OK: fleet/sw-eng/3402f526 — no design concerns
[fleet] MERGED: Fix test collection — https://github.com/.../pull/3
[fleet] TASK DONE: Fix test collection errors — cleaned up worktree
```

Human can respond in channel:
```
<human> @architect review the NNRT pipeline changes before we merge
<human> @software-engineer hold on that PR, I want to check something
<human> merge PR #3
```

---

## MC Dashboard Hygiene

### Custom Fields (per board)

| Field | Type | Set by | When |
|-------|------|--------|------|
| project | text | create-task.sh | Task creation |
| branch | text | Agent | Task completion |
| pr_url | url | Agent | PR creation |
| worktree | text | dispatch-task.sh | Task dispatch |

### Tags

| Tag | Purpose |
|-----|---------|
| project:<name> | Which project (nnrt, aicp, fleet) |
| type:<type> | Task type (feature, fix, review, docs, chore) |
| agent:<name> | Assigned agent |
| needs-review | Human review needed |
| auto-merge | Can be auto-merged after checks |

### Board Views

- **Active**: status = in_progress (what agents are working on now)
- **Review**: status = review (what needs human attention)
- **By Project**: grouped by project tag
- **Blockers**: tagged with blocker

---

## Review & Merge Automation

### When Task Moves to Review

1. **QA agent** is notified (via board memory or direct dispatch)
   - Runs project tests on the PR branch
   - Posts result as task comment: "QA: PASS (604/604)" or "QA: FAIL (3 failures)"
2. **Architect agent** reviews if task is tagged `needs-review`
   - Reviews diff for design concerns
   - Posts: "Review: Approved" or "Review: Changes needed — <details>"
3. Results summarized in channel:
   ```
   [qa-engineer] TESTS PASS: fleet/sw-eng/3402f526
   [architect] REVIEW OK: fleet/sw-eng/3402f526
   ```

### Merge Triggers

**Option A: Human merges on GitHub**
- Human clicks "Merge" on the PR
- Webhook (or polling) detects merge
- Task auto-moves to "done"
- Worktree cleaned up

**Option B: Human approves in MC → auto-merge**
- Human moves task to "done" in MC
- Fleet detects state change (polling MC API)
- Runs `gh pr merge <PR_URL> --squash`
- Posts confirmation to channel

**Option C: Auto-merge for tagged tasks**
- Tasks tagged `auto-merge` + all checks pass → merge without human
- Only for low-risk: docs, tests, style changes
- Human configures which tasks get `auto-merge` tag

### Merge Detection Service

A lightweight daemon (or cron) that:
1. Polls MC for tasks in "review" with a pr_url custom field
2. Checks if the PR is merged on GitHub (`gh pr view --json state`)
3. If merged → move task to "done" + post to channel
4. Polls MC for tasks moved to "done" with unmerged PR
5. If task is done → merge the PR + post to channel
6. Cleans up worktrees for completed tasks

---

## Implementation Plan

### Phase A (Code Delivery) — IN PROGRESS
- [x] M61: Agent push + PR workflow in SOUL.md
- [ ] M62: MC custom fields (project, branch, pr_url)
- [ ] M63: Board memory PR notifications
- [ ] M64: Structured completion comments

### Phase B (MC Context) — NEXT
- [ ] M65: Board custom field setup automation
- [ ] M66: Board tags setup automation
- [ ] M67: Structured task comment format enforcement
- [ ] M68: create-task.sh sets project tag + custom field

### Phase C (Review & Merge) — HIGH PRIORITY
- [ ] M69: QA agent auto-review on task → review
- [ ] M70: Merge detection service (poll MC + GitHub)
- [ ] M71: Auto-merge for tagged tasks
- [ ] M72: Worktree cleanup on task done

### Phase D (Channel Communication) — HIGH PRIORITY
- [ ] M73: IRC/Discord channel setup (scripted, in setup.sh)
- [ ] M74: Agent channel messaging on key events
- [ ] M75: Human → agent interaction via channel
- [ ] M76: URL format standard for all references

### Phase E (Dashboard Quality)
- [ ] M77: Board views configuration
- [ ] M78: Fleet dashboard page or widget
- [ ] M79: Activity digest (daily summary to channel)

### Phase F (Operational Daemon)
- [ ] M80: Fleet operations service (replaces individual polling)
  - Watches MC task state changes
  - Watches GitHub PR state changes
  - Triggers review agents
  - Handles merge automation
  - Posts to channel
  - Cleans up worktrees
  - Single process, single config

---

## What We're Building

Not just scripts. An **operations system** where:
- The human creates tasks and reviews PRs
- Everything else is automated
- Every event flows to the right surface (task, memory, channel)
- Every reference is a clickable URL
- The dashboard is clean, structured, navigable
- Nothing sits idle, nothing requires manual intervention

This is the fleet's operating system.