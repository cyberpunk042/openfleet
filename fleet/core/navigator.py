"""Navigator — the autocomplete web core.

Reads the knowledge map metadata (intent-map.yaml, injection-profiles.yaml,
cross-references.yaml) and assembles focused context for each agent based on
their role, current stage, task, and model capacity.

The navigator is the brain that turns static knowledge into dynamic context.
It answers: "What does THIS agent need to know RIGHT NOW?"

Three data sources:
1. Knowledge map (static) — KB entries, manuals, metadata files
2. LightRAG (graph) — entity-relationship queries across the knowledge web
3. Claude-mem (memory) — per-agent cross-session observations

Flow:
    Navigator.assemble(role, stage, task, model)
    → reads intent-map.yaml for injection recipe
    → reads injection-profiles.yaml for depth level
    → loads content from KB/manuals at the right depth
    → queries LightRAG for task-relevant graph context
    → returns assembled context string for injection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Knowledge map root — relative to fleet repo
KNOWLEDGE_MAP_DIR = Path(__file__).parent.parent.parent / "docs" / "knowledge-map"
KB_DIR = KNOWLEDGE_MAP_DIR / "kb"


@dataclass
class InjectionProfile:
    """How much content to inject per branch for a given context tier."""

    name: str
    context_budget: int  # approximate token budget
    levels: dict[str, str] = field(default_factory=dict)
    # levels maps branch → depth: "full", "condensed", "minimal", "names_only", "none"


@dataclass
class Intent:
    """What to inject for a specific role+stage combination."""

    name: str
    inject: list[dict] = field(default_factory=list)
    # Each inject item: {branch: content_ref} or {note: reminder}


@dataclass
class NavigatorContext:
    """Assembled context ready for injection."""

    role: str
    stage: str
    model: str
    sections: list[str] = field(default_factory=list)
    token_estimate: int = 0

    def render(self) -> str:
        """Render all sections into a single context string."""
        return "\n\n".join(s for s in self.sections if s)


class Navigator:
    """The autocomplete web — reads maps, finds paths, assembles context.

    Usage:
        nav = Navigator()
        ctx = nav.assemble(role="architect", stage="reasoning", model="opus-4-6")
        # ctx.render() → focused context string for injection
    """

    def __init__(self):
        self._intent_map: dict = {}
        self._profiles: dict[str, InjectionProfile] = {}
        self._cross_refs: dict = {}
        self._loaded = False
        self._file_cache: dict[str, str] = {}  # path → content

    def load(self) -> None:
        """Load metadata files from knowledge map. Caches file reads."""
        self._intent_map = self._load_yaml("intent-map.yaml")
        self._profiles = self._parse_profiles(self._load_yaml("injection-profiles.yaml"))
        self._cross_refs = self._load_yaml("cross-references.yaml")
        self._file_cache.clear()
        self._loaded = True
        logger.info("Navigator loaded: %d intents, %d profiles",
                     len(self._intent_map.get("intents", {})),
                     len(self._profiles))

    def reload(self) -> None:
        """Force reload — clears cache and re-reads all metadata."""
        self._loaded = False
        self.load()

    def assemble(
        self,
        role: str,
        stage: str,
        model: str = "opus-4-6",
        task_context: Optional[str] = None,
    ) -> NavigatorContext:
        """Assemble focused context for an agent.

        This is the core autocomplete function. Given WHO (role),
        WHAT (stage), and HOW MUCH (model) — returns the right content.

        Args:
            role: Agent role (architect, software-engineer, fleet-ops, etc.)
            stage: Methodology stage (conversation, reasoning, work, etc.)
            model: Model ID for profile selection.
            task_context: Optional task description for graph queries.

        Returns:
            NavigatorContext with assembled sections ready for injection.
        """
        if not self._loaded:
            self.load()

        ctx = NavigatorContext(role=role, stage=stage, model=model)

        # 1. Select injection profile based on model
        profile = self._select_profile(model)

        # 2. Find intent for this role+stage
        intent = self._find_intent(role, stage)

        # 3. Assemble content per branch at the profile's depth
        if intent:
            self._assemble_from_intent(ctx, intent, profile, role)
        else:
            # No specific intent — use profile defaults
            self._assemble_defaults(ctx, role, profile)

        # 4. Enrich with cross-references (tool → system connections)
        if intent and profile.name in ("opus-1m", "sonnet-200k"):
            xref_context = self._enrich_from_crossrefs(intent, profile)
            if xref_context:
                ctx.sections.append(xref_context)

        # 5. Query LightRAG for task-relevant graph context
        if task_context and profile.name != "heartbeat":
            graph_context = self._query_graph(task_context, role, profile)
            if graph_context:
                ctx.sections.append(graph_context)

        # 6. Enforce gateway character limit (8000 chars per context file)
        self._enforce_limit(ctx, max_chars=7500)  # margin for separators + gateway overhead

        return ctx

    def _enforce_limit(self, ctx: NavigatorContext, max_chars: int = 7500) -> None:
        """Drop lowest-priority sections to fit gateway's per-file limit.

        NEVER hard-cuts mid-section — broken text confuses the AI.
        Drops entire sections from the end (lowest priority) until
        the total fits. Priority order: agent manual + methodology
        (highest) are preserved over graph context + notes (lowest).
        """
        def _total() -> int:
            seps = max(0, len(ctx.sections) - 1) * 2
            return sum(len(s) for s in ctx.sections) + seps

        while ctx.sections and _total() > max_chars:
            ctx.sections.pop()

    # ── Profile selection ──────────────────────────────────────────

    def _select_profile(self, model: str) -> InjectionProfile:
        """Select injection profile based on model."""
        selection_rules = self._intent_map.get("profiles", {})

        # Direct match
        if "opus" in model and "1m" in model:
            return self._profiles.get("opus-1m", self._default_profile())
        if "opus" in model:
            return self._profiles.get("opus-1m", self._default_profile())
        if "sonnet" in model:
            return self._profiles.get("sonnet-200k", self._default_profile())
        if "hermes" in model or "qwen" in model or "phi" in model:
            return self._profiles.get("localai-8k", self._default_profile())

        # Default to sonnet profile (safe)
        return self._profiles.get("sonnet-200k", self._default_profile())

    def _default_profile(self) -> InjectionProfile:
        return InjectionProfile(name="default", context_budget=15000, levels={})

    # ── Intent lookup ──────────────────────────────────────────────

    def _find_intent(self, role: str, stage: str) -> Optional[Intent]:
        """Find the intent for a role+stage combination."""
        intents = self._intent_map.get("intents", {})

        role_short = self._role_short(role)

        # Try exact match: "architect-reasoning", "engineer-work"
        key = f"{role_short}-{stage}"
        if key in intents:
            return Intent(name=key, inject=intents[key].get("inject", []))

        # Try compound stages: "writer-heartbeat-autonomous"
        for intent_key in intents:
            if intent_key.startswith(f"{role_short}-") and stage in intent_key:
                return Intent(name=intent_key, inject=intents[intent_key].get("inject", []))

        return None

    def _role_short(self, role: str) -> str:
        """Map agent role names to intent-map keys."""
        mapping = {
            "architect": "architect",
            "software-engineer": "engineer",
            "qa-engineer": "qa",
            "devops": "devops",
            "devsecops-expert": "devsecops",
            "fleet-ops": "fleet-ops",
            "project-manager": "pm",
            "technical-writer": "writer",
            "ux-designer": "ux",
            "accountability-generator": "accountability",
        }
        return mapping.get(role, role)

    # ── Content assembly ───────────────────────────────────────────

    def _assemble_from_intent(
        self,
        ctx: NavigatorContext,
        intent: Intent,
        profile: InjectionProfile,
        role: str = "",
    ) -> None:
        """Assemble context from an intent's injection recipe."""
        # Always inject agent manual if profile allows — even if intent doesn't list it
        has_agent_manual = any(
            isinstance(item, dict) and "agent_manual" in item
            for item in intent.inject
        )
        if not has_agent_manual:
            level = profile.levels.get("agent_manual", "none")
            if level != "none":
                content = self._load_agent_manual(role, level)
                if content:
                    ctx.sections.append(content)

        for item in intent.inject:
            if isinstance(item, str):
                # Simple string reference — try to parse as "branch: ref"
                if ":" in item:
                    branch, ref = item.split(":", 1)
                    branch = branch.strip()
                    ref = self._strip_annotation(ref.strip())
                else:
                    continue
            elif isinstance(item, dict):
                # Dict item — normal case
                for branch, ref in item.items():
                    branch = branch.strip()
                    break
                else:
                    continue
            else:
                continue

            if branch == "note":
                ctx.sections.append(f"**Note:** {ref}")
                continue

            # Strip parenthetical annotations from ref
            if isinstance(ref, str):
                ref = self._strip_annotation(ref)

            level = profile.levels.get(branch, "none")
            if level == "none":
                continue

            content = self._load_branch_content(branch, ref, level)
            if content:
                ctx.sections.append(content)

    def _strip_annotation(self, ref: str) -> str:
        """Strip parenthetical annotation from a ref value.

        'pm (mission + tools + rules)' → 'pm'
        'conversation (MUST/MUST NOT)' → 'conversation'
        'none (PM doesn't receive contributions)' → 'none'
        """
        if "(" in ref:
            return ref[:ref.index("(")].strip()
        return ref

    def _assemble_defaults(
        self,
        ctx: NavigatorContext,
        role: str,
        profile: InjectionProfile,
    ) -> None:
        """Assemble default context when no specific intent matches."""
        # Always inject agent manual at profile depth
        level = profile.levels.get("agent_manual", "none")
        if level != "none":
            content = self._load_agent_manual(role, level)
            if content:
                ctx.sections.append(content)

        # Always inject methodology at profile depth
        level = profile.levels.get("methodology", "none")
        if level != "none":
            content = self._load_methodology(level)
            if content:
                ctx.sections.append(content)

    def _load_branch_content(self, branch: str, ref: str, level: str) -> Optional[str]:
        """Load content from a knowledge map branch at specified depth."""
        if branch == "agent_manual":
            return self._load_agent_manual(ref, level)
        elif branch == "methodology":
            return self._load_methodology(level, stage=ref if isinstance(ref, str) else None)
        elif branch == "standards":
            return self._load_standards(ref, level)
        elif branch == "skills":
            return self._load_skills(ref, level)
        elif branch == "commands":
            return self._load_commands(ref, level)
        elif branch == "tools":
            return self._load_tools(ref, level)
        elif branch == "system_manuals":
            return self._load_system_manuals(ref, level)
        elif branch == "plugins":
            return self._load_plugins(ref, level)
        elif branch == "mcp":
            return self._load_mcp(ref, level)
        elif branch == "contributions":
            return self._load_contributions(ref, level)
        elif branch == "context_awareness":
            return self._load_context_awareness(ref, level)
        elif branch == "trail":
            return self._load_trail(ref, level)
        elif branch == "target_task":
            return self._load_target_task(ref, level)
        elif branch in ("fleet_state", "role_data", "directives", "messages",
                         "tasks", "health", "challenge", "predefined_criteria"):
            # Dynamic data — comes from fleet-context.md/task-context.md, not navigator
            return None

        return None

    # ── Branch loaders ─────────────────────────────────────────────

    def _load_agent_manual(self, role: str, level: str) -> Optional[str]:
        """Load agent manual section."""
        path = KNOWLEDGE_MAP_DIR / "agent-manuals.md"
        if not path.exists():
            return None

        content = self._read_file(path)
        if not content:
            return None

        # Map short role names to how they appear in agent-manuals.md headers
        manual_names = {
            "pm": "Project Manager",
            "fleet-ops": "Fleet-Ops",
            "architect": "Architect",
            "devsecops": "DevSecOps",
            "engineer": "Software Engineer",
            "devops": "DevOps",
            "qa": "QA Engineer",
            "writer": "Technical Writer",
            "ux": "UX Designer",
            "accountability": "Accountability Generator",
            # Also handle full role names from agent-tooling.yaml
            "project-manager": "Project Manager",
            "software-engineer": "Software Engineer",
            "qa-engineer": "QA Engineer",
            "devsecops-expert": "DevSecOps",
            "technical-writer": "Technical Writer",
            "ux-designer": "UX Designer",
            "accountability-generator": "Accountability Generator",
        }

        search_name = manual_names.get(role, role).lower()

        # Find the section for this role
        sections = content.split("\n## ")
        for section in sections:
            header = section.split("\n")[0].lower()
            if search_name in header:
                if level == "full":
                    return f"## {section}"
                elif level == "condensed":
                    lines = section.strip().split("\n")
                    return "## " + "\n".join(lines[:10])
                elif level == "minimal":
                    first_line = section.strip().split("\n")[0]
                    return f"You are {first_line.strip()}"
        return None

    def _load_methodology(self, level: str, stage: Optional[str] = None) -> Optional[str]:
        """Load methodology manual section."""
        path = KNOWLEDGE_MAP_DIR / "methodology-manual.md"
        if not path.exists():
            return None

        content = self._read_file(path)
        if not content:
            return None

        if stage and level in ("full", "stage_only"):
            # Find the section for this stage
            sections = content.split("\n## ")
            for section in sections:
                if stage.lower() in section.lower().split("\n")[0].lower():
                    if level == "full":
                        return f"## {section}"
                    elif level == "stage_only":
                        # MUST/MUST NOT lines only
                        lines = section.strip().split("\n")
                        must_lines = [l for l in lines if "MUST" in l or "must" in l.lower()]
                        stage_name = lines[0].strip()
                        return f"Stage: {stage_name}\n" + "\n".join(must_lines)
            return None

        if level == "full":
            return content
        return None

    def _load_standards(self, ref, level: str) -> Optional[str]:
        """Load standards manual section — specific standards, not entire manual."""
        path = KNOWLEDGE_MAP_DIR / "standards-manual.md"
        if not path.exists():
            return None
        if level == "none":
            return None

        content = self._read_file(path)
        if not content:
            return None
        sections = content.split("\n## ")

        # If ref is a list of specific standards, load only those
        if isinstance(ref, list):
            results = []
            for standard in ref:
                standard_clean = self._strip_annotation(str(standard)) if isinstance(standard, str) else str(standard)
                for section in sections:
                    header = section.split("\n")[0].lower()
                    if standard_clean.lower().replace("_", " ") in header or standard_clean.lower() in header:
                        if level == "full":
                            results.append(f"## {section.strip()}")
                        elif level == "required_fields":
                            results.append(f"## {section.split(chr(10))[0]}")
                            for line in section.split("\n"):
                                if line.strip().startswith("- ") and ":" in line:
                                    results.append(line)
                        break
            return "\n\n".join(results) if results else None

        # If ref is a string (single standard or "full")
        if isinstance(ref, str):
            ref_clean = self._strip_annotation(ref)
            if ref_clean == "full" or level == "full":
                # Still don't load entire manual — load methodology-relevant sections
                return None
            for section in sections:
                if ref_clean.lower() in section.lower().split("\n")[0].lower():
                    return f"## {section.strip()}"

        return None

    def _load_skills(self, ref, level: str) -> Optional[str]:
        """Load skills for injection."""
        if level == "none":
            return None

        if isinstance(ref, list):
            if level == "full_descriptions":
                lines = ["## Available Skills"]
                for skill_name in ref:
                    skill_path = KB_DIR / "skills" / f"{skill_name}.md"
                    if skill_path.exists():
                        content = self._read_file(skill_path)
                        # Extract Purpose section content
                        desc = self._extract_section(content, "Purpose")
                        if not desc:
                            desc = self._extract_section(content, "What It Does")
                        if not desc:
                            # Fallback: first non-metadata paragraph
                            for para in content.split("\n\n"):
                                if not para.startswith("#") and not para.startswith("**"):
                                    desc = para.strip()[:200]
                                    break
                        lines.append(f"- **/{skill_name}**: {desc[:200] if desc else ''}")
                    else:
                        lines.append(f"- **/{skill_name}**")
                return "\n".join(lines)
            elif level == "names_only":
                return "Available skills: " + ", ".join(f"/{s}" for s in ref)
        return None

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content from a ## section by name."""
        sections = content.split("\n## ")
        for section in sections:
            if section.strip().lower().startswith(section_name.lower()):
                # Return content after the header line
                lines = section.strip().split("\n")[1:]
                text = "\n".join(l for l in lines if l.strip()).strip()
                return text[:300] if text else None
        return None

    def _load_commands(self, ref, level: str) -> Optional[str]:
        """Load commands for injection."""
        if level == "none":
            return None

        if isinstance(ref, list):
            if level == "full_guidance":
                lines = ["## Recommended Commands"]
                for cmd_name in ref:
                    cmd_path = KB_DIR / "commands" / f"{cmd_name.lstrip('/')}.md"
                    if cmd_path.exists():
                        content = self._read_file(cmd_path)
                        # Extract "What It Actually Does" section
                        lines.append(f"### {cmd_name}")
                        for section in content.split("\n## "):
                            if "what it" in section.lower():
                                desc_lines = section.strip().split("\n")[1:4]
                                lines.extend(desc_lines)
                                break
                return "\n".join(lines)
            elif level == "key_per_stage":
                return "Key commands: " + ", ".join(ref)
        return None

    def _load_tools(self, ref, level: str) -> Optional[str]:
        """Load fleet tools for injection."""
        if level == "none":
            return None

        if isinstance(ref, list):
            if level == "full_chains":
                lines = ["## Fleet Tools"]
                for tool_name in ref:
                    tool_path = KB_DIR / "tools" / f"{tool_name}.md"
                    if tool_path.exists():
                        content = self._read_file(tool_path)
                        # Extract purpose
                        for line in content.split("\n"):
                            if line.startswith("**Purpose"):
                                lines.append(f"- **{tool_name}**: {line.split(':', 1)[-1].strip()}")
                                break
                        else:
                            lines.append(f"- **{tool_name}**")
                return "\n".join(lines)
            elif level == "names_and_purpose":
                return "Fleet tools: " + ", ".join(ref)
            elif level == "fleet_read_context":
                return "Call fleet_read_context for full task context."
        return None

    def _load_system_manuals(self, ref, level: str) -> Optional[str]:
        """Load system manual content."""
        if level == "none":
            return None

        if level == "full":
            if isinstance(ref, str):
                return self._read_file(KB_DIR / "systems" / f"{ref}.md")
        elif level == "condensed":
            return self._read_file(KNOWLEDGE_MAP_DIR / "system-manuals-condensed.md")
        elif level == "minimal":
            return self._read_file(KNOWLEDGE_MAP_DIR / "system-manuals-minimal.md")
        return None

    def _load_plugins(self, ref, level: str) -> Optional[str]:
        """Load plugin info for injection."""
        if level == "none":
            return None
        if isinstance(ref, list) and level == "names_only":
            return "Plugins: " + ", ".join(ref)
        return None

    def _load_mcp(self, ref, level: str) -> Optional[str]:
        """Load MCP server info for injection."""
        if level == "none":
            return None
        if isinstance(ref, list):
            lines = ["## MCP Servers"]
            for server_name in ref:
                mcp_path = KB_DIR / "mcp" / f"{server_name}.md"
                if mcp_path.exists():
                    content = self._read_file(mcp_path)
                    # Extract first paragraph after title
                    parts = content.split("\n\n")
                    desc = parts[1] if len(parts) > 1 else ""
                    lines.append(f"- **{server_name}**: {desc.strip()[:150]}")
                else:
                    lines.append(f"- **{server_name}**")
            return "\n".join(lines)
        return None

    def _load_contributions(self, ref, level: str) -> Optional[str]:
        """Load contribution context for injection."""
        if level == "none" or ref == "none":
            return None
        if isinstance(ref, str):
            if ref == "none":
                return None
            # Simple reference like "received_only" or "full"
            return f"**Contributions:** Check fleet_read_context for contribution status ({ref})"
        if isinstance(ref, list):
            return "**Contributions:** " + ", ".join(str(r) for r in ref)
        return None

    def _load_context_awareness(self, ref, level: str) -> Optional[str]:
        """Load context awareness info for injection."""
        if level == "none":
            return None
        if level == "full":
            return ("**Context awareness:** Monitor context % and rate limit %.\n"
                    "Use /context for visual grid. Use /usage for rate limit status.\n"
                    "Compact at 70% context. Strategic compaction at 85% rate limit.")
        elif level == "both_pcts":
            return "**Context:** Check /context and /usage for remaining capacity."
        return None

    def _load_trail(self, ref, level: str) -> Optional[str]:
        """Load trail info for injection."""
        if level == "none":
            return None
        if level == "full":
            return ("**Trail:** Every tool call is recorded. fleet-ops verifies trail completeness.\n"
                    "Ensure commits, artifacts, and task updates create proper trail events.")
        elif level == "summary":
            return "**Trail:** Your actions are being recorded for review."
        return None

    # ── LightRAG graph queries ─────────────────────────────────────

    def _query_graph(
        self,
        task_context: str,
        role: str,
        profile: InjectionProfile,
    ) -> Optional[str]:
        """Query LightRAG knowledge graph for task-relevant context.

        Uses the graph to find entities and relationships related to the
        task — traversing the autocomplete web to find knowledge the
        static intent map doesn't cover.

        Query mode selection:
        - local: entity-focused ("What is X?") — for specific tasks
        - global: relationship-focused ("How are X and Y related?") — for broad tasks
        - hybrid: both — default for most work
        - mix: all sources with reranking — for complex queries
        """
        try:
            import urllib.request
            import json

            url = "http://localhost:9621/query"

            # Select query mode based on context
            mode = self._select_graph_mode(task_context, role)

            query = f"What fleet systems, tools, and knowledge relate to: {task_context}"

            data = json.dumps({
                "query": query,
                "mode": mode,
                "only_need_context": True,
            }).encode()

            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                if isinstance(result, str) and len(result) > 50:
                    budget = profile.context_budget // 4
                    truncated = result[:budget * 4]
                    return f"## Knowledge Graph Context\n\n{truncated}"

        except Exception as e:
            logger.debug("LightRAG query skipped (not running): %s", e)

        # Fallback: traverse cross-references.yaml as local graph
        return self._traverse_local_graph(task_context, role, profile)

    def _select_graph_mode(self, task_context: str, role: str) -> str:
        """Select LightRAG query mode based on task and role.

        - Specific entity names → local (entity-focused)
        - Broad/thematic questions → global (relationship-focused)
        - Implementation tasks → hybrid (both)
        - Review/audit → mix (all sources)
        """
        ctx_lower = task_context.lower() if task_context else ""

        # Review/audit roles benefit from comprehensive results
        if role in ("fleet-ops", "accountability-generator"):
            return "mix"

        # Security tasks need comprehensive coverage
        if "security" in ctx_lower or "vulnerab" in ctx_lower or "audit" in ctx_lower:
            return "mix"

        # Architecture/design → relationship-focused
        if "design" in ctx_lower or "architect" in ctx_lower or "plan" in ctx_lower:
            return "global"

        # Specific systems/tools referenced → entity-focused
        if any(kw in ctx_lower for kw in ("system", "tool", "module", "hook", "command")):
            return "local"

        # Default: hybrid
        return "hybrid"

    def _load_target_task(self, ref, level: str) -> Optional[str]:
        """Inject target task guidance for contribution intents."""
        if level == "none":
            return None
        if isinstance(ref, str) and ref != "none":
            return (f"**Target task:** Read the target task's full context with fleet_read_context "
                    f"before contributing. Your contribution must address the task's specific needs.")
        return None

    # ── Local graph traversal (cross-references.yaml) ───────────────

    def _traverse_local_graph(
        self,
        task_context: str,
        role: str,
        profile: InjectionProfile,
    ) -> Optional[str]:
        """Traverse cross-references.yaml as a local knowledge graph.

        Fallback when LightRAG isn't running. Searches system descriptions,
        modules, tools, skills for keywords from the task context. Returns
        matching systems with their connections.

        This is the autocomplete web without Docker — the cross-references
        ARE a relationship graph, just stored as YAML.
        """
        if not self._cross_refs or not task_context:
            return None

        systems = self._cross_refs.get("systems", {})
        if not systems:
            return None

        # Extract keywords from task context
        keywords = set()
        for word in task_context.lower().split():
            if len(word) > 3 and word not in ("the", "and", "for", "with", "from", "that", "this", "what", "work"):
                keywords.add(word)

        if not keywords:
            return None

        # Score each system by keyword match
        scored = []
        for sys_name, sys_data in systems.items():
            if not isinstance(sys_data, dict):
                continue

            score = 0
            sys_text = str(sys_data).lower()

            for kw in keywords:
                if kw in sys_text:
                    score += 1
                # Bonus for name match
                if kw in sys_name.lower():
                    score += 2

            # Bonus for role match
            roles_data = sys_data.get("agent_roles", {})
            role_short = self._role_short(role)
            if role_short in str(roles_data).lower() or "all" in roles_data:
                score += 1

            if score > 0:
                sys_id = sys_data.get("id", "")
                modules = sys_data.get("modules", [])
                connections = sys_data.get("connected_systems", [])
                scored.append((score, sys_id, sys_name, modules, connections))

        if not scored:
            return None

        # Take top 3 matches
        scored.sort(reverse=True)
        top = scored[:3]

        lines = ["## Relevant Systems (from knowledge graph)"]
        for score, sys_id, name, modules, connections in top:
            conn_ids = []
            for c in connections[:3]:
                if isinstance(c, str):
                    # Extract system ID from "S02 (protocol_violation → doctor)"
                    conn_id = c.split("(")[0].strip()
                    conn_ids.append(conn_id)

            line = f"- **{sys_id} {name}**"
            if modules:
                mod_str = ", ".join(str(m) for m in modules[:3])
                line += f" ({mod_str})"
            if conn_ids:
                line += f" → connects to {', '.join(conn_ids)}"
            lines.append(line)

        return "\n".join(lines)

    # ── Cross-reference enrichment ──────────────────────────────────

    def _enrich_from_crossrefs(self, intent: Intent, profile: InjectionProfile) -> Optional[str]:
        """Find systems related to intent's tools via cross-references.

        When an intent references tools like fleet_commit, the cross-ref
        shows which systems use that tool (S01 methodology gates it).
        This adds a compact "Related systems" section.
        """
        if not self._cross_refs:
            return None

        # Collect tools referenced in this intent
        intent_tools = set()
        for item in intent.inject:
            if isinstance(item, dict) and "tools" in item:
                ref = item["tools"]
                if isinstance(ref, list):
                    intent_tools.update(str(t).split("(")[0].strip() for t in ref)

        if not intent_tools:
            return None

        # Find which systems reference these tools
        systems = self._cross_refs.get("systems", {})
        related = []
        for sys_name, sys_data in systems.items():
            if not isinstance(sys_data, dict):
                continue
            sys_id = sys_data.get("id", "")
            tools = sys_data.get("tools", {})
            # Check all tool lists in the system
            for key, tool_list in tools.items():
                if isinstance(tool_list, list):
                    for tool in tool_list:
                        tool_clean = str(tool).split("(")[0].strip()
                        if tool_clean in intent_tools:
                            related.append(f"- **{sys_id} {sys_name}**: {key} {tool}")
                            break

        if not related and profile.name == "opus-1m":
            return None
        if related:
            return "## Related Systems\n" + "\n".join(related[:5])  # max 5 systems
        return None

    # ── Cached file reading ─────────────────────────────────────────

    def _read_file(self, path: Path) -> Optional[str]:
        """Read a file with caching. Returns None if file doesn't exist."""
        key = str(path)
        if key in self._file_cache:
            return self._file_cache[key]
        if not path.exists():
            return None
        try:
            content = path.read_text()
            self._file_cache[key] = content
            return content
        except Exception:
            return None

    # ── YAML loading ───────────────────────────────────────────────

    def _load_yaml(self, filename: str) -> dict:
        """Load a YAML metadata file from the knowledge map."""
        path = KNOWLEDGE_MAP_DIR / filename
        if not path.exists():
            logger.warning("Knowledge map file not found: %s", path)
            return {}
        try:
            content = self._read_file(path)
            if not content:
                return {}
            return yaml.safe_load(content) or {}
        except Exception as e:
            logger.error("Failed to load %s: %s", filename, e)
            return {}

    def _parse_profiles(self, raw: dict) -> dict[str, InjectionProfile]:
        """Parse injection profiles from YAML."""
        profiles = {}
        for name in ("opus-1m", "sonnet-200k", "localai-8k", "heartbeat"):
            data = raw.get(name, {})
            branches = data.get("branches", {})
            levels = {}
            for branch, config in branches.items():
                if isinstance(config, dict):
                    levels[branch] = config.get("level", "none")
                elif isinstance(config, str):
                    levels[branch] = config
            profiles[name] = InjectionProfile(
                name=name,
                context_budget=self._parse_budget(data.get("context_budget", "15K")),
                levels=levels,
            )
        return profiles

    def _parse_budget(self, budget) -> int:
        """Parse budget string like '~50K tokens' to int."""
        if isinstance(budget, int):
            return budget
        s = str(budget).lower().replace("~", "").replace(",", "")
        s = s.split("token")[0].strip()
        if "k" in s:
            return int(float(s.replace("k", "")) * 1000)
        try:
            return int(s)
        except ValueError:
            return 15000
