# fleet-security-audit

**Type:** Skill (slash command)
**Invocation:** /fleet-security-audit
**System:** S21 (Agent Tooling)
**Location:** openclaw-fleet/.claude/skills/fleet-security-audit
**User-invocable:** No (agent-only)

## Purpose

Guides agents in conducting security reviews of code, infrastructure, and supply chain. Covers secrets detection, injection patterns, dependency CVEs, container security, network isolation, TLS, and lock file integrity. Produces severity-classified findings and can trigger security holds for critical issues.

## Assigned Roles

- **devsecops-expert** -- primary user, conducts security reviews of PRs, deployments, configurations, and dependencies

## Methodology Stages

- **Stage 3 (INVESTIGATION)** -- security investigation of code, infrastructure, and supply chain
- **Stage 5 (WORK)** -- devsecops executes security audits during active review cycles

## What It Produces

- Security findings classified by severity (critical/high/medium/low) via fleet_alert
- Security hold requests for critical findings via fleet_notify_human (posts to ntfy urgent channel)
- Structured report per finding: title, evidence, recommendation

## Key Steps

1. **Scope** -- determine what is being reviewed (PR, deployment, configuration, dependencies), which project and component
2. **Check Areas -- Code Review** -- no secrets in code (tokens, keys, passwords), no hardcoded credentials, input validation at boundaries, no SQL injection or command injection patterns, no XSS patterns in output, dependencies checked for known CVEs, no world-writable permissions (chmod 777)
3. **Check Areas -- Infrastructure Review** -- default credentials changed, ports properly restricted, network isolation between services, TLS/encryption for external connections, secrets in .env (gitignored) not in code, container images from trusted registries
4. **Check Areas -- Supply Chain** -- dependencies from official sources, no unnecessary dependencies, lock files present and up to date
5. **Report Findings** -- use fleet_alert with severity, title, details (evidence + recommendation), and category "security"
6. **Security Hold (Critical)** -- for critical findings, use fleet_notify_human with urgent priority to request human intervention

## Relationships

- USED BY: devsecops-expert
- CONNECTS TO: fleet_alert (MCP tool), fleet_notify_human (MCP tool), infra-security (AICP skill, overlapping infrastructure security), quality-audit (AICP skill, broader quality checks), config-secrets (AICP skill, secret management)
- FEEDS: security hold pipeline (critical findings block deployment), fleet-review decision (security findings influence approval), IRC #security channel (findings posted automatically), ntfy fleet-alert (urgent notifications for critical issues)
- DEPENDS ON: code diff or deployment configuration to review, fleet MCP server running, access to dependency manifests (requirements.txt, package-lock.json, etc.)
