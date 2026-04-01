# Fleet Documentation — How Everything Fits Together

> **~100 documents. ~30,000+ lines. This README is the map.**
>
> Documentation exists at 5 layers. Each layer serves a different
> purpose and audience. Documents reference each other — read this
> README to know WHERE to find WHAT.

---

## 1. Documentation Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: VISION (why + what, high level)                    │
│  docs/ARCHITECTURE.md — system map, interconnections         │
│  docs/INTEGRATION.md — 12 cross-system data flows            │
│  milestones/active/fleet-vision-architecture.md — code audit │
│  milestones/active/MASTER-INDEX.md — milestone status         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: SYSTEM REFERENCE (how each system works)           │
│  docs/systems/01-22 — per-system docs (10,138 lines)         │
│  Each: purpose, modules, functions, connections, gaps        │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: DESIGN SPECIFICATIONS (what to build)              │
│  milestones/active/fleet-elevation/ (31 docs)                │
│  milestones/active/agent-rework/ (14 docs)                   │
│  milestones/active/{immune,teaching,methodology,context}/    │
│  milestones/active/{budget,labor,router,challenge,storm,...}  │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: PLANS (when + how to deploy)                       │
│  milestones/active/path-to-live.md — 10-step ordered path    │
│  milestones/active/ecosystem-deployment-plan.md — 15 items   │
│  milestones/active/unified-implementation-plan.md — 38 items │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: VERIFICATION (did we actually do it)               │
│  milestones/active/VERIFICATION-MATRIX.md — 69/69 verified   │
│  (Only covers foundation systems. Strategic + agent = 0 live)│
└─────────────────────────────────────────────────────────────┘

READING ORDER for new context:
  1. This README (orientation)
  2. ARCHITECTURE.md (system map)
  3. INTEGRATION.md (how systems connect)
  4. MASTER-INDEX.md (what exists, honest status)
  5. Specific system doc for the area you're working on
  6. Design spec for the feature you're implementing
  7. Path-to-live for deployment order
```

---

## 2. Layer 1 — Vision (Start Here)

| Document | Lines | What It Answers |
|----------|-------|----------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 291 | "What are the 20 systems and how do they relate?" System map, module inventory, infrastructure, agent file structure. |
| [INTEGRATION.md](INTEGRATION.md) | 783 | "How does data flow across systems?" 12 cross-system flows traced end-to-end. Read/write dependency matrix. |
| [fleet-vision-architecture.md](milestones/active/fleet-vision-architecture.md) | 731 | "What code actually exists?" Code-verified audit of 94 modules. Honest assessment: what's built vs designed vs missing. |
| [fleet-vision-architecture-part2.md](milestones/active/fleet-vision-architecture-part2.md) | 478 | Gateway integration, per-agent state, critical path to live test, document index with honest status. |
| [MASTER-INDEX.md](milestones/active/MASTER-INDEX.md) | 257 | "What's the status of everything?" 255 milestones across 36 docs. Honest: ✅ live tested, 🔨 code exists, 📐 design only. |
| [SPEC-TO-CODE.md](SPEC-TO-CODE.md) | 222 | "Does the code match the design specs?" 69 specs mapped to 94 modules. Shows divergences and gaps. |
| [WORK-BACKLOG.md](WORK-BACKLOG.md) | 260 | "What's left to do?" 31 items consolidated from all system docs. Prioritized: blockers → high → medium → low. |

---

## 3. Layer 2 — System Reference

22 per-system docs in [docs/systems/](systems/). Each follows the standard:
purpose, modules, key functions, dependencies, consumers, design decisions, data shapes, what's needed.

| # | System | Lines | Key Focus |
|---|--------|-------|-----------|
| 1 | [Methodology](systems/01-methodology.md) | 559 | 5 stages, readiness, stage checks, delivery phases |
| 2 | [Immune System](systems/02-immune-system.md) | 566 | Doctor, 11 diseases, 3 lines of defense |
| 3 | [Teaching](systems/03-teaching-system.md) | 395 | Adapted lessons, exercises, comprehension |
| 4 | [Event Bus](systems/04-event-bus.md) | 536 | 47 event types, 6 surfaces, chains, routing |
| 5 | [Control Surface](systems/05-control-surface.md) | 415 | 3 axes, effort profiles, PO directives |
| 6 | [Agent Lifecycle](systems/06-agent-lifecycle.md) | 414 | 5 states, PR authority, cost model |
| 7 | [Orchestrator](systems/07-orchestrator.md) | 610 | 9-step cycle, context refresh, wake drivers |
| 8 | [MCP Tools](systems/08-mcp-tools.md) | 379 | 25 tools, stage gating, review gates |
| 9 | [Standards](systems/09-standards.md) | 475 | 7 artifact types, plan quality, PR hygiene |
| 10 | [Transpose](systems/10-transpose.md) | 447 | Object↔HTML, 7 renderers, progressive work |
| 11 | [Storm](systems/11-storm.md) | 484 | 9 indicators, 5 severity levels, circuit breakers |
| 12 | [Budget](systems/12-budget.md) | 414 | 6 modes, real OAuth quota, auto-transitions |
| 13 | [Labor](systems/13-labor.md) | 348 | Stamps, confidence tiers, heartbeat cost |
| 14 | [Router](systems/14-router.md) | 409 | 4 backends, cheapest-capable, fallback chains |
| 15 | [Challenge](systems/15-challenge.md) | 604 | 4 types, multi-round, budget-aware, deferred queue |
| 16 | [Models](systems/16-models.md) | 419 | Select, benchmark, shadow, promote, tier track |
| 17 | [Plane](systems/17-plane.md) | 437 | PM↔ops two-level model, methodology labels |
| 18 | [Notifications](systems/18-notifications.md) | 411 | 3 levels, cross-refs, IRC channels |
| 19 | [Session/Context](systems/19-session.md) | 415 | Telemetry, assembly, pre-embed, HeartbeatBundle |
| 20 | [Infrastructure](systems/20-infrastructure.md) | 315 | 8 clients, IaC scripts, ecosystem gap |
| 21 | [Agent Tooling](systems/21-agent-tooling.md) | 439 | Per-role MCP/plugins/skills spec |
| 22 | [Agent Intelligence](systems/22-agent-intelligence.md) | 647 | Autonomy, escalation, research, context awareness |

---

## 4. Layer 3 — Design Specifications

### Fleet Elevation (31 docs — the comprehensive agent redesign)

```
docs/milestones/active/fleet-elevation/
├── 01-overview.md             Why the elevation is needed
├── 02-agent-architecture.md   File structure, injection order, onion arch
├── 03-delivery-phases.md      Phase progressions (idea → production)
├── 04-the-brain.md            Orchestrator design, autocomplete chains
├── 05-project-manager.md      PM role specification
├── 06-fleet-ops.md            Fleet-ops role specification
├── 07-architect.md            Architect role specification
├── 08-devsecops.md            DevSecOps role specification
├── 09-software-engineer.md    Engineer role specification
├── 10-devops.md               DevOps role specification
├── 11-qa-engineer.md          QA role specification
├── 12-technical-writer.md     Writer role specification
├── 13-ux-designer.md          UX role specification
├── 14-accountability.md       Accountability role specification
├── 15-cross-agent-synergy.md  Contribution matrix, parallel work
├── 16-multi-fleet-identity.md Fleet naming, shared Plane
├── 17-standards-framework.md  Quality standards per artifact
├── 18-po-governance.md        PO authority, gates
├── 19-flow-validation.md      Diagram validation
├── 20-ai-behavior.md          Anti-corruption rules, disease prevention
├── 21-task-lifecycle.md        PRE → PROGRESS → POST
├── 22-milestones.md           Milestone tracking
├── 23-agent-lifecycle.md      ACTIVE→DROWSY→SLEEPING, strategic calls
├── 24-tool-call-tree.md       Tool chains catalog
├── 25-diagrams.md             Architecture diagrams
├── 26-unified-config.md       Config reference
├── 27-evolution.md            Change management
├── 28-codebase-inventory.md   Module inventory
├── 29-lessons-learned.md      What went wrong before
├── 30-strategy-synthesis.md   Strategy summary
└── 31-transition-strategy.md  How to get from here to there
```

### Agent Rework (14 docs — making agents alive)

```
docs/milestones/active/agent-rework/
├── 01-overview.md              Why agents need rework
├── 02-pre-embedded-data.md     FULL data per role, not compressed
├── 03-orchestrator-waking.md   Wake PM and fleet-ops
├── 04-project-manager.md       PM heartbeat details
├── 05-fleet-ops.md             Fleet-ops heartbeat details
├── 06-architect.md             Architect heartbeat details
├── 07-devsecops.md             DevSecOps heartbeat details
├── 08-workers.md               Worker heartbeat template
├── 09-inter-agent-comms.md     Communication protocol
├── 10-standards-integration.md Standards per role
├── 11-plane-integration.md     Plane data in agent context
├── 12-milestones.md            AR-01 to AR-20
├── 13-live-test-plan.md        35+ live test scenarios
└── 14-full-fleet-vision.md     PO's complete vision verbatim
```

### Subsystem Designs (24 docs)

```
immune-system/    7 docs  (doctor, diseases, detection, response)
teaching-system/  1 doc   (lessons, injection, comprehension)
methodology/      8 docs  (5 stages, protocols, standards)
context-system/   8 docs  (bundles, MCP, heartbeat, integration)
```

### Strategic Designs (6 docs — the 47 milestones)

```
budget-mode-system.md          6 budget modes (M-BM01-06)
labor-attribution.md           Labor stamps (M-LA01-08)
multi-backend-routing.md       4 backends (M-BR01-08)
iterative-validation.md        Challenge loops (M-IV01-08)
model-upgrade-path.md          Shadow→promote (M-MU01-08)
storm-prevention.md            9 indicators (M-SP01-09)
```

---

## 5. Layer 4 — Plans

| Document | Lines | What It Plans |
|----------|-------|-------------|
| [path-to-live.md](milestones/active/path-to-live.md) | 271 | 10 ordered steps from documentation to running fleet. Timeline: 3-6 weeks. |
| [ecosystem-deployment-plan.md](milestones/active/ecosystem-deployment-plan.md) | 454 | 15 items across 3 tiers: prompt caching, plugins, MCP, RAG, Agent Teams. |
| [unified-implementation-plan.md](milestones/active/unified-implementation-plan.md) | 232 | 38 milestones (U-01 to U-38) across 9 phases. Merges AR + extension. |
| [implementation-roadmap.md](milestones/active/implementation-roadmap.md) | 334 | 5-wave sequencing for 47 strategic milestones. |
| [fleet-extension-milestones.md](milestones/active/fleet-extension-milestones.md) | 364 | 30 extension milestones (Waves 6-11). Research findings. |

---

## 6. Layer 5 — Verification

| Document | What It Proves |
|----------|---------------|
| [VERIFICATION-MATRIX.md](milestones/active/VERIFICATION-MATRIX.md) | 69/69 foundation milestones LIVE VERIFIED (three systems, event bus). |

**Honest gap:** Only foundation systems are verified. Strategic milestones (47), agent rework (20), unified plan (38) = 0 live tests.

---

## 7. How Documents Reference Each Other

```
ARCHITECTURE.md
  ├── references → systems/01-22 (per-system detail)
  ├── references → INTEGRATION.md (cross-system flows)
  └── references → MASTER-INDEX.md (milestone status)

INTEGRATION.md
  ├── references → systems/01-22 (each flow cites affected systems)
  ├── references → fleet-elevation/15 (contribution flow design)
  └── references → fleet-elevation/23 (lifecycle design)

systems/01-22
  ├── reference → source code (fleet/core/*.py with line numbers)
  ├── reference → fleet-elevation/* (design specs for what's needed)
  ├── reference → agent-rework/* (pre-embed and heartbeat specs)
  └── cross-reference other system docs (connections table)

path-to-live.md
  ├── references → ecosystem-deployment-plan.md (Tier 1 first)
  ├── references → fleet-elevation/02,05-14,20 (agent file specs)
  ├── references → agent-rework/02-08 (heartbeat specs)
  └── references → systems/* (what to read before each step)

ecosystem-deployment-plan.md
  ├── references → systems/21-agent-tooling.md (per-role spec)
  ├── references → systems/20-infrastructure.md (ecosystem gap)
  └── references → unified-implementation-plan.md (milestone mapping)

fleet-elevation/* + agent-rework/*
  ├── reference → each other (architecture↔role specs↔heartbeats)
  ├── referenced BY → systems/* ("design doc says...")
  └── referenced BY → path-to-live.md (read before implementing)
```

---

## 8. How to Navigate

### "I want to understand the fleet"
→ ARCHITECTURE.md → INTEGRATION.md → MASTER-INDEX.md

### "I want to understand system X"
→ docs/systems/{X}.md

### "I want to understand how systems connect"
→ INTEGRATION.md (12 flows) → ARCHITECTURE.md (dependency matrix)

### "I want to implement agent CLAUDE.md"
→ fleet-elevation/02 (structure) → fleet-elevation/{role}.md (per-role spec) → fleet-elevation/20 (anti-corruption) → fleet-elevation/15 (synergy)

### "I want to deploy ecosystem tools"
→ ecosystem-deployment-plan.md → systems/21-agent-tooling.md → systems/20-infrastructure.md

### "I want to reach live fleet operation"
→ WORK-BACKLOG.md (prioritized items) → path-to-live.md (10 steps in order)

### "I want to restructure agent directories"
→ agent-directory-cleanup.md → then provision from templates

### "I want to understand the PO's vision"
→ agent-rework/14-full-fleet-vision.md → extension requirements (in memory)

### "I want to check what's done vs not done"
→ MASTER-INDEX.md (honest status for 255 milestones)

---

## 9. What's NOT Documented Yet

| Gap | Why | Priority |
|-----|-----|----------|
| TurboQuant / Qwen3.5-Omni latest research | Research in progress | HIGH — affects model strategy |
| Claude Code full anatomy (commands, rules, skills, plugins, hooks, agents) | Research in progress | HIGH — affects agent configuration |
| Per-agent CLAUDE.md content | Must be written per fleet-elevation specs | CRITICAL — blocks live testing |
| Per-agent HEARTBEAT.md content | Must be written per agent-rework specs | CRITICAL — blocks live testing |
| Live test results | Never done | CRITICAL — 0 live tests |
