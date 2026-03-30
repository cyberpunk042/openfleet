# MCP Layer Upgrade

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 6 of 8)

---

## What This Is

The MCP tool layer itself needs infrastructure changes to support
group calls and pre-embedded data. This is the foundation that the
four quadrants build on.

---

## Current MCP Architecture

- 20+ individual tools registered on a FastMCP server
- Each tool is independent — no grouping, no shared assembly
- `fleet_read_context` does partial aggregation but mixes concerns
- Agent makes multiple calls to assemble its working context
- No concept of "task mode" vs "heartbeat mode"
- No role-awareness in tool responses

---

## What Needs to Change

### Group Call Pattern
- Tools that aggregate multiple data sources in one call
- Not replacing individual tools — adding aggregate tools on top
- The aggregate tools call the same underlying data functions

### Context Mode
- The MCP server knows if the agent is in task mode or heartbeat mode
- Task mode: fleet_task_context is the primary call
- Heartbeat mode: fleet_heartbeat_context is the primary call
- Mode can be set at session start or inferred from context

### Role Awareness
- The MCP context (FleetMCPContext) knows the agent's role
- Role-specific data included in heartbeat responses
- Role providers registered per agent type

### Data Assembly Pipeline
- Shared data assembly functions used by both MCP calls and pre-embed
- Same data, two delivery mechanisms: tool response OR session injection
- Assembly functions are the single source of truth

---

## Milestones

### ML-F01: Data assembly module
- `fleet/core/context_assembly.py` (NEW)
- `assemble_task_context(task_id, mc, plane, ...) -> dict`
- `assemble_heartbeat_context(agent_name, role, mc, ...) -> dict`
- Shared by MCP tools AND pre-embed builders
- Single source of truth for data aggregation

### ML-F02: Role provider registry
- `fleet/core/role_providers.py` (NEW)
- Register per-role data functions
- Each returns a dict of role-specific data
- Queried by both MCP and pre-embed

### ML-I01: MCP context mode
- FleetMCPContext tracks current mode (task/heartbeat)
- Set when agent starts a session
- Affects which tools are available and what data they return

### ML-I02: Aggregate MCP tools
- `fleet_task_context(task_id)` — calls assemble_task_context
- `fleet_heartbeat_context()` — calls assemble_heartbeat_context
- Registered alongside existing individual tools

### ML-G01: Wire assembly to all data sources
- MC client for tasks, comments, approvals
- Plane client for issues, states, labels
- Event store for activity history
- Transpose layer for artifacts
- Methodology for stages and checks
- Standards for completeness
- Immune system for health
- Directives for pending PO commands