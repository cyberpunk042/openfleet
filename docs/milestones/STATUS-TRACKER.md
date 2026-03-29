# Fleet Status Tracker — Where We Actually Are

## Last Updated: 2026-03-29

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
| configure-agent-settings.sh | ✅ OK | |
| push-agent-framework.sh | ✅ OK | |
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
**MCP Tools:** 20 total (13 fleet + 7 Plane)
**Skills:** 7 Claude Code skills
**Tests:** 381 passing

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
13. **Build Plane MCP tools (M-SC04)** — PM needs Plane access from sessions
14. **Build chain runner (M-SC02)** — MCP tools need to emit event chains
15. **Execute one real task end-to-end** — dispatch, work, PR, review, done
16. **PM first heartbeat with Plane** — reads sprint, creates OCMC tasks
17. **AICP Stage 1 complete** — cluster verification, full benchmarks
18. **Build sync worker (M-SW01-08)** — real-time cross-platform bridge
19. **Fleet 24h observation** — stable daemons, no OOM, agents responsive
20. **Resume autonomous flow** — PM drives sprints from Plane, agents execute

---

## THINGS BUILT BUT NEVER VERIFIED RUNNING

- fleet_chat tool — agents have it but never used it live
- fleet_notify_human — ntfy works but agents never called it
- fleet_escalate — never called by an agent
- Budget monitor (OAuth API) — code in orchestrator, never triggered
- Effort profiles — conservative active, never tested with dispatches
- Outage detector — code in orchestrator, never triggered
- All 10 heartbeat rewrites — pushed but agents haven't read them
- Review gates — fleet_task_complete populates but fleet-ops never reviewed
- Agent roles / PR authority — coded but never enforced in real flow
- Plane ↔ OCMC sync — code exists, never tested end-to-end