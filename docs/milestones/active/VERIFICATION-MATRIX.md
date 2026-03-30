# Verification Matrix — Live Testing

**Date:** 2026-03-30
**Status:** In progress — to be filled one by one with REAL live verification
**Infrastructure:** MC ✓ | Gateway ✓ | Plane ✓ | LocalAI ✓ | IRC ✓

---

## A: Foundation

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| A01 | task_readiness on OCMC | Create task, verify field visible on card | ✅ | MC API: type=integer, visibility=always, description="Task readiness percentage (0-100)" |
| A02 | task_readiness on Plane | Check Plane label readiness:50 exists | ✅ | Plane API: 12 readiness labels (0,5,10,20,30,50,70,80,90,95,99,100) + 5 stage labels on OF project |
| A03 | requirement_verbatim on OCMC | Set verbatim on task, verify in API | ✅ | MC API: type=text_long, visibility=always, description="PO exact words" |
| A04 | requirement_verbatim on Plane | Write verbatim, check Plane description | ⚠️ PARTIAL | Verbatim VISIBLE as blockquote in Plane BUT HTML comments stripped by Plane sanitizer — programmatic extraction fails. Need data-attribute or different marker approach. |
| A05 | task_stage on both | Set stage, verify on OCMC + Plane label | ✅ | MC API: type=text, visibility=always, description="Methodology stage" |
| A06 | Sync new fields | Change readiness on Plane, verify OCMC updates | | |
| A07 | Plane state metadata | Change Plane state, verify OCMC status | | |
| A08 | Conflict resolution | Change same field on both, verify winner | | |

## B: Methodology

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| B01 | Stage progression | Create epic, verify 5 required stages | | |
| B02 | Conversation protocol | Set stage=conversation, verify instructions | | |
| B03 | Analysis protocol | Set stage=analysis, verify instructions | | |
| B04 | Investigation protocol | Set stage=investigation, verify instructions | | |
| B05 | Reasoning protocol | Set stage=reasoning, verify instructions | | |
| B06 | Work protocol | Set stage=work + readiness=99, verify dispatch | | |
| B07 | Observability | Change stage, verify event emitted | | |
| B08 | Orchestrator aware | Set readiness=50, verify NOT dispatched | | |
| B09 | Standards | Check analysis_document standard has 5 required fields | | |

## C: Teaching

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| C01 | Lesson store | Verify 8 templates loaded | | |
| C02 | Injection mechanism | Format lesson, verify TEACHING SYSTEM header | | |
| C03 | Comprehension verification | Evaluate good + bad response | | |
| C04 | Adapted lessons | Adapt deviation lesson with context, verify content | | |
| C05 | Lesson tracking | Record lesson, verify history query | | |
| C06 | Integration | Doctor medium severity → trigger_teaching | | |

## D: Immune System

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| D01 | Doctor architecture | Run doctor cycle against live board | | |
| D02 | Detect laziness | 5SP task completed in 1min → detected | | |
| D03 | Detect deviation | Commit during conversation → detected | | |
| D04 | Detect confident-but-wrong | 3 corrections → prune decision | | |
| D05 | Detect stuck | No activity 2hrs → detected | | |
| D06 | Detect context contamination | Disease category exists | | |
| D07 | Detect protocol violation | fleet_commit during conversation → blocked | | |
| D08 | Response prune | Critical severity → prune action | | |
| D09 | Response force compact | Stuck → compact action | | |
| D10 | Response trigger teaching | Medium severity → teach action | | |

## E: Platform

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| E01 | Orchestrator wired | Doctor step in orchestrator cycle | | |
| E02 | Gateway client | prune/compact/inject functions callable | | |
| E03 | Event types | 15 new event types registered | | |
| E04 | Heartbeat context | Stage instructions in bundle | | |
| E06 | MCP stage enforcement | fleet_commit blocked in conversation | | |

## F: Control Surface

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| F01 | fleet_config backend | Read fleet_config from live board | | |
| F02 | FleetControlBar | Component file exists in patches | | |
| F06 | Fleet state reader | Read work_mode from live board | | |
| F07 | Mode-aware orchestrator | work-paused blocks dispatch | | |
| F08 | Directives | Post directive to board memory, parse it | | |
| F09 | Mode-aware heartbeats | Fleet state in heartbeat bundle | | |
| F10 | Mode change events | Change mode, verify event created | | |

## T: Transpose

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| T01 | Transpose engine | Render analysis_document → HTML + roundtrip | | |
| T02 | Artifact MCP tools | fleet_artifact_create/read/update exist | | |
| T03 | Artifact tracker | Empty analysis → 0%, full → 100% | | |
| T04 | Plane integration | HTML markers in rendered output | | |
| T05 | Standards validation | Completeness returns missing fields | | |
| T06 | Subtask tracking | check_subtask_coverage returns counts | | |
| T07 | HTML templates | Tables in investigation, blockquotes in plan | | |

## Context System

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| ML-F01 | Data assembly | assemble_task_context from live task | | |
| ML-F02 | Role providers | 13 roles registered | | |
| ML-I02 | Aggregate MCP tools | fleet_task_context + fleet_heartbeat_context | | |
| TP-F02 | Task pre-embed | Build from live task, <1000 chars | | |
| HP-F01 | Heartbeat pre-embed | Build with counts + fleet state | | |
| HP-I02 | Context writer | write_task_context creates file | | |

## Event Bus

| # | Milestone | Live Test | Status | Evidence |
|---|-----------|-----------|--------|----------|
| EB | Event store | Append + query works | | |
| EB | Event display | Renders on IRC + board memory + ntfy | | |
| EB | System tags | immune-system, teaching-system, methodology tags | | |

---

## How to Fill This Matrix

Test each item one by one against the live fleet:

1. Run the specific test or command
2. Verify the result matches expected behavior
3. Mark Status: ✅ PASS or ❌ FAIL
4. Record evidence (command output, API response, screenshot reference)

This is not automated tests — this is live verification that the
systems work in the real fleet environment.