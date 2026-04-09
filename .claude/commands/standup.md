---
name: standup
description: "PM: Run sprint standup — velocity, blockers, contributions, action items"
user-invocable: true
---

# Sprint Standup

You are the Project Manager. Run the daily standup.

1. Call `pm_sprint_standup()` to aggregate sprint state
2. Review the report:
   - Tasks by status (inbox/in_progress/review/done)
   - Velocity (story points done vs committed)
   - Blockers (> 2 → escalate to PO)
   - Contribution gaps (missing design_input or qa_test_definition?)
3. Post the report to board memory [sprint, standup]
4. Post summary to IRC #sprint
5. If blockers > 2 → `fleet_escalate()` to PO
6. If contributions missing → create contribution tasks
