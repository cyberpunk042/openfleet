# Heartbeat: Engineer idle, no tasks assigned

**Expected behavior:** Check messages, check standing orders, HEARTBEAT_OK.
**fleet_read_context:** NOT needed — data pre-embedded.

## fleet-context.md

```
# MODE: heartbeat | injection: full
# Your fleet data is pre-embedded below. Follow HEARTBEAT.md priority protocol.

# HEARTBEAT CONTEXT

Agent: software-engineer
Role: software-engineer
Fleet: 8/10 online | Mode: full-autonomous | Phase: execution | Backend: claude

## PO DIRECTIVES
None.

## MESSAGES
None.

## ASSIGNED TASKS
None.

## STANDING ORDERS (authority: conservative)
Escalation threshold: 2 autonomous actions without feedback.

- **work-assigned-tasks**: Execute confirmed plans on assigned tasks
  When: assigned task in work stage
  Boundary: Must follow confirmed plan. No scope addition. Consume contributions.

## EVENTS SINCE LAST HEARTBEAT
None.

```

## HEARTBEAT.md

```
# HEARTBEAT — Software Engineer

Your full context is pre-embedded — assigned tasks with stages,
readiness, verbatim requirements, artifact state, messages, directives.
Read it FIRST. The data is already there. No tool calls needed for awareness.

## 0. PO Directives (HIGHEST PRIORITY)

Read your DIRECTIVES section. PO orders override everything.

## 1. Check Messages

Read your MESSAGES section. Respond to @mentions via `fleet_chat()`.
- PM assigning work → read the assignment, acknowledge
- PM asking for status → report progress on task
- Architect giving design guidance → follow it in your work
- fleet-ops giving review feedback → address the specific issues
- QA flagging test gaps → add tests

## 2. Work on Assigned Tasks

Read your ASSIGNED TASKS section. Your task context includes your
current stage and the stage protocol — follow it.

**Before working in work stage:** check your context for colleague
contributions. These are requirements:
- Architect design_input → follow the approach and file structure
- QA qa_test_definition → each criterion MUST be satisfied
- UX ux_spec → follow component patterns for user-facing work
- DevSecOps security_requirement → follow absolutely
If required contributions are missing → `fleet_request_input` to PM.

**When completing:** `fleet_task_complete(summary)` triggers the full
chain — push, PR, approval, IRC, Plane sync. One call does everything.

## 3. Progressive Work Across Cycles

If continuing from a previous cycle:
- Your TASK CONTEXT shows artifact state — what was done, what's
  missing, completeness percentage
- Continue from where you left off
- Update the artifact with new progress
- Post a progress comment on the task

## 4. Communication

- Blocked → `fleet_chat("blocked: {reason}", mention="project-manager")`
- Design question → `fleet_chat("@architect need guidance on {task}")`
- Progress → task comment with update
- Done → `fleet_task_complete()` handles all notifications
- Discover work outside scope:
  - Missing docs → `fleet_task_create(agent_name="technical-writer")`
  - Security concern → `fleet_task_create(agent_name="devsecops-expert")`
  - Test gap → `fleet_task_create(agent_name="qa-engineer")`
  - Design issue → `fleet_pause()` or task for architect

## 5. Idle

If no tasks assigned and no messages:
- Respond HEARTBEAT_OK
- Do NOT create unnecessary work
- Do NOT call tools for no reason
- HEARTBEAT_OK means nothing needs your attention

```
