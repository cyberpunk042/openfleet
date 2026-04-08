# Tools System Session Handoff — 2026-04-07

**Purpose:** Context extraction for session continuation after compact/new session.

---

## What Was Done This Session

### Research Phase (solid — 10 documents)
- Read all 31 fleet-elevation docs, 22 system docs, 8 standards
- Researched OpenArms/OpenClaw gateway automation (CRONs, Tasks, TaskFlow, Hooks, Standing Orders)
- Researched skills ecosystem (5 sources, 32 Anthropic plugins, superpowers 14 skills, 1000+ available)
- Researched Claude Code features (hooks 23+ events, sub-agents, Agent Teams, extended thinking)
- Produced: tool-chain-elevation-plan.md, role-specific-tooling-elevation-plan.md, gateway-automation-capabilities.md, skills-and-plugins-ecosystem-research.md, strategic-agent-capabilities-research.md, tools-system-full-capability-map.md, tools-system-directives-and-usage.md, phase-a-operations-analysis.md, phase-b-mcp-plugin-findings.md, phase-c-group-call-architecture.md, tools-system-session-decisions.md

### Code Phase — What Actually Exists Now

**7 building block modules:**
- fleet/core/phases.py — check_phase_standards() + PhaseStandardResult (41 tests)
- fleet/core/plan_quality.py — check_plan_references_verbatim() (20 tests)
- fleet/core/contributions.py — check_contribution_completeness() (ALREADY EXISTED, 17 tests added)
- fleet/core/contributor_notify.py — NEW: notify_contributors() 
- fleet/core/transfer_context.py — NEW: package_transfer_context() + TransferPackage (16 tests)
- fleet/core/velocity.py — update_sprint_progress_for_task() added
- fleet/core/doctor.py — signal_rejection() added
- fleet/core/context_writer.py — append_contribution_to_task_context() added
- fleet/core/context_assembly.py — phase data + contribution status sections added
- fleet/core/preembed.py — phase standards + required contributions in pre-embed added

**16 generic fleet tools elevated in fleet/mcp/tools.py:**
- fleet_task_accept: verbatim reference check, event emission
- fleet_task_progress: readiness_changed events, 50% checkpoint with PO notification, auto gate request at 90% with ntfy
- fleet_commit: event emission, methodology defense-in-depth
- fleet_alert: security_hold on security category, event emission
- fleet_pause: fleet.task.blocked event, PM mention
- fleet_escalate: po-required tag, event emission
- fleet_chat: event emission, mention routing
- fleet_task_create: event emission, contribution opportunity event
- fleet_contribute: context embedding in target agent, contribution completeness check with PM notification
- fleet_transfer: full context packaging (contributions, artifacts, trail)
- fleet_approve: approve (Plane done, sprint progress, trail) + reject (readiness regression, stage regression, doctor signal, trail)
- fleet_phase_advance: NEW tool, phase standards check
- fleet_artifact_create/update: event emission, readiness suggestion
- fleet_request_input: contribution task existence check
- fleet_gate_request: chain wired
- fleet_task_complete: notify_contributors added

**36 role-specific group calls in fleet/mcp/roles/:**
- PM (5): pm_sprint_standup, pm_contribution_check, pm_epic_breakdown, pm_gate_route, pm_blocker_resolve
- Fleet-ops (4): ops_real_review, ops_board_health_scan, ops_compliance_spot_check, ops_budget_assessment
- Architect (4): arch_design_contribution, arch_codebase_assessment, arch_option_comparison, arch_complexity_estimate
- DevSecOps (6): sec_contribution, sec_pr_security_review, sec_dependency_audit, sec_code_scan, sec_secret_scan, sec_infrastructure_health
- Engineer (2): eng_contribution_check, eng_fix_task_response
- DevOps (4): devops_infrastructure_health, devops_deployment_contribution, devops_cicd_review, devops_phase_infrastructure
- QA (4): qa_test_predefinition, qa_test_validation, qa_coverage_analysis, qa_acceptance_criteria_review
- Writer (2): writer_doc_contribution, writer_staleness_scan
- UX (2): ux_spec_contribution, ux_accessibility_audit
- Accountability (3): acct_trail_reconstruction, acct_sprint_compliance, acct_pattern_detection

**Role-aware registration:** fleet/mcp/roles/__init__.py + fleet/mcp/server.py two-phase registration. Each agent sees 30 generic + their role-specific tools only.

**Deployment fixes:**
- scripts/push-soul.sh: per-agent mcp.json (not template) + .claude/skills/ symlink
- config/agent-tooling.yaml: 3 package names corrected, lightrag made conditional
- Per-agent mcp.json regenerated and deployed to 7/10 workspaces

**2008 tests, 0 failures, 19 skipped (full suite):**
- fleet/tests/core/test_phase_standards.py (41)
- fleet/tests/core/test_plan_verbatim.py (20)
- fleet/tests/core/test_contributions.py (17)
- fleet/tests/core/test_building_blocks.py (16)
- fleet/tests/core/test_new_chain_builders.py (17)
- fleet/tests/core/test_event_chain.py (25)
- fleet/tests/mcp/test_tool_operations.py (84)
- fleet/tests/mcp/test_role_tools.py (50 — 36 registration + 14 behavioral)

---

## Session 2 Changes (2026-04-07)

**Test fixes (6 pre-existing failures → 0):**
- 3 backend router tests: updated count from 4 to 5 (openrouter-qwen36plus added)
- TestE06_MCPStageEnforcement: rewrote to use methodology_config.is_tool_blocked()
- TestF02_FleetControlBar: updated path from openclaw-fleet to openfleet
- TestMethodologyMCPFlow: removed COMMIT_ALLOWED_STAGES import

**IaC fixes:**
- config/agent-tooling.yaml: removed phantom pytest-mcp MCP server entries (no package exists)
- scripts/setup-mcp-deps.sh: removed bad pytest-mcp install, added semgrep to venv
- Per-agent mcp.json regenerated (engineer 5→4, QA 4→3 servers)
- semgrep 1.157.0 installed and verified for devsecops

**Phase C behavioral tests (14 new):**
- PM: standup posts to board memory + IRC, contribution check detects gaps, blocker warns >2
- Fleet-ops: review detects no verbatim, no trail, blocked tasks
- Engineer: contribution check shows received inputs
- Accountability: trail counting, sprint compliance gaps, pattern detection
- QA: predefinition reads architect input, validation warns missing criteria
- Writer: staleness scan filters by task type

**Phase D foundation:**
- config/skill-stage-mapping.yaml created — maps skills to methodology stages
  - 5 stages × generic + role-specific + plugin recommendations
  - 10 roles mapped with role-specific skill recommendations
  - Stage restrictions (advisory, complement methodology.yaml tools_blocked)
  - All 15 referenced local skills verified to exist

### Session 2 continued — Phase D Skills

**13 workspace skills created** (.claude/skills/):
- fleet-methodology-guide: stage awareness — do/don't/tools/skills per stage
- fleet-contribution: synergy system — produce/consume contributions
- fleet-completion-checklist: 8-point pre-completion verification
- fleet-qa-predefinition: pessimistic thinking, TC-XXX, boundary values
- fleet-design-contribution: pattern selection, SRP, dependency direction
- fleet-security-contribution: specific actionable controls (not "be secure")
- fleet-ops-review-protocol: 10-step REAL review, anti-rubber-stamp
- fleet-engineer-workflow: contribution consumption, TDD, conventional commits
- fleet-pm-orchestration: task triage ALL fields, PO routing, contribution orchestration
- fleet-devops-iac: IaC principles, everything scriptable, phase infrastructure
- fleet-doc-lifecycle: living documentation, staleness, complementary work
- fleet-ux-every-level: UX beyond UI — CLI, API, config, errors, events, logs
- fleet-accountability-trail: trail reconstruction, compliance, pattern detection

**config/skill-stage-mapping.yaml**: 97 entries mapping skills to methodology stages × roles

**10 deeper role-specific skills added** (.claude/skills/):
- fleet-epic-breakdown (PM): decompose epics — seams, dependency chains, contribution requirements
- fleet-sprint-planning (PM): capacity awareness, contribution tax, velocity, realistic commitment
- fleet-trail-verification (fleet-ops): audit trail verification during review — completeness, authenticity
- fleet-threat-modeling (devsecops): STRIDE threat modeling — attack surface, trust boundaries
- fleet-adr-creation (architect): Architecture Decision Records — context, options, rationale
- fleet-boundary-value-analysis (QA): systematic edge cases — off-by-one, state transitions, combinations
- fleet-phase-testing (QA): phase-appropriate rigor — POC vs MVP vs staging vs production
- fleet-cicd-pipeline (devops): CI/CD design — build/test/deploy, phase-gated, rollback strategy
- fleet-api-documentation (writer): API docs — endpoint reference, examples, error codes
- fleet-accessibility-audit (UX): WCAG audit — keyboard, screen reader, contrast, non-visual UX

**config/skill-stage-mapping.yaml updated**: 140 entries (up from 97) with all new skills registered

### Session 2 continued — Phase F Sub-Agents (expanded)

**8 additional sub-agents** (.claude/agents/) — 12 total:
- sprint-analyzer (PM, haiku): sprint data aggregation, velocity, blockers
- pattern-analyzer (architect, haiku): architecture patterns, anti-patterns, coupling
- dependency-mapper (architect, sonnet): import graphs, circular deps, change impact
- secret-detector (devsecops, sonnet): leaked credentials, secret patterns, git history
- security-auditor (devsecops, sonnet): full OWASP-based security audit
- container-inspector (devops, haiku): Docker health, config audit, resource usage
- regression-checker (QA, sonnet): targeted regression after changes
- coverage-analyzer (QA, sonnet): coverage gaps, uncovered paths, distribution

### Session 2 continued — Phase E CRONs + Standing Orders

**config/agent-crons.yaml**: 17 CRON jobs across 8 roles:
- PM: daily-standup, backlog-grooming
- Fleet-ops: review-queue-sweep (3h), board-health-check, compliance-spot-check (weekly), budget-assessment
- DevSecOps: nightly-dependency-scan, secret-scan (weekly), infrastructure-security-check
- Architect: architecture-health-check (weekly), design-contribution-backlog
- QA: test-contribution-backlog, coverage-report (weekly)
- Accountability: sprint-compliance-report (weekly), pattern-detection
- Writer: documentation-staleness-scan (weekly)
- DevOps: infrastructure-health-check (4h)
- Model/effort per job. Fleet state guard prefix in all messages.

**scripts/sync-agent-crons.sh**: deploys CRONs from config to gateway. --dry-run, --list, per-agent targeting. Dry-run verified: all 17 CRONs parse correctly.

**config/standing-orders.yaml**: 14 standing orders across 10 roles with PO-controlled authority levels (conservative default). Escalation threshold: 2 autonomous actions without feedback. Fleet state override: all orders suspended when paused/over budget.

### Session 2 continued — Phase F Sub-Agents + Hooks

**4 sub-agent definitions** (.claude/agents/):
- code-explorer.md: read-only codebase navigation (sonnet, no Edit/Write)
- test-runner.md: run tests and report results (sonnet, no Edit/Write)
- trail-reconstructor.md: audit trail reconstruction (haiku, no Edit/Write)
- dependency-scanner.md: vulnerability scanning (sonnet, no Edit/Write)

**config/agent-hooks.yaml**: per-role hook configs:
- Default PreToolUse: conventional commit format enforcement on fleet_commit
- Default PostToolUse: trail recording for state-modifying tools
- software-engineer: warn if completing without running tests
- fleet-ops: block short approval/rejection comments
- devsecops-expert: security_hold verification reminder

**scripts/configure-agent-settings.sh**: rewritten to read agent-hooks.yaml via Python, generate proper JSON with hooks, deploy to all workspaces. Verified: 7 workspaces configured (2 hooks baseline, 3 for fleet-ops and software-engineer).

---

## Honest Status Per Phase (2026-04-07 final)

**Phase A (~80%):** Building blocks built+tested. 16 elevated generic tools with 93 behavioral tests (stage regression, readiness events, security_hold, contributor notification, task transitions). 12 chain builders. Context system has phase standards, contribution status, AND dynamic skill recommendations. Preembed includes skill recommendations (task dispatch) and standing orders (heartbeat). 2 new modules: skill_recommendations.py, standing_orders.py. Remaining: chain builder enrichment.

**Phase B (~40%):** Config fixed. pytest-mcp phantom removed, semgrep installed. Per-agent mcp.json regenerated. Remaining: plugin install needs running gateway.

**Phase C (~80%):** 36 group calls across 10 roles. 89 tests (36 registration + 53 behavioral — all 10 roles with deep coverage). Chain docs in tool-chains.yaml for all 36 group calls. Behavioral coverage: PM 8, fleet-ops 4, architect 3, devsecops 4, devops 7, engineer 5, QA 8, writer 5, UX 4, accountability 3. Remaining: more complex interaction tests.

**Phase D (~50%):** 30 workspace skills (7 gateway + 13 broad + 10 deep). skill-stage-mapping.yaml (140 entries, all refs verified). Dynamic skill recommendations wired into context_assembly + preembed. Remaining: plugin ecosystem evaluation/install, more granular skills.

**Phase E (~35%):** 17 CRONs in agent-crons.yaml. sync-agent-crons.sh (dry-run verified). 14 standing orders in standing-orders.yaml. Standing orders wired into heartbeat preembed runtime. Remaining: CRON deployment (needs gateway), PO authority_level review.

**Phase F (~30%):** 12 sub-agents (all read-only, model-appropriate). Role-aware sub-agent deployment via push-soul.sh + agent-tooling.yaml. Hook configs + deployment via configure-agent-settings.sh. Stage-aware effort integrated into model_selection.py (_STAGE_EFFORT_FLOOR + _apply_stage_adjustment). Dispatch fix: Claude backends use model_config (stage-aware) for dispatch record. Remaining: Agent Teams evaluation, monitoring hooks.

**Phase G (~70%):** generate-tools-md.py (Python) reads 7 layers + tool-roles.yaml + role_tools chain docs. "Always Available" + per-stage skills with dedup. _cross_role_tools for 10 previously unassigned tools. TOOLS.md (270-324 lines) generated for all 10 agents, deployed to 7 workspaces. Remaining: minor enrichment.

**Phase H (~50%):** validate-tooling-configs.py: 0 errors, 3 warnings (3 unprovisioned workspaces). 98 pipeline + 53 behavioral + 18 skill recs + 12 standing orders + 10 model selection stage + 3 dispatch stage + 19 cross-flow + 9 edge cases + 2 context integration = 224 new tests this session. STATUS-TRACKER.md + MASTER-INDEX.md updated. Test suite: **2218 passed, 0 failed, 19 skipped.** Remaining: per-agent smoke test (needs gateway).

---

## What the Next Session Needs to Do

1. Read `tools-system-session-index.md` FIRST — the 8-phase map
2. Read this handoff for honest status per phase
3. Validate: `python scripts/validate-tooling-configs.py` (should be 0 errors)
4. Run tests: `.venv/bin/python -m pytest fleet/tests/ -q` (should be 2107+ passed)
5. Import check: `python -c "from fleet.core.skill_recommendations import get_skill_recommendations; print('OK')"`
6. **Gateway-blocked work** (when gateway available): plugin install (B), CRON deployment (E), smoke test (H)
7. **Unblocked remaining work**: edge case tests (A/C), plugin evaluation research (D), Agent Teams evaluation (F), stage-aware effort (F)
8. PO instruction: "no rush. we take our time. we never at any point start rushing or doing quickfix or cutting corners."

---

## Key Files — Complete List

```
# Phase A — Foundation (code)
fleet/core/phases.py                    — check_phase_standards
fleet/core/plan_quality.py              — check_plan_references_verbatim
fleet/core/contributor_notify.py        — NEW
fleet/core/transfer_context.py          — NEW
fleet/core/context_writer.py            — append_contribution_to_task_context
fleet/core/velocity.py                  — update_sprint_progress_for_task
fleet/core/doctor.py                    — signal_rejection
fleet/core/context_assembly.py          — phase + contribution + skill_recommendations sections
fleet/core/preembed.py                  — phase standards + contributions + skill recs + standing orders
fleet/core/event_chain.py               — 8 new builders + evolution
fleet/core/chain_runner.py              — 3 new handler actions
fleet/core/skill_recommendations.py     — NEW: stage+role skill lookup (cached YAML)
fleet/core/standing_orders.py           — NEW: per-role authority + orders (cached YAML)
fleet/mcp/tools.py                      — 16 tools elevated + fleet_phase_advance
fleet/mcp/server.py                     — two-phase registration

# Phase B — MCP + plugins (config)
config/agent-tooling.yaml               — package fixes + sub_agents per role + _cross_role_tools
scripts/setup-mcp-deps.sh              — removed pytest-mcp, added semgrep

# Phase C — Role-specific group calls (code)
fleet/mcp/roles/__init__.py             — NEW: role-aware registration
fleet/mcp/roles/pm.py                   — 5 group calls
fleet/mcp/roles/fleet_ops.py            — 4 group calls
fleet/mcp/roles/architect.py            — 4 group calls
fleet/mcp/roles/devsecops.py            — 6 group calls
fleet/mcp/roles/engineer.py             — 2 group calls
fleet/mcp/roles/devops.py               — 4 group calls
fleet/mcp/roles/qa.py                   — 4 group calls
fleet/mcp/roles/writer.py               — 2 group calls
fleet/mcp/roles/ux.py                   — 2 group calls
fleet/mcp/roles/accountability.py       — 3 group calls

# Phase D — Skills (30 workspace skills)
config/skill-stage-mapping.yaml         — 140 entries (stages × roles × skills)
.claude/skills/fleet-methodology-guide  — stage awareness
.claude/skills/fleet-contribution       — synergy system
.claude/skills/fleet-completion-checklist — 8-point pre-completion
.claude/skills/fleet-qa-predefinition   — TC-XXX, boundary values
.claude/skills/fleet-design-contribution — pattern selection, SRP
.claude/skills/fleet-security-contribution — STRIDE, actionable controls
.claude/skills/fleet-ops-review-protocol — 10-step REAL review
.claude/skills/fleet-engineer-workflow  — TDD, contribution consumption
.claude/skills/fleet-pm-orchestration   — triage ALL fields, PO routing
.claude/skills/fleet-devops-iac         — IaC principles
.claude/skills/fleet-doc-lifecycle      — staleness, living docs
.claude/skills/fleet-ux-every-level     — UX beyond UI
.claude/skills/fleet-accountability-trail — trail, compliance, patterns
.claude/skills/fleet-epic-breakdown     — epic decomposition
.claude/skills/fleet-sprint-planning    — capacity, velocity, commitment
.claude/skills/fleet-trail-verification — audit trail verification
.claude/skills/fleet-threat-modeling    — STRIDE threat modeling
.claude/skills/fleet-adr-creation       — Architecture Decision Records
.claude/skills/fleet-boundary-value-analysis — systematic edge cases
.claude/skills/fleet-phase-testing      — POC/MVP/staging/production rigor
.claude/skills/fleet-cicd-pipeline      — CI/CD design
.claude/skills/fleet-api-documentation  — API docs
.claude/skills/fleet-accessibility-audit — WCAG accessibility

# Phase E — CRONs + Standing Orders (config)
config/agent-crons.yaml                 — 17 CRON jobs across 8 roles
scripts/sync-agent-crons.sh            — CRON deployment to gateway
config/standing-orders.yaml             — 14 standing orders across 10 roles

# Phase F — Sub-agents + Hooks (12 sub-agents)
.claude/agents/code-explorer.md         — codebase nav (sonnet)
.claude/agents/test-runner.md           — run tests (sonnet)
.claude/agents/trail-reconstructor.md   — audit trail (haiku)
.claude/agents/dependency-scanner.md    — vuln scanning (sonnet)
.claude/agents/sprint-analyzer.md       — sprint data (haiku)
.claude/agents/pattern-analyzer.md      — arch patterns (haiku)
.claude/agents/dependency-mapper.md     — import graphs (sonnet)
.claude/agents/secret-detector.md       — leaked creds (sonnet)
.claude/agents/security-auditor.md      — OWASP audit (sonnet)
.claude/agents/container-inspector.md   — Docker health (haiku)
.claude/agents/regression-checker.md    — targeted regression (sonnet)
.claude/agents/coverage-analyzer.md     — coverage gaps (sonnet)
config/agent-hooks.yaml                 — 5 hooks (2 default + 3 role-specific)

# Phase G — Generation pipeline
scripts/generate-tools-md.py            — Python, 7 layers + tool-roles.yaml
scripts/generate-tools-md.sh            — bash wrapper
config/tool-chains.yaml                 — 20 generic + 36 role-specific chain docs
config/tool-roles.yaml                  — per-role tool descriptions + _cross_role_tools

# Phase H — Validation
scripts/validate-tooling-configs.py     — 11 cross-checks, 0 errors

# Deployment (IaC)
scripts/configure-agent-settings.sh     — REWRITTEN: reads hooks YAML
scripts/push-soul.sh                    — UPDATED: role-aware sub-agent symlinks
scripts/push-agent-framework.sh         — UPDATED: deploys generated TOOLS.md
scripts/reprovision-agents.sh           — UPDATED: includes push-soul.sh

# Tests (2218 passed, 0 failures, 19 skipped)
fleet/tests/core/test_phase_standards.py      — 41 tests
fleet/tests/core/test_plan_verbatim.py        — 20 tests
fleet/tests/core/test_contributions.py        — 17 tests
fleet/tests/core/test_building_blocks.py      — 16 tests
fleet/tests/core/test_new_chain_builders.py   — 17 tests
fleet/tests/core/test_skill_recommendations.py — NEW: 18 tests
fleet/tests/core/test_standing_orders.py      — NEW: 12 tests
fleet/tests/core/test_model_selection.py      — UPDATED: +10 stage tests (20 total)
fleet/tests/core/test_context_assembly.py     — UPDATED: +2 tests (skill recs)
fleet/tests/mcp/test_tool_operations.py       — 93 tests (+9 Phase A edge cases)
fleet/tests/mcp/test_role_tools.py            — 89 tests (36 reg + 53 behavioral)
fleet/tests/integration/test_tooling_pipeline.py — NEW: 98 tests
fleet/tests/integration/test_flow_dispatch.py — UPDATED: +3 stage-aware tests (8 total)
fleet/tests/integration/test_flow_contributions.py — NEW: 19 cross-flow tests
```

---

## The Bigger Picture (Don't Lose This)

This is a 42+ hours effort covering 7 capability layers × 10 roles × 5 methodology stages. Each agent is a TOP-TIER EXPERT with their own tools, chains, group calls, skills, CRONs, sub-agents, hooks, standing orders, and directives — generic AND role-specific, adapted per methodology stage.

What exists now covers roughly **50%** of the total work. The system is connected end-to-end: config → generation → deployment → runtime context. Agents who start a session see: TOOLS.md with all 7 layers, preembed with stage-appropriate skill recommendations and standing orders, dynamic context with skill recs per call.

**What's gateway-blocked:** plugin install (B), CRON deployment (E), per-agent smoke test (H). These are the final 20% — they need the gateway running.

**What's unblocked:** edge case tests (A/C), plugin evaluation research (D), Agent Teams evaluation (F), stage-aware effort (F), more granular skills. These are depth items that improve quality but don't block operation.
