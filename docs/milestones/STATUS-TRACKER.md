# Fleet Status Tracker — Where We Actually Are

## Last Updated: 2026-04-07

---

## FLEET STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| Gateway | ✅ RUNNING | PID stable, NODE_OPTIONS=4GB heap, OOM fix applied |
| MC Backend | ✅ RUNNING | Docker, 10/10 agents online |
| MC Frontend | ✅ RUNNING | http://localhost:3000 |
| Orchestrator | ✅ RUNNING | 30s cycles, conservative effort, NameError bugs fixed |
| Sync daemon | ✅ RUNNING | 60s interval |
| Monitor daemon | ✅ RUNNING | 300s interval |
| Auth daemon | ✅ RUNNING | 120s interval |
| IRC | ✅ RUNNING | miniircd on port 6667, 10 channels configured |
| The Lounge | ✅ RUNNING | http://localhost:9000 (fleet/fleet) |
| ntfy | ✅ RUNNING | 3 topics configured |
| Agents | ✅ 10/10 ONLINE | Template sync working, last_seen_at fix applied |
| Board | ✅ CLEAN | Fresh board, 0 tasks (ready for PM to populate) |
| Communication | ✅ VERIFIED | 8-point check passed (PR8) |

---

## SETUP IaC STATUS

| Script | Status | Notes |
|--------|--------|-------|
| setup.sh | ✅ WORKS END-TO-END | Ran 3 times, bugs fixed each time |
| install-openclaw.sh | ✅ OK | |
| configure-auth.sh | ✅ OK | |
| configure-openclaw.sh | ✅ OK | |
| register-agents.sh | ✅ OK | |
| setup-irc.sh | ✅ OK | #fleetS typo fixed |
| start-fleet.sh | ✅ OK | 4GB heap, fail-hard on timeout |
| setup-mc.sh | ✅ OK | Retry sync with timeout, no duplicate sync |
| setup-lounge.sh | ✅ OK | |
| clean-gateway-config.sh | ✅ OK | Session ID derivation from openclaw_session_id |
| configure-agent-settings.sh | ✅ OK | Rewritten: reads agent-hooks.yaml, deploys hooks |
| push-agent-framework.sh | ✅ OK | Updated: deploys generated TOOLS.md |
| push-soul.sh | ✅ OK | Updated: role-aware sub-agent symlinks |
| generate-tools-md.py | ✅ OK | Python rewrite: 7-layer TOOLS.md generation |
| validate-tooling-configs.py | ✅ OK | Cross-validation: 0 errors |
| sync-agent-crons.sh | ✅ OK | CRON deployment (needs gateway) |
| reprovision-agents.sh | ✅ OK | Updated: includes push-soul.sh |
| configure-board.sh | ✅ OK | 14 custom fields, 20 tags |

---

## BUGS FIXED THIS SESSION

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| TOOLS.md parser | MC template generates markdown format, parser expects plain | Strip `- ` and backticks in _parse_tools_md |
| Agents stuck at "provisioning" | mark_provision_complete didn't set last_seen_at | Always set last_seen_at when status=online |
| Agents show "offline" after setup | last_seen_at only set on first provision (is None check) | Removed is None — always refresh |
| Board lead ID mismatch | clean-gateway-config used mc-{id} for board lead | Derive from openclaw_session_id |
| Gateway config anomaly | Step 8 shrinks config, gateway rejects size drop | Reset config-health.json |
| Gateway OOM crash | Template sync rapid config.patch → SIGUSR1 storm → heap exhaustion | NODE_OPTIONS=4GB + no force_bootstrap on final sync |
| Orchestrator crash (DRIVER_AGENTS) | Undefined constant referenced | Inline default list |
| Orchestrator crash (config) | _dispatch_ready_tasks missing config parameter | Added config parameter |
| IRC channel typo | #fleetS instead of #fleet | Fixed to #fleet |
| Hardcoded username | "Jean Fortin" in gateway/setup.py | FLEET_USER_NAME env var |
| Template sync hangs | No timeout on curl in setup-mc.sh | Added 180s timeout + retry logic |
| setup.sh hangs | Gateway not starting (config anomaly) | Reset health checkpoint + fail-hard |

---

## VENDOR PATCHES (survive fresh git clone)

| Patch | File | Purpose |
|-------|------|---------|
| 0001 | skills_marketplace.py | Category/risk upsert fix |
| 0002 | provisioning_db.py | TOOLS.md parser handles markdown format |
| 0003 | db_agent_state.py | last_seen_at set on provision complete |

---

## DSPD STATUS

| Item | Status | Notes |
|------|--------|-------|
| Docker compose | ✅ BUILT | docker-compose.plane.yaml, 12 services |
| plane.env.example | ✅ BUILT | All creds marked ⚠️ CHANGE |
| setup.sh | ✅ BUILT | install/start/stop/status/validate/upgrade/uninstall |
| plane-configure.sh | ✅ BUILT | Superuser + workspace + API token + god-mode + password |
| plane-seed-mission.sh | ✅ BUILT | Reads config/mission.yaml + per-project board configs |
| config/mission.yaml | ✅ BUILT | 4 projects, per-project states, modules, labels, estimates |
| config/aicp-board.yaml | ✅ BUILT | LocalAI 5 stages as epics, pages, acceptance criteria |
| config/fleet-board.yaml | ✅ BUILT | Fleet modules, operational status page |
| config/dspd-board.yaml | ✅ BUILT | DSPD phases, architecture page |
| config/nnrt-board.yaml | ✅ BUILT | Pipeline modules, assessment page |
| dspd/config.py | ✅ BUILT | All settings from env, no hardcoded values |
| dspd/webhooks.py | ✅ BUILT | HMAC-SHA256, event handlers, ASGI receiver |
| fleet/infra/plane_client.py | ✅ BUILT | Typed async API client |
| fleet/cli/plane.py | ✅ BUILT | create/list/sync/status CLI |
| fleet/core/plane_sync.py | ✅ BUILT | Bidirectional Plane ↔ OCMC sync |
| Unit tests | ✅ 78 PASSING | config, webhooks, plane_client, plane_sync |
| Integration tests | ✅ BUILT | Live Plane API CRUD |
| Plane deployed | ✅ RUNNING | 12 containers, all healthy |
| Mission seeded | ✅ DONE | 4 projects via REST API, 22 modules, 76 labels, 9 pages |
| Fleet connected | ✅ DONE | Credentials in fleet .env, fleet plan list-projects works |
| Agent accounts | ✅ DONE | 12 users (admin + 10 agents + service), visible in picker |
| Issue types | ✅ DONE | Epic, Story, Task, Bug, Spike, Chore with hierarchy |
| Saved views | ✅ DONE | 24 views (6 per project) |
| Module links | ✅ DONE | 26 GitHub + docs cross-references |
| Module leads | ✅ DONE | 22 lead assignments from fleet-roles.yaml |
| Starter issues | ✅ DONE | 13 issues (4 epics + 9 tasks), typed, assigned, in cycles |
| Issue relations | ✅ DONE | 9 cross-project + intra-project dependencies |
| Workspace links | ✅ DONE | 7 home page quick links (GitHub, MC, IRC, LocalAI) |
| Rich HTML pages | ✅ DONE | Tables, blockquotes, code blocks, links — no more pre blocks |
| Milestone docs | ✅ DONE | 47 milestones across 6 documents |
| config/fleet-roles.yaml | ✅ DONE | All 10 agents with roles, skills, capabilities |
| config/fleet-members.yaml | ✅ DONE | Agent accounts, issue types, views — IaC |
| plane-setup-members.sh | ✅ DONE | Creates agents, types, views from config |
| plane-setup-content.sh | ✅ DONE | Creates links, leads, welcome issues, starter issues |

---

## AICP/LocalAI STATUS

| Item | Status | Notes |
|------|--------|-------|
| LocalAI container | ✅ RUNNING | Healthy, 9 models loaded |
| hermes (7B) | ✅ WORKING | 80s cold, 1s warm, GPU |
| hermes-3b (3B) | ✅ WORKING | 10s cold, 1.2s warm, GPU — target for heartbeats |
| codellama (7B) | ✅ LOADED | Not benchmarked yet |
| phi-2 (2.7B) | ✅ LOADED | CPU-only, fallback |
| OpenAI-compatible API | ✅ VERIFIED | Chat completions working |
| AICP package | ✅ EXISTS | aicp/ with core, backends, guardrails, cli, config, mcp |
| Stage 1 assessment | 🔶 IN PROGRESS | Models working, benchmarks started |
| Stage 2 inference router | ❌ NOT STARTED | Needs Stage 1 complete |
| Stages 3-5 | ❌ NOT STARTED | Long-term |

---

## EVENT BUS STATUS (The Nervous System)

| Component | File | Status | Tests |
|-----------|------|--------|-------|
| Event Store | fleet/core/events.py | ✅ BUILT | 15 tests |
| Event Router | fleet/core/event_router.py | ✅ BUILT | 16 tests |
| Chain Runner | fleet/core/chain_runner.py | ✅ BUILT | 9 tests |
| PLANE Surface | fleet/core/event_chain.py | ✅ ADDED | — |
| MCP Event Emission | fleet/mcp/tools.py | ✅ 10 tools emit events | — |
| Agent Event Feed | fleet/mcp/tools.py | ✅ fleet_read_context | — |
| Plane Watcher | fleet/core/plane_watcher.py | ✅ BUILT | — |
| Sync Events | fleet/cli/sync.py | ✅ WIRED | — |
| Error Reporting | fleet/mcp/tools.py | ✅ WIRED | — |
| Plane MCP Tools (7) | fleet/mcp/tools.py | ✅ BUILT | — |
| Fleet-Plane Skill | .claude/skills/fleet-plane/ | ✅ BUILT | — |
| Chain Wiring (M-EB15) | — | ❌ NOT DONE | fleet_task_complete still monolith |
| Adaptive Display (M-EB16) | — | ❌ NOT DONE | Same event → diff format per channel |
| IaC Sync (M-EB18) | — | ❌ NOT DONE | Config differential tracking |

**Daemons:** 5 concurrent (sync 60s, auth 120s, monitor 300s, orchestrator 30s, plane-watcher 120s)
**MCP Tools:** 66 total (30 generic fleet + 36 role-specific group calls)
**Skills:** 30 workspace + 7 gateway = 37
**Sub-agents:** 12 custom definitions
**Tests:** 2075 passing (was 381 on 2026-03-31)

---

## TOOLS SYSTEM ELEVATION (updated 2026-04-08)

8-phase effort making every agent a top-tier expert with 7 capability layers.
Session index: `docs/milestones/active/tools-system-session-index.md`

| Phase | What | Status | Key Metric |
|-------|------|--------|------------|
| A: Foundation | 30 elevated tools, 9 building blocks, chain builders, stage-aware effort | ~80% | 93 tool operation tests, 2249 total |
| B: MCP+Plugins | Per-agent mcp.json, plugin evaluation (4 INSTALL) | ~45% | 7/10 workspaces. Install blocked on gateway |
| C: Group Calls | 36 role-specific tools across 10 roles | ~80% | 89 tests (36 registration + 53 behavioral) |
| D: Skills | **78 workspace skills, 69/69 deep skills, 10/10 roles at 100%** | **~95%** | 77 skill-stage refs, all verified |
| E: CRONs+Orders | 17 CRONs, 14 standing orders, sync script | ~35% | Deployment blocked on gateway |
| F: Sub-agents+Hooks | 12 sub-agents, 10 hooks, 10 role-specific heartbeats | ~50% | All 10 agents: full 7-position directive chain |
| G: Generation | Python pipeline, 66 chain docs (30 generic + 36 role) | ~90% | TOOLS.md per agent regenerated with all skills |
| H: Validation | 14 config checks, 2249 tests, 31 heartbeat+MCP tests | ~55% | 0 errors, 77 skill refs verified |

**Test suite: 2218 passed, 0 failures, 19 skipped.**

**New scripts:**

| Script | Purpose |
|--------|---------|
| `generate-tools-md.py` | Generate per-agent TOOLS.md from all 7 layers |
| `generate-agents-md.py` | Generate per-agent AGENTS.md (synergy + colleagues) |
| `validate-tooling-configs.py` | Cross-validate all tooling configs (0 errors) |
| `sync-agent-crons.sh` | Deploy CRONs from agent-crons.yaml to gateway |
| `configure-agent-settings.sh` | ✅ REWRITTEN: reads agent-hooks.yaml, deploys hooks |
| `push-soul.sh` | ✅ UPDATED: role-aware sub-agent symlinks |
| `push-agent-framework.sh` | ✅ UPDATED: deploys TOOLS.md + AGENTS.md |
| `reprovision-agents.sh` | ✅ UPDATED: includes push-soul.sh step |

**New configs:**

| Config | Entries |
|--------|--------|
| `config/skill-stage-mapping.yaml` | ~105 entries (stages × roles × 38 skills) |
| `config/agent-crons.yaml` | 17 CRON jobs across 8 roles |
| `config/standing-orders.yaml` | 14 standing orders across 10 roles |
| `config/agent-hooks.yaml` | 6 hooks (2 default + 4 role-specific) |
| `config/tool-chains.yaml` | 30 generic + 36 role-specific = 66 chain docs (100% coverage) |
| `config/tool-roles.yaml` | ✅ UPDATED: cross-role tools section |
| `config/agent-tooling.yaml` | ✅ UPDATED: sub_agents + plugins per role |
| `config/plugin-evaluation.yaml` | 4 INSTALL, 5 DEFER, 3 SKIP |
| `config/synergy-matrix.yaml` | Contribution requirements per role |

**Runtime wiring (code modules):**

| Module | What It Does |
|--------|-------------|
| `fleet/core/skill_recommendations.py` | Cached YAML → stage+role skill recs in context/preembed |
| `fleet/core/standing_orders.py` | Cached YAML → per-role authority + orders in heartbeat preembed |
| `fleet/core/model_selection.py` | Stage-aware effort floor (reasoning/investigation → high) |
| `fleet/cli/dispatch.py` | Stage-aware model_config for Claude backend dispatch records |

**New tests:**

| Test File | Tests | What |
|-----------|-------|------|
| `test_role_tools.py` | 65 | Registration + behavioral for all 10 roles |
| `test_tooling_pipeline.py` | 52 | Config parsing, cross-refs, TOOLS.md output |
| `test_tool_operations.py` | 84 | Generic tool behavioral outcomes |

---

## WHAT'S ACTUALLY NEXT

1. ✅ ~~Start MC + gateway~~ — done
2. ✅ ~~Verify communication e2e~~ — 8/8 passed
3. ✅ ~~Fix orchestrator bugs~~ — NameError + config fixed
4. ✅ ~~Fix gateway OOM~~ — 4GB heap + no force_bootstrap
5. ✅ ~~DSPD IaC built~~ — configs, scripts, Python, tests
6. ✅ ~~LocalAI assessment started~~ — models working, benchmarks
7. ✅ ~~Docs cleaned~~ — organized into active/design/archive
8. ✅ ~~Deploy Plane~~ — 12 containers running, seeded via REST API
9. ✅ ~~Mission seeded~~ — 4 projects, 22 modules, 76 labels, 9 pages, 13 issues
10. ✅ ~~Connect fleet to Plane~~ — credentials in fleet .env, CLI works
11. ✅ ~~Plane platform config~~ — agents, types, views, links, leads, relations
12. ✅ ~~Milestone docs~~ — 47 milestones across 6 Plane documents
13. ✅ ~~Build Plane MCP tools (M-SC04)~~ — 7 tools, PM has Plane access
14. ✅ ~~Build chain runner (M-SC02)~~ — 6 surfaces, cross-refs, event emission
15. ✅ ~~Build event bus (M-EB01-20)~~ — 20/20 milestones, 7 event sources
16. ✅ ~~Plane sync to git~~ — pages, issues, stickies, comments auto-committed
17. **Execute one real task end-to-end** — dispatch, work, PR, review, done
18. **PM first heartbeat with Plane** — reads sprint, creates OCMC tasks
19. **AICP Stage 1 complete** — cluster verification, full benchmarks
20. **Fleet 24h observation** — stable daemons, no OOM, agents responsive
21. **Resume autonomous flow** — PM drives sprints from Plane, agents execute

---

## NEW STRATEGIC MILESTONES (2026-03-31)

| Set | Document | Milestones | Status |
|-----|----------|-----------|--------|
| Storm Prevention | `storm-prevention-system.md` | M-SP01-09 (9) | DESIGN |
| Budget Modes | `budget-mode-system.md` | M-BM01-06 (6) | DESIGN |
| Multi-Backend Router | `multi-backend-routing-engine.md` | M-BR01-08 (8) | DESIGN |
| Labor Attribution | `labor-attribution-and-provenance.md` | M-LA01-08 (8) | DESIGN |
| Iterative Validation | `iterative-validation-and-challenge-loops.md` | M-IV01-08 (8) | DESIGN |
| Model Upgrade Path | `model-upgrade-path.md` | M-MU01-08 (8) | DESIGN |
| **Total new** | | **47** | **All DESIGN** |

Driven by PO requirements for multi-model routing, budget control per order,
labor attribution with trainee tagging, adversarial challenge loops, and lessons
from the March 2026 catastrophic process storms. See MASTER-INDEX.md for details.

---

## THINGS BUILT BUT NEVER VERIFIED RUNNING

- fleet_chat tool — agents have it but never used it live
- fleet_notify_human — ntfy works but agents never called it
- fleet_escalate — never called by an agent
- Budget monitor (OAuth API) — code in orchestrator, never triggered
- Outage detector — code in orchestrator, never triggered
- All 10 heartbeat rewrites — pushed but agents haven't read them
- Review gates — fleet_task_complete populates but fleet-ops never reviewed
- Agent roles / PR authority — coded but never enforced in real flow
- Plane ↔ OCMC sync — code exists, never tested end-to-end