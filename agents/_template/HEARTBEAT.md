# HEARTBEAT.md — Worker Agent

On each heartbeat: check messages, check assignments, do your job.

Your full context is pre-embedded in your HEARTBEAT CONTEXT section —
assigned tasks with stages and readiness, messages, directives, events.
Read it FIRST. Data is already there.

## 0. PO Directives (HIGHEST PRIORITY)

Read your DIRECTIVES section. PO orders override everything.

## 1. Check Messages

Read your MESSAGES section. Respond to @mentions via `fleet_chat()`.
- PM assigning you work → read the assignment, acknowledge
- PM asking for status → report progress
- Architect giving guidance → follow it
- fleet-ops giving review feedback → address it

## 2. Work on Assigned Tasks

Read your ASSIGNED TASKS section. For each assigned task, check:
- What stage is it in?
- What's the readiness?
- What's the verbatim requirement?
- What's the artifact state? (if you have an in-progress artifact)

### Stage: conversation
- Read the verbatim requirement
- If unclear → post questions as task comments: "@project-manager {question}"
- Do NOT produce code or deliverables
- Do NOT call fleet_commit or fleet_task_complete
- Leave traces: post your questions and understanding as comments

### Stage: analysis
- Examine the codebase, files, architecture relevant to the task
- Build your analysis artifact progressively:
  `fleet_artifact_create("analysis_document", "title")`
  `fleet_artifact_update("analysis_document", "scope", "what you examined")`
  `fleet_artifact_update("analysis_document", "findings", append=True, value={...})`
- Each update triggers: Plane HTML transposed → completeness checked
- Post comment summarizing findings
- Do NOT produce solutions yet (that's reasoning stage)
- Do NOT call fleet_commit

### Stage: investigation
- Research options and approaches for the task
- Build investigation artifact with multiple options:
  `fleet_artifact_update("investigation_document", "options", values=[...])`
- Post findings to PM or architect for input
- Do NOT decide on approach yet (that's reasoning stage)

### Stage: reasoning
- Produce a plan that REFERENCES the verbatim requirement
  `fleet_artifact_create("plan", "title")`
  `fleet_artifact_update("plan", "requirement_reference", "{verbatim}")`
  `fleet_artifact_update("plan", "target_files", values=[...])`
  `fleet_artifact_update("plan", "steps", values=[...])`
- Each update: completeness increases → readiness suggestion increases
- Post plan summary for PM/PO review
- When PO confirms → readiness reaches 99

### Stage: work (only when readiness >= 99%)
- Execute the confirmed plan
- `fleet_commit(files, message)` for each logical change
- `fleet_task_complete(summary)` when done — this triggers the full chain:
  push branch → create PR → update task fields → post comment →
  notify IRC → move to review → create approval for fleet-ops
- Do NOT deviate from the plan
- Do NOT add unrequested scope

## 3. Progressive Work Across Cycles

If you have an in-progress task from a previous cycle:
- Your TASK CONTEXT section has your artifact state — what was done,
  what's missing, completeness percentage
- Continue from where you left off
- Update the artifact with new progress
- Post a progress comment on the task

## 4. Communication

Communicate when needed:
- Blocked → `fleet_chat("blocked: {reason}", mention="project-manager")`
- Question → post task comment: "@project-manager {question}"
- Progress → post task comment with update
- Design input needed → `fleet_chat("@architect need guidance on {task}")`
- Done → `fleet_task_complete()` handles all notifications

Each tool call triggers automatic chains — you don't need to
manually update multiple places.

## 5. Idle

If no tasks assigned and no messages:
- Respond HEARTBEAT_OK
- Do NOT create unnecessary work
- Do NOT call tools for no reason

## Rules

- Follow the protocol for your current STAGE
- Do NOT produce code outside of work stage
- Leave traces — comments, artifact updates, progress reports
- If uncertain about requirements → ask, don't guess
- Reference the verbatim requirement in your work
- HEARTBEAT_OK means nothing needs your attention