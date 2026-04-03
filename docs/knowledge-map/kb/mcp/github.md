# GitHub MCP Server

**Type:** External MCP Server
**Package:** @modelcontextprotocol/server-github
**Transport:** npx (stdio)
**Tools:** 80+ (issues, PRs, Actions, search, Dependabot, repos, branches)
**Auth:** GitHub PAT or OAuth
**Installed for:** architect, software-engineer, devops, fleet-ops, project-manager, technical-writer

## What It Does

Full GitHub API access via MCP. Create/read/update issues, pull requests, branches, Actions workflows, Dependabot alerts, code search, repository management. The most tool-rich MCP server in the ecosystem.

## Fleet Use Case

Essential for agents that interact with GitHub — creating PRs (engineer), reviewing PRs (fleet-ops), managing Actions (devops), tracking issues (PM), reading code (architect), documenting (writer).

## Relationships

- INSTALLED FOR: 6 of 10 agents
- AUTH: requires GITHUB_TOKEN environment variable
- CONNECTS TO: fleet_commit tool (fleet tool creates commits → GitHub MCP manages PRs)
- CONNECTS TO: /pr-comments command (reads PR comments via GitHub API)
- CONNECTS TO: /security-review command (may use GitHub code scanning)
- CONNECTS TO: github-actions MCP (subset — Actions-specific operations)
