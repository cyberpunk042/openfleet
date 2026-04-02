# fleet-communicate

**Type:** Skill (slash command)
**Invocation:** /fleet-communicate
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-communicate
**User-invocable:** No (agent-only)

## Purpose

Communication guide for all agents: which surface to use for which type of message. Covers internal chat (agent-to-agent), board memory (persistent decisions/alerts/knowledge), IRC channels (topic-specific), ntfy (human notifications by urgency), and escalation (human attention required). Ensures agents route messages to the correct communication surface.

## Assigned Roles

- **ALL agents** -- this is a default skill assigned to every agent via the defaults block in agent-tooling.yaml

## Methodology Stages

- **Stage 1 (CONVERSATION)** -- agents use this to know how to communicate with PO and colleagues
- **Stage 2 (ANALYSIS)** -- communication guidance for discussing findings
- **Stage 3 (INVESTIGATION)** -- communication guidance for discussing options
- **Stage 4 (REASONING)** -- communication guidance during planning
- **Stage 5 (WORK)** -- communication guidance during active work
- Used across ALL stages as a cross-cutting concern

## What It Produces

- Correctly routed messages across 5 communication surfaces
- Properly tagged board memory entries (decision, alert, knowledge, suggestion)
- Appropriate ntfy urgency levels (info/important/urgent)

## Key Steps

1. **Internal Chat (fleet_chat)** -- for agent-to-agent real-time communication: request work, ask questions, share info, respond to requests. Use @mentions to target specific agents.
2. **Board Memory (fleet_alert, fleet_task_complete)** -- for persistent knowledge spanning tasks. Tag entries: [decision, project:{name}], [alert, {severity}, {category}], [knowledge, {topic}], [suggestion, {area}].
3. **IRC Channels** -- routed automatically via fleet tools. 10 channels: #fleet (general), #sprint (progress), #agents (health), #security (findings), #human (needs attention), #reviews (PRs), #builds (CI/CD), #memory (decisions), #alerts (critical), #plane (sync).
4. **ntfy (fleet_notify_human)** -- human notifications by urgency: info to fleet-progress (quiet), important to fleet-review (prominent), urgent to fleet-alert (sound, persistent).
5. **Escalation (fleet_escalate)** -- when human attention needed NOW. Posts to board memory + IRC #human + ntfy urgent. Must include: what you need, why, what is blocked.

## Communication Decision Matrix

| Situation | Surface | Tool |
|-----------|---------|------|
| Quick question to teammate | Internal chat | fleet_chat |
| Decision affecting team | Board memory | fleet_alert(category) |
| Work completed | Automatic | fleet_task_complete |
| Stuck, need help | Escalation | fleet_escalate |
| Security issue found | Board memory + alert | fleet_alert(severity, "security") |
| Progress update | Task comment | fleet_task_progress |
| Need human decision | Escalation | fleet_escalate |
| Sprint milestone | Automatic | Orchestrator via ntfy |
| Idle, requesting work | Internal chat | fleet_chat(mention="lead") |

## Relationships

- USED BY: ALL agents (architect, software-engineer, qa-engineer, devops, devsecops-expert, fleet-ops, project-manager, technical-writer, ux-designer, accountability-generator)
- CONNECTS TO: fleet_chat (MCP tool), fleet_alert (MCP tool), fleet_notify_human (MCP tool), fleet_escalate (MCP tool), fleet_task_complete (MCP tool), fleet_task_progress (MCP tool), IRC system (10 channels), ntfy notification system (3 urgency levels)
- FEEDS: IRC channels (all agent messages routed to appropriate channels), ntfy notifications (human-facing alerts), board memory (persistent cross-task knowledge), escalation pipeline (human attention requests)
- DEPENDS ON: fleet MCP server running, IRC daemon running, ntfy server configured, board memory storage available
