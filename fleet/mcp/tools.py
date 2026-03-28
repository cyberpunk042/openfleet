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


def _get_ctx() -> FleetMCPContext:
    """Get or create the shared context."""
    global _ctx
    if _ctx is None:
        _ctx = FleetMCPContext.from_env()
    return _ctx


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
            except Exception as e:
                result["task"] = {"id": ctx.task_id, "error": str(e)}

        if ctx.project_name:
            urls = ctx.urls.resolve(project=ctx.project_name, task_id=ctx.task_id)
            result["urls"] = {"task": urls.task or "", "board": urls.board or ""}

        try:
            memory = await ctx.mc.list_memory(board_id, limit=10)
            result["recent_memory"] = [
                {"content": m.content[:200], "tags": m.tags, "source": m.source}
                for m in memory
            ]
        except Exception:
            result["recent_memory"] = []

        return result

    @server.tool()
    async def fleet_task_accept(plan: str, task_id: str = "") -> dict:
        """Accept and start working on your assigned task.

        Args:
            plan: Brief description of your approach (1-2 sentences).
            task_id: Task ID (if not already set via fleet_read_context).
        """
        ctx = _get_ctx()
        if task_id:
            ctx.task_id = task_id
        if not ctx.task_id:
            return {"ok": False, "error": "No task_id. Call fleet_read_context first."}

        board_id = await ctx.resolve_board_id()

        comment = comment_tmpl.format_accept(plan, ctx.agent_name or "agent")

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

        return {"ok": True, "status": "in_progress", "task_url": task_url}

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

        # Create approval for quality gate
        try:
            await ctx.mc.create_approval(
                board_id,
                task_ids=[ctx.task_id],
                action_type="task_completion",
                confidence=85.0,  # Agent self-assessment default
                rubric_scores={
                    "correctness": 85,
                    "completeness": 85,
                    "quality": 85,
                },
                reason=(
                    f"Task completed by {agent_name}. "
                    f"PR: {pr.url}. "
                    f"{len(commits)} commit(s), {len(diff_stat)} file(s) changed. "
                    f"Summary: {summary[:200]}"
                ),
            )
        except Exception:
            pass  # Approval creation is best-effort

        # IRC notifications using templates
        try:
            await ctx.irc.notify(
                "#fleet", irc_tmpl.format_pr_ready(agent_name, task_title, pr.url)
            )
            await ctx.irc.notify(
                "#reviews", irc_tmpl.format_pr_review(agent_name, task_title, pr.url)
            )
        except Exception:
            pass

        # Board memory using templates
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
    ) -> dict:
        """Approve or reject a pending task completion.

        Use this to process approvals in the review queue.
        fleet-ops and PM should use this during heartbeats.

        Args:
            approval_id: The approval ID to act on.
            decision: "approved" or "rejected".
            comment: Optional comment explaining the decision.
        """
        ctx = _get_ctx()
        board_id = await ctx.resolve_board_id()

        if decision not in ("approved", "rejected"):
            return {"ok": False, "error": "decision must be 'approved' or 'rejected'"}

        try:
            approval = await ctx.mc.approve_approval(
                board_id, approval_id, status=decision, comment=comment,
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

        emoji = "\u2705" if decision == "approved" else "\u274c"
        try:
            await ctx.irc.notify(
                "#fleet",
                irc_tmpl.format_event(
                    ctx.agent_name or "agent",
                    f"{emoji} {decision.upper()}",
                    f"approval {approval_id[:8]}",
                ),
            )
        except Exception:
            pass

        return {"ok": True, "approval_id": approval.id, "status": approval.status}

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