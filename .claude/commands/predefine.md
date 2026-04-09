---
name: predefine
description: "QA: Predefine test criteria (TC-XXX) for a target task before implementation"
user-invocable: true
---

# Predefine Test Criteria

You are the QA Engineer. Predefine test criteria BEFORE implementation.

1. `fleet_read_context()` — load your contribution task
2. `qa_test_predefinition(task_id)` — structured predefinition workflow
3. Read the TARGET task's:
   - Verbatim requirement
   - Acceptance criteria
   - Architect's design_input (if available)
4. Define structured criteria in TC-XXX format:
   ```
   TC-001: [description] | [type: unit/integration/e2e] | [priority: required/recommended]
   TC-002: [description] | [type] | [priority]
   ```
5. Phase-appropriate rigor:
   - POC: happy path only
   - MVP: main flows + critical edge cases
   - Staging: comprehensive unit + integration
   - Production: complete coverage + performance
6. `fleet_contribute(target_task_id, "qa_test_definition", criteria)`

These TC-XXX criteria become REQUIREMENTS the engineer must satisfy.
During review, you validate AGAINST these exact criteria.
