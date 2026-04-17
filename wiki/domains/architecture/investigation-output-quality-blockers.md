---
title: "Investigation: Solutions for Context Output Quality"
type: reference
domain: architecture
status: draft
confidence: medium
created: 2026-04-11
updated: 2026-04-11
tags: [investigation, context-injection, output-quality, solutions, options]
epic: E001
related:
  - analysis-output-quality-blockers.md
sources: []
---

# Investigation: Solutions for Context Output Quality

Options for each of the 10 systemic issues. No decisions.

---

## Summary

Investigation of solution options for the 10 context-output-quality blockers identified during TK-01 analysis. Per blocker (contribution marker stripped, fleet state missing, confirmed plan loader, tier-aware contribution depth, dead heartbeat code, generator Navigator gap, etc.), lists candidate fixes and their tradeoffs — feeds the reasoning-stage plan.

## Finding 1: Contribution content marker stripped

### Option A: Stop stripping the marker

Remove the 3 lines at preembed.py:344-347 that strip `<!-- CONTRIBUTIONS_ABOVE -->`. The marker stays in the output. The orchestrator at orchestrator.py:714-716 can then insert contribution blocks at it. The generator's render_task_scenario can also insert at it. In production output, if no contributions were inserted, the marker is an invisible HTML comment — harmless.

Tradeoff: Simplest fix. One line removal. The marker is invisible in rendered markdown. But the marker IS part of the output, which is slightly messy.

### Option B: Accept contribution_content as a parameter in build_task_preembed

Add `contribution_content: list[tuple[str, str, str]] = None` parameter (type, contributor, content). Preembed renders the blocks itself at the marker position, then strips the marker. The orchestrator passes loaded contribution content. The generator passes it directly.

Tradeoff: Cleaner — preembed owns the full rendering. But requires the orchestrator to load contribution content into structured data before calling preembed, whereas currently the orchestrator works with raw text blocks from the existing file.

### Option C: Move contribution preservation into preembed

Pass the existing task-context.md content to build_task_preembed. Let preembed extract `## CONTRIBUTION:` blocks and insert them. The orchestrator just passes the existing file content along with the new task data.

Tradeoff: Preembed becomes aware of its own previous output — circular dependency feel. But consolidates all rendering in one place.

---

## Finding 2: Navigator bypassed in generator

### Option A: Call Navigator.assemble() in the generator

The generator imports Navigator, creates an instance, calls `nav.assemble(role="software-engineer", stage="work", model="opus-4-6", task_context="Add fleet health dashboard")`. Uses the real assembly pipeline. Requires knowledge-map files to exist (they do — 90+ KB entries).

Tradeoff: Strongest guarantee — generator shows what production shows. But depends on external services (LightRAG, claude-mem) which may not be running. Navigator already handles graceful fallback (logs debug, returns None from graph/memory queries). Static knowledge-map assembly works without any services.

### Option B: Capture a real Navigator output and use it as fixture

Run Navigator.assemble once, save the output, use it as a static fixture in the generator. Update the fixture periodically.

Tradeoff: Fast generator execution. But the fixture drifts from real Navigator output when knowledge-map changes. Manual maintenance.

### Option C: Build a Navigator-lite for the generator

A simplified function that reads intent-map.yaml for engineer-work, loads the skills/commands/tools at the right depth from KB files, produces a representative output. Doesn't query LightRAG or claude-mem.

Tradeoff: Exercises real knowledge-map data without service dependencies. But duplicates Navigator logic in a simplified form.

---

## Finding 3: heartbeat_context.py dead code

### Option A: Fix the parameter names

Change lines 302-312 in heartbeat_context.py: `messages_count=` → `messages=bundle.chat_messages_as_dicts()` (need to check if this method exists, or transform the data). `events_count=` → `events=bundle.domain_events`. Also need to pass `role_data`, `directives`, `renderer`, etc.

Tradeoff: The HeartbeatBundle becomes a real preembed source. But HeartbeatBundle.chat_messages is a list of dicts with different keys than what build_heartbeat_preembed expects for `messages`.

### Option B: Remove the preembed call from heartbeat_context.py

The orchestrator calls build_heartbeat_preembed directly (orchestrator.py:542-555). heartbeat_context.py's call is redundant. Remove it. The HeartbeatBundle serves format_message() for legacy/fallback only.

Tradeoff: Acknowledges reality — the orchestrator IS the real path. heartbeat_context.py's preembed call was aspirational dead code.

---

## Finding 4: Contributions depth status_only and summary unimplemented

### Option A: Implement in preembed.py

Add elif branches in preembed.py at line 267-268:
- `status_only`: show "✓ type (role) — received" or "✗ type (role) — awaiting" per contribution
- `summary`: show contribution type + from + first 100 chars of content

Tradeoff: Straightforward. 10-15 lines of code. Matches what the config intended.

### Option B: Implement in TierRenderer

Move the entire contribution section rendering to TierRenderer (like format_role_data handles different depths per tier). Preembed calls `renderer.format_contributions(specs, received_set)`.

Tradeoff: More consistent architecture (renderer owns ALL depth decisions). But contributions in preembed are tightly coupled to the synergy matrix loading logic — extracting that is nontrivial.

---

## Finding 5: fleet_mode absent from task preembed

### Option A: Add fleet_state parameter to build_task_preembed

Add `fleet_state: dict = None` parameter. Render as a line after the mode header: `# FLEET: {work_mode} | {cycle_phase} | {backend_mode}`. Orchestrator passes it from the fleet_state_dict it already has.

Tradeoff: Simple. 3 lines of code + 1 parameter. The agent sees fleet state in task context.

### Option B: Include fleet_state in §0 mode header

Extend the existing mode line: `# MODE: task | injection: full | model: X | fleet: work-paused/planning/claude | generated: HH:MM:SS`

Tradeoff: One line instead of two. But the mode line is already long. Could truncate in narrow terminals.

---

## Finding 6: Confirmed plan fixture is a TODO list

### Option A: Write a realistic design plan fixture

Replace the 7-line TODO list with a 20-30 line design plan that demonstrates: architecture rationale ("React component hierarchy under DashboardShell"), data flow ("useFleetStatus hook → MC status API → 4 child components via props"), component relationships ("AgentGrid receives agent[] array, renders StatusCard per agent"), constraints ("existing MC build pipeline, no new dependencies"), acceptance criteria mapping ("TC-001 → AgentGrid renders 10 cards, TC-005 → BudgetGauge shows API %").

Tradeoff: Better demonstration of what the output should look like. But it's still a fixture — the real confirmed plan depends on the architect's design_input and the engineer's reasoning stage output.

### Option B: Generate the plan from the contribution fixtures

Since the generator already has ARCH_CONTRIB and QA_CONTRIB constants, derive the confirmed plan fixture from them. The plan references the architect's approach and maps QA's TC-XXX criteria.

Tradeoff: Shows the traceability chain: contribution → plan → implementation. But adds complexity to the generator.

---

## Finding 7: No events in scenarios

### Option A: Add hardcoded event fixtures to the generator

Create event dicts for TK-01: task dispatched, contributions received (2), fleet_task_accept, 2 commits at 20% and 40%.

Tradeoff: Simple. Shows the WHAT CHANGED section. But doesn't exercise real EventStore. And the orchestrator's event prepend logic (orchestrator.py:671-690) happens AFTER build_task_preembed returns — the generator would need to prepend events manually.

### Option B: The generator calls the event prepend logic separately

After calling build_task_preembed, the generator manually prepends a WHAT CHANGED section the same way the orchestrator does (orchestrator.py:681-688). Uses hardcoded event data but follows the same rendering path.

Tradeoff: Exercises the same rendering format as production. More realistic. But duplicates the orchestrator's event rendering.

---

## Finding 8: context_assembly data not in preembed

### Option A: Selectively bring context_assembly data into preembed

Add task comments (last 5), related tasks (parent + children), and activity summary to build_task_preembed as optional parameters. The orchestrator loads them and passes them. Preembed renders them as new sections after §9.

Tradeoff: Richer preembed. But build_task_preembed already has 9 parameters — adding 3 more makes it unwieldy.

### Option B: Create a unified assembly function

A new function that calls both build_task_preembed AND selectively pulls from context_assembly data, merging them into one output. Replaces the direct build_task_preembed call in the orchestrator.

Tradeoff: Single assembly point. But significant refactor — the orchestrator's data loading logic would need to change.

### Option C: Accept that preembed and context_assembly serve different purposes

Preembed is the push path — fast, every 30 seconds, essential data only. context_assembly is the pull path — on-demand, full data. The agent calls fleet_read_context when they need the richer data. Don't merge them.

Tradeoff: Least disruptive. But the mode header says "fleet_read_context NOT needed" which is misleading if essential data (comments, related tasks) is only available via the pull path.

---

## Finding 9: Confirmed plan loading is brittle

### Option A: Structured comment format

Change fleet_task_accept (fleet/mcp/tools.py) to post comments with a structured prefix: `"[CONFIRMED_PLAN] {plan_content}"`. The orchestrator searches for `"[CONFIRMED_PLAN]"` instead of guessing from substrings.

Tradeoff: Reliable. But requires changing the MCP tool's comment format — existing plans in MC won't match the new pattern.

### Option B: Store confirmed plan in custom fields

Instead of a comment, fleet_task_accept stores the plan in a new custom field `confirmed_plan` on the task. The orchestrator reads it directly.

Tradeoff: Most reliable — no parsing, no substring matching. But TaskCustomFields needs a new field. And confirmed plans can be long — custom fields may have size limits in MC.

### Option C: Tag the comment

fleet_task_accept posts the plan as a comment with a tag like `confirmed_plan`. The orchestrator searches by tag instead of content.

Tradeoff: Clean if MC supports tagged comments. Needs to verify MC API supports comment tags.

---

## Finding 10: Generator skips 7 of 11 pipeline steps

### Option A: Make the generator call the full orchestrator path

Create a `generate_scenario_via_orchestrator()` that sets up mock MC data and calls _refresh_agent_contexts. Reads the written context files and captures them.

Tradeoff: Exercises the real pipeline end-to-end. But _refresh_agent_contexts is async, needs MC mocking, and the orchestrator has many side effects (writing files, querying EventStore, etc.).

### Option B: Extract a pure rendering function from the orchestrator

Factor out the data assembly logic from _refresh_agent_contexts into a testable pure function: `assemble_agent_context(task, agent, fleet_state, ...) → (fleet_text, task_text, knowledge_text)`. Both the orchestrator and the generator call this function. The orchestrator adds the side effects (file writing, event marking). The generator uses it directly.

Tradeoff: Best long-term architecture. Both paths use the same code. But it's a significant refactor of a 300-line function with many dependencies.

### Option C: Incrementally bring missing steps into the generator

For each missing step, add the equivalent to the generator: call Navigator for knowledge-context, prepend events manually, pass fleet_state, etc. The generator becomes a parallel implementation that mirrors the orchestrator's logic.

Tradeoff: Fastest to implement. But creates two parallel paths that can drift. Each new feature needs to be added in two places.

---

## Cross-cutting observation

Findings 1, 7, 8, 10 all trace to the same root: the generator bypasses the real pipeline. Fixing the generator (F10) would automatically fix or reduce F1 (contribution preservation), F7 (events), and F8 (richer data). The question is whether to fix the generator incrementally (Option C for each) or restructure it to use the real path (Option A or B).

## Relationships

- BUILDS ON: [Analysis: Output Quality Blockers](analysis-output-quality-blockers.md)
- FEEDS INTO: reasoning stage (plan)
