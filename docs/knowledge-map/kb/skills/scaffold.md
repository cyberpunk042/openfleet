# scaffold

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/scaffold/SKILL.md
**Invocation:** /scaffold <project-name> [path-to-architecture-doc]
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Create a fully structured, immediately runnable project from an architecture document. Not just directories — generates ALL boilerplate: README, CLAUDE.md, .gitignore, package manifest, config files, Docker, CI pipeline, test structure, project state tracking. For each architecture component: creates module directory, stub implementation with correct interfaces, corresponding test file. Initializes git and creates initial commit.

## Input

- Project name: first argument
- Architecture doc: second argument (default: `docs/architecture.md`)

## Process

1. Read architecture document
2. Create directory structure from architecture
3. Generate ALL boilerplate files:
   - README.md — project overview, WORKING setup instructions
   - CLAUDE.md — AI assistant instructions, conventions, architecture reference
   - .gitignore — appropriate for the tech stack
   - Package manifest — pyproject.toml / package.json / Cargo.toml / go.mod
   - Config files — linter, formatter, editor config
   - Docker — Dockerfile + docker-compose.yaml if applicable
   - CI — GitHub Actions workflow (lint, test, build)
   - Test structure — test directory mirroring source
   - .aicp/state.yaml — project state for AICP tracking
4. For each component in architecture:
   - Create module/package directory
   - Create `__init__.py` or equivalent with docstring
   - Create stub implementation with the right interfaces
   - Create corresponding test file
5. Initialize git repository
6. Create initial commit

## Rules (non-negotiable)

- Every file must have REAL content, not just placeholders
- Follow conventions from the architecture
- README must include working setup instructions (not "TODO: add setup")
- CLAUDE.md must describe the architecture accurately
- Tests must actually RUN (even if trivially)
- Project must be immediately runnable after scaffold

## Output

Working project directory. Report what was created + what user should do next.

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| Architect | ESSENTIAL | Creates project structure from their architecture |
| Engineer | ESSENTIAL | Sets up new project or component |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| work | Create the project structure (after architecture is approved) |

## Relationships

- DEPENDS ON: architecture-propose (architecture doc must exist — scaffold reads it)
- DEPENDS ON: architecture-review (architecture should be reviewed before scaffolding)
- FOLLOWED BY: foundation-deps (install dependencies in scaffolded project)
- FOLLOWED BY: foundation-config (set up configuration management)
- FOLLOWED BY: foundation-testing (set up test infrastructure)
- FOLLOWED BY: foundation-ci (set up CI/CD pipeline)
- PRODUCES: complete project directory with git initialized
- CONNECTS TO: fleet_commit (commit the scaffolded structure)
- CONNECTS TO: IaC principle — "everything must be reproducible" — scaffold creates a from-scratch reproducible project
- VARIANT: scaffold-monorepo (monorepo structure with workspaces)
- VARIANT: scaffold-subagent (new fleet agent directory)
- CONNECTS TO: openclaw-add-agent (register scaffolded agent in gateway)
