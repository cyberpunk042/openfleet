# Design: Surface Interaction Models

## User Requirements

> "This will need to be highly operable from all front with all logical order like from IRC its not the same type of interactions as from the internal / board chat and whatnot"

> "for everything we need proper custom fields and tagging and our own headers and structures and format and whatnot and pre and/or post and whatnot"

## What This Means

Each surface has its OWN interaction model. You don't interact with agents the same
way in IRC as in MC board memory as in task comments. Each surface has different:
- Input format (how the human/agent writes)
- Output format (how information is displayed)
- Capabilities (what actions are possible)
- Context (what's visible, what's not)
- Urgency (real-time vs async)

## Surface Definitions

### IRC (#fleet, #alerts, #reviews)

**Nature:** Real-time, conversational, ephemeral (but logged)
**Input from human:** Natural language, @mentions, short commands
**Output from system:** Structured one-liners with emoji + URLs
**Interaction pattern:**

```
Human:    @architect what's the status of NNRT architecture?
Agent:    [architect] NNRT architecture: 3 decisions made, 1 open question.
          See board memory: http://localhost:3000/boards/.../memory?tags=architecture,project:nnrt
Human:    merge PR #4
System:   [fleet] 🔀 Merging PR #4... done. Task auto-closed.
Human:    create task "Add CI pipeline to NNRT" for devops priority high
System:   [fleet] 📋 Task created: Add CI pipeline to NNRT → devops
          http://localhost:3000/boards/.../tasks/...
```

**IRC is for:**
- Quick commands (merge, create task, check status)
- Real-time alerts (human sees immediately)
- Agent status broadcasts
- Brief Q&A with agents

**IRC is NOT for:**
- Detailed task descriptions (use MC)
- Code review (use GitHub)
- Long-form decisions (use board memory)

### MC Board Memory (Internal Chat)

**Nature:** Persistent, searchable, tagged, cross-agent
**Input from human:** Structured messages with @mentions and tags
**Output from agents:** Formatted markdown with templates
**Interaction pattern:**

Human posts a directive:
```markdown
@architect Review the current NNRT pipeline architecture and identify
any coupling risks with the new validation layer.

Tags: chat, directive, project:nnrt
```

Architect responds:
```markdown
## 📋 Architecture Review: NNRT Pipeline × Validation

**Requested by:** @human
**Project:** nnrt

### Findings
- Pipeline passes (p01-p50) are loosely coupled via IR ✅
- Validation layer imports directly from pipeline internals ⚠️
  - [`nnrt/validate/schema.py`](github_url) imports `PipelineConfig`
  - This creates a circular dependency risk

### Recommendation
Extract shared types to `nnrt/core/types.py` to break the coupling.

### Follow-up
Created task: [Extract shared types](task_url) → software-engineer

---
Tags: architecture, review, project:nnrt
```

**Board memory is for:**
- Decisions that affect the project
- Cross-agent knowledge
- Directives from human to agents
- Detailed analysis and reports
- Persistent knowledge base

**Board memory is NOT for:**
- Task-specific progress (use task comments)
- Quick commands (use IRC)
- Code review (use GitHub)

### MC Task Comments

**Nature:** Task-scoped, chronological, structured
**Input from human:** @mentions, instructions, feedback
**Output from agents:** Structured templates (acceptance, progress, completion, blocker)
**Interaction pattern:**

Human comments on a task:
```
@software-engineer also check if the validation module has type hints
```

Agent responds in next progress update:
```markdown
## 🔄 Progress Update

**Done:** Type hints added to engine.py (5 functions)
**Next:** Checking validation module for type hints (per @human request)
**Blockers:** None

---
<sub>software-engineer · [task:abc123](task_url)</sub>
```

**Task comments are for:**
- Task-specific progress and results
- Communication about THIS task
- Structured completion reports
- Blocker notifications

**Task comments are NOT for:**
- Cross-task decisions (use board memory)
- Quick alerts (use IRC)
- General discussion (use board memory or IRC)

### MC Approvals

**Nature:** Formal, gated, scored
**Input:** Agent creates approval request with confidence + rubric
**Output:** Human approves/rejects with optional feedback
**Interaction pattern:**

Agent requests approval:
```json
{
  "action_type": "task_completion",
  "confidence": 92.0,
  "rubric_scores": {"correctness": 95, "completeness": 90, "quality": 91},
  "payload": {"reason": "All type hints added, tests pass, no breaking changes"}
}
```

Human reviews in MC dashboard, sees scores, approves or rejects.
If rejected, agent is notified with reason and reworks.

**Approvals are for:**
- Quality gates before task completion
- Security-sensitive changes
- Architecture decisions that need human sign-off
- PR merge authorization

### GitHub (PRs, Issues)

**Nature:** Public, permanent, code-focused
**Input from human:** Code review comments, merge actions
**Output from agents:** PR body, PR comments, commit messages
**Interaction pattern:**

Standard GitHub PR review flow. The fleet system creates PRs,
human reviews code, merges when ready. The fleet system detects
merges and syncs state back to MC.

## Headers and Structures

> "our own headers and structures and format"

### IRC Message Header
```
[{agent_name}] {emoji} {EVENT}: {title} — {url}
```

### Board Memory Header
```markdown
## {emoji} {Type}: {title}

**{metadata_field}:** {value}
...

### {Section}
{content}

---
Tags: {tag1}, {tag2}, ...
```

### Task Comment Header
```markdown
## {emoji} {Type}

**{key}:** {value}
...

---
<sub>{agent_name} · [{task_short}]({task_url})</sub>
```

### Approval Header
```json
{
  "action_type": "{type}",
  "confidence": {0-100},
  "rubric_scores": {...},
  "payload": {"reason": "..."}
}
```

Each surface has its own header. Consistent within surface, distinct between surfaces.

## Milestones

| # | Milestone | Scope |
|---|-----------|-------|
| M157 | IRC interaction model | Commands, responses, routing |
| M158 | Board memory interaction model | Directives, responses, threading |
| M159 | Task comment interaction model | Templates, per-type formatting |
| M160 | Approval interaction model | Creation, review, resolution flow |
| M161 | Cross-surface reference linking | IRC msg → board memory → task → PR |
| M162 | Surface-aware formatting in fleet MCP | Tools format differently per surface |

---