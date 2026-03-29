# Design: Project Management, Multi-Project & Multi-Model Operations

## User Requirements

> "some agent can work on a project while others work on another"

> "some can use opus while other can use sonnet. sometime it depends on the size of the task, how it was evaluated using SCRUM values like priority and such"

> "using a project manager agent, here again a new one. but we dont fear."

> "I set the requirements and the high standards."

## What This Means

### Multi-Project Parallel Operation

The fleet doesn't work on one project at a time. Multiple agents work on
multiple projects simultaneously:

```
architect → working on fleet architecture      (fleet project, opus)
software-engineer → fixing NNRT test suite     (nnrt project, sonnet)
qa-engineer → validating NNRT pipeline          (nnrt project, sonnet)
devops → setting up AICP CI pipeline            (aicp project, sonnet)
technical-writer → documenting fleet ops        (fleet project, sonnet)
```

Each agent has its own:
- Worktree (project-specific)
- Context (project-specific board memory, tags)
- MCP server instance (project-specific config)
- Model (based on task complexity)

### Model Selection

> "some can use opus while other can use sonnet"

Not all tasks need the most expensive model:
- Complex architecture decisions → opus (deep reasoning)
- Standard implementation tasks → sonnet (fast, capable)
- Documentation tasks → sonnet (speed matters more)
- Security audit → opus (thoroughness critical)
- Simple fixes → sonnet (don't overkill)

**Who decides?** The project manager agent evaluates:
- Task complexity (from description, dependencies, scope)
- Risk level (security? architecture? data?)
- Size estimate (SCRUM story points or T-shirt sizing)
- Agent capability requirements

**How it's configured:**
- Per-agent model default in agent.yaml
- Per-task model override in dispatch
- Project manager can override based on evaluation

### The Project Manager Agent

> "using a project manager agent, here again a new one"

**Role:** Evaluate, prioritize, size, assign, track.

**Responsibilities:**

1. **Task Evaluation**
   - Read task description
   - Assess complexity (simple / moderate / complex / epic)
   - Assess risk (low / medium / high / critical)
   - Estimate size (XS / S / M / L / XL — or story points)
   - Recommend model (sonnet / opus)

2. **Prioritization (SCRUM)**
   - Priority: urgent / high / medium / low
   - Business value vs effort
   - Dependencies (what blocks what)
   - Sprint planning: what fits in the next iteration

3. **Assignment**
   - Match task to best agent based on:
     - Required capabilities
     - Current workload
     - Agent availability
     - Project familiarity
   - Route via fleet routing engine

4. **Tracking**
   - Sprint velocity: tasks completed per period
   - Agent utilization: who's busy, who's idle
   - Blocker resolution time
   - PR review cycle time
   - Quality metrics per agent

5. **Reporting**
   - Sprint summary (what was planned, what was done, what's left)
   - Velocity trends
   - Bottleneck analysis
   - Recommendations (more agents needed? different assignment?)

### SCRUM Integration with OCMC

OCMC already has the primitives:

| SCRUM Concept | OCMC Feature |
|---------------|--------------|
| Story points | Custom field: `story_points` (integer) |
| Sprint | Tag: `sprint:N` or custom field: `sprint` |
| Priority | Task priority field (already exists) |
| Acceptance criteria | Task description (already exists) |
| Definition of Done | Approval system (confidence + rubric) |
| Sprint review | Daily digest + weekly summary |
| Retrospective | Board memory analysis by fleet-ops |
| Backlog | Tasks in `inbox` status |
| Sprint board | Tasks filtered by `sprint:current` tag |

**Additional custom fields needed:**
- `story_points` (integer) — complexity estimate
- `sprint` (text) — which sprint this belongs to
- `complexity` (text) — simple/moderate/complex/epic
- `model` (text) — recommended model (sonnet/opus)
- `estimated_hours` (decimal) — time estimate

### New Agents

> "but we dont fear. I set the requirements and the high standards."

Current roster: 8 agents. With project management and lifecycle:

| Agent | Role | Model |
|-------|------|-------|
| architect | System design, architecture review | opus |
| software-engineer | Implementation, bug fixes, tests | sonnet (opus for complex) |
| qa-engineer | Testing, validation, coverage | sonnet |
| ux-designer | Interface design, accessibility | sonnet |
| devops | CI/CD, infrastructure, deployment | sonnet |
| technical-writer | Documentation | sonnet |
| accountability-generator | Accountability systems | opus |
| fleet-ops | Governance, monitoring, digest | sonnet |
| **fleet-lifecycle** | Service health, self-healing | sonnet (daemon, minimal LLM) |
| **project-manager** | SCRUM: evaluate, prioritize, assign, track | opus |
| **fleet-admin** | Framework management, routing, updates | sonnet |

11 agents. Each with clear SRP. Some are LLM-heavy (project-manager uses opus for
judgment calls). Some are daemon-heavy (fleet-lifecycle mostly Python scripts).

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M170 | Project manager agent definition | SOUL.md, capabilities, SCRUM knowledge |
| M171 | Task evaluation skill | Complexity, risk, size, model recommendation |
| M172 | Sprint management | Sprint custom field, sprint planning, velocity tracking |
| M173 | Multi-model dispatch | Agent model selection based on task complexity |
| M174 | Agent workload tracking | Who's busy, who's idle, utilization metrics |
| M175 | Sprint reporting | Summary, velocity trends, bottleneck analysis |
| M176 | SCRUM custom fields | story_points, sprint, complexity, model, estimated_hours |
| M177 | Backlog management | Prioritized inbox, sprint assignment |

---