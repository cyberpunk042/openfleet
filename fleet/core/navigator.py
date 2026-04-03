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

    def load(self) -> None:
        """Load metadata files from knowledge map."""
        self._intent_map = self._load_yaml("intent-map.yaml")
        self._profiles = self._parse_profiles(self._load_yaml("injection-profiles.yaml"))
        self._cross_refs = self._load_yaml("cross-references.yaml")
        self._loaded = True
        logger.info("Navigator loaded: %d intents, %d profiles",
                     len(self._intent_map.get("intents", {})),
                     len(self._profiles))

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
            self._assemble_from_intent(ctx, intent, profile)
        else:
            # No specific intent — use profile defaults
            self._assemble_defaults(ctx, role, profile)

        # 4. Query LightRAG for task-relevant graph context
        if task_context and profile.name != "heartbeat":
            graph_context = self._query_graph(task_context, role, profile)
            if graph_context:
                ctx.sections.append(graph_context)

        return ctx

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

        # Try exact match: "architect-reasoning", "engineer-work"
        role_short = self._role_short(role)
        key = f"{role_short}-{stage}"
        if key in intents:
            return Intent(name=key, inject=intents[key].get("inject", []))

        # Try role-only heartbeat: "fleet-ops-heartbeat"
        key = f"{role_short}-heartbeat"
        if stage == "heartbeat" and key in intents:
            return Intent(name=key, inject=intents[key].get("inject", []))

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
    ) -> None:
        """Assemble context from an intent's injection recipe."""
        for item in intent.inject:
            if isinstance(item, str):
                # Simple reference like "- agent_manual: architect"
                continue

            for branch, ref in item.items():
                if branch == "note":
                    ctx.sections.append(f"**Note:** {ref}")
                    continue

                level = profile.levels.get(branch, "none")
                if level == "none":
                    continue

                content = self._load_branch_content(branch, ref, level)
                if content:
                    ctx.sections.append(content)

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

        return None

    # ── Branch loaders ─────────────────────────────────────────────

    def _load_agent_manual(self, role: str, level: str) -> Optional[str]:
        """Load agent manual section."""
        path = KNOWLEDGE_MAP_DIR / "agent-manuals.md"
        if not path.exists():
            return None

        content = path.read_text()
        role_short = self._role_short(role) if "-" in role else role

        # Find the section for this role
        # Agent manuals use ## headers with role names
        sections = content.split("\n## ")
        for section in sections:
            if role_short.lower() in section.lower().split("\n")[0].lower():
                if level == "full":
                    return f"## {section}"
                elif level == "condensed":
                    # First 10 lines
                    lines = section.strip().split("\n")
                    return "## " + "\n".join(lines[:10])
                elif level == "minimal":
                    # First line only (mission)
                    first_line = section.strip().split("\n")[0]
                    return f"You are {first_line.strip()}"
        return None

    def _load_methodology(self, level: str, stage: Optional[str] = None) -> Optional[str]:
        """Load methodology manual section."""
        path = KNOWLEDGE_MAP_DIR / "methodology-manual.md"
        if not path.exists():
            return None

        content = path.read_text()

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

    def _load_standards(self, ref: str, level: str) -> Optional[str]:
        """Load standards manual section."""
        path = KNOWLEDGE_MAP_DIR / "standards-manual.md"
        if not path.exists():
            return None
        if level == "none":
            return None
        content = path.read_text()
        if level == "full":
            return content
        # For required_fields level, extract just field lists
        if level == "required_fields" and isinstance(ref, list):
            sections = content.split("\n## ")
            results = []
            for standard in ref:
                for section in sections:
                    if standard.lower() in section.lower().split("\n")[0].lower():
                        results.append(f"## {section.split(chr(10))[0]}")
                        # Extract just "- field:" lines
                        for line in section.split("\n"):
                            if line.strip().startswith("- ") and ":" in line:
                                results.append(line)
                        break
            return "\n".join(results) if results else None
        return None

    def _load_skills(self, ref, level: str) -> Optional[str]:
        """Load skills for injection."""
        if level == "none":
            return None

        if isinstance(ref, list):
            # Specific skills listed
            if level == "full_descriptions":
                lines = ["## Available Skills"]
                for skill_name in ref:
                    skill_path = KB_DIR / "skills" / f"{skill_name}.md"
                    if skill_path.exists():
                        content = skill_path.read_text()
                        # Extract first paragraph after the title
                        parts = content.split("\n\n")
                        desc = parts[1] if len(parts) > 1 else ""
                        lines.append(f"- **/{skill_name}**: {desc.strip()[:200]}")
                    else:
                        lines.append(f"- **/{skill_name}**")
                return "\n".join(lines)
            elif level == "names_only":
                return "Available skills: " + ", ".join(f"/{s}" for s in ref)
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
                        content = cmd_path.read_text()
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
                        content = tool_path.read_text()
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
            # Load from full system docs
            if isinstance(ref, str):
                path = KB_DIR / "systems" / f"{ref}.md"
                if path.exists():
                    return path.read_text()
        elif level == "condensed":
            path = KNOWLEDGE_MAP_DIR / "system-manuals-condensed.md"
            if path.exists():
                return path.read_text()
        elif level == "minimal":
            path = KNOWLEDGE_MAP_DIR / "system-manuals-minimal.md"
            if path.exists():
                return path.read_text()
        return None

    def _load_plugins(self, ref, level: str) -> Optional[str]:
        """Load plugin info for injection."""
        if level == "none":
            return None
        if isinstance(ref, list) and level == "names_only":
            return "Plugins: " + ", ".join(ref)
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
        """
        try:
            import urllib.request
            import json

            url = "http://localhost:9621/query"
            # Build query from task context
            query = f"What fleet knowledge is relevant for {role} working on: {task_context}"

            data = json.dumps({
                "query": query,
                "mode": "hybrid",  # entities + relationships
                "only_need_context": True,  # return context, not LLM response
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
                    # Truncate to profile budget
                    budget = profile.context_budget // 4  # graph gets ~25% of budget
                    truncated = result[:budget * 4]  # rough char-to-token ratio
                    return f"## Knowledge Graph Context\n\n{truncated}"

        except Exception as e:
            logger.debug("LightRAG query failed (may not be running): %s", e)

        return None

    # ── YAML loading ───────────────────────────────────────────────

    def _load_yaml(self, filename: str) -> dict:
        """Load a YAML metadata file from the knowledge map."""
        path = KNOWLEDGE_MAP_DIR / filename
        if not path.exists():
            logger.warning("Knowledge map file not found: %s", path)
            return {}
        try:
            with open(path) as f:
                return yaml.safe_load(f) or {}
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
