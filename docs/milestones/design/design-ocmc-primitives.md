# Design: OCMC Primitives — Tags, Approvals, Custom Fields as Building Blocks

## User Requirements

> "There is also a Tags notion and we can use them and even add new ones in the OpenClaw Mission Control. There is also a whole 'approvals' notion and There is also a 'custom fields' notion"

> "So we need to detangle all that. do our researchs we need to identify the milestones and plan accordingly."

## Research Findings

### Tags — Currently Underused

We created 13 tags but they're barely used. Tags in OCMC are organization-scoped
and can be assigned to tasks.

**What tags CAN do that we're NOT doing:**
- Filter board views by tag → human sees only `project:nnrt` tasks
- Drive dispatch: "all `type:review` tasks go to qa-engineer"
- Track work categories: how much `type:feature` vs `type:fix` work?
- Group in dashboard: tasks by project tag
- Agent awareness: "what tags does my task have? what should I do differently?"

**What's missing:**
- Agents don't read or set tags programmatically
- No tag-based routing or automation
- No tag management in the fleet MCP server
- Board views aren't configured to use tags

### Approvals — Completely Untapped

OCMC has a full approval system we've never used. Key findings from research:

**Board settings that exist RIGHT NOW:**
- `require_approval_for_done = True` (DEFAULT!) — tasks CAN'T move to done without an approved approval
- `block_status_changes_with_pending_approval = False` — can enable to lock tasks during review
- `require_review_before_done = False` — can require review status before done
- `comment_required_for_review = False` — can require comment when moving to review
- `only_lead_can_change_status = False` — can restrict status changes to lead agent

**Approval features:**
- Confidence scores (0-100) — "how confident is the agent in this work?"
- Rubric scores — structured quality scoring (`{"code_quality": 94, "test_coverage": 98}`)
- Multi-task linking — one approval covers multiple related tasks
- Lead agent notification on resolution — lead knows when human approves/rejects
- SSE stream — real-time approval events
- Required reasoning — every approval must explain WHY

**This is the quality gate the user asked for.** When an agent completes a task:
1. Agent creates an approval (via fleet MCP tool) with confidence + rubric scores
2. Task can't move to done until human approves
3. Human sees approval in MC dashboard with scores and reasoning
4. Human approves → lead notified → task moves to done → PR merged

### Custom Fields — Partially Used

We created 4 fields (project, branch, pr_url, worktree). They're set sometimes.

**What custom fields CAN do:**
- Carry structured metadata through the entire task lifecycle
- Drive the fleet MCP server (server reads project field → knows which repo)
- Enable filtering and reporting (all tasks with pr_url → PR review queue)
- Display in dashboard (human sees PR link inline on the task card)

**What's missing:**
- Not all tasks have fields populated
- No validation (task without project field should be flagged)
- No additional fields that could be useful:
  - `agent_name` — which agent is working on this
  - `commit_count` — how many commits on the branch
  - `test_result` — pass/fail/skip counts
  - `quality_score` — from rubric

## Design: Primitives as System Building Blocks

> "We need to think I/O and directive and Meta"

Tags, approvals, and custom fields are the **metadata layer** of the fleet.
They're not features to configure once — they're primitives that flow through
every operation.

### Tags as Routing and Classification

**The fleet MCP server uses tags to:**
1. Know which project a task belongs to → resolve URLs automatically
2. Know what type of work → adjust template (feature PR vs fix PR vs docs PR)
3. Route notifications → `type:review` tasks notify #reviews channel
4. Track patterns → governance agent analyzes tag distribution

**Tag lifecycle:**
- `create-task.sh` (or fleet MCP `fleet_create_task`) sets initial tags
- Agent can add tags during work (found a security issue → add `alert:security`)
- Governance agent adds tags for classification
- Tags are inherited by follow-up tasks

### Approvals as Quality Gates

**The fleet MCP server creates approvals when:**
1. Agent completes a task → `fleet_task_complete` creates approval with:
   - `action_type`: "code_review" or "task_completion"
   - `confidence`: agent's self-assessed confidence (0-100)
   - `rubric_scores`: `{"correctness": X, "completeness": Y, "quality": Z}`
   - `payload.reason`: explanation of what was done and why it's ready
2. Agent finds a security issue → creates approval for human sign-off
3. Agent wants to merge → creates approval for merge authorization

**Human approval workflow:**
1. Human sees pending approval in MC dashboard
2. Reviews: confidence score, rubric, reasoning, linked PR
3. Approves → lead notified → task done → PR merged (via fleet-sync)
4. Rejects → agent notified → rework needed

**Board configuration needed:**
```python
Board.require_approval_for_done = True       # Already default!
Board.require_review_before_done = True      # Enable this
Board.comment_required_for_review = True     # Enable this
```

### Custom Fields as Metadata Pipeline

**Custom fields flow through the system:**

```
create-task.sh → sets: project
dispatch-task.sh → sets: worktree
fleet_task_accept (MCP) → sets: agent_name
fleet_commit (MCP) → updates: commit_count
fleet_task_complete (MCP) → sets: branch, pr_url, quality_score
fleet-sync → reads: pr_url for merge detection
fleet-monitor → reads: all fields for reporting
fleet-digest → reads: all fields for daily summary
```

**Additional fields to create:**
- `agent_name` (text) — which agent is working on this
- `commit_count` (integer) — commits on the branch
- `test_result` (text) — "604/604 pass" or "3 failures"
- `quality_score` (decimal) — from approval rubric average

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M117 | Board approval configuration | Enable require_review_before_done, comment_required_for_review |
| M118 | Approval creation in fleet MCP | fleet_task_complete creates approval with confidence + rubric |
| M119 | Approval-driven merge flow | Approved → fleet-sync merges PR |
| M120 | Tag-based routing | Fleet MCP reads tags, routes notifications |
| M121 | Additional custom fields | agent_name, commit_count, test_result, quality_score |
| M122 | Custom field pipeline | Fields set at every lifecycle stage |
| M123 | Board view configuration | Filter by project tag, review queue, blocker view |
| M124 | Governance integration | fleet-ops checks for missing fields, unused tags, stale approvals |

## Open Questions

1. **Should agents set their own confidence scores?** Or should quality checks
   determine the score? Agent self-assessment + automated checks averaged?

2. **What rubric dimensions?** Proposal: correctness, completeness, quality,
   test_coverage, documentation. Configurable per project?

3. **Should rejection create a new task or reopen the old one?** Reopen is simpler.
   New task gives cleaner history. Reopen with comment seems right.

4. **Tag creation:** Can agents create new tags, or only use existing ones?
   If agents create tags, they might create duplicates or noise.
   Recommendation: agents use existing tags, fleet-ops proposes new ones.