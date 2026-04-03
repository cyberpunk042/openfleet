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
    "KEY PRINCIPLE", "ZERO RISK", "DANGER",
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

    # Description from What It Does / Purpose / Mission
    description = title
    for section_name in ["What It Does", "What It Actually Does", "Purpose",
                         "What This System Does", "What It Is", "Mission",
                         "What the Navigator Is"]:
        section = _extract_section(text, section_name)
        if section:
            first_para = section.strip().split("\n\n")[0].strip()
            if first_para and len(first_para) > 20:
                description = first_para[:400]
                break

    source_file = str(filepath.relative_to(FLEET_DIR))
    entity = Entity(name=title, entity_type=entity_type,
                    description=description, source_file=source_file)

    # Relationships
    relationships = []
    rel_section = _extract_section(text, "Relationships")
    if rel_section:
        for line in rel_section.strip().split("\n"):
            line = line.strip()
            if not line.startswith("-"):
                continue
            rels = _parse_rel_line(line[2:].strip(), title, source_file)
            relationships.extend(rels)

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

        ctx_match = re.search(r"\(([^)]+)\)", part)
        context = ctx_match.group(1) if ctx_match else ""
        part_clean = part[:ctx_match.start()].strip() if ctx_match else part

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

    def create_entity(self, entity: Entity) -> tuple[bool, str]:
        payload = {
            "entity_name": entity.name.upper(),
            "entity_data": {
                "entity_type": entity.entity_type,
                "description": entity.description,
                "source_id": entity.source_file,
            },
        }
        return self._post("/graph/entity/create", payload)

    def create_relationship(self, rel: Relationship) -> tuple[bool, str]:
        payload = {
            "source_entity": rel.src.upper(),
            "target_entity": rel.tgt.upper(),
            "relation_data": {
                "description": rel.description,
                "keywords": rel.rel_type,
                "weight": rel.weight,
                "source_id": rel.source_file,
            },
        }
        return self._post("/graph/relation/create", payload)

    def _post(self, endpoint: str, payload: dict) -> tuple[bool, str]:
        data = json.dumps(payload).encode()
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
            return (False, f"HTTP {e.code}: {body}")
        except Exception as e:
            return (False, str(e))


# ── Sync engine ────────────────────────────────────────────────────

class KBGraphSync:
    """Synchronizes KB entries to LightRAG knowledge graph."""

    def __init__(self, lightrag_url: str = DEFAULT_LIGHTRAG_URL,
                 kb_dir: Path = KB_DIR):
        self.client = LightRAGClient(lightrag_url)
        self.kb_dir = kb_dir

    def full_sync(self) -> SyncResult:
        """Sync all KB files to graph."""
        files = sorted(self.kb_dir.rglob("*.md"))
        logger.info("Full sync: %d KB files", len(files))
        result = self._sync_files(files)
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

            if (i + 1) % 50 == 0:
                print(f"    {i+1}/{len(entities)} ({result.entities_ok} ok, "
                      f"{result.entities_fail} fail)", flush=True)

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

            if (i + 1) % 100 == 0:
                print(f"    {i+1}/{len(relationships)} ({result.relationships_ok} ok, "
                      f"{result.relationships_fail} fail)", flush=True)

        print(f"  Relationships done: {result.relationships_ok} ok, "
              f"{result.relationships_fail} fail", flush=True)

        result.duration_seconds = time.time() - t0
        logger.info("Sync complete in %.1fs", result.duration_seconds)
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
