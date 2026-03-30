# Task × MCP Group Calls

**Date:** 2026-03-30
**Status:** Design
**Part of:** Context System (document 2 of 8)

---

## What This Is

When an agent is working on a task, it calls ONE MCP tool and gets
everything it needs about that task. Aggregated. Ready to work from.

Currently the agent calls:
- `fleet_read_context` — partial task info + fleet data
- `fleet_artifact_read` — the transposed object
- `fleet_agent_status` — team info

Three calls to assemble what should be one bundle.

---

## The Aggregated Task Bundle

One call returns:

### Task Core
- ID, title, status, priority
- Verbatim requirement (the anchor)
- Description

### Methodology State
- Task readiness (0-100%)
- Current stage (conversation/analysis/investigation/reasoning/work)
- Stage instructions (what protocol to follow)
- Required stages for this task type
- Next stage (what advancing looks like)

### Artifact
- The transposed object (from transpose layer)
- Artifact type
- Completeness check (required %, missing fields, suggested readiness)

### Comments & Activity
- All task comments (progressive work trail)
- Activity events for this task
- Last N cycles of work history

### Relations
- Parent task (if subtask)
- Child tasks (if epic/story)
- Dependencies (blocked by / blocking)

### Plane
- Plane issue ID, state, labels
- Plane description (the rich HTML source)

### Custom Fields
- All custom field values in one dict

---

## Foundation Milestones

### TM-F01: Task data aggregation function
- Single function that collects all the above from existing sources
- MC client for task + comments + approvals
- Transpose layer for artifact
- Methodology for stage + checks
- Standards for completeness

### TM-F02: Comment history aggregation
- Fetch all comments for a task from OCMC
- Fetch comments from Plane if linked
- Merge and sort by time
- Include author, timestamp, content

### TM-F03: Activity history aggregation
- Filter event store for events about this task
- Include dispatches, updates, artifact changes, doctor actions

---

## Infrastructure Milestones

### TM-I01: MCP group call implementation
- New tool: fleet_task_context(task_id) OR upgrade fleet_read_context
- Calls the aggregation function
- Returns the full bundle as structured dict
- Replaces multiple separate calls

### TM-I02: Caching strategy
- Should the bundle be cached per orchestrator cycle?
- Or fresh every MCP call?
- Balance: freshness vs token cost of assembly

---

## Integration Milestones

### TM-G01: Wire to transpose layer
- Artifact object included in bundle via from_html
- Completeness via artifact_tracker

### TM-G02: Wire to methodology
- Stage instructions from stage_context
- Readiness from custom fields
- Required stages from methodology engine

### TM-G03: Wire to Plane
- Plane state, labels from sync data
- Comments from Plane via API

---

## Testing Milestones

### TM-T01: Unit tests for aggregation
- Mock MC client, test bundle assembly
- Verify all sections populated

### TM-T02: Integration test
- End-to-end: create task, add artifact, call fleet_task_context
- Verify bundle contains correct aggregated data