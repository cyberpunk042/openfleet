# Workstream 2: Skills Ecosystem

## Goal

Fleet agents use skills from multiple sources — OpenClaw built-in, ClawHub registry,
OCMC marketplace, GitHub skill packs, and fleet-specific skills. Skills are discoverable,
installable, and associated with agents through standard mechanisms.

## What Exists

### OpenClaw Skill System (Built-in)
- **SKILL.md format**: YAML frontmatter + Markdown instructions
- **Discovery**: scans workspace, bundled, personal, project skill dirs
- **ClawHub**: registry with `openclaw skills search/install/update`
- **53 bundled skills**: github, slack, discord, weather, coding-agent, skill-creator, etc.
- **Precedence**: workspace > project > personal > managed > bundled
- **CLI**: `openclaw skills list`, `openclaw skills install <slug>`
- **Gateway integration**: `skills.status`, `skills.install`, `skills.clawhub.install`

### OCMC Skills Marketplace
- **Skill Packs**: register GitHub repos as skill sources
- **API**: `POST /skills/packs` → `POST /skills/packs/{id}/sync` → discover SKILL.md files
- **Installation**: `POST /skills/marketplace/{id}/install` → dispatches to Gateway Agent
- **Discovery**: `skills_index.json` (indexed) or recursive SKILL.md scan (fallback)
- **Security**: GitHub-only, HTTPS-only, no localhost/private IPs
- **Scoping**: organization-wide catalog, gateway-scoped installation

### External Skill Repos (Known)
- https://github.com/anthropics/skills — Anthropic's official Claude Code skills
- https://github.com/ComposioHQ/awesome-claude-skills — Community collection
- ClawHub registry (OpenClaw's skill store)

## What's Needed

### M48: Inventory Current Skills

**Scope:** Know exactly what skills are available and which agents use them.

**Tasks:**
1. Run `openclaw skills list` and document all available skills
2. Run `openclaw skills check` to see which are ready vs missing requirements
3. Check OCMC marketplace state: `GET /skills/marketplace?gateway_id=<id>`
4. Document in `docs/skills-inventory.md`:
   - Skill name, source (bundled/clawhub/pack), status (ready/missing deps)
   - Relevance to fleet agents (which agent would use which skill)

### M49: Register External Skill Packs in OCMC

**Scope:** Add useful skill repos to the OCMC marketplace.

**Tasks:**
1. Register `anthropics/skills` as a skill pack:
   ```
   POST /skills/packs
   { "source_url": "https://github.com/anthropics/skills", "name": "Anthropic Official" }
   POST /skills/packs/{id}/sync
   ```
2. Register `ComposioHQ/awesome-claude-skills` as a skill pack
3. Evaluate which discovered skills are useful for fleet agents
4. Script this: `scripts/register-skill-packs.sh`
5. Add to `setup-mc.sh` (auto-register packs after MC setup)

### M50: Install Skills on Gateway

**Scope:** Install selected skills on the fleet gateway.

**Tasks:**
1. From the OCMC marketplace, install relevant skills:
   - github (PR/issue management)
   - coding-agent (delegate coding tasks)
   - Any NNRT-relevant skills
2. Via ClawHub: `openclaw skills install <slug>` for OpenClaw-native skills
3. Script: `scripts/install-skills.sh` — installs a curated set of skills
4. Add to setup.sh flow

### M51: Fleet-Specific Skills

**Scope:** Create custom skills for fleet operations.

**Tasks:**
1. Create fleet skills in `skills/` directory (fleet workspace):
   - `fleet-task-update` — standardized MC task update workflow
   - `fleet-commit` — conventional commit with task reference
   - `fleet-report` — post structured report to MC board memory
2. Use OpenClaw's `skill-creator` to scaffold them properly
3. These become available to all agents via workspace skill discovery

### M52: Skill Association per Agent Role

**Scope:** Different agents get different skill sets.

**Tasks:**
1. Evaluate per-agent skill needs:
   - architect: system-design, architecture-review skills
   - software-engineer: coding-agent, github, fleet-commit
   - qa-engineer: test-runner, coverage-report
   - devops: infrastructure, monitoring, fleet-task-update
   - technical-writer: documentation, api-docs
2. Configure per-agent skill allowlists in openclaw.json:
   ```json
   "agents.list[].skills": { "allowBundled": ["github", "coding-agent"] }
   ```
3. Document skill-agent mapping in `docs/skills-inventory.md`

## Open Questions

1. Can OCMC skills and OpenClaw skills coexist? (OCMC installs to `{workspace}/skills/`,
   OpenClaw discovers from the same path — should work)
2. Does the Gateway Agent properly handle OCMC skill install instructions?
   (Need to test: register a pack, sync, install a skill, verify it appears in `openclaw skills list`)
3. Can we create a fleet skill pack repo (`openclaw-fleet-skills`) and register it in OCMC?

## Verification

- [ ] `openclaw skills list` shows installed skills
- [ ] OCMC marketplace shows registered packs and skills
- [ ] At least one skill installed and usable by an agent
- [ ] Fleet-specific skills created and discoverable
- [ ] `scripts/install-skills.sh` works from clean setup