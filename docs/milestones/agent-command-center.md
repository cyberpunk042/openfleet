# Agent Command Center — Smart System In, Middleware, and Out

## User Requirements (Verbatim)

> "the agents need a 'command center' that will guide them to use the skills and workflow and make sure this evolve if we respect the rules and high standards"

> "I dont want an expression that could be a clean, clear and interpolated, interoperable, one liner to be a monstruous long or even multiline operation of something that could be greatly reduced / optimised / made better / easier to use and leaner."

> "We need to think I/O and directive and Meta, and preparation to task and before and after and structure and triggers and operations and so on."

> "We have to build clean patterns. make clean design pattern usage, libs when relevant and infrastructure pieces when relevant and know when its appropriate and so on."

> "We have to build with strong OOP and SRP and remember code hygiene like rule of never more than ~500 in general. (>~700 for exceptions, and stuff like this, like consistent naming and commenting and code headers and code docs and global docs too.)"

> "We need to think onion and domain. we need to remember how to split things by folder and use prefix or even suffix when appropriate."

> "There is also a Tags notion and we can use them and even add new ones in the OpenClaw Mission Control. There is also a whole 'approvals' notion and There is also a 'custom fields' notion"

> "So we need to detangle all that. do our researchs we need to identify the milestones and plan accordingly."

> "What we need is a smart system in, middleware and out. pre - progress - post - etc"

---

## The Problem

Agents have 12 skills, 7 templates, and a full communication protocol.
**They don't use them.** The E2E test proved it — the agent completed a task
correctly but used plain text instead of rich templates, didn't resolve URLs,
didn't use fleet-pr, fleet-comment, or fleet-urls skills.

The skills are reference documents. The SOUL.md mentions them. But there's no
**system** that guides agents through the workflow. No pre-task setup, no
mid-task enforcement, no post-task quality check.

The user's insight: **agents need a command center** — not more skills, but a
smart orchestration layer that:
- Prepares the agent before work (pre)
- Guides during work (progress)
- Validates after work (post)
- Evolves as standards change

## The Architecture: Smart System In, Middleware, Out

> "What we need is a smart system in, middleware and out. pre - progress - post - etc"

### PRE (Input / Preparation)

Before the agent starts ANY task:

1. **Context Loading** — agent reads its essentials:
   - TOOLS.md (credentials)
   - SOUL.md (role + standards + workflow)
   - Board memory (recent decisions, alerts, knowledge)
   - Task description + custom fields + tags + dependencies

2. **Directive Resolution** — what skills apply to this task?
   - Project worktree task → fleet-urls, fleet-pr, fleet-commit, fleet-comment
   - Review task → fleet-comment (completion format)
   - Alert situation → fleet-alert, fleet-irc
   - The "command center" tells the agent: "for THIS task, use THESE skills"

3. **Meta Setup** — resolve all references upfront:
   - Read config/url-templates.yaml → cache project URLs
   - Read config/skill-assignments.yaml → know what's available
   - Read board tags → know what tags to use
   - Resolve BOARD_ID, TASK_ID, PROJECT → ready for all API calls

### PROGRESS (Middleware / During Work)

While the agent works:

1. **Structured Checkpoints** — agent posts progress using templates (not freeform)
2. **Skill Invocation** — when the agent needs to commit, it invokes fleet-commit.
   When it needs to report, fleet-comment. Not by choice — by protocol.
3. **Quality Gates** — before each milestone action (commit, PR, completion),
   the agent verifies:
   - Commit follows conventional format?
   - All references are URLs?
   - Template used correctly?

### POST (Output / Validation)

After the agent completes:

1. **Completion Checklist** — the agent runs through:
   - [ ] Branch pushed?
   - [ ] PR created with fleet-pr template?
   - [ ] PR URL set in task custom fields?
   - [ ] Completion comment follows template?
   - [ ] IRC notified?
   - [ ] Board memory updated (if cross-task knowledge)?
2. **Self-Validation** — agent checks its own output before marking review
3. **Post-Hook** — fleet-sync and fleet-monitor pick up the rest

---

## Design Principles (from user)

### Clean Patterns and Design

> "make clean design pattern usage, libs when relevant and infrastructure pieces when relevant"

This means:
- **Library approach**: reusable functions/modules, not inline scripts
- **Design patterns**: command pattern for skill invocation, observer for events,
  template method for the pre/progress/post lifecycle
- **Right tool for the job**: Python lib for complex logic, SKILL.md for agent
  guidance, bash scripts for orchestration

### Code Hygiene

> "strong OOP and SRP... never more than ~500... consistent naming and commenting"

This means:
- Each module does ONE thing (SRP)
- Files under 500 lines (hard limit 700)
- Consistent naming: `fleet_` prefix for fleet modules, `skill_` for skills
- Code headers with purpose, author, date
- Docstrings on public functions
- Comments for non-obvious logic only

### Onion Architecture / Domain Thinking

> "We need to think onion and domain... split things by folder and use prefix or even suffix"

This means:
- **Core domain**: task lifecycle, agent communication, quality rules
- **Infrastructure**: MC API client, IRC client, GitHub client, OpenClaw gateway
- **Application**: skills, scripts, daemons, CLI
- **Presentation**: templates, formatters, message composers

Folder structure follows domain:
```
fleet/
├── core/               # Domain logic — task lifecycle, rules, protocols
│   ├── lifecycle.py    # Pre/progress/post task lifecycle
│   ├── quality.py      # Quality rules and validation
│   ├── routing.py      # Communication surface routing
│   └── urls.py         # URL resolution
├── infra/              # External system clients
│   ├── mc_client.py    # Mission Control API client
│   ├── irc_client.py   # IRC messaging
│   ├── gh_client.py    # GitHub CLI wrapper
│   └── gateway.py      # OpenClaw gateway RPC
├── skills/             # Skill invocation and management
│   ├── registry.py     # Discover and load skills
│   └── invoker.py      # Invoke skills programmatically
├── templates/          # Message templates and formatters
│   ├── pr.py           # PR body composer
│   ├── comment.py      # Task comment composer
│   ├── memory.py       # Board memory composer
│   └── irc.py          # IRC message formatter
└── cli/                # CLI entry points
    ├── dispatch.py     # Task dispatch
    ├── sync.py         # Task↔PR sync
    ├── monitor.py      # Board state monitor
    └── digest.py       # Daily digest
```

### Tags, Approvals, Custom Fields

> "There is also a Tags notion... a whole 'approvals' notion... a 'custom fields' notion"

These OCMC features are underused. Research needed:
- **Tags**: we created 13 tags. Are agents using them? Are we filtering by them?
  Can agents add new tags? How do tags drive workflow (auto-assign by tag)?
- **Approvals**: OCMC has a full approval system. We haven't used it.
  How does it work? Can it gate PR merges? Can agents create approvals?
  Can humans approve from the dashboard?
- **Custom fields**: we created 4. Are they populated consistently?
  Can we add more? What field types make sense (url, text, date)?

---

## What Needs to Happen

### Research Phase

1. **OCMC Approvals system** — full API study, how it integrates with task lifecycle
2. **OCMC Tags** — can tags drive automation? Agent-created tags? Tag-based views?
3. **OpenClaw skill invocation** — how to make agents USE skills automatically,
   not just have them available. Frontmatter settings, invocation policies.
4. **Agent SOUL.md architecture** — what's the right structure for a SOUL.md
   that enforces the pre/progress/post lifecycle?

### Architecture Phase

5. **Fleet Python library** — design the `fleet/` package with onion architecture
6. **Command center SOUL.md** — the master document agents read that guides them
   through the entire lifecycle with skill references
7. **Pre/progress/post lifecycle** — formalize as a protocol agents follow

### Build Phase

8. **fleet/ Python package** — core, infra, skills, templates, cli
9. **Refactor scripts** — replace 25+ bash scripts with clean Python CLI
10. **Command center integration** — agents use the library, not raw curl

### Validation Phase

11. **E2E quality test** — dispatch task, verify EVERY output meets standard
12. **Quality gate enforcement** — fleet-ops rejects substandard output

---

## Milestones (Preliminary — Needs Discussion)

| # | Milestone | Phase | Description |
|---|-----------|-------|-------------|
| M106 | OCMC approvals research | Research | Study API, integration, workflow |
| M107 | OCMC tags research | Research | Automation, agent-created, views |
| M108 | Skill invocation architecture | Research | How to make agents USE skills |
| M109 | Fleet Python library design | Architecture | Onion architecture, SRP, modules |
| M110 | Command center SOUL.md | Architecture | Pre/progress/post lifecycle doc |
| M111 | fleet/core/ — lifecycle + quality | Build | Task lifecycle, quality rules |
| M112 | fleet/infra/ — MC + IRC + GH clients | Build | Clean API clients |
| M113 | fleet/templates/ — composers | Build | PR, comment, memory, IRC formatters |
| M114 | fleet/cli/ — refactor scripts | Build | Replace bash with Python CLI |
| M115 | Agent SOUL.md rewrite | Build | Command center integration |
| M116 | E2E quality validation | Validation | Full test at godlike standard |
| M117 | Quality gate enforcement | Validation | Fleet-ops rejects bad output |

---

## Open Questions for Discussion

1. **Should the fleet/ package replace scripts/ entirely?** Or coexist?
   Scripts are simpler for one-off operations. Python is better for complex logic.

2. **How do we make agents USE skills without explicit prompting?**
   The current approach (skills in .agents/skills/) makes them available but not mandatory.
   Options: stronger SOUL.md, skill invocation hooks, pre-task prompt injection.

3. **Should the pre/progress/post lifecycle be in SOUL.md or in the dispatch message?**
   SOUL.md: agent always follows it. Dispatch: per-task customization possible.
   Could be both: SOUL.md defines the framework, dispatch fills in specifics.

4. **How aggressive should quality enforcement be?**
   Warn only? Block task completion? Require re-do?
   Start with warnings, graduate to blocking.

5. **What's the right level of abstraction for the Python library?**
   Too abstract = hard to understand. Too concrete = not reusable.
   Follow the user's guidance: "know when its appropriate."