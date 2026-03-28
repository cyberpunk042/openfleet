# Fleet Milestone Plans

## Workstreams

| # | Workstream | Doc | Milestones | Priority |
|---|-----------|-----|------------|----------|
| 1 | [Standards & Discipline](standards-and-discipline.md) | Conventional commits, changelogs, coding standards | M44-M47 | **Immediate** |
| 2 | [Skills Ecosystem](skills-ecosystem.md) | OpenClaw + OCMC skills, packs, fleet skills | M48-M52 | **High** |
| 3 | [Observability & Channels](observability-and-channels.md) | Control UI, WS monitor, external channels | M53-M56 | **High** |
| 4 | [Navigability & Traceability](navigability-and-traceability.md) | Commit↔task linking, smart refs, trace tool | M57-M60 | **Medium** |

## Recommended Execution Order

### Phase 1: Foundation Standards (M44-M47)
Do this FIRST — it affects everything that follows. Every subsequent milestone
produces commits and tasks that should follow these standards.

### Phase 2: Visibility (M53-M54)
Control UI documentation + WS event monitor. Low effort, high value.
These are already running — just need documentation and a CLI wrapper.

### Phase 3: Skills (M48-M50)
Inventory what exists, register packs, install useful skills.
This makes agents more capable before we send them on real missions.

### Phase 4: Traceability (M57-M58)
Commit↔task linking and smart references.
This ties the standards from Phase 1 to the task system.

### Phase 5: Deep Integration (M51-M52, M55-M56, M59-M60)
Fleet-specific skills, channel setup, unified dashboard, trace tool.
These build on everything above.

## Current Phase: Operations + Governance (Phases A-F)

| Phase | Doc | Milestones | Status |
|-------|-----|------------|--------|
| A | [Code Delivery](phase-a-code-delivery.md) | M61-M64: push, PR, custom fields, notifications | Mostly done |
| B+C | [Operations Protocol](fleet-operations-protocol.md) | M65-M72: board config, sync, merge detection | Mostly done |
| — | [Operational Gaps](operational-gaps.md) | 6 fundamental gaps identified | Documented |
| F1 | [Foundation Skills](phase-f1-foundation-skills.md) | M81-M86: URL builder, markdown templates, PR/comment/memory/IRC skills | **Planning** |
| F2 | [Agent Communication](phase-f2-agent-communication.md) | M87-M91: decision matrix, follow-ups, alerts, pause, gap detection | **Planning** |
| F3 | [IRC + The Lounge](phase-f3-irc-the-lounge.md) | M92-M96: web client, channels, message format, IRC ops | **Planning** |
| F4 | [Governance Agent](phase-f4-governance-agent.md) | M97-M102: monitoring, digest, quality enforcement, gap detection | **Planning** |
| F5 | [Integration + Polish](phase-f5-integration-polish.md) | M103-M105: E2E quality test, agent awareness, playbook | **Planning** |
| — | [Governance Requirements](fleet-governance-and-quality.md) | User requirements with verbatim quotes | Reference |

## Completed Milestones

| # | Milestone | Status |
|---|-----------|--------|
| M38-M40 | Provisioning, autonomous execution, observation tools | Done |
| M44-M47 | Standards, conventional commits, changelog, STANDARDS.md | Done |
| M48-M51 | Skills inventory, packs, marketplace install, fleet skills | Done |
| M53-M54 | Control UI, WS event monitor | Done |
| M57, M59 | Commit↔task linking, trace tool | Done |
| M61 | Agent push + PR workflow | Done |
| M65-M66 | Board custom fields + tags | Done |
| M70, M72 | Fleet sync (merge detection + worktree cleanup) | Done |
| M73-M74 | IRC setup + notifications | Done |
| — | Infrastructure: worktrees, auth, patches, systemd | Done |

## Phase Dependencies

```
F1 (Foundation Skills — URL builder, markdown, PR/comment skills)
    ↓
F2 (Agent Communication — decision matrix, follow-ups, alerts)
    ↓
F3 (IRC + The Lounge — web client, channels, message format)
    ↓
F4 (Governance Agent — monitoring, digest, quality, gaps)
    ↓
F5 (Integration + Polish — E2E test, awareness, playbook)
```

Each phase builds on the previous. Quality gates between phases.
Do NOT start the next phase until the current one meets the standard.