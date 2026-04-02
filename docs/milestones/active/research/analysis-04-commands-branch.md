# Analysis 04 — Commands Branch of the Knowledge Map

**Date:** 2026-04-02
**Status:** ANALYSIS — mapping all commands into the knowledge tree
**Purpose:** Every command has a place per role per stage in the map

---

## The Commands Landscape

50+ slash commands available in Claude Code. None currently documented
in any agent's CLAUDE.md or TOOLS.md. This branch maps WHEN each
command is valuable, for WHICH role, at WHICH methodology stage.

---

## Commands Mapped to Roles and Stages

### Session Management Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/compact [focus]` | Compact with preservation instructions | ALL | any | Context approaching 70%. Save key state first. Specify what to preserve: "retain task context, plan, contributions" |
| `/clear` | Clear conversation, fresh start | ALL | between tasks | Between logical tasks. After fleet_task_complete. When starting unrelated work. |
| `/resume [id]` | Resume session by ID | ALL | any | Continue interrupted work. After gateway restart. |
| `/rewind` | Rewind to checkpoint | ALL | work | Undo a wrong approach. Return to known-good state. |
| `/branch [name]` | Branch conversation | ARCH, ENG | reasoning | Explore alternative approaches without losing current context. |
| `/export [file]` | Export as plain text | PM, WRITER, ACCT | any | Archive session for audit trail. Create handoff documents. |

### Model & Effort Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/model [model]` | Select model | ALL | any | Switch to opus for complex reasoning. Switch to sonnet for routine work. Match model to task complexity. |
| `/effort [level]` | Set effort level | ALL | any | `high` for architecture decisions. `max` (opus only) for critical security analysis. `low` for simple updates. |
| `/fast [on\|off]` | Toggle fast mode | ALL | work | Speed up routine implementation. Toggle off for complex reasoning. |

### Context & Cost Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/context` | Visualize context grid | ALL | any | Before heavy codebase reads. When context feels sluggish. After compaction to verify preservation. |
| `/cost` | Token usage stats | PM, FLEET-OPS, ACCT | any | Budget awareness. Sprint cost tracking. Per-task cost assessment. |
| `/usage` | Rate limit status | ALL | any | Check remaining quota before heavy operations. Near rate limit rollover awareness. |

### Git & Code Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/diff` | Interactive diff viewer | ENG, QA, FLEET-OPS | work, review | Review changes before commit. Fleet-ops review step 2. Compare turn-by-turn changes. |
| `/plan [desc]` | Enter plan mode | ALL | reasoning | Before complex implementation. Architecture design sessions. Sprint planning. Read-only exploration. |
| `/pr-comments [PR]` | Fetch PR comments | FLEET-OPS, ENG | review | Read review feedback. Process rejection comments. |
| `/security-review` | Analyse branch for vulns | DEVSEC, FLEET-OPS | review, work | Before approval. Security gate check. On security-flagged PRs. |

### Agents & Tasks Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/agents` | Manage subagents | ARCH, FLEET-OPS | any | Configure custom subagents for specialized tasks. |
| `/skills` | List available skills | ALL | any | Discovery — what skills do I have? |
| `/tasks` | List background tasks | ALL | work | Monitor parallel operations. Check subagent progress. |

### Bundled Skill Commands

| Command | What It Does | Roles | Stages | When to Use |
|---------|-------------|-------|--------|-------------|
| `/batch <instruction>` | Orchestrate parallel changes | ARCH, ENG, DEVOPS | work | Large-scale refactors across multiple files/worktrees. Parallel PR creation. |
| `/debug [desc]` | Debug logging + troubleshoot | ENG, DEVOPS, QA | investigation, work | Test failures. Runtime errors. Integration issues. Replaces guessing with systematic diagnosis. |
| `/loop [interval] <prompt>` | Repeat prompt on schedule | DEVOPS, FLEET-OPS | work | Monitoring checks. Periodic health assessment. Watching for deployment completion. |
| `/simplify [focus]` | Review + fix quality issues | ENG, QA | work | Post-implementation quality pass. 3 parallel agents review changed files. |

---

## Per-Role Command Guidance

### Project Manager
**Primary:** `/plan` (sprint planning), `/cost` (budget tracking), `/usage` (rate limits)
**Secondary:** `/compact` (between planning sessions), `/export` (archive decisions)
**Stage guidance:**
- REASONING: `/plan` to structure sprint, `/cost` to estimate
- WORK: `/usage` to monitor fleet consumption

### Fleet-Ops
**Primary:** `/diff` (review step 2), `/pr-comments` (read feedback), `/security-review` (security gate)
**Secondary:** `/context` (before heavy reviews), `/cost` (fleet budget awareness)
**Stage guidance:**
- REVIEW: `/diff` → `/pr-comments` → `/security-review` → fleet_approve
- ANALYSIS: `/context` to inspect fleet health

### Architect
**Primary:** `/plan` (design mode), `/branch` (explore alternatives), `/batch` (parallel refactors)
**Secondary:** `/model opus` (complex design), `/effort high` (architecture decisions)
**Stage guidance:**
- REASONING: `/plan` → explore design options → `/branch` to try alternatives
- WORK: `/batch` for cross-file architecture changes

### DevSecOps (Cyberpunk-Zero)
**Primary:** `/security-review` (vulnerability analysis), `/debug` (security investigation)
**Secondary:** `/effort max` (critical security analysis — opus only)
**Stage guidance:**
- INVESTIGATION: `/security-review` on branches, `/debug` on security issues
- ANALYSIS: Systematic vulnerability assessment

### Software Engineer
**Primary:** `/debug` (troubleshooting), `/diff` (review own changes), `/plan` (before complex impl)
**Secondary:** `/compact` (near context limit), `/fast on` (routine implementation)
**Stage guidance:**
- REASONING: `/plan` to structure implementation approach
- WORK: `/debug` when stuck, `/diff` before commit, `/fast on` for routine
- INVESTIGATION: `/debug` to understand existing behavior

### DevOps
**Primary:** `/loop` (monitoring), `/debug` (deployment issues), `/batch` (infrastructure changes)
**Secondary:** `/plan` (infrastructure design)
**Stage guidance:**
- WORK: `/loop 5m check deployment status`, `/batch` for multi-file infra changes
- INVESTIGATION: `/debug` for infrastructure issues

### QA Engineer
**Primary:** `/debug` (test failure analysis), `/diff` (verify changes), `/simplify` (quality pass)
**Secondary:** `/plan` (test strategy)
**Stage guidance:**
- WORK: `/debug` on failures, `/simplify` post-implementation quality review
- ANALYSIS: `/diff` to understand what changed

### Technical Writer
**Primary:** `/plan` (doc structure), `/compact` (between doc sections)
**Secondary:** `/context` (before large doc reads), `/export` (archive docs)
**Stage guidance:**
- REASONING: `/plan` to structure documentation
- WORK: `/compact` to manage context during large doc sessions

### UX Designer
**Primary:** `/plan` (UX design), `/context` (before UI analysis)
**Secondary:** `/branch` (explore design alternatives)
**Stage guidance:**
- REASONING: `/plan` for UX design → `/branch` to explore alternatives
- WORK: implementation of UX specs

### Accountability Generator
**Primary:** `/cost` (fleet cost audit), `/export` (compliance records)
**Secondary:** `/context` (before large audit sessions)
**Stage guidance:**
- ANALYSIS: `/cost` for budget audit, compile compliance data
- WORK: `/export` audit reports

---

## Commands Manual Structure in the Map

```
Commands Manual/
├── session/
│   ├── compact — context management per role + stage
│   ├── clear — between-task fresh start
│   ├── resume — continue interrupted work
│   ├── rewind — undo wrong approach
│   ├── branch — explore alternatives
│   └── export — archive/handoff
├── model/
│   ├── model — switch model for task complexity
│   ├── effort — set thinking depth
│   └── fast — speed toggle
├── context/
│   ├── context — visualize + optimize
│   ├── cost — token tracking
│   └── usage — rate limit awareness
├── git/
│   ├── diff — interactive diff review
│   ├── plan — read-only exploration
│   ├── pr-comments — review feedback
│   └── security-review — vulnerability scan
├── agents/
│   ├── agents — subagent management
│   ├── skills — discovery
│   └── tasks — background monitoring
└── workflow/
    ├── batch — parallel orchestration
    ├── debug — systematic troubleshooting
    ├── loop — scheduled checks
    └── simplify — quality pass
```

Each command node in the map includes:
- Which roles benefit most
- Which stages it's recommended in
- How it connects to fleet tools (e.g., `/diff` → fleet-ops review step 2)
- How it connects to skills (e.g., `/debug` → systematic-debugging from Superpowers)
- Injection guidance per context size

---

## How Commands Connect to Other Branches

| Command | Connects To |
|---------|------------|
| `/compact` | → Session Manager (brain Step 10), → CW-03 strategic compaction |
| `/plan` | → Methodology Manual (reasoning stage), → Superpowers writing-plans |
| `/debug` | → Superpowers systematic-debugging, → ops-incident skill |
| `/diff` | → Fleet-ops review protocol, → fleet-review skill step 2 |
| `/security-review` | → DevSecOps CLAUDE.md, → fleet-security-audit skill |
| `/batch` | → Agent Teams, → worktree management |
| `/cost` | → Budget system, → LaborStamp analytics |
| `/usage` | → Rate limit awareness (CW-07), → session_manager.py |
| `/context` | → Context strategy (CW-01 to CW-10) |
| `/loop` | → Heartbeat concept, → monitoring skills |
| `/simplify` | → Quality skills, → feature-review |
