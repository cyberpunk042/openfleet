# fleet-sprint

**Type:** Skill (slash command)
**Invocation:** /fleet-sprint
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-sprint
**User-invocable:** Yes

## Purpose

Manages the full sprint lifecycle: loading sprint YAML configs into Mission Control, checking sprint status, and orchestrating the 8-phase sprint cycle from planning through retrospective. Defines the sprint YAML format that drives task creation and dependency chains.

## Assigned Roles

- **project-manager** -- primary user, manages sprint lifecycle end-to-end

## Methodology Stages

- **Stage 5 (WORK)** -- PM uses this skill during active sprint management, tracking progress, and coordinating dispatch

## What It Produces

- Loaded sprints in Mission Control from YAML config files
- Sprint status reports (task states, progress, blockers)
- Sprint retrospectives with velocity and agent performance metrics

## Key Steps

1. **Load a Sprint** -- run `fleet sprint load config/sprints/{plan}.yaml` to load sprint YAML into Mission Control with dependency chains
2. **Check Sprint Status** -- run `fleet sprint status {plan-id}` to view current sprint state
3. **Sprint Lifecycle (8 phases)**:
   - **Plan** -- PM breaks down epic into tasks with dependencies (uses fleet-plan skill)
   - **Load** -- sprint YAML loaded into MC with dependency chains
   - **Dispatch** -- orchestrator auto-dispatches unblocked tasks to assigned agents
   - **Work** -- agents execute tasks, commit changes, complete work
   - **Review** -- fleet-ops reviews completed work via review chain (uses fleet-review skill)
   - **Done** -- tasks transition states, dependencies unblock, next tasks dispatched
   - **Complete** -- all tasks done, parent epic transitions to review
   - **Retro** -- PM reports velocity, agent performance, lessons learned

## Sprint YAML Format

Sprint configs live in `config/sprints/` and define: sprint metadata (id, name, dates), task list with ids, titles, types (epic/task/subtask), parent linkage, agent assignments, story points, and dependency chains (depends_on arrays).

## Relationships

- USED BY: project-manager
- CONNECTS TO: fleet-plan (skill, produces the task breakdown that becomes sprint YAML), fleet-review (skill, review phase of sprint lifecycle), fleet-plane (skill, Plane sync for sprint tracking), orchestrator (system, auto-dispatches unblocked tasks)
- FEEDS: orchestrator dispatch queue (loaded sprint tasks become dispatchable work), agent work queues (dispatched tasks route to assigned agents), sprint retrospective (velocity and performance data), IRC #sprint channel (sprint progress and milestones)
- DEPENDS ON: sprint YAML config file in config/sprints/, fleet-plan output (task breakdown with dependencies), Mission Control running, orchestrator daemon for auto-dispatch
