# fleet_approve

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — fleet-ops processes approvals during heartbeat

## Purpose

Approve or reject a pending task completion. Fleet-ops ONLY tool (PR authority enforced). Must follow the 7-step REAL review protocol — never rubber-stamp. Rejection includes specific feedback, readiness regression, and stage reversion.

## Parameters

- `task_id` (string) — Task to approve/reject
- `approved` (boolean) — true = approve, false = reject
- `reasoning` (string) — SPECIFIC reasoning (not "looks good" — must cite criteria)

## Chain Operations — APPROVED

```
fleet_approve(task_id, approved=true, reasoning)
├── CHECK: agent has PR authority (agent_roles.py — fleet-ops, devsecops, architect, QA)
├── UPDATE APPROVAL: status → "approved", reasoning, confidence
├── UPDATE TASK: status → "done" (or brain transitions next cycle)
├── SET PROGRESS: task_progress = 90 (REVIEW_PASSED)
├── POST COMMENT: "Approved by {agent}: {reasoning}" (type: approval)
├── PLANE SYNC: issue state → "Done", labels updated
├── IRC: #reviews "[approved] {task_title}"
├── TRAIL: trail.review.approved event
├── EVALUATE PARENT: all children done? → parent to review
├── UPDATE SPRINT: sprint progress recalculated
├── EVENT: fleet.approval.approved
└── LABOR: review signature (reviewer, model, duration, criteria count)
```

## Chain Operations — REJECTED

```
fleet_approve(task_id, approved=false, reasoning)
├── CHECK: agent has PR authority
├── UPDATE APPROVAL: status → "rejected", reasoning
├── REGRESS READINESS: task_readiness drops (99 → 80 or lower)
├── REGRESS STAGE: task_stage may revert (work → reasoning)
├── SET PROGRESS: task_progress = 0 (reset — must rework)
├── POST COMMENT: "Rejected by {agent}: {reasoning}" (type: rejection)
│   ├── WHAT to fix (specific)
│   ├── WHICH stage to return to
│   ├── HOW MUCH to regress readiness
├── PLANE SYNC: issue state → "In Progress", labels updated
├── IRC: #reviews "[rejected] {task_title}: {reasoning}"
├── TRAIL: trail.review.rejected event with regression details
├── DOCTOR SIGNAL: signal_rejection(agent, task) — repeated rejections → detection
├── NOTIFY AGENT: @mention assigned agent with rejection feedback
├── EVENT: fleet.approval.rejected
└── AUTO-CREATE FIX TASK: if rejected by architect/QA/devsecops
```

## The 7-Step REAL Review Protocol

Fleet-ops MUST follow these steps (from fleet-review skill + heartbeat-md-standard):

1. **READ REQUIREMENT** — Read requirement_verbatim word by word. Compare with acceptance_criteria.
2. **READ THE DIFF** — Read FULL PR diff. Every line added, removed, touched.
3. **VERIFY ACCEPTANCE CRITERIA** — Each criterion: ✓ met / ✗ not met / ✗ partially met. ALL must be ✓.
4. **CHECK TRAIL** — Verify: conventional commits, tests exist + pass, coverage maintained, branch naming, labor stamp reasonable.
5. **VERIFY NO SCOPE CREEP** — Only what was asked. No "while I'm here" changes. No files outside plan scope.
6. **QUALITY CHECK** — Security (no injection, XSS, SQL), architecture (follows patterns), style (consistent), error handling.
7. **DECISION** — APPROVE (with specific criteria cited) or REJECT (with specific failure points + regression guidance) or ESCALATE (to PO).

**Doctor detection:** If fleet-ops approves in <30 seconds → detect_laziness → teaching lesson about REAL review.

## Who Uses It

| Role | Authority | Can Reject | Can Close PR |
|------|-----------|-----------|-------------|
| Fleet-ops | FINAL authority | Yes | Yes |
| DevSecOps | Security domain | Yes (security_hold) | Yes |
| Architect | Architecture domain | Yes (design alignment) | No |
| QA | Quality domain | Yes (test criteria) | No |

## Relationships

- DEPENDS ON: fleet_task_complete (creates the approval to review)
- READS: PR diff (gh_client.py), trail (board memory), labor stamp, requirement_verbatim
- PRODUCES: approval decision, regression (if rejected), fix task (if rejected by specialist)
- TRIGGERS: parent evaluation (orchestrator Step 7 — all children done → parent review)
- TRIGGERS: sprint progress update
- TRIGGERS: doctor signal on repeated rejections
- CONSUMED BY: orchestrator (_transition_approved_reviews → DONE)
- CONNECTS TO: challenge system (challenge results should be available during review — NOT YET WIRED)
- CONNECTS TO: codex review (codex results should be visible — NOT YET WIRED)
- TRAIL: trail.review.approved or trail.review.rejected
- ANTI-CORRUPTION: rubber-stamp detection (< 30s review → disease)
