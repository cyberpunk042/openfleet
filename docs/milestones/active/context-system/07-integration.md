# Context System Integration

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 7 of 8)

---

## How All Four Quadrants Connect to Fleet Systems

### Orchestrator
- Dispatch triggers task pre-embed assembly
- Heartbeat cycle triggers heartbeat pre-embed assembly
- Orchestrator passes fleet state to both bundles
- Doctor report influences both (health alerts, agent status)

### Gateway
- Receives pre-embed data from orchestrator
- Injects into agent session context
- Task pre-embed on dispatch
- Heartbeat pre-embed on heartbeat trigger
- Existing mechanisms: context/ files, chat.send, system prompt append

### Event Bus
- Task bundle: activity events filtered for the specific task
- Heartbeat bundle: events since last heartbeat for this agent
- Event router provides agent-specific filtering

### Transpose Layer
- Task bundle includes transposed artifact object
- Completeness check against standards
- Agent works with the object, updates via MCP tools

### Methodology System
- Task bundle: current stage, instructions, readiness, checks
- Heartbeat bundle: assigned tasks with their stages
- Stage transitions tracked across cycles

### Immune System
- Heartbeat bundle: health alerts from the doctor
- Task bundle: any doctor flags on this task
- Health profiles influence what data is highlighted

### Teaching System
- If agent is in a lesson, the lesson content is part of the pre-embed
- Lesson status visible in heartbeat bundle

### Plane Sync
- Task bundle: Plane issue state, labels, description
- Heartbeat bundle: recent Plane updates for relevant projects

### Standards Library
- Task bundle: artifact completeness against standard
- Missing required fields highlighted

### Directives
- Heartbeat bundle: pending directives for this agent
- Task bundle: directives related to this specific task

### Agent Roles
- Heartbeat bundle: role-specific data from providers
- Fleet-ops gets different data than architect gets different data than PM