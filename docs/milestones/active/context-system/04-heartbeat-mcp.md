# Heartbeat × MCP Group Calls

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 4 of 8)

---

## What This Is

When an agent wakes up for a heartbeat (between tasks), it calls ONE
MCP tool and gets role-specific data. Events, messages, directives,
role responsibilities. Different from task context — this is fleet-wide
awareness for the agent's role.

---

## The Aggregated Heartbeat Bundle

### Events Since Last Heartbeat
- Task completions by other agents
- Immune system actions (prunes, lessons)
- Mode changes
- Plane updates
- Filtered for relevance to this agent

### Messages & Mentions
- Board memory entries @mentioning this agent
- Directives from PO targeting this agent
- Chat messages in relevant channels

### Role-Specific Data
Each role gets different data:

**fleet-ops:**
- Pending approvals queue with task details
- Review queue (tasks in review status)
- Health alerts from the doctor
- Budget status

**project-manager:**
- Unassigned inbox tasks
- Sprint progress / velocity
- Tasks stuck or blocked
- Plane sprint updates

**architect:**
- Design review requests
- Architecture-related comments
- Complexity flags on new tasks

**devsecops-expert:**
- Security findings
- Dependency alerts
- PR security review queue

**software-engineer / devops / others:**
- Their assigned tasks and status
- PR feedback on their work
- Merge conflicts

### Fleet State
- Work mode, cycle phase, backend mode
- Agents online/offline
- Tasks blocked count

### Assigned Tasks Summary
- List of this agent's tasks with stage + readiness
- Not the full context — just enough to decide what to work on

---

## Foundation Milestones

### HM-F01: Role data provider interface
- Define interface for role-specific data functions
- Each role registers a provider
- Provider returns dict of role-relevant data

### HM-F02: Role data providers (per role)
- fleet-ops: approvals, reviews, health
- PM: unassigned, sprint, velocity
- architect: design reviews, complexity
- devsecops: security, dependencies
- Others: assigned work, feedback

### HM-F03: Event filtering for heartbeat
- Events since last heartbeat timestamp
- Filtered by agent's tag subscriptions
- Relevance scoring

---

## Infrastructure Milestones

### HM-I01: MCP heartbeat group call
- Upgrade fleet_read_context or new fleet_heartbeat_context
- Role detection from agent name → role-specific provider
- Returns aggregated heartbeat bundle

---

## Integration Milestones

### HM-G01: Wire to event bus
- Events since last heartbeat from event store
- Agent-specific filtering via event router

### HM-G02: Wire to agent roles
- Role detection
- Role-specific provider dispatch

### HM-G03: Wire to directives
- Pending directives for this agent

---

## Testing Milestones

### HM-T01: Role provider tests
- Each role provider returns correct data shape
- Fleet-ops gets approvals, PM gets sprint, etc.