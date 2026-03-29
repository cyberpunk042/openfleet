# Fleet Milestones

## Source of Truth

**[STATUS-TRACKER.md](STATUS-TRACKER.md)** — the single file that tracks what's done, what's not, and what's next. Start here.

## Directory Structure

```
milestones/
├── README.md              ← you are here
├── STATUS-TRACKER.md      ← source of truth for all work status
├── active/                ← work with remaining items
│   ├── fleet-autonomy-milestones.md    (29 remaining — event chains, routing, self-healing)
│   ├── fleet-operations-protocol.md    (19 remaining — board ops, merge detection)
│   ├── strategic-vision-localai-independence.md  (THE mission — 5 stages)
│   ├── agent-command-center.md         (PRE→PROGRESS→POST lifecycle)
│   ├── phase-f1-foundation-skills.md   (URL builder, markdown, PR/comment skills)
│   ├── phase-f2-agent-communication.md (decision matrix, alerts, pause)
│   ├── phase-f3-irc-the-lounge.md      (web client, channels, message format)
│   ├── phase-f4-governance-agent.md    (monitoring, digest, quality)
│   ├── phase-a-code-delivery.md        (push, PR, custom fields)
│   ├── navigability-and-traceability.md (commit↔task linking)
│   ├── observability-and-channels.md   (control UI, channels)
│   ├── skills-ecosystem.md            (OpenClaw skills, packs)
│   └── standards-and-discipline.md    (commits, changelogs, standards)
├── design/                ← architecture and design reference (no checklists)
│   ├── design-agent-framework-routing.md
│   ├── design-agent-interface.md
│   ├── design-autonomous-drivers.md
│   ├── design-event-chains.md
│   ├── design-fleet-mcp-server.md
│   ├── design-fleet-python-library.md
│   ├── design-lifecycle-health.md
│   ├── design-ocmc-primitives.md
│   ├── design-pre-post-pipeline.md
│   ├── design-project-management.md
│   ├── design-surface-interactions.md
│   ├── claude-code-feature-exploitation.md
│   ├── communication-infrastructure-milestones.md
│   ├── fleet-evolution-milestones.md
│   ├── fleet-governance-and-quality.md
│   └── phase-f5-integration-polish.md
└── archive/               ← completed or superseded (historical reference)
    ├── catastrophic-usage-drain-investigation.md
    ├── critical-bugs-and-missing-work.md
    ├── dspd-plane-integration.md  (moved to DSPD repo)
    ├── investigation-flow-gaps.md
    ├── note-persistence-caching.md
    ├── operational-gaps.md
    └── pre-relaunch-milestones.md
```

## Priority Order

1. **Fleet operational validation** — daemons stable, orchestrator cycling, agents heartbeating
2. **DSPD/Plane deployment** — setup.sh install, mission seeded, PM agent connected
3. **AICP/LocalAI Stage 1** — inference working, benchmarked, 3B model for heartbeats
4. **Fleet autonomy** — event chains, routing, self-healing (29 items)
5. **Agent quality** — command center, governance, skills

## Cross-Project Work

Fleet work items live in Plane (DSPD) once deployed:
- **OF** project — fleet infrastructure, MCP, agents, autonomy
- **AICP** project — LocalAI independence (THE mission)
- **DSPD** project — Plane itself, CLI, sync, webhooks
- **NNRT** project — report transformer

The project-manager agent creates tasks from epics. Humans define direction in Plane.