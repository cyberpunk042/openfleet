"""KB Graph Sync — Automatic synchronization of KB entries to LightRAG.

Parses ## Relationships sections from KB markdown files and syncs
entities + relationships to the LightRAG knowledge graph via REST API.

This is a proper system module, not a one-shot script:
- Tracks file mtimes for incremental sync
- Logs every operation with structured output
- Handles errors per-entity/per-relationship (never blocks on one failure)
- Flushes output in real-time (no buffering surprises)
- Designed to run in background during setup or as periodic sync

Usage from code:
    from fleet.core.kb_sync import KBGraphSync
    sync = KBGraphSync(lightrag_url="http://localhost:9621")
    sync.full_sync()    # all KB files
    sync.incremental()  # only changed since last sync

Usage from CLI:
    python -m fleet.core.kb_sync --full
    python -m fleet.core.kb_sync --sync
    python -m fleet.core.kb_sync --stats
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Fleet paths
FLEET_DIR = Path(__file__).parent.parent.parent
KB_DIR = FLEET_DIR / "docs" / "knowledge-map" / "kb"
SYNC_STATE_FILE = FLEET_DIR / ".kb-graph-sync.json"
DEFAULT_LIGHTRAG_URL = "http://localhost:9621"


# ── Entity type normalization ──────────────────────────────────────

TYPE_MAP = {
    "fleet system": "system",
    "fleet module": "module",
    "fleet agent": "agent",
    "mcp tool": "tool",
    "fleet mcp tool": "tool",
    "external mcp server": "mcp_server",
    "claude code hook": "hook",
    "claude code built-in command": "command",
    "claude code bundled skill": "command",
    "claude code plugin": "plugin",
    "skill": "skill",
    "agent file": "layer",
    "infrastructure component": "infrastructure",
    "research": "research",
}


def _normalize_type(raw: str) -> str:
    raw_lower = raw.lower().strip()
    for pattern, etype in TYPE_MAP.items():
        if pattern in raw_lower:
            return etype
    return "concept"


# ── Relationship line filter ───────────────────────────────────────

SKIP_PREFIXES = [
    "NOT YET", "CRITICAL", "PERFORMANCE", "HISTORICAL",
    "CAUTION", "TIER", "KEY INSIGHT", "ANTI-CORRUPTION",
    "KEY PRINCIPLE", "ZERO RISK", "DANGER", "DOES NOT",
    "ONE OF", "WHAT", "WHY", "HOW", "THE ", "IS ",
    "SAME ", "ENTIRELY", "PROGRESSIVE", "MISSING",
    "PENDING", "FUTURE", "NOTE", "DATA NOTE",
]


# ── Data classes ───────────────────────────────────────────────────

@dataclass
class Entity:
    name: str
    entity_type: str
    description: str
    source_file: str


@dataclass
class Relationship:
    src: str
    tgt: str
    rel_type: str
    description: str
    source_file: str
    weight: float = 1.0


@dataclass
class SyncResult:
    entities_ok: int = 0
    entities_fail: int = 0
    relationships_ok: int = 0
    relationships_fail: int = 0
    files_processed: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


# ── KB file parser ─────────────────────────────────────────────────

def parse_kb_file(filepath: Path) -> tuple[Entity, list[Relationship]]:
    """Parse one KB markdown file into entity + relationships."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Title
    title = filepath.stem
    for line in lines:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    # Type
    entity_type = "concept"
    for line in lines[:20]:
        if "**Type:**" in line:
            entity_type = _normalize_type(line.split("**Type:**")[1].strip())
            break

    # Branch (parent directory name — systems, tools, hooks, etc.)
    branch = filepath.parent.name

    # Roles from metadata
    roles = []
    for line in lines[:25]:
        if "**Roles:**" in line or "**Installed for:**" in line:
            roles_raw = line.split(":**")[1].strip()
            roles = [r.strip() for r in roles_raw.split(",") if r.strip()]

    # Description — try multiple section headers
    description = title
    for section_name in ["What It Does", "What It Actually Does", "Purpose",
                         "What This System Does", "What It Is", "Mission",
                         "What the Navigator Is", "What This Project Is",
                         "What Claude-Mem Is", "What LightRAG Is"]:
        section = _extract_section(text, section_name)
        if section:
            first_para = section.strip().split("\n\n")[0].strip()
            if first_para and len(first_para) > 20:
                description = first_para[:400]
                break

    # If no section found, try first non-metadata paragraph
    if description == title:
        in_body = False
        for line in lines:
            if line.startswith("## "):
                in_body = True
                continue
            if in_body and line.strip() and not line.startswith("**") and not line.startswith("|") and not line.startswith("-"):
                description = line.strip()[:300]
                break

    # Build description with metadata
    desc_parts = [description]
    if branch and branch != "kb":
        desc_parts.append(f"Branch: {branch}.")
    if roles:
        desc_parts.append(f"Used by: {', '.join(roles)}.")
    description = " ".join(desc_parts)

    source_file = str(filepath.relative_to(FLEET_DIR))
    entity = Entity(name=title, entity_type=entity_type,
                    description=description[:500], source_file=source_file)

    # Relationships from ## Relationships section
    relationships = []
    rel_section = _extract_section(text, "Relationships")
    if rel_section:
        for line in rel_section.strip().split("\n"):
            line = line.strip()
            if not line.startswith("-"):
                continue
            rels = _parse_rel_line(line[2:].strip(), title, source_file)
            relationships.extend(rels)

    # Additional relationships from roles metadata
    for role in roles:
        relationships.append(Relationship(
            src=title, tgt=role, rel_type="used by",
            description=f"{title} used by {role}",
            source_file=source_file,
        ))

    # Additional relationship: entity belongs to its branch
    if branch and branch not in ("kb",):
        relationships.append(Relationship(
            src=title, tgt=f"KB:{branch}",
            rel_type="belongs to",
            description=f"{title} belongs to {branch} branch of the knowledge map",
            source_file=source_file,
        ))

    return entity, relationships


def _extract_section(text: str, header: str) -> Optional[str]:
    sections = text.split("\n## ")
    for section in sections:
        if section.strip().lower().startswith(header.lower()):
            return "\n".join(section.strip().split("\n")[1:])
    return None


def _parse_rel_line(line: str, source: str, source_file: str) -> list[Relationship]:
    match = re.match(r"^([A-Z][A-Z /\-]+?):\s*(.+)$", line)
    if not match:
        return []

    rel_type = match.group(1).strip()
    targets_raw = match.group(2).strip()

    if any(rel_type.startswith(s) for s in SKIP_PREFIXES):
        return []

    results = []
    parts = re.split(r",\s*(?=[A-Z])|,\s*(?=[a-z_])", targets_raw)

    for part in parts:
        part = part.strip().rstrip(".")
        if not part or len(part) < 2:
            continue

        # Strip ALL parentheticals from entity name
        context = ""
        ctx_match = re.search(r"\(([^)]+)\)", part)
        if ctx_match:
            context = ctx_match.group(1)
        # Remove all parenthetical content from target name
        part_clean = re.sub(r"\s*\([^)]*\)\s*", " ", part).strip()
        # Clean up any remaining parens or trailing punctuation
        part_clean = part_clean.rstrip(".,;:()").strip()

        if part_clean.lower() in ("none", "n/a", "yes", "no", "all"):
            continue
        if len(part_clean) < 2:
            continue

        desc = f"{source} {rel_type.lower()} {part_clean}"
        if context:
            desc += f" ({context})"

        results.append(Relationship(
            src=source, tgt=part_clean, rel_type=rel_type.lower(),
            description=desc, source_file=source_file,
        ))

    return results


# ── LightRAG API client ───────────────────────────────────────────

class LightRAGClient:
    """HTTP client for LightRAG graph API."""

    def __init__(self, base_url: str = DEFAULT_LIGHTRAG_URL, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def wait_healthy(self, max_wait: int = 60) -> bool:
        """Wait for LightRAG to be healthy, with backoff."""
        for i in range(max_wait // 3):
            if self.health():
                return True
            time.sleep(3)
        return False

    def pending_locks(self) -> int:
        """Check how many async locks are pending cleanup."""
        try:
            req = urllib.request.Request(f"{self.base_url}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data.get("keyed_locks", {}).get(
                    "current_status", {}).get("pending_async_cleanup", 0)
        except Exception:
            return -1

    def wait_locks_clear(self, threshold: int = 100, max_wait: int = 120) -> bool:
        """Wait until pending locks drop below threshold."""
        for i in range(max_wait // 5):
            pending = self.pending_locks()
            if 0 <= pending < threshold:
                return True
            logger.info("Waiting for locks to clear: %d pending", pending)
            time.sleep(5)
        return False

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize entity names for LightRAG.

        LightRAG hangs on entity names containing '/' or '.' — these
        characters interfere with its internal keyed lock lookup.
        Replace with '::' and ':' to preserve readability.
        """
        return name.upper().replace("/", "::").replace(".", ":")

    def create_entity(self, entity: Entity) -> tuple[bool, str]:
        name = self._sanitize_name(entity.name)
        payload = {
            "entity_name": name,
            "entity_data": {
                "entity_type": entity.entity_type,
                "description": entity.description,
                "source_id": entity.source_file,
            },
        }
        ok, msg = self._post("/graph/entity/create", payload)
        if ok and msg == "exists":
            # Update description on existing entity
            update_payload = {
                "entity_name": name,
                "updated_data": {
                    "entity_type": entity.entity_type,
                    "description": entity.description,
                },
            }
            return self._post("/graph/entity/edit", update_payload)
        return ok, msg

    def create_relationship(self, rel: Relationship) -> tuple[bool, str]:
        src = self._sanitize_name(rel.src)
        tgt = self._sanitize_name(rel.tgt)
        payload = {
            "source_entity": src,
            "target_entity": tgt,
            "relation_data": {
                "description": rel.description,
                "keywords": rel.rel_type,
                "weight": rel.weight,
                "source_id": rel.source_file,
            },
        }
        ok, msg = self._post("/graph/relation/create", payload)
        if ok and msg == "exists":
            # Update weight/description on existing relationship
            update_payload = {
                "source_id": src,
                "target_id": tgt,
                "updated_data": {
                    "description": rel.description,
                    "keywords": rel.rel_type,
                    "weight": rel.weight,
                },
            }
            return self._post("/graph/relation/edit", update_payload)
        return ok, msg

    def _post(self, endpoint: str, payload: dict, retries: int = 2) -> tuple[bool, str]:
        data = json.dumps(payload).encode()
        for attempt in range(retries + 1):
            req = urllib.request.Request(
                f"{self.base_url}{endpoint}",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode()
                    return (resp.status < 300, body)
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:200] if e.fp else str(e)
                if e.code == 400 and "already exists" in body:
                    return (True, "exists")
                if attempt < retries:
                    continue
                return (False, f"HTTP {e.code}: {body}")
            except Exception as e:
                if attempt < retries:
                    # Timeout or connection error — wait for LightRAG to recover
                    self.wait_healthy(max_wait=30)
                    continue
                return (False, str(e))


# ── Sync engine ────────────────────────────────────────────────────

class KBGraphSync:
    """Synchronizes KB entries to LightRAG knowledge graph."""

    def __init__(self, lightrag_url: str = DEFAULT_LIGHTRAG_URL,
                 kb_dir: Path = KB_DIR):
        self.client = LightRAGClient(lightrag_url)
        self.kb_dir = kb_dir

    def _restart_lightrag(self) -> None:
        """Restart LightRAG container to clear accumulated async locks.

        LightRAG leaks keyed async locks — each entity/relation create acquires
        a lock that's never released. After ~1000 requests, response time degrades
        from <1s to 5s+, eventually timing out. Restarting clears the lock table.
        """
        import subprocess
        compose_file = FLEET_DIR / "docker-compose.yaml"
        print("  Restarting LightRAG (clearing lock table)...", flush=True)
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "restart", "lightrag"],
            capture_output=True, timeout=30,
        )
        # Wait for it to be healthy
        for _ in range(20):
            if self.client.health():
                return
            time.sleep(2)
        print("  WARN: LightRAG did not recover after restart", flush=True)

    def full_sync(self, include_sources: bool = True) -> SyncResult:
        """Sync all KB files + additional sources to graph."""
        files = sorted(self.kb_dir.rglob("*.md"))
        logger.info("Full sync: %d KB files", len(files))
        result = self._sync_files(files)

        if include_sources:
            source_result = self._sync_sources()
            result.entities_ok += source_result.entities_ok
            result.entities_fail += source_result.entities_fail
            result.relationships_ok += source_result.relationships_ok
            result.relationships_fail += source_result.relationships_fail
            result.files_processed += source_result.files_processed

        self._save_state()
        return result

    def incremental(self) -> SyncResult:
        """Sync only changed files since last sync."""
        changed = self._find_changed()
        if not changed:
            logger.info("No KB changes since last sync")
            return SyncResult()
        logger.info("Incremental sync: %d changed files", len(changed))
        result = self._sync_files(changed)
        self._save_state()
        return result

    def stats(self) -> dict:
        """Parse all KB files and return statistics without inserting."""
        files = sorted(self.kb_dir.rglob("*.md"))
        all_entities = []
        all_relationships = []

        for filepath in files:
            try:
                entity, rels = parse_kb_file(filepath)
                all_entities.append(entity)
                all_relationships.extend(rels)
            except Exception as e:
                logger.warning("Skip %s: %s", filepath.name, e)

        # Type distributions
        entity_types = {}
        for e in all_entities:
            entity_types[e.entity_type] = entity_types.get(e.entity_type, 0) + 1

        rel_types = {}
        for r in all_relationships:
            rel_types[r.rel_type] = rel_types.get(r.rel_type, 0) + 1

        # Most connected
        connections = {}
        for r in all_relationships:
            connections[r.src] = connections.get(r.src, 0) + 1
            connections[r.tgt] = connections.get(r.tgt, 0) + 1

        return {
            "files": len(files),
            "entities": len(all_entities),
            "relationships": len(all_relationships),
            "entity_types": dict(sorted(entity_types.items(), key=lambda x: -x[1])),
            "rel_types": dict(sorted(rel_types.items(), key=lambda x: -x[1])[:20]),
            "most_connected": dict(sorted(connections.items(), key=lambda x: -x[1])[:15]),
        }

    def _sync_files(self, files: list[Path]) -> SyncResult:
        """Parse files and insert into LightRAG."""
        t0 = time.time()
        result = SyncResult()

        if not self.client.health():
            logger.error("LightRAG not reachable at %s", self.client.base_url)
            result.errors.append("LightRAG not reachable")
            return result

        # Parse all files first
        entities = []
        relationships = []
        seen_entities = set()
        seen_rels = set()

        for filepath in files:
            try:
                entity, rels = parse_kb_file(filepath)
                result.files_processed += 1

                if entity.name.upper() not in seen_entities:
                    entities.append(entity)
                    seen_entities.add(entity.name.upper())

                for rel in rels:
                    key = (rel.src.upper(), rel.rel_type, rel.tgt.upper())
                    if key not in seen_rels:
                        relationships.append(rel)
                        seen_rels.add(key)

                        # Ensure target exists as entity
                        if rel.tgt.upper() not in seen_entities:
                            entities.append(Entity(
                                name=rel.tgt, entity_type="reference",
                                description=f"Referenced by {rel.src}",
                                source_file=entity.source_file,
                            ))
                            seen_entities.add(rel.tgt.upper())
            except Exception as e:
                logger.warning("Skip %s: %s", filepath.name, e)

        logger.info("Parsed: %d entities, %d relationships from %d files",
                     len(entities), len(relationships), result.files_processed)

        # Insert entities
        print(f"  Inserting {len(entities)} entities...", flush=True)
        for i, ent in enumerate(entities):
            ok, msg = self.client.create_entity(ent)
            if ok:
                result.entities_ok += 1
            else:
                result.entities_fail += 1
                print(f"    FAIL entity [{ent.name}]: {msg}", flush=True)

            if (i + 1) % 25 == 0 or i + 1 == len(entities):
                print(f"    {i+1}/{len(entities)} ({result.entities_ok} ok, "
                      f"{result.entities_fail} fail)", flush=True)
            time.sleep(0.1)

        print(f"  Entities done: {result.entities_ok} ok, "
              f"{result.entities_fail} fail", flush=True)

        # Insert relationships
        print(f"  Inserting {len(relationships)} relationships...", flush=True)
        for i, rel in enumerate(relationships):
            ok, msg = self.client.create_relationship(rel)
            if ok:
                result.relationships_ok += 1
            else:
                result.relationships_fail += 1
                if result.relationships_fail <= 20:
                    print(f"    FAIL rel [{rel.src} -> {rel.tgt}]: {msg}", flush=True)

            if (i + 1) % 25 == 0 or i + 1 == len(relationships):
                print(f"    {i+1}/{len(relationships)} ({result.relationships_ok} ok, "
                      f"{result.relationships_fail} fail)", flush=True)
            time.sleep(0.1)

        print(f"  Relationships done: {result.relationships_ok} ok, "
              f"{result.relationships_fail} fail", flush=True)

        result.duration_seconds = time.time() - t0
        logger.info("Sync complete in %.1fs", result.duration_seconds)
        return result

    def _sync_sources(self) -> SyncResult:
        """Parse and sync additional fleet sources (Python, YAML, Markdown, Agent templates)."""
        from fleet.core.source_parsers import (
            parse_python, parse_yaml_config, parse_markdown_doc, parse_agent_claude_md,
            parse_skill_md, AICP_SKILLS_DIR,
        )

        result = SyncResult()
        all_entities = []
        all_relationships = []
        seen_entities = set()
        seen_rels = set()

        def _collect(ents, rels, source_type):
            for e in ents:
                if e.name.upper() not in seen_entities:
                    all_entities.append(e)
                    seen_entities.add(e.name.upper())
            for r in rels:
                key = (r.src.upper(), r.rel_type, r.tgt.upper())
                if key not in seen_rels:
                    all_relationships.append(r)
                    seen_rels.add(key)
                    if r.tgt.upper() not in seen_entities:
                        all_entities.append(Entity(
                            name=r.tgt, entity_type="reference",
                            description=f"Referenced by {r.src}",
                            source_file=source_type,
                        ))
                        seen_entities.add(r.tgt.upper())
            result.files_processed += 1

        # ALL Python source files (fleet/, gateway/)
        print("  Parsing ALL Python sources...", flush=True)
        for py_dir in ["fleet/core", "fleet/cli", "fleet/mcp", "fleet/infra", "gateway"]:
            full_dir = FLEET_DIR / py_dir
            if full_dir.exists():
                for filepath in sorted(full_dir.glob("*.py")):
                    if filepath.name == "__init__.py":
                        continue
                    try:
                        ents, rels = parse_python(filepath)
                        _collect(ents, rels, "python")
                    except Exception as e:
                        logger.warning("Skip %s: %s", filepath.name, e)

        # ALL config YAMLs
        print("  Parsing ALL config YAMLs...", flush=True)
        config_dir = FLEET_DIR / "config"
        if config_dir.exists():
            for filepath in sorted(config_dir.glob("*.yaml")):
                try:
                    ents, rels = parse_yaml_config(filepath)
                    _collect(ents, rels, "config")
                except Exception as e:
                    logger.warning("Skip %s: %s", filepath.name, e)

        # ALL documentation: manuals, system docs, research, cross-refs
        doc_dirs = [
            "docs/knowledge-map",
            "docs/systems",
            "docs/milestones/active/research",
        ]
        print("  Parsing documentation...", flush=True)
        for dir_path in doc_dirs:
            full_dir = FLEET_DIR / dir_path
            if full_dir.exists():
                for filepath in sorted(full_dir.glob("*.md")):
                    try:
                        ents, rels = parse_markdown_doc(filepath)
                        _collect(ents, rels, "docs")
                    except Exception as e:
                        logger.warning("Skip %s: %s", filepath.name, e)
        # cross-references.yaml
        crossref = FLEET_DIR / "docs" / "knowledge-map" / "cross-references.yaml"
        if crossref.exists():
            try:
                ents, rels = parse_markdown_doc(crossref)
                _collect(ents, rels, "docs")
            except Exception:
                pass

        # ALL design docs
        print("  Parsing ALL design docs...", flush=True)
        design_dir = FLEET_DIR / "docs" / "milestones" / "active"
        if design_dir.exists():
            for filepath in sorted(design_dir.glob("*.md")):
                try:
                    ents, rels = parse_markdown_doc(filepath)
                    _collect(ents, rels, "design")
                except Exception as e:
                    logger.warning("Skip %s: %s", filepath.name, e)

        # ALL fleet-elevation design docs
        print("  Parsing fleet-elevation docs...", flush=True)
        for elev_dir in sorted((FLEET_DIR / "docs").rglob("fleet-elevation*")):
            if elev_dir.is_dir():
                for filepath in sorted(elev_dir.glob("*.md")):
                    try:
                        ents, rels = parse_markdown_doc(filepath)
                        _collect(ents, rels, "design")
                    except Exception as e:
                        logger.warning("Skip %s: %s", filepath.name, e)

        # ALL plans
        plans_dir = FLEET_DIR / "docs" / "milestones" / "active" / "plans"
        if plans_dir.exists():
            for filepath in sorted(plans_dir.glob("*.md")):
                try:
                    ents, rels = parse_markdown_doc(filepath)
                    _collect(ents, rels, "design")
                except Exception as e:
                    logger.warning("Skip %s: %s", filepath.name, e)

        # ALL agent CLAUDE.md templates
        agent_template_dir = FLEET_DIR / "agents" / "_template" / "CLAUDE.md"
        if agent_template_dir.exists():
            print("  Parsing agent templates...", flush=True)
            for filepath in sorted(agent_template_dir.glob("*.md")):
                try:
                    ents, rels = parse_agent_claude_md(filepath)
                    _collect(ents, rels, "agent_template")
                except Exception as e:
                    logger.warning("Skip %s: %s", filepath.name, e)
        # Other agent template files
        agent_tmpl = FLEET_DIR / "agents" / "_template"
        if agent_tmpl.exists():
            for filepath in sorted(agent_tmpl.glob("*.md")):
                try:
                    ents, rels = parse_markdown_doc(filepath)
                    _collect(ents, rels, "agent_template")
                except Exception as e:
                    logger.warning("Skip %s: %s", filepath.name, e)

        # AICP SKILL.md files (78 skills from devops-expert-local-ai repo)
        if AICP_SKILLS_DIR.exists():
            print("  Parsing AICP skills...", flush=True)
            for skill_dir in sorted(AICP_SKILLS_DIR.iterdir()):
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        ents, rels = parse_skill_md(skill_file)
                        _collect(ents, rels, "skill")
                    except Exception as e:
                        logger.warning("Skip %s: %s", skill_dir.name, e)

        logger.info("Sources parsed: %d entities, %d relationships from %d files",
                     len(all_entities), len(all_relationships), result.files_processed)

        # Insert
        if not self.client.health():
            logger.error("LightRAG not reachable")
            return result

        print(f"  Inserting {len(all_entities)} source entities...", flush=True)
        for i, ent in enumerate(all_entities):
            ok, msg = self.client.create_entity(ent)
            if ok:
                result.entities_ok += 1
            else:
                result.entities_fail += 1
                if result.entities_fail <= 5:
                    print(f"    FAIL entity [{ent.name}]: {msg[:100]}", flush=True)
            if (i + 1) % 25 == 0 or i + 1 == len(all_entities):
                print(f"    {i+1}/{len(all_entities)} ({result.entities_ok} ok, "
                      f"{result.entities_fail} fail)", flush=True)
            time.sleep(0.1)
        print(f"  Source entities done: {result.entities_ok} ok, "
              f"{result.entities_fail} fail", flush=True)

        print(f"  Inserting {len(all_relationships)} source relationships...", flush=True)
        for i, rel in enumerate(all_relationships):
            ok, msg = self.client.create_relationship(rel)
            if ok:
                result.relationships_ok += 1
            else:
                result.relationships_fail += 1
                if result.relationships_fail <= 10:
                    print(f"    FAIL rel [{rel.src} → {rel.tgt}]: {msg[:100]}", flush=True)
            if (i + 1) % 25 == 0 or i + 1 == len(all_relationships):
                print(f"    {i+1}/{len(all_relationships)} ({result.relationships_ok} ok, "
                      f"{result.relationships_fail} fail)", flush=True)
            time.sleep(0.1)
        print(f"  Source relationships done: {result.relationships_ok} ok, "
              f"{result.relationships_fail} fail", flush=True)

        return result

    def _find_changed(self) -> list[Path]:
        """Find files changed since last sync."""
        state = {}
        if SYNC_STATE_FILE.exists():
            state = json.loads(SYNC_STATE_FILE.read_text())

        changed = []
        for md_file in sorted(self.kb_dir.rglob("*.md")):
            key = str(md_file.relative_to(FLEET_DIR))
            mtime = md_file.stat().st_mtime
            if mtime > state.get(key, 0):
                changed.append(md_file)
        return changed

    def _save_state(self) -> None:
        """Save current file mtimes."""
        state = {}
        for md_file in sorted(self.kb_dir.rglob("*.md")):
            key = str(md_file.relative_to(FLEET_DIR))
            state[key] = md_file.stat().st_mtime
        SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


# ── CLI ────────────────────────────────────────────────────────────

def main():
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="KB → LightRAG graph sync")
    parser.add_argument("--full", action="store_true", help="Full sync (all files)")
    parser.add_argument("--sync", action="store_true", help="Incremental sync (changed only)")
    parser.add_argument("--stats", action="store_true", help="Show statistics (no insert)")
    parser.add_argument("--url", default=DEFAULT_LIGHTRAG_URL, help="LightRAG URL")
    args = parser.parse_args()

    if not any([args.full, args.sync, args.stats]):
        args.stats = True

    sync = KBGraphSync(lightrag_url=args.url)

    if args.stats:
        s = sync.stats()
        print(f"\nKB Graph: {s['entities']} entities, {s['relationships']} relationships "
              f"from {s['files']} files")
        print("\nEntity types:")
        for t, c in s["entity_types"].items():
            print(f"  {t:20s} {c:4d}")
        print("\nTop relationship types:")
        for t, c in s["rel_types"].items():
            print(f"  {t:25s} {c:4d}")
        print("\nMost connected:")
        for n, c in s["most_connected"].items():
            print(f"  {n:40s} {c:4d}")

    if args.full:
        result = sync.full_sync()
        print(f"\nResult: {result.entities_ok} entities, {result.relationships_ok} relationships "
              f"in {result.duration_seconds:.1f}s")
        if result.errors:
            print(f"Errors: {result.errors}")

    if args.sync:
        result = sync.incremental()
        print(f"\nResult: {result.entities_ok} entities, {result.relationships_ok} relationships "
              f"in {result.duration_seconds:.1f}s")


if __name__ == "__main__":
    main()
