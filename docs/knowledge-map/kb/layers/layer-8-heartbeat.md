# Layer 8: HEARTBEAT.md

**Type:** Agent File (Middle layer — stable, injected LAST)
**Position:** 8 of 8 (action prompt — drives immediate next action)
**System:** S22 (Agent Intelligence)
**Standard:** heartbeat-md-standard.md

## Purpose

The action protocol. Injected LAST after the agent has absorbed identity, values, rules, tools, team, state, and task. By position 8, the AI's response space is narrowed — HEARTBEAT.md drives the IMMEDIATE next action within that narrow band. "What to do NOW."

## Universal Priority Order (ALL agents)

```
0. PO DIRECTIVES          ← highest priority, execute immediately
1. MESSAGES (@mentions)   ← respond to all colleague messages
2. CORE JOB               ← role-specific primary work
3. PROACTIVE CONTRIBUTIONS ← role-specific proactive actions
4. HEALTH/MONITORING      ← role-specific health checks
5. HEARTBEAT_OK           ← ONLY if nothing above needs attention
```

**HEARTBEAT_OK is ALWAYS LAST.** Never report OK before checking priorities 0-4.

## 5 Heartbeat Types (not 10 — shared worker template)

| Type | Roles | Core Job Focus |
|------|-------|---------------|
| **PM** | project-manager | Task assignment (ALL fields), contribution check, gate routing (50%/90%), stage progression, sprint management, epic breakdown |
| **Fleet-Ops** | fleet-ops | 4-step real review (read work → verify trail → check quality → decide), board health, methodology compliance |
| **Architect** | architect | Stage-driven design work + design contributions + architecture health, investigation always min 2 options |
| **DevSecOps** | devsecops-expert | Security contributions (SPECIFIC requirements), PR security review, security_hold mechanism, crisis response (1 of 2 crisis agents) |
| **Worker** | engineer, devops, QA, writer, UX, accountability | Shared template with stage-driven work + per-role variation table for work stage and contribution protocol |

## Relationships

- INJECTED BY: gateway (_build_agent_context, position 8 — LAST)
- PROVISIONED FROM: agents/_template/heartbeats/{pm,fleet-ops,architect,devsecops,worker}.md
- CONTENT FROM: fleet-elevation/05-14 (per-role heartbeat specifications)
- VALIDATED BY: scripts/validate-agents.sh (priority order preserved, HEARTBEAT_OK last, core job role-specific, stage awareness, readiness >= 99 prerequisite)
- FEEDS: agent's immediate behavior (the action they take RIGHT NOW)
- CONNECTS TO: agent_lifecycle.py (consecutive HEARTBEAT_OK → IDLE → SLEEPING → brain evaluation)
- CONNECTS TO: heartbeat_gate.py (brain evaluates sleeping agents BEFORE firing heartbeat)
- CONNECTS TO: fleet-context.md Layer 6 (agent reads state THEN heartbeat tells them what to do about it)
- CONNECTS TO: fleet_read_context tool (heartbeat often starts with this call)
- DOES NOT CONTAIN: identity (Layer 1), values (Layer 2), rules (Layer 3), tool docs (Layer 4), colleague info (Layer 5), dynamic data (Layers 6-7)
- STABLE: changes when fleet evolves, not during operation
- PER AGENT: 5 unique types covering 10 agents

## The Heartbeat → Lifecycle Connection

```
Agent heartbeats → reads HEARTBEAT.md → follows priority order
├── Has work? → ACTIVE (does work, calls tools)
├── No work? → reports HEARTBEAT_OK
│   ├── 1 consecutive HEARTBEAT_OK → brain_evaluates = True
│   │   └── Next heartbeat: brain evaluates in Python ($0)
│   │       ├── Wake trigger found → WAKE (real heartbeat)
│   │       └── Nothing found → SILENT ($0)
│   ├── 3+ consecutive → SLEEPING
│   └── 4+ hours → OFFLINE
└── Work assigned → reset to ACTIVE
```

**Impact:** HEARTBEAT_OK drives the lifecycle state transitions that enable the 70% cost reduction from silent heartbeats.
