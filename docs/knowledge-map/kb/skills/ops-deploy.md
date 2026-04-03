# ops-deploy

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/ops-deploy/SKILL.md
**Invocation:** /ops-deploy [environment: dev|staging|prod]
**Effort:** high
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Execute a deployment with pre-flight safety checks, build, deploy, smoke test, and automatic rollback on failure. Enforces: never deploy with failing tests, always have a rollback plan, smoke test immediately, log every deployment.

## Process

1. **Pre-flight checks:** verify tests pass, lint clean, no uncommitted changes, correct branch
2. **Build** the deployment artifact
3. **Deploy** to target environment (dev/staging/prod)
4. **Smoke test** immediately against the deployed version
5. **Rollback** automatically if smoke tests fail
6. **Log** deployment with timestamp, version, deployer, status

## Rules (non-negotiable)

- Never deploy with failing tests
- Always have a rollback plan BEFORE deploying
- Smoke test immediately after deploy
- Log every deployment: timestamp, version, deployer, status

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| DevOps | ESSENTIAL | Primary deployment operator |
| Engineer | OPTIONAL | Self-deploy in dev environment |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| work | Execute deployment (after plan confirmed, readiness >= 99) |

## Relationships

- DEPENDS ON: foundation-ci (CI pipeline must exist — tests verified there)
- DEPENDS ON: foundation-docker (containerization for deployment artifacts)
- PAIRED WITH: ops-rollback (rollback if deploy fails — used as the safety net)
- FOLLOWED BY: ops-maintenance (post-deploy monitoring and maintenance)
- CONNECTS TO: fleet_task_complete (deployment task completion)
- CONNECTS TO: fleet_commit (deployment config changes committed)
- CONNECTS TO: ops-incident skill (if deployment causes incident)
- CONNECTS TO: release-cycle composite skill (deploy is step 5 of 6)
- CONNECTS TO: fleet infrastructure — DevOps also deploys LocalAI, MC, Gateway, Plane
- CONNECTS TO: IaC principle — deployment must be scriptable, reproducible
- CONNECTS TO: /loop command — DevOps may use /loop to monitor deployment status
