# Heartbeat: Engineer has message from PM (new assignment)

**Expected behavior:** Read message, acknowledge assignment.

## fleet-context.md

```
# MODE: heartbeat | injection: full
# Your fleet data is pre-embedded below. Follow HEARTBEAT.md priority protocol.

# HEARTBEAT CONTEXT

Agent: software-engineer
Role: software-engineer
Fleet: 9/10 online | Mode: full-autonomous | Phase: execution | Backend: claude

## PO DIRECTIVES
None.

## MESSAGES
- From project-manager: Assigned you task-xyz: Implement fleet controls sidebar. Story points: 3. Stage: reasoning.

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
