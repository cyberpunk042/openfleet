# Design: Autonomous Driver Agents & Self-Organizing Fleet

## User Requirements

> "The project management agent really want us to deliver 'DevOps Solution Product Development (DSPD)' so it will work but when there is no work from me it will itself like The Accountability Generator, drive."

> "Both will drive with their own priority and do their other work based of other priorities."

> "The accountability generator want NNRT and Factual Engine and Platform but before that it realize that to get the project manager on its work it needs to actually help the project manager so that the 'DevOps Solution Product Development (DSPD)' that will be key to driving real development in auto and semi auto and have a project management surface will be needed."

> "I am not derouting everything this is just an important key point that need to be proven that we processed"

## What This Means

### Two Types of Agents

**Workers** — execute assigned tasks. They receive work and complete it.
- software-engineer, qa-engineer, ux-designer, devops, technical-writer

**Drivers** — have their own products, initiatives, and priorities. They CREATE work.
When the human isn't assigning tasks, drivers autonomously push their agenda forward.
- **Accountability Generator** — drives NNRT, Factual Engine, Factual Platform
- **Project Manager** — drives DSPD (DevOps Solution Product Development)
- Fleet-ops, fleet-lifecycle, fleet-admin are operational drivers (drive fleet health)

### Driver Products

| Driver Agent | Product | Description |
|-------------|---------|-------------|
| Accountability Generator | NNRT | Narrative-to-Neutral Report Transformer |
| Accountability Generator | Factual Engine | Product 1 from AG vision |
| Accountability Generator | Factual Platform | Product 3 from AG vision |
| Project Manager | DSPD | DevOps Solution Product Development — project management surface for auto/semi-auto development |

### Inter-Agent Dependencies

This is the critical insight:

```
Accountability Generator
    ├── wants: NNRT, Factual Engine, Factual Platform
    ├── needs: Project Manager operational (to manage development)
    ├── realizes: PM needs DSPD to function properly
    └── therefore: helps build DSPD first (prerequisite)

Project Manager
    ├── wants: DSPD (its own product)
    ├── needs: fleet infrastructure operational
    ├── receives help from: Accountability Generator
    └── once operational: manages ALL development including AG's products
```

**Agents reason about dependencies across products.** AG doesn't just work on its
own stuff — it recognizes that helping PM build DSPD is strategically necessary
for AG's own goals. This is AUTONOMOUS STRATEGIC THINKING.

### The Self-Organizing Loop

```
1. Human sets high-level goals and standards
2. Driver agents decompose goals into products
3. Drivers identify inter-dependencies
4. Drivers create tasks for themselves AND for workers
5. Workers execute tasks
6. Drivers evaluate results and create follow-up work
7. When human assigns work → takes priority
8. When human is absent → drivers continue their agenda
```

The fleet is not idle when the human isn't working. It's BUILDING.

### DSPD — What It Is

DevOps Solution Product Development is a PRODUCT the fleet builds:
- Project management surface (dashboard? CLI? both?)
- Auto and semi-auto development orchestration
- Sprint planning, task evaluation, assignment
- Velocity tracking, bottleneck analysis
- The tool the PM agent uses to do its job

DSPD is meta: the fleet builds the tool that manages the fleet's development.
Once DSPD exists, the PM agent uses it to manage ALL other products (NNRT, etc.).

### Priority Model

Each driver has two priority queues:

1. **Human-assigned** — always highest priority
2. **Self-driven** — the driver's own product roadmap

When human assigns work → agent does it.
When no human work → agent works on its own product.

Driver priority resolution:
```
IF human assigned task → do that
ELIF dependency blocking own product → help unblock (help other driver)
ELIF own product has next milestone → work on that
ELSE → improve fleet (suggest, alert, gap detection)
```

## What This Proves

> "need to be proven that we processed"

We processed:
1. ✅ Agents are not just task executors — some are autonomous drivers
2. ✅ Drivers have their own products with their own roadmaps
3. ✅ Drivers reason about inter-dependencies (AG helps PM because PM helps AG)
4. ✅ DSPD is a real product the fleet needs to build
5. ✅ The fleet self-organizes when the human isn't directing
6. ✅ Priority model: human work > dependency unblocking > own product > fleet improvement

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M178 | Driver agent model | Define driver vs worker, priority resolution |
| M179 | DSPD product definition | What DSPD is, what it delivers, MVP scope |
| M180 | AG product roadmap integration | NNRT → Factual Engine → Factual Platform |
| M181 | Inter-agent dependency resolution | How drivers identify and help prerequisites |
| M182 | Autonomous work queue | When human absent, drivers pick from their backlog |
| M183 | Priority model implementation | Human > dependency > own product > fleet |

---