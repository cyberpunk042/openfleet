#!/usr/bin/env python3
"""kb-to-graph.py — Parse KB ## Relationships into LightRAG custom_kg.

Reads all 219+ KB markdown files, extracts entities from metadata and
explicit relationships from ## Relationships sections, builds a custom_kg
dict, and inserts into LightRAG via ainsert_custom_kg REST API.

NO LLM needed. NO ML models. Just parsing structured markdown we wrote.

Usage:
    python scripts/kb-to-graph.py --stats                    # dry run, show graph stats
    python scripts/kb-to-graph.py --output data/custom_kg.json  # export to JSON
    python scripts/kb-to-graph.py --insert                   # insert into LightRAG
    python scripts/kb-to-graph.py --insert --stats           # both
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

FLEET_DIR = Path(__file__).parent.parent
KB_DIR = FLEET_DIR / "docs" / "knowledge-map" / "kb"
MANUALS_DIR = FLEET_DIR / "docs" / "knowledge-map"
LIGHTRAG_URL = "http://localhost:9621"


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
    "skill (aicp)": "skill",
    "skill (aicp lifecycle)": "skill",
    "skill (slash command)": "skill",
    "skill (superpowers plugin)": "skill",
    "agent file (onion layer)": "layer",
    "infrastructure component": "infrastructure",
    "infrastructure component (fleet module)": "infrastructure",
    "research finding": "research",
    "research conclusion": "research",
    "research conclusion / plan": "research",
}


def normalize_type(raw: str) -> str:
    raw_lower = raw.lower().strip()
    for pattern, etype in TYPE_MAP.items():
        if pattern in raw_lower:
            return etype
    return "concept"


# ── KB file parser ─────────────────────────────────────────────────

def parse_kb_file(filepath: Path) -> dict:
    """Parse one KB markdown file into entity + relationships."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Title from first H1
    title = filepath.stem
    for line in lines:
        if line.startswith("# "):
            title = line.lstrip("# ").strip()
            break

    # Metadata
    entity_type = "concept"
    description_parts = []
    for line in lines[:20]:
        if "**Type:**" in line:
            entity_type = normalize_type(line.split("**Type:**")[1].strip())
        elif "**Purpose" in line or "**Role:**" in line:
            val = line.split(":**", 1)[1].strip() if ":**" in line else ""
            if val:
                description_parts.append(val)

    # What It Does / Purpose section — first paragraph
    for section_name in ["What It Does", "What It Actually Does", "Purpose",
                         "What This System Does", "What It Is", "Mission"]:
        section = _extract_section(text, section_name)
        if section:
            first_para = section.strip().split("\n\n")[0].strip()
            if first_para and len(first_para) > 20:
                description_parts.append(first_para[:300])
                break

    description = " ".join(description_parts) if description_parts else title

    # Fleet Use Case section
    fleet_use = _extract_section(text, "Fleet Use Case")
    if fleet_use:
        first_para = fleet_use.strip().split("\n\n")[0].strip()
        if first_para and len(first_para) > 20:
            description += " " + first_para[:200]

    # Relationships section
    relationships = []
    rel_section = _extract_section(text, "Relationships")
    if rel_section:
        for line in rel_section.strip().split("\n"):
            line = line.strip()
            if not line.startswith("-"):
                continue
            parsed = _parse_rel_line(line[2:].strip(), title)
            if parsed:
                relationships.extend(parsed)

    return {
        "entity_name": title,
        "entity_type": entity_type,
        "description": description[:500],
        "relationships": relationships,
        "source_file": str(filepath.relative_to(FLEET_DIR)),
        "branch": filepath.parent.name,
    }


def _extract_section(text: str, header: str) -> str | None:
    """Extract content between ## header and next ## header."""
    sections = text.split("\n## ")
    for section in sections:
        if section.strip().lower().startswith(header.lower()):
            content = "\n".join(section.strip().split("\n")[1:])
            return content
    return None


def _parse_rel_line(line: str, source: str) -> list[dict]:
    """Parse one relationship line into edge(s).

    Handles:
      CONNECTS TO: S01 methodology (stage checks, readiness gates)
      READS FROM: mc_client.py, context_assembly.py
      USED BY: software-engineer, qa-engineer
      INSTALLED FOR: ALL agents (default)
    """
    match = re.match(r"^([A-Z][A-Z /\-]+?):\s*(.+)$", line)
    if not match:
        return []

    rel_type = match.group(1).strip()
    targets_raw = match.group(2).strip()

    # Skip non-relationship lines
    skip = ["NOT YET", "CRITICAL", "PERFORMANCE", "HISTORICAL",
            "CAUTION", "TIER", "KEY INSIGHT", "ANTI-CORRUPTION"]
    if any(rel_type.startswith(s) for s in skip):
        return []

    # Split on commas but preserve parenthetical context
    # "S01 methodology (stage checks), S02 immune system (doctor)"
    results = []
    # First try splitting by known separators
    parts = re.split(r",\s*(?=[A-Z])|,\s*(?=[a-z_])", targets_raw)

    for part in parts:
        part = part.strip().rstrip(".")
        if not part or len(part) < 2:
            continue

        # Extract parenthetical context
        context = ""
        ctx_match = re.search(r"\(([^)]+)\)", part)
        if ctx_match:
            context = ctx_match.group(1)
            part_clean = part[:ctx_match.start()].strip()
        else:
            part_clean = part

        # Skip pure descriptions without a target
        if part_clean.lower() in ("none", "n/a", "yes", "no", "all"):
            continue
        if len(part_clean) < 2:
            continue

        desc = f"{source} {rel_type.lower()} {part_clean}"
        if context:
            desc += f" ({context})"

        results.append({
            "src_id": source,
            "tgt_id": part_clean,
            "description": desc,
            "keywords": rel_type.lower(),
            "weight": 1.0,
        })

    return results


# ── Build custom_kg ────────────────────────────────────────────────

def build_custom_kg(kb_dir: Path) -> dict:
    """Parse all KB files and build LightRAG custom_kg dict."""
    md_files = sorted(kb_dir.rglob("*.md"))
    print(f"Found {len(md_files)} KB files\n")

    all_entries = []
    for filepath in md_files:
        try:
            entry = parse_kb_file(filepath)
            all_entries.append(entry)
        except Exception as e:
            print(f"  SKIP {filepath.name}: {e}")

    # Build entities
    entities = []
    seen_entities = set()
    for entry in all_entries:
        name = entry["entity_name"]
        if name.upper() not in seen_entities:
            entities.append({
                "entity_name": name,
                "entity_type": entry["entity_type"],
                "description": entry["description"],
                "source_id": entry["source_file"],
            })
            seen_entities.add(name.upper())

    # Build relationships + discover referenced entities
    relationships = []
    seen_rels = set()
    for entry in all_entries:
        for rel in entry["relationships"]:
            key = (rel["src_id"].upper(), rel["keywords"], rel["tgt_id"].upper())
            if key not in seen_rels:
                relationships.append(rel)
                seen_rels.add(key)

                # Add target as entity if not already known
                tgt_upper = rel["tgt_id"].upper()
                if tgt_upper not in seen_entities:
                    entities.append({
                        "entity_name": rel["tgt_id"],
                        "entity_type": "reference",
                        "description": f"Referenced by {rel['src_id']}",
                        "source_id": entry["source_file"],
                    })
                    seen_entities.add(tgt_upper)

    # Build chunks (full text per file)
    chunks = []
    for entry in all_entries:
        filepath = FLEET_DIR / entry["source_file"]
        chunks.append({
            "content": filepath.read_text(encoding="utf-8"),
            "source_id": entry["source_file"],
        })

    return {
        "chunks": chunks,
        "entities": entities,
        "relationships": relationships,
    }


def print_stats(kg: dict) -> None:
    """Print graph statistics."""
    print(f"\n{'='*60}")
    print(f"  Knowledge Graph Statistics")
    print(f"{'='*60}")
    print(f"  Entities:      {len(kg['entities'])}")
    print(f"  Relationships: {len(kg['relationships'])}")
    print(f"  Chunks:        {len(kg['chunks'])}")

    # Entity type distribution
    type_counts = {}
    for e in kg["entities"]:
        t = e["entity_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"\n  Entity types:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {t:20s} {c:4d}")

    # Relationship type distribution
    rel_counts = {}
    for r in kg["relationships"]:
        k = r["keywords"]
        rel_counts[k] = rel_counts.get(k, 0) + 1
    print(f"\n  Relationship types:")
    for k, c in sorted(rel_counts.items(), key=lambda x: -x[1]):
        print(f"    {k:25s} {c:4d}")

    # Most connected entities
    connections = {}
    for r in kg["relationships"]:
        connections[r["src_id"]] = connections.get(r["src_id"], 0) + 1
        connections[r["tgt_id"]] = connections.get(r["tgt_id"], 0) + 1
    print(f"\n  Most connected entities:")
    for name, count in sorted(connections.items(), key=lambda x: -x[1])[:15]:
        print(f"    {name:40s} {count:4d} connections")


def insert_to_lightrag(kg: dict, url: str) -> None:
    """Insert entities and relationships into LightRAG via graph API."""
    import urllib.request

    def _post(endpoint: str, payload: dict) -> bool:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status < 300
        except Exception:
            return False

    # Insert entities via /graph/entity/create
    print(f"\n  Inserting {len(kg['entities'])} entities...")
    ok = 0
    fail = 0
    for i, ent in enumerate(kg["entities"]):
        success = _post("/graph/entity/create", {
            "entity_name": ent["entity_name"],
            "entity_data": {
                "entity_type": ent["entity_type"],
                "description": ent["description"],
                "source_id": ent.get("source_id", ""),
            },
        })
        if success:
            ok += 1
        else:
            fail += 1
        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(kg['entities'])} entities ({ok} ok, {fail} fail)")
    print(f"    Entities: {ok} ok, {fail} fail")

    # Insert relationships via /graph/relation/create
    print(f"\n  Inserting {len(kg['relationships'])} relationships...")
    ok = 0
    fail = 0
    for i, rel in enumerate(kg["relationships"]):
        success = _post("/graph/relation/create", {
            "source_entity": rel["src_id"],
            "target_entity": rel["tgt_id"],
            "relation_data": {
                "description": rel["description"],
                "keywords": rel["keywords"],
                "weight": rel.get("weight", 1.0),
                "source_id": rel.get("source_id", ""),
            },
        })
        if success:
            ok += 1
        else:
            fail += 1
        if (i + 1) % 200 == 0:
            print(f"    {i+1}/{len(kg['relationships'])} relationships ({ok} ok, {fail} fail)")
    print(f"    Relationships: {ok} ok, {fail} fail")


# ── Sync — detect changes and sync incrementally ──────────────────

SYNC_STATE_FILE = FLEET_DIR / ".kb-graph-sync.json"


def load_sync_state() -> dict:
    """Load previous sync state (file mtimes)."""
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text())
    return {}


def save_sync_state(state: dict) -> None:
    """Save sync state."""
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


def find_changed_files(kb_dir: Path) -> tuple[list[Path], dict]:
    """Find KB files changed since last sync."""
    state = load_sync_state()
    changed = []
    new_state = {}

    for md_file in sorted(kb_dir.rglob("*.md")):
        key = str(md_file.relative_to(FLEET_DIR))
        mtime = md_file.stat().st_mtime
        new_state[key] = mtime

        old_mtime = state.get(key, 0)
        if mtime > old_mtime:
            changed.append(md_file)

    return changed, new_state


def sync_to_lightrag(url: str, full: bool = False) -> None:
    """Sync KB changes to LightRAG. Incremental by default."""
    if full:
        changed = sorted(KB_DIR.rglob("*.md"))
        print(f"Full sync: {len(changed)} files")
    else:
        changed, new_state = find_changed_files(KB_DIR)
        if not changed:
            print("No KB changes since last sync.")
            return
        print(f"Incremental sync: {len(changed)} changed files")

    # Parse only changed files
    entities = []
    relationships = []
    seen_entities = set()
    seen_rels = set()

    for filepath in changed:
        try:
            entry = parse_kb_file(filepath)

            name = entry["entity_name"]
            if name.upper() not in seen_entities:
                entities.append({
                    "entity_name": name,
                    "entity_type": entry["entity_type"],
                    "description": entry["description"],
                    "source_id": entry["source_file"],
                })
                seen_entities.add(name.upper())

            for rel in entry["relationships"]:
                key = (rel["src_id"].upper(), rel["keywords"], rel["tgt_id"].upper())
                if key not in seen_rels:
                    relationships.append(rel)
                    seen_rels.add(key)

                    tgt_upper = rel["tgt_id"].upper()
                    if tgt_upper not in seen_entities:
                        entities.append({
                            "entity_name": rel["tgt_id"],
                            "entity_type": "reference",
                            "description": f"Referenced by {rel['src_id']}",
                            "source_id": entry["source_file"],
                        })
                        seen_entities.add(tgt_upper)
        except Exception as e:
            print(f"  SKIP {filepath.name}: {e}")

    print(f"  Parsed: {len(entities)} entities, {len(relationships)} relationships")

    # Insert
    kg = {"entities": entities, "relationships": relationships, "chunks": []}
    insert_to_lightrag(kg, url)

    # Save sync state (only on full sync or after success)
    if not full:
        save_sync_state(new_state)
    else:
        _, new_state = find_changed_files(KB_DIR)
        save_sync_state(new_state)

    print("  Sync complete.")


# ── Main ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse KB ## Relationships into LightRAG knowledge graph"
    )
    parser.add_argument("--stats", action="store_true", help="Print graph statistics (dry run)")
    parser.add_argument("--output", "-o", help="Export custom_kg to JSON file")
    parser.add_argument("--insert", action="store_true", help="Full insert into LightRAG")
    parser.add_argument("--sync", action="store_true", help="Incremental sync (changed files only)")
    parser.add_argument("--url", default=LIGHTRAG_URL, help="LightRAG API URL")
    args = parser.parse_args()

    if not any([args.stats, args.output, args.insert, args.sync]):
        args.stats = True

    if args.sync:
        sync_to_lightrag(args.url)
        return

    if args.insert:
        sync_to_lightrag(args.url, full=True)
        return

    kg = build_custom_kg(KB_DIR)

    if args.stats:
        print_stats(kg)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(kg, indent=2))
        print(f"\n  Written to {args.output}")


if __name__ == "__main__":
    main()
