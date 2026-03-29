# Design: Agent Framework & Routing — Shared Intelligence

## User Requirements

> "I talked about a lot of skills and logic and rules my agents should respectively and commonly have, understand, follow and respect and use."

> "This is a complex task but it is possible with the right 'framework' and 'routing'."

> "we need an agent that will manage all this stuff to make it keen and keep it up to date and so on."

> "This does not remove anything we already wrote it only augment it. again tenfold."

## What This Means

There are TWO layers of agent intelligence:

### Layer 1: Common Intelligence (all agents share)
- How to use fleet tools (MCP)
- Communication protocols (which surface, when, what format)
- Quality standards (commits, comments, PRs)
- How to alert, pause, suggest, create follow-ups
- How to read context and work within the fleet

This is the **framework**. It's not in each agent's SOUL.md — it's a SHARED system
that every agent inherits. Like a base class in OOP. Every agent IS-A fleet agent
first, and a specialist second.

### Layer 2: Specialist Intelligence (per-agent)
- Architect knows system design
- Software-engineer knows implementation
- QA knows testing methodology
- Each agent has domain-specific skills and judgment

The specialist layer EXTENDS the framework. It doesn't replace it.

### The Routing

> "the right 'framework' and 'routing'"

Routing means: **the right work goes to the right agent through the right path.**

- Task created with `type:review` tag → routes to qa-engineer or architect
- Alert with `category:security` → routes to devops + human (IRC #alerts)
- Follow-up task about docs → routes to technical-writer
- Task about UI → routes to ux-designer
- Task too complex for one agent → project-manager splits it

**Routing is not hardcoded.** It's based on:
- Tags (project, type, severity)
- Agent capabilities (defined in agent.yaml)
- Agent availability (online/offline, current workload)
- Task priority and size
- Project assignment

### The Management Agent

> "we need an agent that will manage all this stuff to make it keen and keep it up to date"

This is bigger than fleet-ops (governance). This is a **fleet management agent** that:
- Maintains the framework itself (updates rules, adds skills)
- Keeps agents up to date (pushes SOUL.md changes, .mcp.json updates)
- Manages routing rules (which agent gets what)
- Tracks framework compliance (are agents following the rules?)
- Evolves the system (proposes new skills, new agents, new rules)

> "taking the latest change if working on itself and so on and updating about the status"

Self-referential: the management agent can work on its own system. If a skill
needs updating, it updates it. If a new rule is needed, it proposes and implements it.
It tracks its own changes and reports status.

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M148 | Framework base class design | Common intelligence all agents inherit |
| M149 | Routing rules engine | Tag-based, capability-based, availability-based routing |
| M150 | Fleet management agent definition | SOUL.md, capabilities, self-management |
| M151 | Framework distribution system | How updates reach all agents automatically |
| M152 | Compliance tracking | Are agents following the framework? |

---