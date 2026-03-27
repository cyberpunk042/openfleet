#!/usr/bin/env bash
set -euo pipefail

# Register skill packs, sync, and apply category/risk metadata.
#
# Flow:
#   1. Register each pack from config/skill-packs.yaml
#   2. Sync each pack (discover skills from repo)
#   3. Apply category/risk from config/skill-assignments.yaml
#      (uses POST /marketplace upsert — patched to accept category/risk)

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$FLEET_DIR/.env" 2>/dev/null || true

MC_URL="${OCF_MISSION_CONTROL_URL:-http://localhost:8000}"
TOKEN="${LOCAL_AUTH_TOKEN:-}"
PACKS_CONFIG="$FLEET_DIR/config/skill-packs.yaml"
ASSIGNMENTS="$FLEET_DIR/config/skill-assignments.yaml"

if [[ -z "$TOKEN" ]]; then echo "ERROR: No LOCAL_AUTH_TOKEN" >&2; exit 1; fi
if [[ ! -f "$PACKS_CONFIG" ]]; then echo "No skill-packs.yaml, skipping"; exit 0; fi

python3 << PYEOF
import yaml, json, sys
import urllib.request, urllib.error

MC_URL = "$MC_URL"
TOKEN = "$TOKEN"

def api(method, path, data=None):
    url = f"{MC_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except: return {"detail": str(e)}

# Load configs
with open("$PACKS_CONFIG") as f:
    packs_cfg = yaml.safe_load(f)

assignments = {}
if "$ASSIGNMENTS" and __import__("os").path.exists("$ASSIGNMENTS"):
    with open("$ASSIGNMENTS") as f:
        a_cfg = yaml.safe_load(f)
    for s in a_cfg.get("skills", []):
        assignments[s["name"]] = s

packs = packs_cfg.get("packs", [])
if not packs:
    print("No packs configured")
    sys.exit(0)

# Get existing packs
existing_resp = api("GET", "/api/v1/skills/packs")
existing_packs = {}
if isinstance(existing_resp, dict):
    for p in existing_resp.get("items", []):
        existing_packs[p.get("source_url", "")] = p

print("=== Registering Skill Packs ===")

for pack_cfg in packs:
    name = pack_cfg["name"]
    url = pack_cfg["source_url"]
    desc = pack_cfg.get("description", "")
    branch = pack_cfg.get("branch", "main")
    defaults = pack_cfg.get("defaults", {})

    # Register or get existing
    if url in existing_packs:
        pack = existing_packs[url]
        pack_id = pack["id"]
        print(f"  EXISTS: {name}")
    else:
        result = api("POST", "/api/v1/skills/packs", {
            "source_url": url, "name": name,
            "description": desc, "branch": branch,
        })
        pack_id = result.get("id")
        if not pack_id:
            print(f"  FAIL: {name} — {result.get('detail', '?')}")
            continue
        print(f"  REGISTERED: {name}")

    # Sync
    sync = api("POST", f"/api/v1/skills/packs/{pack_id}/sync")
    synced = sync.get("synced", 0)
    created = sync.get("created", 0)
    print(f"  SYNCED: {synced} skills (new: {created})")

# Get gateway ID for marketplace query
agents_resp = api("GET", "/api/v1/agents")
gw_id = None
for a in (agents_resp.get("items", []) if isinstance(agents_resp, dict) else []):
    if a.get("gateway_id"):
        gw_id = str(a["gateway_id"])
        break

if not gw_id:
    print("WARN: No gateway found, skipping metadata update")
    sys.exit(0)

# Apply category/risk from assignments
marketplace = api("GET", f"/api/v1/skills/marketplace?gateway_id={gw_id}&limit=200")
skills_list = marketplace if isinstance(marketplace, list) else marketplace.get("items", [])

print()
print("=== Applying Skill Metadata ===")
updated = 0
for skill in skills_list:
    skill_name = skill.get("name", "")
    source_url = skill.get("source_url", "")
    current_cat = skill.get("category")
    current_risk = skill.get("risk")

    # Check assignments for overrides
    assignment = assignments.get(skill_name, {})
    target_cat = assignment.get("category") or packs_cfg.get("packs", [{}])[0].get("defaults", {}).get("category")
    target_risk = assignment.get("risk") or packs_cfg.get("packs", [{}])[0].get("defaults", {}).get("risk")

    needs_update = False
    update_data = {"source_url": source_url, "name": skill_name}
    if target_cat and current_cat != target_cat:
        update_data["category"] = target_cat
        needs_update = True
    if target_risk and current_risk != target_risk:
        update_data["risk"] = target_risk
        needs_update = True

    if needs_update:
        result = api("POST", "/api/v1/skills/marketplace", update_data)
        if result.get("id"):
            new_cat = result.get("category", "?")
            new_risk = result.get("risk", "?")
            print(f"  UPDATED: {skill_name} → category={new_cat}, risk={new_risk}")
            updated += 1
        else:
            print(f"  FAIL: {skill_name} — {result.get('detail', '?')}")
    else:
        if current_cat or current_risk:
            pass  # already set
        # else: no override configured

print(f"  Updated: {updated} skills")
print()
print("Done.")
PYEOF