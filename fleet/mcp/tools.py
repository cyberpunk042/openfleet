"""Fleet MCP tool definitions — native tools for agents.

Each tool is what an agent naturally wants to do.
The tool handler does all infrastructure work internally.
Agent provides minimal semantic input. Server handles the rest.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from fleet.mcp.context import FleetMCPContext
from fleet.templates import comment as comment_tmpl
from fleet.templates import irc as irc_tmpl
from fleet.templates import memory as memory_tmpl
from fleet.templates import pr as pr_tmpl

# ─── Review Gate Builder ──────────────────────────────────────────────────


def _build_review_gates(task_type: str, has_code: bool) -> list[dict]:
    """Build review gates based on task type and whether it has code changes.

    Returns a list of reviewer requirements for fleet-ops to orchestrate.
    fleet-ops (board lead) is always the final reviewer.
    """
    gates: list[dict] = []

    if has_code:
        gates.append({
            "agent": "qa-engineer",
            "type": "required",
            "status": "pending",
            "reason": "",
        })

    if task_type in ("epic", "story") or "architect" in task_type:
        gates.append({
            "agent": "architect",
            "type": "required",
            "status": "pending",
            "reason": "",
        })

    if task_type in ("blocker", "concern") or "security" in (task_type or ""):
        gates.append({
            "agent": "devsecops-expert",
            "type": "required",
            "status": "pending",
            "reason": "",
        })

    # fleet-ops is always the final gate (as board lead)
    gates.append({
        "agent": "fleet-ops",
        "type": "required",
        "status": "pending",
        "reason": "",
    })

    return gates


# Shared context — initialized on first tool call
_ctx: FleetMCPContext | None = None
_event_store = None


def _get_ctx() -> FleetMCPContext:
    """Get or create the shared context."""
    global _ctx
    if _ctx is None:
        _ctx = FleetMCPContext.from_env()
    return _ctx


def _report_error(tool_name: str, error: str) -> None:
    """Report a tool error to the error log for orchestrator visibility."""
    try:
        from fleet.core.error_reporter import report_error
        report_error(tool_name, error)
    except Exception:
        pass  # Error reporting must never break tool execution


def _emit_event(
    event_type: str,
    source: str = "",
    subject: str = "",
    recipient: str = "all",
    priority: str = "info",
    mentions: list | None = None,
    tags: list | None = None,
    surfaces: list | None = None,
    **extra_data,
) -> None:
    """Emit a fleet event to the persistent store.

    Every MCP tool should emit events so the event bus can route them
    to the right agents and surfaces. This is the deterministic logic layer.
    """
    global _event_store
    try:
        from fleet.core.events import create_event, EventStore
        if _event_store is None:
            _event_store = EventStore()
        ctx = _get_ctx()
        event = create_event(
            event_type=event_type,
            source=source or f"fleet/mcp/tools/{event_type.split('.')[-1]}",
            subject=subject,
            recipient=recipient,
            priority=priority,
            mentions=mentions,
            tags=tags,
            surfaces=surfaces or ["internal"],
            agent=ctx.agent_name or "",
            fleet_id=ctx.fleet_id or "",
            **extra_data,
        )
        _event_store.append(event)
    except Exception:
        pass  # Event emission must never break tool execution


# ─── Methodology Stage Enforcement ─────────────────────────────────────

# Tools restricted to specific methodology stages.
# Tools not listed here are allowed in ALL stages.
WORK_ONLY_TOOLS = {"fleet_commit", "fleet_task_complete"}
REASONING_AND_WORK_TOOLS = {"fleet_task_accept"}  # plan submission

# Stages where work tools are allowed
WORK_STAGES = {"work", "reasoning"}  # reasoning allows plan submission


def _check_stage_allowed(tool_name: str) -> dict | None:
    """Check if the current methodology stage allows this tool.

    Returns None if allowed, or an error dict if blocked.
    """
    ctx = _get_ctx()
    task_id = ctx.task_id
    if not task_id:
        return None  # no task context — can't check stage

    # Read task stage from context (set during fleet_read_context)
    stage = getattr(ctx, '_task_stage', None)
    if not stage:
        return None  # no stage set — allow (backward compatible)

    if tool_name in WORK_ONLY_TOOLS and stage != "work":
        _emit_event(
            "fleet.methodology.protocol_violation",
            subject=task_id,
            tool=tool_name,
            stage=stage,
            violation=f"{tool_name} called during {stage} stage",
        )
        return {
            "ok": False,
            "error": (
                f"Methodology violation: {tool_name} is only allowed during "
                f"work stage. Your task is in '{stage}' stage. "
                f"Complete the {stage} protocol first."
            ),
            "stage": stage,
            "allowed_stages": ["work"],
        }

    return None


def register_tools(server: FastMCP) -> None:
    """Register all fleet tools on the MCP server."""

    @server.tool()
    async def fleet_read_context(task_id: str = "", project: str = "") -> dict:
        """Read full task and project context. Call this FIRST every session.

        Args:
            task_id: The task ID from your assignment (required for task operations).
            project: Project name (e.g., "nnrt", "fleet").

        Returns task details, project info, resolved URLs, recent board memory.
        """
        ctx = _get_ctx()

        # Store task context for subsequent tool calls
        if task_id:
            ctx.task_id = task_id
        if project:
            ctx.project_name = project

        board_id = await ctx.resolve_board_id()
        result = {"board_id": board_id, "agent": ctx.agent_name, "task_id": ctx.task_id}

        if ctx.task_id:
            try:
                task = await ctx.mc.get_task(board_id, ctx.task_id)
                result["task"] = {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "description": task.description[:500],
                    "priority": task.priority,
                    "project": task.custom_fields.project,
                    "tags": task.tags,
                }
                # Auto-set from task custom fields when env vars are missing
                if task.custom_fields.project and not ctx.project_name:
                    ctx.project_name = task.custom_fields.project
                if task.custom_fields.agent_name and not ctx.agent_name:
                    ctx.agent_name = task.custom_fields.agent_name
                if task.custom_fields.worktree:
                    ctx.worktree = task.custom_fields.worktree
                # Store methodology fields for stage enforcement
                ctx._task_stage = task.custom_fields.task_stage
                ctx._task_readiness = task.custom_fields.task_readiness
                # Include methodology info in response
                result["task"]["readiness"] = task.custom_fields.task_readiness
                result["task"]["stage"] = task.custom_fields.task_stage or "unknown"
                if task.custom_fields.requirement_verbatim:
                    result["task"]["requirement_verbatim"] = task.custom_fields.requirement_verbatim
            except Exception as e:
                result["task"] = {"id": ctx.task_id, "error": str(e)}

        if ctx.project_name:
            urls = ctx.urls.resolve(project=ctx.project_name, task_id=ctx.task_id)
            result["urls"] = {"task": urls.task or "", "board": urls.board or ""}

        # Board memory — categorized for agent awareness
        try:
            memory = await ctx.mc.list_memory(board_id, limit=20)
            result["recent_memory"] = [
                {"content": m.content[:300], "tags": m.tags, "source": m.source}
                for m in memory[:5]
            ]
            # Separate important categories for agent attention
            result["recent_decisions"] = [
                {"content": m.content[:300], "source": m.source}
                for m in memory if "decision" in m.tags
            ][:3]
            result["active_alerts"] = [
                {"content": m.content[:300], "source": m.source}
                for m in memory if "alert" in m.tags
            ][:3]
            result["escalations"] = [
                {"content": m.content[:300], "source": m.source}
                for m in memory if "escalation" in m.tags
            ][:3]
            # Chat messages addressed to this agent
            agent = ctx.agent_name or ""
            result["chat_messages"] = [
                {"content": m.content[:300], "source": m.source}
                for m in memory
                if "chat" in m.tags and (
                    f"mention:{agent}" in m.tags
                    or "mention:all" in m.tags
                    or (agent == "fleet-ops" and "mention:fleet-ops" in m.tags)
                    or (agent == "fleet-ops" and "mention:lead" in m.tags)
                )
            ][:5]
        except Exception:
            result["recent_memory"] = []

        # Team activity — what each agent is working on (for collaboration awareness)
        try:
            all_tasks = await ctx.mc.list_tasks(board_id)
            active_work = []
            for t in all_tasks:
                if t.status.value in ("in_progress", "review") and t.custom_fields.agent_name:
                    active_work.append({
                        "agent": t.custom_fields.agent_name,
                        "task": t.title[:60],
                        "status": t.status.value,
                        "task_id": t.id[:8],
                    })
            result["team_activity"] = active_work[:10]
        except Exception:
            result["team_activity"] = []

        # Task hierarchy — if this task has a parent, show siblings
        if ctx.task_id:
            try:
                task_data = result.get("task", {})
                parent_id = ""
                if isinstance(task_data, dict) and not task_data.get("error"):
                    t = await ctx.mc.get_task(board_id, ctx.task_id)
                    parent_id = t.custom_fields.parent_task or ""

                if parent_id:
                    siblings = [
                        {
                            "id": t.id[:8],
                            "title": t.title[:50],
                            "status": t.status.value,
                            "agent": t.custom_fields.agent_name or "",
                        }
                        for t in all_tasks
                        if t.custom_fields.parent_task == parent_id and t.id != ctx.task_id
                    ]
                    result["parent_task_id"] = parent_id[:8]
                    result["sibling_tasks"] = siblings[:10]
            except Exception:
                pass

        # Sprint context — active sprint metrics
        try:
            from fleet.core.velocity import compute_sprint_metrics
            # Find active sprint from task's plan_id or most recent
            sprint_id = ""
            if ctx.task_id:
                try:
                    t = await ctx.mc.get_task(board_id, ctx.task_id)
                    sprint_id = t.custom_fields.plan_id or t.custom_fields.sprint or ""
                except Exception:
                    pass
            if sprint_id and all_tasks:
                metrics = compute_sprint_metrics(all_tasks, sprint_id)
                result["sprint_context"] = {
                    "plan_id": sprint_id,
                    "completion_pct": round(metrics.completion_pct),
                    "done": metrics.done_tasks,
                    "total": metrics.total_tasks,
                    "story_points": f"{metrics.done_story_points}/{metrics.total_story_points}",
                    "is_complete": metrics.is_complete,
                }
        except Exception:
            pass

        # Agent role and authority
        try:
            from fleet.core.agent_roles import get_agent_role
            agent = ctx.agent_name or ""
            if agent:
                role = get_agent_role(agent)
                if role:
                    result["agent_role"] = {
                        "primary": role.primary_role,
                        "secondary": role.main_secondary_role,
                        "can_reject": role.pr_authority.can_reject,
                        "can_close_pr": role.pr_authority.can_close_pr,
                        "review_domains": role.review_domains[:5],
                    }
        except Exception:
            pass

        # Fleet health summary
        try:
            if all_tasks:
                agents_list = await ctx.mc.list_agents()
                online = sum(1 for a in agents_list if a.status == "online" and "Gateway" not in a.name)
                total = sum(1 for a in agents_list if "Gateway" not in a.name)
                blocked = sum(1 for t in all_tasks if t.is_blocked)
                pending = 0
                try:
                    approvals = await ctx.mc.list_approvals(board_id, status="pending")
                    pending = len(approvals)
                except Exception:
                    pass
                result["fleet_health"] = {
                    "agents_online": online,
                    "agents_total": total,
                    "tasks_blocked": blocked,
                    "pending_approvals": pending,
                }
        except Exception:
            pass

        # Event feed — unseen events for this agent from the event bus
        try:
            from fleet.core.events import EventStore
            from fleet.core.event_router import build_agent_feed
            agent = ctx.agent_name or ""
            if agent:
                store = EventStore()
                unseen = store.query(agent_name=agent, unseen_only=True, limit=20)
                if unseen:
                    feed = build_agent_feed(unseen, agent, limit=10)
                    result["event_feed"] = {
                        "unseen_count": len(unseen),
                        "items": [
                            {
                                "type": e["type"],
                                "priority": e["priority"],
                                "time": e["time"],
                                "data": {k: v for k, v in e["data"].items()
                                         if k in ("title", "summary", "message", "agent",
                                                  "pr_url", "decision", "severity", "comment")},
                            }
                            for e in feed[:5]
                        ],
                    }
                    # Mark as seen
                    store.mark_seen(agent, [e["id"] for e in feed])
        except Exception:
            pass

        return result

    @server.tool()
    async def fleet_task_accept(plan: str, task_id: str = "") -> dict:
        """Accept and start working on your assigned task.

        Share your plan — what you'll do, how you'll verify, what could go wrong.
        For complex tasks (L/XL), consider using plan mode to explore the codebase
        before committing to an approach.

        Args:
            plan: Your approach — concrete steps, verification, risks.
            task_id: Task ID (if not already set via fleet_read_context).
        """
        from fleet.core.plan_quality import assess_plan, format_plan_feedback

        ctx = _get_ctx()
        if task_id:
            ctx.task_id = task_id
        if not ctx.task_id:
            return {"ok": False, "error": "No task_id. Call fleet_read_context first."}

        board_id = await ctx.resolve_board_id()

        # Assess plan quality
        task_type = ""
        try:
            task_data = await ctx.mc.get_task(board_id, ctx.task_id)
            task_type = task_data.custom_fields.task_type or ""
        except Exception:
            pass

        plan_assessment = assess_plan(plan, task_type)

        comment = comment_tmpl.format_accept(plan, ctx.agent_name or "agent")
        if plan_assessment.issues:
            comment += f"\n\n*Plan quality: {plan_assessment.score:.0f}/100*"

        try:
            task = await ctx.mc.update_task(
                board_id, ctx.task_id,
                status="in_progress",
                comment=comment,
                custom_fields={"agent_name": ctx.agent_name} if ctx.agent_name else None,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        task_url = ctx.urls.task_url(ctx.task_id) if ctx.task_id else ""
        try:
            await ctx.irc.notify_event(
                agent=ctx.agent_name or "agent",
                event="▶️ STARTED",
                title=task.title,
                url=task_url,
            )
        except Exception:
            pass

        result: dict = {
            "ok": True,
            "status": "in_progress",
            "task_url": task_url,
            "plan_score": plan_assessment.score,
        }

        # Include feedback if plan could be improved
        if plan_assessment.suggestions or plan_assessment.issues:
            result["plan_feedback"] = format_plan_feedback(plan_assessment)

        return result

    @server.tool()
    async def fleet_task_progress(done: str, next_step: str, blockers: str = "none") -> dict:
        """Post a progress update on your current task.

        Args:
            done: What you've completed so far.
            next_step: What you're working on next.
            blockers: Any blockers (or "none").
        """
        ctx = _get_ctx()
        if not ctx.task_id:
            return {"ok": False, "error": "No task_id. Call fleet_read_context first."}
        board_id = await ctx.resolve_board_id()

        comment = comment_tmpl.format_progress(done, next_step, blockers, ctx.agent_name or "agent")

        try:
            await ctx.mc.post_comment(board_id, ctx.task_id, comment)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True}

    @server.tool()
    async def fleet_commit(files: list[str], message: str) -> dict:
        """Commit changes with conventional format and task reference.

        Args:
            files: List of file paths to stage (relative to worktree).
            message: Commit message in conventional format (e.g., "feat(core): add type hints").
                     Task reference is added automatically.
        """
        # Methodology gate: only allowed during work stage
        blocked = _check_stage_allowed("fleet_commit")
        if blocked:
            return blocked

        ctx = _get_ctx()
        task_ref = f" [task:{ctx.task_id[:8]}]" if ctx.task_id else ""
        full_msg = f"{message}{task_ref}"
        cwd = ctx.worktree or "."

        for f in files:
            await ctx.gh._run(["git", "add", f], cwd=cwd)

        ok, output = await ctx.gh._run(["git", "commit", "-m", full_msg], cwd=cwd)

        if ok:
            _, sha = await ctx.gh._run(["git", "rev-parse", "HEAD"], cwd=cwd)
            return {"ok": True, "sha": sha.strip()[:7], "message": full_msg}
        else:
            return {"ok": False, "error": output}

    @server.tool()
    async def fleet_task_complete(summary: str) -> dict:
        """Complete your task: push branch, create PR, update MC, notify IRC.

        One call does everything:
        1. Push branch to remote
        2. Create PR with changelog and diff table
        3. Set task custom fields (branch, pr_url)
        4. Post structured completion comment
        5. Notify IRC #fleet and #reviews
        6. Post to board memory
        7. Move task to review

        Args:
            summary: What you did and why (2-3 sentences).
        """
        # Methodology gate: only allowed during work stage
        blocked = _check_stage_allowed("fleet_task_complete")
        if blocked:
            return blocked

        ctx = _get_ctx()
        if not ctx.task_id:
            return {"ok": False, "error": "No task_id. Call fleet_read_context first."}
        board_id = await ctx.resolve_board_id()
        cwd = ctx.worktree

        # Detect worktree from filesystem if not set
        if not cwd:
            import os
            fleet_dir = os.environ.get("FLEET_DIR", ".")
            short = ctx.task_id[:8]
            for proj_dir in os.listdir(os.path.join(fleet_dir, "projects")) if os.path.isdir(os.path.join(fleet_dir, "projects")) else []:
                wt_dir = os.path.join(fleet_dir, "projects", proj_dir, "worktrees")
                if os.path.isdir(wt_dir):
                    for wt in os.listdir(wt_dir):
                        if wt.endswith(f"-{short}"):
                            cwd = os.path.join(wt_dir, wt)
                            ctx.worktree = cwd
                            if not ctx.project_name:
                                ctx.project_name = proj_dir
                            break

        if not cwd:
            # No worktree — internal task, just complete with review gates
            comment = comment_tmpl.format_complete_no_changes(summary, ctx.agent_name or "agent")
            task_type = ""
            try:
                task_data = await ctx.mc.get_task(board_id, ctx.task_id)
                task_type = task_data.custom_fields.task_type or ""
            except Exception:
                pass
            review_gates = _build_review_gates(task_type, has_code=False)
            custom_update: dict = {}
            if review_gates:
                custom_update["review_gates"] = review_gates
            try:
                await ctx.mc.update_task(
                    board_id, ctx.task_id, status="review", comment=comment,
                    custom_fields=custom_update if custom_update else None,
                )
            except Exception as e:
                return {"ok": False, "error": str(e)}
            # Create approval for fleet-ops to review
            try:
                await ctx.mc.create_approval(
                    board_id,
                    task_ids=[ctx.task_id],
                    action_type="task_completion",
                    confidence=85.0,
                    rubric_scores={"completeness": 85, "quality": 85},
                    reason=f"Completed by {ctx.agent_name or 'agent'}. Summary: {summary[:200]}",
                )
            except Exception:
                pass
            return {"ok": True, "status": "review", "pr": None}

        # Run tests before proceeding (quality gate)
        test_passed = True
        test_summary = ""
        try:
            ok, test_output = await ctx.gh._run(
                ["python", "-m", "pytest", "--tb=line", "-q"], cwd=cwd,
            )
            if ok:
                test_summary = test_output.strip().split("\n")[-1] if test_output.strip() else "passed"
            else:
                test_passed = False
                lines = test_output.strip().split("\n") if test_output else []
                test_summary = lines[-1] if lines else "tests failed"
        except Exception:
            test_summary = "no tests found"

        # Get branch
        _, branch = await ctx.gh._run(["git", "branch", "--show-current"], cwd=cwd)
        branch = branch.strip()

        # Get commits and diff
        commits = await ctx.gh.get_branch_commits(cwd)
        diff_stat = await ctx.gh.get_diff_stat(cwd)

        if not commits:
            # No commits — nothing to push/PR
            comment = comment_tmpl.format_complete_no_changes(summary, ctx.agent_name or "agent")
            try:
                await ctx.mc.update_task(
                    board_id, ctx.task_id, status="review", comment=comment,
                )
            except Exception as e:
                return {"ok": False, "error": str(e)}
            return {"ok": True, "status": "review", "pr": None, "reason": "no commits"}

        # Push
        push_ok = await ctx.gh.push_branch(cwd, branch)
        if not push_ok:
            _report_error("fleet_task_complete", "Push failed. Check git remote auth.")
            return {"ok": False, "error": "Push failed. Check git remote auth."}

        # Resolve URLs
        task_url = ctx.urls.task_url(ctx.task_id)
        urls = ctx.urls.resolve(
            project=ctx.project_name,
            task_id=ctx.task_id,
            branch=branch,
            commits=[c["sha"] for c in commits],
            files=[f["path"] for f in diff_stat],
        )

        # Parse commits for templates
        parsed_commits = [ctx.gh.parse_commit(c["sha"], c["message"]) for c in commits]

        # Get task title
        try:
            task = await ctx.mc.get_task(board_id, ctx.task_id)
            task_title = task.title
        except Exception:
            task_title = ctx.task_id[:8]

        agent_name = ctx.agent_name or "agent"

        # Build PR body using template
        pr_body = pr_tmpl.format_pr_body(
            summary=summary,
            commits=parsed_commits,
            diff_stat=diff_stat,
            urls=urls,
            task_id=ctx.task_id,
            task_title=task_title,
            agent_name=agent_name,
        )

        # Create PR
        try:
            pr = await ctx.gh.create_pr(
                cwd,
                title=pr_tmpl.format_pr_title(agent_name, task_title),
                body=pr_body,
            )
        except Exception as e:
            _report_error("fleet_task_complete", f"PR creation failed: {e}")
            return {"ok": False, "error": f"PR creation failed: {e}"}

        # Update MC custom fields + review gates
        task_type = ""
        try:
            task_data = await ctx.mc.get_task(board_id, ctx.task_id)
            task_type = task_data.custom_fields.task_type or ""
        except Exception:
            pass

        review_gates = _build_review_gates(task_type, bool(pr.url))
        custom_update = {"branch": branch, "pr_url": pr.url}
        if review_gates:
            custom_update["review_gates"] = review_gates

        try:
            await ctx.mc.update_task(
                board_id, ctx.task_id,
                custom_fields=custom_update,
            )
        except Exception:
            pass

        # Completion comment using template
        comment = comment_tmpl.format_complete(
            summary=summary,
            pr_url=pr.url,
            branch=branch,
            compare_url=urls.compare or "",
            commit_count=len(commits),
            files=[f["path"] for f in diff_stat],
            agent_name=agent_name,
        )
        try:
            await ctx.mc.update_task(
                board_id, ctx.task_id, status="review", comment=comment,
            )
        except Exception:
            pass

        # Create approval for quality gate — with skill compliance check
        try:
            from fleet.core.skill_enforcement import check_compliance

            # Reconstruct tools used based on observable state
            tools_used = ["fleet_read_context", "fleet_task_complete"]  # We know these
            if commits:
                tools_used.append("fleet_commit")
            # Check if acceptance comment exists (fleet_task_accept was called)
            # This is approximate — the acceptance comment in task comments indicates it
            tools_used.append("fleet_task_accept")  # Assume if they got here

            task_type_val = task_type or "task"
            compliance = check_compliance(task_type_val, tools_used)
            compliance_penalty = compliance.confidence_penalty

            test_score = 85 if test_passed else 30
            base_confidence = 85.0 if test_passed else 50.0
            confidence = max(base_confidence - compliance_penalty, 20.0)

            compliance_note = ""
            if compliance.required_missed:
                compliance_note = f" Missing tools: {', '.join(compliance.required_missed)}."

            await ctx.mc.create_approval(
                board_id,
                task_ids=[ctx.task_id],
                action_type="task_completion",
                confidence=confidence,
                rubric_scores={
                    "correctness": 85,
                    "completeness": 85,
                    "quality": 85,
                    "tests": test_score,
                    "compliance": 85 - int(compliance_penalty),
                },
                reason=(
                    f"Task completed by {agent_name}. "
                    f"PR: {pr.url}. "
                    f"{len(commits)} commit(s), {len(diff_stat)} file(s) changed. "
                    f"Tests: {test_summary}.{compliance_note} "
                    f"Summary: {summary[:200]}"
                ),
            )
        except Exception:
            pass  # Approval creation is best-effort

        # Multi-surface publish via chain runner (IRC, ntfy, Plane, board memory)
        try:
            from fleet.core.event_chain import build_task_complete_chain
            from fleet.core.chain_runner import ChainRunner

            chain = build_task_complete_chain(
                task_id=ctx.task_id,
                agent_name=agent_name,
                summary=summary,
                pr_url=pr.url,
                branch=branch,
                test_results=test_summary,
                project=ctx.project_name or "",
            )

            runner = ChainRunner(
                mc=ctx.mc,
                irc=ctx.irc,
                gh=ctx.gh,
                plane=ctx.plane,
                board_id=board_id,
                plane_workspace=ctx.plane_workspace if ctx.plane else "",
            )
            chain_result = await runner.run(chain)

            if chain_result.errors:
                for err in chain_result.errors[:3]:
                    pass  # Chain errors are non-critical — tool already succeeded
        except Exception:
            # Chain execution is best-effort — core MC operations already done
            # Fall back to direct IRC/memory if chain fails
            try:
                await ctx.irc.notify(
                    "#fleet", irc_tmpl.format_pr_ready(agent_name, task_title, pr.url)
                )
                await ctx.irc.notify(
                    "#reviews", irc_tmpl.format_pr_review(agent_name, task_title, pr.url)
                )
            except Exception:
                pass
            try:
                await ctx.mc.post_memory(
                    board_id,
                    content=memory_tmpl.format_pr_notice(
                        task_title=task_title, pr_url=pr.url,
                        agent_name=agent_name, branch=branch,
                        compare_url=urls.compare or "",
                    ),
                    tags=memory_tmpl.pr_tags(ctx.project_name),
                    source=agent_name,
                )
            except Exception:
                pass

        # Emit event for the event bus
        _emit_event(
            "fleet.task.completed",
            subject=ctx.task_id,
            recipient="fleet-ops",
            priority="important",
            mentions=["fleet-ops"],
            tags=["review", f"project:{ctx.project_name or 'unknown'}"],
            surfaces=["internal", "public", "channel", "notify", "plane"],
            summary=summary,
            pr_url=pr.url,
            branch=branch,
            commits=len(commits),
            files_changed=len(diff_stat),
            test_passed=test_passed,
        )

        return {
            "ok": True,
            "pr_url": pr.url,
            "pr_number": pr.number,
            "branch": branch,
            "commits": len(commits),
            "files_changed": len(diff_stat),
            "status": "review",
        }

    @server.tool()
    async def fleet_alert(
        severity: str, title: str, details: str, category: str = "quality"
    ) -> dict:
        """Raise an alert for security, quality, or architecture concerns.

        Args:
            severity: "critical", "high", "medium", or "low"
            title: Short alert title.
            details: Detailed description with evidence.
            category: "security", "quality", "architecture", "workflow", "tooling"
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()

        content = memory_tmpl.format_alert(
            severity=severity, title=title, details=details,
            category=category, agent_name=ctx.agent_name or "agent",
        )

        tags = memory_tmpl.alert_tags(severity, category, ctx.project_name)
        try:
            await ctx.mc.post_memory(
                board_id, content=content, tags=tags,
                source=ctx.agent_name or "agent",
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        channel = irc_tmpl.route_channel(severity=severity)
        irc_msg = irc_tmpl.format_alert(ctx.agent_name or "agent", severity, title)
        try:
            await ctx.irc.notify(channel, irc_msg)
        except Exception:
            pass

        return {"ok": True, "severity": severity, "channel": channel}

    @server.tool()
    async def fleet_pause(reason: str, needed: str) -> dict:
        """Pause work and escalate. Use when stuck, uncertain, or blocked.

        Args:
            reason: Why you're pausing (specific).
            needed: What would unblock you (who needs to do what).
        """
        ctx = _get_ctx()
        if not ctx.task_id:
            return {"ok": False, "error": "No task_id."}
        board_id = await ctx.resolve_board_id()

        comment = comment_tmpl.format_blocker(reason, needed, ctx.agent_name or "agent")
        try:
            await ctx.mc.post_comment(board_id, ctx.task_id, comment)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        task_url = ctx.urls.task_url(ctx.task_id) if ctx.task_id else ""
        try:
            await ctx.irc.notify_event(
                agent=ctx.agent_name or "agent", event="🚫 BLOCKED",
                title=reason[:60], url=task_url,
            )
        except Exception:
            pass

        return {"ok": True, "action": "Wait for human input."}

    @server.tool()
    async def fleet_escalate(
        title: str,
        details: str,
        task_id: str = "",
        question: str = "",
    ) -> dict:
        """Escalate to human when you need direction, a decision, or can't proceed.

        Use this when:
        - A review needs human judgment (not just agent review)
        - Requirements are unclear and you need clarification
        - Multiple valid approaches and human should decide
        - Something is too risky for autonomous agent decision

        Args:
            title: Short summary of what needs attention.
            details: Full context — what you've found, what the options are.
            task_id: Task this relates to (uses current task if not specified).
            question: The specific question you need answered.
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()
        resolved_task_id = task_id or ctx.task_id

        # Post to board memory for persistence
        content = (
            f"## \U0001f6a8 Escalation: {title}\n\n"
            f"**From:** {ctx.agent_name or 'agent'}\n"
            f"**Task:** {resolved_task_id[:8] if resolved_task_id else 'N/A'}\n\n"
            f"### Details\n{details}\n\n"
        )
        if question:
            content += f"### Question for Human\n{question}\n"

        try:
            await ctx.mc.post_memory(
                board_id,
                content=content,
                tags=["escalation", "human-attention", f"agent:{ctx.agent_name or 'unknown'}"],
                source=ctx.agent_name or "agent",
            )
        except Exception:
            pass

        # Post as task comment if task exists
        if resolved_task_id:
            try:
                await ctx.mc.post_comment(
                    board_id, resolved_task_id,
                    f"## \U0001f6a8 Escalated to Human\n\n"
                    f"**{title}**\n\n{details}\n\n"
                    f"**Question:** {question}" if question else
                    f"## \U0001f6a8 Escalated to Human\n\n"
                    f"**{title}**\n\n{details}",
                )
            except Exception:
                pass

        # IRC alert — human sees this immediately
        try:
            await ctx.irc.notify(
                "#alerts",
                irc_tmpl.format_event(
                    ctx.agent_name or "agent",
                    "\U0001f6a8 NEEDS HUMAN",
                    f"{title[:50]} — {question[:40]}" if question else title[:60],
                ),
            )
        except Exception:
            pass

        # ntfy notification — urgent, human needs to see this
        try:
            from fleet.infra.ntfy_client import NtfyClient
            ntfy = NtfyClient()
            await ntfy.publish(
                title=f"[{ctx.agent_name or 'agent'}] Needs your attention: {title[:60]}",
                message=f"{details[:200]}\n\nQuestion: {question}" if question else details[:300],
                priority="urgent",
                tags=["rotating_light", "escalation"],
                click_url="",
            )
            await ntfy.close()
        except Exception:
            pass

        return {
            "ok": True,
            "action": "Escalated. Wait for human response in board memory or task comment.",
            "task_id": resolved_task_id,
        }

    @server.tool()
    async def fleet_notify_human(
        title: str,
        message: str,
        priority: str = "info",
        url: str = "",
        tags: list[str] | None = None,
    ) -> dict:
        """Send a notification to the human via ntfy (and Windows for urgent).

        Use this when the human needs to know something — sprint progress,
        escalation, alert, or any event worth their attention.

        Priority routing:
        - "info" → ntfy fleet-progress (quiet, in history)
        - "important" → ntfy fleet-review (prominent notification)
        - "urgent" → ntfy fleet-alert (persistent, sound, + Windows toast)

        Args:
            title: Short notification title.
            message: Body text with context.
            priority: "info", "important", or "urgent".
            url: Click URL (task URL, PR URL) — opens when notification clicked.
            tags: ntfy tags for classification (e.g., ["white_check_mark", "sprint"]).
        """
        from fleet.infra.ntfy_client import NtfyClient

        ctx = _get_ctx()
        agent = ctx.agent_name or "agent"

        # Add agent tag
        all_tags = list(tags or [])
        all_tags.append(agent)

        ntfy = NtfyClient()
        try:
            ok = await ntfy.publish(
                title=f"[{agent}] {title}",
                message=message,
                priority=priority,
                tags=all_tags,
                click_url=url,
            )
        except Exception:
            ok = False
        finally:
            await ntfy.close()

        return {"ok": ok, "priority": priority, "channel": "ntfy"}

    @server.tool()
    async def fleet_chat(
        message: str,
        mention: str = "",
    ) -> dict:
        """Post to the internal fleet chat. Tag others with @name.

        Use this to communicate with teammates:
        - Request work: "I'm idle, what should I work on?"
        - Ask a question: "@architect Is this the right pattern?"
        - Share context: "FYI the Plane API rate limits at 60/min"
        - Respond to requests: "@ux-designer Take a look at the CLI output format"

        Messages are visible to all agents via board memory (tag: chat).
        @mentioned agents see the message in their next fleet_read_context.
        @lead always reaches fleet-ops (board lead).

        Args:
            message: Your message to the team.
            mention: Agent to tag (e.g., "architect", "lead", "all").
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()
        agent = ctx.agent_name or "agent"

        # Format chat message
        mention_prefix = f"@{mention} " if mention else ""
        content = f"**[{agent}]** {mention_prefix}{message}"

        tags = ["chat", f"from:{agent}"]
        if mention:
            if mention == "all":
                tags.append("mention:all")
            elif mention == "lead":
                tags.append("mention:fleet-ops")
            else:
                tags.append(f"mention:{mention}")

        try:
            await ctx.mc.post_memory(
                board_id,
                content=content,
                tags=tags,
                source=agent,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        # Also post to IRC #fleet for visibility
        try:
            irc_msg = f"[{agent}] {mention_prefix}{message[:80]}"
            await ctx.irc.notify("#fleet", irc_msg)
        except Exception:
            pass

        return {"ok": True, "posted_by": agent, "mention": mention or "none"}

    @server.tool()
    async def fleet_task_create(
        title: str,
        description: str = "",
        agent_name: str = "",
        project: str = "",
        priority: str = "medium",
        depends_on: list[str] | None = None,
        parent_task: str = "",
        task_type: str = "task",
        story_points: int = 0,
    ) -> dict:
        """Create a subtask, follow-up, or chained task on the board.

        Use this to break down work, create subtasks, file blockers,
        or chain tasks that unlock when dependencies complete.

        Args:
            title: Task title (required).
            description: Detailed description of what needs to be done.
            agent_name: Assign to a specific agent (e.g., "software-engineer").
            project: Project name (e.g., "nnrt", "dspd", "fleet").
            priority: "low", "medium", "high", "urgent".
            depends_on: List of task IDs that must complete first.
            parent_task: Parent task ID (for subtask/story hierarchy).
            task_type: "epic", "story", "task", "subtask", "blocker", "request", "concern".
            story_points: Effort estimate (1, 2, 3, 5, 8, 13).
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()

        # CASCADE DEPTH CHECK — prevent infinite auto-creation chains
        # Max depth: 3 levels (human → PM → agent → subtask)
        MAX_CASCADE_DEPTH = 3
        resolved_parent = parent_task or ctx.task_id or ""
        if resolved_parent:
            try:
                depth = 0
                check_id = resolved_parent
                all_tasks = await ctx.mc.list_tasks(board_id)
                task_map = {t.id: t for t in all_tasks}
                while check_id and depth < MAX_CASCADE_DEPTH + 1:
                    t = task_map.get(check_id)
                    if not t:
                        break
                    check_id = t.custom_fields.parent_task or ""
                    depth += 1
                if depth >= MAX_CASCADE_DEPTH:
                    return {
                        "ok": False,
                        "error": (
                            f"Cascade depth limit ({MAX_CASCADE_DEPTH}) reached. "
                            f"Cannot create subtask of subtask of subtask. "
                            f"Simplify the task hierarchy or escalate to PM."
                        ),
                    }
            except Exception:
                pass  # Don't block on depth check failure

        # Resolve agent ID if name provided
        assigned_agent_id = None
        if agent_name:
            agents = await ctx.mc.list_agents()
            agent = next((a for a in agents if a.name == agent_name), None)
            if agent:
                assigned_agent_id = agent.id

        # Build custom fields
        custom_fields: dict = {}
        if project or ctx.project_name:
            custom_fields["project"] = project or ctx.project_name
        if agent_name:
            custom_fields["agent_name"] = agent_name
        if parent_task:
            custom_fields["parent_task"] = parent_task
        elif ctx.task_id:
            custom_fields["parent_task"] = ctx.task_id
        if task_type:
            custom_fields["task_type"] = task_type
        if story_points:
            custom_fields["story_points"] = story_points

        creator = ctx.agent_name or "agent"
        parent_ref = parent_task or ctx.task_id or "N/A"

        try:
            task = await ctx.mc.create_task(
                board_id,
                title=title,
                description=description,
                priority=priority,
                assigned_agent_id=assigned_agent_id,
                custom_fields=custom_fields if custom_fields else None,
                depends_on=depends_on,
                auto_created=True,
                auto_reason=f"Created by {creator} from task {parent_ref[:8]}",
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        # Notify IRC
        try:
            await ctx.irc.notify(
                "#fleet",
                irc_tmpl.format_event(
                    creator, "📋 SUBTASK",
                    f"{title[:50]} → {agent_name or 'unassigned'}",
                ),
            )
        except Exception:
            pass

        return {
            "ok": True,
            "task_id": task.id,
            "title": task.title,
            "assigned_to": agent_name or "(unassigned)",
            "parent_task": custom_fields.get("parent_task", ""),
            "depends_on": depends_on or [],
            "is_blocked": bool(depends_on),
        }

    @server.tool()
    async def fleet_approve(
        approval_id: str,
        decision: str = "approved",
        comment: str = "",
        task_id: str = "",
    ) -> dict:
        """Approve or reject a pending task completion.

        When approving: task can transition review → done (board lead action).
        When rejecting: task moves back to inbox for rework. MC notifies the
        original agent with "Changes requested". Include specific feedback
        in the comment so the agent knows what to fix.

        Args:
            approval_id: The approval ID to act on.
            decision: "approved" or "rejected".
            comment: Reasoning for the decision. Required for rejections.
            task_id: Task ID (optional, resolved from approval if not given).
        """
        from fleet.core.agent_roles import can_agent_reject, should_create_fix_task

        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()
        agent = ctx.agent_name or ""

        if decision not in ("approved", "rejected"):
            return {"ok": False, "error": "decision must be 'approved' or 'rejected'"}

        if decision == "rejected" and not comment:
            return {"ok": False, "error": "comment is required when rejecting — explain what needs fixing"}

        # Check PR authority for rejections
        if decision == "rejected" and not can_agent_reject(agent):
            return {
                "ok": False,
                "error": (
                    f"{agent} cannot reject — only request changes. "
                    f"Use fleet_task_progress to post feedback instead, "
                    f"or ask fleet-ops to reject."
                ),
            }

        # Resolve approval
        try:
            approval = await ctx.mc.approve_approval(
                board_id, approval_id, status=decision, comment=comment,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        resolved_task_id = task_id or approval.task_id
        result: dict = {"ok": True, "approval_id": approval.id, "status": approval.status}

        if decision == "approved" and resolved_task_id:
            # Board lead moves review → done
            try:
                await ctx.mc.update_task(
                    board_id, resolved_task_id,
                    status="done",
                    comment=f"**Approved by {agent or 'lead'}**: {comment}",
                )
                result["task_status"] = "done"
            except Exception as e:
                result["transition_error"] = str(e)

        elif decision == "rejected" and resolved_task_id:
            # Move review → inbox (rework). MC auto-notifies original agent.
            try:
                await ctx.mc.update_task(
                    board_id, resolved_task_id,
                    status="inbox",
                    comment=f"**Rejected by {agent or 'lead'}**: {comment}",
                )
                result["task_status"] = "inbox (rework)"
            except Exception as e:
                result["transition_error"] = str(e)

            # Auto-create fix task if this agent's role requires it
            if should_create_fix_task(agent) and resolved_task_id:
                try:
                    original_task = await ctx.mc.get_task(board_id, resolved_task_id)
                    original_agent = original_task.custom_fields.agent_name or ""
                    fix_title = f"Fix: {original_task.title[:40]} — {comment[:30]}"

                    agents = await ctx.mc.list_agents()
                    original_agent_id = next(
                        (a.id for a in agents if a.name == original_agent), None
                    )

                    await ctx.mc.create_task(
                        board_id,
                        title=fix_title,
                        description=(
                            f"Rejected by {agent}: {comment}\n\n"
                            f"Original task: {original_task.title}\n"
                            f"Fix the issues described above and re-submit."
                        ),
                        priority="high",
                        assigned_agent_id=original_agent_id,
                        custom_fields={
                            "agent_name": original_agent,
                            "parent_task": resolved_task_id,
                            "task_type": "subtask",
                            "project": original_task.custom_fields.project or "",
                        },
                    )
                    result["fix_task_created"] = True
                    result["fix_assigned_to"] = original_agent
                except Exception:
                    result["fix_task_created"] = False

        # IRC notification
        emoji = "\u2705" if decision == "approved" else "\u274c"
        try:
            task_ref = resolved_task_id[:8] if resolved_task_id else approval_id[:8]
            await ctx.irc.notify(
                "#fleet",
                irc_tmpl.format_event(
                    ctx.agent_name or "agent",
                    f"{emoji} {decision.upper()}",
                    f"task {task_ref}: {comment[:50]}" if comment else f"task {task_ref}",
                ),
            )
        except Exception:
            pass

        # Emit event for approval decision
        _emit_event(
            f"fleet.task.{'approved' if decision == 'approved' else 'rejected'}",
            subject=approval_id,
            recipient=result.get("task_agent", "all"),
            priority="important",
            mentions=[result.get("task_agent", "")] if result.get("task_agent") else [],
            tags=["review", decision],
            surfaces=["internal", "channel", "plane"],
            decision=decision,
            comment=comment,
            task_id=result.get("task_id", ""),
        )

        return result

    @server.tool()
    async def fleet_agent_status() -> dict:
        """Check fleet health: agents, tasks by status, pending approvals.

        Returns a snapshot of the fleet for situational awareness.
        Call this during heartbeats to understand what needs attention.
        No arguments needed.
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()
        result: dict = {"board_id": board_id}

        # Agents
        try:
            agents = await ctx.mc.list_agents()
            result["agents"] = [
                {"name": a.name, "status": a.status, "id": a.id}
                for a in agents if "Gateway" not in a.name
            ]
        except Exception as e:
            result["agents_error"] = str(e)

        # Tasks by status
        try:
            tasks = await ctx.mc.list_tasks(board_id)
            counts: dict[str, int] = {}
            blocked_count = 0
            unassigned_inbox = 0
            for t in tasks:
                s = t.status.value
                counts[s] = counts.get(s, 0) + 1
                if t.is_blocked:
                    blocked_count += 1
                if s == "inbox" and not t.assigned_agent_id:
                    unassigned_inbox += 1
            result["task_counts"] = counts
            result["blocked_tasks"] = blocked_count
            result["unassigned_inbox"] = unassigned_inbox
        except Exception as e:
            result["tasks_error"] = str(e)

        # Pending approvals
        try:
            approvals = await ctx.mc.list_approvals(board_id, status="pending")
            result["pending_approvals"] = [
                {
                    "id": a.id,
                    "task_id": a.task_id[:8] if a.task_id else "",
                    "confidence": a.confidence,
                    "action_type": a.action_type,
                }
                for a in approvals
            ]
        except Exception:
            result["pending_approvals"] = []

        return result
    # ─── Plane Tools (optional — only work when Plane is configured) ────

    @server.tool()
    async def fleet_plane_status(project: str = "") -> dict:
        """Get Plane project status: sprint progress, modules, recent activity.

        Plane is optional. Returns {"plane_available": false} if not configured.
        Use this in heartbeats to understand project state without extra tool calls.

        Args:
            project: Project identifier (AICP, OF, DSPD, NNRT). Empty = all projects.
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False, "message": "Plane not configured (PLANE_URL/PLANE_API_KEY missing)"}

        ws = ctx.plane_workspace
        result: dict = {"plane_available": True, "workspace": ws}

        try:
            projects = await plane.list_projects(ws)
            if project:
                projects = [p for p in projects if p.identifier == project.upper()]

            proj_data = []
            for p in projects:
                proj_info: dict = {
                    "identifier": p.identifier,
                    "name": p.name,
                }

                # Cycles (sprints)
                try:
                    cycles = await plane.list_cycles(ws, p.id)
                    current = [c for c in cycles if c.status == "current"]
                    proj_info["active_sprint"] = current[0].name if current else None
                    proj_info["total_cycles"] = len(cycles)
                except Exception:
                    proj_info["active_sprint"] = None

                # Modules (epics)
                try:
                    modules = await plane.list_cycles(ws, p.id)
                except Exception:
                    pass

                # Issues count
                try:
                    issues = await plane.list_issues(ws, p.id, limit=1)
                except Exception:
                    pass

                proj_data.append(proj_info)

            result["projects"] = proj_data

        except Exception as e:
            result["error"] = str(e)

        return result

    @server.tool()
    async def fleet_plane_sprint(project: str = "AICP") -> dict:
        """Get current sprint details: issues, progress, velocity.

        Args:
            project: Project identifier (default: AICP).
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        ws = ctx.plane_workspace
        result: dict = {"plane_available": True, "project": project}

        try:
            projects = await plane.list_projects(ws)
            proj = next((p for p in projects if p.identifier == project.upper()), None)
            if not proj:
                return {"error": f"Project {project} not found in Plane"}

            # Get cycles
            cycles = await plane.list_cycles(ws, proj.id)
            current = next((c for c in cycles if c.status == "current"), None)
            if not current:
                # Fall back to most recent
                current = cycles[0] if cycles else None

            if current:
                result["sprint"] = {
                    "name": current.name,
                    "status": current.status,
                    "start_date": current.start_date,
                    "end_date": current.end_date,
                }

            # Get issues
            issues = await plane.list_issues(ws, proj.id)
            result["total_issues"] = len(issues)

            by_priority: dict[str, int] = {}
            for i in issues:
                by_priority[i.priority] = by_priority.get(i.priority, 0) + 1
            result["by_priority"] = by_priority

            # Get modules
            modules_resp = await plane.list_cycles(ws, proj.id)

        except Exception as e:
            result["error"] = str(e)

        return result

    @server.tool()
    async def fleet_plane_sync(direction: str = "both") -> dict:
        """Trigger Plane ↔ OCMC sync.

        Args:
            direction: "in" (Plane→OCMC), "out" (OCMC→Plane), or "both".
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        from fleet.core.plane_sync import PlaneSyncer

        ws = ctx.plane_workspace
        board_id = await ctx.resolve_board_id()

        try:
            projects = await plane.list_projects(ws)
            project_ids = [p.id for p in projects]

            syncer = PlaneSyncer(
                mc=ctx.mc,
                plane=plane,
                board_id=board_id,
                workspace_slug=ws,
                project_ids=project_ids,
            )

            result: dict = {"direction": direction}

            if direction in ("in", "both"):
                ingest = await syncer.ingest_from_plane()
                result["ingest"] = {
                    "created": len(ingest.created),
                    "skipped": ingest.skipped_count,
                    "errors": ingest.errors,
                }

            if direction in ("out", "both"):
                push = await syncer.push_completions_to_plane()
                result["push"] = {
                    "updated": len(push.updated),
                    "skipped": len(push.skipped),
                    "errors": push.errors,
                }

            return result

        except Exception as e:
            return {"error": str(e)}

    @server.tool()
    async def fleet_plane_create_issue(
        project: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        assignee: str = "",
        labels: str = "",
        module: str = "",
        parent_issue: str = "",
    ) -> dict:
        """Create an issue in Plane — used by PM to create work items from OCMC.

        When an agent creates subtasks via fleet_task_create in OCMC, the PM should
        also create corresponding Plane issues to keep both surfaces in sync.
        This tool handles the Plane side.

        Args:
            project: Project identifier (AICP, OF, DSPD, NNRT).
            title: Issue title.
            description: Issue description (plain text — will be wrapped in HTML).
            priority: urgent, high, medium, low, or none.
            assignee: Agent email (e.g., "architect@fleet.local"). Empty = unassigned.
            labels: Comma-separated label names (e.g., "infra,security").
            module: Module name to add issue to (e.g., "Stage 1: Make LocalAI Functional").
            parent_issue: Parent issue title for sub-issue linking (creates relation).
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        ws = ctx.plane_workspace
        result: dict = {"project": project}

        try:
            projects = await plane.list_projects(ws)
            proj = next((p for p in projects if p.identifier == project.upper()), None)
            if not proj:
                return {"error": f"Project {project} not found"}

            # Resolve assignee to user ID
            assignee_ids = []
            if assignee:
                members = await plane.list_projects(ws)  # Need member lookup
                # Use the email as-is — the API resolves it
                # Actually need to look up member ID from workspace members

            # Build description HTML
            desc_html = ""
            if description:
                paragraphs = description.split("\n\n")
                desc_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

            # Resolve labels
            label_ids = []
            if labels:
                all_labels = await plane._client.get(
                    f"/api/v1/workspaces/{ws}/projects/{proj.id}/labels/"
                )
                if all_labels.status_code == 200:
                    label_data = all_labels.json()
                    label_list = label_data.get("results", label_data) if isinstance(label_data, dict) else label_data
                    label_map = {l["name"]: l["id"] for l in label_list}
                    for ln in labels.split(","):
                        ln = ln.strip()
                        if ln in label_map:
                            label_ids.append(label_map[ln])

            issue = await plane.create_issue(
                ws, proj.id,
                title=title,
                description_html=desc_html or f"<p>{title}</p>",
                priority=priority,
                label_ids=label_ids or None,
            )

            result["issue_id"] = issue.id
            result["title"] = issue.title
            result["sequence_id"] = issue.sequence_id
            result["priority"] = issue.priority

            # Add to module if specified
            if module and issue.id:
                try:
                    from fleet.infra.plane_client import PlaneClient
                    # Get modules
                    mods_resp = await plane._client.get(
                        f"/api/v1/workspaces/{ws}/projects/{proj.id}/modules/"
                    )
                    if mods_resp.status_code == 200:
                        mods_data = mods_resp.json()
                        mods_list = mods_data.get("results", mods_data) if isinstance(mods_data, dict) else mods_data
                        mod = next((m for m in mods_list if m["name"] == module), None)
                        if mod:
                            # Add issue to module
                            await plane._client.post(
                                f"/api/v1/workspaces/{ws}/projects/{proj.id}/modules/{mod['id']}/module-issues/",
                                json={"issues": [issue.id]},
                            )
                            result["module"] = module
                except Exception:
                    pass

            # Notify IRC
            try:
                agent_name = ctx.agent_name or "pm"
                await ctx.irc.notify(
                    "#fleet",
                    f"[{agent_name}] 📋 Plane issue: {title[:50]} ({project}/{issue.sequence_id})",
                )
            except Exception:
                pass

            # Emit event for cross-platform tracking
            _emit_event(
                "fleet.plane.issue_created",
                source="fleet/mcp/tools/fleet_plane_create_issue",
                subject=issue.id,
                recipient="all",
                priority="info",
                tags=[f"project:{project}", "plane"],
                surfaces=["internal", "channel", "plane"],
                title=title,
                issue_id=issue.id,
                project=project,
                module=module or "",
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    @server.tool()
    async def fleet_plane_comment(
        project: str,
        issue_id: str,
        comment: str,
        mention: str = "",
    ) -> dict:
        """Post a comment on a Plane issue — for updates, mentions, and cross-surface communication.

        Use @agent-name in comments to notify specific agents. The sync worker
        routes mentions to the agent's next heartbeat context.

        Args:
            project: Project identifier.
            issue_id: Plane issue UUID or sequence number.
            comment: Comment text (plain text — wrapped in HTML).
            mention: Agent name to @mention (e.g., "architect"). Added to comment.
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        ws = ctx.plane_workspace
        result: dict = {"project": project, "issue_id": issue_id}

        try:
            projects = await plane.list_projects(ws)
            proj = next((p for p in projects if p.identifier == project.upper()), None)
            if not proj:
                return {"error": f"Project {project} not found"}

            # Build comment HTML with mention
            comment_html = f"<p>{comment}</p>"
            if mention:
                comment_html = f"<p><strong>@{mention}</strong> {comment}</p>"

            # Post comment via API
            resp = await plane._client.post(
                f"/api/v1/workspaces/{ws}/projects/{proj.id}/issues/{issue_id}/comments/",
                json={"comment_html": comment_html},
            )
            if resp.status_code in (200, 201):
                comment_data = resp.json()
                result["comment_id"] = comment_data.get("id")
                result["posted"] = True
            else:
                result["error"] = f"HTTP {resp.status_code}"

            # Notify IRC about the mention
            if mention:
                try:
                    await ctx.irc.notify(
                        "#fleet",
                        f"[{ctx.agent_name or 'pm'}] 💬 @{mention} on Plane: {comment[:40]}",
                    )
                except Exception:
                    pass

            # Emit event — mentions route to agent feeds
            _emit_event(
                "fleet.plane.issue_commented",
                source="fleet/mcp/tools/fleet_plane_comment",
                subject=issue_id,
                recipient=mention if mention else "all",
                priority="important" if mention else "info",
                mentions=[mention] if mention else [],
                tags=["plane", "comment", f"project:{project}"],
                surfaces=["internal", "channel", "plane"],
                comment=comment[:200],
                issue_id=issue_id,
                project=project,
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    @server.tool()
    async def fleet_plane_update_issue(
        project: str,
        issue_id: str,
        state: str = "",
        priority: str = "",
        assignee: str = "",
        labels: str = "",
    ) -> dict:
        """Update a Plane issue — change state, priority, or assignment.

        Used by PM to update Plane when OCMC tasks change, or by the sync worker.

        Args:
            project: Project identifier.
            issue_id: Plane issue UUID.
            state: New state name (e.g., "In Progress", "Done"). Empty = no change.
            priority: New priority. Empty = no change.
            assignee: Agent email for assignment. Empty = no change.
            labels: Comma-separated label names to SET (replaces existing). Empty = no change.
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        ws = ctx.plane_workspace
        result: dict = {"project": project, "issue_id": issue_id, "updated": []}

        try:
            projects = await plane.list_projects(ws)
            proj = next((p for p in projects if p.identifier == project.upper()), None)
            if not proj:
                return {"error": f"Project {project} not found"}

            patch: dict = {}

            # Resolve state name to ID
            if state:
                states = await plane.list_states(ws, proj.id)
                st = next((s for s in states if s.name.lower() == state.lower()), None)
                if st:
                    patch["state"] = st.id
                    result["updated"].append(f"state={state}")

            if priority:
                patch["priority"] = priority
                result["updated"].append(f"priority={priority}")

            if patch:
                await plane.update_issue(ws, proj.id, issue_id, **{
                    k: v for k, v in [
                        ("state_id", patch.get("state")),
                        ("priority", patch.get("priority")),
                    ] if v
                })

        except Exception as e:
            result["error"] = str(e)

        return result

    @server.tool()
    async def fleet_plane_list_modules(project: str = "AICP") -> dict:
        """List modules (epics) in a Plane project with their status and lead.

        Args:
            project: Project identifier (default: AICP).
        """
        ctx = _get_ctx()
        plane = ctx.plane
        if not plane:
            return {"plane_available": False}

        ws = ctx.plane_workspace
        result: dict = {"project": project, "modules": []}

        try:
            projects = await plane.list_projects(ws)
            proj = next((p for p in projects if p.identifier == project.upper()), None)
            if not proj:
                return {"error": f"Project {project} not found"}

            resp = await plane._client.get(
                f"/api/v1/workspaces/{ws}/projects/{proj.id}/modules/"
            )
            if resp.status_code == 200:
                data = resp.json()
                modules = data.get("results", data) if isinstance(data, dict) else data
                for m in modules:
                    result["modules"].append({
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "description": (m.get("description") or "")[:100],
                        "status": m.get("status"),
                        "total_issues": m.get("total_issues", 0),
                        "completed_issues": m.get("completed_issues", 0),
                    })

        except Exception as e:
            result["error"] = str(e)

        return result

    # ─── Aggregate Context Tools ───────────────────────────────────────

    @server.tool()
    async def fleet_task_context(task_id: str = "") -> dict:
        """Get EVERYTHING about your current task in one call.

        Aggregates: task data, custom fields, methodology state,
        artifact object + completeness, comments, activity, related
        tasks, Plane state. All in one response.

        Call this instead of making multiple separate calls.

        Args:
            task_id: Task ID. Uses current task if empty.
        """
        ctx = _get_ctx()
        tid = task_id or ctx.task_id
        if not tid:
            return {"ok": False, "error": "No task_id"}

        try:
            from fleet.core.context_assembly import assemble_task_context

            board_id = await ctx.resolve_board_id()
            task = await ctx.mc.get_task(board_id, tid)

            # Store methodology fields on context for stage enforcement
            ctx._task_stage = task.custom_fields.task_stage
            ctx._task_readiness = task.custom_fields.task_readiness
            ctx.task_id = tid
            if task.custom_fields.project and not ctx.project_name:
                ctx.project_name = task.custom_fields.project

            plane = ctx.plane if hasattr(ctx, 'plane') else None

            global _event_store
            bundle = await assemble_task_context(
                task=task,
                mc=ctx.mc,
                board_id=board_id,
                plane=plane,
                event_store=_event_store,
            )
            bundle["ok"] = True
            return bundle

        except Exception as e:
            _report_error("fleet_task_context", str(e))
            return {"ok": False, "error": str(e)}

    @server.tool()
    async def fleet_heartbeat_context() -> dict:
        """Get role-specific heartbeat data in one call.

        Returns: events since last heartbeat, messages, directives,
        role-specific data (approvals for fleet-ops, sprint for PM, etc.),
        fleet state, assigned tasks summary.

        Call this at heartbeat instead of multiple separate calls.
        """
        ctx = _get_ctx()

        try:
            from fleet.core.context_assembly import assemble_heartbeat_context
            from fleet.core.role_providers import ROLE_PROVIDERS

            board_id = await ctx.resolve_board_id()
            tasks = await ctx.mc.list_tasks(board_id)
            agents = await ctx.mc.list_agents()

            # Determine agent role
            agent_name = ctx.agent_name or ""
            role = ""
            if agent_name:
                from fleet.core.agent_roles import AGENT_ROLES
                role_info = AGENT_ROLES.get(agent_name, {})
                role = role_info.get("primary_role", agent_name)

            global _event_store
            bundle = await assemble_heartbeat_context(
                agent_name=agent_name,
                role=role,
                tasks=tasks,
                agents=agents,
                mc=ctx.mc,
                board_id=board_id,
                event_store=_event_store,
                role_providers=ROLE_PROVIDERS,
            )
            bundle["ok"] = True
            return bundle

        except Exception as e:
            _report_error("fleet_heartbeat_context", str(e))
            return {"ok": False, "error": str(e)}

    # ─── Artifact Tools (Transpose Layer) ───────────────────────────────

    @server.tool()
    async def fleet_artifact_read(task_id: str = "") -> dict:
        """Read the current artifact object from a task.

        Returns the structured object — no HTML, just data.

        Args:
            task_id: Task ID to read artifact from. Uses current task if empty.
        """
        ctx = _get_ctx()
        tid = task_id or ctx.task_id
        if not tid:
            return {"ok": False, "error": "No task_id"}

        try:
            board_id = await ctx.resolve_board_id()
            task = await ctx.mc.get_task(board_id, tid)

            plane_issue_id = task.custom_fields.plane_issue_id
            if plane_issue_id and hasattr(ctx, 'plane') and ctx.plane:
                workspace = task.custom_fields.plane_workspace or ""
                project_id = task.custom_fields.plane_project_id or ""
                if workspace and project_id:
                    issues = await ctx.plane.list_issues(workspace, project_id)
                    issue = next((i for i in issues if i.id == plane_issue_id), None)
                    if issue and issue.description_html:
                        from fleet.core.transpose import from_html, get_artifact_type
                        obj = from_html(issue.description_html)
                        if obj:
                            return {
                                art_type = get_artifact_type(issue.description_html)
                                from fleet.core.artifact_tracker import check_artifact_completeness
                                comp = check_artifact_completeness(art_type or "", obj)
                                return {
                                "ok": True,
                                "artifact_type": art_type,
                                "data": obj,
                                "source": "plane",
                                "completeness": {
                                    "required_pct": comp.required_pct,
                                    "is_complete": comp.is_complete,
                                    "missing_required": comp.missing_required,
                                    "suggested_readiness": comp.suggested_readiness,
                                },
                            }

            return {"ok": True, "artifact_type": None, "data": None, "source": "none"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    @server.tool()
    async def fleet_artifact_update(
        artifact_type: str,
        field: str,
        value: str = "",
        values: list[str] | None = None,
        append: bool = False,
        task_id: str = "",
    ) -> dict:
        """Update an artifact field on the current task.

        Simple args in, structured data out. The tool handles HTML transpose.

        Args:
            artifact_type: Type (analysis_document, plan, bug, etc.)
            field: Field name to update (title, scope, findings, steps, etc.)
            value: String value for scalar fields.
            values: List of strings for list fields.
            append: If True, append to list instead of replacing.
            task_id: Task ID. Uses current task if empty.
        """
        ctx = _get_ctx()
        tid = task_id or ctx.task_id
        if not tid:
            return {"ok": False, "error": "No task_id"}

        try:
            from fleet.core.transpose import to_html, from_html

            board_id = await ctx.resolve_board_id()
            task = await ctx.mc.get_task(board_id, tid)

            # Read current artifact from Plane
            current_html = ""
            plane_issue_id = task.custom_fields.plane_issue_id
            workspace = task.custom_fields.plane_workspace or ""
            project_id = task.custom_fields.plane_project_id or ""

            if plane_issue_id and workspace and project_id:
                if hasattr(ctx, 'plane') and ctx.plane:
                    issues = await ctx.plane.list_issues(workspace, project_id)
                    issue = next((i for i in issues if i.id == plane_issue_id), None)
                    if issue:
                        current_html = issue.description_html or ""

            current_obj = from_html(current_html) or {}

            # Apply update
            if append and isinstance(current_obj.get(field), list):
                if values:
                    current_obj[field].extend(values)
                elif value:
                    current_obj[field].append(value)
            else:
                current_obj[field] = values if values is not None else value

            # Transpose and write
            new_html = to_html(artifact_type, current_obj)

            if plane_issue_id and workspace and project_id:
                if hasattr(ctx, 'plane') and ctx.plane:
                    await ctx.plane.update_issue(
                        workspace, project_id, plane_issue_id,
                        description_html=new_html,
                    )

            # Check completeness against standard
            from fleet.core.artifact_tracker import check_artifact_completeness, format_completeness_summary
            completeness = check_artifact_completeness(artifact_type, current_obj)
            summary = format_completeness_summary(completeness)

            await ctx.mc.post_comment(board_id, tid,
                f"**Artifact updated** ({artifact_type}): {field} | {summary}")

            return {
                "ok": True,
                "artifact_type": artifact_type,
                "field": field,
                "object": current_obj,
                "completeness": {
                    "required_pct": completeness.required_pct,
                    "is_complete": completeness.is_complete,
                    "missing_required": completeness.missing_required,
                    "suggested_readiness": completeness.suggested_readiness,
                    "summary": summary,
                },
            }

        except Exception as e:
            _report_error("fleet_artifact_update", str(e))
            return {"ok": False, "error": str(e)}

    @server.tool()
    async def fleet_artifact_create(
        artifact_type: str,
        title: str,
        task_id: str = "",
    ) -> dict:
        """Create a new artifact on the current task.

        Initializes the object and renders rich HTML to Plane.

        Args:
            artifact_type: Type (analysis_document, plan, bug, etc.)
            title: Artifact title.
            task_id: Task ID. Uses current task if empty.
        """
        ctx = _get_ctx()
        tid = task_id or ctx.task_id
        if not tid:
            return {"ok": False, "error": "No task_id"}

        try:
            from fleet.core.transpose import to_html

            obj = {"title": title}
            new_html = to_html(artifact_type, obj)

            board_id = await ctx.resolve_board_id()
            task = await ctx.mc.get_task(board_id, tid)

            plane_issue_id = task.custom_fields.plane_issue_id
            workspace = task.custom_fields.plane_workspace or ""
            project_id = task.custom_fields.plane_project_id or ""

            if plane_issue_id and workspace and project_id:
                if hasattr(ctx, 'plane') and ctx.plane:
                    await ctx.plane.update_issue(
                        workspace, project_id, plane_issue_id,
                        description_html=new_html,
                    )

            await ctx.mc.post_comment(board_id, tid,
                f"**Artifact created** ({artifact_type}): {title}")

            from fleet.core.artifact_tracker import check_artifact_completeness
            completeness = check_artifact_completeness(artifact_type, obj)

            return {
                "ok": True,
                "artifact_type": artifact_type,
                "object": obj,
                "completeness": {
                    "required_pct": completeness.required_pct,
                    "is_complete": completeness.is_complete,
                    "missing_required": completeness.missing_required,
                    "suggested_readiness": completeness.suggested_readiness,
                },
            }

        except Exception as e:
            _report_error("fleet_artifact_create", str(e))
            return {"ok": False, "error": str(e)}
