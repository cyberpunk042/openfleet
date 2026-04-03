# GitHub Actions MCP Server

**Type:** External MCP Server
**Package:** github-actions-mcp-server
**Transport:** npx (stdio)
**Tools:** workflows, runs, logs, artifacts
**Auth:** GitHub PAT
**Installed for:** devops

## What It Does

GitHub Actions workflow management via MCP. List workflows, trigger runs, view run status/logs, download artifacts. Focused subset of GitHub API specifically for CI/CD operations.

## Fleet Use Case

DevOps manages CI/CD pipelines. github-actions MCP provides direct access to workflow status, build logs, and artifacts without navigating the full GitHub API. Essential for ops-deploy and ops-incident skills.

## Relationships

- INSTALLED FOR: devops
- AUTH: requires GITHUB_TOKEN environment variable
- CONNECTS TO: GitHub MCP (github-actions is Actions-specific subset)
- CONNECTS TO: foundation-ci skill (CI pipeline management)
- CONNECTS TO: ops-deploy skill (deployment via Actions workflows)
- CONNECTS TO: ops-incident skill (investigate failed Actions runs)
- CONNECTS TO: /loop command (monitor deployment progress)
