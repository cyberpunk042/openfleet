# fleet-plan

**Type:** Skill (slash command)
**Invocation:** /fleet-plan
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-plan
**User-invocable:** No (agent-only)

## Purpose

Guides agents in breaking down epics and requests into structured sprint plans with tasks, dependencies, agent assignments, story point estimates, and priority levels. Produces a DAG of tasks ready for orchestrator dispatch.

## Assigned Roles

- **project-manager** -- primary user, responsible for sprint planning and epic decomposition

## Methodology Stages

- **Stage 4 (REASONING)** -- PM uses this to break epics into sprint tasks with dependencies as part of planning
- **Stage 5 (WORK)** -- PM executes the plan creation, producing task structures in OCMC

## What It Produces

- Structured task breakdown with titles, types (epic/story/task/subtask), agent assignments, story points, dependencies, and priorities
- Dependency DAG (directed acyclic graph) ensuring no circular dependencies
- Critical path identification (longest dependency chain)
- Risk and blocker identification

## Key Steps

1. **Analyze the Epic/Request** -- identify requirements, involved components, dependencies, and risks
2. **Break Down into Tasks** -- for each task define: clear actionable title (start with verb), type (epic/story/task/subtask), agent assignment (architect for design, sw-eng for code, etc.), story points (1/2/3/5/8/13), dependencies, priority (urgent/high/medium/low)
3. **Create Tasks with Dependencies** -- use fleet_task_create for each task, linking parent_task to epic, setting depends_on for sequential work
4. **Verify the Plan** -- confirm all tasks have agents assigned, dependencies form a DAG (no circular), critical path identified, story points total is reasonable, blockers and risks identified

## Relationships

- USED BY: project-manager
- CONNECTS TO: fleet_task_create (MCP tool), fleet-sprint (skill, consumes the plan output), fleet-plane (skill, Plane issue creation from plan), pm-plan (AICP skill, project-level planning)
- FEEDS: orchestrator dispatch (unblocked tasks get auto-dispatched), sprint YAML (plan can be serialized as sprint config), agent work queues (tasks route to assigned agents)
- DEPENDS ON: epic or request to decompose, agent roster (must know available roles for assignment), fleet MCP server running
