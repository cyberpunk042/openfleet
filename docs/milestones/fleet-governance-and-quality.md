# Fleet Governance, Quality, and Communication Architecture

## Requirements (from user, verbatim scope)

Every single one of these is a requirement, not a nice-to-have.

---

### 1. PR Quality and Changelog

**Current state:** PRs have a basic template with task ID, agent, and diff stat. No changelog. No visual appeal. No markdown exploitation. Bare minimum.

**Required:**
- Every PR includes a **changelog section** in the body
- Changelog follows conventional commit grouping (Features, Fixes, Docs, etc.)
- Visually appealing markdown: headers, code blocks, tables, emoji where appropriate
- Diff summary with file-by-file descriptions, not just `git diff --stat`
- Links to: MC task URL, agent session, related PRs, related issues
- Before/after comparison where relevant
- Test results summary if tests were run

**Milestones:**
- M81: PR template skill — agents use a rich PR template
- M82: Changelog in PR body — generated from branch commits
- M83: PR quality gate — review PR body before creating, reject if substandard

---

### 2. Cross-Referencing Everywhere

**Current state:** Task IDs in commit messages. PR URLs in task comments. That's it. No links between MC tasks, no links to specific files, no links in IRC messages.

**Required:**
- Every MC task comment includes clickable URLs to: PR, branch compare, changed files on GitHub
- Every IRC message includes clickable URLs
- Every commit message references the task
- Every PR references the task with MC URL
- Board memory entries reference related tasks, PRs, agents
- Agent reports include GitHub file links (not just file paths)
- Task descriptions reference parent tasks, blocking tasks, related tasks
- Cross-project references: NNRT task links to fleet task that spawned it

**URL templates needed:**
- MC task: `http://localhost:3000/boards/{board_id}/tasks/{task_id}`
- GitHub PR: `https://github.com/{owner}/{repo}/pull/{number}`
- GitHub file: `https://github.com/{owner}/{repo}/blob/{branch}/{path}`
- GitHub compare: `https://github.com/{owner}/{repo}/compare/main...{branch}`
- GitHub commit: `https://github.com/{owner}/{repo}/commit/{sha}`

**Milestones:**
- M84: URL template library (config file with project→repo mapping + URL builders)
- M85: Agent markdown skill — proper markdown with links, tables, code blocks
- M86: MC task comment formatter — structured comments with all references

---

### 3. Agent Communication Protocol

**Current state:** Agents post to MC task comments when they complete. Board memory is nearly empty. No agent-to-agent communication. No proactive alerts.

**Required:**
- Agents use board memory for **cross-task communication**:
  - "I found a security issue in X" → tags: [alert, security, project:nnrt]
  - "I suggest we add a Y agent" → tags: [suggestion, fleet]
  - "I'm blocked on Z, need @architect input" → tags: [blocked, chat]
  - "This task should be split into A, B, C" → tags: [planning]
- Agents create follow-up tasks for themselves or other agents
- Agents can pause work and explain why
- Agents warn about:
  - Missing skills or knowledge
  - Security concerns (CVEs, exposed secrets, vulnerable deps)
  - Quality concerns (low test coverage, missing docs, code smells)
  - Architecture concerns (coupling, scaling issues, design debt)
  - Improvement suggestions (better tools, missing automation)
- Lead agent coordinates multi-agent work:
  - Assigns tasks from backlog
  - Prioritizes based on board state
  - Escalates blocked tasks to human

**Milestones:**
- M87: Agent communication skill — when/how to use board memory, IRC, task comments
- M88: Follow-up task creation skill — agents create tasks for other agents
- M89: Alert/warning skill — proactive alerts for security, quality, architecture
- M90: Lead agent configuration and coordination protocol

---

### 4. IRC as First-Class Surface with The Lounge

**Current state:** miniircd running, fleet-bot connected, notifications sent on dispatch/merge. Human needs a CLI IRC client.

**Required:**
- **The Lounge** (thelounge.chat) as the web IRC client — no need for CLI irssi/weechat
- Auto-installed and configured in setup.sh
- Accessible at `http://localhost:9000` (or similar)
- Pre-configured to connect to the local IRC server and join #fleet
- Agents post structured messages to #fleet with full URLs
- Human can respond in IRC and agents see the messages
- Dedicated channels possible: #fleet (general), #alerts (security/blockers), #reviews (PRs)
- IRC history backed up / searchable
- Agent responsible for IRC operations and backup

**Milestones:**
- M91: Install The Lounge in setup.sh (Docker or npm)
- M92: Configure The Lounge to auto-connect to fleet IRC
- M93: Agent IRC messaging format standard (structured, with URLs)
- M94: Multiple IRC channels (#fleet, #alerts, #reviews)
- M95: IRC operations agent (backup, history, channel management)

---

### 5. Governance Agent

**Current state:** No governance. No coordination. No quality enforcement beyond standards doc.

**Required:**
- A dedicated agent (or lead agent role) that:
  - Monitors board state and task flow
  - Enforces standards (commit format, PR quality, comment structure)
  - Manages IRC channels and backup
  - Creates operational reports (daily digest, weekly summary)
  - Identifies gaps: missing agents, missing skills, missing automation
  - Escalates to human when needed
  - Manages agent lifecycle (suggest new agents, retire unused ones)
  - Enforces governance rules:
    - No task sits in inbox > 1 hour without assignment
    - No task sits in review > 24 hours without review
    - No PR without changelog
    - No commit without task reference
    - No agent work without MC reporting

**Milestones:**
- M96: Governance agent definition (SOUL.md, capabilities, skills)
- M97: Board state monitoring skill (detect stale tasks, unreviewed PRs)
- M98: Daily digest skill (summary of fleet activity to IRC + board memory)
- M99: Quality enforcement skill (check PR bodies, commit messages, comment structure)
- M100: Gap detection skill (missing skills, agents, automation, docs)

---

### 6. Markdown Mastery

**Current state:** Agents write functional but visually plain markdown. No exploitation of formatting.

**Required:**
- Agents produce **publication-quality markdown** in:
  - PR descriptions
  - Task comments
  - Board memory entries
  - IRC messages (where supported)
  - Documentation
  - Reports
- Proper use of: headers, tables, code blocks, checklists, blockquotes, badges, diff blocks
- Consistent formatting across all agents
- Template library for common formats (PR, report, alert, changelog)

**Milestones:**
- M101: Markdown template library (PR, report, alert, changelog, review)
- M102: Install Anthropic's markdown/document skills from marketplace
- M103: Agent markdown quality gate in governance rules

---

### 7. Logic for When to Use What

**Current state:** MC_WORKFLOW.md has basic rules. No decision tree for which surface to use when.

**Required:**
- Clear decision matrix:

| Situation | Surface | Format |
|-----------|---------|--------|
| Task progress | MC task comment | Structured update |
| Task completion | MC task comment + IRC + board memory | Full report with PR link |
| Cross-task knowledge | Board memory | Tagged knowledge entry |
| Security alert | IRC #alerts + board memory | Alert format with severity |
| Blocker | MC task comment + IRC #fleet | Blocker format |
| Suggestion | Board memory | Suggestion format |
| Follow-up task | MC task creation API | New task with depends_on |
| Human needs attention | IRC #fleet + board memory | @human mention |
| Agent-to-agent | Board memory | @agent mention |
| Architecture decision | Board memory | Decision record format |

**Milestones:**
- M104: Communication decision matrix in STANDARDS.md
- M105: Surface routing skill — agents know which surface to use when

---

## Summary: 25 Milestones (M81–M105)

| Phase | Milestones | Focus |
|-------|-----------|-------|
| PR Quality | M81–M83 | Rich PRs, changelogs, quality gates |
| Cross-References | M84–M86 | URL templates, markdown, formatters |
| Agent Communication | M87–M90 | Board memory protocol, follow-ups, alerts, lead agent |
| IRC + The Lounge | M91–M95 | Web client, format standard, channels, ops agent |
| Governance | M96–M100 | Governance agent, monitoring, digests, enforcement |
| Markdown | M101–M103 | Templates, skills, quality gates |
| Communication Logic | M104–M105 | Decision matrix, routing skill |

This is not a weekend project. This is the fleet's operating system maturation.
Each milestone is a discrete unit of work that can be planned, built, tested, and shipped.

---

## Execution Priority

1. **M84 + M101** (URL templates + markdown templates) — foundation for everything else
2. **M81 + M82** (PR template + changelog) — immediate quality improvement
3. **M87 + M104** (agent communication skill + decision matrix) — agents start using the system properly
4. **M91 + M92** (The Lounge setup) — human gets a proper IRC interface
5. **M96** (governance agent) — someone keeps order
6. Everything else builds on these foundations