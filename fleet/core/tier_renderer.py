"""Tier-aware context renderer — controls depth of rendered sections.

Each capability tier defines HOW MUCH context to render for each section.
Preembed owns ORDER. TierRenderer owns DEPTH.

Tier profiles are loaded from config/tier-profiles.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from fleet.core.models import Task

# ─── Config path ────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "tier-profiles.yaml"


# ─── Tier profile loading ────────────────────────────────────────────────────


def load_tier_rules(tier: str) -> dict:
    """Load depth rules for a capability tier.

    Handles the ``extends`` keyword — child overrides are merged on top of
    the base tier.  ``description`` is stripped from the returned dict.

    Falls back to ``expert`` if the requested tier is unknown.

    Args:
        tier: Tier name (expert, capable, flagship_local, lightweight, …)

    Returns:
        Dict of depth rule keys → values (no ``description`` key).
    """
    with open(_CONFIG_PATH, "r") as fh:
        profiles: dict = yaml.safe_load(fh)

    def _resolve(name: str, visited: set | None = None) -> dict:
        if visited is None:
            visited = set()
        if name not in profiles:
            # Unknown tier → fall back to expert
            name = "expert"
        if name in visited:
            # Cycle guard
            return {}
        visited.add(name)

        raw = dict(profiles[name])
        base_name = raw.pop("extends", None)
        raw.pop("description", None)

        if base_name:
            base = _resolve(base_name, visited)
            merged = dict(base)
            merged.update(raw)
            return merged

        return raw

    return _resolve(tier)


# ─── TierRenderer ────────────────────────────────────────────────────────────


class TierRenderer:
    """Render context sections at the depth appropriate for a capability tier."""

    def __init__(self, tier: str = "expert") -> None:
        self.tier = tier
        self.rules = load_tier_rules(tier)

    # ── Role data ────────────────────────────────────────────────────────────

    def format_role_data(self, role: str, data: dict) -> str:
        """Format role-specific data block, eliminating raw dict rendering.

        Fixes F1-F4.  Returns "" if data is empty.  Always starts with
        ``## ROLE DATA`` header when data is present.

        Depth rules (role_data):
            full_formatted   — all items shown (limit 5)
            counts_plus_top5 — counts + top 5 items
            counts_plus_top3 — counts + top 3 items
            counts_only      — just the counts, no item lists
        """
        if not data:
            return ""

        depth = self.rules.get("role_data", "full_formatted")

        # Determine item limit based on depth rule
        if depth == "counts_only":
            item_limit = 0
        elif depth == "counts_plus_top3":
            item_limit = 3
        elif depth == "counts_plus_top5":
            item_limit = 5
        else:
            # full_formatted
            item_limit = 5

        lines: list[str] = ["## ROLE DATA"]

        if role == "fleet-ops":
            lines.extend(self._render_fleet_ops(data, item_limit))
        elif role == "project-manager":
            lines.extend(self._render_pm(data, item_limit))
        elif role == "architect":
            lines.extend(self._render_architect(data, item_limit))
        elif role == "devsecops-expert":
            lines.extend(self._render_devsecops(data, item_limit))
        else:
            lines.extend(self._render_worker(data, item_limit))

        return "\n".join(lines)

    def _render_fleet_ops(self, data: dict, item_limit: int) -> list[str]:
        lines: list[str] = []
        if "pending_approvals" in data:
            lines.append(f"**Pending approvals:** {data['pending_approvals']}")
            if item_limit > 0 and "approval_details" in data:
                details = data["approval_details"][:item_limit]
                for d in details:
                    lines.append(
                        f"- {d.get('id', '?')}: task {d.get('task_id', '?')} ({d.get('status', '?')})"
                    )
        if "review_queue" in data:
            queue = data["review_queue"]
            lines.append(f"**Review queue:** {len(queue)}")
            if item_limit > 0:
                for item in queue[:item_limit]:
                    lines.append(
                        f"- {item.get('id', '?')}: {item.get('title', '?')} ({item.get('agent', '?')})"
                    )
        if "offline_agents" in data:
            agents = data["offline_agents"]
            if isinstance(agents, list):
                lines.append(f"**Offline agents:** {', '.join(agents)}")
            else:
                lines.append(f"**Offline agents:** {agents}")
        return lines

    def _render_pm(self, data: dict, item_limit: int) -> list[str]:
        lines: list[str] = []
        if "unassigned_tasks" in data:
            lines.append(f"**Unassigned tasks:** {data['unassigned_tasks']}")
            if item_limit > 0 and "unassigned_details" in data:
                details = data["unassigned_details"][:item_limit]
                for d in details:
                    lines.append(
                        f"- {d.get('id', '?')}: {d.get('title', '?')} ({d.get('priority', '?')})"
                    )
        if "blocked_tasks" in data:
            lines.append(f"**Blocked tasks:** {data['blocked_tasks']}")
        if "progress" in data:
            lines.append(f"**Progress:** {data['progress']}")
        if "inbox_count" in data:
            lines.append(f"**Inbox:** {data['inbox_count']}")
        return lines

    def _render_architect(self, data: dict, item_limit: int) -> list[str]:
        lines: list[str] = []
        if "design_tasks" in data:
            tasks = data["design_tasks"]
            lines.append(f"**Design tasks:** {len(tasks)}")
            if item_limit > 0:
                for t in tasks[:item_limit]:
                    lines.append(
                        f"- {t.get('id', '?')}: {t.get('title', '?')} ({t.get('stage', '?')})"
                    )
        if "high_complexity" in data:
            hc = data["high_complexity"]
            lines.append(f"**High complexity:** {len(hc)}")
            if item_limit > 0:
                for t in hc[:item_limit]:
                    lines.append(
                        f"- {t.get('id', '?')}: {t.get('title', '?')}"
                    )
        return lines

    def _render_devsecops(self, data: dict, item_limit: int) -> list[str]:
        lines: list[str] = []
        if "security_tasks" in data:
            tasks = data["security_tasks"]
            lines.append(f"**Security tasks:** {len(tasks)}")
            if item_limit > 0:
                for t in tasks[:item_limit]:
                    lines.append(
                        f"- {t.get('id', '?')}: {t.get('title', '?')}"
                    )
        if "prs_needing_security_review" in data:
            prs = data["prs_needing_security_review"]
            lines.append(f"**PRs needing security review:** {len(prs)}")
            if item_limit > 0:
                for pr in prs[:item_limit]:
                    url = pr.get("pr") or pr.get("pr_url") or pr.get("url", "?")
                    lines.append(
                        f"- {pr.get('id', '?')}: {pr.get('title', '?')} — {url}"
                    )
        return lines

    def _render_worker(self, data: dict, item_limit: int) -> list[str]:
        lines: list[str] = []
        if "my_tasks_count" in data:
            lines.append(f"**My tasks:** {data['my_tasks_count']}")
        if "contribution_tasks" in data:
            ctasks = data["contribution_tasks"]
            lines.append(f"**Contribution tasks:** {len(ctasks)}")
            if item_limit > 0:
                for ct in ctasks[:item_limit]:
                    lines.append(
                        f"- Contribute {ct.get('type', '?')} for: {ct.get('title', '?')}"
                    )
        if "contributions_received" in data:
            received = data["contributions_received"]
            # role_providers returns dict keyed by task short ID:
            #   {'task-a1b': [{'type': 'design_input', 'from': 'architect', 'status': 'done'}]}
            # OR a flat list (from test fixtures). Handle both.
            if isinstance(received, dict):
                total = sum(len(v) for v in received.values())
                lines.append(f"**Contributions received:** {total}")
                if item_limit > 0:
                    for task_id, contribs in list(received.items())[:item_limit]:
                        parts = [f"{c.get('type', '?')} ({c.get('from', '?')}, {c.get('status', '?')})" for c in contribs]
                        lines.append(f"- {task_id}: {', '.join(parts)}")
            else:
                lines.append(f"**Contributions received:** {len(received)}")
                if item_limit > 0:
                    for cr in received[:item_limit]:
                        ctype = cr.get("type", "?")
                        cfrom = cr.get("from", "?")
                        cstatus = cr.get("status", "?")
                        lines.append(f"- {ctype} ({cfrom}, {cstatus})")
        if "in_review" in data:
            in_review = data["in_review"]
            lines.append(f"**In review:** {len(in_review)}")
            if item_limit > 0:
                for item in in_review[:item_limit]:
                    pr = item.get("pr_url") or item.get("pr", "")
                    lines.append(
                        f"- {item.get('id', '?')}: {item.get('title', '?')}"
                        + (f" — {pr}" if pr else "")
                    )
        return lines

    # ── Rejection context ────────────────────────────────────────────────────

    def format_rejection_context(self, iteration: int, feedback: str) -> str:
        """Format rejection/rework context block.

        Fixes H11/H12.  Returns "" if iteration <= 1.

        Args:
            iteration: Current attempt number (labor_iteration).
            feedback:  Feedback text from the reviewer.

        Returns:
            Formatted markdown section, or "".
        """
        if iteration <= 1:
            return ""

        lines: list[str] = [
            f"## REJECTION REWORK (iteration {iteration})",
            "",
            "Your previous submission was rejected. Fix the ROOT CAUSE — do not paper over it.",
            "Use `eng_fix_task_response()` to structure your fix.",
            "",
            "**Feedback:**",
            f"> {feedback}",
        ]

        if iteration >= 3:
            lines += [
                "",
                "WARNING: You are on iteration 3+. If this submission is also rejected, "
                "the task will be escalated to a human for intervention.",
            ]

        return "\n".join(lines)

    # ── Action directive ─────────────────────────────────────────────────────

    def format_action_directive(
        self, stage: str, progress: int, iteration: int
    ) -> str:
        """Format the action directive for the current task state.

        Fixes J1.  Adapts directive to stage/progress/iteration.

        Respects action_directive rule:
            full     — full directive text
            one_line — first sentence only

        Args:
            stage:     Current methodology stage (work, reasoning, etc.)
            progress:  task_progress value (0-100).
            iteration: labor_iteration (>=2 triggers rework directive).

        Returns:
            Formatted directive string.
        """
        depth = self.rules.get("action_directive", "full")

        directive = self._compute_action_directive(stage, progress, iteration)

        if depth == "one_line":
            # Return just the first sentence
            first = directive.split(".")[0]
            return first.strip() + "."

        return directive

    def _compute_action_directive(
        self, stage: str, progress: int, iteration: int
    ) -> str:
        # Rework overrides everything in work stage
        if stage == "work" and iteration >= 2:
            return (
                "REWORK required. Fix the root cause identified in the rejection feedback. "
                "Use `eng_fix_task_response()` to structure your approach, then implement the fix."
            )

        if stage == "work":
            if progress == 0:
                return (
                    "Starting work. `fleet_task_accept()` with your plan first, then implement."
                )
            elif progress < 50:
                return (
                    "Continue implementation. `fleet_commit()` per logical change."
                )
            elif progress < 70:
                return (
                    "Halfway. Continue implementation. Post progress update via `fleet_task_progress()`."
                )
            elif progress < 80:
                return (
                    "Implementation done. Run tests. Prepare for `fleet_task_complete()`."
                )
            elif progress < 90:
                return (
                    "Challenged. Address challenge findings before completing."
                )
            else:
                return (
                    "Reviewed. Final polish, then `fleet_task_complete()`."
                )

        # Non-work stages — each directive includes WHERE the artifact goes
        stage_directives: dict[str, str] = {
            "conversation": (
                "Ask clarifying questions. Post them to the task comments. "
                "Do NOT write code. Your job is to understand, not to build."
            ),
            "analysis": (
                "Examine the codebase. Produce an analysis document in wiki/domains/ "
                "with file and line references. Do NOT produce solutions yet."
            ),
            "investigation": (
                "Research options. Explore multiple approaches. "
                "Produce an investigation document in wiki/domains/ with findings and tradeoffs."
            ),
            "reasoning": (
                "Produce a plan in docs/superpowers/plans/ or as a task comment. "
                "Reference the verbatim requirement explicitly. "
                "Use `fleet_task_accept()` to submit for PO confirmation."
            ),
        }

        return stage_directives.get(
            stage,
            f"Follow the {stage} protocol. Complete the required deliverable for this stage.",
        )

    # ── Events ───────────────────────────────────────────────────────────────

    def format_events(self, events: list) -> str:
        """Format the events-since-last-heartbeat section.

        Fixes A5 (events always present even when empty).

        Depth rules (events_limit):
            0       — count only or "None."
            N > 0   — formatted list, "+N more" if truncated

        Always returns a section with the header.

        Args:
            events: List of event dicts (type, agent, summary, time).

        Returns:
            Formatted section string.
        """
        limit = self.rules.get("events_limit", 10)
        lines: list[str] = ["## EVENTS SINCE LAST HEARTBEAT"]

        if not events:
            lines.append("None.")
            return "\n".join(lines)

        if limit == 0:
            lines.append(f"{len(events)} events. Call fleet_read_context for details.")
            return "\n".join(lines)

        shown = events[:limit]
        for ev in shown:
            etype = ev.get("type", "?")
            agent = ev.get("agent", "?")
            summary = ev.get("summary", "")
            time = ev.get("time", "")
            line = f"- [{time}] {etype} ({agent}): {summary}"
            lines.append(line)

        remaining = len(events) - len(shown)
        if remaining > 0:
            lines.append(f"+{remaining} more")

        return "\n".join(lines)

    # ── Contribution task context ─────────────────────────────────────────────

    def format_contribution_task_context(
        self,
        contribution_type: str,
        contribution_target: str,
        target_task: Optional[Task] = None,
    ) -> str:
        """Format contribution task context block.

        Fixes I1/I2/I3.  Returns "" if no contribution_type.

        Args:
            contribution_type:   What kind of contribution (qa_test_def, design_input, …).
            contribution_target: Target task ID this contribution is for.
            target_task:         Loaded Task object for the target (optional).

        Returns:
            Formatted section or "".
        """
        if not contribution_type:
            return ""

        short_target = contribution_target[:8] if contribution_target else "unknown"

        lines: list[str] = [
            "## CONTRIBUTION TASK",
            f"**Type:** {contribution_type}",
            f"**Target task:** {short_target}",
        ]

        if target_task is not None:
            lines.append(f"**Title:** {target_task.title}")
            cf = target_task.custom_fields
            if cf.requirement_verbatim:
                lines.append(f"**Verbatim:** {cf.requirement_verbatim}")
            if cf.delivery_phase:
                lines.append(f"**Delivery phase:** {cf.delivery_phase}")
            if cf.task_stage:
                lines.append(f"**Stage:** {cf.task_stage}")

        lines += [
            "",
            "Call `fleet_contribute()` when your contribution is ready.",
        ]

        return "\n".join(lines)

    # ── Stage protocol ───────────────────────────────────────────────────────

    def format_stage_protocol(self, stage: str, role: str, iteration: int = 1) -> str:
        """Format the stage protocol with role-specific and iteration-aware language.

        Fixes I5 (role-specific reasoning) and BUG-03 (rework protocol confusion).

        Args:
            stage: Methodology stage name.
            role:  Agent role name.
            iteration: labor_iteration (>=2 adapts work protocol for rework).

        Returns:
            Protocol text (possibly role-adapted and iteration-adapted).
        """
        from fleet.core.stage_context import get_stage_instructions

        protocol = get_stage_instructions(stage)

        # Work stage + rework: replace "Execute the confirmed plan" with fix-oriented language
        if stage == "work" and iteration >= 2:
            protocol = protocol.replace(
                "Execute the confirmed plan. Stay in scope.",
                "Fix the rejected work. Address the ROOT CAUSE identified in rejection feedback.",
            )
            protocol = protocol.replace(
                "Execute the plan confirmed in reasoning stage",
                "Fix the specific issues from the rejection feedback",
            )
            protocol = protocol.replace(
                "Consume all contributions before implementing",
                "Re-read contributions and rejection feedback before fixing",
            )
            return protocol

        if stage != "reasoning":
            return protocol

        # Role-specific reasoning outputs
        role_outputs: dict[str, str] = {
            "software-engineer": (
                "implementation plan with target files and acceptance criteria mapping"
            ),
            "architect": (
                "design_input: approach, target files, patterns, constraints, integration points"
            ),
            "qa-engineer": (
                "qa_test_definition: TC-XXX structured test criteria with priority and type"
            ),
            "devsecops-expert": (
                "security_requirement: threat model, required controls, compliance needs"
            ),
            "ux-designer": (
                "ux_spec: all states, all interactions, accessibility, all UX levels"
            ),
            "technical-writer": (
                "documentation_outline: audience, structure, scope"
            ),
            "devops": (
                "infrastructure plan: deployment architecture, scaling strategy, monitoring"
            ),
            "fleet-ops": (
                "review assessment: requirements coverage, compliance check"
            ),
            "project-manager": (
                "task breakdown: subtasks with dependencies, assignments, estimates"
            ),
            "accountability-generator": (
                "compliance report: trail verification, methodology compliance"
            ),
        }

        role_plan_text: dict[str, str] = {
            "software-engineer": (
                "Implementation plans with target files and acceptance criteria mapping"
            ),
            "architect": (
                "Design inputs with approach, patterns, constraints, and integration points"
            ),
            "qa-engineer": (
                "QA test definitions structured as TC-XXX with priority and type"
            ),
            "devsecops-expert": (
                "Security requirements with threat model and required controls"
            ),
            "ux-designer": (
                "UX specs covering all states, interactions, and accessibility"
            ),
            "technical-writer": (
                "Documentation outlines with audience, structure, and scope"
            ),
            "devops": (
                "Infrastructure plans with deployment architecture and scaling strategy"
            ),
            "fleet-ops": (
                "Review assessments covering requirements and compliance"
            ),
            "project-manager": (
                "Task breakdowns with subtasks, dependencies, and estimates"
            ),
            "accountability-generator": (
                "Compliance reports with trail verification and methodology compliance"
            ),
        }

        output_desc = role_outputs.get(role, "implementation plan")
        plan_text = role_plan_text.get(
            role, "Implementation plans with specific file/component references"
        )

        protocol = protocol.replace(
            "Produce a plan (docs/superpowers/plans/ or task comment — temporary execution artifact)",
            f"Produce a {output_desc}",
        )
        protocol = protocol.replace(
            "Implementation plans with specific file/component references",
            plan_text,
        )

        return protocol
