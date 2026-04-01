# System 1: Methodology

**Source:** `fleet/core/methodology.py` (477 lines), `fleet/core/stage_context.py` (215 lines), `fleet/core/phases.py` (60+ lines)
**Status:** ✅ Live verified (VERIFICATION-MATRIX.md)
**Design docs:** `methodology-system/01-07`, `fleet-elevation/03`

---

## Purpose

Defines HOW agents work through tasks. Every task has a stage and a readiness percentage. Stages advance when methodology checks pass and the PO confirms. Work stage is only entered at readiness 99-100%.

## Key Concepts

### Stages (methodology.py)

5 stages in order: `CONVERSATION → ANALYSIS → INVESTIGATION → REASONING → WORK`

| Stage | Agent Must | Agent Must NOT | Readiness Suggestion |
|-------|-----------|---------------|---------------------|
| conversation | Discuss with PO, ask questions, extract requirements | Write code, commit, produce deliverables | 10 |
| analysis | Read codebase, produce analysis document, reference files | Produce solutions, commit | 30 |
| investigation | Research options (MULTIPLE), cite sources | Decide on approach, commit | 50 |
| reasoning | Produce plan referencing verbatim, specify files | Start implementing, commit | 80 |
| work | Execute confirmed plan, fleet_commit, fleet_task_complete | Deviate from plan, add scope | 99 |

### Task Types Skip Stages (methodology.py:44-91)

| Type | Required Stages |
|------|----------------|
| epic | All 5 |
| story | conversation, reasoning, work |
| task/subtask | reasoning, work |
| bug | analysis, reasoning, work |
| spike | conversation, investigation, reasoning (NO work) |
| concern | conversation, analysis, investigation (NO work) |

### Readiness (methodology.py:367-389)

Valid values: `0, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99, 100`

Strategic checkpoints: 0 (nothing), 50 (direction review), 90 (final review).

**Work stage requires readiness >= 99** (lines 196, 339-341).

### Stage Checks (methodology.py:213-362)

Each stage has explicit boolean checks. ALL must pass before `can_advance = True`:

- **conversation:** has_verbatim_requirement, has_po_response, no_open_questions
- **analysis:** has_analysis_document, po_reviewed
- **investigation:** has_research_document, multiple_options_explored, po_reviewed
- **reasoning:** has_plan, plan_references_verbatim, plan_specifies_files, po_confirmed_plan
- **work:** readiness >= 99, has_commits, has_pr, acceptance_criteria_met, required_tools_called

### Stage Instructions (stage_context.py)

Full MUST do / MUST NOT do / CAN produce / How to advance templates. Injected into agent context via preembed.py. Each stage explicitly blocks `fleet_commit` and `fleet_task_complete`.

### Delivery Phases (phases.py)

Distinct from stages. Stages = how you work. Phases = how mature the deliverable is.

Defined by PO in `config/phases.yaml`:
- standard: ideal → conceptual → poc → mvp → staging → production
- release: alpha → beta → rc → release

Each phase: standards dict, required_contributions list, gate bool (requires PO approval).

### Transition Tracking (methodology.py:395-477)

`MethodologyTracker` records every stage transition: task_id, from/to stage, authorized_by, readiness before/after, checks passed/total. Emits `fleet.methodology.stage_changed` event.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Stage Context** | Provides stage instructions for preembed | Methodology → Context |
| **Preembed** | Injects stage instructions into agent context | Methodology → Preembed |
| **MCP Tools** | `_check_stage_allowed()` blocks work tools in non-work stages | Methodology → MCP |
| **Doctor** | `detect_protocol_violation()` catches work tools in wrong stage | Methodology → Immune |
| **Standards** | Standards define what artifacts are required per stage | Standards → Methodology |
| **Artifact Tracker** | Completeness → suggested readiness mapping | Tracker → Methodology |
| **Phases** | Required contributions per phase gate | Phases → Methodology |
| **Events** | Stage transitions emit events | Methodology → Events |

## What's Needed

- [ ] Contribution flow: brain creates contribution subtasks when task enters REASONING
- [ ] Standards injection: relevant standards loaded based on current artifact type
- [ ] Phase gate enforcement: PO approval required at phase boundaries
