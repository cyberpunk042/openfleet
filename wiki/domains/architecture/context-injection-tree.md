---
title: "Context Injection Decision Tree"
type: reference
domain: architecture
status: draft
created: 2026-04-09
updated: 2026-04-09
tags: [context, injection, autocomplete, preembed, navigator, profiles, tree, validation]
epic: E001
confidence: medium
sources: []
---

# Context Injection Decision Tree

Every path from root to leaf = one validated scenario.

> "I would not overwhelm my trainee"
> — PO, 2026-04-09

## Summary

The decision tree controlling how context is injected per agent per cycle. Three fleet-level axes (OCMC dropdowns) gate everything below them; downstream branches select tier, model, stage, protocol adaptations, and skill/plugin loads. Canonical reference for every pre-embed, heartbeat, and task-injection pipeline decision.

## Fleet-Level Axes (apply to EVERYTHING below)

These three axes are set at the fleet level via OCMC dropdowns. They affect
what gets injected, who gets context, and how much they see.

```
FLEET CONTROL STATE
│
├── Work Mode (where new work comes from)
│   ├── full-autonomous ────── all agents active, Plane pulls enabled
│   ├── project-management-work ── PM-driven, normal dispatch
│   ├── local-work-only ────── OCMC tasks only, no Plane pull
│   ├── finish-current-work ── no NEW dispatch, in-progress continues
│   └── work-paused ────────── no dispatch at all
│
├── Cycle Phase (what KIND of activity — FILTERS ACTIVE AGENTS)
│   ├── execution ──────────── all agents active (normal operations)
│   ├── planning ───────────── ONLY project-manager + architect active
│   ├── analysis ───────────── ONLY architect + project-manager active
│   ├── investigation ──────── any assigned agent active
│   ├── review ─────────────── ONLY fleet-ops active
│   └── crisis-management ──── ONLY fleet-ops + devsecops active
│   │
│   │  IMPACT ON CONTEXT:
│   │  Agent NOT active in current phase →
│   │    heartbeat: "Fleet is in {phase} mode. You are not active. HEARTBEAT_OK."
│   │  Agent IS active in current phase →
│   │    heartbeat: normal context + phase indicator in fleet state line
│   │  dispatch: only dispatches to agents active in current phase
│
└── Backend Mode (which AI backends are enabled — determines routing)
    ├── claude ─────────────── expert only (opus/sonnet, 200K-1M)
    ├── localai ────────────── trainee only (hermes/phi, 8K)
    ├── openrouter ─────────── community only (free models, ~32K)
    ├── claude+localai ─────── expert + trainee (route by complexity)
    ├── claude+openrouter ──── expert + community (route by complexity)
    ├── localai+openrouter ─── trainee + community (free-only fleet)
    └── claude+localai+openrouter ── all backends (cheapest capable wins)
    │
    │  ROUTING: cheapest capable backend for each task
    │  Security/architecture agents NEVER go to trainee/community
    │  Fallback chain: localai → openrouter → claude sonnet → claude opus → queue
```

## Backend → Capability Tier → Context Adaptation

> "I would not overwhelm my trainee" — PO, 2026-04-09

Context adaptation is about what the model can HANDLE, not just what fits.
The transition from Claude to other backends is PROGRESSIVE — tested tier
by tier, not a sudden switch. Each tier maps to AICP operational profiles.

LocalAI has evolved beyond the legacy hermes-3b/8K assumption:
- qwen3-8b: 16K context, thinking mode, native tool calling
- qwen3-4b: 16K context, lightweight fleet model
- gemma4-e2b: 16K (8K in fleet-light), 53 tok/s, multimodal
- Dual GPU (8+11GB) enables: qwen3-30b MoE, gemma4-26b at 256K

```
CAPABILITY TIERS
│
├── EXPERT ─────────────────────────────────────── [TIER-EXPERT]
│   │  Claude opus/sonnet (200K-1M context)
│   │  AICP profile: N/A (cloud backend)
│   │
│   │  Full content everywhere. All knowledge map branches.
│   │  All contribution content inline. Full chain awareness.
│   │  All skills, sub-agents, plugins. Trust the agent.
│   │  Full methodology (MUST/MUST NOT/CAN/How to advance).
│   │  Full role data formatted. Full events. Full standing orders.
│   │  Knowledge budget: ~50K tokens.
│   │
│   │  Agent reasons autonomously. Brain provides context, agent decides.
│
├── CAPABLE ────────────────────────────────────── [TIER-CAPABLE]
│   │  qwen3-8b (16K, thinking), qwen3-30b MoE (8K-32K dual GPU)
│   │  OpenRouter capable models (~32K)
│   │  AICP profiles: default, code-review, thorough, reliable
│   │
│   │  Condensed: summaries + references to full content.
│   │  Core fields on tasks. MUST/MUST NOT on protocol (no CAN/advance).
│   │  Contributions: type + from + status (not full inline content).
│   │  Top 3 per role data list. Methodology ALWAYS full (never compress).
│   │  Skills: names only. Events: up to 5.
│   │  Knowledge budget: ~10-15K tokens.
│   │
│   │  Agent follows clear instructions. Can handle multi-step protocols.
│   │  Brain provides focused context, agent executes with guidance.
│
├── LIGHTWEIGHT ────────────────────────────────── [TIER-LIGHTWEIGHT]
│   │  gemma4-e2b (8-16K, 53 tok/s), qwen3-4b (16K)
│   │  OpenRouter free models (variable quality)
│   │  AICP profiles: fleet-light, fast
│   │
│   │  Focused. Direct. Simple instructions.
│   │  Task: title + stage + verbatim + one-line action.
│   │  Protocol: MUST/MUST NOT as short rules (2-3 lines).
│   │  Contributions: names only. No inline content.
│   │  No chain awareness. No standing orders. No events detail.
│   │  Role data: counts only.
│   │  Knowledge budget: ~3-5K tokens.
│   │
│   │  "Don't overwhelm my trainee."
│   │  Brain supervises. Agent executes prescribed work.
│   │  Clear assignment, not autonomous reasoning.
│
├── FLAGSHIP-LOCAL ─────────────────────────────── [TIER-FLAGSHIP]
│   │  gemma4-26b (256K, dual GPU), future large local models
│   │  AICP profiles: dual-gpu
│   │
│   │  Large context like sonnet-200k, but local model capabilities.
│   │  Same adaptation as CAPABLE tier but with more context budget.
│   │  Can receive more contribution content inline.
│   │  Can see full knowledge map at condensed depth.
│   │  Knowledge budget: ~15K tokens.
│   │
│   │  Agent follows instructions like CAPABLE. More context available
│   │  but model reasoning is local-tier, not Claude-tier.
│   │  Trust with verification — labor stamp marks as local.
│
└── DIRECT ─────────────────────────────────────── [TIER-DIRECT]
    │  No LLM. Pure MCP tool calls. Deterministic operations.
    │  Brain handles these without creating an agent session.
    │  No context injection needed.
    │
    │  Examples: heartbeat silent response, template-based status,
    │  simple task state transitions the brain can evaluate in Python.
```

### Tier Selection Logic

```
Fleet backend_mode + task complexity + agent role → tier
│
├── backend_mode: claude
│   └── always EXPERT
│
├── backend_mode: localai
│   ├── AICP profile: fleet-light → LIGHTWEIGHT
│   ├── AICP profile: dual-gpu → FLAGSHIP-LOCAL or CAPABLE
│   └── AICP profile: default → CAPABLE
│
├── backend_mode: openrouter
│   ├── free model, simple task → LIGHTWEIGHT
│   └── capable model, medium task → CAPABLE
│
├── backend_mode: hybrid (claude+localai, etc.)
│   ├── security/architect agents → always EXPERT (never trainee)
│   ├── complex task → EXPERT (routed to claude)
│   ├── medium task → CAPABLE (routed to qwen3-8b or openrouter)
│   └── simple task → LIGHTWEIGHT (routed to gemma4-e2b or qwen3-4b)
│
└── brain evaluates "no LLM needed" → DIRECT
```

### Progressive Rollout

The PO does NOT flip to all-backends mode suddenly.
Each tier is validated through the tree's scenarios before enabling:

```
Phase 1: EXPERT only (current — claude backend)
Phase 2: EXPERT + CAPABLE (add qwen3-8b for medium tasks)
Phase 3: EXPERT + CAPABLE + LIGHTWEIGHT (add gemma4-e2b for heartbeats)
Phase 4: EXPERT + CAPABLE + FLAGSHIP-LOCAL (dual GPU, add gemma4-26b)
Phase 5: Full spectrum (all tiers operational, cheapest capable wins)
```

Each phase requires: infrastructure ready, profiles configured,
tree scenarios validated for that tier, PO confirmed.

## Master Tree

```
ROOT
│
├── HEARTBEAT (agent wakes on CRON)
│   │
│   ├── Cycle Phase Check (FIRST — before anything else)
│   │   ├── agent IS active in current phase ──── proceed to context assembly
│   │   └── agent NOT active in current phase ─── "Fleet in {phase}. You are not active. HEARTBEAT_OK."
│   │
│   ├── Tier: EXPERT (claude, 200K-1M) ────────────────── [HB-EXPERT]
│   │   │
│   │   ├── §2 PO Directives
│   │   │   ├── none ─────────────────────────────────── "None."
│   │   │   ├── normal ──────────────────────────────── "- {content} (from {source})"
│   │   │   └── urgent ──────────────────────────────── "- URGENT {content} (from {source})"
│   │   │
│   │   ├── §3 Messages
│   │   │   ├── none ─────────────────────────────────── "None."
│   │   │   └── has ──────────────────────────────────── "- From {source}: {full content}"
│   │   │
│   │   ├── §4 Assigned Tasks
│   │   │   ├── none ─────────────────────────────────── "None."
│   │   │   ├── 1 task
│   │   │   │   ├── conversation ─────────────────────── title+ID+stage+readiness+verbatim(sparse)+desc
│   │   │   │   ├── analysis ─────────────────────────── title+ID+stage+readiness+verbatim+desc
│   │   │   │   ├── investigation ────────────────────── title+ID+stage+readiness+verbatim+desc
│   │   │   │   ├── reasoning ────────────────────────── title+ID+stage+readiness+verbatim+desc+SP
│   │   │   │   └── work ────────────────────────────── title+ID+stage+readiness+progress+verbatim+desc+SP+phase+PR
│   │   │   └── multiple tasks ───────────────────────── count + full detail each
│   │   │
│   │   ├── §5 Role Data (FORMATTED — not raw dicts)
│   │   │   ├── project-manager
│   │   │   │   ├── has unassigned ───────────────────── "- task-un1: Title (priority)" per task
│   │   │   │   ├── has blocked ──────────────────────── "{N} blocked tasks"
│   │   │   │   ├── sprint progress ──────────────────── "12/25 done (48%)"
│   │   │   │   └── no role-specific data ────────────── section omitted
│   │   │   │
│   │   │   ├── fleet-ops
│   │   │   │   ├── has approvals ────────────────────── "- appr-001: 'Task Title' by agent (pending)"
│   │   │   │   ├── has review queue ─────────────────── "- task-abc: Title (agent-name)"
│   │   │   │   ├── has offline agents ───────────────── "Offline: agent1, agent2"
│   │   │   │   └── no role-specific data ────────────── section omitted
│   │   │   │
│   │   │   ├── architect
│   │   │   │   ├── has design tasks ─────────────────── "- task-xyz: Title (stage)"
│   │   │   │   ├── has high complexity ──────────────── "- task-abc: Title (high)"
│   │   │   │   └── no role-specific data ────────────── section omitted
│   │   │   │
│   │   │   ├── devsecops
│   │   │   │   ├── has security tasks ───────────────── "- task-sec: Title"
│   │   │   │   ├── has PRs needing review ───────────── "- task-pr: Title (PR: url)"
│   │   │   │   └── no role-specific data ────────────── section omitted
│   │   │   │
│   │   │   └── worker (engineer, devops, QA, writer, UX, accountability)
│   │   │       ├── has contribution tasks ───────────── "- Contribute {type} for: task-abc"
│   │   │       ├── has contributions received ───────── "task-a1b: design_input (architect, done)"
│   │   │       ├── has tasks in review ──────────────── "- task-rv: Title (PR: url)"
│   │   │       └── no role-specific data ────────────── "1 assigned task" or section omitted
│   │   │
│   │   ├── §6 Standing Orders
│   │   │   ├── conservative + no orders ─────────────── section omitted
│   │   │   └── standard/autonomous ──────────────────── authority + threshold + orders (name, desc, when, boundary)
│   │   │
│   │   ├── §7 Events
│   │   │   ├── none ─────────────────────────────────── "None."
│   │   │   └── has ──────────────────────────────────── "{time} [{type}] {agent}: {summary}" (up to 10)
│   │   │
│   │   ├── §8 Context Awareness
│   │   │   ├── normal (ctx < 93%, rate < 85%) ───────── section omitted
│   │   │   ├── context prepare (93-95%) ─────────────── "PREPARE — save working state to artifacts"
│   │   │   ├── context extract (95%+) ───────────────── "EXTRACT — dump everything NOW"
│   │   │   ├── rate conserve (85-90%) ───────────────── "PREPARE — controlled transition"
│   │   │   └── rate critical (90%+) ─────────────────── "MANAGE — force compact, no new dispatches"
│   │   │
│   │   └── §9 Fleet State (in header line)
│   │       ├── normal ───────────────────────────────── "{N}/{T} online | Mode: X | Phase: Y | Backend: Z"
│   │       ├── paused ───────────────────────────────── mode shows "work-paused"
│   │       └── storm ────────────────────────────────── mode shows storm severity
│   │
│   ├── Tier: CAPABLE (qwen3-8b 16K, openrouter ~32K) ── [HB-CAPABLE]
│   │   │
│   │   ├── §2 PO Directives ────────────────────────── SAME (never compress PO words)
│   │   ├── §3 Messages ─────────────────────────────── SAME (actionable, can't compress)
│   │   ├── §4 Assigned Tasks ────────────────────────── title + ID + stage + readiness + verbatim ONLY
│   │   ├── §5 Role Data ────────────────────────────── counts + top 3 items per list
│   │   ├── §6 Standing Orders ──────────────────────── name + description only (no when/boundary)
│   │   ├── §7 Events ───────────────────────────────── up to 5, condensed format
│   │   ├── §8 Context Awareness ────────────────────── SAME (safety, never compress)
│   │   └── §9 Fleet State ──────────────────────────── SAME (one line)
│   │
│   ├── Tier: FLAGSHIP-LOCAL (gemma4-26b 256K, dual GPU) ─ [HB-FLAGSHIP]
│   │   │  Same structure as CAPABLE but more context budget.
│   │   │  Can show more items in role data lists (top 5 vs top 3).
│   │   └── (same sections as CAPABLE, slightly more detail)
│   │
│   └── Tier: LIGHTWEIGHT (gemma4-e2b 8-16K, qwen3-4b) ── [HB-LIGHTWEIGHT]
│       │
│       ├── §2 PO Directives ────────────────────────── SAME (never compress PO words)
│       ├── §3 Messages ─────────────────────────────── first 100 chars + "fleet_read_context for full"
│       ├── §4 Assigned Tasks ────────────────────────── title + stage + "fleet_read_context for details"
│       ├── §5 Role Data ────────────────────────────── counts only ("2 approvals, 1 offline")
│       ├── §6 Standing Orders ──────────────────────── OMIT
│       ├── §7 Events ───────────────────────────────── count only ("3 events")
│       ├── §8 Context Awareness ────────────────────── SAME (safety, never compress)
│       └── §9 Fleet State ──────────────────────────── SAME (one line)
│
│
└── TASK (agent dispatched or context refreshed)
    │
    ├── Injection Level
    │   │
    │   ├── none ──────────────────────────────────────── [TK-NONE]
    │   │   │  "NO pre-embedded data. Call fleet_read_context() FIRST."
    │   │   │  Only renders: §0 mode + §1 identity + §3 stage + §5 verbatim (if set)
    │   │   │  Everything else: "Call fleet_read_context()"
    │   │   │
    │   │   └── (profile doesn't matter here — content is minimal regardless)
    │   │
    │   └── full ──────────────────────────────────────── [continues below]
    │
    ├── Task Nature
    │   │
    │   ├── REGULAR TASK ──────────────────────────────── [TK-REG]
    │   │   └── (standard autocomplete chain, continues to Stage below)
    │   │
    │   ├── CONTRIBUTION TASK ─────────────────────────── [TK-CONTRIB]
    │   │   │  (has contribution_type + contribution_target)
    │   │   │
    │   │   │  Changes vs regular:
    │   │   │  §2: shows contribution task + TARGET TASK context (title, verbatim, phase)
    │   │   │  §5: target task verbatim shown alongside contribution task verbatim
    │   │   │  §6: role-specific protocol (not generic stage protocol)
    │   │   │  §7: "You are CONTRIBUTING TO task-{id}. fleet_contribute() when done."
    │   │   │  §9: "Produce {contribution_type} for {target_task_title}"
    │   │   │  §10: "fleet_contribute() → content delivered → contribution_received event"
    │   │   │
    │   │   ├── architect producing design_input
    │   │   │   └── §6: "Produce design_input: approach, target files, patterns, constraints"
    │   │   ├── qa producing qa_test_definition
    │   │   │   └── §6: "Produce TC-XXX criteria with priority and type"
    │   │   ├── devsecops producing security_requirement
    │   │   │   └── §6: "Produce threat model, required controls, compliance needs"
    │   │   ├── ux producing ux_spec
    │   │   │   └── §6: "Produce all states, interactions, accessibility, all UX levels"
    │   │   ├── writer producing documentation_outline
    │   │   │   └── §6: "Produce audience, structure, scope, complementary with arch/eng"
    │   │   └── engineer producing feasibility/implementation_context
    │   │       └── §6: "Produce implementation constraints, key decisions"
    │   │
    │   └── REJECTION REWORK ──────────────────────────── [TK-REJECT]
    │       │  (labor_iteration >= 2)
    │       │
    │       │  Changes vs regular:
    │       │  §0: adds "ITERATION: {N} (rework after rejection)"
    │       │  §2: adds "Iteration: {N} (previous attempt rejected)"
    │       │  NEW §6b: "## REJECTION FEEDBACK" — what was wrong, what to fix
    │       │  §6: prepend "This is REWORK. Read rejection feedback. Fix ROOT CAUSE."
    │       │  §9: "Read rejection feedback. eng_fix_task_response(). Fix root cause. Regression tests."
    │       │
    │       ├── iteration 2 (first rework)
    │       └── iteration 3+ (repeated rejection — escalation likely)
    │
    ├── Stage
    │   │
    │   ├── CONVERSATION (readiness 0-20) ─────────────── [TK-CONV]
    │   │   §6: MUST discuss, ask, identify unknowns
    │   │       MUST NOT code, commit, complete
    │   │       CAN questions, draft proposals
    │   │   §7: contributions not shown (premature)
    │   │   §9: "Read verbatim. Ask clarifying questions. NO code."
    │   │   §10: fleet_chat, fleet_artifact_create (drafts only)
    │   │
    │   ├── ANALYSIS (readiness 20-50) ────────────────── [TK-ANAL]
    │   │   §6: MUST examine codebase, produce analysis_document, reference files+lines
    │   │       MUST NOT produce solutions, implement
    │   │       CAN analysis docs, gap analysis, commits of docs
    │   │   §7: contributions not shown (premature)
    │   │   §9: "Examine codebase. Produce analysis_document with file references."
    │   │   §10: fleet_artifact_create/update, fleet_chat
    │   │
    │   ├── INVESTIGATION (readiness 50-80) ───────────── [TK-INVEST]
    │   │   §6: MUST research, explore 2+ options, cite sources
    │   │       MUST NOT decide, implement
    │   │       CAN research docs, option comparisons, commits of docs
    │   │   §7: contributions not shown (premature)
    │   │   §9: "Research multiple approaches (min 2). Document options."
    │   │   §10: fleet_artifact_create/update, fleet_chat
    │   │
    │   ├── REASONING (readiness 80-99) ───────────────── [TK-REASON]
    │   │   │
    │   │   │  §6: MUST decide approach, produce plan, reference verbatim, specify files
    │   │   │      MUST NOT implement
    │   │   │      CAN plans, task breakdown, fleet_task_accept
    │   │   │  §9: "Produce plan that REFERENCES verbatim. Specify target files."
    │   │   │  §10: fleet_task_accept, fleet_artifact_create
    │   │   │
    │   │   ├── Role-specific reasoning protocol (I5)
    │   │   │   ├── engineer ─────── "Produce implementation plan"
    │   │   │   ├── architect ────── "Produce design_input: approach, files, patterns"
    │   │   │   ├── qa ──────────── "Produce qa_test_definition: TC-XXX criteria"
    │   │   │   ├── devsecops ────── "Produce security_requirement: threat model, controls"
    │   │   │   ├── ux ──────────── "Produce ux_spec: states, interactions, accessibility"
    │   │   │   ├── writer ──────── "Produce documentation_outline: audience, structure"
    │   │   │   ├── devops ──────── "Produce infrastructure plan: deployment, scaling"
    │   │   │   ├── fleet-ops ────── "Produce review assessment: requirements, compliance"
    │   │   │   ├── pm ──────────── "Produce task breakdown: subtasks, dependencies"
    │   │   │   └── accountability ─ "Produce compliance report: trail, methodology"
    │   │   │
    │   │   └── Contribution state at reasoning
    │   │       ├── not applicable ──── skip contributions type
    │   │       ├── not yet received ── show requirements list, no content
    │   │       └── partially received ─ show received content + flag missing
    │   │
    │   └── WORK (readiness 99+) ──────────────────────── [TK-WORK]
    │       │
    │       │  §6: MUST execute plan, conventional commits, stay in scope
    │       │      MUST NOT deviate, add scope, skip tests
    │       │      Sequence: accept → commit → complete
    │       │  §10: fleet_commit → git+event+trail. fleet_task_complete → full chain.
    │       │
    │       ├── Contribution State
    │       │   ├── N/A (subtask/blocker/spike/concern) ── "No contributions required."
    │       │   ├── required, NONE received ───────────── BLOCKED by dispatch gate (shouldn't reach here)
    │       │   │   └── if somehow here ──────────────── "MISSING contributions. fleet_request_input(). Do NOT proceed."
    │       │   ├── required, PARTIAL ─────────────────── received shown inline + "MISSING: {types}. fleet_request_input()."
    │       │   └── required, ALL received ────────────── full content inline (## CONTRIBUTION: sections)
    │       │
    │       ├── Progress
    │       │   ├── 0% ───────── §9: "Starting. fleet_task_accept() first."
    │       │   ├── 1-49% ────── §9: "Continue implementation. Commit progress."
    │       │   ├── 50-69% ───── §9: "Halfway. Continue. Post progress update."
    │       │   ├── 70% ──────── §9: "Implementation done. Run tests. Prepare completion."
    │       │   ├── 80% ──────── §9: "Challenged. Address challenge findings."
    │       │   └── 90% ──────── §9: "Reviewed. Final polish, then fleet_task_complete()."
    │       │
    │       ├── Confirmed Plan
    │       │   ├── not in context ─── §6b: "Plan not in context. fleet_read_context() to load."
    │       │   └── in context ─────── §6b: "## CONFIRMED PLAN\n{plan_content}"
    │       │
    │       └── Previous Stage Findings
    │           ├── not available ───── (no section)
    │           └── available ────────── §6c: "## PREVIOUS FINDINGS\n{summary}"
    │
    ├── Delivery Phase
    │   ├── not set ───────────────────────────────────── §8 omitted
    │   ├── idea ──────────────────────────────────────── §8: no standards
    │   ├── conceptual ────────────────────────────────── §8: design required, requirements captured
    │   ├── poc ───────────────────────────────────────── §8: tests(happy path), docs(readme), security(no secrets)
    │   ├── mvp ───────────────────────────────────────── §8: tests(main flows), docs(setup+usage+API), security(auth+validation+deps)
    │   ├── staging ───────────────────────────────────── §8: tests(comprehensive), docs(full), security(pen-tested), monitoring(health+alerts)
    │   └── production ────────────────────────────────── §8: tests(complete), docs(comprehensive), security(certified), monitoring(full)
    │
    ├── Plane Connection
    │   ├── not connected ─────────────────────────────── no Plane references anywhere
    │   └── connected + issue linked ──────────────────── §2: "Plane: {issue_id}". §10: chains mention Plane sync.
    │
    ├── Blocked
    │   ├── no ────────────────────────────────────────── normal flow
    │   └── yes ───────────────────────────────────────── §2: "BLOCKED by: {ids}". §9: "BLOCKED. fleet_pause() or resolve dependency."
    │
    ├── Task Type (affects required stages + contribution applicability)
    │   ├── epic ──────────── all 5 stages required, full contributions
    │   ├── story ─────────── conversation + reasoning + work, full contributions
    │   ├── task ──────────── reasoning + work, full contributions
    │   ├── subtask ────────── reasoning + work, SKIP contributions
    │   ├── bug ───────────── analysis + reasoning + work, full contributions
    │   ├── spike ─────────── conversation + investigation + reasoning, NO work stage
    │   ├── blocker ────────── conversation + reasoning + work, SKIP contributions
    │   ├── request ────────── conversation + analysis + reasoning + work, full contributions
    │   └── concern ────────── conversation + analysis + investigation, NO work stage
    │
    ├── Verbatim Requirement
    │   ├── set ───────────────────────────────────────── §5: "> {verbatim}" (THE ANCHOR, never compressed)
    │   └── not set ───────────────────────────────────── §5: "(No verbatim requirement set — ask PO for clarification.)"
    │
    └── Tier (cross-cutting — affects ALL sections above)
        │
        ├── EXPERT (claude, 200K-1M) ──────────────────── [TK-EXPERT]
        │   All sections: full content
        │   Contributions: full content inline
        │   Stage protocol: MUST + MUST NOT + CAN + How to advance
        │   Phase standards: full per-standard detail
        │   Chain awareness: full chain descriptions
        │
        ├── CAPABLE (qwen3-8b 16K, openrouter ~32K) ──── [TK-CAPABLE]
        │   §2 task detail: title + ID + stage + readiness + verbatim (core only)
        │   §5 verbatim: SAME (never compress anchor)
        │   §6 protocol: MUST + MUST NOT only (no CAN, no How to advance)
        │   §7 contributions: type + from + status + "fleet_read_context for full content"
        │   §8 phase: one-liner per standard
        │   §10 chains: one-line per chain
        │
        ├── FLAGSHIP-LOCAL (gemma4-26b 256K, dual GPU) ── [TK-FLAGSHIP]
        │   Same structure as CAPABLE but more knowledge budget.
        │   Can include more contribution detail (summaries, not full inline).
        │   Can include condensed Navigator knowledge context.
        │
        └── LIGHTWEIGHT (gemma4-e2b 8-16K, qwen3-4b) ─── [TK-LIGHTWEIGHT]
            §0: "Your task data is below. fleet_read_context() for full details."
            §1: identity (same)
            §2: title + stage + type only
            §3: stage (same)
            §5: verbatim (SAME — never compress anchor)
            §6: MUST + MUST NOT as short rules (2-3 lines)
            §7: names only ("Inputs: design_input (architect), qa_tests (QA)")
            §8: phase name only
            §9: one-line clear directive
            §10: omit
            Labor stamp: flag as lightweight/trainee tier
            "I would not overwhelm my trainee" — PO
```

## Knowledge Context Tree (Navigator — separate file)

```
NAVIGATOR (knowledge-context.md)
│
├── Tier: EXPERT
│   ├── agent_manual ────────── full section (~35 lines)
│   ├── methodology ─────────── full stage content (all subsections)
│   ├── standards ───────────── full for artifact type
│   ├── skills ──────────────── full descriptions (fleet-* + pack)
│   ├── commands ────────────── full guidance per stage
│   ├── tools ───────────────── full chain trees
│   ├── plugins ─────────────── full capabilities
│   ├── contributions ───────── full synergy + received + missing
│   ├── trail ───────────────── full event list
│   ├── context_awareness ───── full metrics
│   ├── LightRAG ────────────── up to remaining budget (graph query)
│   └── claude-mem ──────────── 5 recent observations
│
├── Tier: CAPABLE
│   ├── agent_manual ────────── mission + primary tools + 3 rules
│   ├── methodology ─────────── current stage only (full — methodology never compressed)
│   ├── standards ───────────── required fields list
│   ├── skills ──────────────── names only ("Available: /skill1, /skill2")
│   ├── commands ────────────── top 3 for current stage
│   ├── tools ───────────────── name + purpose one-liner
│   ├── plugins ─────────────── names only
│   ├── contributions ───────── received names + contributor (not content)
│   ├── trail ───────────────── summary line
│   ├── context_awareness ───── "Context: 45% | Rate: 23%"
│   ├── LightRAG ────────────── proportional to remaining budget
│   └── claude-mem ──────────── 3 recent observations
│
├── Tier: FLAGSHIP-LOCAL
│   │  Same as CAPABLE (large context, but local model capabilities).
│   │  More knowledge budget available — can load more KB branches.
│   └── (same structure as CAPABLE, expanded to ~15K budget)
│
├── Tier: LIGHTWEIGHT
│   ├── agent_manual ────────── "You are {name}, {role}. {mission}."
│   ├── methodology ─────────── "Stage: {stage}. MUST: {list}. MUST NOT: {list}."
│   ├── tools ───────────────── "fleet_read_context for full context."
│   ├── contributions ───────── names only ("Inputs: design_input, qa_tests")
│   └── (all others) ────────── omitted
│
├── Tier: DIRECT
│   └── no Navigator output (no LLM to inject into)
│
└── Heartbeat mode (any tier)
    └── (all branches) ──────── none (fleet-context.md handles dynamic, static files handle identity)
```
```

## Never-Compress Rules

```
NEVER COMPRESS (any profile, any scenario):
├── PO directives ─────────── PO words are sacrosanct
├── Verbatim requirement ──── THE anchor — never summarized, never shortened
├── Context awareness ─────── safety mechanism — agent must see pressure
├── Stage MUST NOT rules ──── preventing violations is critical
└── Rejection feedback ────── agent MUST see what went wrong
```

## Compound States (meaningful combinations)

```
COMPOUND HEARTBEAT STATES
├── idle (nothing) ──────────────────────────── HEARTBEAT_OK, no tools
├── not active in cycle_phase ───────────────── "Fleet in {phase}. You are not active. HEARTBEAT_OK."
├── directive only ──────────────────────────── execute directive, then check rest
├── messages only ───────────────────────────── respond, then HEARTBEAT_OK
├── tasks only ──────────────────────────────── follow stage protocol
├── directive + tasks ───────────────────────── directive FIRST (overrides), then tasks
├── directive + messages + tasks ─────────────── directive → messages → tasks (priority order)
├── reviews + storm (fleet-ops) ─────────────── budget-aware review, reduced dispatch
├── unassigned + blocked (PM) ───────────────── triage unassigned, resolve blockers
├── contribution tasks + own work (worker) ──── contribution tasks first if urgent
├── context pressure + active work ──────────── save state, prepare for compaction
└── planning phase + architect ──────────────── focused on design work, ignore execution tasks

COMPOUND TASK STATES
├── work + all contributions + plan visible ─── golden path (TK-01)
├── work + missing contributions ────────────── blocked, request input
├── work + rejection rework + contributions ─── fix path: read feedback, fix root cause
├── reasoning + no contributions yet ────────── plan without inputs, note they're coming
├── contribution + analysis stage ───────────── examine codebase FOR target task
├── contribution + reasoning stage ──────────── produce contribution artifact
├── conversation + no verbatim ──────────────── ask PO for clarification
├── work + blocked ──────────────────────────── report blocker, can't proceed
├── work + progress 70% + all contrib ───────── run tests, prepare completion
└── work + progress 0% + iteration 2 ────────── rework: read feedback first
```

## Scenario Coverage Checklist

Every leaf and compound state maps to a test scenario.
PO confirms each. Isolated test locks it.

### Heartbeat Scenarios

```
[ ] HB-01  idle, no tasks, no messages (EXPERT)
[ ] HB-02  has 1 in-progress task at work stage (EXPERT)
[ ] HB-03  has messages from PM (EXPERT)
[ ] HB-04  fleet-ops with pending reviews — FORMATTED (EXPERT)
[ ] HB-05  PM with unassigned tasks — FORMATTED (EXPERT)
[ ] HB-06  urgent PO directive (EXPERT)
[ ] HB-07  normal PO directive (EXPERT)
[ ] HB-08  multiple tasks at different stages (EXPERT)
[ ] HB-09  architect with design tasks — FORMATTED (EXPERT)
[ ] HB-10  devsecops with security tasks — FORMATTED (EXPERT)
[ ] HB-11  worker with contribution tasks pending (EXPERT)
[ ] HB-12  worker with contributions received — FORMATTED (EXPERT)
[ ] HB-13  has events since last heartbeat (EXPERT)
[ ] HB-14  context pressure: prepare (93%) (EXPERT)
[ ] HB-15  rate limit pressure: conserve (85%) (EXPERT)
[ ] HB-16  fleet in storm (warning) (EXPERT)
[ ] HB-17  compound: directive + tasks + messages (EXPERT)
[ ] HB-18  compound: idle with standing orders (EXPERT)
[ ] HB-19  HB-01 at CAPABLE (qwen3-8b condensed)
[ ] HB-20  HB-01 at LIGHTWEIGHT (gemma4-e2b minimal)
[ ] HB-21  HB-04 at CAPABLE (condensed fleet-ops reviews)
[ ] HB-22  HB-05 at CAPABLE (condensed PM triage)
[ ] HB-23  HB-04 at LIGHTWEIGHT (minimal fleet-ops)
[ ] HB-24  HB-02 at CAPABLE (condensed task detail)
[ ] HB-25  HB-02 at LIGHTWEIGHT (minimal task detail)
[ ] HB-26  HB-01 at FLAGSHIP-LOCAL (gemma4-26b dual GPU)
```

### Task Scenarios

```
[ ] TK-01  work, full injection, all contributions, opus-1m (GOLDEN PATH)
[ ] TK-02  work, full injection, NO contributions (missing)
[ ] TK-03  reasoning stage
[ ] TK-04  conversation stage
[ ] TK-05  injection:none
[ ] TK-06  rejection rework iteration 2
[ ] TK-07  architect contribution: design_input
[ ] TK-08  QA contribution: qa_test_definition
[ ] TK-09  with Plane, MVP phase
[ ] TK-10  progress 70% (implementation done)
[ ] TK-11  analysis stage
[ ] TK-12  investigation stage
[ ] TK-13  blocked task
[ ] TK-14  work, partial contributions
[ ] TK-15  devsecops contribution: security_requirement
[ ] TK-16  UX contribution: ux_spec
[ ] TK-17  writer contribution: documentation_outline
[ ] TK-18  work, confirmed plan visible
[ ] TK-19  work, previous stage findings visible
[ ] TK-20  progress 0% (just started)
[ ] TK-21  progress 50% (halfway)
[ ] TK-22  progress 90% (reviewed)
[ ] TK-23  reasoning, contributions not yet received
[ ] TK-24  epic task (all stages)
[ ] TK-25  subtask (skip contributions)
[ ] TK-26  bug task (analysis first)
[ ] TK-27  spike task (no work stage)
[ ] TK-28  rejection rework iteration 3
[ ] TK-29  no verbatim requirement
[ ] TK-30  TK-01 at CAPABLE (condensed golden path)
[ ] TK-31  TK-01 at LIGHTWEIGHT (minimal golden path)
[ ] TK-32  delivery phase: production (full standards)
[ ] TK-33  delivery phase: poc (minimal standards)
[ ] TK-34  engineer role-specific reasoning
[ ] TK-35  architect role-specific reasoning
[ ] TK-36  QA role-specific reasoning
[ ] TK-37  work with coworkers
[ ] TK-38  contribution task: target task visible (I1 fix)
[ ] TK-39  work + progress 0% + iteration 2 (rework start)
[ ] TK-40  TK-06 at CAPABLE (condensed rejection)
[ ] TK-41  TK-07 at CAPABLE (condensed contribution)
[ ] TK-42  concern task (no work stage)
[ ] TK-43  request task (all stages except investigation)
[ ] TK-44  TK-01 at FLAGSHIP-LOCAL (gemma4-26b dual GPU golden path)
[ ] TK-45  TK-01 at LIGHTWEIGHT (gemma4-e2b simple task)
```

### Fleet-Level Scenarios

```
[ ] FL-01  cycle_phase: planning — PM gets context, engineer gets "not active"
[ ] FL-02  cycle_phase: review — fleet-ops gets context, others get "not active"
[ ] FL-03  cycle_phase: crisis-management — fleet-ops + devsecops active, others "not active"
[ ] FL-04  cycle_phase: execution — all agents active (baseline)
[ ] FL-05  work_mode: work-paused — no dispatch, agents see "paused" in fleet state
[ ] FL-06  work_mode: finish-current-work — in-progress continues, no new dispatch
[ ] FL-07  work_mode: local-work-only — no Plane pull, OCMC tasks only
[ ] FL-08  backend_mode: claude — expert profile, full context
[ ] FL-09  backend_mode: localai — trainee profile, minimal context ("don't overwhelm")
[ ] FL-10  backend_mode: openrouter — community profile, focused context
[ ] FL-11  backend_mode: claude+localai — routing split: complex→claude, trivial→localai
[ ] FL-12  backend_mode: claude+openrouter — routing split: complex→claude, simple→openrouter
[ ] FL-13  backend_mode: localai+openrouter — free-only fleet, both trainee/community
[ ] FL-14  backend_mode: claude+localai+openrouter — full routing, cheapest capable wins
[ ] FL-15  security agent (devsecops) NEVER routes to trainee/community
[ ] FL-16  architecture agent (architect) NEVER routes to trainee/community
[ ] FL-17  budget_mode: turbo (5s cycle) — faster heartbeats, same context
[ ] FL-18  budget_mode: economic (60s cycle) — slower heartbeats, same context
[ ] FL-19  compound: planning phase + claude+localai backend — PM→claude, but PM is the only one active
[ ] FL-20  compound: crisis + storm warning — devsecops active, budget-aware, reduced dispatch
```

### Total: 26 heartbeat + 45 task + 20 fleet-level = 91 scenarios

Each gets:
1. Rendered by generate-validation-matrix.py
2. Inspected line by line
3. PO confirmed or corrected
4. Locked by pessimistic test

## Relationships

- RELATES TO: [[Tier Rendering Design Rationale]]
- RELATES TO: [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]]
- RELATES TO: [[Operational Modes — Heartbeat vs Task, Injection Levels]]
- BUILDS ON: [[Methodology Models Rationale]]
- FEEDS INTO: all context injection validation scenarios
