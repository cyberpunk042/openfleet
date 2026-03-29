# Operational Gaps — What's Broken in the Fleet

Identified 2026-03-28. These are not nice-to-haves — these are fundamental gaps
that make the fleet unusable as a real operational system.

## Gap 1: Code Never Reaches Remote

**What happens now:**
- Agent commits to a local git worktree
- Task moves to "review" in MC
- Branch exists locally only
- No push, no PR, nothing online
- `integrate-task.sh` exists but is manual and nobody runs it

**What should happen:**
- Agent completes work → auto-push branch to remote
- PR created automatically with task reference, files changed, agent name
- Review-worthy PRs surfaced to human (MC notification + channel message)
- Auto-merge for low-risk PRs (docs, tests) after automated checks pass
- Human approval required for high-risk PRs (logic changes, security)

**What's needed:**
- Auto-push on task completion (in agent workflow or post-completion hook)
- Auto-PR creation (via `gh` CLI in the agent's completion step)
- MC task should link to the PR URL
- Review agent (or lead agent) that can approve/request changes
- Merge policy configuration per project

---

## Gap 2: No Agent Communication / Board Memory is Dead

**What happens now:**
- Board memory has ONE entry (the test message we sent)
- Agents don't chat with each other
- Agents don't proactively message the human
- No cross-agent awareness (architect doesn't know what sw-eng did)
- The "chat" feature in MC is effectively unused

**What should happen:**
- Agents post to board memory when they start, find something interesting, or complete
- Lead agent coordinates work and communicates with human
- Human can @mention agents in board memory and get responses
- Agents reference each other's work: "@architect the sw-eng made this change, review?"
- Board memory becomes the living record of fleet activity

**What's needed:**
- Agent SOUL.md/workflow must instruct agents to use board memory actively
- Lead agent role needs to be assigned and configured
- Board memory notifications need to flow to agents (MC already supports this)
- Agent-to-agent communication protocol (via board memory tags)
- Human interaction through board memory must trigger agent responses

---

## Gap 3: Poor Context and Navigability in MC

**What happens now:**
- Task comments are text dumps with no clickable links
- No way to see which project a task is about
- No custom fields used (project, branch, PR URL, worktree path)
- No tags (project name, priority level, agent role)
- Can't navigate from MC to the actual code or commit
- Human has to read walls of text to understand what happened

**What should happen:**
- Every task has: project name, branch URL, PR URL as custom fields
- Tags: project name, agent name, task type (feature, fix, review)
- Task comments include GitHub-style links to commits, files, PRs
- Completion comment is structured with clear sections, not a text dump
- MC custom fields populated automatically by dispatch and completion scripts

**What's needed:**
- Define MC custom fields for fleet tasks (project, branch, pr_url, worktree)
- Populate custom fields during task creation and agent completion
- Agent completion comments must include clickable URLs
- For GitHub-hosted projects: commit URLs, compare URLs, file URLs
- MC board configuration (custom fields, tags) automated in setup
- Consider: OCMC customization to render links/references better

---

## Gap 4: No Review/Merge Automation

**What happens now:**
- Task goes to "review" and sits there forever
- No agent reviews the work
- No automated checks (tests, lint) on the branch
- "Done" requires manual intervention
- No merge path from review → merged → done

**What should happen:**
- When task moves to review:
  1. QA agent runs automated checks (tests, lint) on the branch
  2. Architect agent reviews for design concerns (if marked for review)
  3. Technical writer agent reviews for doc updates needed
  4. Results posted as task comments
  5. If all checks pass + appropriate reviews done → auto-merge or surface to human
- Human can approve/reject from MC
- Approved PRs auto-merge via `gh pr merge`
- Merged → task moves to "done"

**What's needed:**
- Review workflow definition (which agents review, what triggers review)
- Hook: task status → "review" triggers review agents
- QA agent skill: run project tests on a branch, report results
- Architect agent skill: review code changes for design concerns
- Merge automation script
- MC approval flow integration (existing approval system, untapped)

---

## Gap 5: IRC / Real-Time Communication Channel

**What happens now:**
- No external channel configured
- Control UI exists but is web-only, no mobile, no persistent history
- Human can't get pinged when something needs attention
- No way for agents to share URLs/references interactively
- Board memory is async and buried in the MC UI

**What should happen:**
- IRC (or Discord) channel where:
  - Agents announce task starts, completions, blockers
  - Agents share clickable URLs to commits, PRs, files, task pages
  - Human can respond and agents pick it up
  - Persistent history of all fleet activity
  - Human connects with any IRC client (irssi, weechat, web client)
- Messages include rich context:
  - "[software-engineer] Completed: Fix NNRT test collection (PR: https://...)"
  - "[architect] Review needed: fleet/sw-eng/3402f526 changes 40 files"
  - "[qa-engineer] Tests passing: 604/604 on fleet/sw-eng/3402f526"

**What's needed:**
- Choose platform: IRC (local, lightweight) vs Discord (rich, mobile)
- Configure channel in OpenClaw
- Bind agents to channel
- Agent workflow: post to channel on key events (start, blocker, complete)
- URL format for each reference type (MC task, GitHub PR, commit, file)
- Human → agent interaction via channel (agent reads channel messages)
- Channel configuration in setup.sh

---

## Gap 6: MC Customization for Fleet

**What happens now:**
- OCMC used as-is with minimal configuration
- Board has no custom fields
- No fleet-specific UI components
- Skills marketplace patched but minimal
- No fleet dashboard in MC

**What should happen:**
- MC board configured with fleet-specific custom fields
- Board tags for project names, task types
- Fleet activity dashboard (widget or page)
- Skill marketplace properly integrated with categories visible
- Consider: OCMC frontend extensions for fleet-specific views

**What's needed:**
- Board setup automation: create custom fields, tags
- OCMC API for custom fields and board configuration
- Evaluate: can we add fleet-specific pages to OCMC frontend?
- Or: separate lightweight dashboard that reads MC API

---

## Priority and Sequencing

These gaps are interdependent. Recommended order:

### Phase A: Make Code Reach Remote (Gap 1)
Without this, nothing the fleet does is visible or useful.
- Auto-push in agent workflow
- Auto-PR creation
- PR URL in task custom fields

### Phase B: Rich Context in MC (Gap 3)
Without this, the human can't follow what's happening.
- Custom fields for project, branch, PR
- Structured completion comments with URLs
- Tags for project and type

### Phase C: Communication (Gap 2 + Gap 5)
Without this, the fleet is a black box.
- IRC/Discord channel setup
- Agent announcement messages on key events
- Board memory active usage
- Human↔agent interaction

### Phase D: Review Automation (Gap 4)
Without this, work piles up in review forever.
- Review triggers
- QA/architect review agents
- Merge automation

### Phase E: MC Customization (Gap 6)
This makes everything above look professional.
- Board setup automation
- Custom fields, tags
- Dashboard

---

## Estimated Scope

This is NOT a weekend project. Each phase is multiple milestones:

- Phase A: 3-4 milestones (push flow, PR creation, custom fields, task linking)
- Phase B: 2-3 milestones (custom fields API, completion format, URL templates)
- Phase C: 4-5 milestones (channel setup, agent messaging, URL format, interaction protocol, setup automation)
- Phase D: 3-4 milestones (review triggers, QA skill, review protocol, merge automation)
- Phase E: 2-3 milestones (board config API, tags, dashboard)

Total: ~15-20 milestones of real work.