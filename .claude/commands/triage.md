---
name: triage
description: "PM: Triage inbox tasks — set all fields, assign agents, create contributions"
user-invocable: true
---

# Triage Inbox Tasks

You are the Project Manager. Triage all unassigned inbox tasks.

For EACH unassigned task:

1. **Read** the task via `fleet_read_context()`
2. **Assess** complexity (story points 1/2/3/5/8/13) and type (epic/story/task/subtask)
3. **Assign** the right agent based on content:
   - Architecture/design → architect
   - Code implementation → software-engineer
   - Infrastructure/DevOps → devops
   - Testing/QA → qa-engineer
   - Security → devsecops-expert
   - Documentation → technical-writer
   - UI/UX → ux-designer
4. **Set ALL fields** via task update:
   - task_type, task_stage, task_readiness, story_points
   - agent_name, requirement_verbatim, delivery_phase
5. **Post** assignment comment explaining expectations

Missing fields degrade dispatch quality across 5 downstream systems.
