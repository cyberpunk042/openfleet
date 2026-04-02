# fleet-plane

**Type:** Skill (slash command)
**Invocation:** /fleet-plane
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-plane
**User-invocable:** No (agent-only)

## Purpose

Guides sprint management via Plane (self-hosted project management). Covers reading sprint status, creating work items from OCMC epics, updating issues on task completion, posting comments with @mentions, bidirectional Plane-OCMC sync, and listing modules (epics) for progress tracking. Enforces that PM is the sole writer to Plane while other agents read only.

## Assigned Roles

- **project-manager** -- primary user, sole writer to Plane (other agents read only)

## Methodology Stages

- **Stage 5 (WORK)** -- PM uses this during active sprint management to sync Plane with OCMC task state

## What It Produces

- Plane issues created from OCMC epics (with module linkage)
- Plane issue state updates on OCMC task completion
- Plane comments with @mentions for follow-ups
- Sprint status reports from Plane cycle data
- Bidirectional Plane-OCMC sync events

## Key Steps

1. **Breaking Down Epics** -- list modules via fleet_plane_list_modules, evaluate needed tasks, create OCMC tasks via fleet_task_create, create Plane issues via fleet_plane_create_issue with module linkage, sync worker keeps them linked
2. **Sprint Status Report** -- get current cycle via fleet_plane_sprint, get all projects overview via fleet_plane_status, post report to IRC #sprint via fleet_chat, update Plane page with report
3. **Completing OCMC to Updating Plane** -- when OCMC task done, update Plane issue state to "Done" via fleet_plane_update_issue, post completion comment with PR URL via fleet_plane_comment
4. **Human Created Plane Issue** -- PM heartbeat context includes plane_new_items, PM evaluates (classify, estimate, assign), creates OCMC task with Plane reference via fleet_task_create, notifies agents via fleet_chat on #fleet

## Available Plane MCP Tools

| Tool | Purpose | Who Uses It |
|------|---------|-------------|
| fleet_plane_status(project) | Project overview -- sprint, modules, issues | PM, fleet-ops |
| fleet_plane_sprint(project) | Current cycle details and issue breakdown | PM |
| fleet_plane_list_modules(project) | List epics with status and progress | PM, architect |
| fleet_plane_create_issue(project, title, ...) | Create work item in Plane | PM only |
| fleet_plane_comment(project, issue_id, comment, mention) | Post comment, @mention | PM, fleet-ops |
| fleet_plane_update_issue(project, issue_id, state, ...) | Change state/priority | PM only |
| fleet_plane_sync(direction) | Trigger Plane-OCMC sync | PM, orchestrator |

## Key Rules

1. PM is the sole writer to Plane -- other agents read only
2. Plane is optional -- if tools return {plane_available: false}, skip Plane work
3. OCMC is authoritative for agent task state -- Plane reflects, not leads
4. Every OCMC task that came from Plane should be synced back when done
5. @mentions route to agent heartbeats -- use them for follow-ups

## Projects Managed

| ID | Name | Role |
|----|------|------|
| AICP | AI Control Platform | PRIMARY MISSION -- LocalAI independence |
| OF | OpenClaw Fleet | Fleet infrastructure and operations |
| DSPD | DevOps Solution Product Development | Plane itself |
| NNRT | Narrative-to-Neutral Report Transformer | NLP pipeline |

## Relationships

- USED BY: project-manager
- CONNECTS TO: fleet_plane_status (MCP tool), fleet_plane_sprint (MCP tool), fleet_plane_list_modules (MCP tool), fleet_plane_create_issue (MCP tool), fleet_plane_comment (MCP tool), fleet_plane_update_issue (MCP tool), fleet_plane_sync (MCP tool), fleet_task_create (MCP tool), fleet_chat (MCP tool), Plane MCP server, DSPD project (Plane instance itself)
- FEEDS: sprint reports (posted to IRC #sprint), Plane issue state (reflects OCMC task completion), agent heartbeats (via @mention routing), IRC #plane channel (sync events)
- DEPENDS ON: Plane MCP server running, Plane instance accessible (DSPD project), OCMC running (authoritative task state), fleet MCP server running, sync worker for bidirectional linking
