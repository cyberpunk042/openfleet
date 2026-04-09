---
name: contribute
description: "All contributors: Produce and deliver a contribution to another agent's task"
user-invocable: true
---

# Produce Contribution

You have a contribution task assigned. Deliver your specialist input.

1. **Read** your assigned contribution task via `fleet_read_context()`
2. **Identify** the target task and contribution type from your context:
   - design_input (architect) → approach, target files, patterns, constraints
   - qa_test_definition (QA) → structured TC-XXX criteria
   - security_requirement (devsecops) → specific actionable controls
   - ux_spec (UX) → all states, interactions, accessibility
   - documentation_outline (writer) → what docs expected
3. **Read** the target task's verbatim requirement and existing analysis
4. **Produce** your contribution — FULL content, not compressed
5. **Deliver** via `fleet_contribute(target_task_id, contribution_type, content)`
6. Your contribution task is automatically marked done

The target agent sees your contribution in their pre-embedded context.
If ALL required contributions arrive, the target task can advance to work stage.
