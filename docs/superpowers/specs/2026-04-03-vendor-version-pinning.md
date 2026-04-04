# Vendor & Plugin Version Pinning — Safety Inventory

## Purpose

Pin all vendor, plugin, and tool versions so the fleet controls when updates happen. If Anthropic updates Claude Code with new telemetry/detection, we can stay on the current version or fork.

## Critical Versions (Pin These)

| Component | Version | Location | Lock Status |
|-----------|---------|----------|-------------|
| **Claude Code CLI** | 2.1.87 | `~/.local/share/claude/versions/2.1.87` | Pinned (binary) |
| **Claude Code Source** | 2.1.87 | `../claude-code-main/` | Local copy for diffing |
| **Claude Code (prev)** | 2.1.86 | `~/.local/share/claude/versions/2.1.86` | Cached |
| **Claude Code (prev)** | 2.1.76 | `~/.local/share/claude/versions/2.1.76` | Cached |
| **OpenArms** | 2026.4.1 | `../openarms/` | pnpm-lock.yaml (434KB) |
| **OpenClaw (legacy)** | 2026.3.24 | `npm -g openclaw` / `vendor/openclaw/` | Installed globally |
| **Mission Control Backend** | 0.1.0 | `vendor/openclaw-mission-control/backend/` | uv.lock (262KB, frozen) |
| **Mission Control Frontend** | 0.1.0 | `vendor/openclaw-mission-control/frontend/` | package-lock.json (521KB) |
| **Node.js** | 22.16.0 | fnm-managed | Pinned |
| **Python** | 3.11 (fleet venv) / 3.12 (MC Docker) | System + Docker | Pinned |
| **pnpm** | 10.33.0 | System | Pinned |
| **npm** | 10.9.2 | System | Pinned |
| **PostgreSQL** | 16-alpine | Docker image | Pinned |
| **Redis** | 7-alpine | Docker image | Pinned |
| **LightRAG** | ghcr.io/hkuds/lightrag:latest | Docker image | FLOATING — pin tag |

## Claude Code Plugins (Exact Versions)

| Plugin | Org | Version | Git SHA | Risk |
|--------|-----|---------|---------|------|
| **superpowers** | claude-plugins-official | 5.0.7 | b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 | MEDIUM |
| **claude-mem** | thedotmack | 10.6.3 | d06882126fe24f6ebcbe433385daeb8322ba8009 | MEDIUM |
| **safety-net** | safety-net-dev | 0.8.2 | a8acf4db1c0d73964b51be6c4c125def2443da5d | MEDIUM |
| **sage** | sage | 4.2.3 | fae02de7dcba12df125dae0459c7140e84a1837c | MEDIUM |
| **plannotator** | plannotator | 0.16.7 | 70ad54dd701356499d0816b9a65f04713741db67 | LOW |
| **adversarial-spec** | adversarial-spec | 1.0.0 | f90cf0c36c3999b8dc272c9c06dee9846076f369 | LOW |
| **pyright-lsp** | claude-plugins-official | 1.0.0 | N/A | LOW |
| **context7** | claude-plugins-official | unknown | N/A | LOW — MCP-based |
| **hookify** | claude-plugins-official | unknown | N/A | LOW — MCP-based |
| **commit-commands** | claude-plugins-official | unknown | N/A | LOW — MCP-based |
| **security-guidance** | claude-plugins-official | unknown | N/A | LOW — MCP-based |
| **pr-review-toolkit** | claude-plugins-official | unknown | N/A | LOW — MCP-based |

Cache location: `~/.claude/plugins/cache/{org}/{plugin}/{version}/`

## MCP Servers (Exact Resolved Versions)

| MCP Server | Resolved Version | Install Method | Pinning | Used By |
|------------|-----------------|----------------|---------|---------|
| **@modelcontextprotocol/server-filesystem** | 2026.1.14 | npx (^2026.1.14) | FLOATING | 8 agents |
| **@modelcontextprotocol/server-github** | 2025.4.8 | npx (^2025.4.8) | FLOATING | 6 agents |
| **@modelcontextprotocol/server-docker** | unpinned | npx (no version) | FLOATING | devops, devsecops |
| **@playwright/mcp** | latest | npx (@latest) | FLOATING | sw-eng, qa, ux |
| **github-actions-mcp-server** | unpinned | npx (no version) | FLOATING | devops |
| **makeplane/plane-mcp-server** | unpinned | npx (no version) | FLOATING | project-manager |
| **pytest-mcp** | 0.1.0 | python -m (venv) | Pinned (local) | qa, sw-eng |
| **daniel-lightrag-mcp** | 0.1.0 | pip (git+https) | Pinned (local) | all agents |
| **fleet** | internal | python -m fleet.mcp.server | Pinned (local) | all agents |
| **@upstash/context7-mcp** | 2.1.6 | npx (^2.1.6) | FLOATING | via context7 plugin |

## Fleet Python Dependencies (from .venv)

| Package | Installed Version | pyproject.toml Pin | Status |
|---------|-------------------|-------------------|--------|
| **httpx** | 0.28.1 | >=0.27 | FLOATING |
| **pyyaml** | 6.0.3 | >=6.0 | FLOATING |
| **rich** | 14.3.3 | >=13.0 | FLOATING |
| **websockets** | 16.0 | >=12.0 | FLOATING |
| **mcp** | 1.26.0 | >=1.0 | FLOATING |
| **anthropic** | 0.88.0 | not specified | FLOATING |
| **mcp_agent** | 0.2.6 | not specified | FLOATING |
| **ruff** | 0.15.8 | >=0.4 (dev) | FLOATING |
| **pytest** | 9.0.2 | >=8.0 (dev) | FLOATING |

## Global npm Packages

| Package | Version |
|---------|---------|
| **openclaw** | 2026.3.24 (legacy — keep until openarms validated) |
| **@openai/codex** | 0.118.0 |
| **eslint** | 10.0.0 |
| **prettier** | 3.8.1 |

## Key Lock Files to Preserve

| File | Size | Purpose | CRITICAL |
|------|------|---------|----------|
| `../openarms/pnpm-lock.yaml` | 434KB | OpenArms full dependency tree | YES |
| `vendor/openclaw-mission-control/backend/uv.lock` | 262KB | MC backend Python deps | YES |
| `vendor/openclaw-mission-control/frontend/package-lock.json` | 521KB | MC frontend Node deps | YES |

## Update Strategy

1. **Claude Code** — DO NOT auto-update. Stay on 2.1.87 until new version is audited against `../claude-code-main` for new telemetry
2. **OpenArms** — We control this. Update only from our fork
3. **OpenClaw (legacy)** — Keep installed globally at 2026.3.24 for backwards compatibility
4. **Mission Control** — We control patches. Update only via fleet IaC
5. **MCP Servers** — Pin to resolved versions listed above. Update individually after testing
6. **Plugins** — Pin to exact versions + git SHAs listed above. Audit updates before deploying
7. **Python deps** — Generate a requirements.txt or uv.lock from current .venv state

## If Claude Code Gets Updated

1. Diff new version against `../claude-code-main` to identify new telemetry/detection
2. Update `../claude-code-main` to new version for reference
3. Assess impact on fleet operations
4. Either: stay on pinned version, or adapt fleet env vars/IaC to handle new detection
5. OpenArms is independent — Claude Code updates don't affect it
6. Key telemetry files to diff: `src/services/analytics/metadata.ts`, `src/services/api/client.ts`, `src/main.tsx`
