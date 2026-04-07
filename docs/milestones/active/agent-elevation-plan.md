# Agent Elevation — Comprehensive Plan

**Date:** 2026-04-07
**Status:** Reasoning — plan for PO review before work
**Scope:** Elevate all 10 agent file sets to fleet-elevation standard
**Depends on:** ~80 documentation files read, PO corrections incorporated

---

## 1. What This Document Is

The reasoning-stage plan for agent file elevation. Produced after:
- Conversation: PO direction on scope, corrections on role conflation
- Analysis: agent-elevation-analysis.md (partial, updated here)
- Investigation: read all 31 fleet-elevation docs, 14 agent-rework docs,
  8 context-system docs, 8 standards docs, 7 methodology protocol docs,
  all relevant source code, all agent templates, all provisioning scripts

This plan references the PO's verbatim corrections and documents
exactly what changes are needed, where, and in what order.

---

## 2. PO Corrections (Verbatim, Incorporated)

### 2.1 PM is NOT the PO
> PM is a Scrum Master and work coordinator. The PO is the HUMAN.
> "I am the PO." PM DRIVES development, never OWNS products.
> Never use "Product Owner" for PM. The word is "Driver."

### 2.2 PO works however they want
> "I do anything anywhere however I want.... Plane is not even needed,
> it could be entirely down."
> Never constrain PO to a specific surface. PM adapts to wherever
> the PO works — ops board, Plane, board memory, verbal, anywhere.

### 2.3 Plane is optional
> The fleet works with or without Plane. PM's core job (triage, assign,
> manage) exists on the ops board regardless. Plane is an enhancement
> that adds sprint management, issue bridging, module tracking when
> connected. Plane down ≠ fleet down.

### 2.4 No models in agent files
> Model selection is the brain's job via call_strategy config
> (fleet-elevation/26 lines 300-329) and model_selection.py (already
> task-aware). Agent files describe WHAT to do, not which model.
> Remove the model recommendation table from PM CLAUDE.md.

### 2.5 Artifacts are multi-section
> Plane HTML description can hold MULTIPLE artifact sections with
> different data-types. Agents contribute through separate sections
> (per-agent or per-domain concern ID), not one monolithic artifact.
> The PO can add manual content between sections. Document artifacts
> exist too, separate from the Plane HTML transposition.

### 2.6 Work hierarchy is per-case evaluation
> Not a mechanical rule. PM evaluates per situation:
> - Does it need its own artifact? → subtask with artifact ownership
> - Is it just a comment response? → not a task unless it creates work
> - What level? Root (epic) → branch (story) → leaf (subtask)
> - Artifact collision prevention: don't let two agents update the
>   same artifact section — break down to separate tasks if needed
> - This is PM intelligence, not a formula

### 2.7 PM is intelligent, not mechanical
> Top-tier Scrum Master. Anticipates, communicates, prepares backlogs,
> grooms, plans sprints with capacity awareness, filters noise for PO.
> Not "for each unassigned task: assign it."

### 2.8 Fleet-ops drives the ops board, PM drives Plane/DSPD
> Two agents, two primary surfaces, overlapping on ops board:
> - Fleet-ops: ops board lead (reviews, approvals, quality, health)
> - PM: work coordinator (triage, assign, break down, route) + Plane
> Both work ON the ops board but with distinct authorities.

### 2.9 Fully autonomous mode means Plane integration
> Not just "agents work on ops board tasks." PM also scans Plane
> proactively — new issues, priority changes, module progress.
> PM creates pre-work tasks (analysis, investigation) from Plane items.
> Agents can work on Plane-sourced tasks that aren't sprint-ready yet
> to BUILD readiness through methodology stages.

### 2.10 Don't regress to reach new standard
> Existing good content must not be deleted. The elevation ENRICHES
> existing files — adds missing sections, fixes errors, but preserves
> all behavioral capabilities agents currently have.

### 2.11 SOUL.md is combined with STANDARDS.md + MC_WORKFLOW.md
> push-soul.sh concatenates: agent SOUL.md + STANDARDS.md + MC_WORKFLOW.md
> into workspace SOUL.md. Don't duplicate content that's already in
> STANDARDS.md or MC_WORKFLOW.md within the SOUL.md template.

### 2.12 Heartbeat vs work session
> Drivers (PM, fleet-ops): heartbeat IS their work. Detailed heartbeat
> is correct — it's the action protocol for their core job.
> Workers (engineer, devops, QA, etc.): heartbeat is the check-in.
> Stage methodology comes from dynamic context (task-context.md),
> NOT from static HEARTBEAT.md. Worker heartbeats are lean.

---

## 3. The Agent File Architecture (Correct Understanding)

### 3.1 Gateway Injection Order

Both the fleet Python executor (gateway/executor.py `_build_agent_context`)
and the OpenArms Node.js gateway (workspace.ts `loadWorkspaceBootstrapFiles`)
read ALL 8 files. The injection order in the Python executor is:

```
Position 1: IDENTITY.md    ([:4000])  — who I am
Position 2: SOUL.md         ([:4000])  — values + anti-corruption
         ↳ In workspace: combined with STANDARDS.md + MC_WORKFLOW.md
Position 3: CLAUDE.md       ([:4000])  — role-specific rules
Position 4: TOOLS.md        ([:4000])  — chain-aware tool docs
Position 5: AGENTS.md       ([:4000])  — synergy relationships
Position 6: context/*.md    ([:8000])  — dynamic fleet + task data
Position 7: HEARTBEAT.md    ([:4000])  — action prompt (last)
```

OpenArms has higher limits: 20K per file, 150K total.

### 3.2 Template → Agent → Workspace Pipeline

```
Source of truth (git-tracked):
  agents/_template/IDENTITY.md/{role}.md    ({{placeholders}})
  agents/_template/SOUL.md/{role}.md        ({{placeholders}})
  agents/_template/CLAUDE.md/{role}.md      (role-specific rules)
  agents/_template/heartbeats/{role}.md     (action protocol)
  agents/_template/STANDARDS.md             (shared standards)
  agents/_template/MC_WORKFLOW.md           (shared workflow)
  agents/_template/mcp.json                 (MCP template)
  agents/_template/.claude/settings.json    (permissions)

Provisioned (gitignored):
  provision-agent-files.sh → agents/{name}/
    IDENTITY.md ← copy_template (sed {{placeholders}} from config)
    SOUL.md     ← copy_template (sed {{placeholders}} from config)
    CLAUDE.md   ← copy_template
    HEARTBEAT.md ← copy_if_changed (role-specific or worker fallback)
    TOOLS.md    ← generated by generate-tools-md.sh
    AGENTS.md   ← generated by generate-agents-md.sh
    agent.yaml  ← from template with name replacement
    context/    ← stubs (brain fills at runtime)

Deployed to workspace:
  push-soul.sh → workspace-mc-{uuid}/
    SOUL.md = agents/{name}/SOUL.md + STANDARDS.md + MC_WORKFLOW.md
    .mcp.json = template with path substitution
    .claude/settings.json = from template
    .agents/skills/ = symlinked to fleet skills

  push-agent-framework.sh → workspace-mc-{uuid}/
    CLAUDE.md = from agents/{name}/CLAUDE.md
    HEARTBEAT.md = from agents/{name}/HEARTBEAT.md
    STANDARDS.md = from template
    MC_WORKFLOW.md = from template
```

### 3.3 Placeholder System

Templates use `{{PLACEHOLDER}}` substituted by `copy_template()`:
- `{{AGENT_NAME}}` — from config key (e.g., "software-engineer")
- `{{DISPLAY_NAME}}` — from agent-identities.yaml
- `{{USERNAME}}` — from agent-identities.yaml
- `{{FLEET_ID}}` — from agent-identities.yaml fleet.id
- `{{FLEET_NAME}}` — from agent-identities.yaml fleet.name
- `{{FLEET_NUMBER}}` — from agent-identities.yaml fleet.number

### 3.4 What's Generated vs Hand-Written

| File | Source | How |
|------|--------|-----|
| IDENTITY.md | Hand-written template per role | copy_template with placeholders |
| SOUL.md | Hand-written template per role | copy_template with placeholders |
| CLAUDE.md | Hand-written template per role | copy_template |
| HEARTBEAT.md | Hand-written (5 types: PM, fleet-ops, architect, devsecops, worker) | copy_if_changed |
| TOOLS.md | **Generated** from code + config | generate-tools-md.sh |
| AGENTS.md | **Generated** from synergy matrix | generate-agents-md.sh |
| agent.yaml | Template + config values | provision-agent-files.sh |
| context/ | **Generated** by orchestrator at runtime | preembed.py, context_writer.py |

---

## 4. The Artifact System (Correct Understanding)

### 4.1 Plane HTML as Shared Canvas

The Plane issue `description_html` supports multiple artifact sections:
- Each wrapped in `fleet-artifact-start`/`fleet-artifact-end` markers
- Each identified by `data-type` attribute (analysis_document, plan, etc.)
- Hidden `fleet-data` span contains JSON source of truth per section
- Content OUTSIDE markers is preserved (PO notes, manual additions)
- Multiple agents contribute different sections in the SAME issue

### 4.2 Current Artifact Types (7)

From standards.py: task, bug, analysis_document, investigation_document,
plan, pull_request, completion_claim. Each has required fields and
quality criteria.

### 4.3 Contributions

Currently: `fleet_contribute()` posts typed COMMENTS on the target task.
Evolution: contributions become artifact SECTIONS in the Plane HTML
with per-contributor data-type IDs.

Contribution types from synergy matrix: design_input, qa_test_definition,
ux_spec, security_requirement, documentation_outline, feasibility_assessment,
deployment_manifest, qa_validation, security_review, ux_review,
documentation_update, trail_verification.

### 4.4 Work Hierarchy (PM Intelligence)

Per-case evaluation by PM:
- Root (epic/module) → branches (stories) → leaves (subtasks)
- Each level needing its own artifact → gets its own task
- Agents share a Plane issue through different artifact sections
- If artifact sections would collide → break into subtasks
- Comment responses are not tasks unless they generate new work
- PM evaluates: what level, what breakdown, what artifact ownership

---

## 5. The Full Autonomous Flow

### 5.1 Plane → Ops Board → Sprint → Done

1. Work arrives (PO creates in Plane, or on ops board, or anywhere)
2. PM evaluates: what type, what complexity, what entry point
3. PM creates ops board task (if not already there), sets ALL fields
4. Agent works through methodology stages (conversation → analysis →
   investigation → reasoning), building readiness
5. Contributions orchestrated at reasoning stage (parallel from specialists)
6. PM routes PO gates (50% checkpoint, 90% blocking)
7. Task becomes sprint-ready at ~80%+ (reasoning stage, contributions complete)
8. PO approves 90% gate → readiness 99 → work stage
9. Agent implements with full context (plan, contributions, standards)
10. fleet_task_complete → review chain → fleet-ops reviews → done

### 5.2 What "Fully Autonomous" Means

- PM scans Plane proactively for new issues, priority changes
- PM creates PRE-WORK tasks (analysis, investigation) from Plane items
  to build readiness before sprint inclusion
- Agents work on these pre-work tasks producing real artifacts
- Technical writer scans for stale Plane pages, updates documentation
- Architect proactively reviews tasks with architecture implications
- QA predefines tests for tasks entering reasoning stage
- DevSecOps reviews PRs, provides security requirements
- Fleet-ops processes approvals, monitors compliance
- All of this happens on heartbeat cycles without human intervention

### 5.3 Plane Is Optional

When Plane is down or not connected:
- PM still triages and assigns on ops board
- Sprint management via board memory and task tracking
- No Plane scanning, but all other functions work
- DSPD roadmap tasks live on ops board
- PO creates work directly on ops board or via directives

---

## 6. Heartbeat Architecture (Correct Understanding)

### 6.1 Driver Agents (PM, fleet-ops, architect, devsecops)

HEARTBEAT.md IS their work protocol. Their core job happens ON heartbeat:
- PM assigns, breaks down, routes, manages sprints
- Fleet-ops reviews, approves, monitors compliance
- Architect designs, contributes, monitors architecture health
- DevSecOps reviews security, contributes requirements, monitors infra

Detailed heartbeats are CORRECT for drivers. 100-155 lines is appropriate.

### 6.2 Worker Agents (engineer, devops, QA, writer, UX, accountability)

HEARTBEAT.md is a lean CHECK-IN protocol:
- Read pre-embedded context (data already there)
- Directives → messages → if you have work, your task context
  tells you what stage and what to do → idle
- Stage methodology comes from DYNAMIC context (task-context.md
  with stage instructions from stage_context.py)
- Worker doesn't need 5-stage instructions baked into static heartbeat
- 60-70 lines is appropriate

### 6.3 Per-Role Variations

| Role | Heartbeat Type | Key Variation |
|------|---------------|---------------|
| PM | Driver (detailed) | Board driving, assignment, sprint standup |
| Fleet-ops | Driver (detailed) | Approval processing, compliance monitoring |
| Architect | Driver (detailed) | Design contributions, architecture health |
| DevSecOps | Driver (detailed) | Security review, infrastructure monitoring |
| Software Engineer | Worker (lean) | Contribution consumption before work stage |
| DevOps | Worker (lean) | IaC focus, infrastructure health |
| QA | Worker (lean) | Test predefinition contributions |
| Technical Writer | Worker (lean) | Plane page maintenance when autonomous |
| UX Designer | Worker (lean) | UX spec contributions |
| Accountability | Worker (lean) | Trail verification |

---

## 7. Per-Agent File Changes

### 7.1 Software Engineer (DONE)

| File | Status | What Was Done |
|------|--------|---------------|
| IDENTITY.md | ✅ Created | Fleet placeholders, top-tier specialty, personality from existing CLAUDE.md, place in fleet |
| SOUL.md | ✅ Created | Role values (follow plan, contributions are requirements), 10 anti-corruption rules, boundaries, humility |
| CLAUDE.md | ✅ Elevated | 8 standard sections, moved identity→IDENTITY.md, removed model refs, added stage protocol + contributions + tool chains + boundaries + context awareness + anti-corruption. 3808/4000 chars. Zero capability loss. |
| HEARTBEAT.md | ✅ Created | Lean worker type. Trusts context for stage instructions. Contribution consumption check before work. 63 lines. |

### 7.2 Project Manager (IN PROGRESS — needs plan confirmation)

**IDENTITY.md** — Created but needs review:
- Role: "Work Coordinator & DSPD Product Driver" ✓
- Specialty: Scrum Master, work coordination (surface-independent) ✓
- Plane described as optional capability ✓
- PO works wherever they want ✓

**SOUL.md** — Created, partially fixed:
- Values: "Work coordination drives the fleet" (fixed from "board") ✓
- 10 anti-corruption rules ✓
- What I Do / Don't ✓
- Does NOT duplicate STANDARDS.md or MC_WORKFLOW.md content ✓

**CLAUDE.md** — Existing 3027 chars, needs elevation:
- REMOVE: "DSPD Product Owner" → "Product Driver" throughout
- REMOVE: model recommendation table (lines 20-29, ~300 chars)
- KEEP: task evaluation process, agent capability matching (without models), sprint management, DSPD vision, priority model, autonomous driver loop
- ADD: Stage protocol (PM manages others' stages, not own)
- ADD: Contribution orchestration (ensure specialists contribute before work)
- ADD: PO routing (filter, 50% checkpoint, 90% gate, phase advance)
- ADD: Work hierarchy evaluation (per-case breakdown intelligence)
- ADD: Boundaries (don't design, don't approve, don't implement, don't own products, don't override PO)
- ADD: Context awareness (both countdowns)
- ADD: Anti-corruption summary
- Budget: ~300 chars freed by removals, ~900 chars needed for additions = need ~600 more chars from condensing existing content

**HEARTBEAT.md** — Existing 155 lines, review needed:
- Check for model references → remove if found
- Check for Plane-as-requirement assumptions → soften to "when connected"
- Check for fully autonomous Plane scanning → add if missing
- This is a driver heartbeat — detail is appropriate

### 7.3 Fleet-Ops (NOT STARTED)

**IDENTITY.md** — To create:
- Role: ops board lead, quality guardian
- Specialty: code review methodology, trail verification, methodology compliance, budget awareness
- Fleet-ops drives the OCMC ops board (distinct from PM)
- At the "back end" — monitoring, health, quality (PM is "front end")

**SOUL.md** — To create:
- Values: "Quality over speed", "A review under 30 seconds is lazy", "Trail completeness is non-negotiable"
- 10 anti-corruption rules
- What I Do: review, approve, monitor, enforce
- What I Don't: write code, assign tasks, override PO

**CLAUDE.md** — Existing 3200 chars (estimated), needs elevation:
- 7-step REAL review process from fleet-elevation/06
- Approval decision rules (approve/reject/escalate)
- Trail verification (stages, contributions, PO gates)
- Phase standard verification
- Missing: stage protocol (fleet-ops doesn't follow stages — reviews AT review stage), contribution model, boundaries, context awareness, anti-corruption

**HEARTBEAT.md** — Existing 96 lines, review needed:
- Driver heartbeat — detail is appropriate
- Verify approval processing protocol matches fleet-elevation/06

### 7.4 Architect (NOT STARTED)

Driver agent. Heartbeat IS the work (design contributions, architecture health).
- IDENTITY: top-tier architect, design patterns (9+), SRP/DDD/Onion
- SOUL: "Design before implementation", "Multiple options before recommendation"
- CLAUDE: investigation rules (min 2 options), design specificity, pattern governance
- HEARTBEAT: design contributions, architecture health monitoring, complexity assessment

### 7.5 DevSecOps / Cyberpunk-Zero (NOT STARTED)

Driver agent. Has special identity (display_name: Cyberpunk-Zero).
- IDENTITY: security thinker, data minimization philosophy, creator's concern
- SOUL: "Security is a layer, not a checkpoint", "Specific requirements, not generic advice"
- CLAUDE: security contribution rules, security_hold mechanism, phase-aware security
- HEARTBEAT: security contributions, PR review, infrastructure health, crisis response

### 7.6-7.11 Worker Agents (NOT STARTED)

QA, DevOps, Technical Writer, UX Designer, Accountability Generator all follow
the worker pattern: lean heartbeat, stage methodology from context.

Each needs:
- IDENTITY.md with role-specific top-tier expertise
- SOUL.md with role-specific values + shared anti-corruption
- CLAUDE.md elevated with missing standard sections
- HEARTBEAT.md as lean worker type (or verify existing is correct)

Per-role specifics documented in fleet-elevation/10-14.

---

## 8. Infrastructure Changes Needed

### 8.1 Provisioning Script (DONE)

- `copy_template()` function added for placeholder substitution ✓
- IDENTITY.md uses per-role templates from `_template/IDENTITY.md/` ✓
- SOUL.md uses per-role templates from `_template/SOUL.md/` ✓
- CLAUDE.md uses copy_template for placeholder support ✓

### 8.2 Generator Scripts (NOT STARTED)

- `generate-tools-md.sh` — needs upgrade for chain-aware TOOLS.md
  (What/When/Chain/Input/"You do NOT need to" per tool per role)
- `generate-agents-md.sh` — needs upgrade for synergy-aware AGENTS.md
  (Contributes to me / I contribute to them / When to @mention)

### 8.3 Methodology Config (DONE)

- `config/methodology.yaml` created ✓
- methodology.py reads from config ✓
- stage_context.py reads from config ✓
- tools.py gating reads from config ✓
- doctor.py violation detection reads from config ✓
- Sprint ready threshold: needs adding (PO confirmed: 80)

### 8.4 Orchestrator Dispatch (DONE)

- Readiness >= 99 gate removed ✓
- Auto-set task_stage from readiness via get_initial_stage() ✓
- Instant wake on dispatch (brain decision + MC heartbeat + lifecycle) ✓

### 8.5 Brain Gate (DONE)

- OpenArms: already has brain gate (verified) ✓
- OpenClaw: patch 0013 for parity ✓

---

## 9. Work Order

### Phase 1: Complete PM Files
1. Fix PM CLAUDE.md (remove models, remove "Product Owner", add missing sections)
2. Review PM HEARTBEAT.md (model refs, Plane assumptions)
3. Validate PM file set against standards

### Phase 2: Fleet-Ops Files
4. Create fleet-ops IDENTITY.md template
5. Create fleet-ops SOUL.md template
6. Elevate fleet-ops CLAUDE.md
7. Review fleet-ops HEARTBEAT.md

### Phase 3: Architect + DevSecOps Files (drivers)
8. Architect: IDENTITY.md, SOUL.md, CLAUDE.md elevation, HEARTBEAT.md review
9. DevSecOps: IDENTITY.md, SOUL.md, CLAUDE.md elevation, HEARTBEAT.md review

### Phase 4: Worker Files (6 agents)
10. QA Engineer: full file set
11. DevOps: full file set
12. Technical Writer: full file set
13. UX Designer: full file set
14. Accountability Generator: full file set
15. (Software Engineer already done)

### Phase 5: Generated Files
16. Upgrade generate-tools-md.sh for chain-aware output
17. Upgrade generate-agents-md.sh for synergy-aware output
18. Run generators for all 10 agents

### Phase 6: Config + Validation
19. Add sprint_ready_threshold to methodology.yaml
20. Create/update validate-agents.sh per standards
21. Run validation against all 10 agents
22. Run all existing tests — zero regressions

### Phase 7: Deploy + Verify
23. Run provision-agent-files.sh for all agents
24. Run push-soul.sh to deploy to workspaces
25. Run push-agent-framework.sh to deploy to workspaces
26. Verify gateway reads files correctly (both Python executor and OpenArms)
27. Test one live dispatch to software-engineer

---

## 10. Open Items for PO

1. The PM CLAUDE.md agent capability table (lines 18-29) maps work types
   to agents WITHOUT models. Should this table remain (as role-matching
   guidance for PM) or be removed entirely (PM uses routing.py's
   suggest_agent() instead)?

2. For the sprint_ready_threshold: confirmed 80. Should this also appear
   in the heartbeat standard as explicit guidance for PM ("tasks at
   readiness >= 80 with contributions complete are sprint-ready")?

3. The existing PM heartbeat (155 lines) references specific readiness
   values for different task clarity levels (5-20% for vague, 70-80%
   for clear). Do these align with your intent, or should they reference
   the methodology.yaml readiness ranges instead?
