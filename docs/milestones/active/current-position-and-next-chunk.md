# Current Position & Next Chunk Plan

**Date:** 2026-04-06
**Purpose:** Where we are, what's immediately ahead, in what order, and why.

---

## Where We Are

### Just Completed (This Session)
- Heartbeat architecture refactored: per-agent CRON intervals from openarms.json
- Brain evaluation writes decisions every cycle, MC liveness at CRON tempo
- Budget mode changes propagate to HeartbeatRunner intervals + MC heartbeat_config
- MC patch 0012: per-agent OFFLINE_AFTER from heartbeat_config.every
- Daemon stability: setsid isolation, startup grace period, timestamp seeding
- Teardown script rewritten with mask/unmask
- Gateway service stable path (fnm resolution)
- Setup.sh flow fixes: template sync ordering, reprovisioning, IRC dedup

### What Works Right Now
- 10/10 agents registered in MC
- Gateway running on stable path, correct port (18789)
- Orchestrator cycling every 15-30s (budget-adjusted)
- Brain evaluates all agents, writes .brain-decision.json files
- CRON fires at per-agent intervals (10m fleet-ops through 28m accountability-generator)
- MC heartbeat_config synced with staggered intervals
- Per-agent OFFLINE_AFTER (1.5x interval) via patch 0012
- Budget monitoring reads real Claude OAuth quota
- FleetControlBar shows real values, budget mode changes propagate
- Event bus fires, routes, reaches agents in heartbeat context
- Doctor runs step 2 every cycle (4/11 detections active)
- All 10 vendor patches apply cleanly

### What's Broken Right Now
1. **Dispatch gates on readiness >= 99** — nothing gets dispatched to agents
2. **task_stage never set** — methodology system has no automation to set initial stage
3. **Agent identity: 0/10 built** — agents run as blank slates
4. **Gateway reads 3/8 agent files** — IDENTITY, SOUL, TOOLS, AGENTS, HEARTBEAT not injected
5. **Contribution system dormant** — code exists, orchestrator never calls it
6. **Challenge system dormant** — code exists, fleet_task_complete never triggers it
7. **Brain decisions possibly not honored by gateway** — needs verification
8. **Wake events write brain decision but don't properly trigger HeartbeatRunner**
9. **3/10 agents sometimes miss .mcp.json** — provision failures during gateway restart

---

## The Next Chunk

### Scope: "First Live Task End-to-End"

The goal is to get ONE task through the full lifecycle: inbox -> conversation -> analysis -> reasoning -> work -> review -> done. With real agents, real Claude calls, real methodology enforcement.

### Logical Order

**Block A: Unblock Dispatch (Foundation)**
These changes let tasks reach agents at any readiness level.

| # | Item | What | Files | Effort |
|---|------|------|-------|--------|
| A1 | Remove readiness gate from dispatch | Change `readiness >= 99` filter to include ALL assigned inbox tasks | orchestrator.py:1192 | 30min |
| A2 | Add readiness-to-stage mapping | Function that maps readiness % to stage name | methodology.py or new | 1h |
| A3 | Auto-set task_stage | Orchestrator sets task_stage based on readiness when dispatching | orchestrator.py dispatch section | 1h |
| A4 | Stage drives dispatch context | Pass stage + protocol text in dispatch message | dispatch.py, preembed.py | 1h |
| A5 | Verify MCP tool gating works with auto-set stages | Test: conversation stage blocks fleet_commit | manual test | 30min |

**Block B: Agent Identity (Minimum Viable)**
Agents need to know who they are. Full 8-layer onion is 20-40h. Minimum viable: write CLAUDE.md per role with identity + rules + tools.

| # | Item | What | Files | Effort |
|---|------|------|-------|--------|
| B1 | Write fleet-ops CLAUDE.md | Board lead, reviews, governance | agents/fleet-ops/CLAUDE.md | 2h |
| B2 | Write project-manager CLAUDE.md | Sprint planning, task assignment | agents/project-manager/CLAUDE.md | 2h |
| B3 | Write software-engineer CLAUDE.md | Implementation, coding | agents/software-engineer/CLAUDE.md | 2h |
| B4 | Write remaining 7 agent CLAUDE.md | Per-role identity | agents/*/CLAUDE.md | 7h |
| B5 | Fix gateway injection order | Read all 8 layers with correct char limits | gateway executor + ws_server | 3h |
| B6 | Deploy agent files via push-agent-framework.sh | Push to all workspaces | scripts/push-agent-framework.sh | 30min |

**Block C: Brain Gate Verification**
Verify the gateway honors brain decisions. Without this, every heartbeat calls Claude ($$$).

| # | Item | What | Files | Effort |
|---|------|------|-------|--------|
| C1 | Verify OpenArms build includes brain gate code | Check heartbeat-runner.ts in running binary | inspection | 30min |
| C2 | Test brain-silent path end-to-end | Agent idle, brain says silent, verify no Claude call | manual test | 1h |
| C3 | Test brain-wake path | Assign task, brain says wake, verify Claude fires | manual test | 1h |
| C4 | Fix if broken | If gateway doesn't honor, patch heartbeat-runner.ts | openarms source | 2-4h |

**Block D: Wake & Dispatch Flow**
When a task is assigned, the agent should wake immediately and start working.

| # | Item | What | Files | Effort |
|---|------|------|-------|--------|
| D1 | Instant wake on assignment | Orchestrator detects assigned inbox task, writes wake decision, calls MC heartbeat, injects context | orchestrator.py | 2h |
| D2 | Stage-appropriate dispatch message | Based on task_stage, build dispatch message with correct protocol text | dispatch.py | 1h |
| D3 | PM wake for unassigned tasks | Already exists (step 4), verify brain decision written | orchestrator.py | 30min |
| D4 | Verify dispatch -> agent receives -> agent acts | End-to-end manual test | manual test | 2h |

**Block E: Review & Completion**
After agent works, task goes to review, fleet-ops reviews.

| # | Item | What | Files | Effort |
|---|------|------|-------|--------|
| E1 | Verify fleet_task_complete flow | Agent completes, PR created, review gates built | manual test | 1h |
| E2 | Fleet-ops wake for pending reviews | Already exists (step 4), verify | orchestrator.py | 30min |
| E3 | Approval flow | fleet-ops approves/rejects via fleet_approve tool | manual test | 1h |

### Total Effort for "First Live Task"

| Block | Items | Effort |
|-------|-------|--------|
| A: Unblock Dispatch | 5 | 4h |
| B: Agent Identity | 6 | 17h |
| C: Brain Gate | 4 | 2-5h |
| D: Wake & Dispatch | 4 | 5.5h |
| E: Review & Completion | 3 | 2.5h |
| **Total** | **22** | **31-34h** |

---

## After the First Live Task

### Next Chunks (In Order)

**Chunk 2: Cross-Agent Collaboration (8-16h)**
- Wire contribution detection to orchestrator
- Auto-create contribution subtasks
- Gate work stage on contribution completeness
- Test: architect reviews software-engineer's design before coding

**Chunk 3: Quality Assurance (4-8h)**
- Wire challenge system to fleet_task_complete
- Gate approval on challenge_status
- Test: automated challenge validates agent's work

**Chunk 4: Full Doctor Coverage (8-12h)**
- Implement remaining 7 disease detections
- Complete teaching templates
- Test: doctor catches lazy agent, teaches, verifies comprehension

**Chunk 5: Session Telemetry (4h)**
- Wire orchestrator to session_telemetry.py
- Feed real token/cache/duration data to labor attribution
- Test: labor stamp has real cost data

**Chunk 6: Plane Round-Trip (4-8h)**
- Test bidirectional Plane sync end-to-end
- PM creates tasks from Plane sprint
- Test: Plane issue -> OCMC task -> agent work -> PR -> Plane done

**Chunk 7: Standards Injection (4h)**
- Inject artifact-type standards into agent context
- Per-role standards in heartbeat preembed
- Test: agent sees analysis standard when in analysis stage

---

## Design Decisions Still Needed

Before implementing Block A, PO confirmation needed on:

1. **Readiness-to-stage mapping boundaries** — proposed: 0-20 conversation, 20-50 analysis, 50-80 investigation, 80-99 reasoning, 99+ work. Are these right?

2. **Should readiness auto-increment?** The PO said "increase of readiness has to come from clear evaluation confirmed with PO." If so, orchestrator never auto-increments — only PO or PM with PO confirmation.

3. **Can tasks skip stages?** The methodology docs say simple tasks can skip early stages. How does the orchestrator know? By task_type? (bug -> skip to analysis, spike -> stop at investigation, epic -> all stages)

4. **What happens at readiness=0 with no stage?** New task, no readiness set, no stage. Should orchestrator set stage=conversation and dispatch? Or wait for PO to set readiness first?

5. **Agent files: full 8-layer or CLAUDE.md first?** Full build is 20-40h per agent. Minimum viable (CLAUDE.md with identity+rules) is 2h per agent. Gateway fix (read 8 files) is separate.

---

## Continuity Notes

This document covers the **immediate next chunk** (31-34h to first live task) and **6 follow-on chunks** (32-48h additional). Total scope: ~70-80h of work to reach autonomous multi-agent operation with quality gates.

Beyond that, ~300 Phase 2 Infrastructure milestones and ~300 Phase 3 Feature milestones remain. Those are documented in `complete-roadmap.md` and `MASTER-INDEX.md`.

The LightRAG knowledge graph has 2,694 entity labels covering the fleet architecture. It can be queried for relationship discovery but is limited for line-level debugging. The second batch (text indexing) hasn't been tested for relevance yet.
