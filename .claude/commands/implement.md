---
name: implement
description: "Engineer: Execute confirmed plan — read contributions, commit, complete"
user-invocable: true
---

# Implement Confirmed Plan

You are the Software Engineer. Execute your confirmed plan.

1. `fleet_read_context()` — refresh task + contributions
2. `eng_contribution_check()` — verify ALL required contributions received:
   - Architect design_input → follow approach
   - QA qa_test_definition → each TC-XXX is a REQUIREMENT
   - DevSecOps security_requirement → follow absolutely
   - UX ux_spec → follow for user-facing work
   Missing → `fleet_request_input()`, do NOT proceed without
3. `fleet_task_accept(plan)` — confirm your implementation approach
4. Implement incrementally:
   - Small focused commits via `fleet_commit(files, message)`
   - Conventional format: `type(scope): description [task:XXXXXXXX]`
   - Tests alongside code, not after
5. Run tests — `pytest` must pass
6. `fleet_task_complete(summary)` — ONE call handles push, PR, approval, trail

Stay within scope. No "while I'm here" additions.
