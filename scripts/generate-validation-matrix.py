#!/usr/bin/env python3
"""Generate validation matrix — every state combination rendered for inspection.

Each scenario produces a separate file in validation-matrix/ that shows
EXACTLY what the agent sees. Line by line. No summarization.

Two primary modes:
  HEARTBEAT — agent wakes on CRON, processes queue
  TASK — agent dispatched to work on specific task

Each mode has multiple state axes:
  Stage: conversation, analysis, investigation, reasoning, work
  Contributions: none received, partial, all received
  Plane: connected, not connected
  Iteration: first attempt, rejection rework
  Injection: full, none
"""

import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from fleet.core.models import Task, TaskStatus, TaskCustomFields
from fleet.core.preembed import build_task_preembed, build_heartbeat_preembed
from fleet.core.tier_renderer import TierRenderer

EXPERT_RENDERER = TierRenderer("expert")

OUT_DIR = Path("validation-matrix")
if OUT_DIR.exists():
    shutil.rmtree(OUT_DIR)
OUT_DIR.mkdir()


def write_scenario(filename, title, content):
    path = OUT_DIR / filename
    with open(path, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(content)
    print(f"  {filename} ({len(content)} chars)")


def read_runtime(agent, filename):
    p = Path(f"agents/{agent}/{filename}")
    if p.exists():
        return p.read_text()
    p2 = Path(f"agents/_template/heartbeats/{agent}.md")
    if filename == "HEARTBEAT.md" and p2.exists():
        return p2.read_text()
    return f"[{filename} not found for {agent}]"


def make_task(**kwargs):
    defaults = dict(
        id="task-a1b2c3d4", board_id="b1",
        title="Add fleet health dashboard", status=TaskStatus.IN_PROGRESS,
        priority="high", description="Dashboard with agent grid, task pipeline, storm, budget",
        custom_fields=TaskCustomFields(
            agent_name="software-engineer", task_type="story", story_points=5,
            project="fleet",
        ),
    )
    defaults.update(kwargs)
    return Task(**defaults)


# Simulated contributions
ARCH_CONTRIB = """## CONTRIBUTION: design_input (from architect)

**Approach:** DashboardHealth component in fleet/ui/components/ using React.
- AgentGrid: 10 cards, color-coded by status
- TaskPipeline: horizontal bar chart (inbox/progress/review/done)
- StormIndicator: circular gauge with severity colors
- BudgetGauge: arc gauge with 5h and 7d usage

**Target files:** fleet/ui/components/DashboardHealth.tsx, fleet/ui/hooks/useFleetStatus.ts
**Patterns:** Observer (real-time), Adapter (API → component)
**Constraints:** Existing MC build pipeline. No new deps.

---"""

QA_CONTRIB = """## CONTRIBUTION: qa_test_definition (from qa-engineer)

TC-001: AgentGrid shows 10 agent cards | unit | required
TC-002: Agent card color matches status | unit | required
TC-003: TaskPipeline segments sum to total | unit | required
TC-004: StormIndicator correct severity color | unit | required
TC-005: BudgetGauge shows API percentage | integration | required
TC-006: Dashboard refreshes on status change | integration | recommended
TC-007: Keyboard navigation works | e2e | required

---"""

NAV_WORK = """## Stage: WORK — Resources Available

### Skills:
- /fleet-engineer-workflow — contribution consumption, TDD, conventional commits
- /fleet-completion-checklist — 8-point pre-completion check
- /test-driven-development (superpowers) — RED-GREEN-REFACTOR cycle
- /verification-before-completion (superpowers) — run tests before claiming done

### Sub-agents:
- **test-runner** (sonnet) — run pytest in isolated context
- **code-explorer** (sonnet) — trace execution paths

### MCP: fleet · filesystem · github · playwright
### Plugins: claude-mem · safety-net · context7 · superpowers · pyright-lsp
"""

NAV_REASONING = """## Stage: REASONING — Resources Available

### Skills:
- /fleet-implementation-planning — map plan to files and changes
- /writing-plans (superpowers) — detailed implementation roadmap
- /brainstorming (superpowers) — explore approaches

### Sub-agents:
- **code-explorer** (sonnet) — understand codebase before planning

### MCP: fleet · filesystem · github · context7
"""

NAV_CONVERSATION = """## Stage: CONVERSATION — Resources Available

### Skills:
- /fleet-communicate — which channel for what
- /brainstorming (superpowers) — explore problem space

### Sub-agents:
- **code-explorer** (sonnet) — reference codebase in questions

### MCP: fleet · filesystem
"""


print("=" * 60)
print("  Generating Validation Matrix")
print("=" * 60)
print()


# ═══════════════════════════════════════════════════════════
# HEARTBEAT MODE SCENARIOS
# ═══════════════════════════════════════════════════════════

print("HEARTBEAT MODE:")

# HB-01: Idle, no tasks
hb = build_heartbeat_preembed(
    agent_name="software-engineer", role="software-engineer",
    assigned_tasks=[], agents_online=8, agents_total=10,
    fleet_mode="full-autonomous", fleet_phase="execution", fleet_backend="claude",
    renderer=EXPERT_RENDERER,
)
write_scenario("HB-01-idle-no-tasks.md",
    "Heartbeat: Engineer idle, no tasks assigned",
    f"**Expected behavior:** Check messages, check standing orders, HEARTBEAT_OK.\n"
    f"**fleet_read_context:** NOT needed — data pre-embedded.\n\n"
    f"## fleet-context.md\n\n```\n{hb}\n```\n\n"
    f"## HEARTBEAT.md\n\n```\n{read_runtime('software-engineer', 'HEARTBEAT.md')}\n```\n"
)

# HB-02: Has in-progress task (work stage)
task_work = make_task(custom_fields=TaskCustomFields(
    task_stage="work", task_readiness=99, task_progress=40,
    requirement_verbatim="Add health dashboard with agent grid and budget gauge",
    agent_name="software-engineer", task_type="story", story_points=5,
    delivery_phase="mvp",
))
hb2 = build_heartbeat_preembed(
    agent_name="software-engineer", role="software-engineer",
    assigned_tasks=[task_work], agents_online=9, agents_total=10,
    fleet_mode="full-autonomous", fleet_phase="execution", fleet_backend="claude",
    role_data={"my_tasks_count": 1, "contribution_tasks": [],
        "contributions_received": [
            {"type": "design_input", "from": "architect", "status": "done"},
            {"type": "qa_test_definition", "from": "qa-engineer", "status": "done"},
        ], "in_review": []},
    renderer=EXPERT_RENDERER,
)
write_scenario("HB-02-has-work-task.md",
    "Heartbeat: Engineer has in-progress task (work stage)",
    f"**Expected behavior:** See task in assigned, continue work, follow HEARTBEAT.md §2.\n"
    f"**fleet_read_context:** NOT needed — task visible in pre-embed.\n\n"
    f"## fleet-context.md\n\n```\n{hb2}\n```\n\n"
    f"## HEARTBEAT.md\n\n```\n{read_runtime('software-engineer', 'HEARTBEAT.md')}\n```\n"
)

# HB-03: Has messages (PM assigned work)
hb3 = build_heartbeat_preembed(
    agent_name="software-engineer", role="software-engineer",
    assigned_tasks=[], agents_online=9, agents_total=10,
    fleet_mode="full-autonomous", fleet_phase="execution", fleet_backend="claude",
    messages=[
        {"from": "project-manager", "content": "Assigned you task-xyz: Implement fleet controls sidebar. Story points: 3. Stage: reasoning."},
    ],
    renderer=EXPERT_RENDERER,
)
write_scenario("HB-03-has-messages.md",
    "Heartbeat: Engineer has message from PM (new assignment)",
    f"**Expected behavior:** Read message, acknowledge assignment.\n\n"
    f"## fleet-context.md\n\n```\n{hb3}\n```\n"
)

# HB-04: Fleet-ops with pending reviews
hb4 = build_heartbeat_preembed(
    agent_name="fleet-ops", role="fleet-ops",
    assigned_tasks=[], agents_online=10, agents_total=10,
    fleet_mode="full-autonomous", fleet_phase="execution", fleet_backend="claude",
    role_data={
        "pending_approvals": 2,
        "approval_details": [
            {"id": "appr-001", "task_id": "task-abc1", "status": "pending"},
            {"id": "appr-002", "task_id": "task-def2", "status": "pending"},
        ],
        "review_queue": [
            {"id": "task-abc1", "title": "Add fleet health dashboard", "agent": "software-engineer"},
            {"id": "task-def2", "title": "Fix orchestrator stage bug", "agent": "devops"},
        ],
        "offline_agents": ["ux-designer"],
    },
    renderer=EXPERT_RENDERER,
)
write_scenario("HB-04-fleet-ops-reviews.md",
    "Heartbeat: Fleet-ops with 2 pending reviews",
    f"**Expected behavior:** Process each review using ops_real_review(). 7-step protocol.\n\n"
    f"## fleet-context.md\n\n```\n{hb4}\n```\n\n"
    f"## HEARTBEAT.md\n\n```\n{read_runtime('fleet-ops', 'HEARTBEAT.md')}\n```\n"
)

# HB-05: PM with unassigned tasks
hb5 = build_heartbeat_preembed(
    agent_name="project-manager", role="project-manager",
    assigned_tasks=[], agents_online=9, agents_total=10,
    fleet_mode="full-autonomous", fleet_phase="execution", fleet_backend="claude",
    role_data={
        "unassigned_tasks": 3,
        "unassigned_details": [
            {"id": "task-un1", "title": "Investigate memory leak in orchestrator", "priority": "high"},
            {"id": "task-un2", "title": "Add changelog generation to writer CRON", "priority": "medium"},
            {"id": "task-un3", "title": "Update fleet-identity config for beta", "priority": "low"},
        ],
        "blocked_tasks": 1,
        "progress": "12/25 done (48%)",
        "inbox_count": 5,
    },
    renderer=EXPERT_RENDERER,
)
write_scenario("HB-05-pm-unassigned.md",
    "Heartbeat: PM with 3 unassigned inbox tasks + 1 blocker",
    f"**Expected behavior:** Triage each task with ALL fields. Assign agents.\n\n"
    f"## fleet-context.md\n\n```\n{hb5}\n```\n\n"
    f"## HEARTBEAT.md\n\n```\n{read_runtime('project-manager', 'HEARTBEAT.md')}\n```\n"
)


print()
print("TASK MODE:")

# ═══════════════════════════════════════════════════════════
# TASK MODE SCENARIOS
# ═══════════════════════════════════════════════════════════

def render_task_scenario(filename, title, task, injection="full",
                         contribs="", nav="", notes="",
                         renderer=None, rejection_feedback="", target_task=None,
                         confirmed_plan=""):
    r = renderer or EXPERT_RENDERER
    base = build_task_preembed(task, injection_level=injection,
                                renderer=r, rejection_feedback=rejection_feedback,
                                target_task=target_task, confirmed_plan=confirmed_plan)
    if contribs:
        # Insert contribution content at the marker and update checklist
        insert_marker = "<!-- CONTRIBUTIONS_ABOVE -->"
        if insert_marker in base:
            base = base.replace(insert_marker, f"\n{contribs}\n", 1)
        # Mark delivered types as received in checklist
        import re
        for ctype_match in re.findall(r'## CONTRIBUTION:\s*(\S+)', contribs):
            base = base.replace(
                f"**{ctype_match}** from",
                f"**{ctype_match}** ✓ from",
            )
            # Only replace awaiting on the specific line
            lines_list = base.split("\n")
            for i, line in enumerate(lines_list):
                if f"**{ctype_match}**" in line and "awaiting delivery" in line:
                    lines_list[i] = line.replace("— *awaiting delivery*", "— *received*")
            base = "\n".join(lines_list)
    parts = [
        f"**Expected:** {notes}\n",
        f"## task-context.md\n\n```\n{base}\n```\n",
    ]
    if nav:
        parts.append(f"## knowledge-context.md\n\n```\n{nav}\n```\n")
    write_scenario(filename, title, "\n".join(parts))


# TK-01: Work stage, full injection, all contributions received
render_task_scenario("TK-01-work-full-contrib.md",
    "Task: Work stage, full injection, contributions received",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99, task_progress=40,
        requirement_verbatim="Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge",
        agent_name="software-engineer", task_type="story", story_points=5,
        delivery_phase="mvp", parent_task="epic-fleet-ui-001",
    )),
    contribs=ARCH_CONTRIB + "\n" + QA_CONTRIB,
    nav=NAV_WORK,
    notes="Engineer has everything. Follow plan, commit, complete. fleet_read_context NOT needed.",
    confirmed_plan="1. Create DashboardHealth.tsx component\n2. Implement AgentGrid (10 cards, color-coded)\n3. Implement TaskPipeline (horizontal bar chart)\n4. Implement StormIndicator (circular gauge)\n5. Implement BudgetGauge (arc gauge)\n6. Wire useFleetStatus.ts hook\n7. Tests for TC-001 through TC-007",
)

# TK-02: Work stage, full injection, NO contributions (missing)
render_task_scenario("TK-02-work-no-contrib.md",
    "Task: Work stage, full injection, contributions MISSING",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99, task_progress=0,
        requirement_verbatim="Add health dashboard with agent grid",
        agent_name="software-engineer", task_type="story", story_points=5,
        delivery_phase="mvp",
    )),
    nav=NAV_WORK,
    notes="Contributions required but NOT received. Should see 'fleet_request_input()' directive. Should NOT proceed.",
)

# TK-03: Reasoning stage
render_task_scenario("TK-03-reasoning.md",
    "Task: Reasoning stage — produce plan, NOT implement",
    make_task(custom_fields=TaskCustomFields(
        task_stage="reasoning", task_readiness=85, task_progress=0,
        requirement_verbatim="Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge",
        agent_name="software-engineer", task_type="story", story_points=5,
    )),
    nav=NAV_REASONING,
    notes="PLAN only. NO code. NO commits. Reference verbatim. fleet_commit should NOT appear in recommended actions.",
)

# TK-04: Conversation stage
render_task_scenario("TK-04-conversation.md",
    "Task: Conversation stage — clarify requirements, NO code",
    make_task(custom_fields=TaskCustomFields(
        task_stage="conversation", task_readiness=10, task_progress=0,
        requirement_verbatim="We need a dashboard but details unclear",
        agent_name="software-engineer", task_type="story",
    )),
    nav=NAV_CONVERSATION,
    notes="CLARIFY only. NO code, NO solutions, NO designs. Ask questions.",
)

# TK-05: No injection (direct CLI dispatch)
render_task_scenario("TK-05-no-injection.md",
    "Task: Work stage, NO injection (direct CLI)",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99,
        requirement_verbatim="Add health dashboard",
        agent_name="software-engineer", task_type="task",
    )),
    injection="none",
    notes="NO pre-embedded data. Must call fleet_read_context() FIRST.",
)

# TK-06: Rejection rework (iteration 2)
render_task_scenario("TK-06-rejection-rework.md",
    "Task: Work stage, rejection rework (iteration 2)",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99, task_progress=0,
        requirement_verbatim="Add health dashboard with agent grid",
        agent_name="software-engineer", task_type="story", story_points=5,
        delivery_phase="mvp", labor_iteration=2,
    )),
    contribs=ARCH_CONTRIB + "\n" + QA_CONTRIB,
    nav=NAV_WORK,
    notes="Second attempt after rejection. Should show iteration 2, rejection feedback, eng_fix_task_response().",
    rejection_feedback="REJECTED by fleet-ops: Missing test for TC-003 (TaskPipeline segments). Add integration test verifying segment sum equals total count.",
)

# TK-07: Architect contribution task
TARGET_TASK = Task(id="task-a1b2c3d4", board_id="b1",
    title="Add fleet health dashboard to MC frontend",
    status=TaskStatus.IN_PROGRESS, priority="high",
    description="Dashboard with agent grid, task pipeline, storm, budget",
    custom_fields=TaskCustomFields(
        requirement_verbatim="Add a health dashboard showing: agent grid (online/idle/sleeping/offline), task pipeline (inbox/progress/review/done counts), storm indicator with severity color, budget gauge with percentage",
        delivery_phase="mvp", task_stage="work", task_readiness=99,
        agent_name="software-engineer",
    ))

render_task_scenario("TK-07-architect-contribution.md",
    "Task: Architect producing design_input contribution",
    Task(id="task-contrib99", board_id="b1",
        title="Contribute design_input for: fleet health dashboard",
        status=TaskStatus.IN_PROGRESS, priority="medium",
        custom_fields=TaskCustomFields(
            task_stage="analysis", task_readiness=50,
            requirement_verbatim="Provide design_input: approach, target files, patterns for the fleet health dashboard",
            agent_name="architect", task_type="subtask",
            contribution_type="design_input", contribution_target="task-a1b2c3d4",
        )),
    notes="Architect examining codebase for design. Should show CONTRIBUTION TASK section with target task verbatim, fleet_contribute() reference.",
    target_task=TARGET_TASK,
)

# TK-08: QA predefinition contribution
render_task_scenario("TK-08-qa-predefinition.md",
    "Task: QA predefining test criteria (TC-XXX)",
    Task(id="task-qa-predef", board_id="b1",
        title="Contribute qa_test_definition for: fleet health dashboard",
        status=TaskStatus.IN_PROGRESS, priority="medium",
        custom_fields=TaskCustomFields(
            task_stage="reasoning", task_readiness=80,
            requirement_verbatim="Define structured TC-XXX test criteria for the fleet health dashboard story",
            agent_name="qa-engineer", task_type="subtask",
            contribution_type="qa_test_definition", contribution_target="task-a1b2c3d4",
        )),
    notes="QA producing TC-XXX criteria. Phase-appropriate (MVP = main flows + critical edges).",
)

# TK-09: With Plane connected (delivery phase mvp)
render_task_scenario("TK-09-with-plane-mvp.md",
    "Task: Work stage with Plane connected, MVP phase",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99, task_progress=60,
        requirement_verbatim="Add health dashboard with agent grid",
        agent_name="software-engineer", task_type="story", story_points=5,
        delivery_phase="mvp", phase_progression="standard",
        plane_issue_id="issue-abc123", plane_project_id="proj-fleet",
    )),
    contribs=ARCH_CONTRIB + "\n" + QA_CONTRIB,
    nav=NAV_WORK,
    notes="Plane connected — issue linked. MVP phase standards visible. fleet_task_complete will sync to Plane.",
)

# TK-10: Nearly complete (progress 70%)
render_task_scenario("TK-10-nearly-complete.md",
    "Task: Work stage, nearly complete (progress 70%)",
    make_task(custom_fields=TaskCustomFields(
        task_stage="work", task_readiness=99, task_progress=70,
        requirement_verbatim="Add health dashboard with agent grid",
        agent_name="software-engineer", task_type="story", story_points=5,
        delivery_phase="mvp",
    )),
    contribs=ARCH_CONTRIB + "\n" + QA_CONTRIB,
    nav=NAV_WORK,
    notes="Progress 70% = implementation done. Should run tests, then fleet_task_complete.",
)

# TK-34: Engineer role-specific reasoning
render_task_scenario("TK-34-engineer-reasoning.md",
    "Task: Engineer reasoning — role-specific protocol",
    make_task(custom_fields=TaskCustomFields(
        task_stage="reasoning", task_readiness=85,
        requirement_verbatim="Add health dashboard with agent grid, task pipeline, storm indicator, budget gauge",
        agent_name="software-engineer", task_type="story", story_points=5,
    )),
    nav=NAV_REASONING,
    notes="Engineer reasoning should say 'implementation plan'. Compare: architect would say 'design_input'.",
)


print()
print("=" * 60)
total = len(list(OUT_DIR.glob("*.md")))
print(f"  Generated {total} scenario files in validation-matrix/")
print(f"  Inspect each file to verify line-by-line correctness.")
print("=" * 60)
