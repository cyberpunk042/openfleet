---
title: "Full Autonomous Mode"
type: epic
domain: backlog
status: draft
priority: P1
created: 2026-04-08
updated: 2026-04-19
tags: [autonomous, plane, writer, contributions, synergy, complementary, gates]
confidence: high
sources:
  - id: po-vision-2026-04-08
    type: notes
    file: wiki/log/2026-04-08-fleet-evolution-vision.md
    title: "PO 17-Epic Vision — Fleet Evolution"
---

# Full Autonomous Mode

## Summary

Full autonomous operation when Plane is connected and PO activates the mode. Writer keeps pages updated proactively. All agents do complementary work — architect designs before engineer builds, QA predefines before engineer implements, UX provides specs at all levels. Automatic contribution orchestration through the brain. Everyone brings their piece. Multi-agent iteration where validation and testing challenge work repeatedly until requirements are really met.

> "the technical-writer like every agent will need to do its job when the Plane is connected and I am in Full Autonomous mode. it will need to keep the pages up to date for example and whatever else rely on him like complementary work to the architect and UX designer and software engineer. Everyone's work is very important. without UX thinking a software engineer make too many mistake and same things when there was no architecture steps done before executing and whatnot."

> "this also make me realize that in situation like we just experience we really have to be ready to do multiple agent iteration where the validation and testing had to be challenged and challenged in order to really fix the bugs and meet the requirements."

> "everyone is the fleet is a generalist expert to some degree but everyone has their speciality and we need to create synergy and allow everyone to bring their piece. their segments and artifacts."

> "As much as I can accept a task to move forward in readiness I can reject or even regress the progress. The documentation and the tasks and sub-tasks details and comments and all artifacts have to be strong. high standards. This is why we have multiple specialist and multiple stage and methodologies."

## Goals

- Writer proactively maintains Plane pages when completed features have no docs
- Architect automatically provides design_input when tasks enter reasoning
- QA automatically predefines tests (TC-XXX) when tasks enter reasoning
- DevSecOps automatically provides security_requirements for security-relevant tasks
- UX automatically provides ux_spec for user-facing tasks at all levels
- Brain orchestrates contribution creation from synergy matrix automatically
- Multiple agent iteration on rejection — not just one-pass fix, challenge until right
- PM monitors and routes PO gates without PO having to check constantly
- All agents respect fleet state, budget mode, storm level
- 24-hour autonomous operation with PO monitoring via Plane + IRC + ntfy

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Writer proactively maintains Plane pages when completed features have no docs
- [ ] Architect automatically provides design_input when tasks enter reasoning
- [ ] QA automatically predefines tests (TC-XXX) when tasks enter reasoning
- [ ] DevSecOps automatically provides security_requirements for security-relevant tasks
- [ ] UX automatically provides ux_spec for user-facing tasks at all levels
- [ ] Brain orchestrates contribution creation from synergy matrix automatically
- [ ] Multiple agent iteration on rejection — not just one-pass fix, challenge until right
- [ ] PM monitors and routes PO gates without PO having to check constantly
- [ ] All agents respect fleet state, budget mode, storm level
- [ ] 24-hour autonomous operation with PO monitoring via Plane + IRC + ntfy

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- config/synergy-matrix.yaml — who contributes what to whom (defined)
- fleet/core/contributions.py — opportunity detection, completeness checking (built, not wired)
- config/standing-orders.yaml — per-role autonomous authority
- config/phases.yaml — delivery phase progressions with PO gates
- fleet/core/agent_lifecycle.py — ACTIVE→IDLE→SLEEPING→OFFLINE
- fleet/core/heartbeat_gate.py — brain-evaluated heartbeats (silent when idle)
- Orchestrator 13-step cycle — runs every 30s
- writer-heartbeat-autonomous intent in Navigator intent-map

## What's Missing for Full Autonomous

1. **Brain contribution auto-creation** — orchestrator doesn't call detect_contribution_opportunities() when tasks enter REASONING
2. **fleet_contribute MCP tool** — referenced in TOOLS.md but brain doesn't create contribution subtasks automatically
3. **Writer proactive mode** — writer-heartbeat-autonomous intent exists but writer standing order is still "conservative"
4. **Multi-agent iteration** — rejection creates fix task, but no mechanism for challenging the fix itself repeatedly
5. **PO gate routing** — fleet_gate_request tool defined but PM doesn't proactively route gates
6. **Phase standards injection** — phases.yaml defines quality bars but they're not injected into agent context
7. **Contribution completeness as dispatch gate** — contributions.py has check_contribution_completeness() but orchestrator doesn't use it as a dispatch gate

## Phases

### Phase 0: Document & Research

- [ ] Audit current standing orders — which agents could operate autonomously today
- [ ] Audit contribution system wiring gaps (contributions.py exists, orchestrator doesn't call it)
- [ ] Document the PM/fleet-ops role in autonomous mode (still gatekeep, just proactive)
- [ ] Document multi-agent iteration requirements (how many rounds? when to escalate to PO?)
- [ ] Research Plane API capabilities for proactive page maintenance

### Phase 1: Design

- [ ] Design contribution auto-creation sequence (task enters REASONING → brain reads synergy matrix → creates contribution subtasks for required roles)
- [ ] Design contribution completeness as dispatch gate (required contributions received → work stage allowed)
- [ ] Design writer proactive mode (authority_level → autonomous when Plane connected)
- [ ] Design multi-agent iteration protocol (rejection → fix → re-review → reject again? → escalate)
- [ ] Design PM proactive gate routing (readiness 90% → auto-route to PO)
- [ ] Design phase standards injection into agent context per delivery phase

### Phase 2: Implement

- [ ] Wire contributions.detect_contribution_opportunities() into orchestrator Step 4
- [ ] Wire check_contribution_completeness() as dispatch gate in orchestrator Step 5
- [ ] Implement writer proactive heartbeat with Plane staleness scanning
- [ ] Implement multi-agent iteration in rejection → fix flow
- [ ] Implement PM proactive gate routing
- [ ] Wire phase standards into context assembly

### Phase 3: Test & Validate

- [ ] Full lifecycle test: PM assigns → contributions flow → engineer implements → review → done
- [ ] Test writer proactive mode creates/updates Plane pages
- [ ] Test multi-agent iteration converges (doesn't loop forever)
- [ ] Test PO gates route correctly
- [ ] 24-hour autonomous observation run

## Relationships

- BUILDS ON: [[Agent Directive Chain Evolution]] (agents need complete directives for autonomous operation)
- BUILDS ON: [[Brain Evolution]] (brain creates contributions, manages dispatch gates)
- BUILDS ON: [[Plugin/Skill/Command Ecosystem]] (agents need their skills available)
- RELATES TO: [[Chain/Bus Architecture]] (chains propagate contribution events)
- RELATES TO: [[Budget & Tempo Modes]] (autonomous mode must respect budget constraints)
- RELATES TO: [[Agent Lifecycle Fine-Tuning]] (autonomous timing must be tuned)
- RELATES TO: [[Signatures & Transparency]] (autonomous work needs provenance)
