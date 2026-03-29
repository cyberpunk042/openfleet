# Workstream 1: Standards & Discipline

## Goal

Every commit — human or agent — follows the same standards. The codebase is navigable,
auditable, and professional. No batch dumps, no mystery changes.

## What Exists

- Agents commit via `git commit` in their worktrees (when they do at all)
- No commit message format enforced
- No changelog generation
- No shared coding standards document
- SOUL.md has role instructions but no standards section

## What's Needed

### M44: Conventional Commits Enforcement

**Scope:** All commits in openclaw-fleet and agent-produced work.

**Format:** `type(scope): description` per https://www.conventionalcommits.org/en/v1.0.0/

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `ci`, `test`, `style`, `perf`

**Tasks:**
1. Add commit message convention to `agents/_template/MC_WORKFLOW.md`
   - Agents must use conventional commits for all worktree commits
   - Include examples in the workflow section
2. Add a `.commitlintrc.yaml` to the fleet repo (for human and CI validation)
3. Add a git commit-msg hook (optional, for local enforcement)
4. Update all agent SOUL.md with the convention (via `push-soul.sh`)

### M45: Changelog Generation

**Scope:** Auto-generate CHANGELOG.md from conventional commit history.

**Tasks:**
1. Add `scripts/generate-changelog.sh` using `git log` + conventional commit parsing
   - Groups by type (Features, Fixes, Docs, etc.)
   - Includes task ID references where available
2. Add `make changelog` target
3. Agent commits should reference task IDs: `feat(nnrt): add type hints [task:ea36a032]`

### M46: Shared Coding Standards

**Scope:** Common standards document that all agents read.

**Tasks:**
1. Create `agents/_template/STANDARDS.md` with:
   - Python: type hints, docstrings, ruff config
   - Bash: shellcheck, set -euo pipefail, portable patterns
   - Git: conventional commits, branch naming (`fleet/<agent>/<task-short>`)
   - Testing: every feature needs tests
   - Security: no secrets in code, no hardcoded paths
2. Include STANDARDS.md in SOUL.md push (agents read it at session start)
3. Add to AGENTS.md read order (after SOUL.md, before TOOLS.md)

### M47: Frequent Small Commits

**Scope:** Agents commit incrementally, not in one big dump.

**Tasks:**
1. Update MC_WORKFLOW.md: "Commit after each meaningful change, not at the end"
2. Add commit guidance to task dispatch message:
   - "Commit early and often. Each commit should be one logical change."
3. Agent SOUL.md should say: "Never batch all changes into one commit"

## Verification

- [ ] All new commits follow `type(scope): description`
- [ ] `make changelog` produces a readable CHANGELOG.md
- [ ] Agents produce 2+ commits per non-trivial task
- [ ] STANDARDS.md exists and is readable by agents