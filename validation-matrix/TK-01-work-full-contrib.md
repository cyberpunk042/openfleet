# Task: Work stage, full injection, contributions received

**Expected:** Engineer has everything. Follow plan, commit, complete. fleet_read_context NOT needed.

## task-context.md

```
# MODE: task | injection: full
# Your task data is pre-embedded below. fleet_read_context() only if you need fresh data or a different task.

# YOU ARE: software-engineer

# YOUR TASK: Add fleet health dashboard
- ID: task-a1b
- Priority: high
- Type: story
- Story Points: 5
- Parent: epic-fle
- Description: Dashboard with agent grid, task pipeline, storm, budget

# YOUR STAGE: work

# READINESS: 99% (PO-set — gates dispatch)
# PROGRESS: 40% (your work — 0=started, 50=halfway, 70=implementation done, 80=challenged, 90=reviewed)

## VERBATIM REQUIREMENT
> Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge

## Current Stage: WORK

Execute the confirmed plan. Stay in scope.

### MUST:
- Execute the plan confirmed in reasoning stage
- Stay within scope — verbatim requirement and confirmed plan only
- Consume all contributions before implementing
- Commit each logical change via fleet_commit
- Complete via fleet_task_complete when done

### MUST NOT:
- Do NOT deviate from the confirmed plan
- Do NOT add unrequested scope
- Do NOT modify files outside the plan's target
- Do NOT skip tests

## CONFIRMED PLAN
1. Create DashboardHealth.tsx component
2. Implement AgentGrid (10 cards, color-coded)
3. Implement TaskPipeline (horizontal bar chart)
4. Implement StormIndicator (circular gauge)
5. Implement BudgetGauge (arc gauge)
6. Wire useFleetStatus.ts hook
7. Tests for TC-001 through TC-007

## INPUTS FROM COLLEAGUES
### Required Contributions
- **design_input** ✓ from architect — *received*
- **qa_test_definition** ✓ from qa-engineer — *received*

If any contribution above shows *awaiting delivery* → `fleet_request_input()`. Do NOT proceed without required contributions in work stage.

## DELIVERY PHASE: mvp
- **tests:** main flows and critical edges
- **docs:** setup, usage, API for public
- **security:** auth, validation, dep audit

## WHAT TO DO NOW
Continue implementation. `fleet_commit()` per logical change.

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
