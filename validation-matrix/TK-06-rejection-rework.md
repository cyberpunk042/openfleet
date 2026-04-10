# Task: Work stage, rejection rework (iteration 2)

**Expected:** Second attempt after rejection. Should show iteration 2, rejection feedback, eng_fix_task_response().

## task-context.md

```
# MODE: task | injection: full
# Your task data is pre-embedded below. fleet_read_context() only if you need fresh data or a different task.

# ITERATION: 2 (rework after rejection)

# YOU ARE: software-engineer

# YOUR TASK: Add fleet health dashboard
- ID: task-a1b
- Priority: high
- Type: story
- Story Points: 5
- Description: Dashboard with agent grid, task pipeline, storm, budget

# YOUR STAGE: work

# READINESS: 99% (PO-set — gates dispatch)

## VERBATIM REQUIREMENT
> Add health dashboard with agent grid

## Current Stage: WORK

Fix the rejected work. Address the ROOT CAUSE identified in rejection feedback.

### MUST:
- Fix the specific issues from the rejection feedback
- Stay within scope — verbatim requirement and confirmed plan only
- Re-read contributions and rejection feedback before fixing
- Commit each logical change via fleet_commit
- Complete via fleet_task_complete when done

### MUST NOT:
- Do NOT deviate from the confirmed plan
- Do NOT add unrequested scope
- Do NOT modify files outside the plan's target
- Do NOT skip tests

## REJECTION REWORK (iteration 2)

Your previous submission was rejected. Fix the ROOT CAUSE — do not paper over it.
Use `eng_fix_task_response()` to structure your fix.

**Feedback:**
> REJECTED by fleet-ops: Missing test for TC-003 (TaskPipeline segments). Add integration test verifying segment sum equals total count.

## INPUTS FROM COLLEAGUES

## CONTRIBUTION: design_input (from architect)

**Approach:** DashboardHealth component in fleet/ui/components/ using React.
- AgentGrid: 10 cards, color-coded by status
- TaskPipeline: horizontal bar chart (inbox/progress/review/done)
- StormIndicator: circular gauge with severity colors
- BudgetGauge: arc gauge with 5h and 7d usage

**Target files:** fleet/ui/components/DashboardHealth.tsx, fleet/ui/hooks/useFleetStatus.ts
**Patterns:** Observer (real-time), Adapter (API → component)
**Constraints:** Existing MC build pipeline. No new deps.

---
## CONTRIBUTION: qa_test_definition (from qa-engineer)

TC-001: AgentGrid shows 10 agent cards | unit | required
TC-002: Agent card color matches status | unit | required
TC-003: TaskPipeline segments sum to total | unit | required
TC-004: StormIndicator correct severity color | unit | required
TC-005: BudgetGauge shows API percentage | integration | required
TC-006: Dashboard refreshes on status change | integration | recommended
TC-007: Keyboard navigation works | e2e | required

---

### Required Contributions
- **design_input** ✓ from architect — *received*
- **qa_test_definition** ✓ from qa-engineer — *received*

If any contribution above shows *awaiting delivery* → `fleet_request_input()`. Do NOT proceed without required contributions in work stage.

## DELIVERY PHASE: mvp
- **tests:** main flows and critical edges
- **docs:** setup, usage, API for public
- **security:** auth, validation, dep audit

## WHAT TO DO NOW
REWORK required. Fix the root cause identified in the rejection feedback. Use `eng_fix_task_response()` to structure your approach, then implement the fix.

## WHAT HAPPENS WHEN YOU ACT
- `fleet_commit()` → git + event + trail (one logical change per commit)
- `fleet_task_complete()` → push → PR → approval → IRC → Plane → trail → parent eval
- Every tool call fires automatic chains — you don't update multiple places manually.

```

## knowledge-context.md

```
## Stage: WORK — Resources Available

### Skills:
- /fleet-engineer-workflow — contribution consumption, TDD, conventional commits
- /fleet-completion-checklist — 8-point pre-completion check
- /test-driven-development (superpowers) — RED-GREEN-REFACTOR cycle
- /verification-before-completion (superpowers) — run tests before claiming done

### Sub-agents:
- **test-runner** (sonnet) — run pytest in isolated context
- **code-explorer** (sonnet) — trace execution paths

### MCP: fleet · filesystem · github · playwright
### Plugins: claude-mem · safety-net · context7 · superpowers · pyright-lsp

```
